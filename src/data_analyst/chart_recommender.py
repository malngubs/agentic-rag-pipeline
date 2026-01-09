"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       CHART RECOMMENDER MODULE                               ║
║              Intelligent Visualization Selection Engine                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Analyzes data and recommends optimal chart types from 80 options            ║
║  Features: Data analysis, chart scoring, intent detection, explanations      ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📊 80 Chart Types     - Comprehensive visualization library
🧠 Smart Selection    - Analyzes data shape, types, and cardinality
🎯 Intent Detection   - Understands comparison, correlation, distribution, etc.
📝 Explanations       - Why each chart is recommended
⭐ Scoring System     - Ranks charts by suitability

CHART CATEGORIES (80 Total):
----------------------------
1. COMPARISON (15)     - Bar, Column, Lollipop, Bullet, Radar, etc.
2. CORRELATION (7)     - Scatter, Bubble, Heatmap, etc.
3. PART-TO-WHOLE (15)  - Pie, Donut, Treemap, Sunburst, etc.
4. TIME SERIES (11)    - Line, Area, Candlestick, Gantt, etc.
5. DISTRIBUTION (12)   - Histogram, Box, Violin, etc.
6. SPECIALIZED (20)    - Sankey, Chord, Network, Gauge, Maps, etc.

USAGE:
------
    from data_analyst import ChartRecommender, DataProfiler
    
    # Profile your data first
    profiler = DataProfiler()
    profile = profiler.profile(df)
    
    # Get chart recommendations
    recommender = ChartRecommender()
    recommendations = recommender.recommend(df, profile)
    
    # Or with specific intent
    recommendations = recommender.recommend(df, profile, intent="comparison")
    
    # Access results
    for rec in recommendations[:5]:
        print(f"{rec.chart_type.value}: {rec.score:.0f}% - {rec.explanation}")

ARCHITECTURE:
-------------
ChartRecommender (main class)
    ├── ChartRegistry         - All 80 chart definitions with requirements
    ├── DataShapeAnalyzer     - Understand data structure
    ├── IntentDetector        - Detect analysis intent from query/data
    ├── ChartScorer           - Score charts based on data fit
    └── ExplanationGenerator  - Generate human-readable explanations
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

# Import from our modules
try:
    from .data_profiler import (
        DataProfile, ColumnProfile, ColumnType, QualityLevel
    )
    PROFILER_AVAILABLE = True
except ImportError:
    PROFILER_AVAILABLE = False
    logging.debug("data_profiler not available for type hints")

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS - Chart Categories
# =============================================================================

class ChartCategory(Enum):
    """Categories of charts based on their primary purpose"""
    COMPARISON = "comparison"           # Compare values across categories
    CORRELATION = "correlation"         # Show relationships between variables
    PART_TO_WHOLE = "part_to_whole"     # Show composition/proportions
    TIME_SERIES = "time_series"         # Show changes over time
    DISTRIBUTION = "distribution"       # Show data distribution
    GEOSPATIAL = "geospatial"           # Geographic data
    FLOW = "flow"                       # Show flows/connections
    HIERARCHY = "hierarchy"             # Hierarchical data
    SPECIALIZED = "specialized"         # Special purpose charts


class ChartType(Enum):
    """
    All 80 supported chart types.
    
    Naming convention: CATEGORY_SPECIFIC_NAME
    """
    # =========================================================================
    # COMPARISON CHARTS (15)
    # =========================================================================
    BAR_HORIZONTAL = "bar_horizontal"
    BAR_VERTICAL = "bar_vertical"
    BAR_GROUPED = "bar_grouped"
    BAR_STACKED = "bar_stacked"
    BAR_DIVERGING = "bar_diverging"
    LOLLIPOP = "lollipop"
    BULLET = "bullet"
    DOT_PLOT = "dot_plot"
    DUMBBELL = "dumbbell"
    SLOPE = "slope"
    RADAR = "radar"
    RADIAL_BAR = "radial_bar"
    PICTOGRAM = "pictogram"
    RANGE_PLOT = "range_plot"
    WATERFALL = "waterfall"
    
    # =========================================================================
    # CORRELATION CHARTS (7)
    # =========================================================================
    SCATTER = "scatter"
    SCATTER_CONNECTED = "scatter_connected"
    BUBBLE = "bubble"
    HEATMAP = "heatmap"
    CORRELATION_MATRIX = "correlation_matrix"
    CONTOUR = "contour"
    QUADRANT = "quadrant"
    
    # =========================================================================
    # PART-TO-WHOLE CHARTS (15)
    # =========================================================================
    PIE = "pie"
    DONUT = "donut"
    DONUT_SEMI = "donut_semi"
    TREEMAP = "treemap"
    TREEMAP_CIRCULAR = "treemap_circular"
    SUNBURST = "sunburst"
    WAFFLE = "waffle"
    PARLIAMENT = "parliament"
    MARIMEKKO = "marimekko"
    STACKED_AREA_PERCENT = "stacked_area_percent"
    STACKED_BAR_PERCENT = "stacked_bar_percent"
    FUNNEL = "funnel"
    PYRAMID = "pyramid"
    VENN = "venn"
    ICICLE = "icicle"
    
    # =========================================================================
    # TIME SERIES CHARTS (11)
    # =========================================================================
    LINE = "line"
    LINE_MULTI = "line_multi"
    AREA = "area"
    AREA_STACKED = "area_stacked"
    STREAM = "stream"
    STEP = "step"
    SPLINE = "spline"
    BUMP = "bump"
    CANDLESTICK = "candlestick"
    OHLC = "ohlc"
    GANTT = "gantt"
    
    # =========================================================================
    # DISTRIBUTION CHARTS (12)
    # =========================================================================
    HISTOGRAM = "histogram"
    HISTOGRAM_STACKED = "histogram_stacked"
    DENSITY = "density"
    BOX = "box"
    VIOLIN = "violin"
    STRIP = "strip"
    SWARM = "swarm"
    RIDGELINE = "ridgeline"
    QQ_PLOT = "qq_plot"
    ECDF = "ecdf"
    KDE = "kde"
    RAINCLOUD = "raincloud"
    
    # =========================================================================
    # GEOSPATIAL CHARTS (6)
    # =========================================================================
    CHOROPLETH = "choropleth"
    BUBBLE_MAP = "bubble_map"
    HEATMAP_GEO = "heatmap_geo"
    POINT_MAP = "point_map"
    CONNECTION_MAP = "connection_map"
    TILE_MAP = "tile_map"
    
    # =========================================================================
    # FLOW & RELATIONSHIP CHARTS (8)
    # =========================================================================
    SANKEY = "sankey"
    CHORD = "chord"
    NETWORK = "network"
    ARC = "arc"
    ALLUVIAL = "alluvial"
    FLOW_MAP = "flow_map"
    PARALLEL_COORDINATES = "parallel_coordinates"
    PARALLEL_SETS = "parallel_sets"
    
    # =========================================================================
    # SPECIALIZED CHARTS (6)
    # =========================================================================
    GAUGE = "gauge"
    SPARKLINE = "sparkline"
    WORD_CLOUD = "word_cloud"
    CALENDAR_HEATMAP = "calendar_heatmap"
    TABLE = "table"
    KPI_CARD = "kpi_card"
    
    # =========================================================================
    # HIERARCHY CHARTS (4)
    # =========================================================================
    TREE_DIAGRAM = "tree_diagram"
    DENDROGRAM = "dendrogram"
    ORG_CHART = "org_chart"
    RADIAL_TREE = "radial_tree"


class AnalysisIntent(Enum):
    """Types of analysis intent the user might have"""
    COMPARISON = "comparison"           # Compare values
    TREND = "trend"                     # See changes over time
    DISTRIBUTION = "distribution"       # See how values are distributed
    CORRELATION = "correlation"         # Find relationships
    COMPOSITION = "composition"         # See parts of a whole
    RANKING = "ranking"                 # Rank items
    FLOW = "flow"                       # See flows/transitions
    GEOGRAPHIC = "geographic"           # Location-based
    KPI = "kpi"                         # Key performance indicators
    GENERAL = "general"                 # No specific intent


class DataShape(Enum):
    """Shape classifications for data"""
    SINGLE_VALUE = "single_value"       # One number (KPI)
    SINGLE_SERIES = "single_series"     # One column of values
    MULTI_SERIES = "multi_series"       # Multiple columns
    TIME_INDEXED = "time_indexed"       # Has datetime index
    CATEGORICAL_NUMERIC = "categorical_numeric"  # Category + number
    CATEGORICAL_MULTI_NUMERIC = "categorical_multi_numeric"  # Category + multiple numbers
    NUMERIC_PAIR = "numeric_pair"       # Two numeric columns
    NUMERIC_TRIPLE = "numeric_triple"   # Three numeric columns
    HIERARCHICAL = "hierarchical"       # Parent-child structure
    MATRIX = "matrix"                   # 2D numeric matrix
    TEXT_HEAVY = "text_heavy"           # Mostly text data
    GEOGRAPHIC = "geographic"           # Has lat/long or region codes


# =============================================================================
# DATA CLASSES - Chart Definition
# =============================================================================

@dataclass
class ChartRequirements:
    """
    Requirements that data must meet for a chart type.
    """
    # Column type requirements
    min_numeric_cols: int = 0
    max_numeric_cols: Optional[int] = None
    min_categorical_cols: int = 0
    max_categorical_cols: Optional[int] = None
    requires_datetime: bool = False
    requires_hierarchy: bool = False
    requires_geographic: bool = False
    
    # Data size requirements
    min_rows: int = 1
    max_rows: Optional[int] = None
    min_categories: int = 0             # Minimum unique values in categorical
    max_categories: Optional[int] = None  # Maximum categories for readability
    
    # Special requirements
    requires_positive: bool = False     # All values must be positive
    requires_pairs: bool = False        # Need paired data
    requires_source_target: bool = False  # Need source/target columns
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_numeric_cols": self.min_numeric_cols,
            "max_numeric_cols": self.max_numeric_cols,
            "min_categorical_cols": self.min_categorical_cols,
            "max_categorical_cols": self.max_categorical_cols,
            "requires_datetime": self.requires_datetime,
            "requires_hierarchy": self.requires_hierarchy,
            "min_rows": self.min_rows,
            "max_rows": self.max_rows,
            "min_categories": self.min_categories,
            "max_categories": self.max_categories
        }


