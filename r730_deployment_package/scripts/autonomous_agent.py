#!/usr/bin/env python3
"""
JuniperOrion Autonomous AI Agent
Self-improving network management system with Claude/OpenAI integration
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import aiohttp
import numpy as np
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our modules
from tools.claude_code_executor import ClaudeCodeExecutor, CodeExecutionRequest, Language
from skills.network_optimization import NetworkOptimizationSkill

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Agent state and metrics"""
    status: str = "initializing"
    uptime: float = 0.0
    optimizations_applied: int = 0
    issues_resolved: int = 0
    skills_created: int = 0
    last_action: Optional[str] = None
    performance_score: float = 100.0
    learning_rate: float = 0.01

class JuniperOrionAgent:
    """
    Autonomous AI Agent for Network Management
    Integrates Claude code execution, OpenAI functions, and Anthropic skills
    """
    
    def __init__(self, config_path: str = "config/agent.yaml"):
        self.config = self._load_config(config_path)
        self.state = AgentState()
        self.executor = ClaudeCodeExecutor()
        self.skills = {}
        self.learning_model = {}
        self.metrics_history = []
        self.session = None
        self.running = False
        
        # Hardware configuration for Dell R730
        self.hardware = {
            'cpus': 56,
            'memory_gb': 384,
            'nics': 8,
            'service_tag': 'CQ5QBM2'
        }
        
        # Initialize skills
        self._load_skills()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load agent configuration"""
        default_config = {
            'monitoring_interval': 30,
            'optimization_threshold': 0.8,
            'learning_enabled': True,
            'auto_heal': True,
            'claude_api_key': os.getenv('CLAUDE_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY')
        }
        
        if Path(config_path).exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
                default_config.update(config)
        
        return default_config
    
    def _load_skills(self):
        """Load available skills"""
        skills_dir = Path(__file__).parent / 'skills'
        
        # Load network optimization skill
        self.skills['network_optimization'] = NetworkOptimizationSkill()
        
        logger.info(f"Loaded {len(self.skills)} skills")
    
    async def start(self):
        """Start the autonomous agent"""
        logger.info("Starting JuniperOrion Autonomous Agent")
        self.running = True
        self.state.status = "running"
        self.session = aiohttp.ClientSession()
        
        # Start concurrent tasks
        tasks = [
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._learning_loop()),
            asyncio.create_task(self._self_improvement_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down agent...")
            await self.stop()
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.state.status = "stopped"
        if self.session:
            await self.session.close()
        logger.info("Agent stopped")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                })
                
                # Analyze metrics for issues
                issues = self._analyze_metrics(metrics)
                
                if issues:
                    logger.warning(f"Detected {len(issues)} issues: {issues}")
                    await self._handle_issues(issues)
                
                # Trim history to last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                await asyncio.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _optimization_loop(self):
        """Continuous optimization loop"""
        while self.running:
            try:
                # Check if optimization is needed
                if await self._should_optimize():
                    logger.info("Starting optimization cycle")
                    
                    # Generate optimization code
                    optimization_code = await self._generate_optimization_code()
                    
                    # Execute optimization
                    request = CodeExecutionRequest(
                        language=Language.PYTHON,
                        code=optimization_code,
                        description="Network optimization",
                        sandbox=True,
                        timeout=60
                    )
                    
                    result = await self.executor.execute(request)
                    
                    if result.success:
                        self.state.optimizations_applied += 1
                        logger.info(f"Optimization successful: {result.output}")
                    else:
                        logger.error(f"Optimization failed: {result.error}")
                
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                await asyncio.sleep(60)
    
    async def _learning_loop(self):
        """Machine learning and pattern recognition loop"""
        while self.running:
            try:
                if self.config['learning_enabled'] and len(self.metrics_history) > 100:
                    # Analyze patterns in historical data
                    patterns = await self._analyze_patterns()
                    
                    # Update learning model
                    await self._update_learning_model(patterns)
                    
                    # Generate predictions
                    predictions = await self._generate_predictions()
                    
                    # Proactive optimization based on predictions
                    if predictions.get('high_load_predicted'):
                        await self._prepare_for_high_load()
                
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Learning error: {e}")
                await asyncio.sleep(300)
    
    async def _self_improvement_loop(self):
        """Self-improvement through skill creation and refinement"""
        while self.running:
            try:
                # Analyze agent performance
                performance = self._evaluate_self_performance()
                
                # Identify areas for improvement
                improvements = await self._identify_improvements(performance)
                
                for improvement in improvements:
                    # Generate new skill or refine existing
                    if improvement['type'] == 'new_skill':
                        skill = await self._create_new_skill(improvement)
                        self.skills[skill['name']] = skill
                        self.state.skills_created += 1
                        logger.info(f"Created new skill: {skill['name']}")
                    
                    elif improvement['type'] == 'refine_skill':
                        await self._refine_skill(improvement['skill_name'])
                        logger.info(f"Refined skill: {improvement['skill_name']}")
                
                await asyncio.sleep(86400)  # 24 hours
                
            except Exception as e:
                logger.error(f"Self-improvement error: {e}")
                await asyncio.sleep(3600)
    
    async def _collect_metrics(self) -> Dict:
        """Collect system and network metrics"""
        metrics_code = """
