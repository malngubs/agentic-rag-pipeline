"""
📊 ANALYTICS & CONVERSATION DATABASE MODULE
===========================================
Stores conversation history, usage analytics, and cost tracking for the RAG system.

Features:
- Conversation history storage with full message tracking
- Query analytics and performance metrics
- OpenAI API cost tracking and budget monitoring
- Usage statistics and trends analysis
- Performance monitoring and optimization insights

Author: AI King @ Macrocomm
Version: 2.1 - Phase 1 Implementation
Date: November 2025
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid
from contextlib import contextmanager

# Setup logging
logger = logging.getLogger(__name__)

# =============================================================================
# 📋 DATA MODELS
# =============================================================================

@dataclass
class ConversationMessage:
    """
    Single message in a conversation
    Tracks both user queries and assistant responses with metadata
    """
    message_id: str
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    response_time: Optional[float] = None  # Time taken to generate response (seconds)
    using_rag: Optional[bool] = False  # Whether RAG was used
    context_found: Optional[int] = 0  # Number of context chunks found
    confidence: Optional[float] = None  # Response confidence score
    sources: Optional[List[str]] = None  # Source documents used

@dataclass
class QueryMetrics:
    """
    Comprehensive metrics for a single query
    Used for analytics, cost tracking, and performance monitoring
    """
    query_id: str
    conversation_id: str
    query_text: str
    response_text: str
    timestamp: datetime
    response_time: float  # Total response time in seconds
    using_rag: bool
    context_found: int
    confidence: float
    sources: List[str]
    input_tokens: int  # Tokens in prompt
    output_tokens: int  # Tokens in response
    cost: float  # Estimated cost in USD
    model_used: str  # LLM model identifier
    success: bool  # Whether query completed successfully
    error_message: Optional[str] = None

@dataclass
class AnalyticsSummary:
    """
    Summary statistics for analytics dashboard
    Provides high-level overview of system usage and performance
    """
    total_queries: int
    total_conversations: int
    avg_response_time: float
    total_cost: float
    success_rate: float
    most_asked_questions: List[Dict[str, Any]]
    popular_documents: List[Dict[str, Any]]
    queries_per_day: List[Dict[str, Any]]
    cost_per_day: List[Dict[str, Any]]
    avg_confidence: float
    rag_usage_rate: float

# =============================================================================
# 💰 COST CALCULATION UTILITIES
# =============================================================================

def calculate_openai_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """
    Calculate OpenAI API cost based on token usage
    
    Pricing (as of Nov 2024):
    - GPT-4o-mini: $0.150 per 1M input tokens, $0.600 per 1M output tokens
    - GPT-4o: $2.50 per 1M input tokens, $10.00 per 1M output tokens
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier
        
    Returns:
        Estimated cost in USD
    """
    # Pricing per million tokens
    pricing = {
        "gpt-4o-mini": {"input": 0.150, "output": 0.600},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4": {"input": 30.00, "output": 60.00},  # Legacy pricing
    }
    
    # Default to gpt-4o-mini if model not found
    model_key = "gpt-4o-mini"
    if "gpt-4o-mini" in model.lower():
        model_key = "gpt-4o-mini"
    elif "gpt-4o" in model.lower():
        model_key = "gpt-4o"
    elif "gpt-4" in model.lower():
        model_key = "gpt-4"
    
    rates = pricing.get(model_key, pricing["gpt-4o-mini"])
    
    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    
    return round(input_cost + output_cost, 6)

# =============================================================================
# 🗄️ ANALYTICS DATABASE CLASS
# =============================================================================

class AnalyticsDatabase:
    """
    SQLite-based analytics and conversation storage system
    
    Features:
    - Persistent conversation history
    - Query metrics and performance tracking
    - Cost tracking and budget monitoring
    - Analytics aggregation and reporting
    - Export capabilities
    
    Database Schema:
    - conversations: Stores conversation metadata
    - messages: Stores individual messages
    - query_metrics: Stores detailed query analytics
    - daily_stats: Aggregated daily statistics
    """
    
    def __init__(self, db_path: str = "analytics.db"):
        """
        Initialize database connection and create tables if needed
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self.logger.info(f"✅ Analytics database initialized: {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Create database schema if it doesn't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    tenant TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    metadata TEXT
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time REAL,
                    using_rag BOOLEAN,
                    context_found INTEGER,
                    confidence REAL,
                    sources TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)
            
            # Query metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_metrics (
                    query_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    query_text TEXT,
                    response_text TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    response_time REAL,
                    using_rag BOOLEAN,
                    context_found INTEGER,
                    confidence REAL,
                    sources TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cost REAL,
                    model_used TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)
            
            # Daily statistics table (for efficient aggregation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date DATE PRIMARY KEY,
                    total_queries INTEGER DEFAULT 0,
                    total_conversations INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    avg_response_time REAL DEFAULT 0.0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    rag_queries INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                ON messages(conversation_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON query_metrics(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_conversation 
                ON query_metrics(conversation_id)
            """)
            
            self.logger.info("✅ Database schema initialized")
    
    # =========================================================================
    # 💬 CONVERSATION METHODS
    # =========================================================================
    
    def create_conversation(self, conversation_id: str = None, user_id: str = None, 
                          tenant: str = "default") -> str:
        """
        Create a new conversation entry
        
        Args:
            conversation_id: Optional custom conversation ID
            user_id: User identifier
            tenant: Tenant/client identifier
            
        Returns:
            conversation_id: The created conversation ID
        """
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (conversation_id, user_id, tenant)
                VALUES (?, ?, ?)
            """, (conversation_id, user_id, tenant))
        
        self.logger.info(f"Created conversation: {conversation_id}")
        return conversation_id
    
    def add_message(self, message: ConversationMessage):
        """
        Add a message to the conversation history
        
        Args:
            message: ConversationMessage object
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert message
            cursor.execute("""
                INSERT INTO messages (
                    message_id, conversation_id, role, content, timestamp,
                    response_time, using_rag, context_found, confidence, sources
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.message_id,
                message.conversation_id,
                message.role,
                message.content,
                message.timestamp,
                message.response_time,
                message.using_rag,
                message.context_found,
                message.confidence,
                json.dumps(message.sources) if message.sources else None
            ))
            
            # Update conversation metadata
            cursor.execute("""
                UPDATE conversations
                SET last_message_at = ?,
                    message_count = message_count + 1
                WHERE conversation_id = ?
            """, (message.timestamp, message.conversation_id))
        
        self.logger.debug(f"Added {message.role} message to conversation {message.conversation_id}")
    
    def get_conversation_history(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve conversation history
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages as dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                msg = dict(row)
                if msg['sources']:
                    msg['sources'] = json.loads(msg['sources'])
                messages.append(msg)
            
            return messages
    
    def get_all_conversations(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get list of all conversations with metadata

        Args:
            limit: Number of conversations to retrieve
            offset: Offset for pagination

        Returns:
            List of conversation metadata dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations
                ORDER BY last_message_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return [dict(row) for row in cursor.fetchall()]

    def search_conversations(
        self,
        query: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search conversations by various criteria

        Args:
            query: Search term to find in message content
            conversation_id: Filter by conversation ID (partial match)
            user_id: Filter by user ID
            start_date: Start date for date range filter (ISO format)
            end_date: End date for date range filter (ISO format)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Dictionary with 'conversations' list and 'total' count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE conditions
            conditions = []
            params = []

            # Search in message content
            if query:
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM messages m
                        WHERE m.conversation_id = conversations.conversation_id
                        AND m.content LIKE ?
                    )
                """)
                params.append(f"%{query}%")

            # Filter by conversation ID (partial match)
            if conversation_id:
                conditions.append("conversations.conversation_id LIKE ?")
                params.append(f"%{conversation_id}%")

            # Filter by user ID
            if user_id:
                conditions.append("conversations.user_id = ?")
                params.append(user_id)

            # Filter by date range
            if start_date:
                conditions.append("conversations.last_message_at >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("conversations.last_message_at <= ?")
                params.append(end_date)

            # Build the WHERE clause
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM conversations
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Get conversations
            query_sql = f"""
                SELECT * FROM conversations
                WHERE {where_clause}
                ORDER BY last_message_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor.execute(query_sql, params)

            conversations = [dict(row) for row in cursor.fetchall()]

            return {
                'conversations': conversations,
                'total': total,
                'limit': limit,
                'offset': offset
            }
    
    def export_conversation(self, conversation_id: str, format: str = "json") -> str:
        """
        Export conversation to JSON or CSV format
        
        Args:
            conversation_id: Conversation to export
            format: 'json' or 'csv'
            
        Returns:
            Formatted conversation data
        """
        messages = self.get_conversation_history(conversation_id)
        
        if format == "json":
            return json.dumps(messages, indent=2, default=str)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if messages:
                writer = csv.DictWriter(output, fieldnames=messages[0].keys())
                writer.writeheader()
                writer.writerows(messages)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    # =========================================================================
    # 📊 METRICS METHODS
    # =========================================================================
    
    def record_query_metrics(self, metrics: QueryMetrics):
        """
        Record comprehensive metrics for a query
        
        Args:
            metrics: QueryMetrics object with all query details
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert query metrics
            cursor.execute("""
                INSERT INTO query_metrics (
                    query_id, conversation_id, query_text, response_text,
                    timestamp, response_time, using_rag, context_found,
                    confidence, sources, input_tokens, output_tokens,
                    cost, model_used, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.query_id,
                metrics.conversation_id,
                metrics.query_text,
                metrics.response_text,
                metrics.timestamp,
                metrics.response_time,
                metrics.using_rag,
                metrics.context_found,
                metrics.confidence,
                json.dumps(metrics.sources),
                metrics.input_tokens,
                metrics.output_tokens,
                metrics.cost,
                metrics.model_used,
                metrics.success,
                metrics.error_message
            ))
            
            # Update conversation cost
            cursor.execute("""
                UPDATE conversations
                SET total_cost = total_cost + ?
                WHERE conversation_id = ?
            """, (metrics.cost, metrics.conversation_id))
            
            # Update daily stats
            date = metrics.timestamp.date()
            cursor.execute("""
                INSERT INTO daily_stats (
                    date, total_queries, total_cost, avg_response_time,
                    success_count, failure_count, total_input_tokens,
                    total_output_tokens, rag_queries
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_queries = total_queries + 1,
                    total_cost = total_cost + ?,
                    avg_response_time = (avg_response_time * total_queries + ?) / (total_queries + 1),
                    success_count = success_count + ?,
                    failure_count = failure_count + ?,
                    total_input_tokens = total_input_tokens + ?,
                    total_output_tokens = total_output_tokens + ?,
                    rag_queries = rag_queries + ?
            """, (
                date,
                metrics.cost,
                metrics.response_time,
                1 if metrics.success else 0,
                0 if metrics.success else 1,
                metrics.input_tokens,
                metrics.output_tokens,
                1 if metrics.using_rag else 0,
                # UPDATE values
                metrics.cost,
                metrics.response_time,
                1 if metrics.success else 0,
                0 if metrics.success else 1,
                metrics.input_tokens,
                metrics.output_tokens,
                1 if metrics.using_rag else 0
            ))
        
        self.logger.debug(f"Recorded metrics for query {metrics.query_id}")
    
    # =========================================================================
    # 📈 ANALYTICS METHODS
    # =========================================================================
    
    def get_analytics_summary(self, days: int = 30) -> AnalyticsSummary:
        """
        Get comprehensive analytics summary for dashboard
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            AnalyticsSummary object with all metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Overall metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    AVG(response_time) as avg_response_time,
                    SUM(cost) as total_cost,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    SUM(CASE WHEN using_rag THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as rag_usage_rate
                FROM query_metrics
                WHERE timestamp >= ?
            """, (cutoff_date,))
            
            overall = cursor.fetchone()
            
            # Total conversations
            cursor.execute("""
                SELECT COUNT(*) FROM conversations
                WHERE started_at >= ?
            """, (cutoff_date,))
            
            total_conversations = cursor.fetchone()[0]
            
            # Most asked questions (using fuzzy grouping by first 50 chars)
            cursor.execute("""
                SELECT 
                    SUBSTR(query_text, 1, 100) as question,
                    COUNT(*) as frequency,
                    AVG(confidence) as avg_confidence
                FROM query_metrics
                WHERE timestamp >= ? AND success = 1
                GROUP BY SUBSTR(query_text, 1, 100)
                ORDER BY frequency DESC
                LIMIT 10
            """, (cutoff_date,))
            
            most_asked = [dict(row) for row in cursor.fetchall()]
            
            # Popular documents (fallback: aggregate sources in Python to avoid sqlite json1 dependency / malformed JSON)
            cursor.execute("""
                SELECT sources
                FROM query_metrics
                WHERE timestamp >= ? AND sources IS NOT NULL AND TRIM(sources) != ''
            """, (cutoff_date,))
            rows = cursor.fetchall()

            doc_counts: Dict[str, int] = {}
            for row in rows:
                # row is sqlite3.Row because row_factory = sqlite3.Row
                raw = row['sources'] if isinstance(row, sqlite3.Row) else row[0]
                if raw is None:
                    continue

                # Try robust JSON parsing, tolerate common malformed forms
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
                    # Try converting single-quoted lists to valid JSON
                    try:
                        if isinstance(raw, str) and raw.strip().startswith('[') and raw.strip().endswith(']'):
                            parsed = json.loads(raw.replace("'", '"'))
                    except Exception:
                        parsed = None

                    # Fallback to treating as a single source string
                    if parsed is None:
                        parsed = [raw]

                # Normalize to list
                if isinstance(parsed, (str, bytes)):
                    parsed = [parsed]
                if not isinstance(parsed, list):
                    parsed = [parsed]

                for item in parsed:
                    if not item:
                        continue
                    key = str(item)
                    doc_counts[key] = doc_counts.get(key, 0) + 1

            popular_docs = [
                {"document": doc, "usage_count": count}
                for doc, count in sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Queries per day
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as query_count
                FROM query_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """, (cutoff_date,))
            
            queries_per_day = [dict(row) for row in cursor.fetchall()]
            
            # Cost per day
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(cost) as daily_cost
                FROM query_metrics
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date ASC
            """, (cutoff_date,))
            
            cost_per_day = [dict(row) for row in cursor.fetchall()]
            
            return AnalyticsSummary(
                total_queries=overall['total_queries'] or 0,
                total_conversations=total_conversations or 0,
                avg_response_time=round(overall['avg_response_time'] or 0, 2),
                total_cost=round(overall['total_cost'] or 0, 4),
                success_rate=round(overall['success_rate'] or 0, 2),
                most_asked_questions=most_asked,
                popular_documents=popular_docs,
                queries_per_day=queries_per_day,
                cost_per_day=cost_per_day,
                avg_confidence=round(overall['avg_confidence'] or 0, 2),
                rag_usage_rate=round(overall['rag_usage_rate'] or 0, 2)
            )
    
    def get_cost_breakdown(self, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed cost breakdown by model, time period, etc.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with cost breakdown details
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Cost by model
            cursor.execute("""
                SELECT 
                    model_used,
                    COUNT(*) as query_count,
                    SUM(cost) as total_cost,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens
                FROM query_metrics
                WHERE timestamp >= ?
                GROUP BY model_used
            """, (cutoff_date,))
            
            by_model = [dict(row) for row in cursor.fetchall()]
            
            # Total cost
            cursor.execute("""
                SELECT SUM(cost) as total FROM query_metrics
                WHERE timestamp >= ?
            """, (cutoff_date,))
            
            total_cost = cursor.fetchone()['total'] or 0
            
            return {
                "total_cost": round(total_cost, 4),
                "by_model": by_model,
                "period_days": days,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now().isoformat()
            }
    
    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily statistics for charting

        Args:
            days: Number of days to retrieve

        Returns:
            List of daily statistics dictionaries
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM daily_stats
                WHERE date >= DATE(?)
                ORDER BY date ASC
            """, (cutoff_date,))

            return [dict(row) for row in cursor.fetchall()]

    def get_budget_alert(self, daily_budget: float, monthly_budget: float) -> Dict[str, Any]:
        """
        Check if spending is approaching budget limits

        Args:
            daily_budget: Daily spending limit in USD
            monthly_budget: Monthly spending limit in USD

        Returns:
            Dictionary with alert status and details
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Today's spending
            cursor.execute("""
                SELECT COALESCE(SUM(cost), 0) as daily_cost
                FROM query_metrics
                WHERE DATE(timestamp) = DATE('now')
            """)
            
            daily_cost = cursor.fetchone()['daily_cost']
            
            # This month's spending
            cursor.execute("""
                SELECT COALESCE(SUM(cost), 0) as monthly_cost
                FROM query_metrics
                WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
            """)
            
            monthly_cost = cursor.fetchone()['monthly_cost']
            
            # Calculate percentages
            daily_pct = (daily_cost / daily_budget * 100) if daily_budget > 0 else 0
            monthly_pct = (monthly_cost / monthly_budget * 100) if monthly_budget > 0 else 0
            
            # Determine alert level
            alert_level = "none"
            if daily_pct >= 90 or monthly_pct >= 90:
                alert_level = "critical"
            elif daily_pct >= 75 or monthly_pct >= 75:
                alert_level = "warning"
            elif daily_pct >= 50 or monthly_pct >= 50:
                alert_level = "info"
            
            return {
                "alert_level": alert_level,
                "daily": {
                    "spent": round(daily_cost, 4),
                    "budget": daily_budget,
                    "percentage": round(daily_pct, 2),
                    "remaining": round(daily_budget - daily_cost, 4)
                },
                "monthly": {
                    "spent": round(monthly_cost, 4),
                    "budget": monthly_budget,
                    "percentage": round(monthly_pct, 2),
                    "remaining": round(monthly_budget - monthly_cost, 4)
                }
            }
    
    # =========================================================================
    
    def get_total_conversations(self) -> int:
        """
        Get total number of conversations in the database
        
        Returns:
            Total count of conversations
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM conversations")
            result = cursor.fetchone()
            return result['total'] if result else 0
    
    def export_to_json(self) -> dict:
        """
        Export all analytics data as JSON for global analytics export
        
        Returns:
            Dictionary with comprehensive analytics data
        """
        summary = self.get_analytics_summary(days=30)
        conversations = self.get_all_conversations(limit=1000)
        cost_breakdown = self.get_cost_breakdown(days=30)
        
        return {
            "summary": asdict(summary),
            "conversations": conversations,
            "cost_breakdown": cost_breakdown,
            "exported_at": datetime.now().isoformat(),
            "export_type": "global_analytics"
        }
    
    def export_to_csv(self) -> str:
        """
        Export analytics summary as CSV for global analytics export
        
        Returns:
            CSV formatted string with analytics summary
        """
        import csv
        import io
        
        summary = self.get_analytics_summary(days=30)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary statistics
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Queries", summary.total_queries])
        writer.writerow(["Total Conversations", summary.total_conversations])
        writer.writerow(["Avg Response Time (s)", round(summary.avg_response_time, 3)])
        writer.writerow(["Total Cost ($)", round(summary.total_cost, 4)])
        writer.writerow(["Success Rate (%)", round(summary.success_rate, 2)])
        writer.writerow(["Avg Confidence", round(summary.avg_confidence, 2)])
        writer.writerow(["RAG Usage Rate (%)", round(summary.rag_usage_rate, 2)])
        writer.writerow([])
        
        # Write cost per day data
        writer.writerow(["Date", "Total Cost", "Total Queries"])
        for day_data in summary.cost_per_day:
            writer.writerow([day_data['date'], day_data['cost'], day_data['queries']])
        
        return output.getvalue()

    # 🧹 CLEANUP METHODS
    # =========================================================================
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Remove old data beyond retention period
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old messages
            cursor.execute("""
                DELETE FROM messages WHERE timestamp < ?
            """, (cutoff_date,))
            messages_deleted = cursor.rowcount
            
            # Delete old metrics
            cursor.execute("""
                DELETE FROM query_metrics WHERE timestamp < ?
            """, (cutoff_date,))
            metrics_deleted = cursor.rowcount
            
            # Delete conversations with no messages
            cursor.execute("""
                DELETE FROM conversations
                WHERE conversation_id NOT IN (SELECT DISTINCT conversation_id FROM messages)
            """)
            conversations_deleted = cursor.rowcount
            
            self.logger.info(
                f"Cleanup completed: {messages_deleted} messages, "
                f"{metrics_deleted} metrics, {conversations_deleted} conversations deleted"
            )

# =============================================================================
# 🧪 TEST FUNCTION
# =============================================================================

def test_analytics_database():
    """Test the analytics database functionality"""
    import tempfile
    import os
    
    # Create temporary database
    db_path = os.path.join(tempfile.gettempdir(), "test_analytics.db")
    db = AnalyticsDatabase(db_path)
    
    print("🧪 Testing Analytics Database...")
    
    # Test 1: Create conversation
    conv_id = db.create_conversation(user_id="test_user")
    print(f"✅ Created conversation: {conv_id}")
    
    # Test 2: Add messages
    msg1 = ConversationMessage(
        message_id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content="What is the password policy?",
        timestamp=datetime.now()
    )
    db.add_message(msg1)
    
    msg2 = ConversationMessage(
        message_id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content="The password must be at least 12 characters...",
        timestamp=datetime.now(),
        response_time=2.5,
        using_rag=True,
        context_found=3,
        confidence=0.92,
        sources=["IT_Policy.pdf"]
    )
    db.add_message(msg2)
    print("✅ Added messages to conversation")
    
    # Test 3: Record metrics
    metrics = QueryMetrics(
        query_id=str(uuid.uuid4()),
        conversation_id=conv_id,
        query_text="What is the password policy?",
        response_text="The password must be at least 12 characters...",
        timestamp=datetime.now(),
        response_time=2.5,
        using_rag=True,
        context_found=3,
        confidence=0.92,
        sources=["IT_Policy.pdf"],
        input_tokens=150,
        output_tokens=50,
        cost=calculate_openai_cost(150, 50),
        model_used="gpt-4o-mini",
        success=True
    )
    db.record_query_metrics(metrics)
    print("✅ Recorded query metrics")
    
    # Test 4: Get analytics
    summary = db.get_analytics_summary(days=30)
    print(f"\n📊 Analytics Summary:")
    print(f"  Total Queries: {summary.total_queries}")
    print(f"  Total Cost: ${summary.total_cost}")
    print(f"  Avg Response Time: {summary.avg_response_time}s")
    print(f"  Success Rate: {summary.success_rate}%")
    
    # Test 5: Cost breakdown
    cost_breakdown = db.get_cost_breakdown(days=30)
    print(f"\n💰 Cost Breakdown:")
    print(f"  Total Cost: ${cost_breakdown['total_cost']}")
    
    # Test 6: Budget alert
    budget_alert = db.get_budget_alert(daily_budget=10.0, monthly_budget=300.0)
    print(f"\n🚨 Budget Alert: {budget_alert['alert_level']}")
    print(f"  Daily: ${budget_alert['daily']['spent']} / ${budget_alert['daily']['budget']}")
    print(f"  Monthly: ${budget_alert['monthly']['spent']} / ${budget_alert['monthly']['budget']}")
    
    # Test 7: Export conversation
    exported_json = db.export_conversation(conv_id, format="json")
    print(f"\n📤 Exported conversation ({len(exported_json)} characters)")
    
    # Cleanup
    os.remove(db_path)
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    # Setup logging for tests
    logging.basicConfig(level=logging.INFO)
    test_analytics_database()