@dataclass
class ChartDefinition:
    """
    Complete definition of a chart type including metadata and requirements.
    """
    chart_type: ChartType
    category: ChartCategory
    name: str                           # Human-readable name
    description: str                    # What this chart shows
    requirements: ChartRequirements
    
    # Best use cases
    best_for: List[str] = field(default_factory=list)
    avoid_when: List[str] = field(default_factory=list)
    
    # Related charts (alternatives)
    alternatives: List[ChartType] = field(default_factory=list)
    
    # Scoring weights
    complexity: int = 1                 # 1-5, higher = more complex
    popularity: int = 3                 # 1-5, higher = more commonly used
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type.value,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "requirements": self.requirements.to_dict(),
            "best_for": self.best_for,
            "avoid_when": self.avoid_when,
            "complexity": self.complexity,
            "popularity": self.popularity
        }


@dataclass
class ChartRecommendation:
    """
    A single chart recommendation with score and explanation.
    """
    chart_type: ChartType
    category: ChartCategory
    name: str
    score: float                        # 0-100, how well it fits
    rank: int                           # 1 = best recommendation
    
    # Explanations
    explanation: str                    # Why this chart is recommended
    data_fit_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Configuration suggestions
    suggested_x: Optional[str] = None
    suggested_y: Optional[str] = None
    suggested_color: Optional[str] = None
    suggested_size: Optional[str] = None
    
    # Metadata
    complexity: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_type": self.chart_type.value,
            "category": self.category.value,
            "name": self.name,
            "score": round(self.score, 1),
            "rank": self.rank,
            "explanation": self.explanation,
            "data_fit_reasons": self.data_fit_reasons,
            "warnings": self.warnings,
            "suggested_x": self.suggested_x,
            "suggested_y": self.suggested_y,
            "suggested_color": self.suggested_color,
            "suggested_size": self.suggested_size,
            "complexity": self.complexity
        }


@dataclass
class DataCharacteristics:
    """
    Characteristics of the data being analyzed for chart selection.
    """
    # Shape
    row_count: int = 0
    column_count: int = 0
    shape: DataShape = DataShape.SINGLE_SERIES
    
    # Column types
    numeric_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)
    id_columns: List[str] = field(default_factory=list)
    
    # Cardinality
    categorical_cardinality: Dict[str, int] = field(default_factory=dict)
    max_cardinality: int = 0
    
    # Value characteristics
    has_negative_values: bool = False
    has_zero_values: bool = False
    has_missing_values: bool = False
    
    # Special patterns
    has_time_series: bool = False
    has_hierarchy: bool = False
    has_geographic: bool = False
    has_pairs: bool = False
    
    # Detected intent
    detected_intent: AnalysisIntent = AnalysisIntent.GENERAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "shape": self.shape.value,
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "categorical_cardinality": self.categorical_cardinality,
            "has_time_series": self.has_time_series,
            "detected_intent": self.detected_intent.value
        }


# =============================================================================
# CHART REGISTRY - All 80 Chart Definitions
# =============================================================================