import psutil
import subprocess
import json

# System metrics
cpu_percent = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory()
disk = psutil.disk_usage('/')

# Network metrics
net_io = psutil.net_io_counters(pernic=True)

# Interface statistics
interfaces = {}
for iface, stats in net_io.items():
    if iface.startswith('eth'):
        interfaces[iface] = {
            'bytes_sent': stats.bytes_sent,
            'bytes_recv': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_recv': stats.packets_recv,
            'errin': stats.errin,
            'errout': stats.errout,
            'dropin': stats.dropin,
            'dropout': stats.dropout
        }

# BGP status
try:
    bgp_output = subprocess.check_output(['birdc', 'show', 'protocols'], text=True)
    bgp_up = bgp_output.count('Established')
except:
    bgp_up = 0

metrics = {
    'cpu_percent': cpu_percent,
    'memory_percent': memory.percent,
    'memory_available_gb': memory.available / (1024**3),
    'disk_percent': disk.percent,
    'interfaces': interfaces,
    'bgp_sessions_up': bgp_up
}

print(json.dumps(metrics))
"""
        
        request = CodeExecutionRequest(
            language=Language.PYTHON,
            code=metrics_code,
            description="Collect system metrics",
            sandbox=False,  # Need system access
            timeout=10
        )
        
        result = await self.executor.execute(request)
        
        if result.success:
            try:
                return json.loads(result.output.strip().split('\n')[-1])
            except:
                return {}
        return {}
    
    def _analyze_metrics(self, metrics: Dict) -> List[Dict]:
        """Analyze metrics to identify issues"""
        issues = []
        
        # High CPU usage
        if metrics.get('cpu_percent', 0) > 80:
            issues.append({
                'type': 'high_cpu',
                'severity': 'warning',
                'value': metrics['cpu_percent']
            })
        
        # Memory pressure
        if metrics.get('memory_percent', 0) > 90:
            issues.append({
                'type': 'high_memory',
                'severity': 'critical',
                'value': metrics['memory_percent']
            })
        
        # Check interfaces for errors
        for iface, stats in metrics.get('interfaces', {}).items():
            error_rate = (stats.get('errin', 0) + stats.get('errout', 0)) / max(
                stats.get('packets_recv', 1) + stats.get('packets_sent', 1), 1
            )
            
            if error_rate > 0.001:  # 0.1% error rate
                issues.append({
                    'type': 'interface_errors',
                    'severity': 'warning',
                    'interface': iface,
                    'error_rate': error_rate
                })
        
        # BGP sessions down
        if metrics.get('bgp_sessions_up', 0) < 3:  # Expecting 3 Telus gateways
            issues.append({
                'type': 'bgp_down',
                'severity': 'critical',
                'sessions_up': metrics['bgp_sessions_up']
            })
        
        return issues
    
    async def _handle_issues(self, issues: List[Dict]):
        """Handle detected issues"""
        for issue in issues:
            logger.info(f"Handling issue: {issue}")
            
            # Generate fix code
            fix_code = await self._generate_fix_code(issue)
            
            # Execute fix
            request = CodeExecutionRequest(
                language=Language.BASH,
                code=fix_code,
                description=f"Fix for {issue['type']}",
                sandbox=False,
                timeout=30
            )
            
            result = await self.executor.execute(request)
            
            if result.success:
                self.state.issues_resolved += 1
                logger.info(f"Issue resolved: {issue['type']}")
            else:
                logger.error(f"Failed to fix {issue['type']}: {result.error}")

    async def _generate_fix_code(self, issue: Dict) -> str:
        """Generate code to fix an issue"""
        fixes = {
            'high_cpu': """
