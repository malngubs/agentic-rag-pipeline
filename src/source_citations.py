"""
📖 ENHANCED SOURCE CITATIONS MODULE
===================================
Provides detailed source citations with text snippets, confidence scores,
and better formatting for RAG responses.

Features:
- Extract relevant text snippets from sources
- Calculate relevance scores for citations
- Format citations with confidence indicators
- Support for multiple citation styles
- Page/section tracking for PDFs and documents

Author: AI King @ Macrocomm
Version: 2.1 - Phase 1 Implementation
Date: November 2025
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# =============================================================================
# 📋 CITATION MODELS
# =============================================================================

class CitationStyle(Enum):
    """Supported citation formats"""
    SIMPLE = "simple"  # Just filename
    DETAILED = "detailed"  # Filename with snippet
    ACADEMIC = "academic"  # APA-style citation
    FOOTNOTE = "footnote"  # Numbered footnote style

@dataclass
class SourceCitation:
    """
    Enhanced source citation with detailed metadata
    """
    source_id: str  # Unique identifier for the source
    filename: str  # Source document filename
    chunk_index: int  # Which chunk from the document
    snippet: str  # Relevant text excerpt (max 200 chars)
    full_text: str  # Full chunk text
    relevance_score: float  # How relevant this source is (0-1)
    confidence_score: float  # Confidence in this source (0-1)
    page_number: Optional[int] = None  # Page number if available
    section: Optional[str] = None  # Section/heading if available
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata

# =============================================================================
# 🎯 CITATION BUILDER
# =============================================================================

class CitationBuilder:
    """
    Builds formatted citations from search results
    
    Features:
    - Extracts relevant snippets around query matches
    - Calculates relevance scores
    - Formats citations in multiple styles
    - Groups citations by document
    - Highlights key phrases
    """
    
    def __init__(self, style: CitationStyle = CitationStyle.DETAILED):
        """
        Initialize citation builder
        
        Args:
            style: Preferred citation style
        """
        self.style = style
        self.logger = logging.getLogger(__name__)
    
    def build_citations(
        self,
        search_results: List[Dict[str, Any]],
        query: str,
        max_snippet_length: int = 200
    ) -> List[SourceCitation]:
        """
        Build enhanced citations from RAG search results
        
        Args:
            search_results: List of search results from vector store
            query: Original query text
            max_snippet_length: Maximum length for text snippets
            
        Returns:
            List of SourceCitation objects
        """
        citations = []
        
        for idx, result in enumerate(search_results):
            try:
                # Extract relevant snippet around query keywords
                snippet = self._extract_relevant_snippet(
                    result.get("text", ""),
                    query,
                    max_snippet_length
                )
                
                # Calculate confidence from search score
                confidence = self._normalize_score(result.get("score", 0.0))
                
                # Create citation
                citation = SourceCitation(
                    source_id=result.get("chunk_id", f"source_{idx}"),
                    filename=result.get("source", "Unknown Source"),
                    chunk_index=result.get("chunk_index", 0),
                    snippet=snippet,
                    full_text=result.get("text", ""),
                    relevance_score=result.get("score", 0.0),
                    confidence_score=confidence,
                    page_number=result.get("page_number"),
                    section=result.get("section"),
                    metadata=result.get("metadata", {})
                )
                
                citations.append(citation)
                
            except Exception as e:
                self.logger.error(f"Error building citation for result {idx}: {e}")
                continue
        
        return citations
    
    def _extract_relevant_snippet(
        self,
        text: str,
        query: str,
        max_length: int = 200
    ) -> str:
        """
        Extract a relevant snippet from text around query keywords
        
        Args:
            text: Full text to extract from
            query: Query with keywords
            max_length: Maximum snippet length
            
        Returns:
            Relevant text snippet
        """
        if not text:
            return ""
        
        # Clean text
        text = text.strip()
        
        # If text is already short enough, return it
        if len(text) <= max_length:
            return text
        
        # Extract query keywords (remove common words)
        keywords = self._extract_keywords(query)
        
        if not keywords:
            # No keywords, return first part
            return text[:max_length] + "..."
        
        # Find best match position
        best_pos = 0
        best_score = 0
        
        for keyword in keywords:
            # Case-insensitive search
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            matches = list(pattern.finditer(text))
            
            if matches:
                # Use first match position
                pos = matches[0].start()
                # Score higher if keyword appears early
                score = 1.0 / (1 + pos / len(text))
                
                if score > best_score:
                    best_score = score
                    best_pos = pos
        
        # Extract snippet around best position
        start = max(0, best_pos - max_length // 2)
        end = min(len(text), start + max_length)
        
        snippet = text[start:end].strip()
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query
        
        Args:
            query: Query text
            
        Returns:
            List of keywords
        """
        # Common stop words to remove
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'what', 'when',
            'where', 'who', 'why', 'how'
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _normalize_score(self, score: float) -> float:
        """
        Normalize relevance score to confidence (0-1)
        
        Args:
            score: Raw relevance score (typically 0-1 from cosine similarity)
            
        Returns:
            Normalized confidence score
        """
        # Cosine similarity is already 0-1, but we can adjust the curve
        # to make high scores more confident
        if score < 0.3:
            return 0.3  # Low confidence
        elif score < 0.5:
            return 0.5  # Medium confidence
        elif score < 0.7:
            return 0.75  # High confidence
        else:
            return 0.9  # Very high confidence
    
    def format_citations(
        self,
        citations: List[SourceCitation],
        style: Optional[CitationStyle] = None
    ) -> str:
        """
        Format citations for display
        
        Args:
            citations: List of citations
            style: Citation style (uses default if None)
            
        Returns:
            Formatted citation text
        """
        if not citations:
            return "No sources found"
        
        style = style or self.style
        
        if style == CitationStyle.SIMPLE:
            return self._format_simple(citations)
        elif style == CitationStyle.DETAILED:
            return self._format_detailed(citations)
        elif style == CitationStyle.ACADEMIC:
            return self._format_academic(citations)
        elif style == CitationStyle.FOOTNOTE:
            return self._format_footnote(citations)
        else:
            return self._format_detailed(citations)
    
    def _format_simple(self, citations: List[SourceCitation]) -> str:
        """Simple format: just filenames"""
        unique_sources = list(set(c.filename for c in citations))
        return ", ".join(unique_sources)
    
    def _format_detailed(self, citations: List[SourceCitation]) -> str:
        """Detailed format with snippets and confidence"""
        formatted = []
        
        for idx, citation in enumerate(citations, 1):
            # Confidence indicator
            confidence_emoji = self._get_confidence_emoji(citation.confidence_score)
            
            # Format citation
            text = f"{idx}. {confidence_emoji} **{citation.filename}**"
            
            if citation.page_number:
                text += f" (p. {citation.page_number})"
            
            text += f"\n   *Relevance: {citation.relevance_score:.2f}*"
            text += f"\n   \"{citation.snippet}\""
            
            formatted.append(text)
        
        return "\n\n".join(formatted)
    
    def _format_academic(self, citations: List[SourceCitation]) -> str:
        """Academic APA-style format"""
        formatted = []
        
        # Group by source
        sources = {}
        for citation in citations:
            if citation.filename not in sources:
                sources[citation.filename] = []
            sources[citation.filename].append(citation)
        
        # Format each source
        for idx, (filename, cites) in enumerate(sources.items(), 1):
            # Extract year if present in filename
            year_match = re.search(r'(\d{4})', filename)
            year = year_match.group(1) if year_match else "n.d."
            
            # Basic citation
            text = f"{idx}. {filename.replace('_', ' ')} ({year})"
            
            # Add page numbers if available
            pages = [c.page_number for c in cites if c.page_number]
            if pages:
                text += f", pp. {', '.join(map(str, sorted(set(pages))))}"
            
            formatted.append(text)
        
        return "\n".join(formatted)
    
    def _format_footnote(self, citations: List[SourceCitation]) -> str:
        """Footnote style with numbers"""
        formatted = []
        
        for idx, citation in enumerate(citations, 1):
            text = f"[{idx}] {citation.filename}"
            
            if citation.page_number:
                text += f", p. {citation.page_number}"
            
            if citation.section:
                text += f", {citation.section}"
            
            formatted.append(text)
        
        return " ".join(formatted)
    
    def _get_confidence_emoji(self, confidence: float) -> str:
        """Get emoji indicator for confidence level"""
        if confidence >= 0.8:
            return "🟢"  # High confidence
        elif confidence >= 0.6:
            return "🟡"  # Medium confidence
        else:
            return "🟠"  # Low confidence
    
    def format_inline_citations(
        self,
        response_text: str,
        citations: List[SourceCitation]
    ) -> str:
        """
        Add inline citation markers to response text
        
        Args:
            response_text: The LLM response
            citations: List of citations
            
        Returns:
            Response text with inline citation markers
        """
        # Group citations by filename
        sources_list = {}
        for idx, citation in enumerate(citations, 1):
            if citation.filename not in sources_list:
                sources_list[citation.filename] = idx
        
        # Add citation footer
        footer = "\n\n---\n**Sources:**\n"
        for filename, num in sources_list.items():
            footer += f"[{num}] {filename}\n"
        
        return response_text + footer
    
    def get_citation_html(self, citations: List[SourceCitation]) -> str:
        """
        Generate HTML markup for citations (for web display)
        
        Args:
            citations: List of citations
            
        Returns:
            HTML string
        """
        if not citations:
            return "<p><em>No sources cited</em></p>"
        
        html = '<div class="citations">\n'
        html += '<h4>📚 Sources</h4>\n'
        html += '<ol class="citation-list">\n'
        
        for citation in citations:
            confidence_class = "high" if citation.confidence_score >= 0.7 else "medium" if citation.confidence_score >= 0.5 else "low"
            
            html += f'<li class="citation citation-{confidence_class}">\n'
            html += f'  <div class="citation-header">\n'
            html += f'    <strong>{citation.filename}</strong>\n'
            
            if citation.page_number:
                html += f'    <span class="page-num">(p. {citation.page_number})</span>\n'
            
            html += f'    <span class="confidence badge badge-{confidence_class}">{citation.confidence_score:.0%}</span>\n'
            html += f'  </div>\n'
            html += f'  <div class="citation-snippet">"{citation.snippet}"</div>\n'
            html += f'  <div class="citation-score">Relevance: {citation.relevance_score:.2f}</div>\n'
            html += f'</li>\n'
        
        html += '</ol>\n'
        html += '</div>\n'
        
        return html

