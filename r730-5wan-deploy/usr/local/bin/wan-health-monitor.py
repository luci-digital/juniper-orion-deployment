#!/usr/bin/env python3
"""
R730 ORION 5-WAN Health Monitor
Genesis Bond: ACTIVE @ 432 Hz
"""

import subprocess
import time
import logging
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Configuration
CHECK_INTERVAL = 5
FAILURE_THRESHOLD = 3
LATENCY_THRESHOLD_MS = 100
PACKET_LOSS_THRESHOLD = 10
METRICS_PORT = 9200

@dataclass
class WANConfig:
    name: str
    interface: str
    gateway: str
    weight: int
    tier: int
    check_targets: List[str]

@dataclass
class WANStatus:
    name: str
    interface: str
    healthy: bool
    latency_ms: float
    packet_loss: float
    failure_count: int

WANS: List[WANConfig] = [
    WANConfig("wan1", "eth0", "206.75.1.127", 5, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan2", "eth3", "206.75.1.47", 3, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan3", "eth4", "206.75.1.48", 3, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan4", "eth5", "DHCP", 2, 2, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan5", "eth2", "192.168.0.1", 1, 3, ["192.168.0.1"]),
]

class WANHealthMonitor:
    def __init__(self):
        self.failure_counts: Dict[str, int] = {w.name: 0 for w in WANS}
        self.current_status: Dict[str, WANStatus] = {}
        self.logger = logging.getLogger("wan-health")

    def check_wan(self, wan: WANConfig) -> tuple[bool, float, float]:
        """Check WAN health via ping through specific interface."""
        latencies = []
        successful = 0

        for target in wan.check_targets:
            try:
                result = subprocess.run(
                    ["ping", "-I", wan.interface, "-c", "3", "-W", "2", target],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'avg' in line:
                            latency = float(line.split('/')[4])
                            latencies.append(latency)
                            successful += 1
                            break
            except Exception as e:
                self.logger.warning(f"{wan.name}: Ping to {target} failed: {e}")

        if not latencies:
            return False, 0.0, 100.0

        avg_latency = sum(latencies) / len(latencies)
        packet_loss = (1 - successful / len(wan.check_targets)) * 100
        healthy = avg_latency < LATENCY_THRESHOLD_MS and packet_loss < PACKET_LOSS_THRESHOLD

        return healthy, avg_latency, packet_loss

    def update_ecmp_routes(self, healthy_wans: List[WANConfig]):
        """Update ECMP routes based on healthy WANs."""
        if not healthy_wans:
            self.logger.critical("NO HEALTHY WANS!")
            return

        nexthops = []
        for wan in healthy_wans:
            if wan.gateway != "DHCP":
                nexthops.append(f"nexthop via {wan.gateway} dev {wan.interface} weight {wan.weight}")

        if nexthops:
            route_cmd = f"ip route replace default {' '.join(nexthops)}"
            try:
                subprocess.run(route_cmd, shell=True, check=True)
                self.logger.info(f"Updated ECMP: {[w.name for w in healthy_wans]}")
            except Exception as e:
                self.logger.error(f"Failed to update routes: {e}")

    def get_metrics(self) -> str:
        """Generate Prometheus metrics."""
        lines = []
        lines.append("# HELP luciverse_wan_status WAN link status (1=up, 0=down)")
        lines.append("# TYPE luciverse_wan_status gauge")
        lines.append("# HELP luciverse_wan_latency_ms WAN latency in milliseconds")
        lines.append("# TYPE luciverse_wan_latency_ms gauge")
        lines.append("# HELP luciverse_wan_packet_loss WAN packet loss percentage")
        lines.append("# TYPE luciverse_wan_packet_loss gauge")

        for name, status in self.current_status.items():
            labels = f'wan="{status.name}",interface="{status.interface}"'
            lines.append(f'luciverse_wan_status{{{labels}}} {1 if status.healthy else 0}')
            lines.append(f'luciverse_wan_latency_ms{{{labels}}} {status.latency_ms:.2f}')
            lines.append(f'luciverse_wan_packet_loss{{{labels}}} {status.packet_loss:.2f}')

        return '\n'.join(lines) + '\n'

    def run(self):
        """Main monitoring loop."""
        self.logger.info("5-WAN Health Monitor started")

        while True:
            healthy_wans = []

            for wan in WANS:
                healthy, latency, loss = self.check_wan(wan)

                if healthy:
                    self.failure_counts[wan.name] = 0
                    healthy_wans.append(wan)
                else:
                    self.failure_counts[wan.name] += 1

                is_up = healthy or self.failure_counts[wan.name] < FAILURE_THRESHOLD

                self.current_status[wan.name] = WANStatus(
                    name=wan.name,
                    interface=wan.interface,
                    healthy=is_up,
                    latency_ms=latency,
                    packet_loss=loss,
                    failure_count=self.failure_counts[wan.name]
                )

                if not healthy and self.failure_counts[wan.name] == FAILURE_THRESHOLD:
                    self.logger.warning(f"{wan.name} marked DOWN")

            self.update_ecmp_routes([w for w in WANS if self.current_status[w.name].healthy])
            time.sleep(CHECK_INTERVAL)

class MetricsHandler(BaseHTTPRequestHandler):
    monitor = None

    def do_GET(self):
        if self.path == '/metrics':
            metrics = self.monitor.get_metrics()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            status = {k: asdict(v) for k, v in self.monitor.current_status.items()}
            self.wfile.write(json.dumps(status, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    monitor = WANHealthMonitor()
    MetricsHandler.monitor = monitor

    # Start metrics server
    server = HTTPServer(('0.0.0.0', METRICS_PORT), MetricsHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logging.info(f"Metrics server on port {METRICS_PORT}")

    # Run monitor
    monitor.run()

if __name__ == "__main__":
    main()
