"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        INSIGHT GENERATOR MODULE                              ║
║              AI-Powered Automatic Data Insights Engine                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Generates natural language insights from data using GPT-4o-mini             ║
║  Features: Trend analysis, anomaly detection, narratives, recommendations    ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📊 Data Insights      - Automatic discovery of patterns and trends
📈 Trend Analysis     - Identify and explain trends in time series
⚠️ Anomaly Detection  - Find and explain unusual data points
📝 Chart Narratives   - Generate explanations for visualizations
💡 Recommendations    - Actionable business recommendations
🔮 Predictive Insights- Forecast-based insights
🎯 KPI Commentary     - Explain KPI performance

USAGE:
------
    from data_analyst import InsightGenerator
    
    # Initialize with OpenAI API key
    generator = InsightGenerator(api_key="your-key")
    
    # Generate insights from DataFrame
    insights = generator.generate_insights(df)
    
    # Get trend insights
    trend_insights = generator.analyze_trends(df, date_col='Date', value_col='Revenue')
    
    # Generate chart narrative
    narrative = generator.generate_chart_narrative(df, chart_type='line', x='Date', y='Sales')
    
    # Get anomaly insights
    anomalies = generator.detect_anomalies(df, column='Revenue')

ARCHITECTURE:
-------------
InsightGenerator (main class)
    ├── DataAnalyzer        - Statistical analysis for insight generation
    ├── TrendInsightEngine  - Trend-based insights
    ├── AnomalyInsightEngine- Anomaly detection and explanation
    ├── NarrativeEngine     - Natural language generation
    ├── RecommendationEngine- Business recommendations
    └── LLMClient           - OpenAI GPT-4o-mini integration
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import re

import numpy as np
import pandas as pd

# OpenAI integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not installed. Install with: pip install openai")

# Import from our modules
try:
    from .data_profiler import DataProfiler, DataProfile
    from .statistical_engine import StatisticalEngine, TrendDirection
    from .chart_recommender import ChartType
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    logging.debug("Other data_analyst modules not available")

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class InsightType(Enum):
    """Types of insights"""
    TREND = "trend"
    ANOMALY = "anomaly"
    COMPARISON = "comparison"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    SUMMARY = "summary"
    FORECAST = "forecast"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    ACHIEVEMENT = "achievement"