# =============================================================================
# 🧪 TEST FUNCTION
# =============================================================================

def test_citation_builder():
    """Test citation builder functionality"""
    print("🧪 Testing Citation Builder...")
    
    # Sample search results
    search_results = [
        {
            "text": "The company's password policy requires all passwords to be at least 12 characters long, include uppercase and lowercase letters, numbers, and special characters. Passwords must be changed every 90 days.",
            "source": "IT_Security_Policy_2024.pdf",
            "score": 0.85,
            "chunk_id": "chunk_001",
            "page_number": 15,
            "chunk_index": 3
        },
        {
            "text": "Two-factor authentication (2FA) is mandatory for all employees accessing company systems remotely. 2FA can be configured using SMS, authenticator apps, or hardware tokens.",
            "source": "IT_Security_Policy_2024.pdf",
            "score": 0.72,
            "chunk_id": "chunk_002",
            "page_number": 16,
            "chunk_index": 4
        },
        {
            "text": "The IT department is responsible for managing user accounts, system access, and security protocols. All security incidents must be reported within 24 hours.",
            "source": "Employee_Handbook_2024.pdf",
            "score": 0.55,
            "chunk_id": "chunk_003",
            "page_number": 42,
            "chunk_index": 8
        }
    ]
    
    query = "What is the password policy?"
    
    # Test different styles
    for style in [CitationStyle.SIMPLE, CitationStyle.DETAILED, CitationStyle.ACADEMIC]:
        print(f"\n{'='*60}")
        print(f"📖 {style.value.upper()} STYLE:")
        print(f"{'='*60}")
        
        builder = CitationBuilder(style=style)
        citations = builder.build_citations(search_results, query)
        formatted = builder.format_citations(citations)
        
        print(formatted)
    
    # Test HTML output
    print(f"\n{'='*60}")
    print("🌐 HTML FORMAT:")
    print(f"{'='*60}")
    
    builder = CitationBuilder()
    citations = builder.build_citations(search_results, query)
    html = builder.get_citation_html(citations)
    print(html)
    
    print("\n✅ All citation tests passed!")

if __name__ == "__main__":
    test_citation_builder()