class ChartRegistry:
    """
    Registry of all 80 chart types with their definitions and requirements.
    """
    
    def __init__(self):
        """Initialize registry with all chart definitions"""
        self.charts: Dict[ChartType, ChartDefinition] = {}
        self._register_all_charts()
    
    def _register_all_charts(self):
        """Register all 80 chart types"""
        
        # =====================================================================
        # COMPARISON CHARTS (15)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.BAR_HORIZONTAL,
            category=ChartCategory.COMPARISON,
            name="Horizontal Bar Chart",
            description="Compare values across categories with horizontal bars. Best for long category names.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=30
            ),
            best_for=["Comparing categories", "Long category labels", "Rankings"],
            avoid_when=["Too many categories (>30)", "Time series data"],
            alternatives=[ChartType.BAR_VERTICAL, ChartType.LOLLIPOP, ChartType.DOT_PLOT],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BAR_VERTICAL,
            category=ChartCategory.COMPARISON,
            name="Vertical Bar Chart (Column)",
            description="Compare values across categories with vertical bars. Classic chart for comparisons.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=20
            ),
            best_for=["Comparing categories", "Short labels", "Small to medium datasets"],
            avoid_when=["Long category names", "Too many categories"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.LOLLIPOP],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BAR_GROUPED,
            category=ChartCategory.COMPARISON,
            name="Grouped Bar Chart",
            description="Compare multiple series across categories side by side.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=5,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=15
            ),
            best_for=["Comparing multiple metrics", "Before/after comparisons", "Multi-dimensional comparison"],
            avoid_when=["Single metric", "Too many series (>5)"],
            alternatives=[ChartType.BAR_STACKED, ChartType.RADAR],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BAR_STACKED,
            category=ChartCategory.COMPARISON,
            name="Stacked Bar Chart",
            description="Show composition and total across categories.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=8,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=20,
                requires_positive=True
            ),
            best_for=["Showing composition", "Part-to-whole with comparison", "Cumulative totals"],
            avoid_when=["Negative values", "Comparing individual segments"],
            alternatives=[ChartType.BAR_GROUPED, ChartType.STACKED_AREA_PERCENT],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BAR_DIVERGING,
            category=ChartCategory.COMPARISON,
            name="Diverging Bar Chart",
            description="Show positive and negative values diverging from a center axis.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=2,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=25
            ),
            best_for=["Positive vs negative", "Survey results", "Sentiment analysis", "Profit/loss"],
            avoid_when=["All positive values", "No natural center point"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.WATERFALL],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.LOLLIPOP,
            category=ChartCategory.COMPARISON,
            name="Lollipop Chart",
            description="Minimalist alternative to bar chart with dots on stems.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=30
            ),
            best_for=["Clean comparisons", "When bars look too heavy", "Many categories"],
            avoid_when=["Need to show stacked data"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.DOT_PLOT],
            complexity=1, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BULLET,
            category=ChartCategory.COMPARISON,
            name="Bullet Chart",
            description="Show actual vs target with qualitative ranges.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=3,
                min_categorical_cols=0, max_categorical_cols=1,
                max_categories=10
            ),
            best_for=["KPIs vs targets", "Performance dashboards", "Goal tracking"],
            avoid_when=["No target to compare against"],
            alternatives=[ChartType.GAUGE, ChartType.BAR_HORIZONTAL],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DOT_PLOT,
            category=ChartCategory.COMPARISON,
            name="Dot Plot",
            description="Show values as dots along an axis for precise comparison.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=3,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=40
            ),
            best_for=["Precise value comparison", "Multiple metrics per category", "Cleveland dot plots"],
            avoid_when=["Need to emphasize magnitude"],
            alternatives=[ChartType.LOLLIPOP, ChartType.BAR_HORIZONTAL],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DUMBBELL,
            category=ChartCategory.COMPARISON,
            name="Dumbbell Chart",
            description="Show change between two points (before/after, start/end).",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=25,
                requires_pairs=True
            ),
            best_for=["Before/after comparisons", "Range visualization", "Gap analysis"],
            avoid_when=["More than two time points", "Single values"],
            alternatives=[ChartType.SLOPE, ChartType.BAR_GROUPED],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SLOPE,
            category=ChartCategory.COMPARISON,
            name="Slope Chart",
            description="Show change in ranking or value between two points.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=15,
                requires_pairs=True
            ),
            best_for=["Ranking changes", "Two-period comparison", "Before/after"],
            avoid_when=["More than two time points", "Too many items (>15)"],
            alternatives=[ChartType.DUMBBELL, ChartType.BUMP],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RADAR,
            category=ChartCategory.COMPARISON,
            name="Radar Chart (Spider)",
            description="Compare multiple quantitative variables on axes from center.",
            requirements=ChartRequirements(
                min_numeric_cols=3, max_numeric_cols=12,
                min_categorical_cols=0, max_categorical_cols=1,
                max_categories=5
            ),
            best_for=["Multi-dimensional comparison", "Skill profiles", "Product comparison"],
            avoid_when=["More than 12 variables", "Variables on different scales"],
            alternatives=[ChartType.BAR_GROUPED, ChartType.PARALLEL_COORDINATES],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RADIAL_BAR,
            category=ChartCategory.COMPARISON,
            name="Radial Bar Chart",
            description="Circular bar chart for visual appeal.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=12
            ),
            best_for=["Visual appeal", "Cyclic data", "Limited categories"],
            avoid_when=["Precise comparison needed", "Many categories"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.DONUT],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.PICTOGRAM,
            category=ChartCategory.COMPARISON,
            name="Pictogram Chart",
            description="Use icons/symbols to represent quantities.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=10
            ),
            best_for=["Infographics", "Public presentations", "Making data engaging"],
            avoid_when=["Precise values needed", "Large numbers"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.WAFFLE],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RANGE_PLOT,
            category=ChartCategory.COMPARISON,
            name="Range Plot",
            description="Show minimum to maximum range for each category.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=25
            ),
            best_for=["Min/max ranges", "Price ranges", "Confidence intervals"],
            avoid_when=["Single point data"],
            alternatives=[ChartType.DUMBBELL, ChartType.BOX],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.WATERFALL,
            category=ChartCategory.COMPARISON,
            name="Waterfall Chart",
            description="Show how initial value changes through positive/negative adjustments.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_categories=3, max_categories=20
            ),
            best_for=["Financial analysis", "Variance analysis", "Cumulative changes"],
            avoid_when=["No sequential relationship", "Non-additive data"],
            alternatives=[ChartType.BAR_STACKED, ChartType.BAR_DIVERGING],
            complexity=3, popularity=3
        ))
        
        # =====================================================================
        # CORRELATION CHARTS (7)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.SCATTER,
            category=ChartCategory.CORRELATION,
            name="Scatter Plot",
            description="Show relationship between two numeric variables.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_rows=10
            ),
            best_for=["Correlation analysis", "Outlier detection", "Pattern discovery"],
            avoid_when=["Categorical comparison", "Time series"],
            alternatives=[ChartType.BUBBLE, ChartType.HEATMAP],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SCATTER_CONNECTED,
            category=ChartCategory.CORRELATION,
            name="Connected Scatter Plot",
            description="Scatter plot with points connected in order.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_rows=5
            ),
            best_for=["Trajectory over time", "Ordered relationships", "Path visualization"],
            avoid_when=["No natural order"],
            alternatives=[ChartType.SCATTER, ChartType.LINE],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BUBBLE,
            category=ChartCategory.CORRELATION,
            name="Bubble Chart",
            description="Scatter plot with a third variable encoded as bubble size.",
            requirements=ChartRequirements(
                min_numeric_cols=3, max_numeric_cols=3,
                min_rows=5,
                requires_positive=True  # For size
            ),
            best_for=["Three-variable relationships", "Population data", "Market analysis"],
            avoid_when=["Precise size comparison needed", "Negative size values"],
            alternatives=[ChartType.SCATTER, ChartType.HEATMAP],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.HEATMAP,
            category=ChartCategory.CORRELATION,
            name="Heatmap",
            description="Show values in a matrix using color intensity.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                min_categorical_cols=2, max_categorical_cols=2
            ),
            best_for=["Matrix data", "Correlation matrices", "Time-based patterns"],
            avoid_when=["Too many categories", "Single dimension"],
            alternatives=[ChartType.CORRELATION_MATRIX, ChartType.BUBBLE],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CORRELATION_MATRIX,
            category=ChartCategory.CORRELATION,
            name="Correlation Matrix",
            description="Show correlations between all pairs of numeric variables.",
            requirements=ChartRequirements(
                min_numeric_cols=3,
                min_rows=10
            ),
            best_for=["Exploring relationships", "Feature analysis", "Variable selection"],
            avoid_when=["Few variables (<3)", "Non-numeric data"],
            alternatives=[ChartType.HEATMAP, ChartType.SCATTER],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CONTOUR,
            category=ChartCategory.CORRELATION,
            name="Contour Plot",
            description="Show density of points in 2D space with contour lines.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_rows=50
            ),
            best_for=["High-density scatter data", "Density visualization", "Statistical analysis"],
            avoid_when=["Few data points", "Discrete data"],
            alternatives=[ChartType.SCATTER, ChartType.HEATMAP],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.QUADRANT,
            category=ChartCategory.CORRELATION,
            name="Quadrant Chart",
            description="Scatter plot divided into four quadrants for classification.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=2,
                min_categorical_cols=0, max_categorical_cols=1,
                min_rows=5
            ),
            best_for=["Strategic analysis", "Priority matrix", "BCG matrix", "Performance vs potential"],
            avoid_when=["No meaningful center point"],
            alternatives=[ChartType.SCATTER, ChartType.BUBBLE],
            complexity=2, popularity=3
        ))
        
        # =====================================================================
        # PART-TO-WHOLE CHARTS (15)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.PIE,
            category=ChartCategory.PART_TO_WHOLE,
            name="Pie Chart",
            description="Show proportions of a whole as slices.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_categories=2, max_categories=6,
                requires_positive=True
            ),
            best_for=["Simple composition", "Few categories (≤6)", "Part of whole"],
            avoid_when=["Many categories", "Comparing values precisely", "Similar sizes"],
            alternatives=[ChartType.DONUT, ChartType.BAR_HORIZONTAL, ChartType.TREEMAP],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DONUT,
            category=ChartCategory.PART_TO_WHOLE,
            name="Donut Chart",
            description="Pie chart with center space for additional info.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_categories=2, max_categories=8,
                requires_positive=True
            ),
            best_for=["Composition with center metric", "Modern dashboards", "KPI with breakdown"],
            avoid_when=["Many categories", "Precise comparison"],
            alternatives=[ChartType.PIE, ChartType.TREEMAP],
            complexity=1, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DONUT_SEMI,
            category=ChartCategory.PART_TO_WHOLE,
            name="Semi-Circle Donut",
            description="Half donut chart, good for gauges and progress.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=0, max_categorical_cols=1,
                max_categories=5,
                requires_positive=True
            ),
            best_for=["Progress indicators", "Goal completion", "Limited space"],
            avoid_when=["Many categories", "Full composition view needed"],
            alternatives=[ChartType.GAUGE, ChartType.DONUT],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.TREEMAP,
            category=ChartCategory.PART_TO_WHOLE,
            name="Treemap",
            description="Nested rectangles showing hierarchical composition.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=3,
                requires_positive=True
            ),
            best_for=["Hierarchical data", "Many categories", "Space-efficient composition"],
            avoid_when=["Few categories", "No hierarchy", "Need precise comparison"],
            alternatives=[ChartType.SUNBURST, ChartType.BAR_STACKED],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.TREEMAP_CIRCULAR,
            category=ChartCategory.PART_TO_WHOLE,
            name="Circular Treemap",
            description="Treemap with circular packing instead of rectangles.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=2,
                requires_positive=True
            ),
            best_for=["Visual appeal", "Hierarchical data", "Organic look"],
            avoid_when=["Precise comparison needed"],
            alternatives=[ChartType.TREEMAP, ChartType.SUNBURST],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SUNBURST,
            category=ChartCategory.PART_TO_WHOLE,
            name="Sunburst Chart",
            description="Radial treemap showing hierarchical data in rings.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=2, max_categorical_cols=4,
                requires_positive=True,
                requires_hierarchy=True
            ),
            best_for=["Hierarchical composition", "Drill-down analysis", "Multi-level breakdown"],
            avoid_when=["Flat data", "Too many levels (>4)"],
            alternatives=[ChartType.TREEMAP, ChartType.ICICLE],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.WAFFLE,
            category=ChartCategory.PART_TO_WHOLE,
            name="Waffle Chart",
            description="Grid of squares showing percentage composition.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=5,
                requires_positive=True
            ),
            best_for=["Percentage visualization", "Part of 100", "Infographics"],
            avoid_when=["Many categories", "Non-percentage data"],
            alternatives=[ChartType.PIE, ChartType.PICTOGRAM],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.PARLIAMENT,
            category=ChartCategory.PART_TO_WHOLE,
            name="Parliament Chart",
            description="Semicircle of dots showing seat distribution.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=10,
                requires_positive=True
            ),
            best_for=["Political data", "Seat distribution", "Voting representation"],
            avoid_when=["Non-discrete data", "Non-political context"],
            alternatives=[ChartType.DONUT, ChartType.WAFFLE],
            complexity=3, popularity=1
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.MARIMEKKO,
            category=ChartCategory.PART_TO_WHOLE,
            name="Marimekko Chart",
            description="Variable-width stacked bar showing two-dimensional composition.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=2, max_categorical_cols=2,
                max_categories=10,
                requires_positive=True
            ),
            best_for=["Market share analysis", "Two-dimensional composition", "Business strategy"],
            avoid_when=["Single dimension", "Too many categories"],
            alternatives=[ChartType.STACKED_BAR_PERCENT, ChartType.TREEMAP],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.STACKED_AREA_PERCENT,
            category=ChartCategory.PART_TO_WHOLE,
            name="100% Stacked Area",
            description="Show composition changes over time, normalized to 100%.",
            requirements=ChartRequirements(
                min_numeric_cols=2,
                requires_datetime=True,
                requires_positive=True
            ),
            best_for=["Composition over time", "Market share trends", "Proportional changes"],
            avoid_when=["Absolute values important", "Few time points"],
            alternatives=[ChartType.AREA_STACKED, ChartType.STACKED_BAR_PERCENT],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.STACKED_BAR_PERCENT,
            category=ChartCategory.PART_TO_WHOLE,
            name="100% Stacked Bar",
            description="Show composition across categories, normalized to 100%.",
            requirements=ChartRequirements(
                min_numeric_cols=2,
                min_categorical_cols=1, max_categorical_cols=1,
                max_categories=20,
                requires_positive=True
            ),
            best_for=["Comparing proportions", "Survey results", "Composition comparison"],
            avoid_when=["Absolute values important"],
            alternatives=[ChartType.BAR_STACKED, ChartType.MARIMEKKO],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.FUNNEL,
            category=ChartCategory.PART_TO_WHOLE,
            name="Funnel Chart",
            description="Show progressive reduction through stages.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_categories=3, max_categories=8,
                requires_positive=True
            ),
            best_for=["Sales funnel", "Conversion rates", "Process stages"],
            avoid_when=["No sequential relationship", "Non-decreasing data"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.SANKEY],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.PYRAMID,
            category=ChartCategory.PART_TO_WHOLE,
            name="Pyramid Chart",
            description="Triangular chart showing hierarchical structure.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_categories=3, max_categories=7,
                requires_positive=True
            ),
            best_for=["Hierarchical levels", "Priority tiers", "Population pyramids"],
            avoid_when=["Non-hierarchical data"],
            alternatives=[ChartType.FUNNEL, ChartType.BAR_HORIZONTAL],
            complexity=2, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.VENN,
            category=ChartCategory.PART_TO_WHOLE,
            name="Venn Diagram",
            description="Show overlapping sets and their intersections.",
            requirements=ChartRequirements(
                min_categorical_cols=2, max_categorical_cols=4
            ),
            best_for=["Set relationships", "Overlapping categories", "Shared attributes"],
            avoid_when=["More than 4 sets", "No overlaps"],
            alternatives=[ChartType.CHORD],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.ICICLE,
            category=ChartCategory.PART_TO_WHOLE,
            name="Icicle Chart",
            description="Rectangular version of sunburst for hierarchical data.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=2, max_categorical_cols=4,
                requires_positive=True,
                requires_hierarchy=True
            ),
            best_for=["Hierarchical data", "File system visualization", "Org charts"],
            avoid_when=["Flat data", "Too deep hierarchy"],
            alternatives=[ChartType.SUNBURST, ChartType.TREEMAP],
            complexity=3, popularity=2
        ))
        
        # =====================================================================
        # TIME SERIES CHARTS (11)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.LINE,
            category=ChartCategory.TIME_SERIES,
            name="Line Chart",
            description="Show trends over time with connected points.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=2
            ),
            best_for=["Time series trends", "Continuous data", "Change over time"],
            avoid_when=["Categorical comparison", "Discontinuous data"],
            alternatives=[ChartType.AREA, ChartType.SPLINE],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.LINE_MULTI,
            category=ChartCategory.TIME_SERIES,
            name="Multi-Line Chart",
            description="Compare multiple series over time.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=8,
                requires_datetime=True,
                min_rows=2
            ),
            best_for=["Comparing trends", "Multiple metrics over time", "Performance tracking"],
            avoid_when=["Too many lines (>8)", "Very different scales"],
            alternatives=[ChartType.AREA_STACKED, ChartType.LINE],
            complexity=2, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.AREA,
            category=ChartCategory.TIME_SERIES,
            name="Area Chart",
            description="Line chart with filled area below, emphasizing volume.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=2
            ),
            best_for=["Cumulative data", "Volume over time", "Emphasizing magnitude"],
            avoid_when=["Negative values", "Multiple overlapping series"],
            alternatives=[ChartType.LINE, ChartType.AREA_STACKED],
            complexity=1, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.AREA_STACKED,
            category=ChartCategory.TIME_SERIES,
            name="Stacked Area Chart",
            description="Show composition changes over time with stacked areas.",
            requirements=ChartRequirements(
                min_numeric_cols=2, max_numeric_cols=8,
                requires_datetime=True,
                requires_positive=True
            ),
            best_for=["Composition over time", "Part-to-whole trends", "Cumulative totals"],
            avoid_when=["Comparing individual series", "Negative values"],
            alternatives=[ChartType.LINE_MULTI, ChartType.STACKED_AREA_PERCENT],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.STREAM,
            category=ChartCategory.TIME_SERIES,
            name="Streamgraph",
            description="Smoothed stacked area centered on axis for aesthetic flow.",
            requirements=ChartRequirements(
                min_numeric_cols=3,
                requires_datetime=True,
                requires_positive=True
            ),
            best_for=["Composition evolution", "Music/cultural data", "Aesthetic presentations"],
            avoid_when=["Precise values needed", "Few categories"],
            alternatives=[ChartType.AREA_STACKED, ChartType.BUMP],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.STEP,
            category=ChartCategory.TIME_SERIES,
            name="Step Chart",
            description="Line chart with stepped transitions for discrete changes.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=2
            ),
            best_for=["Discrete changes", "Price changes", "Inventory levels"],
            avoid_when=["Continuous data", "Smooth trends"],
            alternatives=[ChartType.LINE, ChartType.BAR_VERTICAL],
            complexity=1, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SPLINE,
            category=ChartCategory.TIME_SERIES,
            name="Spline Chart",
            description="Smoothed line chart with curved transitions.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=3
            ),
            best_for=["Smooth trends", "Natural phenomena", "Aesthetic presentations"],
            avoid_when=["Exact values important", "Discrete data"],
            alternatives=[ChartType.LINE, ChartType.AREA],
            complexity=1, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BUMP,
            category=ChartCategory.TIME_SERIES,
            name="Bump Chart",
            description="Show ranking changes over time.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                requires_datetime=True,
                max_categories=15
            ),
            best_for=["Ranking over time", "Competition positions", "League tables"],
            avoid_when=["Absolute values matter", "Too many items (>15)"],
            alternatives=[ChartType.LINE_MULTI, ChartType.SLOPE],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CANDLESTICK,
            category=ChartCategory.TIME_SERIES,
            name="Candlestick Chart",
            description="Show open, high, low, close for financial data.",
            requirements=ChartRequirements(
                min_numeric_cols=4, max_numeric_cols=4,
                requires_datetime=True
            ),
            best_for=["Stock prices", "Financial analysis", "OHLC data"],
            avoid_when=["Non-financial data", "Single values"],
            alternatives=[ChartType.OHLC, ChartType.LINE],
            complexity=3, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.OHLC,
            category=ChartCategory.TIME_SERIES,
            name="OHLC Chart",
            description="Open-high-low-close bars for financial data.",
            requirements=ChartRequirements(
                min_numeric_cols=4, max_numeric_cols=4,
                requires_datetime=True
            ),
            best_for=["Stock prices", "Trading data", "Financial analysis"],
            avoid_when=["Non-financial data"],
            alternatives=[ChartType.CANDLESTICK, ChartType.LINE],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.GANTT,
            category=ChartCategory.TIME_SERIES,
            name="Gantt Chart",
            description="Show project timeline with task durations.",
            requirements=ChartRequirements(
                min_categorical_cols=1, max_categorical_cols=1,
                requires_datetime=True
            ),
            best_for=["Project timelines", "Task scheduling", "Resource planning"],
            avoid_when=["No duration data", "Non-temporal data"],
            alternatives=[ChartType.BAR_HORIZONTAL],
            complexity=3, popularity=4
        ))
        
        # =====================================================================
        # DISTRIBUTION CHARTS (12)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.HISTOGRAM,
            category=ChartCategory.DISTRIBUTION,
            name="Histogram",
            description="Show distribution of numeric values in bins.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_rows=10
            ),
            best_for=["Distribution analysis", "Frequency", "Understanding data shape"],
            avoid_when=["Few data points", "Categorical data"],
            alternatives=[ChartType.DENSITY, ChartType.BOX],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.HISTOGRAM_STACKED,
            category=ChartCategory.DISTRIBUTION,
            name="Stacked Histogram",
            description="Compare distributions across groups.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_rows=20
            ),
            best_for=["Comparing distributions", "Group differences", "Composition within bins"],
            avoid_when=["Too many groups", "Overlapping needed"],
            alternatives=[ChartType.RIDGELINE, ChartType.BOX],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DENSITY,
            category=ChartCategory.DISTRIBUTION,
            name="Density Plot",
            description="Smooth estimate of distribution using kernel density.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_rows=20
            ),
            best_for=["Smooth distribution", "Comparing groups", "Statistical analysis"],
            avoid_when=["Few data points", "Need exact frequencies"],
            alternatives=[ChartType.HISTOGRAM, ChartType.VIOLIN],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BOX,
            category=ChartCategory.DISTRIBUTION,
            name="Box Plot",
            description="Show distribution summary: median, quartiles, outliers.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                min_rows=5
            ),
            best_for=["Distribution summary", "Outlier detection", "Comparing groups"],
            avoid_when=["Small samples", "Non-numeric data"],
            alternatives=[ChartType.VIOLIN, ChartType.STRIP],
            complexity=2, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.VIOLIN,
            category=ChartCategory.DISTRIBUTION,
            name="Violin Plot",
            description="Combination of box plot and density plot.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                min_rows=20
            ),
            best_for=["Distribution shape", "Comparing groups", "Statistical presentations"],
            avoid_when=["Small samples (<20)", "Need simplicity"],
            alternatives=[ChartType.BOX, ChartType.RIDGELINE],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.STRIP,
            category=ChartCategory.DISTRIBUTION,
            name="Strip Plot",
            description="Show all individual data points along an axis.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                max_rows=500
            ),
            best_for=["Small datasets", "Seeing all points", "Outlier identification"],
            avoid_when=["Many overlapping points", "Large datasets"],
            alternatives=[ChartType.SWARM, ChartType.BOX],
            complexity=1, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SWARM,
            category=ChartCategory.DISTRIBUTION,
            name="Swarm Plot (Beeswarm)",
            description="Strip plot with points adjusted to avoid overlap.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                max_rows=500
            ),
            best_for=["Seeing all points", "Moderate datasets", "Distribution + individual values"],
            avoid_when=["Large datasets", "Need speed"],
            alternatives=[ChartType.STRIP, ChartType.VIOLIN],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RIDGELINE,
            category=ChartCategory.DISTRIBUTION,
            name="Ridgeline Plot",
            description="Multiple overlapping density plots for comparison.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                min_rows=30,
                min_categories=3, max_categories=20
            ),
            best_for=["Comparing many distributions", "Time-based distributions", "Survey responses"],
            avoid_when=["Few groups", "Small samples"],
            alternatives=[ChartType.VIOLIN, ChartType.BOX],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.QQ_PLOT,
            category=ChartCategory.DISTRIBUTION,
            name="Q-Q Plot",
            description="Compare distribution to theoretical distribution.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_rows=20
            ),
            best_for=["Normality testing", "Distribution comparison", "Statistical validation"],
            avoid_when=["Non-statistical audience", "Small samples"],
            alternatives=[ChartType.HISTOGRAM, ChartType.DENSITY],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.ECDF,
            category=ChartCategory.DISTRIBUTION,
            name="ECDF Plot",
            description="Empirical cumulative distribution function.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_rows=10
            ),
            best_for=["Distribution comparison", "Percentiles", "Statistical analysis"],
            avoid_when=["Non-technical audience"],
            alternatives=[ChartType.HISTOGRAM, ChartType.BOX],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.KDE,
            category=ChartCategory.DISTRIBUTION,
            name="KDE Plot",
            description="Kernel density estimate, similar to smoothed histogram.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_rows=20
            ),
            best_for=["Smooth distribution", "Multiple groups", "Statistical presentations"],
            avoid_when=["Exact frequencies needed", "Few data points"],
            alternatives=[ChartType.HISTOGRAM, ChartType.DENSITY],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RAINCLOUD,
            category=ChartCategory.DISTRIBUTION,
            name="Raincloud Plot",
            description="Combination of violin, box, and strip plot.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                min_rows=20
            ),
            best_for=["Complete distribution view", "Statistical presentations", "Academic papers"],
            avoid_when=["Simplicity needed", "Small samples"],
            alternatives=[ChartType.VIOLIN, ChartType.BOX],
            complexity=3, popularity=2
        ))
        
        # =====================================================================
        # GEOSPATIAL CHARTS (6)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.CHOROPLETH,
            category=ChartCategory.GEOSPATIAL,
            name="Choropleth Map",
            description="Geographic regions colored by data value.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                requires_geographic=True
            ),
            best_for=["Regional data", "Country/state comparisons", "Geographic patterns"],
            avoid_when=["No geographic component", "Point data"],
            alternatives=[ChartType.BUBBLE_MAP, ChartType.TILE_MAP],
            complexity=3, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.BUBBLE_MAP,
            category=ChartCategory.GEOSPATIAL,
            name="Bubble Map",
            description="Map with bubbles sized by value at locations.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                requires_geographic=True
            ),
            best_for=["Point-based geographic data", "City data", "Event locations"],
            avoid_when=["Regional aggregates", "Too many overlapping points"],
            alternatives=[ChartType.CHOROPLETH, ChartType.POINT_MAP],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.HEATMAP_GEO,
            category=ChartCategory.GEOSPATIAL,
            name="Geographic Heatmap",
            description="Density map showing concentration of points.",
            requirements=ChartRequirements(
                min_rows=50,
                requires_geographic=True
            ),
            best_for=["Density visualization", "Hotspots", "Many points"],
            avoid_when=["Few points", "Regional aggregates"],
            alternatives=[ChartType.BUBBLE_MAP, ChartType.POINT_MAP],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.POINT_MAP,
            category=ChartCategory.GEOSPATIAL,
            name="Point Map",
            description="Simple map with points at locations.",
            requirements=ChartRequirements(
                requires_geographic=True
            ),
            best_for=["Location plotting", "Simple geographic data", "Event mapping"],
            avoid_when=["Need to show magnitude", "Too many points"],
            alternatives=[ChartType.BUBBLE_MAP, ChartType.HEATMAP_GEO],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CONNECTION_MAP,
            category=ChartCategory.GEOSPATIAL,
            name="Connection Map",
            description="Map showing lines connecting locations.",
            requirements=ChartRequirements(
                requires_geographic=True,
                requires_source_target=True
            ),
            best_for=["Routes", "Flights", "Trade flows", "Migration"],
            avoid_when=["No origin-destination data"],
            alternatives=[ChartType.SANKEY, ChartType.ARC],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.TILE_MAP,
            category=ChartCategory.GEOSPATIAL,
            name="Tile Map",
            description="Equal-sized tiles for each region (cartogram).",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=1, max_categorical_cols=1,
                requires_geographic=True
            ),
            best_for=["Equal representation", "Electoral maps", "Avoiding size bias"],
            avoid_when=["Geographic accuracy important"],
            alternatives=[ChartType.CHOROPLETH, ChartType.WAFFLE],
            complexity=3, popularity=2
        ))
        
        # =====================================================================
        # FLOW & RELATIONSHIP CHARTS (8)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.SANKEY,
            category=ChartCategory.FLOW,
            name="Sankey Diagram",
            description="Show flow quantities between nodes.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=2,
                requires_source_target=True,
                requires_positive=True
            ),
            best_for=["Flow visualization", "Budget allocation", "Process flows", "Energy flows"],
            avoid_when=["No flow relationship", "Negative values"],
            alternatives=[ChartType.ALLUVIAL, ChartType.CHORD],
            complexity=3, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CHORD,
            category=ChartCategory.FLOW,
            name="Chord Diagram",
            description="Show flows between entities in a circle.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                min_categorical_cols=2,
                requires_source_target=True,
                requires_positive=True
            ),
            best_for=["Interconnections", "Migration", "Trade between entities"],
            avoid_when=["Too many entities (>15)", "Directional flow important"],
            alternatives=[ChartType.SANKEY, ChartType.NETWORK],
            complexity=4, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.NETWORK,
            category=ChartCategory.FLOW,
            name="Network Diagram",
            description="Show nodes and connections between them.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_source_target=True
            ),
            best_for=["Relationships", "Social networks", "Dependencies"],
            avoid_when=["Too many nodes", "No relationships"],
            alternatives=[ChartType.CHORD, ChartType.ARC],
            complexity=4, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.ARC,
            category=ChartCategory.FLOW,
            name="Arc Diagram",
            description="Show connections with arcs on a linear layout.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_source_target=True
            ),
            best_for=["Sequential relationships", "Timeline connections", "Linear layout"],
            avoid_when=["Many crossing connections"],
            alternatives=[ChartType.NETWORK, ChartType.CHORD],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.ALLUVIAL,
            category=ChartCategory.FLOW,
            name="Alluvial Diagram",
            description="Show flow changes across multiple stages.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_positive=True
            ),
            best_for=["Multi-stage flows", "Category transitions", "Survey panel data"],
            avoid_when=["Single stage", "No flow relationship"],
            alternatives=[ChartType.SANKEY, ChartType.PARALLEL_SETS],
            complexity=4, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.FLOW_MAP,
            category=ChartCategory.FLOW,
            name="Flow Map",
            description="Geographic map showing flows between locations.",
            requirements=ChartRequirements(
                min_numeric_cols=1,
                requires_geographic=True,
                requires_source_target=True
            ),
            best_for=["Migration", "Trade routes", "Transportation flows"],
            avoid_when=["No geographic component"],
            alternatives=[ChartType.CONNECTION_MAP, ChartType.SANKEY],
            complexity=4, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.PARALLEL_COORDINATES,
            category=ChartCategory.FLOW,
            name="Parallel Coordinates",
            description="Show multi-dimensional data with parallel axes.",
            requirements=ChartRequirements(
                min_numeric_cols=3,
                min_rows=10
            ),
            best_for=["Multi-dimensional analysis", "Pattern detection", "Clustering"],
            avoid_when=["Few variables (<3)", "Non-numeric data"],
            alternatives=[ChartType.RADAR, ChartType.PARALLEL_SETS],
            complexity=3, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.PARALLEL_SETS,
            category=ChartCategory.FLOW,
            name="Parallel Sets",
            description="Parallel coordinates for categorical data.",
            requirements=ChartRequirements(
                min_categorical_cols=3
            ),
            best_for=["Categorical relationships", "Survey data", "Segment analysis"],
            avoid_when=["Numeric data", "Few categories"],
            alternatives=[ChartType.ALLUVIAL, ChartType.SANKEY],
            complexity=3, popularity=2
        ))
        
        # =====================================================================
        # SPECIALIZED CHARTS (6)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.GAUGE,
            category=ChartCategory.SPECIALIZED,
            name="Gauge Chart",
            description="Show single value against a scale, like a speedometer.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                max_rows=1
            ),
            best_for=["KPIs", "Progress to goal", "Single metrics"],
            avoid_when=["Multiple values", "Comparison needed"],
            alternatives=[ChartType.BULLET, ChartType.KPI_CARD],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.SPARKLINE,
            category=ChartCategory.SPECIALIZED,
            name="Sparkline",
            description="Tiny inline chart showing trend.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=5
            ),
            best_for=["Inline trends", "Dashboard KPIs", "Table cells"],
            avoid_when=["Need detailed analysis", "Standalone charts"],
            alternatives=[ChartType.LINE, ChartType.KPI_CARD],
            complexity=2, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.WORD_CLOUD,
            category=ChartCategory.SPECIALIZED,
            name="Word Cloud",
            description="Show word frequency with size encoding.",
            requirements=ChartRequirements(
                min_categorical_cols=1, max_categorical_cols=1,
                min_numeric_cols=1, max_numeric_cols=1
            ),
            best_for=["Text analysis", "Tag visualization", "Survey responses"],
            avoid_when=["Precise comparison needed", "Numeric data"],
            alternatives=[ChartType.BAR_HORIZONTAL, ChartType.TREEMAP],
            complexity=2, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.CALENDAR_HEATMAP,
            category=ChartCategory.SPECIALIZED,
            name="Calendar Heatmap",
            description="Show values on a calendar grid.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                requires_datetime=True,
                min_rows=30
            ),
            best_for=["Daily patterns", "Activity tracking", "Seasonal patterns"],
            avoid_when=["Non-daily data", "Short time periods"],
            alternatives=[ChartType.HEATMAP, ChartType.LINE],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.TABLE,
            category=ChartCategory.SPECIALIZED,
            name="Data Table",
            description="Tabular display of data with formatting.",
            requirements=ChartRequirements(
                min_rows=1
            ),
            best_for=["Exact values", "Detailed data", "Export-ready format"],
            avoid_when=["Pattern detection", "Large datasets"],
            alternatives=[ChartType.HEATMAP],
            complexity=1, popularity=5
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.KPI_CARD,
            category=ChartCategory.SPECIALIZED,
            name="KPI Card",
            description="Display key metric with optional trend indicator.",
            requirements=ChartRequirements(
                min_numeric_cols=1, max_numeric_cols=1,
                max_rows=1
            ),
            best_for=["Dashboard headers", "Executive summaries", "Key metrics"],
            avoid_when=["Detailed analysis", "Multiple values"],
            alternatives=[ChartType.GAUGE, ChartType.BULLET],
            complexity=1, popularity=5
        ))
        
        # =====================================================================
        # HIERARCHY CHARTS (4)
        # =====================================================================
        
        self._register(ChartDefinition(
            chart_type=ChartType.TREE_DIAGRAM,
            category=ChartCategory.HIERARCHY,
            name="Tree Diagram",
            description="Show hierarchical relationships in a tree structure with parent-child connections.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_hierarchy=True
            ),
            best_for=["Organizational structures", "File systems", "Taxonomies", "Decision trees"],
            avoid_when=["Flat data", "No parent-child relationship", "Too many levels (>6)"],
            alternatives=[ChartType.DENDROGRAM, ChartType.SUNBURST, ChartType.ORG_CHART],
            complexity=3, popularity=3
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.DENDROGRAM,
            category=ChartCategory.HIERARCHY,
            name="Dendrogram",
            description="Tree diagram showing hierarchical clustering or evolutionary relationships.",
            requirements=ChartRequirements(
                min_numeric_cols=2,
                min_rows=5
            ),
            best_for=["Clustering results", "Phylogenetic trees", "Similarity analysis", "Hierarchical grouping"],
            avoid_when=["Non-hierarchical data", "Too many items (>100)"],
            alternatives=[ChartType.TREE_DIAGRAM, ChartType.HEATMAP],
            complexity=4, popularity=2
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.ORG_CHART,
            category=ChartCategory.HIERARCHY,
            name="Organization Chart",
            description="Show reporting structure and organizational hierarchy with boxes and connecting lines.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_hierarchy=True
            ),
            best_for=["Company structure", "Reporting lines", "Team organization", "Management hierarchy"],
            avoid_when=["Non-organizational data", "Flat structure"],
            alternatives=[ChartType.TREE_DIAGRAM, ChartType.NETWORK],
            complexity=3, popularity=4
        ))
        
        self._register(ChartDefinition(
            chart_type=ChartType.RADIAL_TREE,
            category=ChartCategory.HIERARCHY,
            name="Radial Tree",
            description="Circular tree layout with root at center, radiating outward by hierarchy level.",
            requirements=ChartRequirements(
                min_categorical_cols=2,
                requires_hierarchy=True
            ),
            best_for=["Deep hierarchies", "Balanced trees", "Visual appeal", "Space-efficient hierarchy"],
            avoid_when=["Unbalanced trees", "Few levels", "Need precise reading"],
            alternatives=[ChartType.TREE_DIAGRAM, ChartType.SUNBURST],
            complexity=4, popularity=2
        ))
    
    def _register(self, chart: ChartDefinition):
        """Register a chart definition"""
        self.charts[chart.chart_type] = chart
    
    def get(self, chart_type: ChartType) -> Optional[ChartDefinition]:
        """Get chart definition by type"""
        return self.charts.get(chart_type)
    
    def get_by_category(self, category: ChartCategory) -> List[ChartDefinition]:
        """Get all charts in a category"""
        return [c for c in self.charts.values() if c.category == category]
    
    def get_all(self) -> List[ChartDefinition]:
        """Get all chart definitions"""
        return list(self.charts.values())
    
    def search(self, query: str) -> List[ChartDefinition]:
        """Search charts by name or description"""
        query_lower = query.lower()
        return [
            c for c in self.charts.values()
            if query_lower in c.name.lower() or query_lower in c.description.lower()
        ]


