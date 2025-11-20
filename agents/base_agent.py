"""
Base Agent Class
All agents inherit from this base class
"""

from datetime import datetime
from typing import Dict, List
import time


class BaseAgent:
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, metrics_collector=None):
        self.name = name
        self.status = 'initializing'
        self.tasks_completed = 0
        self.total_execution_time = 0.0  # milliseconds
        self.last_active = None
        self.metrics_collector = metrics_collector
        self.capabilities = []
    
    async def initialize(self):
        """Initialize the agent"""
        print(f"  → Initializing {self.name}...")
        self.status = 'ready'
        print(f"  ✓ {self.name} ready")
    
    def start_task(self):
        """Mark task start"""
        self.status = 'working'
        self.last_active = datetime.now()
        return time.time()
    
    def end_task(self, start_time: float):
        """Mark task end and record metrics"""
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        self.tasks_completed += 1
        self.total_execution_time += execution_time
        self.status = 'ready'
        self.last_active = datetime.now()
        
        if self.metrics_collector:
            self.metrics_collector.record_agent_execution(
                agent_name=self.name,
                execution_time_ms=execution_time
            )
        
        return execution_time
    
    def get_avg_execution_time(self) -> float:
        """Calculate average execution time"""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.tasks_completed
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            'name': self.name,
            'status': self.status,
            'tasks_completed': self.tasks_completed,
            'avg_execution_time_ms': round(self.get_avg_execution_time(), 2),
            'last_active': self.last_active.isoformat() if self.last_active else None
        }
