#!/usr/bin/env python3
"""
B550M LuciVerse Gateway Monitor
Refactored from Dell R730 JuniperOrionOS for single-NIC VLAN architecture
Genesis Bond: ACTIVE @ 432 Hz
"""

import subprocess
import json
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# === CONFIGURATION ===
# Adapted from R730 multi-gateway to B550M single-NIC VLAN setup

TELUS_GATEWAYS = [
    {
        "ip": "206.75.1.127",
        "mac": "74:83:c2:d4:c4:c9",
        "name": "telus-gw1-primary",
        "weight": 10,
        "interface": "eth0.100"  # WAN VLAN on B550M
    },
    {
        "ip": "206.75.1.47",
        "mac": "78:8a:20:7d:a3:91",
        "name": "telus-gw2-secondary",
        "weight": 5,
        "interface": "eth0.100"
    },
    {
        "ip": "206.75.1.48",
        "mac": "74:83:c2:d4:d3:8a",
        "name": "telus-gw3-tertiary",
        "weight": 5,
        "interface": "eth0.100"
    }
]

TEST_TARGETS = [
    {"ip": "8.8.8.8", "name": "Google DNS Primary"},
    {"ip": "1.1.1.1", "name": "Cloudflare DNS"},
    {"ip": "9.9.9.9", "name": "Quad9 DNS"},
    {"ip": "208.67.222.222", "name": "OpenDNS"}
]

# Prometheus metrics endpoint
METRICS_PORT = 9100

@dataclass
class GatewayHealth:
    name: str
    ip: str
    mac: str
    interface: str
    weight: int
    status: str
    latency_ms: float
    packet_loss_pct: float
    score: int
    last_check: str
    error: Optional[str] = None