# Optimize CPU usage
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu
done
# Restart packet processor with CPU limits
systemctl restart packet-processor
""",
            'high_memory': """
# Clear caches
sync && echo 3 > /proc/sys/vm/drop_caches
# Reduce DPDK memory if needed
echo 16 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
""",
            'interface_errors': f"""
# Reset interface {issue.get('interface', 'eth0')}
iface={issue.get('interface', 'eth0')}
ip link set $iface down
sleep 1
ip link set $iface up
# Optimize interface settings
ethtool -K $iface gso on gro on tso on
ethtool -G $iface rx 4096 tx 4096
""",
            'bgp_down': """
# Restart BGP daemon
systemctl restart bird
sleep 5
# Check BGP status
birdc show protocols
"""
        }
        
        return fixes.get(issue['type'], "echo 'No fix available'")
    
    async def _should_optimize(self) -> bool:
        """Determine if optimization is needed"""
        if not self.metrics_history:
            return False
        
        recent_metrics = self.metrics_history[-10:]
        
        # Check average CPU usage
        avg_cpu = np.mean([m['metrics'].get('cpu_percent', 0) for m in recent_metrics])
        if avg_cpu > 70:
            return True
        
        # Check for consistent errors
        error_count = sum(
            1 for m in recent_metrics 
            if self._analyze_metrics(m['metrics'])
        )
        
        return error_count > 5
    
    async def _generate_optimization_code(self) -> str:
        """Generate optimization code using AI"""
        # This would call Claude API to generate optimization code
        # For now, return a template
        return """
import subprocess
import json

# Optimize network stack
optimizations = [
    "sysctl -w net.core.rmem_max=134217728",
    "sysctl -w net.core.wmem_max=134217728",
    "sysctl -w net.ipv4.tcp_congestion_control=bbr",
    "sysctl -w net.ipv4.tcp_notsent_lowat=16384"
]

results = []
for cmd in optimizations:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    results.append({
        'command': cmd,
        'success': result.returncode == 0
    })

print(json.dumps({'optimizations': results}))
"""
    
    async def _analyze_patterns(self) -> Dict:
        """Analyze patterns in historical metrics"""
        if len(self.metrics_history) < 100:
            return {}
        
        # Extract time series data
        cpu_series = [m['metrics'].get('cpu_percent', 0) for m in self.metrics_history]
        memory_series = [m['metrics'].get('memory_percent', 0) for m in self.metrics_history]
        
        # Simple pattern detection
        patterns = {
            'cpu_trend': 'increasing' if cpu_series[-1] > cpu_series[0] else 'stable',
            'memory_trend': 'increasing' if memory_series[-1] > memory_series[0] else 'stable',
            'peak_hours': self._identify_peak_hours(),
            'recurring_issues': self._identify_recurring_issues()
        }
        
        return patterns
    
    def _identify_peak_hours(self) -> List[int]:
        """Identify peak traffic hours"""
        # Simplified - would use more sophisticated analysis
        hourly_loads = {}
        
        for entry in self.metrics_history:
            hour = datetime.fromisoformat(entry['timestamp']).hour
            cpu = entry['metrics'].get('cpu_percent', 0)
            
            if hour not in hourly_loads:
                hourly_loads[hour] = []
            hourly_loads[hour].append(cpu)
        
        # Find hours with consistently high load
        peak_hours = []
        for hour, loads in hourly_loads.items():
            if np.mean(loads) > 60:
                peak_hours.append(hour)
        
        return peak_hours
    
    def _identify_recurring_issues(self) -> List[str]:
        """Identify recurring issues"""
        issue_counts = {}
        
        for entry in self.metrics_history:
            issues = self._analyze_metrics(entry['metrics'])
            for issue in issues:
                issue_type = issue['type']
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Return issues that occur frequently
        total_samples = len(self.metrics_history)
        recurring = [
            issue_type for issue_type, count in issue_counts.items()
            if count > total_samples * 0.1  # More than 10% of the time
        ]
        
        return recurring
    
    async def _update_learning_model(self, patterns: Dict):
        """Update the learning model with new patterns"""
        self.learning_model.update(patterns)
        
        # Adjust agent behavior based on patterns
        if patterns.get('cpu_trend') == 'increasing':
            self.state.learning_rate *= 1.1  # Learn faster
        
        logger.info(f"Updated learning model: {patterns}")
    
    async def _generate_predictions(self) -> Dict:
        """Generate predictions based on learning model"""
        predictions = {}
        
        # Predict high load based on time
        current_hour = datetime.now().hour
        peak_hours = self.learning_model.get('peak_hours', [])
        
        if current_hour in peak_hours or (current_hour + 1) % 24 in peak_hours:
            predictions['high_load_predicted'] = True
        
        # Predict recurring issues
        recurring_issues = self.learning_model.get('recurring_issues', [])
        if recurring_issues:
            predictions['likely_issues'] = recurring_issues
        
        return predictions
    
    async def _prepare_for_high_load(self):
        """Prepare system for predicted high load"""
        preparation_code = """