class InsightPriority(Enum):
    """Priority levels for insights"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InsightCategory(Enum):
    """Business categories for insights"""
    PERFORMANCE = "performance"
    GROWTH = "growth"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    GENERAL = "general"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Insight:
    """
    Single insight with all metadata.
    """
    id: str
    text: str
    insight_type: InsightType
    priority: InsightPriority = InsightPriority.MEDIUM
    category: InsightCategory = InsightCategory.GENERAL
    
    # Supporting data
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    change_value: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Context
    time_period: Optional[str] = None
    comparison_period: Optional[str] = None
    
    # Evidence
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8  # 0-1 confidence score
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    source: str = "auto"  # auto, llm, rule-based
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.insight_type.value,
            "priority": self.priority.value,
            "category": self.category.value,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "change_percent": self.change_percent,
            "confidence": self.confidence
        }
    
    def __str__(self) -> str:
        priority_icons = {
            InsightPriority.CRITICAL: "🚨",
            InsightPriority.HIGH: "⚠️",
            InsightPriority.MEDIUM: "📊",
            InsightPriority.LOW: "📝",
            InsightPriority.INFO: "ℹ️"
        }
        return f"{priority_icons.get(self.priority, '•')} {self.text}"


@dataclass
class InsightCollection:
    """
    Collection of insights with metadata.
    """
    insights: List[Insight] = field(default_factory=list)
    
    # Summary
    total_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    
    # Context
    data_source: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    generation_time_ms: float = 0.0
    
    def add(self, insight: Insight):
        """Add an insight to the collection"""
        self.insights.append(insight)
        self.total_count = len(self.insights)
        self._update_counts()
    
    def _update_counts(self):
        """Update priority counts"""
        self.critical_count = sum(1 for i in self.insights if i.priority == InsightPriority.CRITICAL)
        self.high_count = sum(1 for i in self.insights if i.priority == InsightPriority.HIGH)
    
    def get_by_type(self, insight_type: InsightType) -> List[Insight]:
        """Get insights by type"""
        return [i for i in self.insights if i.insight_type == insight_type]
    
    def get_by_priority(self, priority: InsightPriority) -> List[Insight]:
        """Get insights by priority"""
        return [i for i in self.insights if i.priority == priority]
    
    def get_top(self, n: int = 5) -> List[Insight]:
        """Get top N insights by priority"""
        priority_order = {
            InsightPriority.CRITICAL: 0,
            InsightPriority.HIGH: 1,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 3,
            InsightPriority.INFO: 4
        }
        sorted_insights = sorted(self.insights, key=lambda x: priority_order.get(x.priority, 5))
        return sorted_insights[:n]
    
    def to_text(self) -> str:
        """Convert all insights to formatted text"""
        lines = []
        for insight in self.get_top(10):
            lines.append(str(insight))
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_count": self.total_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "insights": [i.to_dict() for i in self.insights],
            "generated_at": self.generated_at.isoformat()
        }


@dataclass 
class ChartNarrative:
    """
    Narrative explanation for a chart.
    """
    title: str
    summary: str
    key_findings: List[str]
    
    # Details
    trend_description: Optional[str] = None
    notable_points: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Chart context
    chart_type: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    
    def to_html(self) -> str:
        """Convert narrative to HTML"""
        findings_html = "".join([f"<li>{f}</li>" for f in self.key_findings])
        
        return f"""
        <div class="chart-narrative">
            <h4>{self.title}</h4>
            <p>{self.summary}</p>
            <h5>Key Findings:</h5>
            <ul>{findings_html}</ul>
            {f'<p><strong>Trend:</strong> {self.trend_description}</p>' if self.trend_description else ''}
        </div>
        """


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLMClient:
    """
    Client for interacting with OpenAI GPT-4o-mini.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"LLM Client initialized with model: {model}")
        else:
            logger.warning("OpenAI client not initialized - using rule-based insights only")
    
    @property
    def is_available(self) -> bool:
        """Check if LLM is available"""
        return self.client is not None
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens in response
            temperature: Creativity (0-1)
            
        Returns:
            Generated text or None if failed
        """
        if not self.is_available:
            return None
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate structured JSON response"""
        
        json_system = (system_prompt or "") + "\n\nRespond ONLY with valid JSON, no other text."
        
        response = self.generate(prompt, json_system, temperature=0.3)
        
        if response:
            try:
                # Clean up response - remove markdown code blocks if present
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r'^```json?\s*', '', cleaned)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return None
        return None


# =============================================================================
# DATA ANALYZER
# =============================================================================