# =============================================================================
# DATA SHAPE ANALYZER
# =============================================================================

class DataShapeAnalyzer:
    """
    Analyzes data to understand its shape and characteristics.
    """
    
    # Column name patterns for detection
    GEO_PATTERNS = ['country', 'state', 'region', 'city', 'lat', 'lon', 'latitude', 
                    'longitude', 'zip', 'postal', 'province', 'county']
    
    HIERARCHY_PATTERNS = ['parent', 'child', 'level', 'hierarchy', 'category', 
                          'subcategory', 'group', 'subgroup']
    
    SOURCE_TARGET_PATTERNS = [('source', 'target'), ('from', 'to'), ('origin', 'destination'),
                              ('start', 'end'), ('sender', 'receiver')]
    
    def analyze(
        self, 
        df: pd.DataFrame,
        profile: Optional[DataProfile] = None
    ) -> DataCharacteristics:
        """
        Analyze DataFrame to extract characteristics for chart selection.
        
        Args:
            df: DataFrame to analyze
            profile: Optional pre-computed DataProfile
            
        Returns:
            DataCharacteristics
        """
        chars = DataCharacteristics()
        chars.row_count = len(df)
        chars.column_count = len(df.columns)
        
        # Classify columns
        self._classify_columns(df, chars, profile)
        
        # Analyze cardinality
        self._analyze_cardinality(df, chars)
        
        # Check value characteristics
        self._analyze_values(df, chars)
        
        # Detect special patterns
        self._detect_patterns(df, chars)
        
        # Determine data shape
        chars.shape = self._determine_shape(chars)
        
        return chars
    
    def _classify_columns(
        self,
        df: pd.DataFrame,
        chars: DataCharacteristics,
        profile: Optional[DataProfile]
    ):
        """Classify columns by type"""
        for col in df.columns:
            dtype = df[col].dtype
            col_lower = col.lower()
            
            # Check profile first if available
            if profile:
                col_profile = profile.get_column(col)
                if col_profile:
                    if col_profile.dtype in {ColumnType.NUMERIC_CONTINUOUS, ColumnType.NUMERIC_DISCRETE,
                                             ColumnType.NUMERIC_CURRENCY, ColumnType.NUMERIC_PERCENTAGE}:
                        chars.numeric_columns.append(col)
                        continue
                    elif col_profile.dtype in {ColumnType.CATEGORICAL, ColumnType.CATEGORICAL_BINARY,
                                               ColumnType.CATEGORICAL_ORDINAL}:
                        chars.categorical_columns.append(col)
                        continue
                    elif col_profile.dtype in {ColumnType.DATETIME, ColumnType.DATE, ColumnType.TIME}:
                        chars.datetime_columns.append(col)
                        continue
                    elif col_profile.dtype in {ColumnType.ID_NUMERIC, ColumnType.ID_STRING}:
                        chars.id_columns.append(col)
                        continue
                    elif col_profile.dtype in {ColumnType.TEXT_SHORT, ColumnType.TEXT_LONG}:
                        chars.text_columns.append(col)
                        continue
            
            # Fallback to pandas dtype
            if pd.api.types.is_datetime64_any_dtype(dtype):
                chars.datetime_columns.append(col)
            elif pd.api.types.is_numeric_dtype(dtype):
                # Check if it's actually an ID
                if self._is_likely_id(df[col], col_lower):
                    chars.id_columns.append(col)
                else:
                    chars.numeric_columns.append(col)
            elif dtype == 'object' or pd.api.types.is_string_dtype(dtype):
                # Check unique ratio to determine categorical vs text
                unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 0
                avg_len = df[col].astype(str).str.len().mean()
                
                if unique_ratio > 0.9 and avg_len > 20:
                    chars.text_columns.append(col)
                elif unique_ratio > 0.9:
                    chars.id_columns.append(col)
                else:
                    chars.categorical_columns.append(col)
            else:
                chars.categorical_columns.append(col)
    
    def _is_likely_id(self, series: pd.Series, col_name: str) -> bool:
        """Check if a numeric column is likely an ID"""
        id_keywords = ['id', 'key', 'code', 'num', 'number']
        if any(kw in col_name for kw in id_keywords):
            return series.nunique() / len(series) > 0.9 if len(series) > 0 else False
        return False
    
    def _analyze_cardinality(self, df: pd.DataFrame, chars: DataCharacteristics):
        """Analyze cardinality of categorical columns"""
        for col in chars.categorical_columns:
            cardinality = df[col].nunique()
            chars.categorical_cardinality[col] = cardinality
            chars.max_cardinality = max(chars.max_cardinality, cardinality)
    
    def _analyze_values(self, df: pd.DataFrame, chars: DataCharacteristics):
        """Analyze value characteristics"""
        for col in chars.numeric_columns:
            series = df[col].dropna()
            if len(series) > 0:
                if (series < 0).any():
                    chars.has_negative_values = True
                if (series == 0).any():
                    chars.has_zero_values = True
        
        chars.has_missing_values = df.isna().any().any()
    
    def _detect_patterns(self, df: pd.DataFrame, chars: DataCharacteristics):
        """Detect special data patterns"""
        col_names_lower = [c.lower() for c in df.columns]
        
        # Time series detection
        chars.has_time_series = len(chars.datetime_columns) > 0
        
        # Geographic detection
        chars.has_geographic = any(
            any(geo in col for geo in self.GEO_PATTERNS)
            for col in col_names_lower
        )
        
        # Hierarchy detection
        chars.has_hierarchy = any(
            any(hier in col for hier in self.HIERARCHY_PATTERNS)
            for col in col_names_lower
        )
        
        # Source-target detection (for flow charts)
        for source_pattern, target_pattern in self.SOURCE_TARGET_PATTERNS:
            has_source = any(source_pattern in col for col in col_names_lower)
            has_target = any(target_pattern in col for col in col_names_lower)
            if has_source and has_target:
                chars.has_pairs = True
                break
    
    def _determine_shape(self, chars: DataCharacteristics) -> DataShape:
        """Determine the overall data shape"""
        num_cols = len(chars.numeric_columns)
        cat_cols = len(chars.categorical_columns)
        dt_cols = len(chars.datetime_columns)
        
        # Single value (KPI)
        if chars.row_count == 1 and num_cols == 1:
            return DataShape.SINGLE_VALUE
        
        # Time-indexed data
        if dt_cols > 0:
            return DataShape.TIME_INDEXED
        
        # Geographic data
        if chars.has_geographic:
            return DataShape.GEOGRAPHIC
        
        # Hierarchical data
        if chars.has_hierarchy and cat_cols >= 2:
            return DataShape.HIERARCHICAL
        
        # Matrix (many numeric columns, few categorical)
        if num_cols >= 3 and cat_cols == 0:
            return DataShape.MATRIX
        
        # Numeric pair or triple
        if num_cols == 2 and cat_cols == 0:
            return DataShape.NUMERIC_PAIR
        if num_cols == 3 and cat_cols == 0:
            return DataShape.NUMERIC_TRIPLE
        
        # Categorical with multiple numeric
        if cat_cols >= 1 and num_cols >= 2:
            return DataShape.CATEGORICAL_MULTI_NUMERIC
        
        # Categorical with single numeric
        if cat_cols >= 1 and num_cols == 1:
            return DataShape.CATEGORICAL_NUMERIC
        
        # Text heavy
        if len(chars.text_columns) > num_cols + cat_cols:
            return DataShape.TEXT_HEAVY
        
        # Single series
        if num_cols == 1:
            return DataShape.SINGLE_SERIES
        
        # Multi series
        return DataShape.MULTI_SERIES


