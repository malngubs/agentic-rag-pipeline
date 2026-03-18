"""
================================================================================
📊 DATA ANALYST PACKAGE
================================================================================

Conversational BI Platform - A ChatGPT-like interface for business intelligence.

MODULES:
========
1. file_ingestor      - Multi-format document extraction (PDF, Excel, CSV, etc.)
2. data_profiler      - Data quality analysis and profiling
3. statistical_engine - Statistical analysis, forecasting, regression
4. chart_recommender  - Intelligent chart type recommendations (84 types)
5. chart_generator    - Plotly chart generation
6. dashboard_builder  - Professional dashboard creation
7. insight_generator  - AI-powered insight generation
8. analyst_orchestrator - Main coordinator (THE BRAIN)

USAGE:
======
```python
from data_analyst import AnalystOrchestrator

# Create orchestrator
orchestrator = AnalystOrchestrator()

# Create session
session = orchestrator.create_session()

# Upload data
orchestrator.upload_file(session.id, 'sales_data.xlsx')

# Query in natural language
result = orchestrator.query(session.id, "Show me a bar chart of sales by region")

# Quick one-liner analysis
from data_analyst import quick_analyze
result = quick_analyze(df, "What are the key insights?")
```

Author: Macrocomm Development Team
Version: 1.0.0
"""

# =============================================================================
# LAYER 1: DATA INGESTION
# =============================================================================
from .file_ingestor import (
    FileIngestor,
    ExtractionResult,
    ExtractedTable,
    clean_dataframe,
)

# =============================================================================
# LAYER 2: DATA UNDERSTANDING
# =============================================================================
from .data_profiler import (
    DataProfiler,
    DataProfile,
    ColumnProfile,
    DatasetQuality,
)

# =============================================================================
# LAYER 3: STATISTICAL ANALYSIS
# =============================================================================
from .statistical_engine import (
    StatisticalEngine,
    ForecastResult,
)

# =============================================================================
# LAYER 4: VISUALIZATION
# =============================================================================
from .chart_recommender import (
    ChartRecommender,
    ChartRecommendation,
    ChartCategory,
    ChartType,
)

from .chart_generator import (
    ChartGenerator,
    GeneratedChart,
)

# =============================================================================
# LAYER 5: DASHBOARD
# =============================================================================
from .dashboard_builder import (
    DashboardBuilder,
    Dashboard,
)

# =============================================================================
# LAYER 6: AI INTELLIGENCE
# =============================================================================
from .insight_generator import (
    InsightGenerator,
)

# =============================================================================
# LAYER 7: ORCHESTRATION (THE BRAIN)
# =============================================================================
from .analyst_orchestrator import (
    AnalystOrchestrator,
    AnalysisSession,
    QueryResult,
    QueryIntent,
    SessionStatus,
    quick_analyze,
)

# =============================================================================
# PACKAGE INFO
# =============================================================================
__version__ = "1.0.0"
__author__ = "Macrocomm Development Team"
__all__ = [
    # File Ingestor
    "FileIngestor",
    "ExtractionResult",
    "ExtractedTable",
    "clean_dataframe",
    
    # Data Profiler
    "DataProfiler",
    "DataProfile",
    "ColumnProfile",
    "DatasetQuality",
    
    # Statistical Engine
    "StatisticalEngine",
    "ForecastResult",
    
    # Chart Recommender
    "ChartRecommender",
    "ChartRecommendation",
    "ChartCategory",
    "ChartType",
    
    # Chart Generator
    "ChartGenerator",
    "GeneratedChart",
    
    # Dashboard Builder
    "DashboardBuilder",
    "Dashboard",
    
    # Insight Generator
    "InsightGenerator",
    
    # Analyst Orchestrator
    "AnalystOrchestrator",
    "AnalysisSession",
    "QueryResult",
    "QueryIntent",
    "SessionStatus",
    "quick_analyze",
]


# =============================================================================
# PACKAGE INITIALIZATION MESSAGE
# =============================================================================
import logging

logger = logging.getLogger(__name__)
logger.debug(f"Data Analyst package v{__version__} loaded successfully")