class DataAnalyzer:
    """
    Analyzes data to extract facts for insight generation.
    """
    
    def __init__(self):
        self.stats_engine = StatisticalEngine() if MODULES_AVAILABLE else None
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive data analysis.
        
        Returns dict with analysis results.
        """
        analysis = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": {},
            "numeric_summary": {},
            "categorical_summary": {},
            "time_analysis": None,
            "correlations": [],
            "anomalies": []
        }
        
        # Analyze each column
        for col in df.columns:
            col_analysis = self._analyze_column(df, col)
            analysis["columns"][col] = col_analysis
            
            if col_analysis["dtype"] == "numeric":
                analysis["numeric_summary"][col] = col_analysis
            elif col_analysis["dtype"] == "categorical":
                analysis["categorical_summary"][col] = col_analysis
        
        # Time series detection
        date_cols = [c for c, info in analysis["columns"].items() if info["dtype"] == "datetime"]
        numeric_cols = list(analysis["numeric_summary"].keys())
        
        if date_cols and numeric_cols:
            analysis["time_analysis"] = self._analyze_time_series(
                df, date_cols[0], numeric_cols[0]
            )
        
        # Correlations
        if len(numeric_cols) >= 2:
            analysis["correlations"] = self._find_correlations(df, numeric_cols)
        
        # Anomalies
        for col in numeric_cols[:3]:  # Top 3 numeric columns
            anomalies = self._detect_anomalies(df, col)
            if anomalies:
                analysis["anomalies"].extend(anomalies)
        
        return analysis
    
    def _analyze_column(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        """Analyze a single column"""
        series = df[col]
        
        # Determine dtype
        if pd.api.types.is_numeric_dtype(series):
            dtype = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            dtype = "datetime"
        else:
            dtype = "categorical"
        
        result = {
            "name": col,
            "dtype": dtype,
            "null_count": series.isna().sum(),
            "null_percent": series.isna().mean() * 100,
            "unique_count": series.nunique()
        }
        
        if dtype == "numeric":
            result.update({
                "mean": series.mean(),
                "median": series.median(),
                "std": series.std(),
                "min": series.min(),
                "max": series.max(),
                "sum": series.sum(),
                "q25": series.quantile(0.25),
                "q75": series.quantile(0.75)
            })
        elif dtype == "categorical":
            value_counts = series.value_counts()
            result.update({
                "top_values": value_counts.head(5).to_dict(),
                "top_value": value_counts.index[0] if len(value_counts) > 0 else None,
                "top_value_count": value_counts.iloc[0] if len(value_counts) > 0 else 0
            })
        elif dtype == "datetime":
            result.update({
                "min_date": series.min(),
                "max_date": series.max(),
                "date_range_days": (series.max() - series.min()).days if pd.notna(series.min()) else 0
            })
        
        return result
    
    def _analyze_time_series(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str
    ) -> Dict[str, Any]:
        """Analyze time series patterns"""
        
        df_sorted = df.sort_values(date_col)
        values = df_sorted[value_col].values
        
        # Basic trend
        if len(values) >= 2:
            first_half = values[:len(values)//2].mean()
            second_half = values[len(values)//2:].mean()
            
            if second_half > first_half * 1.05:
                trend = "increasing"
            elif second_half < first_half * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
            
            change_percent = ((second_half - first_half) / first_half * 100) if first_half != 0 else 0
        else:
            trend = "insufficient_data"
            change_percent = 0
        
        # Find peaks and troughs
        peaks = []
        troughs = []
        
        if len(values) >= 3:
            for i in range(1, len(values) - 1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peaks.append({"index": i, "value": values[i]})
                elif values[i] < values[i-1] and values[i] < values[i+1]:
                    troughs.append({"index": i, "value": values[i]})
        
        return {
            "trend": trend,
            "change_percent": change_percent,
            "start_value": values[0] if len(values) > 0 else None,
            "end_value": values[-1] if len(values) > 0 else None,
            "peak_count": len(peaks),
            "trough_count": len(troughs),
            "volatility": np.std(values) / np.mean(values) * 100 if np.mean(values) != 0 else 0
        }
    
    def _find_correlations(
        self,
        df: pd.DataFrame,
        numeric_cols: List[str]
    ) -> List[Dict[str, Any]]:
        """Find significant correlations"""
        correlations = []
        
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                try:
                    corr = df[col1].corr(df[col2])
                    if abs(corr) > 0.5:  # Significant correlation
                        correlations.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": corr,
                            "strength": "strong" if abs(corr) > 0.7 else "moderate",
                            "direction": "positive" if corr > 0 else "negative"
                        })
                except:
                    pass
        
        return sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True)
    
    def _detect_anomalies(
        self,
        df: pd.DataFrame,
        col: str,
        threshold: float = 2.5
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using z-score"""
        anomalies = []
        
        try:
            values = df[col].dropna()
            mean = values.mean()
            std = values.std()
            
            if std == 0:
                return []
            
            z_scores = (values - mean) / std
            
            for idx, z in z_scores.items():
                if abs(z) > threshold:
                    anomalies.append({
                        "column": col,
                        "index": idx,
                        "value": values[idx],
                        "z_score": z,
                        "direction": "high" if z > 0 else "low",
                        "severity": "extreme" if abs(z) > 3 else "moderate"
                    })
        except:
            pass
        
        return anomalies[:5]  # Top 5 anomalies


# =============================================================================
# INSIGHT ENGINES
# =============================================================================

