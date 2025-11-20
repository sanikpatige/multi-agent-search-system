"""
Query Processor Agent
Analyzes queries, extracts intent, generates search variations
"""

import re
from typing import Dict, List
from .base_agent import BaseAgent


class QueryProcessorAgent(BaseAgent):
    """Agent responsible for query analysis and processing"""
    
    def __init__(self, metrics_collector=None):
        super().__init__("QueryProcessorAgent", metrics_collector)
        self.capabilities = [
            'query_expansion',
            'intent_extraction',
            'keyword_extraction',
            'query_normalization'
        ]
        
        # Common question words for intent detection
        self.question_words = {
            'what': 'definition',
            'who': 'person',
            'when': 'time',
            'where': 'location',
            'why': 'reason',
            'how': 'process'
        }
        
        # Stop words to filter
        self.stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
    
    async def process(self, query: str) -> Dict:
        """
        Process and analyze query
        
        Returns:
            Dictionary with processed query information
        """
        start_time = self.start_task()
        
        try:
            # Normalize query
            normalized = self._normalize_query(query)
            
            # Extract intent
            intent = self._extract_intent(normalized)
            
            # Extract keywords
            keywords = self._extract_keywords(normalized)
            
            # Generate query variations
            variations = self._generate_variations(normalized, keywords)
            
            result = {
                'original_query': query,
                'normalized_query': normalized,
                'intent': intent,
                'keywords': keywords,
                'variations': variations,
                'query_length': len(query.split())
            }
            
            execution_time = self.end_task(start_time)
            result['processing_time_ms'] = round(execution_time, 2)
            
            return result
            
        except Exception as e:
            self.status = 'error'
            raise Exception(f"Query processing failed: {str(e)}")
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query text"""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters except important ones
        normalized = re.sub(r'[^\w\s\-\?]', '', normalized)
        
        return normalized
    
    def _extract_intent(self, query: str) -> str:
        """Extract query intent"""
        words = query.split()
        
        if not words:
            return 'unknown'
        
        # Check first word for question type
        first_word = words[0].lower()
        if first_word in self.question_words:
            return self.question_words[first_word]
        
        # Check for other patterns
        if 'how to' in query or 'how do' in query:
            return 'tutorial'
        elif 'best' in query or 'top' in query:
            return 'recommendation'
        elif 'compare' in query or 'vs' in query or 'versus' in query:
            return 'comparison'
        elif 'review' in query:
            return 'review'
        else:
            return 'general'
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords"""
        words = query.split()
        
        # Filter stop words and short words
        keywords = [
            word for word in words
            if word not in self.stop_words and len(word) > 2
        ]
        
        return keywords[:5]  # Return top 5 keywords
    
    def _generate_variations(self, query: str, keywords: List[str]) -> List[str]:
        """Generate query variations for broader search"""
        variations = [query]  # Original query first
        
        # Add keyword-only variation
        if len(keywords) >= 2:
            variations.append(' '.join(keywords))
        
        # Add quoted phrase for exact match
        if len(query.split()) >= 2:
            variations.append(f'"{query}"')
        
        # Add variations with common modifiers
        variations.append(f"{query} tutorial")
        variations.append(f"{query} guide")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for v in variations:
            if v not in seen:
                seen.add(v)
                unique_variations.append(v)
        
        return unique_variations[:3]  # Return top 3 variations
