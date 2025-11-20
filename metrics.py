"""
Metrics Collector
Tracks system performance and agent metrics
"""

from typing import Dict, List
from datetime import datetime
from collections import defaultdict, deque


class MetricsCollector:
    """Collects and tracks system metrics"""
    
    def __init__(self):
        self.total_searches = 0
        self.agent_executions = defaultdict(list)
        self.search_history = deque(maxlen=100)  # Keep last 100 searches
        self.error_count = 0
        self.start_time = datetime.now()
    
    def record_search(self, query: str):
        """Record a search query"""
        self.total_searches += 1
        self.search_history.append({
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_agent_execution(self, agent_name: str, execution_time_ms: float):
        """Record agent execution"""
        self.agent_executions[agent_name].append({
            'execution_time_ms': execution_time_ms,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_error(self):
        """Record an error"""
        self.error_count += 1
    
    def get_search_history(self, limit: int = 20) -> List[Dict]:
        """Get recent search history"""
        return list(self.search_history)[-limit:]
    
    def get_agent_metrics(self, agent_name: str) -> Dict:
        """Get metrics for specific agent"""
        executions = self.agent_executions.get(agent_name, [])
        
        if not executions:
            return {
                'agent_name': agent_name,
                'total_executions': 0,
                'avg_execution_time_ms': 0.0,
                'min_execution_time_ms': 0.0,
                'max_execution_time_ms': 0.0
            }
        
        times = [e['execution_time_ms'] for e in executions]
        
        return {
            'agent_name': agent_name,
            'total_executions': len(executions),
            'avg_execution_time_ms': round(sum(times) / len(times), 2),
            'min_execution_time_ms': round(min(times), 2),
            'max_execution_time_ms': round(max(times), 2)
        }
    
    def get_summary(self) -> Dict:
        """Get overall metrics summary"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate agent metrics
        agent_metrics = {}
        for agent_name in self.agent_executions.keys():
            agent_metrics[agent_name] = self.get_agent_metrics(agent_name)
        
        return {
            'uptime_seconds': round(uptime, 2),
            'total_searches': self.total_searches,
            'error_count': self.error_count,
            'searches_per_minute': round(self.total_searches / (uptime / 60), 2) if uptime > 0 else 0.0,
            'agent_metrics': agent_metrics,
            'start_time': self.start_time.isoformat()
        }
