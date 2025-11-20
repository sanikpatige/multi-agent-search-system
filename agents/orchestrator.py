"""
Search Orchestrator
Coordinates all agents and manages the search workflow
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from .base_agent import BaseAgent


class SearchOrchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self, query_processor, search_executor, analysis_agent, 
                 synthesis_agent, cache, metrics):
        self.query_processor = query_processor
        self.search_executor = search_executor
        self.analysis_agent = analysis_agent
        self.synthesis_agent = synthesis_agent
        self.cache = cache
        self.metrics = metrics
        
        self.status = 'ready'
        self.total_searches = 0
        self.successful_searches = 0
        self.failed_searches = 0
    
    async def execute_search(self, query: str, max_results: int = 10,
                            enable_analysis: bool = True,
                            include_synthesis: bool = True,
                            sources: Optional[List[str]] = None) -> Dict:
        """
        Execute complete search workflow
        
        Workflow:
        1. Process query (Query Processor Agent)
        2. Execute searches (Search Executor Agent)
        3. Analyze results (Analysis Agent)
        4. Synthesize answer (Synthesis Agent)
        
        Args:
            query: Search query
            max_results: Maximum results to return
            enable_analysis: Enable result analysis
            include_synthesis: Include answer synthesis
            sources: Specific sources to search
        
        Returns:
            Complete search response
        """
        start_time = datetime.now()
        self.total_searches += 1
        
        try:
            # Record search
            self.metrics.record_search(query)
            
            # Step 1: Process Query
            print(f"\n🔍 Processing query: '{query}'")
            processed_query = await self.query_processor.process(query)
            print(f"  ✓ Intent: {processed_query['intent']}")
            print(f"  ✓ Keywords: {', '.join(processed_query['keywords'])}")
            
            # Step 2: Execute Search
            print(f"\n🌐 Executing searches...")
            search_results = await self.search_executor.search_parallel(
                processed_query=processed_query,
                max_results=max_results,
                sources=sources
            )
            print(f"  ✓ Found {len(search_results)} results")
            
            # Step 3: Analyze Results (if enabled)
            if enable_analysis and search_results:
                print(f"\n📊 Analyzing results...")
                analyzed_results = await self.analysis_agent.analyze(
                    results=search_results,
                    query_info=processed_query
                )
                print(f"  ✓ Ranked {len(analyzed_results)} results")
            else:
                analyzed_results = search_results
            
            # Step 4: Synthesize Answer (if enabled)
            synthesis = None
            if include_synthesis and analyzed_results:
                print(f"\n🔬 Synthesizing answer...")
                synthesis = await self.synthesis_agent.synthesize(
                    analyzed_results=analyzed_results,
                    query_info=processed_query
                )
                print(f"  ✓ Confidence: {synthesis['confidence']}")
            
            # Calculate metrics
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            agent_metrics = {
                'query_processing_ms': processed_query.get('processing_time_ms', 0),
                'search_execution_ms': search_results[0].get('search_execution_time_ms', 0) if search_results else 0,
                'analysis_ms': 0,
                'synthesis_ms': synthesis.get('synthesis_time_ms', 0) if synthesis else 0,
                'total_time_ms': round(total_time, 2),
                'agents_used': self._get_agents_used(enable_analysis, include_synthesis),
                'cache_hit': False
            }
            
            # Build response
            response = {
                'query': query,
                'results': analyzed_results,
                'synthesis': synthesis,
                'agent_metrics': agent_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            self.successful_searches += 1
            print(f"\n✅ Search completed in {agent_metrics['total_time_ms']}ms\n")
            
            return response
            
        except Exception as e:
            self.failed_searches += 1
            print(f"\n❌ Search failed: {str(e)}\n")
            raise Exception(f"Orchestrator execution failed: {str(e)}")
    
    def _get_agents_used(self, enable_analysis: bool, include_synthesis: bool) -> List[str]:
        """Get list of agents used in workflow"""
        agents = ["QueryProcessor", "SearchExecutor"]
        
        if enable_analysis:
            agents.append("AnalysisAgent")
        
        if include_synthesis:
            agents.append("SynthesisAgent")
        
        return agents
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            'status': self.status,
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'failed_searches': self.failed_searches,
            'success_rate': round(
                self.successful_searches / self.total_searches * 100, 2
            ) if self.total_searches > 0 else 0.0
        }
