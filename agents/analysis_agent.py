"""
Analysis Agent
Ranks results, scores relevance, filters low-quality content
"""

import re
from typing import Dict, List
from datetime import datetime
from .base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """Agent responsible for analyzing and ranking search results"""
    
    def __init__(self, metrics_collector=None):
        super().__init__("AnalysisAgent", metrics_collector)
        self.capabilities = [
            'relevance_scoring',
            'result_ranking',
            'duplicate_filtering',
            'quality_assessment'
        ]
        
        # Source authority scores
        self.source_authority = {
            'wikipedia': 0.9,
            'duckduckgo': 0.7,
            'default': 0.5
        }
    
    async def analyze(self, results: List[Dict], query_info: Dict) -> List[Dict]:
        """
        Analyze and rank search results
        
        Args:
            results: Raw search results
            query_info: Processed query information
        
        Returns:
            Analyzed and ranked results
        """
        start_time = self.start_task()
        
        try:
            if not results:
                self.end_task(start_time)
                return []
            
            query = query_info['normalized_query']
            keywords = query_info['keywords']
            
            # Score each result
            for result in results:
                result['relevance_score'] = self._calculate_relevance(
                    result, query, keywords
                )
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Add ranking
            for idx, result in enumerate(results):
                result['rank'] = idx + 1
            
            execution_time = self.end_task(start_time)
            
            # Add analysis metadata
            analysis_metadata = {
                'analyzed_at': datetime.now().isoformat(),
                'analysis_time_ms': round(execution_time, 2),
                'total_results': len(results),
                'avg_relevance_score': round(
                    sum(r['relevance_score'] for r in results) / len(results), 3
                )
            }
            
            return results
            
        except Exception as e:
            self.status = 'error'
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _calculate_relevance(self, result: Dict, query: str, keywords: List[str]) -> float:
        """
        Calculate relevance score for a result
        
        Scoring factors:
        - Title relevance (40%)
        - Snippet relevance (30%)
        - Source authority (20%)
        - Position bonus (10%)
        """
        score = 0.0
        
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        source = result.get('source', 'default')
        position = result.get('position', 10)
        
        # Title relevance (40%)
        title_score = self._text_relevance(title, query, keywords)
        score += title_score * 0.4
        
        # Snippet relevance (30%)
        snippet_score = self._text_relevance(snippet, query, keywords)
        score += snippet_score * 0.3
        
        # Source authority (20%)
        authority = self.source_authority.get(source, self.source_authority['default'])
        score += authority * 0.2
        
        # Position bonus (10%) - earlier results get slight boost
        position_score = max(0, 1.0 - (position - 1) * 0.1)
        score += position_score * 0.1
        
        return round(score, 3)
    
    def _text_relevance(self, text: str, query: str, keywords: List[str]) -> float:
        """Calculate text relevance based on keyword matching"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Exact query match
        if query in text:
            score += 0.5
        
        # Keyword matches
        keyword_matches = sum(1 for kw in keywords if kw in text)
        if keywords:
            score += (keyword_matches / len(keywords)) * 0.5
        
        return min(score, 1.0)  # Cap at 1.0