# =============================================================================
# INTENT DETECTOR
# =============================================================================

class IntentDetector:
    """
    Detects the user's analysis intent from queries and data.
    """
    
    # Intent keywords
    INTENT_KEYWORDS = {
        AnalysisIntent.COMPARISON: [
            'compare', 'versus', 'vs', 'difference', 'between', 'which is',
            'better', 'worse', 'more', 'less', 'highest', 'lowest', 'rank'
        ],
        AnalysisIntent.TREND: [
            'trend', 'over time', 'change', 'growth', 'decline', 'increase',
            'decrease', 'time series', 'forecast', 'predict', 'historical'
        ],
        AnalysisIntent.DISTRIBUTION: [
            'distribution', 'spread', 'range', 'histogram', 'frequency',
            'how many', 'count', 'average', 'median', 'outliers'
        ],
        AnalysisIntent.CORRELATION: [
            'correlation', 'relationship', 'related', 'affect', 'impact',
            'influence', 'depends', 'associated', 'scatter'
        ],
        AnalysisIntent.COMPOSITION: [
            'composition', 'breakdown', 'proportion', 'percentage', 'share',
            'part of', 'makeup', 'consists', 'segments'
        ],
        AnalysisIntent.RANKING: [
            'top', 'bottom', 'best', 'worst', 'ranking', 'leaderboard',
            'first', 'last', 'most', 'least'
        ],
        AnalysisIntent.FLOW: [
            'flow', 'transition', 'movement', 'from to', 'sankey', 'path',
            'journey', 'funnel', 'conversion'
        ],
        AnalysisIntent.GEOGRAPHIC: [
            'map', 'geographic', 'location', 'region', 'country', 'state',
            'city', 'where', 'spatial'
        ],
        AnalysisIntent.KPI: [
            'kpi', 'metric', 'summary', 'total', 'overall', 'dashboard',
            'key', 'indicator', 'performance'
        ]
    }
    
    def detect(
        self,
        query: Optional[str] = None,
        data_chars: Optional[DataCharacteristics] = None
    ) -> AnalysisIntent:
        """
        Detect analysis intent from query and/or data characteristics.
        
        Args:
            query: User's query string
            data_chars: Data characteristics
            
        Returns:
            Detected AnalysisIntent
        """
        # If query provided, analyze it
        if query:
            query_lower = query.lower()
            
            # Score each intent
            intent_scores = {}
            for intent, keywords in self.INTENT_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in query_lower)
                if score > 0:
                    intent_scores[intent] = score
            
            if intent_scores:
                return max(intent_scores, key=intent_scores.get)
        
        # Infer from data characteristics
        if data_chars:
            return self._infer_from_data(data_chars)
        
        return AnalysisIntent.GENERAL
    
    def _infer_from_data(self, chars: DataCharacteristics) -> AnalysisIntent:
        """Infer intent from data characteristics"""
        
        # Geographic data → Geographic intent
        if chars.has_geographic:
            return AnalysisIntent.GEOGRAPHIC
        
        # Time series data → Trend intent
        if chars.has_time_series:
            return AnalysisIntent.TREND
        
        # Single value → KPI
        if chars.shape == DataShape.SINGLE_VALUE:
            return AnalysisIntent.KPI
        
        # Source-target pairs → Flow
        if chars.has_pairs:
            return AnalysisIntent.FLOW
        
        # Two numeric columns → Correlation
        if chars.shape == DataShape.NUMERIC_PAIR:
            return AnalysisIntent.CORRELATION
        
        # Single numeric with categories → Comparison or Distribution
        if chars.shape == DataShape.CATEGORICAL_NUMERIC:
            if chars.max_cardinality <= 15:
                return AnalysisIntent.COMPARISON
            else:
                return AnalysisIntent.DISTRIBUTION
        
        # Multiple numeric with categories → Comparison
        if chars.shape == DataShape.CATEGORICAL_MULTI_NUMERIC:
            return AnalysisIntent.COMPARISON
        
        # Single series → Distribution
        if chars.shape == DataShape.SINGLE_SERIES:
            return AnalysisIntent.DISTRIBUTION
        
        return AnalysisIntent.GENERAL


