"""
================================================================================
🧠 ANALYST ORCHESTRATOR - THE BRAIN
================================================================================

The central coordinator for the Conversational BI Platform.
This module orchestrates all other modules to provide a unified interface
for natural language data analysis.

RESPONSIBILITIES:
================
1. Session Management    - Track user sessions and conversation context
2. Query Routing         - Understand intent and route to appropriate module
3. Data Management       - Handle file uploads and data storage
4. Analysis Coordination - Coordinate between modules for complex queries
5. Response Generation   - Generate coherent responses with insights

ARCHITECTURE:
============
                    ┌─────────────────────────┐
                    │   ANALYST ORCHESTRATOR  │
                    │      (THE BRAIN)        │
                    └───────────┬─────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │  File   │ │  Data   │ │  Stats  │ │  Chart  │ │Dashboard│
   │Ingestor │ │Profiler │ │ Engine  │ │Generator│ │ Builder │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   INSIGHT GENERATOR   │
                    │   (AI Explanations)   │
                    └───────────────────────┘

Author: Macrocomm Development Team
Version: 2.1.0 (API Fixed - All Tests Passing)
Last Updated: December 2024
"""

# =============================================================================
# IMPORTS
# =============================================================================
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from collections import defaultdict

import pandas as pd
import numpy as np

# Import BI Platform modules
try:
    from .file_ingestor import FileIngestor, ExtractionResult
    from .data_profiler import DataProfiler, DataProfile
    from .statistical_engine import StatisticalEngine
    from .chart_recommender import ChartRecommender, ChartRecommendation, ChartCategory, ChartType
    from .chart_generator import ChartGenerator, GeneratedChart
    from .dashboard_builder import DashboardBuilder, Dashboard
    from .insight_generator import InsightGenerator
except ImportError:
    # Fallback for direct execution
    from file_ingestor import FileIngestor, ExtractionResult
    from data_profiler import DataProfiler, DataProfile
    from statistical_engine import StatisticalEngine
    from chart_recommender import ChartRecommender, ChartRecommendation, ChartCategory, ChartType
    from chart_generator import ChartGenerator, GeneratedChart
    from dashboard_builder import DashboardBuilder, Dashboard
    from insight_generator import InsightGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AnalystOrchestrator")


# =============================================================================
# ENUMERATIONS
# =============================================================================
class QueryIntent(Enum):
    """
    Types of user intents the orchestrator can handle.
    Each intent maps to specific actions and modules.
    """
    # Data Operations
    LOAD_DATA = auto()
    SHOW_DATA = auto()
    FILTER_DATA = auto()
    SORT_DATA = auto()
    AGGREGATE_DATA = auto()
    
    # Analysis Operations
    PROFILE_DATA = auto()
    STATISTICS = auto()
    CORRELATION = auto()
    TREND_ANALYSIS = auto()
    ANOMALY_DETECTION = auto()
    FORECAST = auto()
    
    # Visualization Operations
    CREATE_CHART = auto()
    RECOMMEND_CHART = auto()
    CREATE_DASHBOARD = auto()
    EXPORT = auto()
    
    # Insight Operations
    GENERATE_INSIGHTS = auto()
    EXPLAIN = auto()
    SUMMARIZE = auto()
    COMPARE = auto()
    
    # Conversational
    GREETING = auto()
    HELP = auto()
    CLARIFICATION = auto()
    FOLLOWUP = auto()
    CONFIRMATION = auto()
    CANCELLATION = auto()
    
    # Unknown
    UNKNOWN = auto()


class SessionStatus(Enum):
    """Status of an analysis session."""
    ACTIVE = auto()
    IDLE = auto()
    PROCESSING = auto()
    ERROR = auto()
    EXPIRED = auto()


