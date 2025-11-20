"""
Search Executor Agent
Performs parallel searches across multiple sources
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from .base_agent import BaseAgent

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

try:
    import wikipedia
except ImportError:
    wikipedia = None


class SearchExecutorAgent(BaseAgent):
    """Agent responsible for executing searches across multiple sources"""
    
    def __init__(self, metrics_collector=None):
        super().__init__("SearchExecutorAgent", metrics_collector)
        self.capabilities = [
            'duckduckgo_search',
            'wikipedia_search',
            'parallel_execution',
            'result_merging'
        ]
        self.search_timeout = 30  # seconds
    
    async def search_parallel(self, processed_query: Dict, max_results: int = 10,
                             sources: Optional[List[str]] = None) -> List[Dict]:
        """
        Execute searches in parallel across multiple sources
        
        Args:
            processed_query: Processed query from QueryProcessorAgent
            max_results: Maximum results to return
            sources: Specific sources to search (None = all)
        
        Returns:
            List of search results
        """
        start_time = self.start_task()
        
        try:
            query = processed_query['normalized_query']
            
            # Determine which sources to use
            if sources is None:
                sources = ['duckduckgo', 'wikipedia']
            
            # Create search tasks
            tasks = []
            
            if 'duckduckgo' in sources and DDGS is not None:
                tasks.append(self._search_duckduckgo(query, max_results))
            
            if 'wikipedia' in sources and wikipedia is not None:
                tasks.append(self._search_wikipedia(query, max_results))
            
            # Execute all searches in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge and filter results
            merged_results = self._merge_results(results)
            
            # Limit to max_results
            merged_results = merged_results[:max_results]
            
            execution_time = self.end_task(start_time)
            
            # Add execution metadata
            for result in merged_results:
                result['retrieved_at'] = datetime.now().isoformat()
                result['search_execution_time_ms'] = round(execution_time, 2)
            
            return merged_results
            
        except Exception as e:
            self.status = 'error'
            raise Exception(f"Search execution failed: {str(e)}")
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """Search using DuckDuckGo"""
        if DDGS is None:
            return []
        
        try:
            results = []
            
            # Use DDGS for search
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))
                
                for idx, result in enumerate(search_results):
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('href', ''),
                        'snippet': result.get('body', ''),
                        'source': 'duckduckgo',
                        'position': idx + 1,
                        'relevance_score': 0.0  # Will be calculated by analysis agent
                    })
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_wikipedia(self, query: str, max_results: int) -> List[Dict]:
        """Search using Wikipedia"""
        if wikipedia is None:
            return []
        
        try:
            results = []
            
            # Search Wikipedia
            search_results = wikipedia.search(query, results=min(max_results, 5))
            
            for idx, title in enumerate(search_results):
                try:
                    # Get page summary
                    summary = wikipedia.summary(title, sentences=2)
                    page = wikipedia.page(title)
                    
                    results.append({
                        'title': title,
                        'url': page.url,
                        'snippet': summary,
                        'source': 'wikipedia',
                        'position': idx + 1,
                        'relevance_score': 0.0
                    })
                except:
                    continue  # Skip pages that cause errors
            
            return results
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def _merge_results(self, results_list: List) -> List[Dict]:
        """Merge results from multiple sources"""
        merged = []
        
        for results in results_list:
            # Skip exceptions
            if isinstance(results, Exception):
                continue
            
            # Add valid results
            if isinstance(results, list):
                merged.extend(results)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        
        for result in merged:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