# =============================================================================
# CHART SCORER
# =============================================================================

class ChartScorer:
    """
    Scores charts based on how well they fit the data.
    """
    
    def score(
        self,
        chart: ChartDefinition,
        chars: DataCharacteristics,
        intent: AnalysisIntent
    ) -> Tuple[float, List[str], List[str]]:
        """
        Score a chart for the given data and intent.
        
        Args:
            chart: Chart definition to score
            chars: Data characteristics
            intent: Analysis intent
            
        Returns:
            Tuple of (score 0-100, fit_reasons, warnings)
        """
        score = 50.0  # Base score
        fit_reasons = []
        warnings = []
        
        req = chart.requirements
        
        # =====================================================================
        # HARD REQUIREMENTS (Disqualifiers)
        # =====================================================================
        
        # Numeric column requirements
        num_cols = len(chars.numeric_columns)
        if req.min_numeric_cols > num_cols:
            return 0, [], [f"Requires at least {req.min_numeric_cols} numeric columns, found {num_cols}"]
        if req.max_numeric_cols is not None and num_cols > req.max_numeric_cols:
            return 0, [], [f"Maximum {req.max_numeric_cols} numeric columns allowed, found {num_cols}"]
        
        # Categorical column requirements
        cat_cols = len(chars.categorical_columns)
        if req.min_categorical_cols > cat_cols:
            return 0, [], [f"Requires at least {req.min_categorical_cols} categorical columns, found {cat_cols}"]
        if req.max_categorical_cols is not None and cat_cols > req.max_categorical_cols:
            return 0, [], [f"Maximum {req.max_categorical_cols} categorical columns allowed"]
        
        # Datetime requirement
        if req.requires_datetime and len(chars.datetime_columns) == 0:
            return 0, [], ["Requires datetime column"]
        
        # Geographic requirement
        if req.requires_geographic and not chars.has_geographic:
            return 0, [], ["Requires geographic data"]
        
        # Hierarchy requirement
        if req.requires_hierarchy and not chars.has_hierarchy:
            return 0, [], ["Requires hierarchical data"]
        
        # Source-target requirement
        if req.requires_source_target and not chars.has_pairs:
            return 0, [], ["Requires source-target pairs"]
        
        # Positive values requirement
        if req.requires_positive and chars.has_negative_values:
            return 0, [], ["Requires all positive values"]
        
        # Row count requirements
        if req.min_rows > chars.row_count:
            return 0, [], [f"Requires at least {req.min_rows} rows"]
        if req.max_rows is not None and chars.row_count > req.max_rows:
            warnings.append(f"Large dataset ({chars.row_count} rows) may affect performance")
        
        # Category count requirements
        if req.min_categories > 0 and chars.max_cardinality < req.min_categories:
            return 0, [], [f"Requires at least {req.min_categories} categories"]
        if req.max_categories is not None and chars.max_cardinality > req.max_categories:
            warnings.append(f"Many categories ({chars.max_cardinality}) may reduce readability")
            score -= 10
        
        # =====================================================================
        # SOFT SCORING (Preferences)
        # =====================================================================
        
        # Intent alignment (big bonus for matching intent)
        intent_category_map = {
            AnalysisIntent.COMPARISON: ChartCategory.COMPARISON,
            AnalysisIntent.TREND: ChartCategory.TIME_SERIES,
            AnalysisIntent.DISTRIBUTION: ChartCategory.DISTRIBUTION,
            AnalysisIntent.CORRELATION: ChartCategory.CORRELATION,
            AnalysisIntent.COMPOSITION: ChartCategory.PART_TO_WHOLE,
            AnalysisIntent.FLOW: ChartCategory.FLOW,
            AnalysisIntent.GEOGRAPHIC: ChartCategory.GEOSPATIAL,
        }
        
        if intent in intent_category_map:
            if chart.category == intent_category_map[intent]:
                score += 25
                fit_reasons.append(f"Matches {intent.value} intent")
        
        # Data shape alignment
        shape_bonus = self._score_shape_alignment(chart, chars)
        score += shape_bonus
        if shape_bonus > 10:
            fit_reasons.append("Good fit for data shape")
        
        # Popularity bonus (common charts are often good choices)
        score += (chart.popularity - 3) * 3  # -6 to +6
        
        # Complexity penalty for complex charts unless specifically needed
        if chart.complexity > 3:
            score -= (chart.complexity - 3) * 5
            if chart.complexity >= 4:
                warnings.append("Complex chart type - consider simpler alternatives")
        
        # Optimal category count
        if req.max_categories and chars.max_cardinality > 0:
            if chars.max_cardinality <= req.max_categories * 0.7:
                score += 5
                fit_reasons.append("Good number of categories")
        
        # Time series bonus for datetime data
        if len(chars.datetime_columns) > 0 and chart.category == ChartCategory.TIME_SERIES:
            score += 15
            fit_reasons.append("Has datetime data for time series")
        
        # =====================================================================
        # SPECIFIC CHART BONUSES
        # =====================================================================
        
        # Horizontal bar for many categories (long labels)
        if chart.chart_type == ChartType.BAR_HORIZONTAL and chars.max_cardinality > 10:
            score += 5
            fit_reasons.append("Horizontal bars good for many categories")
        
        # Scatter for numeric pairs
        if chart.chart_type == ChartType.SCATTER and chars.shape == DataShape.NUMERIC_PAIR:
            score += 20
            fit_reasons.append("Perfect for two numeric variables")
        
        # Pie for few categories
        if chart.chart_type == ChartType.PIE and 2 <= chars.max_cardinality <= 5:
            score += 10
            fit_reasons.append("Good for simple composition")
        elif chart.chart_type == ChartType.PIE and chars.max_cardinality > 6:
            score -= 20
            warnings.append("Too many slices for pie chart")
        
        # KPI card for single value
        if chart.chart_type == ChartType.KPI_CARD and chars.shape == DataShape.SINGLE_VALUE:
            score += 30
            fit_reasons.append("Perfect for single KPI value")
        
        # Histogram for distribution with many rows
        if chart.chart_type == ChartType.HISTOGRAM and chars.row_count > 50:
            score += 10
            fit_reasons.append("Good sample size for histogram")
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        return score, fit_reasons, warnings
    
    def _score_shape_alignment(
        self,
        chart: ChartDefinition,
        chars: DataCharacteristics
    ) -> float:
        """Score based on data shape alignment"""
        bonus = 0
        
        shape_chart_affinity = {
            DataShape.SINGLE_VALUE: [ChartType.KPI_CARD, ChartType.GAUGE],
            DataShape.SINGLE_SERIES: [ChartType.HISTOGRAM, ChartType.DENSITY, ChartType.BOX],
            DataShape.TIME_INDEXED: [ChartType.LINE, ChartType.AREA, ChartType.LINE_MULTI],
            DataShape.CATEGORICAL_NUMERIC: [ChartType.BAR_HORIZONTAL, ChartType.BAR_VERTICAL, ChartType.PIE],
            DataShape.CATEGORICAL_MULTI_NUMERIC: [ChartType.BAR_GROUPED, ChartType.RADAR, ChartType.BAR_STACKED],
            DataShape.NUMERIC_PAIR: [ChartType.SCATTER, ChartType.CONTOUR],
            DataShape.NUMERIC_TRIPLE: [ChartType.BUBBLE, ChartType.SCATTER],
            DataShape.MATRIX: [ChartType.HEATMAP, ChartType.CORRELATION_MATRIX],
            DataShape.HIERARCHICAL: [ChartType.TREEMAP, ChartType.SUNBURST],
            DataShape.GEOGRAPHIC: [ChartType.CHOROPLETH, ChartType.BUBBLE_MAP],
        }
        
        if chars.shape in shape_chart_affinity:
            if chart.chart_type in shape_chart_affinity[chars.shape]:
                bonus += 15
        
        return bonus