class TrendInsightEngine:
    """
    Generates trend-based insights.
    """
    
    def generate(
        self,
        analysis: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[Insight]:
        """Generate trend insights from analysis"""
        insights = []
        insight_counter = 0
        
        time_analysis = analysis.get("time_analysis")
        
        if time_analysis:
            trend = time_analysis.get("trend", "stable")
            change = time_analysis.get("change_percent", 0)
            
            # Main trend insight
            if trend == "increasing":
                priority = InsightPriority.HIGH if change > 20 else InsightPriority.MEDIUM
                category = InsightCategory.GROWTH
                
                insights.append(Insight(
                    id=f"trend_{insight_counter}",
                    text=f"Data shows an increasing trend with {abs(change):.1f}% growth over the period.",
                    insight_type=InsightType.TREND,
                    priority=priority,
                    category=category,
                    change_percent=change,
                    source="rule-based"
                ))
                insight_counter += 1
                
            elif trend == "decreasing":
                priority = InsightPriority.HIGH if abs(change) > 20 else InsightPriority.MEDIUM
                category = InsightCategory.RISK
                
                insights.append(Insight(
                    id=f"trend_{insight_counter}",
                    text=f"Data shows a decreasing trend with {abs(change):.1f}% decline over the period.",
                    insight_type=InsightType.TREND,
                    priority=priority,
                    category=category,
                    change_percent=change,
                    source="rule-based"
                ))
                insight_counter += 1
            
            # Volatility insight
            volatility = time_analysis.get("volatility", 0)
            if volatility > 30:
                insights.append(Insight(
                    id=f"trend_{insight_counter}",
                    text=f"High volatility detected ({volatility:.1f}% coefficient of variation). Consider investigating the cause of fluctuations.",
                    insight_type=InsightType.WARNING,
                    priority=InsightPriority.MEDIUM,
                    category=InsightCategory.RISK,
                    source="rule-based"
                ))
                insight_counter += 1
        
        return insights


class AnomalyInsightEngine:
    """
    Generates anomaly-based insights.
    """
    
    def generate(
        self,
        analysis: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[Insight]:
        """Generate anomaly insights"""
        insights = []
        anomalies = analysis.get("anomalies", [])
        
        for i, anomaly in enumerate(anomalies[:3]):  # Top 3 anomalies
            direction = "unusually high" if anomaly["direction"] == "high" else "unusually low"
            severity = anomaly.get("severity", "moderate")
            
            priority = InsightPriority.HIGH if severity == "extreme" else InsightPriority.MEDIUM
            
            insights.append(Insight(
                id=f"anomaly_{i}",
                text=f"Anomaly detected in '{anomaly['column']}': Value {anomaly['value']:.2f} is {direction} (z-score: {anomaly['z_score']:.1f}).",
                insight_type=InsightType.ANOMALY,
                priority=priority,
                category=InsightCategory.RISK,
                metric_name=anomaly["column"],
                metric_value=anomaly["value"],
                supporting_data=anomaly,
                source="rule-based"
            ))
        
        return insights


class SummaryInsightEngine:
    """
    Generates summary insights.
    """
    
    def generate(
        self,
        analysis: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[Insight]:
        """Generate summary insights"""
        insights = []
        
        shape = analysis.get("shape", {})
        numeric_summary = analysis.get("numeric_summary", {})
        
        # Dataset overview
        insights.append(Insight(
            id="summary_0",
            text=f"Dataset contains {shape.get('rows', 0):,} records across {shape.get('columns', 0)} columns.",
            insight_type=InsightType.SUMMARY,
            priority=InsightPriority.INFO,
            category=InsightCategory.GENERAL,
            source="rule-based"
        ))
        
        # Top metric insights
        for col, stats in list(numeric_summary.items())[:2]:
            total = stats.get("sum", 0)
            avg = stats.get("mean", 0)
            
            if total > 0:
                insights.append(Insight(
                    id=f"summary_{col}",
                    text=f"Total '{col}': {total:,.2f} (Average: {avg:,.2f})",
                    insight_type=InsightType.SUMMARY,
                    priority=InsightPriority.LOW,
                    category=InsightCategory.PERFORMANCE,
                    metric_name=col,
                    metric_value=total,
                    source="rule-based"
                ))
        
        return insights


class CorrelationInsightEngine:
    """
    Generates correlation-based insights.
    """
    
    def generate(
        self,
        analysis: Dict[str, Any],
        df: pd.DataFrame
    ) -> List[Insight]:
        """Generate correlation insights"""
        insights = []
        correlations = analysis.get("correlations", [])
        
        for i, corr in enumerate(correlations[:2]):  # Top 2 correlations
            strength = corr.get("strength", "moderate")
            direction = corr.get("direction", "positive")
            col1, col2 = corr["column1"], corr["column2"]
            corr_value = corr["correlation"]
            
            if direction == "positive":
                relationship = "increases with"
            else:
                relationship = "decreases as"
            
            insights.append(Insight(
                id=f"correlation_{i}",
                text=f"Strong {direction} correlation found: '{col1}' {relationship} '{col2}' (r={corr_value:.2f}).",
                insight_type=InsightType.CORRELATION,
                priority=InsightPriority.MEDIUM,
                category=InsightCategory.GENERAL,
                supporting_data=corr,
                source="rule-based"
            ))
        
        return insights


class RecommendationEngine:
    """
    Generates business recommendations.
    """
    
    def generate(
        self,
        analysis: Dict[str, Any],
        insights: List[Insight],
        df: pd.DataFrame
    ) -> List[Insight]:
        """Generate recommendations based on analysis and insights"""
        recommendations = []
        
        # Check for trends
        time_analysis = analysis.get("time_analysis")
        if time_analysis:
            trend = time_analysis.get("trend")
            change = time_analysis.get("change_percent", 0)
            
            if trend == "decreasing" and abs(change) > 10:
                recommendations.append(Insight(
                    id="rec_trend",
                    text="Consider investigating the root cause of the declining trend and implementing corrective measures.",
                    insight_type=InsightType.RECOMMENDATION,
                    priority=InsightPriority.HIGH,
                    category=InsightCategory.RISK,
                    source="rule-based"
                ))
            elif trend == "increasing" and change > 20:
                recommendations.append(Insight(
                    id="rec_growth",
                    text="Strong growth detected. Consider scaling resources to sustain momentum.",
                    insight_type=InsightType.RECOMMENDATION,
                    priority=InsightPriority.MEDIUM,
                    category=InsightCategory.OPPORTUNITY,
                    source="rule-based"
                ))
        
        # Check for anomalies
        anomaly_count = len(analysis.get("anomalies", []))
        if anomaly_count > 2:
            recommendations.append(Insight(
                id="rec_anomaly",
                text=f"Multiple anomalies detected ({anomaly_count}). Review data quality and investigate unusual values.",
                insight_type=InsightType.RECOMMENDATION,
                priority=InsightPriority.MEDIUM,
                category=InsightCategory.QUALITY,
                source="rule-based"
            ))
        
        # Check for high volatility
        if time_analysis and time_analysis.get("volatility", 0) > 40:
            recommendations.append(Insight(
                id="rec_volatility",
                text="High data volatility suggests inconsistent performance. Consider implementing stabilization strategies.",
                insight_type=InsightType.RECOMMENDATION,
                priority=InsightPriority.MEDIUM,
                category=InsightCategory.RISK,
                source="rule-based"
            ))
        
        return recommendations


# =============================================================================
# MAIN INSIGHT GENERATOR CLASS
# =============================================================================

class InsightGenerator:
    """
    Main class for generating AI-powered insights from data.
    
    Combines rule-based analysis with LLM-powered narrative generation.
    
    Usage:
        generator = InsightGenerator(api_key="your-openai-key")
        
        # Generate all insights
        insights = generator.generate_insights(df)
        
        # Print top insights
        print(insights.to_text())
        
        # Generate chart narrative
        narrative = generator.generate_chart_narrative(df, "line", "Date", "Revenue")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        use_llm: bool = True
    ):
        """
        Initialize the insight generator.
        
        Args:
            api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            model: LLM model to use
            use_llm: Whether to use LLM for enhanced insights
        """
        self.llm = LLMClient(api_key, model) if use_llm else None
        self.analyzer = DataAnalyzer()
        
        # Insight engines
        self.trend_engine = TrendInsightEngine()
        self.anomaly_engine = AnomalyInsightEngine()
        self.summary_engine = SummaryInsightEngine()
        self.correlation_engine = CorrelationInsightEngine()
        self.recommendation_engine = RecommendationEngine()
        
        logger.info(f"InsightGenerator initialized (LLM: {'enabled' if self.llm and self.llm.is_available else 'disabled'})")
    
    # =========================================================================
    # MAIN GENERATION METHODS
    # =========================================================================
    
    def generate_insights(
        self,
        df: pd.DataFrame,
        focus_columns: Optional[List[str]] = None,
        max_insights: int = 10
    ) -> InsightCollection:
        """
        Generate comprehensive insights from a DataFrame.
        
        Args:
            df: Input DataFrame
            focus_columns: Columns to focus on (None = all)
            max_insights: Maximum insights to return
            
        Returns:
            InsightCollection with all insights
        """
        import time
        start_time = time.time()
        
        collection = InsightCollection(data_source="DataFrame")
        
        # Analyze data
        analysis = self.analyzer.analyze(df)
        
        # Generate rule-based insights
        all_insights = []
        
        # Summary insights
        all_insights.extend(self.summary_engine.generate(analysis, df))
        
        # Trend insights
        all_insights.extend(self.trend_engine.generate(analysis, df))
        
        # Anomaly insights
        all_insights.extend(self.anomaly_engine.generate(analysis, df))
        
        # Correlation insights
        all_insights.extend(self.correlation_engine.generate(analysis, df))
        
        # Recommendations
        all_insights.extend(self.recommendation_engine.generate(analysis, all_insights, df))
        
        # Enhance with LLM if available
        if self.llm and self.llm.is_available:
            llm_insights = self._generate_llm_insights(df, analysis)
            all_insights.extend(llm_insights)
        
        # Add to collection (limit to max)
        for insight in all_insights[:max_insights]:
            collection.add(insight)
        
        collection.generation_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Generated {collection.total_count} insights in {collection.generation_time_ms:.1f}ms")
        return collection
    
    def generate_chart_narrative(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        title: Optional[str] = None
    ) -> ChartNarrative:
        """
        Generate a narrative explanation for a chart.
        
        Args:
            df: Source DataFrame
            chart_type: Type of chart
            x_column: X-axis column
            y_column: Y-axis column
            title: Chart title
            
        Returns:
            ChartNarrative with explanation
        """
        # Analyze the data
        analysis = self.analyzer.analyze(df)
        
        # Build basic narrative
        narrative = self._build_basic_narrative(df, chart_type, x_column, y_column, analysis)
        
        # Enhance with LLM if available
        if self.llm and self.llm.is_available:
            enhanced = self._enhance_narrative_with_llm(df, chart_type, x_column, y_column, narrative)
            if enhanced:
                narrative = enhanced
        
        narrative.chart_type = chart_type
        narrative.x_axis = x_column
        narrative.y_axis = y_column
        
        if title:
            narrative.title = title
        
        return narrative
    
    def analyze_kpi(
        self,
        current_value: float,
        previous_value: Optional[float] = None,
        target_value: Optional[float] = None,
        metric_name: str = "Metric"
    ) -> Insight:
        """
        Generate insight for a KPI.
        
        Args:
            current_value: Current KPI value
            previous_value: Previous period value for comparison
            target_value: Target value
            metric_name: Name of the metric
            
        Returns:
            Insight for the KPI
        """
        # Calculate changes
        change_percent = None
        if previous_value and previous_value != 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
        
        target_percent = None
        if target_value and target_value != 0:
            target_percent = (current_value / target_value) * 100
        
        # Determine insight
        if change_percent is not None:
            if change_percent > 10:
                text = f"{metric_name} increased by {change_percent:.1f}% compared to the previous period."
                priority = InsightPriority.HIGH
                category = InsightCategory.GROWTH
            elif change_percent < -10:
                text = f"{metric_name} decreased by {abs(change_percent):.1f}% compared to the previous period."
                priority = InsightPriority.HIGH
                category = InsightCategory.RISK
            else:
                text = f"{metric_name} remained relatively stable ({change_percent:+.1f}%)."
                priority = InsightPriority.INFO
                category = InsightCategory.PERFORMANCE
        elif target_percent is not None:
            if target_percent >= 100:
                text = f"{metric_name} has achieved {target_percent:.1f}% of target!"
                priority = InsightPriority.HIGH
                category = InsightCategory.ACHIEVEMENT
            elif target_percent >= 80:
                text = f"{metric_name} is at {target_percent:.1f}% of target, on track to meet goals."
                priority = InsightPriority.MEDIUM
                category = InsightCategory.PERFORMANCE
            else:
                text = f"{metric_name} is at {target_percent:.1f}% of target, may need attention."
                priority = InsightPriority.HIGH
                category = InsightCategory.RISK
        else:
            text = f"{metric_name} current value: {current_value:,.2f}"
            priority = InsightPriority.INFO
            category = InsightCategory.GENERAL
        
        return Insight(
            id=f"kpi_{metric_name.lower().replace(' ', '_')}",
            text=text,
            insight_type=InsightType.SUMMARY,
            priority=priority,
            category=category,
            metric_name=metric_name,
            metric_value=current_value,
            change_percent=change_percent,
            source="rule-based"
        )
    
    def get_quick_insights(
        self,
        df: pd.DataFrame,
        n: int = 3
    ) -> List[str]:
        """
        Get quick text insights for display.
        
        Args:
            df: Input DataFrame
            n: Number of insights
            
        Returns:
            List of insight strings
        """
        collection = self.generate_insights(df, max_insights=n)
        return [str(insight) for insight in collection.get_top(n)]
    
    # =========================================================================
    # LLM-POWERED METHODS
    # =========================================================================
    
    def _generate_llm_insights(
        self,
        df: pd.DataFrame,
        analysis: Dict[str, Any]
    ) -> List[Insight]:
        """Generate insights using LLM"""
        insights = []
        
        if not self.llm or not self.llm.is_available:
            return insights
        
        # Prepare data summary for LLM
        data_summary = self._create_data_summary(df, analysis)
        
        system_prompt = """You are a data analyst expert. Analyze the provided data summary and generate 
2-3 key business insights. Focus on actionable findings, trends, and notable patterns.

Respond in JSON format:
{
    "insights": [
        {"text": "insight text", "type": "trend|anomaly|recommendation", "priority": "high|medium|low"}
    ]
}"""
        
        prompt = f"""Analyze this data summary and provide key insights:

{data_summary}

Provide 2-3 concise, actionable insights."""
        
        response = self.llm.generate_json(prompt, system_prompt)
        
        if response and "insights" in response:
            for i, insight_data in enumerate(response["insights"][:3]):
                insight_type = {
                    "trend": InsightType.TREND,
                    "anomaly": InsightType.ANOMALY,
                    "recommendation": InsightType.RECOMMENDATION
                }.get(insight_data.get("type", ""), InsightType.SUMMARY)
                
                priority = {
                    "high": InsightPriority.HIGH,
                    "medium": InsightPriority.MEDIUM,
                    "low": InsightPriority.LOW
                }.get(insight_data.get("priority", ""), InsightPriority.MEDIUM)
                
                insights.append(Insight(
                    id=f"llm_{i}",
                    text=insight_data.get("text", ""),
                    insight_type=insight_type,
                    priority=priority,
                    category=InsightCategory.GENERAL,
                    source="llm"
                ))
        
        return insights
    
    def _enhance_narrative_with_llm(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        basic_narrative: ChartNarrative
    ) -> Optional[ChartNarrative]:
        """Enhance chart narrative using LLM"""
        
        if not self.llm or not self.llm.is_available:
            return None
        
        # Sample data for context
        sample_data = df[[x_column, y_column]].head(10).to_string()
        
        system_prompt = """You are a data visualization expert. Create a clear, professional narrative 
explaining the chart. Be concise and business-focused.

Respond in JSON format:
{
    "summary": "2-3 sentence summary",
    "key_findings": ["finding 1", "finding 2", "finding 3"],
    "trend_description": "description of any trends",
    "recommendation": "one actionable recommendation"
}"""
        
        prompt = f"""Create a narrative for this {chart_type} chart:

X-axis: {x_column}
Y-axis: {y_column}

Sample data:
{sample_data}

Existing findings: {', '.join(basic_narrative.key_findings)}"""
        
        response = self.llm.generate_json(prompt, system_prompt)
        
        if response:
            return ChartNarrative(
                title=basic_narrative.title,
                summary=response.get("summary", basic_narrative.summary),
                key_findings=response.get("key_findings", basic_narrative.key_findings),
                trend_description=response.get("trend_description"),
                recommendations=[response.get("recommendation")] if response.get("recommendation") else []
            )
        
        return None
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _create_data_summary(
        self,
        df: pd.DataFrame,
        analysis: Dict[str, Any]
    ) -> str:
        """Create a text summary of the data for LLM"""
        lines = []
        
        shape = analysis.get("shape", {})
        lines.append(f"Dataset: {shape.get('rows', 0)} rows, {shape.get('columns', 0)} columns")
        
        # Numeric summaries
        for col, stats in list(analysis.get("numeric_summary", {}).items())[:3]:
            lines.append(f"- {col}: sum={stats.get('sum', 0):,.0f}, avg={stats.get('mean', 0):,.2f}")
        
        # Time analysis
        time_analysis = analysis.get("time_analysis")
        if time_analysis:
            lines.append(f"Trend: {time_analysis.get('trend', 'unknown')} ({time_analysis.get('change_percent', 0):+.1f}%)")
        
        # Anomalies
        anomaly_count = len(analysis.get("anomalies", []))
        if anomaly_count > 0:
            lines.append(f"Anomalies detected: {anomaly_count}")
        
        return "\n".join(lines)
    
    def _build_basic_narrative(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x_column: str,
        y_column: str,
        analysis: Dict[str, Any]
    ) -> ChartNarrative:
        """Build basic narrative without LLM"""
        
        # Basic statistics
        y_stats = analysis.get("columns", {}).get(y_column, {})
        
        key_findings = []
        
        if y_stats:
            total = y_stats.get("sum", 0)
            avg = y_stats.get("mean", 0)
            max_val = y_stats.get("max", 0)
            min_val = y_stats.get("min", 0)
            
            key_findings.append(f"Total {y_column}: {total:,.2f}")
            key_findings.append(f"Average {y_column}: {avg:,.2f}")
            key_findings.append(f"Range: {min_val:,.2f} to {max_val:,.2f}")
        
        # Trend if available
        trend_desc = None
        time_analysis = analysis.get("time_analysis")
        if time_analysis:
            trend = time_analysis.get("trend", "stable")
            change = time_analysis.get("change_percent", 0)
            trend_desc = f"The data shows a {trend} trend with {abs(change):.1f}% {'increase' if change > 0 else 'decrease'}."
        
        summary = f"This {chart_type} chart shows {y_column} by {x_column}."
        if len(df) > 0:
            summary += f" The visualization includes {len(df)} data points."
        
        return ChartNarrative(
            title=f"{y_column} by {x_column}",
            summary=summary,
            key_findings=key_findings,
            trend_description=trend_desc
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_insights(
    df: pd.DataFrame,
    api_key: Optional[str] = None,
    max_insights: int = 10
) -> InsightCollection:
    """
    Quick function to generate insights from a DataFrame.
    
    Args:
        df: Input DataFrame
        api_key: Optional OpenAI API key
        max_insights: Maximum insights
        
    Returns:
        InsightCollection
    """
    generator = InsightGenerator(api_key=api_key)
    return generator.generate_insights(df, max_insights=max_insights)


def quick_insights(df: pd.DataFrame, n: int = 3) -> List[str]:
    """
    Get quick text insights.
    
    Args:
        df: Input DataFrame
        n: Number of insights
        
    Returns:
        List of insight strings
    """
    generator = InsightGenerator(use_llm=False)
    return generator.get_quick_insights(df, n)


def explain_chart(
    df: pd.DataFrame,
    chart_type: str,
    x: str,
    y: str
) -> str:
    """
    Generate a text explanation for a chart.
    
    Args:
        df: Source DataFrame
        chart_type: Type of chart
        x: X-axis column
        y: Y-axis column
        
    Returns:
        Explanation text
    """
    generator = InsightGenerator(use_llm=False)
    narrative = generator.generate_chart_narrative(df, chart_type, x, y)
    return narrative.summary + "\n\nKey findings:\n" + "\n".join([f"• {f}" for f in narrative.key_findings])


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'InsightGenerator',
    
    # Result classes
    'Insight',
    'InsightCollection',
    'ChartNarrative',
    
    # Support classes
    'LLMClient',
    'DataAnalyzer',
    'TrendInsightEngine',
    'AnomalyInsightEngine',
    'RecommendationEngine',
    
    # Enums
    'InsightType',
    'InsightPriority',
    'InsightCategory',
    
    # Convenience functions
    'generate_insights',
    'quick_insights',
    'explain_chart',
]