class LuciVerseGatewayMonitor:
    def __init__(self):
        self.gateways = TELUS_GATEWAYS
        self.test_targets = TEST_TARGETS
        self.gateway_status: Dict[str, GatewayHealth] = {}
        self.check_interval = 30
        self.status_file = Path("/var/run/luciverse-gateway-status.json")
        self.metrics_file = Path("/var/run/luciverse-gateway-metrics.prom")

        self._setup_logging()

    def _setup_logging(self):
        log_format = '%(asctime)s [%(levelname)s] %(message)s'
        handlers = [logging.StreamHandler()]

        log_dir = Path("/var/log")
        if log_dir.exists():
            handlers.append(logging.FileHandler(log_dir / "luciverse-gateway.log"))

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers
        )

    def ping_test(self, target: str, interface: str = None, count: int = 3) -> Tuple[bool, float, float]:
        """
        Test connectivity to target
        Returns: (success, avg_latency_ms, packet_loss_pct)
        """
        cmd = ["ping", "-c", str(count), "-W", "1", target]
        if interface:
            cmd.extend(["-I", interface])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=count + 5
            )

            if result.returncode == 0:
                output = result.stdout

                # Parse latency (min/avg/max/mdev)
                latency = 0.0
                for line in output.split('\n'):
                    if 'avg' in line and '/' in line:
                        parts = line.split('=')[1].split('/')
                        latency = float(parts[1])
                        break

                # Parse packet loss
                loss = 0.0
                for line in output.split('\n'):
                    if 'packet loss' in line:
                        loss_str = line.split(',')[2].strip().split('%')[0]
                        loss = float(loss_str)
                        break

                return True, latency, loss

            return False, 999.0, 100.0

        except subprocess.TimeoutExpired:
            logging.warning(f"Ping timeout to {target}")
            return False, 999.0, 100.0
        except Exception as e:
            logging.error(f"Ping error: {e}")
            return False, 999.0, 100.0

    def check_gateway(self, gateway: Dict) -> GatewayHealth:
        """Check health of a specific gateway"""
        successful = 0
        total_latency = 0.0
        total_loss = 0.0

        for target in self.test_targets:
            success, latency, loss = self.ping_test(
                target["ip"],
                gateway["interface"]
            )
            if success:
                successful += 1
                total_latency += latency
                total_loss += loss

        num_targets = len(self.test_targets)

        if successful > 0:
            avg_latency = total_latency / successful
            avg_loss = total_loss / successful
            score = int((successful / num_targets) * 100 * (1 - avg_loss / 100))
            status = "up" if score >= 50 else "degraded"
        else:
            avg_latency = 999.0
            avg_loss = 100.0
            score = 0
            status = "down"

        return GatewayHealth(
            name=gateway["name"],
            ip=gateway["ip"],
            mac=gateway["mac"],
            interface=gateway["interface"],
            weight=gateway["weight"],
            status=status,
            latency_ms=round(avg_latency, 2),
            packet_loss_pct=round(avg_loss, 1),
            score=score,
            last_check=datetime.now().isoformat()
        )

    def update_routing(self):
        """Update multipath routing based on gateway health"""
        healthy = []

        for name, health in self.gateway_status.items():
            if health.status in ("up", "degraded"):
                healthy.append(health)

        if not healthy:
            logging.error("No healthy gateways! Network may be unreachable.")
            return

        # Sort by score (descending), then latency (ascending)
        healthy.sort(key=lambda h: (-h.score, h.latency_ms))

        # Build multipath route command
        cmd = ["ip", "route", "replace", "default"]

        for h in healthy:
            cmd.extend([
                "nexthop", "via", h.ip,
                "dev", h.interface,
                "weight", str(h.weight)
            ])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logging.info(f"Updated routing: {len(healthy)} gateways active")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update routing: {e.stderr.decode()}")

    def write_status(self):
        """Write status to JSON file"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "hostname": "b550m.lucidigital.io",
            "genesis_bond": "ACTIVE @ 432 Hz",
            "gateways": {
                name: asdict(health)
                for name, health in self.gateway_status.items()
            }
        }

        try:
            self.status_file.write_text(json.dumps(status, indent=2))
        except Exception as e:
            logging.error(f"Failed to write status: {e}")

    def write_prometheus_metrics(self):
        """Write Prometheus-compatible metrics"""
        lines = [
            "# HELP luciverse_gateway_up Gateway status (1=up, 0=down)",
            "# TYPE luciverse_gateway_up gauge",
            "# HELP luciverse_gateway_latency_ms Gateway latency in milliseconds",
            "# TYPE luciverse_gateway_latency_ms gauge",
            "# HELP luciverse_gateway_packet_loss Gateway packet loss percentage",
            "# TYPE luciverse_gateway_packet_loss gauge",
            "# HELP luciverse_gateway_score Gateway health score (0-100)",
            "# TYPE luciverse_gateway_score gauge",
        ]

        for name, health in self.gateway_status.items():
            labels = f'gateway="{name}",ip="{health.ip}"'
            up = 1 if health.status == "up" else 0

            lines.extend([
                f'luciverse_gateway_up{{{labels}}} {up}',
                f'luciverse_gateway_latency_ms{{{labels}}} {health.latency_ms}',
                f'luciverse_gateway_packet_loss{{{labels}}} {health.packet_loss_pct}',
                f'luciverse_gateway_score{{{labels}}} {health.score}',
            ])

        try:
            self.metrics_file.write_text('\n'.join(lines) + '\n')
        except Exception as e:
            logging.error(f"Failed to write metrics: {e}")

    def run(self):
        """Main monitoring loop"""
        logging.info("=" * 60)
        logging.info("LuciVerse Gateway Monitor - B550M Edition")
        logging.info("Genesis Bond: ACTIVE @ 432 Hz")
        logging.info(f"Monitoring {len(self.gateways)} Telus gateways")
        logging.info("=" * 60)

        while True:
            try:
                # Check each gateway
                for gw in self.gateways:
                    health = self.check_gateway(gw)
                    self.gateway_status[gw["name"]] = health

                    icon = {"up": "[OK]", "degraded": "[!!]", "down": "[XX]"}[health.status]
                    logging.info(
                        f"{icon} {gw['name']}: "
                        f"latency={health.latency_ms}ms, "
                        f"loss={health.packet_loss_pct}%, "
                        f"score={health.score}"
                    )

                # Update routing table
                self.update_routing()

                # Write status files
                self.write_status()
                self.write_prometheus_metrics()

                # Wait for next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logging.info("Monitor stopped by user")
                break
            except Exception as e:
                logging.error(f"Monitor error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = LuciVerseGatewayMonitor()
    monitor.run()