# =============================================================================
# MAIN CHART RECOMMENDER CLASS
# =============================================================================

class ChartRecommender:
    """
    Main class for recommending charts based on data analysis.
    
    Analyzes data characteristics and recommends the most suitable
    chart types from 80 available options.
    
    Usage:
        recommender = ChartRecommender()
        
        # Basic recommendation
        recommendations = recommender.recommend(df)
        
        # With pre-computed profile
        profile = DataProfiler().profile(df)
        recommendations = recommender.recommend(df, profile)
        
        # With specific intent
        recommendations = recommender.recommend(df, intent="comparison")
        
        # Access results
        for rec in recommendations[:5]:
            print(f"{rec.name}: {rec.score:.0f}% - {rec.explanation}")
    """
    
    def __init__(self):
        """Initialize the chart recommender."""
        self.registry = ChartRegistry()
        self.shape_analyzer = DataShapeAnalyzer()
        self.intent_detector = IntentDetector()
        self.scorer = ChartScorer()
        
        logger.info(f"ChartRecommender initialized with {len(self.registry.charts)} chart types")
    
    def recommend(
        self,
        df: pd.DataFrame,
        profile: Optional[DataProfile] = None,
        intent: Optional[Union[str, AnalysisIntent]] = None,
        query: Optional[str] = None,
        top_n: int = 10,
        min_score: float = 20.0
    ) -> List[ChartRecommendation]:
        """
        Generate chart recommendations for a DataFrame.
        
        Args:
            df: DataFrame to visualize
            profile: Optional pre-computed DataProfile
            intent: Specific analysis intent (string or enum)
            query: User query for intent detection
            top_n: Maximum number of recommendations to return
            min_score: Minimum score threshold
            
        Returns:
            List of ChartRecommendation sorted by score
        """
        # Analyze data characteristics
        chars = self.shape_analyzer.analyze(df, profile)
        
        # Detect or use provided intent
        if intent:
            if isinstance(intent, str):
                try:
                    detected_intent = AnalysisIntent(intent)
                except ValueError:
                    detected_intent = self.intent_detector.detect(intent, chars)
            else:
                detected_intent = intent
        else:
            detected_intent = self.intent_detector.detect(query, chars)
        
        chars.detected_intent = detected_intent
        
        # Score all charts
        recommendations = []
        for chart in self.registry.get_all():
            score, fit_reasons, warnings = self.scorer.score(chart, chars, detected_intent)
            
            if score >= min_score:
                rec = ChartRecommendation(
                    chart_type=chart.chart_type,
                    category=chart.category,
                    name=chart.name,
                    score=score,
                    rank=0,  # Will be set after sorting
                    explanation=self._generate_explanation(chart, chars, fit_reasons),
                    data_fit_reasons=fit_reasons,
                    warnings=warnings,
                    complexity=chart.complexity
                )
                
                # Add column suggestions
                self._add_column_suggestions(rec, df, chars, chart)
                
                recommendations.append(rec)
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # Assign ranks and limit to top_n
        for i, rec in enumerate(recommendations[:top_n]):
            rec.rank = i + 1
        
        return recommendations[:top_n]
    
    def recommend_for_columns(
        self,
        df: pd.DataFrame,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        color_column: Optional[str] = None,
        top_n: int = 5
    ) -> List[ChartRecommendation]:
        """
        Recommend charts for specific column selections.
        
        Args:
            df: DataFrame
            x_column: Selected X-axis column
            y_column: Selected Y-axis column
            color_column: Selected color/group column
            top_n: Number of recommendations
            
        Returns:
            List of recommendations
        """
        # Build subset DataFrame
        cols = [c for c in [x_column, y_column, color_column] if c and c in df.columns]
        if not cols:
            return self.recommend(df, top_n=top_n)
        
        subset = df[cols]
        
        # Get recommendations
        recommendations = self.recommend(subset, top_n=top_n)
        
        # Update suggestions with user's selections
        for rec in recommendations:
            if x_column:
                rec.suggested_x = x_column
            if y_column:
                rec.suggested_y = y_column
            if color_column:
                rec.suggested_color = color_column
        
        return recommendations
    
    def get_chart_info(self, chart_type: Union[str, ChartType]) -> Optional[ChartDefinition]:
        """
        Get detailed information about a specific chart type.
        
        Args:
            chart_type: Chart type string or enum
            
        Returns:
            ChartDefinition or None
        """
        if isinstance(chart_type, str):
            try:
                chart_type = ChartType(chart_type)
            except ValueError:
                return None
        
        return self.registry.get(chart_type)
    
    def get_charts_by_category(
        self, 
        category: Union[str, ChartCategory]
    ) -> List[ChartDefinition]:
        """
        Get all charts in a category.
        
        Args:
            category: Category string or enum
            
        Returns:
            List of ChartDefinition
        """
        if isinstance(category, str):
            try:
                category = ChartCategory(category)
            except ValueError:
                return []
        
        return self.registry.get_by_category(category)
    
    def search_charts(self, query: str) -> List[ChartDefinition]:
        """
        Search charts by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching ChartDefinition
        """
        return self.registry.search(query)
    
    def analyze_data(
        self,
        df: pd.DataFrame,
        profile: Optional[DataProfile] = None
    ) -> DataCharacteristics:
        """
        Analyze data characteristics without recommending charts.
        
        Args:
            df: DataFrame to analyze
            profile: Optional pre-computed profile
            
        Returns:
            DataCharacteristics
        """
        return self.shape_analyzer.analyze(df, profile)
    
    def _generate_explanation(
        self,
        chart: ChartDefinition,
        chars: DataCharacteristics,
        fit_reasons: List[str]
    ) -> str:
        """Generate human-readable explanation"""
        parts = [chart.description]
        
        if fit_reasons:
            parts.append(f"Good fit because: {', '.join(fit_reasons[:2])}")
        
        return " ".join(parts)
    
    def _add_column_suggestions(
        self,
        rec: ChartRecommendation,
        df: pd.DataFrame,
        chars: DataCharacteristics,
        chart: ChartDefinition
    ):
        """Add suggested column mappings"""
        # Categorical for X if comparison chart
        if chart.category == ChartCategory.COMPARISON and chars.categorical_columns:
            rec.suggested_x = chars.categorical_columns[0]
            if chars.numeric_columns:
                rec.suggested_y = chars.numeric_columns[0]
        
        # Datetime for X if time series
        elif chart.category == ChartCategory.TIME_SERIES and chars.datetime_columns:
            rec.suggested_x = chars.datetime_columns[0]
            if chars.numeric_columns:
                rec.suggested_y = chars.numeric_columns[0]
        
        # Numeric pair for scatter
        elif chart.chart_type == ChartType.SCATTER and len(chars.numeric_columns) >= 2:
            rec.suggested_x = chars.numeric_columns[0]
            rec.suggested_y = chars.numeric_columns[1]
        
        # Default numeric for Y
        elif chars.numeric_columns:
            rec.suggested_y = chars.numeric_columns[0]
        
        # Color by categorical if available
        if len(chars.categorical_columns) > 1:
            rec.suggested_color = chars.categorical_columns[1]
        elif chars.categorical_columns and rec.suggested_x != chars.categorical_columns[0]:
            rec.suggested_color = chars.categorical_columns[0]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about recommender capabilities"""
        categories = {}
        for cat in ChartCategory:
            charts = self.registry.get_by_category(cat)
            categories[cat.value] = len(charts)
        
        return {
            "total_charts": len(self.registry.charts),
            "categories": categories,
            "intents": [i.value for i in AnalysisIntent],
            "data_shapes": [s.value for s in DataShape]
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def recommend_charts(
    df: pd.DataFrame,
    top_n: int = 5
) -> List[ChartRecommendation]:
    """
    Quick chart recommendation for a DataFrame.
    
    Args:
        df: DataFrame to visualize
        top_n: Number of recommendations
        
    Returns:
        List of ChartRecommendation
    """
    recommender = ChartRecommender()
    return recommender.recommend(df, top_n=top_n)


def get_best_chart(df: pd.DataFrame) -> Optional[ChartRecommendation]:
    """
    Get the single best chart recommendation.
    
    Args:
        df: DataFrame to visualize
        
    Returns:
        Best ChartRecommendation or None
    """
    recommendations = recommend_charts(df, top_n=1)
    return recommendations[0] if recommendations else None


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'ChartRecommender',
    
    # Result classes
    'ChartRecommendation',
    'ChartDefinition',
    'ChartRequirements',
    'DataCharacteristics',
    
    # Component classes
    'ChartRegistry',
    'DataShapeAnalyzer',
    'IntentDetector',
    'ChartScorer',
    
    # Enums
    'ChartType',
    'ChartCategory',
    'AnalysisIntent',
    'DataShape',
    
    # Convenience functions
    'recommend_charts',
    'get_best_chart',
]