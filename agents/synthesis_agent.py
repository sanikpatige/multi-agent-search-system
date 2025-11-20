"""
Synthesis Agent
Combines information from multiple sources into coherent answers
"""

from typing import Dict, List
from datetime import datetime
from .base_agent import BaseAgent


class SynthesisAgent(BaseAgent):
    """Agent responsible for synthesizing answers from multiple sources"""
    
    def __init__(self, metrics_collector=None):
        super().__init__("SynthesisAgent", metrics_collector)
        self.capabilities = [
            'answer_generation',
            'information_extraction',
            'multi_source_synthesis',
            'key_points_extraction'
        ]
    
    async def synthesize(self, analyzed_results: List[Dict], query_info: Dict) -> Dict:
        """
        Synthesize answer from analyzed results
        
        Args:
            analyzed_results: Analyzed and ranked search results
            query_info: Processed query information
        
        Returns:
            Synthesized answer with key points
        """
        start_time = self.start_task()
        
        try:
            if not analyzed_results:
                return self._empty_synthesis()
            
            # Extract information from top results
            top_results = analyzed_results[:5]  # Use top 5 results
            
            # Generate summary
            summary = self._generate_summary(top_results, query_info)
            
            # Extract key points
            key_points = self._extract_key_points(top_results)
            
            # Calculate confidence
            confidence = self._calculate_confidence(analyzed_results)
            
            # Get source breakdown
            sources_used = self._get_sources_breakdown(top_results)
            
            execution_time = self.end_task(start_time)
            
            return {
                'summary': summary,
                'key_points': key_points,
                'confidence': confidence,
                'sources_used': sources_used,
                'results_synthesized': len(top_results),
                'synthesis_time_ms': round(execution_time, 2),
                'synthesized_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.status = 'error'
            raise Exception(f"Synthesis failed: {str(e)}")
    
    def _generate_summary(self, results: List[Dict], query_info: Dict) -> str:
        """Generate summary from top results"""
        if not results:
            return "No results available for synthesis."
        
        query = query_info['original_query']
        intent = query_info['intent']
        
        # Build summary based on intent
        if intent == 'definition':
            summary = f"Based on search results for '{query}': "
        elif intent == 'tutorial':
            summary = f"Here's information on {query}: "
        else:
            summary = f"Regarding '{query}': "
        
        # Add information from top result
        top_result = results[0]
        snippet = top_result.get('snippet', '')
        
        if snippet:
            # Take first 200 characters
            summary += snippet[:200]
            if len(snippet) > 200:
                summary += "..."
        else:
            summary += "Multiple sources provide information on this topic. See results for details."
        
        return summary
    
    def _extract_key_points(self, results: List[Dict]) -> List[str]:
        """Extract key points from results"""
        key_points = []
        
        for result in results[:3]:  # Top 3 results
            title = result.get('title', '')
            if title and len(key_points) < 5:
                # Use titles as key points
                key_points.append(title)
        
        return key_points if key_points else ["See search results for detailed information"]
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculate confidence score for synthesis"""
        if not results:
            return 0.0
        
        # Average relevance of top 3 results
        top_3 = results[:3]
        avg_relevance = sum(r.get('relevance_score', 0) for r in top_3) / len(top_3)
        
        # Confidence is based on:
        # - Average relevance (70%)
        # - Number of quality results (30%)
        quality_results = sum(1 for r in results if r.get('relevance_score', 0) > 0.5)
        result_score = min(quality_results / 5, 1.0)  # Normalize to 5 results
        
        confidence = (avg_relevance * 0.7) + (result_score * 0.3)
        
        return round(confidence, 2)
    
    def _get_sources_breakdown(self, results: List[Dict]) -> Dict[str, int]:
        """Get breakdown of sources used"""
        sources = {}
        for result in results:
            source = result.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _empty_synthesis(self) -> Dict:
        """Return empty synthesis"""
        return {
            'summary': "No results available to synthesize.",
            'key_points': [],
            'confidence': 0.0,
            'sources_used': {},
            'results_synthesized': 0,
            'synthesis_time_ms': 0.0
        }