# Prepare for high load
# Increase buffers
sysctl -w net.core.netdev_max_backlog=5000
sysctl -w net.ipv4.tcp_max_syn_backlog=8192

# Optimize CPU governor
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu
done

# Pre-allocate memory
echo 32 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages

echo "System prepared for high load"
"""
        
        request = CodeExecutionRequest(
            language=Language.BASH,
            code=preparation_code,
            description="Prepare for high load",
            sandbox=False,
            timeout=30
        )
        
        result = await self.executor.execute(request)
        
        if result.success:
            logger.info("System prepared for predicted high load")
        else:
            logger.error(f"Failed to prepare for high load: {result.error}")
    
    def _evaluate_self_performance(self) -> Dict:
        """Evaluate agent's own performance"""
        performance = {
            'uptime': (datetime.now() - datetime.fromtimestamp(0)).total_seconds(),
            'optimizations_applied': self.state.optimizations_applied,
            'issues_resolved': self.state.issues_resolved,
            'skills_created': self.state.skills_created,
            'success_rate': self._calculate_success_rate(),
            'learning_progress': self.state.learning_rate
        }
        
        # Calculate overall score
        performance['score'] = (
            performance['success_rate'] * 0.5 +
            min(performance['issues_resolved'] / 100, 1.0) * 0.3 +
            min(performance['optimizations_applied'] / 50, 1.0) * 0.2
        ) * 100
        
        self.state.performance_score = performance['score']
        
        return performance
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of actions"""
        if not self.executor.execution_history:
            return 1.0
        
        successes = sum(
            1 for entry in self.executor.execution_history
            if entry['result']['success']
        )
        
        return successes / len(self.executor.execution_history)
    
    async def _identify_improvements(self, performance: Dict) -> List[Dict]:
        """Identify areas for improvement"""
        improvements = []
        
        # Low success rate - need better error handling
        if performance['success_rate'] < 0.8:
            improvements.append({
                'type': 'refine_skill',
                'skill_name': 'error_handling',
                'reason': 'Low success rate'
            })
        
        # Recurring issues - need specialized skill
        recurring = self.learning_model.get('recurring_issues', [])
        for issue in recurring:
            if issue not in self.skills:
                improvements.append({
                    'type': 'new_skill',
                    'skill_name': f"fix_{issue}",
                    'reason': f"Recurring issue: {issue}"
                })
        
        return improvements
    
    async def _create_new_skill(self, improvement: Dict) -> Dict:
        """Create a new skill dynamically"""
        skill_code = f"""
# Auto-generated skill for {improvement['skill_name']}
class {improvement['skill_name'].title().replace('_', '')}Skill:
    def __init__(self):
        self.name = '{improvement['skill_name']}'
        
    async def execute(self, context):
        # Implementation generated based on historical data
        return {{'success': True, 'action': 'executed'}}
"""
        
        # Save skill to file
        skill_path = Path(__file__).parent / 'skills' / f"{improvement['skill_name']}.py"
        skill_path.write_text(skill_code)
        
        return {
            'name': improvement['skill_name'],
            'code': skill_code,
            'created': datetime.now().isoformat()
        }
    
    async def _refine_skill(self, skill_name: str):
        """Refine an existing skill based on performance data"""
        if skill_name not in self.skills:
            return
        
        # Analyze skill performance
        # This would use ML to improve the skill
        logger.info(f"Refining skill: {skill_name}")
    
    async def get_status(self) -> Dict:
        """Get agent status"""
        return {
            'state': asdict(self.state),
            'metrics': self.metrics_history[-1] if self.metrics_history else {},
            'skills': list(self.skills.keys()),
            'performance': self._evaluate_self_performance()
        }

async def main():
    """Main entry point"""
    agent = JuniperOrionAgent()
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