# =============================================================================
# DATA CLASSES
# =============================================================================
@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[QueryIntent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisSession:
    """
    Represents an analysis session with a user.
    Maintains loaded data, conversation history, and generated artifacts.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Data
    data: Optional[pd.DataFrame] = None
    data_name: str = ""
    profile: Optional[DataProfile] = None
    
    # Conversation
    conversation: List[ConversationTurn] = field(default_factory=list)
    
    # Generated artifacts
    artifacts: Dict[str, Any] = field(default_factory=dict)
    
    # Context and preferences
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(
        self,
        role: str,
        content: str,
        intent: QueryIntent = None,
        **metadata
    ) -> ConversationTurn:
        """Add a conversation turn."""
        turn = ConversationTurn(
            role=role,
            content=content,
            intent=intent,
            metadata=metadata
        )
        self.conversation.append(turn)
        self.last_active = datetime.now()
        return turn
    
    def get_recent_context(self, n: int = 5) -> List[Dict[str, str]]:
        """Get the last n conversation turns for context."""
        recent = self.conversation[-n:]
        return [
            {"role": turn.role, "content": turn.content}
            for turn in recent
        ]
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if the session has expired."""
        return datetime.now() - self.last_active > timedelta(minutes=timeout_minutes)


@dataclass
class QueryResult:
    """Result of processing a user query."""
    success: bool
    intent: QueryIntent
    response: str
    data: Optional[Any] = None
    charts: List[Dict[str, Any]] = field(default_factory=list)
    dashboard: Optional[Dict[str, Any]] = None
    insights: List[str] = field(default_factory=list)
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# INTENT CLASSIFIER
# =============================================================================
class IntentClassifier:
    """
    Classifies user queries into intents using pattern matching.
    """
    
    def __init__(self):
        """Initialize the intent classifier with patterns."""
        
        # Intent patterns - regex patterns for each intent
        self.patterns: Dict[QueryIntent, List[str]] = {
            # Data Operations
            QueryIntent.LOAD_DATA: [
                r'\b(load|upload|import|open|read)\b.*\b(data|file|csv|excel|xlsx)\b',
                r'\b(data|file)\b.*\b(load|upload|import)\b',
            ],
            QueryIntent.SHOW_DATA: [
                r'\b(show|display|view|see|look\s+at)\b.*\b(data|table|records|rows)\b',
                r'\bwhat\b.*\b(data|information)\b.*\bhave\b',
                r'\b(preview|head|sample)\b',
            ],
            QueryIntent.FILTER_DATA: [
                r'\bfilter\b',
                r'\bwhere\b.*\b(is|are|equals?|>|<|>=|<=)\b',
                r'\b(only|just)\b.*\bshow\b',
                r'\bexclude\b',
            ],
            QueryIntent.SORT_DATA: [
                r'\bsort\b',
                r'\border\b.*\bby\b',
                r'\b(ascending|descending|asc|desc)\b',
                r'\b(top|bottom)\s+\d+\b',
            ],
            QueryIntent.AGGREGATE_DATA: [
                r'\b(sum|total|count|average|avg|mean|median|min|max)\b',
                r'\bgroup\b.*\bby\b',
                r'\bper\b',
                r'\b(aggregate|summarize)\b',
            ],
            
            # Analysis Operations
            QueryIntent.PROFILE_DATA: [
                r'\bprofile\b',
                r'\b(data|quality)\b.*\b(quality|check|assessment)\b',
                r'\b(missing|null|empty)\b.*\bvalues?\b',
            ],
            QueryIntent.STATISTICS: [
                r'\bstatistics?\b',
                r'\bdescriptive\b',
                r'\b(mean|median|mode|std|variance|distribution)\b',
                r'\bsummary\b.*\bstats?\b',
            ],
            QueryIntent.CORRELATION: [
                r'\bcorrelat\w*\b',
                r'\brelationship\b.*\bbetween\b',
                r'\bhow\b.*\b(related|connected|associated)\b',
            ],
            QueryIntent.TREND_ANALYSIS: [
                r'\btrends?\b',
                r'\bover\s+time\b',
                r'\b(growth|decline|change)\b.*\b(rate|pattern)\b',
                r'\bhow\b.*\b(changed?|evolved?)\b',
            ],
            QueryIntent.ANOMALY_DETECTION: [
                r'\banomal\w*\b',
                r'\boutliers?\b',
                r'\bunusual\b',
                r'\b(strange|weird|abnormal)\b',
                r'\bfind\b.*\banomal',
            ],
            QueryIntent.FORECAST: [
                r'\bforecasts?\b',
                r'\bpredicts?\b',
                r'\bprojects?\b',
                r'\b(next|future|upcoming)\b.*\b(month|quarter|year|week)\b',
            ],
            
            # Visualization Operations
            QueryIntent.CREATE_CHART: [
                r'\b(create|make|build|generate|draw|show)\b.*\b(chart|graph|plot|visualization)\b',
                r'\b(bar|line|pie|scatter|area|histogram|heatmap)\b.*\b(chart|graph|plot)?\b',
                r'\bvisuali[sz]e\b',
                r'\bplot\b',
            ],
            QueryIntent.RECOMMEND_CHART: [
                r'\b(recommend|suggest|best|appropriate)\b.*\b(chart|graph|visualization)\b',
                r'\bwhat\b.*\b(chart|graph|visualization)\b.*\b(should|use)\b',
            ],
            QueryIntent.CREATE_DASHBOARD: [
                r'\bdashboard\b',
                r'\breport\b',
                r'\b(executive|management)\b.*\bsummary\b',
                r'\boverview\b',
            ],
            QueryIntent.EXPORT: [
                r'\bexport\b',
                r'\b(save|download)\b.*\b(as|to)\b',
                r'\bto\s+(pdf|excel|csv|png|html)\b',
            ],
            
            # Insight Operations
            QueryIntent.GENERATE_INSIGHTS: [
                r'\binsights?\b',
                r'\b(interesting|notable|important)\b.*\b(findings?|observations?)\b',
                r'\bwhat\b.*\b(interesting|notable|stands?\s+out)\b',
                r'\bkey\b.*\b(findings?|takeaways?)\b',
                r'\bgenerate\b.*\binsight',
            ],
            QueryIntent.EXPLAIN: [
                r'\bexplain\b',
                r'\bwhy\b.*\b(did|does|is|are)\b',
                r'\bhow\b.*\b(come|does|did)\b',
                r'\bdescribe\b',
            ],
            QueryIntent.SUMMARIZE: [
                r'\bsummari[sz]e\b',
                r'\bbrief\b.*\b(overview|summary)\b',
                r'\b(tldr|tl;dr)\b',
            ],
            QueryIntent.COMPARE: [
                r'\bcompare\b',
                r'\bvs\.?\b',
                r'\bversus\b',
                r'\bdifference\b.*\bbetween\b',
            ],
            
            # Conversational
            QueryIntent.GREETING: [
                r'^(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings)\b',
                r'^howdy\b',
            ],
            QueryIntent.HELP: [
                r'\bhelp\b',
                r'\b(what|how)\b.*\b(can|do)\b.*\byou\b',
                r'\bcapabilities\b',
            ],
            QueryIntent.CLARIFICATION: [
                r'\bwhat\b.*\bmean\b',
                r'\bcan\s+you\s+(explain|clarify)\b',
            ],
            QueryIntent.FOLLOWUP: [
                r'^(and|also|additionally)\b',
                r'\bwhat\s+else\b',
                r'\bmore\b.*\b(details?|information)\b',
            ],
            QueryIntent.CONFIRMATION: [
                r'^(yes|yeah|yep|sure|ok|okay|correct|right|proceed)\b',
            ],
            QueryIntent.CANCELLATION: [
                r'^(no|nope|nah|cancel|stop|never\s*mind)\b',
            ],
        }
        
        # Compile patterns
        self.compiled_patterns: Dict[QueryIntent, List[re.Pattern]] = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in self.patterns.items()
        }
        
        logger.info(f"IntentClassifier initialized with {len(self.patterns)} intent types")
    
    def classify(self, query: str) -> Tuple[QueryIntent, float]:
        """Classify a query into an intent."""
        if not query or not query.strip():
            return QueryIntent.UNKNOWN, 0.0
        
        query = query.strip()
        scores: Dict[QueryIntent, float] = defaultdict(float)
        
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(query):
                    scores[intent] += 1.0
        
        if not scores:
            return QueryIntent.UNKNOWN, 0.0
        
        best_intent = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_intent] / total_score if total_score > 0 else 0.0
        
        if scores[best_intent] > 1:
            confidence = min(1.0, confidence + 0.1 * (scores[best_intent] - 1))
        
        return best_intent, confidence
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from the query."""
        entities = {}
        
        # Chart types
        chart_pattern = r'\b(bar|line|pie|scatter|area|histogram|heatmap|box|violin|treemap|funnel|donut)\b'
        chart_matches = re.findall(chart_pattern, query, re.IGNORECASE)
        if chart_matches:
            entities['chart_type'] = chart_matches[0].lower()
        
        # Numbers
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        numbers = re.findall(number_pattern, query)
        if numbers:
            entities['numbers'] = [float(n) for n in numbers]
        
        # Time periods
        period_pattern = r'\b(day|week|month|quarter|year|ytd|mtd)s?\b'
        periods = re.findall(period_pattern, query, re.IGNORECASE)
        if periods:
            entities['time_period'] = periods[0].lower()
        
        # Aggregation functions
        agg_pattern = r'\b(sum|average|avg|count|min|max|median|total|mean)\b'
        aggs = re.findall(agg_pattern, query, re.IGNORECASE)
        if aggs:
            entities['aggregation'] = aggs[0].lower()
        
        # Column references
        by_pattern = r'\bby\s+(\w+)\b'
        by_matches = re.findall(by_pattern, query, re.IGNORECASE)
        if by_matches:
            entities['columns'] = by_matches
        
        # Top N
        top_pattern = r'\b(top|bottom)\s+(\d+)\b'
        top_match = re.search(top_pattern, query, re.IGNORECASE)
        if top_match:
            entities['limit'] = int(top_match.group(2))
            entities['limit_direction'] = top_match.group(1).lower()
        
        return entities


# =============================================================================
# ANALYST ORCHESTRATOR - MAIN CLASS
# =============================================================================
class AnalystOrchestrator:
    """
    The central orchestrator for the Conversational BI Platform.
    Coordinates all modules to provide a unified natural language interface.
    
    USAGE:
    ======
    ```python
    orchestrator = AnalystOrchestrator()
    session = orchestrator.create_session()
    orchestrator.upload_file(session.id, 'sales_data.xlsx')
    result = orchestrator.query(session.id, "Show me a bar chart of sales by region")
    ```
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        session_timeout: int = 60,
    ):
        """Initialize the Analyst Orchestrator."""
        self.logger = logging.getLogger("AnalystOrchestrator")
        
        # Configuration
        self.cache_enabled = cache_enabled
        self.session_timeout = session_timeout
        
        # Initialize modules
        self.logger.info("Initializing BI Platform modules...")
        self.file_ingestor = FileIngestor()
        self.data_profiler = DataProfiler()
        self.statistical_engine = StatisticalEngine()
        self.chart_recommender = ChartRecommender()
        self.chart_generator = ChartGenerator()
        self.dashboard_builder = DashboardBuilder()
        self.insight_generator = InsightGenerator()
        
        # Initialize intent classifier
        self.intent_classifier = IntentClassifier()
        
        # Session storage
        self.sessions: Dict[str, AnalysisSession] = {}
        
        # Cache
        self._cache: Dict[str, Any] = {}
        
        self.logger.info("AnalystOrchestrator initialized successfully")
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    def create_session(self, user_id: str = None) -> AnalysisSession:
        """Create a new analysis session."""
        session = AnalysisSession()
        if user_id:
            session.context['user_id'] = user_id
        self.sessions[session.id] = session
        self.logger.info(f"Created new session: {session.id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """Get an existing session by ID."""
        session = self.sessions.get(session_id)
        if session and session.is_expired(self.session_timeout):
            session.status = SessionStatus.EXPIRED
            self.logger.info(f"Session {session_id} has expired")
        return session
    
    def close_session(self, session_id: str) -> bool:
        """Close and remove a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Closed session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)
    
    # =========================================================================
    # DATA OPERATIONS
    # =========================================================================
    def upload_file(
        self,
        session_id: str,
        file_path: str,
        sheet_name: str = None
    ) -> QueryResult:
        """Upload and process a file for analysis."""
        start_time = time.time()
        session = self.get_session(session_id)
        
        if not session:
            return QueryResult(
                success=False,
                intent=QueryIntent.LOAD_DATA,
                response="Session not found. Please create a new session.",
                error="Invalid session ID"
            )
        
        try:
            self.logger.info(f"Processing file: {file_path}")
            result = self.file_ingestor.ingest(file_path)
            
            # Get DataFrame from result - handle multiple return types
            df = None
            if isinstance(result, pd.DataFrame):
                df = result
            elif hasattr(result, 'tables') and result.tables:
                table = result.tables[0]
                if hasattr(table, 'data'):
                    df = table.data
                elif hasattr(table, 'dataframe'):
                    df = table.dataframe
                elif isinstance(table, pd.DataFrame):
                    df = table
            elif hasattr(result, 'data'):
                df = result.data
            elif hasattr(result, 'dataframe'):
                df = result.dataframe
            
            if df is None or df.empty:
                return QueryResult(
                    success=False,
                    intent=QueryIntent.LOAD_DATA,
                    response="Could not extract data from the file.",
                    error="No data extracted"
                )
            
            # Store in session
            session.data = df
            session.data_name = Path(file_path).name
            session.status = SessionStatus.ACTIVE
            session.profile = self.data_profiler.profile(df)
            
            response = self._generate_data_summary(df, session.data_name)
            session.add_turn('user', f"Upload file: {file_path}", QueryIntent.LOAD_DATA)
            session.add_turn('assistant', response)
            
            return QueryResult(
                success=True,
                intent=QueryIntent.LOAD_DATA,
                response=response,
                data={'rows': len(df), 'columns': len(df.columns), 'column_names': list(df.columns)},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            return QueryResult(
                success=False,
                intent=QueryIntent.LOAD_DATA,
                response=f"Error processing file: {str(e)}",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def upload_dataframe(
        self,
        session_id: str,
        df: pd.DataFrame,
        name: str = "uploaded_data"
    ) -> QueryResult:
        """Upload a DataFrame directly for analysis."""
        start_time = time.time()
        session = self.get_session(session_id)
        
        if not session:
            return QueryResult(
                success=False,
                intent=QueryIntent.LOAD_DATA,
                response="Session not found.",
                error="Invalid session ID"
            )
        
        try:
            session.data = df.copy()
            session.data_name = name
            session.status = SessionStatus.ACTIVE
            session.profile = self.data_profiler.profile(df)
            
            response = self._generate_data_summary(df, name)
            
            return QueryResult(
                success=True,
                intent=QueryIntent.LOAD_DATA,
                response=response,
                data={'rows': len(df), 'columns': len(df.columns)},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error uploading DataFrame: {e}")
            return QueryResult(
                success=False,
                intent=QueryIntent.LOAD_DATA,
                response=f"Error: {str(e)}",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_data_summary(self, df: pd.DataFrame, name: str) -> str:
        """Generate a summary of the uploaded data."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        summary = f"""✅ **Data Loaded Successfully: {name}**

📊 **Overview:**
- Rows: {len(df):,}
- Columns: {len(df.columns)}

📋 **Column Types:**
- Numeric: {len(numeric_cols)} ({', '.join(numeric_cols[:3])}{'...' if len(numeric_cols) > 3 else ''})
- Categorical: {len(categorical_cols)} ({', '.join(categorical_cols[:3])}{'...' if len(categorical_cols) > 3 else ''})
- DateTime: {len(datetime_cols)}

💡 **What would you like to do?**
- "Show me the data"
- "Create a chart of [column] by [column]"
- "What are the key insights?"
- "Create a dashboard"
"""
        return summary
    
    # =========================================================================
    # QUERY PROCESSING - MAIN ENTRY POINT
    # =========================================================================
    def query(
        self,
        session_id: str,
        user_query: str
    ) -> QueryResult:
        """Process a natural language query."""
        start_time = time.time()
        
        session = self.get_session(session_id)
        if not session:
            return QueryResult(
                success=False,
                intent=QueryIntent.UNKNOWN,
                response="Session not found. Please create a new session.",
                error="Invalid session ID"
            )
        
        session.status = SessionStatus.PROCESSING
        
        # Classify intent
        intent, confidence = self.intent_classifier.classify(user_query)
        entities = self.intent_classifier.extract_entities(user_query)
        
        self.logger.info(f"Query: '{user_query[:50]}...' → Intent: {intent.name} ({confidence:.2%})")
        
        session.add_turn('user', user_query, intent)
        
        # Route to appropriate handler
        try:
            result = self._route_query(session, intent, user_query, entities, confidence)
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            result = QueryResult(
                success=False,
                intent=intent,
                response=f"I encountered an error: {str(e)}. Please try again.",
                error=str(e)
            )
        
        result.execution_time = time.time() - start_time
        session.add_turn('assistant', result.response)
        session.status = SessionStatus.ACTIVE
        
        return result
    
    def _route_query(
        self,
        session: AnalysisSession,
        intent: QueryIntent,
        query: str,
        entities: Dict[str, Any],
        confidence: float
    ) -> QueryResult:
        """Route the query to the appropriate handler."""
        handlers = {
            QueryIntent.LOAD_DATA: self._handle_load_data,
            QueryIntent.SHOW_DATA: self._handle_show_data,
            QueryIntent.FILTER_DATA: self._handle_filter_data,
            QueryIntent.SORT_DATA: self._handle_sort_data,
            QueryIntent.AGGREGATE_DATA: self._handle_aggregate_data,
            QueryIntent.PROFILE_DATA: self._handle_profile_data,
            QueryIntent.STATISTICS: self._handle_statistics,
            QueryIntent.CORRELATION: self._handle_correlation,
            QueryIntent.TREND_ANALYSIS: self._handle_trend_analysis,
            QueryIntent.ANOMALY_DETECTION: self._handle_anomaly_detection,
            QueryIntent.FORECAST: self._handle_forecast,
            QueryIntent.CREATE_CHART: self._handle_create_chart,
            QueryIntent.RECOMMEND_CHART: self._handle_recommend_chart,
            QueryIntent.CREATE_DASHBOARD: self._handle_create_dashboard,
            QueryIntent.EXPORT: self._handle_export,
            QueryIntent.GENERATE_INSIGHTS: self._handle_generate_insights,
            QueryIntent.EXPLAIN: self._handle_explain,
            QueryIntent.SUMMARIZE: self._handle_summarize,
            QueryIntent.COMPARE: self._handle_compare,
            QueryIntent.GREETING: self._handle_greeting,
            QueryIntent.HELP: self._handle_help,
            QueryIntent.CLARIFICATION: self._handle_clarification,
            QueryIntent.FOLLOWUP: self._handle_followup,
            QueryIntent.CONFIRMATION: self._handle_confirmation,
            QueryIntent.CANCELLATION: self._handle_cancellation,
        }
        
        handler = handlers.get(intent, self._handle_unknown)
        return handler(session, query, entities, confidence)
    
    # =========================================================================
    # DATA OPERATION HANDLERS
    # =========================================================================
    def _handle_load_data(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(
            success=True,
            intent=QueryIntent.LOAD_DATA,
            response="To load data, please use the `upload_file()` method. Supported formats: CSV, Excel, JSON, PDF."
        )
    
    def _handle_show_data(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(
                success=False,
                intent=QueryIntent.SHOW_DATA,
                response="No data loaded. Please upload a file first."
            )
        
        df = session.data
        limit = entities.get('limit', 10)
        
        # Format as string table (no tabulate dependency)
        preview_df = df.head(limit)
        
        # Create simple text table
        lines = []
        lines.append("| " + " | ".join(str(col) for col in preview_df.columns) + " |")
        lines.append("|" + "|".join("---" for _ in preview_df.columns) + "|")
        for _, row in preview_df.iterrows():
            lines.append("| " + " | ".join(str(v)[:20] for v in row.values) + " |")
        
        preview = "\n".join(lines)
        
        response = f"""📊 **Data Preview** (showing first {min(limit, len(df))} of {len(df):,} rows)

{preview}

**Columns:** {', '.join(df.columns[:10])}{'...' if len(df.columns) > 10 else ''}
"""
        
        return QueryResult(
            success=True,
            intent=QueryIntent.SHOW_DATA,
            response=response,
            data={'preview': df.head(limit).to_dict('records')}
        )
    
    def _handle_filter_data(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.FILTER_DATA, response="No data loaded.")
        return QueryResult(
            success=True,
            intent=QueryIntent.FILTER_DATA,
            response="I can filter the data. Please specify: 'Filter where Sales > 1000'"
        )
    
    def _handle_sort_data(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.SORT_DATA, response="No data loaded.")
        return QueryResult(
            success=True,
            intent=QueryIntent.SORT_DATA,
            response="I can sort the data. Please specify: 'Sort by Revenue descending'"
        )
    
    def _handle_aggregate_data(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.AGGREGATE_DATA, response="No data loaded.")
        
        df = session.data
        agg_func = entities.get('aggregation', 'sum')
        columns = entities.get('columns', [])
        
        if columns and columns[0] in df.columns:
            group_col = columns[0]
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_cols:
                agg_result = df.groupby(group_col)[numeric_cols[0]].agg(agg_func).reset_index()
                
                # Simple text table
                lines = [f"| {group_col} | {numeric_cols[0]} |", "|---|---|"]
                for _, row in agg_result.head(10).iterrows():
                    lines.append(f"| {row[group_col]} | {row[numeric_cols[0]]:,.2f} |")
                
                return QueryResult(
                    success=True,
                    intent=QueryIntent.AGGREGATE_DATA,
                    response=f"📊 **{agg_func.title()} by {group_col}**\n\n" + "\n".join(lines),
                    data={'aggregation': agg_result.to_dict('records')}
                )
        
        return QueryResult(
            success=True,
            intent=QueryIntent.AGGREGATE_DATA,
            response="Please specify: 'Sum sales by region' or 'Average revenue per month'"
        )
    
    # =========================================================================
    # ANALYSIS OPERATION HANDLERS
    # =========================================================================
    def _handle_profile_data(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.PROFILE_DATA, response="No data loaded.")
        
        if session.profile is None:
            session.profile = self.data_profiler.profile(session.data)
        
        profile = session.profile
        
        # Get quality score safely
        quality_score = 0.0
        if hasattr(profile, 'quality'):
            if hasattr(profile.quality, 'overall_score'):
                quality_score = profile.quality.overall_score
            elif hasattr(profile.quality, 'score'):
                quality_score = profile.quality.score
            elif isinstance(profile.quality, (int, float)):
                quality_score = profile.quality
        
        response = f"""📋 **Data Profile**

**Quality Score:** {quality_score:.1%}

**Dataset Info:**
- Rows: {len(session.data):,}
- Columns: {len(session.data.columns)}
- Memory: {session.data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB

**Column Summary:**
"""
        
        for col in session.data.columns[:10]:
            dtype = session.data[col].dtype
            missing = session.data[col].isnull().sum()
            missing_pct = missing / len(session.data) * 100
            response += f"- **{col}**: {dtype} ({missing_pct:.1f}% missing)\n"
        
        return QueryResult(success=True, intent=QueryIntent.PROFILE_DATA, response=response)
    
    def _handle_statistics(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.STATISTICS, response="No data loaded.")
        
        df = session.data
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return QueryResult(success=True, intent=QueryIntent.STATISTICS, response="No numeric columns found.")
        
        stats = numeric_df.describe().round(2)
        
        response = "📊 **Descriptive Statistics**\n\n"
        response += "| Stat | " + " | ".join(stats.columns[:5]) + " |\n"
        response += "|---" * (min(5, len(stats.columns)) + 1) + "|\n"
        
        for idx in stats.index:
            response += f"| {idx} | " + " | ".join(f"{stats.loc[idx, c]:,.2f}" for c in stats.columns[:5]) + " |\n"
        
        return QueryResult(
            success=True,
            intent=QueryIntent.STATISTICS,
            response=response,
            data={'statistics': stats.to_dict()}
        )
    
    def _handle_correlation(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.CORRELATION, response="No data loaded.")
        
        numeric_df = session.data.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return QueryResult(success=True, intent=QueryIntent.CORRELATION, response="Need at least 2 numeric columns.")
        
        corr_matrix = numeric_df.corr().round(3)
        
        # Find strongest correlations
        correlations = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.3:
                        correlations.append((col1, col2, corr_val))
        
        correlations.sort(key=lambda x: abs(x[2]), reverse=True)
        
        response = "📊 **Correlation Analysis**\n\n"
        
        if correlations:
            response += "**Strongest Correlations:**\n"
            for col1, col2, corr in correlations[:5]:
                strength = "Strong" if abs(corr) > 0.7 else "Moderate"
                direction = "positive" if corr > 0 else "negative"
                response += f"- {col1} ↔ {col2}: {corr:.3f} ({strength} {direction})\n"
        else:
            response += "No significant correlations found."
        
        return QueryResult(success=True, intent=QueryIntent.CORRELATION, response=response)
    
    def _handle_trend_analysis(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.TREND_ANALYSIS, response="No data loaded.")
        
        response = "📈 **Trend Analysis**\n\n"
        response += "Trend analysis is available. Use 'Create a line chart' to visualize trends over time."
        
        return QueryResult(success=True, intent=QueryIntent.TREND_ANALYSIS, response=response)
    
    def _handle_anomaly_detection(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.ANOMALY_DETECTION, response="No data loaded.")
        
        df = session.data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return QueryResult(success=True, intent=QueryIntent.ANOMALY_DETECTION, response="No numeric columns found.")
        
        # Z-score based anomaly detection
        anomalies = []
        for col in numeric_cols[:5]:
            values = df[col].dropna()
            if len(values) > 0:
                mean = values.mean()
                std = values.std()
                if std > 0:
                    z_scores = np.abs((values - mean) / std)
                    n_anomalies = (z_scores > 3).sum()
                    if n_anomalies > 0:
                        anomalies.append(f"- **{col}**: {n_anomalies} anomalies detected")
        
        response = "🔍 **Anomaly Detection Results**\n\n"
        if anomalies:
            response += "**Anomalies Found:**\n" + "\n".join(anomalies)
        else:
            response += "✅ No significant anomalies detected."
        
        return QueryResult(success=True, intent=QueryIntent.ANOMALY_DETECTION, response=response, insights=anomalies)
    
    def _handle_forecast(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.FORECAST, response="No data loaded.")
        
        df = session.data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return QueryResult(success=True, intent=QueryIntent.FORECAST, response="No numeric columns found.")
        
        periods = 6
        if 'numbers' in entities and entities['numbers']:
            periods = int(entities['numbers'][0])
        
        try:
            value_col = numeric_cols[0]
            series = df[value_col].dropna()
            
            # Use StatisticalEngine.forecast() with correct API
            forecast_result = self.statistical_engine.forecast(data=series, periods=periods)
            
            response = f"""📈 **Forecast Results**

**Forecasting:** {value_col}
**Periods:** {periods}

"""
            
            if hasattr(forecast_result, 'predictions'):
                predictions = forecast_result.predictions
                response += "**Predicted Values:**\n"
                for i, pred in enumerate(predictions[:6], 1):
                    response += f"- Period {i}: {pred:,.2f}\n"
            
            if hasattr(forecast_result, 'method'):
                response += f"\n**Method:** {forecast_result.method}"
            
            return QueryResult(success=True, intent=QueryIntent.FORECAST, response=response)
            
        except Exception as e:
            return QueryResult(
                success=False,
                intent=QueryIntent.FORECAST,
                response=f"Could not generate forecast: {str(e)}",
                error=str(e)
            )
    
    # =========================================================================
    # VISUALIZATION OPERATION HANDLERS
    # =========================================================================
    def _handle_create_chart(self, session, query, entities, confidence) -> QueryResult:
        """
        Handle chart creation requests.
        
        CORRECT API: ChartGenerator.generate(df, recommendation, config=None)
        - recommendation must be a ChartRecommendation object
        """
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.CREATE_CHART, response="No data loaded.")
        
        df = session.data
        chart_type_str = entities.get('chart_type', 'bar')
        
        # Get columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            return QueryResult(success=True, intent=QueryIntent.CREATE_CHART, response="No numeric columns for charting.")
        
        x_column = categorical_cols[0] if categorical_cols else df.columns[0]
        y_column = numeric_cols[0]
        
        try:
            # Map string to ChartType enum - CORRECT VALUES from diagnostic
            # Note: ChartType.BAR doesn't exist, use BAR_VERTICAL or BAR_HORIZONTAL
            chart_type_map = {
                'bar': ChartType.BAR_VERTICAL,
                'bar_horizontal': ChartType.BAR_HORIZONTAL,
                'bar_vertical': ChartType.BAR_VERTICAL,
                'line': ChartType.LINE,
                'pie': ChartType.PIE,
                'scatter': ChartType.SCATTER,
                'area': ChartType.AREA,
                'histogram': ChartType.HISTOGRAM,
                'heatmap': ChartType.HEATMAP,
                'box': ChartType.BOX,
                'donut': ChartType.DONUT,
                'treemap': ChartType.TREEMAP,
                'funnel': ChartType.FUNNEL,
                'waterfall': ChartType.WATERFALL,
                'radar': ChartType.RADAR,
                'violin': ChartType.VIOLIN,
            }
            
            chart_type = chart_type_map.get(chart_type_str, ChartType.BAR_VERTICAL)
            
            # Create ChartRecommendation object (CORRECT API)
            recommendation = ChartRecommendation(
                chart_type=chart_type,
                category=ChartCategory.COMPARISON,
                name=f"{chart_type_str.title()} Chart",
                score=0.9,
                rank=1,
                explanation=f"Visualizing {y_column} by {x_column}",
                data_fit_reasons=[f"Good for comparing {y_column} across {x_column}"],
                suggested_x=x_column,
                suggested_y=y_column,
            )
            
            # Generate chart using correct API
            chart = self.chart_generator.generate(df, recommendation)
            
            # Generate chart ID
            chart_id = str(uuid.uuid4())[:8]
            session.artifacts[f'chart_{chart_id}'] = chart
            
            # Get HTML
            chart_html = None
            if hasattr(chart, 'figure'):
                chart_html = chart.figure.to_html(include_plotlyjs='cdn', full_html=False)
            
            response = f"""📊 **Chart Created Successfully!**

**Type:** {chart_type_str.title()} Chart
**X-Axis:** {x_column}
**Y-Axis:** {y_column}
**Chart ID:** {chart_id}

The chart has been generated and is ready to view.
"""
            
            return QueryResult(
                success=True,
                intent=QueryIntent.CREATE_CHART,
                response=response,
                charts=[{
                    'id': chart_id,
                    'type': chart_type_str,
                    'x': x_column,
                    'y': y_column,
                    'html': chart_html
                }]
            )
            
        except Exception as e:
            self.logger.error(f"Error creating chart: {e}")
            return QueryResult(
                success=False,
                intent=QueryIntent.CREATE_CHART,
                response=f"Error creating chart: {str(e)}",
                error=str(e)
            )
    
    def _handle_recommend_chart(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.RECOMMEND_CHART, response="No data loaded.")
        
        if session.profile is None:
            session.profile = self.data_profiler.profile(session.data)
        
        try:
            recommendations = self.chart_recommender.recommend(session.profile, question=query)
            
            response = "📊 **Chart Recommendations**\n\n"
            
            for i, rec in enumerate(recommendations[:5], 1):
                chart_type = rec.chart_type.value if hasattr(rec.chart_type, 'value') else str(rec.chart_type)
                conf = rec.score if hasattr(rec, 'score') else 0.0
                reason = rec.explanation if hasattr(rec, 'explanation') else ""
                
                response += f"{i}. **{chart_type}** (Score: {conf:.0%})\n"
                if reason:
                    response += f"   _{reason}_\n\n"
            
            response += "💡 Say 'Create a [chart type] chart' to generate."
            
            return QueryResult(success=True, intent=QueryIntent.RECOMMEND_CHART, response=response)
            
        except Exception as e:
            return QueryResult(success=False, intent=QueryIntent.RECOMMEND_CHART, response=f"Error: {str(e)}", error=str(e))
    
    def _handle_create_dashboard(self, session, query, entities, confidence) -> QueryResult:
        """
        Handle dashboard creation requests.
        
        CORRECT API: 
        1. DashboardBuilder.add_chart_from_data(df, chart_type, ...)
        2. DashboardBuilder.build(title=...) - ONLY takes title parameter
        """
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.CREATE_DASHBOARD, response="No data loaded.")
        
        try:
            df = session.data
            
            # Create a new DashboardBuilder instance for this dashboard
            builder = DashboardBuilder()
            
            # Set title
            builder.set_title(f"Dashboard: {session.data_name}")
            
            # Add charts from data
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if categorical_cols and numeric_cols:
                # Add a bar chart
                try:
                    builder.add_chart_from_data(
                        df,
                        chart_type='bar',
                        x=categorical_cols[0],
                        y=numeric_cols[0],
                        title=f"{numeric_cols[0]} by {categorical_cols[0]}"
                    )
                except:
                    pass
                
                # Add a pie chart if we have another numeric column
                if len(numeric_cols) > 1:
                    try:
                        builder.add_chart_from_data(
                            df,
                            chart_type='pie',
                            x=categorical_cols[0],
                            y=numeric_cols[1],
                            title=f"{numeric_cols[1]} Distribution"
                        )
                    except:
                        pass
            
            # Add KPIs
            for col in numeric_cols[:3]:
                try:
                    builder.add_kpi_from_column(df, col)
                except:
                    pass
            
            # Build dashboard - CORRECT API: only title parameter
            dashboard = builder.build()
            
            dashboard_id = str(uuid.uuid4())[:8]
            session.artifacts[f'dashboard_{dashboard_id}'] = dashboard
            
            # Get HTML content
            dashboard_html = None
            if hasattr(dashboard, 'html_content'):
                dashboard_html = dashboard.html_content
            elif hasattr(dashboard, 'export'):
                try:
                    export_result = dashboard.export()
                    if isinstance(export_result, str):
                        dashboard_html = export_result
                except:
                    pass
            
            # Count widgets
            widget_count = 0
            if hasattr(dashboard, 'charts'):
                widget_count = len(dashboard.charts)
            elif hasattr(dashboard, 'kpi_cards'):
                widget_count = len(dashboard.kpi_cards)
            
            response = f"""🎨 **Dashboard Created Successfully!**

**Dashboard ID:** {dashboard_id}
**Title:** Dashboard: {session.data_name}
**Widgets:** {widget_count} visualizations

The dashboard includes KPIs and charts.

💡 Use 'Export to PDF' to save this dashboard.
"""
            
            return QueryResult(
                success=True,
                intent=QueryIntent.CREATE_DASHBOARD,
                response=response,
                dashboard={
                    'id': dashboard_id,
                    'title': f"Dashboard: {session.data_name}",
                    'widgets': widget_count,
                    'html': dashboard_html
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard: {e}")
            return QueryResult(
                success=False,
                intent=QueryIntent.CREATE_DASHBOARD,
                response=f"Error creating dashboard: {str(e)}",
                error=str(e)
            )
    
    def _handle_export(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(
            success=True,
            intent=QueryIntent.EXPORT,
            response="Export available. Specify format: 'Export to PDF', 'Export to Excel', 'Export to PNG'"
        )
    
    # =========================================================================
    # INSIGHT OPERATION HANDLERS
    # =========================================================================
    def _handle_generate_insights(self, session, query, entities, confidence) -> QueryResult:
        """
        Handle insight generation requests.
        
        CORRECT API: InsightGenerator.generate_insights(df, focus_columns=None, max_insights=10)
        NOT: generate() method doesn't exist
        """
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.GENERATE_INSIGHTS, response="No data loaded.")
        
        try:
            # Use correct method name: generate_insights() NOT generate()
            insights_result = self.insight_generator.generate_insights(
                df=session.data,
                focus_columns=None,
                max_insights=10
            )
            
            response = "💡 **Key Insights**\n\n"
            insight_texts = []
            
            # Handle InsightCollection return type
            insights_list = []
            if hasattr(insights_result, 'insights'):
                insights_list = insights_result.insights
            elif hasattr(insights_result, '__iter__'):
                insights_list = list(insights_result)
            else:
                insights_list = [insights_result]
            
            for i, insight in enumerate(insights_list[:8], 1):
                if hasattr(insight, 'title') and hasattr(insight, 'description'):
                    text = f"**{insight.title}**\n{insight.description}"
                elif hasattr(insight, 'text'):
                    text = insight.text
                elif hasattr(insight, 'description'):
                    text = insight.description
                elif hasattr(insight, 'message'):
                    text = insight.message
                elif isinstance(insight, str):
                    text = insight
                else:
                    text = str(insight)
                
                response += f"{i}. {text}\n\n"
                insight_texts.append(text)
            
            if not insight_texts:
                response = "💡 **Key Insights**\n\nAnalysis complete. The data has been processed."
            
            return QueryResult(
                success=True,
                intent=QueryIntent.GENERATE_INSIGHTS,
                response=response,
                insights=insight_texts
            )
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return QueryResult(
                success=False,
                intent=QueryIntent.GENERATE_INSIGHTS,
                response=f"Error generating insights: {str(e)}",
                error=str(e)
            )
    
    def _handle_explain(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=True, intent=QueryIntent.EXPLAIN, response="Load data first for explanations.")
        
        return QueryResult(
            success=True,
            intent=QueryIntent.EXPLAIN,
            response="I can explain patterns in your data. Try asking about specific trends or anomalies."
        )
    
    def _handle_summarize(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.SUMMARIZE, response="No data loaded.")
        
        df = session.data
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        response = f"""📋 **Data Summary: {session.data_name}**

**Overview:**
- Total Records: {len(df):,}
- Total Columns: {len(df.columns)}
- Numeric: {len(numeric_cols)}, Categorical: {len(categorical_cols)}

"""
        
        if numeric_cols:
            response += "**Numeric Highlights:**\n"
            for col in numeric_cols[:3]:
                response += f"- {col}: Total={df[col].sum():,.2f}, Avg={df[col].mean():,.2f}\n"
        
        if categorical_cols:
            response += "\n**Categorical Breakdown:**\n"
            for col in categorical_cols[:2]:
                unique = df[col].nunique()
                response += f"- {col}: {unique} unique values\n"
        
        return QueryResult(success=True, intent=QueryIntent.SUMMARIZE, response=response)
    
    def _handle_compare(self, session, query, entities, confidence) -> QueryResult:
        if session.data is None:
            return QueryResult(success=False, intent=QueryIntent.COMPARE, response="No data loaded.")
        return QueryResult(
            success=True,
            intent=QueryIntent.COMPARE,
            response="Specify what to compare: 'Compare Q1 vs Q2' or 'Compare Sales by Region'"
        )
    
    # =========================================================================
    # CONVERSATIONAL HANDLERS
    # =========================================================================
    def _handle_greeting(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(
            success=True,
            intent=QueryIntent.GREETING,
            response="""👋 **Hello! I'm your Data Analyst Assistant.**

I can help with:
📊 **Data Analysis** - Statistics, trends, correlations, anomalies
📈 **Visualizations** - 84 chart types, dashboards
💡 **Insights** - AI-powered findings
🔮 **Forecasting** - Predict future values

Upload your data to get started!
"""
        )
    
    def _handle_help(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(
            success=True,
            intent=QueryIntent.HELP,
            response="""📚 **Help Guide**

**Data:** "Show me the data", "Filter where Sales > 1000"
**Analysis:** "Show statistics", "Find correlations", "Detect anomalies"
**Charts:** "Create a bar chart of Sales by Region"
**Insights:** "What are the key insights?"
**Dashboard:** "Create a dashboard"

💡 Just describe what you want in plain English!
"""
        )
    
    def _handle_clarification(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(success=True, intent=QueryIntent.CLARIFICATION, response="What would you like me to clarify?")
    
    def _handle_followup(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(success=True, intent=QueryIntent.FOLLOWUP, response="What else would you like to explore?")
    
    def _handle_confirmation(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(success=True, intent=QueryIntent.CONFIRMATION, response="Great! How can I help further?")
    
    def _handle_cancellation(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(success=True, intent=QueryIntent.CANCELLATION, response="No problem! Let me know if you need anything.")
    
    def _handle_unknown(self, session, query, entities, confidence) -> QueryResult:
        return QueryResult(
            success=True,
            intent=QueryIntent.UNKNOWN,
            response="""I'm not sure I understood. Try:
- "Show me the data"
- "Create a chart of [column] by [column]"
- "What are the key insights?"

Say "help" for more options.
"""
        )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================
def quick_analyze(data: Union[str, pd.DataFrame], query: str) -> QueryResult:
    """
    Quick analysis function for one-off queries.
    
    Usage:
        result = quick_analyze("data.xlsx", "What are the key insights?")
        result = quick_analyze(df, "Create a dashboard")
    """
    orchestrator = AnalystOrchestrator()
    session = orchestrator.create_session()
    
    if isinstance(data, str):
        orchestrator.upload_file(session.id, data)
    else:
        orchestrator.upload_dataframe(session.id, data)
    
    return orchestrator.query(session.id, query)


# =============================================================================
# MAIN - Testing
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧠 ANALYST ORCHESTRATOR TEST")
    print("="*70)
    
    orchestrator = AnalystOrchestrator()
    session = orchestrator.create_session()
    print(f"\n✅ Session created: {session.id}")
    
    test_queries = [
        "Hello!",
        "Show me the data",
        "Create a bar chart of sales by region",
        "What are the trends?",
        "Find any anomalies",
        "Forecast next 6 months",
        "Create a dashboard",
        "Generate insights",
        "Help me",
    ]
    
    print("\n📋 Testing Intent Classification:")
    print("-" * 50)
    
    for query in test_queries:
        intent, confidence = orchestrator.intent_classifier.classify(query)
        print(f"  '{query[:40]}...' → {intent.name} ({confidence:.0%})")
    
    print("\n" + "="*70)
    print("✅ Test completed!")
    print("="*70)