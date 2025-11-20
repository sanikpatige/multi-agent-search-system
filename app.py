#!/usr/bin/env python3
"""
Multi-Agent Web Search & Analysis System
Main FastAPI application with agent orchestration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import asyncio
import uuid

from agents.orchestrator import SearchOrchestrator
from agents.query_processor import QueryProcessorAgent
from agents.search_executor import SearchExecutorAgent
from agents.analysis_agent import AnalysisAgent
from agents.synthesis_agent import SynthesisAgent
from cache import SearchCache
from metrics import MetricsCollector

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Search System",
    description="Intelligent web search using coordinated AI agents",
    version="1.0.0"
)

# Data Models
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results to return")
    enable_analysis: bool = Field(True, description="Enable result analysis")
    include_synthesis: bool = Field(True, description="Include answer synthesis")
    sources: Optional[List[str]] = Field(None, description="Specific sources to search")


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[Dict]
    synthesis: Optional[Dict] = None
    agent_metrics: Dict
    timestamp: str
    cached: bool = False


class AgentStatus(BaseModel):
    """Agent status model"""
    name: str
    status: str
    tasks_completed: int
    avg_execution_time_ms: float
    last_active: str


# Initialize components
cache = SearchCache(ttl_seconds=3600)
metrics = MetricsCollector()

# Initialize agents
query_processor = QueryProcessorAgent(metrics)
search_executor = SearchExecutorAgent(metrics)
analysis_agent = AnalysisAgent(metrics)
synthesis_agent = SynthesisAgent(metrics)

# Initialize orchestrator
orchestrator = SearchOrchestrator(
    query_processor=query_processor,
    search_executor=search_executor,
    analysis_agent=analysis_agent,
    synthesis_agent=synthesis_agent,
    cache=cache,
    metrics=metrics
)

# Background task storage
background_tasks_store = {}


# API Endpoints

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "name": "Multi-Agent Search System",
        "version": "1.0.0",
        "description": "Intelligent web search using coordinated AI agents",
        "docs": "/docs",
        "endpoints": {
            "search": "/search",
            "agents": "/agents/status",
            "metrics": "/metrics",
            "health": "/health"
        }
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute multi-agent search
    
    - **query**: Search query string
    - **max_results**: Maximum number of results (1-50)
    - **enable_analysis**: Enable result analysis and ranking
    - **include_synthesis**: Generate synthesized answer
    - **sources**: Optional list of specific sources to search
    """
    try:
        start_time = datetime.now()
        
        # Check cache
        cache_key = f"{request.query}:{request.max_results}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            cached_result['cached'] = True
            cached_result['agent_metrics']['cache_hit'] = True
            return cached_result
        
        # Execute search through orchestrator
        result = await orchestrator.execute_search(
            query=request.query,
            max_results=request.max_results,
            enable_analysis=request.enable_analysis,
            include_synthesis=request.include_synthesis,
            sources=request.sources
        )
        
        # Calculate total time
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        result['agent_metrics']['total_time_ms'] = round(total_time, 2)
        result['timestamp'] = datetime.now().isoformat()
        result['cached'] = False
        
        # Cache result
        cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search/async")
async def search_async(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Start async search task
    
    Returns task ID for status checking
    """
    task_id = str(uuid.uuid4())
    
    async def run_search():
        try:
            result = await orchestrator.execute_search(
                query=request.query,
                max_results=request.max_results,
                enable_analysis=request.enable_analysis,
                include_synthesis=request.include_synthesis,
                sources=request.sources
            )
            background_tasks_store[task_id] = {
                'status': 'completed',
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            background_tasks_store[task_id] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    background_tasks.add_task(run_search)
    
    background_tasks_store[task_id] = {
        'status': 'processing',
        'query': request.query,
        'started_at': datetime.now().isoformat()
    }
    
    return {
        'task_id': task_id,
        'status': 'processing',
        'message': 'Search task started',
        'check_status_url': f'/search/task/{task_id}'
    }


@app.get("/search/task/{task_id}")
def get_task_status(task_id: str):
    """Get async task status"""
    if task_id not in background_tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return background_tasks_store[task_id]


@app.get("/search/history")
def get_search_history(limit: int = 20):
    """Get recent search history"""
    history = metrics.get_search_history(limit)
    return {
        'count': len(history),
        'searches': history
    }


@app.get("/agents/status")
def get_agents_status():
    """Get status of all agents"""
    agents = [query_processor, search_executor, analysis_agent, synthesis_agent]
    
    return {
        'agents': [
            {
                'name': agent.name,
                'status': agent.status,
                'tasks_completed': agent.tasks_completed,
                'avg_execution_time_ms': round(agent.get_avg_execution_time(), 2),
                'last_active': agent.last_active.isoformat() if agent.last_active else None
            }
            for agent in agents
        ],
        'orchestrator_status': orchestrator.get_status()
    }


@app.get("/agents/{agent_name}")
def get_agent_info(agent_name: str):
    """Get specific agent information"""
    agent_map = {
        'query_processor': query_processor,
        'search_executor': search_executor,
        'analysis': analysis_agent,
        'synthesis': synthesis_agent
    }
    
    if agent_name not in agent_map:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent = agent_map[agent_name]
    
    return {
        'name': agent.name,
        'status': agent.status,
        'tasks_completed': agent.tasks_completed,
        'total_execution_time_ms': round(agent.total_execution_time, 2),
        'avg_execution_time_ms': round(agent.get_avg_execution_time(), 2),
        'last_active': agent.last_active.isoformat() if agent.last_active else None,
        'capabilities': agent.get_capabilities()
    }


@app.get("/metrics")
def get_metrics():
    """Get system performance metrics"""
    return metrics.get_summary()


@app.delete("/cache/clear")
def clear_cache():
    """Clear result cache"""
    cleared_count = cache.clear()
    return {
        'message': 'Cache cleared successfully',
        'items_cleared': cleared_count
    }


@app.get("/health")
def health_check():
    """System health check"""
    agents_healthy = all(
        agent.status == 'ready'
        for agent in [query_processor, search_executor, analysis_agent, synthesis_agent]
    )
    
    return {
        'status': 'healthy' if agents_healthy else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'agents_status': 'all_ready' if agents_healthy else 'some_unavailable',
        'cache_size': cache.size(),
        'total_searches': metrics.total_searches
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("🤖 Starting Multi-Agent Search System")
    print("="*70)
    print(f"📍 API URL: http://localhost:8000")
    print(f"📚 Interactive docs: http://localhost:8000/docs")
    print(f"📖 Alternative docs: http://localhost:8000/redoc")
    print("\n🔧 Initializing agents...")
    
    # Initialize all agents
    await query_processor.initialize()
    await search_executor.initialize()
    await analysis_agent.initialize()
    await synthesis_agent.initialize()
    
    print("✓ All agents initialized and ready")
    print("="*70 + "\n")


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
