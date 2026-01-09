"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DASHBOARD BUILDER MODULE                              ║
║              Professional Dashboard Generation Engine                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Creates interactive multi-chart dashboards with KPI cards, filters,         ║
║  and professional layouts using Macrocomm branding                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📊 Multi-Chart Layouts  - Grid-based dashboard with multiple visualizations
📈 KPI Cards            - Key metric displays with trends and deltas
🎛️ Filter System        - Interactive filters for data exploration
🎨 Professional Themes  - Macrocomm branded, dark mode, presentation
📱 Responsive Design    - Adapts to different screen sizes
💾 Export Options       - HTML, PNG, PDF dashboard exports
🏗️ Templates            - Pre-built dashboard templates (Sales, Financial, etc.)

USAGE:
------
    from data_analyst import DashboardBuilder, DashboardConfig
    
    # Create dashboard
    builder = DashboardBuilder()
    
    # Add components
    builder.add_kpi("Total Revenue", df['Revenue'].sum(), delta=12.5)
    builder.add_chart(chart_fig, row=1, col=0, width=2)
    builder.add_filter("Region", df['Region'].unique())
    
    # Build and export
    dashboard = builder.build("Sales Dashboard")
    dashboard.export("sales_dashboard.html")

ARCHITECTURE:
-------------
DashboardBuilder (main class)
    ├── LayoutEngine        - Grid-based positioning system
    ├── KPICardBuilder      - KPI metric cards with trends
    ├── FilterBuilder       - Interactive filter components
    ├── WidgetManager       - Manages all dashboard widgets
    ├── ThemeEngine         - Dashboard theming and branding
    └── ExportEngine        - Multi-format export system
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import numpy as np
import pandas as pd

# Plotly imports
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not installed. Install with: pip install plotly")

# Import from our modules
try:
    from .chart_generator import (
        ChartGenerator, GeneratedChart, ChartConfig, 
        MacrocommColors, ThemeStyle, ChartTheme
    )
    from .chart_recommender import ChartType, ChartRecommendation
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False
    logging.debug("chart_generator not available")

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class DashboardLayout(Enum):
    """Pre-defined dashboard layouts"""
    SINGLE = "single"                    # Single chart
    TWO_COLUMN = "two_column"            # 2 charts side by side
    THREE_COLUMN = "three_column"        # 3 charts in a row
    GRID_2X2 = "grid_2x2"               # 2x2 grid
    GRID_2X3 = "grid_2x3"               # 2x3 grid
    GRID_3X3 = "grid_3x3"               # 3x3 grid
    KPI_TOP = "kpi_top"                 # KPIs on top, charts below
    KPI_LEFT = "kpi_left"               # KPIs on left, charts right
    EXECUTIVE = "executive"              # Executive summary layout
    DETAILED = "detailed"                # Detailed analysis layout
    CUSTOM = "custom"                    # Custom grid


class WidgetType(Enum):
    """Types of dashboard widgets"""
    KPI_CARD = "kpi_card"
    CHART = "chart"
    TABLE = "table"
    TEXT = "text"
    FILTER = "filter"
    SPACER = "spacer"
    HEADER = "header"
    DIVIDER = "divider"


class KPITrend(Enum):
    """KPI trend directions"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class FilterType(Enum):
    """Types of filters"""
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select"
    DATE_RANGE = "date_range"
    SLIDER = "slider"
    CHECKBOX = "checkbox"


class DashboardTemplate(Enum):
    """Pre-built dashboard templates"""
    SALES = "sales"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    HR = "hr"
    OPERATIONS = "operations"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class KPICard:
    """
    Configuration for a KPI card widget.
    """
    id: str
    title: str
    value: Union[int, float, str]
    
    # Optional properties
    subtitle: Optional[str] = None
    prefix: str = ""                     # e.g., "$" for currency
    suffix: str = ""                     # e.g., "%" for percentage
    format_string: str = ",.0f"          # Number formatting
    
    # Trend/comparison
    delta: Optional[float] = None        # Change value
    delta_percent: Optional[float] = None # Change percentage
    trend: KPITrend = KPITrend.NEUTRAL
    reference_label: str = "vs last period"
    
    # Sparkline
    sparkline_data: Optional[List[float]] = None
    
    # Styling
    icon: Optional[str] = None           # Icon name/emoji
    color: Optional[str] = None          # Override color
    
    # Position
    row: int = 0
    col: int = 0
    width: int = 1
    height: int = 1


@dataclass
class ChartWidget:
    """
    Configuration for a chart widget in the dashboard.
    """
    id: str
    title: str
    figure: Any                          # Plotly figure
    
    # Optional properties
    description: Optional[str] = None
    insights: List[str] = field(default_factory=list)
    
    # Data binding
    source_data: Optional[pd.DataFrame] = None
    chart_type: Optional[ChartType] = None
    
    # Position
    row: int = 0
    col: int = 0
    width: int = 1
    height: int = 1
    
    # Interactivity
    filterable: bool = True
    drilldown_enabled: bool = False


@dataclass
class FilterWidget:
    """
    Configuration for a filter widget.
    """
    id: str
    label: str
    filter_type: FilterType
    column: str                          # Column to filter on
    
    # Options
    options: List[Any] = field(default_factory=list)
    default_value: Optional[Any] = None
    multi_select: bool = False
    
    # For range filters
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    # Position
    row: int = 0
    col: int = 0


@dataclass
class TextWidget:
    """
    Configuration for a text/header widget.
    """
    id: str
    content: str
    widget_type: WidgetType = WidgetType.TEXT
    
    # Styling
    font_size: int = 14
    font_weight: str = "normal"
    text_align: str = "left"
    color: Optional[str] = None
    
    # Position
    row: int = 0
    col: int = 0
    width: int = 1
    height: int = 1


@dataclass
class DashboardConfig:
    """
    Configuration for the entire dashboard.
    """
    title: str = "Dashboard"
    subtitle: Optional[str] = None
    
    # Layout
    layout: DashboardLayout = DashboardLayout.KPI_TOP
    columns: int = 12                    # Grid columns (12-column system)
    row_height: int = 400                # Default row height in pixels
    
    # Sizing
    width: Optional[int] = None          # Total width (None = responsive)
    height: Optional[int] = None         # Total height
    
    # Theme
    theme: ThemeStyle = ThemeStyle.MACROCOMM
    
    # Features
    show_filters: bool = True
    show_header: bool = True
    show_footer: bool = True
    show_timestamps: bool = True
    
    # Branding
    logo_url: Optional[str] = None
    company_name: str = "Macrocomm"
    
    # Export
    auto_refresh: bool = False
    refresh_interval_seconds: int = 300


@dataclass
class Dashboard:
    """
    Complete dashboard object ready for rendering/export.
    """
    id: str
    config: DashboardConfig
    
    # Widgets
    kpi_cards: List[KPICard] = field(default_factory=list)
    charts: List[ChartWidget] = field(default_factory=list)
    filters: List[FilterWidget] = field(default_factory=list)
    text_widgets: List[TextWidget] = field(default_factory=list)
    
    # Combined figure
    figure: Optional[Any] = None         # Combined Plotly figure
    html_content: Optional[str] = None   # Rendered HTML
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    data_sources: List[str] = field(default_factory=list)
    
    def export(self, filepath: Union[str, Path], format: str = "html") -> bool:
        """Export dashboard to file"""
        filepath = Path(filepath)
        
        try:
            if format == "html" and self.html_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.html_content)
                return True
            elif format == "html" and self.figure:
                self.figure.write_html(str(filepath))
                return True
            elif format == "json":
                # Export dashboard config
                with open(filepath, 'w') as f:
                    json.dump(self.to_dict(), f, indent=2, default=str)
                return True
            else:
                logger.warning(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary"""
        return {
            "id": self.id,
            "title": self.config.title,
            "subtitle": self.config.subtitle,
            "layout": self.config.layout.value,
            "theme": self.config.theme.value,
            "kpi_count": len(self.kpi_cards),
            "chart_count": len(self.charts),
            "filter_count": len(self.filters),
            "created_at": self.created_at.isoformat()
        }
    
    def show(self):
        """Display dashboard in browser/notebook"""
        if self.figure:
            self.figure.show()


# =============================================================================
# KPI CARD BUILDER
# =============================================================================

class KPICardBuilder:
    """
    Builds KPI card visualizations.
    """
    
    def __init__(self):
        self.colors = MacrocommColors()
    
    def create_kpi_indicator(self, kpi: KPICard) -> go.Figure:
        """Create a Plotly indicator for KPI"""
        
        # Determine color based on trend
        if kpi.trend == KPITrend.UP:
            delta_color = self.colors.GREEN
        elif kpi.trend == KPITrend.DOWN:
            delta_color = self.colors.RED
        else:
            delta_color = self.colors.MEDIUM_GRAY
        
        # Format value
        if isinstance(kpi.value, (int, float)):
            formatted_value = f"{kpi.prefix}{kpi.value:{kpi.format_string}}{kpi.suffix}"
        else:
            formatted_value = f"{kpi.prefix}{kpi.value}{kpi.suffix}"
        
        fig = go.Figure()
        
        # Create indicator
        indicator_config = {
            "mode": "number",
            "value": kpi.value if isinstance(kpi.value, (int, float)) else 0,
            "title": {"text": kpi.title, "font": {"size": 16, "color": self.colors.MEDIUM_GRAY}},
            "number": {
                "font": {"size": 40, "color": kpi.color or self.colors.SUNSET_ORANGE},
                "prefix": kpi.prefix,
                "suffix": kpi.suffix,
                "valueformat": kpi.format_string
            },
            "domain": {"x": [0, 1], "y": [0.3, 1]}
        }
        
        # Add delta if provided
        if kpi.delta is not None or kpi.delta_percent is not None:
            indicator_config["mode"] = "number+delta"
            indicator_config["delta"] = {
                "reference": kpi.value - (kpi.delta or 0) if isinstance(kpi.value, (int, float)) else 0,
                "relative": kpi.delta_percent is not None,
                "valueformat": ".1%" if kpi.delta_percent is not None else kpi.format_string,
                "increasing": {"color": self.colors.GREEN},
                "decreasing": {"color": self.colors.RED}
            }
        
        fig.add_trace(go.Indicator(**indicator_config))
        
        # Add sparkline if data provided
        if kpi.sparkline_data:
            fig.add_trace(go.Scatter(
                x=list(range(len(kpi.sparkline_data))),
                y=kpi.sparkline_data,
                mode='lines',
                line=dict(color=self.colors.SUNSET_ORANGE, width=2),
                fill='tozeroy',
                fillcolor=f'rgba(255, 110, 0, 0.1)',
                showlegend=False,
                xaxis='x2',
                yaxis='y2'
            ))
            
            fig.update_layout(
                xaxis2=dict(domain=[0.1, 0.9], anchor='y2', showticklabels=False, showgrid=False),
                yaxis2=dict(domain=[0, 0.25], anchor='x2', showticklabels=False, showgrid=False)
            )
        
        # Style
        fig.update_layout(
            paper_bgcolor='white',
            margin=dict(t=60, b=20, l=20, r=20),
            height=150
        )
        
        return fig
    
    def create_kpi_html(self, kpi: KPICard) -> str:
        """Create HTML for a KPI card"""
        
        # Determine trend icon and color
        if kpi.trend == KPITrend.UP:
            trend_icon = "▲"
            trend_color = "#00B894"
        elif kpi.trend == KPITrend.DOWN:
            trend_icon = "▼"
            trend_color = "#D63031"
        else:
            trend_icon = "●"
            trend_color = "#636E72"
        
        # Format value
        if isinstance(kpi.value, (int, float)):
            try:
                formatted_value = f"{kpi.prefix}{kpi.value:{kpi.format_string}}{kpi.suffix}"
            except:
                formatted_value = f"{kpi.prefix}{kpi.value}{kpi.suffix}"
        else:
            formatted_value = f"{kpi.prefix}{kpi.value}{kpi.suffix}"
        
        # Delta display
        delta_html = ""
        if kpi.delta is not None:
            delta_sign = "+" if kpi.delta >= 0 else ""
            delta_html = f'<span style="color: {trend_color};">{trend_icon} {delta_sign}{kpi.delta:.1f}</span>'
        elif kpi.delta_percent is not None:
            delta_sign = "+" if kpi.delta_percent >= 0 else ""
            delta_html = f'<span style="color: {trend_color};">{trend_icon} {delta_sign}{kpi.delta_percent:.1%}</span>'
        
        # Sparkline SVG
        sparkline_html = ""
        if kpi.sparkline_data and len(kpi.sparkline_data) > 1:
            # Create simple SVG sparkline
            data = kpi.sparkline_data
            min_val, max_val = min(data), max(data)
            range_val = max_val - min_val if max_val != min_val else 1
            
            width, height = 100, 30
            points = []
            for i, val in enumerate(data):
                x = i / (len(data) - 1) * width
                y = height - ((val - min_val) / range_val * height)
                points.append(f"{x:.1f},{y:.1f}")
            
            path = " L ".join(points)
            sparkline_html = f'''
                <svg width="{width}" height="{height}" style="margin-top: 8px;">
                    <path d="M {path}" fill="none" stroke="#FF6E00" stroke-width="2"/>
                </svg>
            '''
        
        return f'''
        <div class="kpi-card" style="
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 180px;
        ">
            <div style="color: #636E72; font-size: 14px; margin-bottom: 8px;">
                {kpi.icon or ''} {kpi.title}
            </div>
            <div style="color: {kpi.color or '#FF6E00'}; font-size: 36px; font-weight: bold;">
                {formatted_value}
            </div>
            <div style="font-size: 12px; margin-top: 4px;">
                {delta_html}
                <span style="color: #B2BEC3; margin-left: 4px;">{kpi.reference_label if delta_html else ''}</span>
            </div>
            {sparkline_html}
        </div>
        '''


# =============================================================================
# LAYOUT ENGINE
# =============================================================================

class LayoutEngine:
    """
    Manages grid-based dashboard layouts.
    """
    
    def __init__(self, columns: int = 12):
        self.columns = columns
        self.grid: Dict[Tuple[int, int], Any] = {}
    
    def calculate_subplot_grid(
        self,
        charts: List[ChartWidget],
        kpis: List[KPICard],
        layout: DashboardLayout
    ) -> Tuple[int, int, List[Dict]]:
        """
        Calculate subplot grid dimensions and specs.
        
        Returns:
            (rows, cols, specs)
        """
        total_widgets = len(charts) + (1 if kpis else 0)  # KPIs in one row
        
        if layout == DashboardLayout.SINGLE:
            return 1, 1, [[{"type": "xy"}]]
        
        elif layout == DashboardLayout.TWO_COLUMN:
            rows = (total_widgets + 1) // 2
            return rows, 2, [[{"type": "xy"}] * 2 for _ in range(rows)]
        
        elif layout == DashboardLayout.THREE_COLUMN:
            rows = (total_widgets + 2) // 3
            return rows, 3, [[{"type": "xy"}] * 3 for _ in range(rows)]
        
        elif layout == DashboardLayout.GRID_2X2:
            return 2, 2, [[{"type": "xy"}] * 2 for _ in range(2)]
        
        elif layout == DashboardLayout.GRID_2X3:
            return 2, 3, [[{"type": "xy"}] * 3 for _ in range(2)]
        
        elif layout == DashboardLayout.GRID_3X3:
            return 3, 3, [[{"type": "xy"}] * 3 for _ in range(3)]
        
        elif layout == DashboardLayout.KPI_TOP:
            # KPIs in top row, charts below
            chart_rows = (len(charts) + 2) // 3
            return 1 + chart_rows, 3, [[{"type": "indicator"}] * 3] + [[{"type": "xy"}] * 3 for _ in range(chart_rows)]
        
        elif layout == DashboardLayout.EXECUTIVE:
            # 4 KPIs on top, 2 large charts, 3 small charts
            return 3, 4, [
                [{"type": "indicator"}] * 4,
                [{"type": "xy", "colspan": 2}] * 2,
                [{"type": "xy"}] * 4
            ]
        
        else:
            # Custom/default: calculate based on widget count
            cols = min(3, total_widgets)
            rows = (total_widgets + cols - 1) // cols
            return rows, cols, [[{"type": "xy"}] * cols for _ in range(rows)]
    
    def position_to_subplot(self, row: int, col: int, total_rows: int, total_cols: int) -> Tuple[int, int]:
        """Convert grid position to subplot indices (1-indexed)"""
        return row + 1, col + 1


# =============================================================================
# MAIN DASHBOARD BUILDER CLASS
# =============================================================================

class DashboardBuilder:
    """
    Main class for building professional dashboards.
    
    Usage:
        builder = DashboardBuilder()
        
        # Configure
        builder.set_title("Sales Dashboard")
        builder.set_layout(DashboardLayout.KPI_TOP)
        
        # Add KPIs
        builder.add_kpi("Revenue", 1250000, prefix="$", delta_percent=0.12)
        builder.add_kpi("Orders", 847, delta=89)
        
        # Add charts
        builder.add_chart(line_fig, title="Revenue Trend")
        builder.add_chart(bar_fig, title="Sales by Region")
        
        # Build
        dashboard = builder.build()
        dashboard.export("dashboard.html")
    """
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        """
        Initialize the dashboard builder.
        
        Args:
            config: Optional dashboard configuration
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly is required. Install with: pip install plotly")
        
        self.config = config or DashboardConfig()
        self.colors = MacrocommColors()
        self.layout_engine = LayoutEngine(self.config.columns)
        self.kpi_builder = KPICardBuilder()
        
        # Widgets
        self._kpis: List[KPICard] = []
        self._charts: List[ChartWidget] = []
        self._filters: List[FilterWidget] = []
        self._text_widgets: List[TextWidget] = []
        
        # Data
        self._dataframes: Dict[str, pd.DataFrame] = {}
        
        # State
        self._widget_counter = 0
        
        logger.info("DashboardBuilder initialized")
    
    # =========================================================================
    # CONFIGURATION METHODS
    # =========================================================================
    
    def set_title(self, title: str, subtitle: Optional[str] = None) -> 'DashboardBuilder':
        """Set dashboard title and subtitle"""
        self.config.title = title
        self.config.subtitle = subtitle
        return self
    
    def set_layout(self, layout: DashboardLayout) -> 'DashboardBuilder':
        """Set dashboard layout"""
        self.config.layout = layout
        return self
    
    def set_theme(self, theme: ThemeStyle) -> 'DashboardBuilder':
        """Set dashboard theme"""
        self.config.theme = theme
        return self
    
    def set_size(self, width: Optional[int] = None, height: Optional[int] = None) -> 'DashboardBuilder':
        """Set dashboard dimensions"""
        self.config.width = width
        self.config.height = height
        return self
    
    # =========================================================================
    # KPI METHODS
    # =========================================================================
    
    def add_kpi(
        self,
        title: str,
        value: Union[int, float, str],
        prefix: str = "",
        suffix: str = "",
        delta: Optional[float] = None,
        delta_percent: Optional[float] = None,
        trend: Optional[KPITrend] = None,
        sparkline: Optional[List[float]] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        row: int = 0,
        col: Optional[int] = None
    ) -> 'DashboardBuilder':
        """
        Add a KPI card to the dashboard.
        
        Args:
            title: KPI title
            value: KPI value
            prefix: Value prefix (e.g., "$")
            suffix: Value suffix (e.g., "%")
            delta: Absolute change value
            delta_percent: Percentage change (0.12 = 12%)
            trend: Trend direction (auto-detected if delta provided)
            sparkline: List of values for sparkline chart
            icon: Icon/emoji for the KPI
            color: Override primary color
            row: Grid row position
            col: Grid column position (auto if None)
            
        Returns:
            Self for chaining
        """
        self._widget_counter += 1
        
        # Auto-detect trend if delta provided
        if trend is None:
            if delta is not None:
                trend = KPITrend.UP if delta > 0 else (KPITrend.DOWN if delta < 0 else KPITrend.NEUTRAL)
            elif delta_percent is not None:
                trend = KPITrend.UP if delta_percent > 0 else (KPITrend.DOWN if delta_percent < 0 else KPITrend.NEUTRAL)
            else:
                trend = KPITrend.NEUTRAL
        
        # Auto column position
        if col is None:
            col = len(self._kpis) % 4
        
        kpi = KPICard(
            id=f"kpi_{self._widget_counter}",
            title=title,
            value=value,
            prefix=prefix,
            suffix=suffix,
            delta=delta,
            delta_percent=delta_percent,
            trend=trend,
            sparkline_data=sparkline,
            icon=icon,
            color=color,
            row=row,
            col=col
        )
        
        self._kpis.append(kpi)
        logger.debug(f"Added KPI: {title}")
        return self
    
    def add_kpi_from_column(
        self,
        df: pd.DataFrame,
        column: str,
        title: Optional[str] = None,
        aggregation: str = "sum",
        compare_column: Optional[str] = None,
        **kwargs
    ) -> 'DashboardBuilder':
        """
        Add KPI calculated from DataFrame column.
        
        Args:
            df: Source DataFrame
            column: Column to aggregate
            title: KPI title (defaults to column name)
            aggregation: sum, mean, count, min, max
            compare_column: Column for comparison (delta calculation)
            **kwargs: Additional KPI arguments
        """
        agg_funcs = {
            "sum": df[column].sum,
            "mean": df[column].mean,
            "count": df[column].count,
            "min": df[column].min,
            "max": df[column].max
        }
        
        value = agg_funcs.get(aggregation, df[column].sum)()
        
        # Calculate delta if comparison provided
        delta = None
        if compare_column and compare_column in df.columns:
            compare_value = agg_funcs.get(aggregation, df[compare_column].sum)()
            delta = value - compare_value
        
        return self.add_kpi(
            title=title or column,
            value=value,
            delta=delta,
            **kwargs
        )
    
    # =========================================================================
    # CHART METHODS
    # =========================================================================
    
    def add_chart(
        self,
        figure: Union[go.Figure, GeneratedChart],
        title: Optional[str] = None,
        description: Optional[str] = None,
        insights: Optional[List[str]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        width: int = 1,
        height: int = 1,
        source_data: Optional[pd.DataFrame] = None
    ) -> 'DashboardBuilder':
        """
        Add a chart to the dashboard.
        
        Args:
            figure: Plotly figure or GeneratedChart
            title: Chart title
            description: Chart description
            insights: AI-generated insights
            row: Grid row position
            col: Grid column position
            width: Number of columns to span
            height: Number of rows to span
            source_data: Source DataFrame for filtering
            
        Returns:
            Self for chaining
        """
        self._widget_counter += 1
        
        # Extract figure if GeneratedChart
        if isinstance(figure, GeneratedChart):
            fig = figure.figure
            title = title or figure.title
            description = description or figure.description
        else:
            fig = figure
        
        # Auto position
        if row is None:
            row = (len(self._charts) // 3) + 1  # Start after KPI row
        if col is None:
            col = len(self._charts) % 3
        
        chart = ChartWidget(
            id=f"chart_{self._widget_counter}",
            title=title or f"Chart {self._widget_counter}",
            figure=fig,
            description=description,
            insights=insights or [],
            row=row,
            col=col,
            width=width,
            height=height,
            source_data=source_data
        )
        
        self._charts.append(chart)
        logger.debug(f"Added chart: {chart.title}")
        return self
    
    def add_chart_from_data(
        self,
        df: pd.DataFrame,
        chart_type: Union[str, ChartType],
        x: str,
        y: str,
        title: Optional[str] = None,
        **kwargs
    ) -> 'DashboardBuilder':
        """
        Create and add a chart from data.
        
        Args:
            df: Source DataFrame
            chart_type: Type of chart
            x: X-axis column
            y: Y-axis column
            title: Chart title
            **kwargs: Additional chart configuration
        """
        if GENERATOR_AVAILABLE:
            generator = ChartGenerator()
            config = ChartConfig(x=x, y=y, title=title, theme=self.config.theme)
            result = generator.generate_from_type(df, chart_type, config)
            return self.add_chart(result, source_data=df, **kwargs)
        else:
            # Fallback to basic Plotly
            import plotly.express as px
            fig = px.bar(df, x=x, y=y, title=title)
            return self.add_chart(fig, title=title, source_data=df, **kwargs)
    
    # =========================================================================
    # FILTER METHODS
    # =========================================================================
    
    def add_filter(
        self,
        label: str,
        column: str,
        options: Optional[List[Any]] = None,
        filter_type: FilterType = FilterType.DROPDOWN,
        default_value: Optional[Any] = None,
        multi_select: bool = False
    ) -> 'DashboardBuilder':
        """
        Add a filter to the dashboard.
        
        Args:
            label: Filter label
            column: Column to filter on
            options: Filter options (auto-detected if None)
            filter_type: Type of filter control
            default_value: Default selected value
            multi_select: Allow multiple selections
            
        Returns:
            Self for chaining
        """
        self._widget_counter += 1
        
        filter_widget = FilterWidget(
            id=f"filter_{self._widget_counter}",
            label=label,
            filter_type=filter_type,
            column=column,
            options=options or [],
            default_value=default_value,
            multi_select=multi_select
        )
        
        self._filters.append(filter_widget)
        logger.debug(f"Added filter: {label}")
        return self
    
    def add_filters_from_data(
        self,
        df: pd.DataFrame,
        columns: List[str],
        filter_type: FilterType = FilterType.DROPDOWN
    ) -> 'DashboardBuilder':
        """
        Add filters for multiple columns from DataFrame.
        
        Args:
            df: Source DataFrame
            columns: Columns to create filters for
            filter_type: Type of filter control
        """
        for col in columns:
            if col in df.columns:
                options = df[col].unique().tolist()
                self.add_filter(
                    label=col,
                    column=col,
                    options=options,
                    filter_type=filter_type
                )
        return self
    
    # =========================================================================
    # TEXT/HEADER METHODS
    # =========================================================================
    
    def add_header(
        self,
        text: str,
        level: int = 1,
        row: int = 0,
        col: int = 0
    ) -> 'DashboardBuilder':
        """Add a header text widget"""
        self._widget_counter += 1
        
        font_sizes = {1: 28, 2: 24, 3: 20, 4: 16}
        
        widget = TextWidget(
            id=f"header_{self._widget_counter}",
            content=text,
            widget_type=WidgetType.HEADER,
            font_size=font_sizes.get(level, 16),
            font_weight="bold",
            row=row,
            col=col
        )
        
        self._text_widgets.append(widget)
        return self
    
    def add_text(
        self,
        text: str,
        row: int = 0,
        col: int = 0,
        **kwargs
    ) -> 'DashboardBuilder':
        """Add a text widget"""
        self._widget_counter += 1
        
        widget = TextWidget(
            id=f"text_{self._widget_counter}",
            content=text,
            widget_type=WidgetType.TEXT,
            row=row,
            col=col,
            **kwargs
        )
        
        self._text_widgets.append(widget)
        return self
    
    # =========================================================================
    # BUILD METHODS
    # =========================================================================
    
    def build(self, title: Optional[str] = None) -> Dashboard:
        """
        Build the complete dashboard.
        
        Args:
            title: Override dashboard title
            
        Returns:
            Dashboard object ready for export
        """
        if title:
            self.config.title = title
        
        dashboard_id = str(uuid.uuid4())[:8]
        
        # Build combined figure
        figure = self._build_plotly_figure()
        
        # Build HTML content
        html_content = self._build_html()
        
        dashboard = Dashboard(
            id=dashboard_id,
            config=self.config,
            kpi_cards=self._kpis.copy(),
            charts=self._charts.copy(),
            filters=self._filters.copy(),
            text_widgets=self._text_widgets.copy(),
            figure=figure,
            html_content=html_content
        )
        
        logger.info(f"Dashboard built: {self.config.title} (ID: {dashboard_id})")
        return dashboard
    
    def _build_plotly_figure(self) -> go.Figure:
        """Build combined Plotly figure - HTML-based approach for mixed chart types"""
        
        if not self._charts:
            # No charts - create empty figure
            fig = go.Figure()
            fig.update_layout(
                title=dict(text=f"<b>{self.config.title}</b>", x=0.5),
                height=400
            )
            return fig
        
        # For mixed chart types, we create individual figures
        # The HTML export handles layout, this is for .show() fallback
        
        # If only one chart, return it directly
        if len(self._charts) == 1:
            fig = go.Figure(self._charts[0].figure)
            fig.update_layout(
                title=dict(
                    text=f"<b>{self.config.title}</b>",
                    x=0.5, y=0.98,
                    font=dict(size=24, color=self.colors.DARK_GRAY)
                )
            )
            self._apply_theme(fig)
            return fig
        
        # For multiple charts, create a simple combined view
        # Note: HTML export is the preferred method for dashboards
        fig = go.Figure()
        
        # Add traces from first chart as primary view
        for trace in self._charts[0].figure.data:
            fig.add_trace(trace)
        
        fig.update_layout(
            title=dict(
                text=f"<b>{self.config.title}</b><br><span style='font-size:12px;color:gray;'>View full dashboard in exported HTML</span>",
                x=0.5, y=0.95,
                font=dict(size=20, color=self.colors.DARK_GRAY)
            ),
            height=self.config.height or 500,
            width=self.config.width,
            margin=dict(t=80, b=60, l=60, r=60)
        )
        
        self._apply_theme(fig)
        return fig

    def _build_html(self) -> str:
        """Build complete HTML dashboard"""
        
        # Theme colors
        if self.config.theme == ThemeStyle.MACROCOMM_DARK:
            bg_color = "#1E1E1E"
            text_color = "#E0E0E0"
            card_bg = "#252525"
        else:
            bg_color = "#F5F6FA"
            text_color = "#2D3436"
            card_bg = "#FFFFFF"
        
        # KPI HTML
        kpi_html = ""
        if self._kpis:
            kpi_cards = "".join([self.kpi_builder.create_kpi_html(kpi) for kpi in self._kpis])
            kpi_html = f'''
            <div class="kpi-container" style="
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 30px;
                justify-content: center;
            ">
                {kpi_cards}
            </div>
            '''
        
        # Filter HTML
        filter_html = ""
        if self._filters and self.config.show_filters:
            filter_items = ""
            for f in self._filters:
                options_html = "".join([f'<option value="{opt}">{opt}</option>' for opt in f.options])
                filter_items += f'''
                <div class="filter-item" style="margin-right: 20px;">
                    <label style="display: block; font-size: 12px; color: {self.colors.MEDIUM_GRAY}; margin-bottom: 4px;">
                        {f.label}
                    </label>
                    <select style="
                        padding: 8px 12px;
                        border: 1px solid {self.colors.LIGHT_GRAY};
                        border-radius: 6px;
                        font-size: 14px;
                        min-width: 150px;
                    ">
                        <option value="">All</option>
                        {options_html}
                    </select>
                </div>
                '''
            
            filter_html = f'''
            <div class="filter-container" style="
                display: flex;
                flex-wrap: wrap;
                padding: 15px 20px;
                background: {card_bg};
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ">
                {filter_items}
            </div>
            '''
        
        # Charts HTML
        charts_html = ""
        if self._charts:
            chart_divs = ""
            for i, chart in enumerate(self._charts):
                chart_html = chart.figure.to_html(full_html=False, include_plotlyjs=False)
                
                insights_html = ""
                if chart.insights:
                    insights_list = "".join([f"<li>{insight}</li>" for insight in chart.insights])
                    insights_html = f'''
                    <div class="chart-insights" style="
                        margin-top: 10px;
                        padding: 10px;
                        background: {self.colors.PALE_ORANGE}20;
                        border-left: 3px solid {self.colors.SUNSET_ORANGE};
                        border-radius: 4px;
                        font-size: 13px;
                    ">
                        <strong>💡 Insights:</strong>
                        <ul style="margin: 5px 0 0 0; padding-left: 20px;">{insights_list}</ul>
                    </div>
                    '''
                
                chart_divs += f'''
                <div class="chart-card" style="
                    background: {card_bg};
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    flex: 1 1 calc(33.333% - 20px);
                    min-width: 350px;
                    max-width: 100%;
                ">
                    <h3 style="margin: 0 0 15px 0; color: {text_color}; font-size: 16px;">
                        {chart.title}
                    </h3>
                    {chart_html}
                    {insights_html}
                </div>
                '''
            
            charts_html = f'''
            <div class="charts-container" style="
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
            ">
                {chart_divs}
            </div>
            '''
        
        # Footer
        footer_html = ""
        if self.config.show_footer:
            footer_html = f'''
            <footer style="
                margin-top: 40px;
                padding: 20px;
                text-align: center;
                color: {self.colors.MEDIUM_GRAY};
                font-size: 12px;
                border-top: 1px solid {self.colors.PALE_GRAY};
            ">
                <p>
                    Generated by <strong style="color: {self.colors.SUNSET_ORANGE};">{self.config.company_name}</strong> 
                    Conversational BI Platform
                </p>
                {f'<p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>' if self.config.show_timestamps else ''}
            </footer>
            '''
        
        # Complete HTML
        html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title} - {self.config.company_name}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Open Sans', Arial, sans-serif;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
        }}
        .dashboard-container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 30px;
        }}
        .dashboard-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid {self.colors.SUNSET_ORANGE};
        }}
        .dashboard-header h1 {{
            font-size: 32px;
            font-weight: 700;
            color: {text_color};
            margin-bottom: 8px;
        }}
        .dashboard-header p {{
            font-size: 16px;
            color: {self.colors.MEDIUM_GRAY};
        }}
        .logo {{
            color: {self.colors.SUNSET_ORANGE};
            font-weight: bold;
        }}
        @media (max-width: 768px) {{
            .dashboard-container {{
                padding: 15px;
            }}
            .kpi-container, .charts-container {{
                flex-direction: column;
            }}
            .chart-card {{
                min-width: 100% !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        {'<header class="dashboard-header"><h1>' + self.config.title + '</h1>' + 
         (f'<p>{self.config.subtitle}</p>' if self.config.subtitle else '') + 
         '</header>' if self.config.show_header else ''}
        
        {filter_html}
        {kpi_html}
        {charts_html}
        {footer_html}
    </div>
</body>
</html>
'''
        return html
    
    def _apply_theme(self, fig: go.Figure):
        """Apply theme to figure"""
        
        if self.config.theme == ThemeStyle.MACROCOMM:
            fig.update_layout(
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(family="Open Sans, Arial, sans-serif", color=self.colors.DARK_GRAY)
            )
        elif self.config.theme == ThemeStyle.MACROCOMM_DARK:
            fig.update_layout(
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#252525',
                font=dict(family="Open Sans, Arial, sans-serif", color="#E0E0E0")
            )
            fig.update_xaxes(gridcolor='#404040')
            fig.update_yaxes(gridcolor='#404040')
    
    # =========================================================================
    # TEMPLATE METHODS
    # =========================================================================
    
    @classmethod
    def from_template(
        cls,
        template: DashboardTemplate,
        df: pd.DataFrame,
        **kwargs
    ) -> 'DashboardBuilder':
        """
        Create a dashboard from a pre-built template.
        
        Args:
            template: Template type
            df: Source DataFrame
            **kwargs: Additional configuration
            
        Returns:
            Configured DashboardBuilder
        """
        builder = cls()
        
        if template == DashboardTemplate.SALES:
            builder._apply_sales_template(df, **kwargs)
        elif template == DashboardTemplate.FINANCIAL:
            builder._apply_financial_template(df, **kwargs)
        elif template == DashboardTemplate.MARKETING:
            builder._apply_marketing_template(df, **kwargs)
        elif template == DashboardTemplate.EXECUTIVE:
            builder._apply_executive_template(df, **kwargs)
        else:
            builder._apply_generic_template(df, **kwargs)
        
        return builder
    
    def _apply_sales_template(self, df: pd.DataFrame, **kwargs):
        """Apply sales dashboard template"""
        self.set_title("Sales Performance Dashboard", "Real-time sales metrics and trends")
        self.set_layout(DashboardLayout.KPI_TOP)
        
        # Auto-detect columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Add KPIs
        if numeric_cols:
            self.add_kpi("Total Revenue", df[numeric_cols[0]].sum(), prefix="$", icon="💰")
            if len(numeric_cols) > 1:
                self.add_kpi("Total Units", df[numeric_cols[1]].sum(), icon="📦")
            self.add_kpi("Avg Transaction", df[numeric_cols[0]].mean(), prefix="$", icon="📊")
            self.add_kpi("Record Count", len(df), icon="📋")
        
        # Add charts using ChartGenerator if available
        if GENERATOR_AVAILABLE:
            generator = ChartGenerator()
            
            # Time series if date column exists
            if date_cols and numeric_cols:
                config = ChartConfig(x=date_cols[0], y=numeric_cols[0], title="Revenue Over Time")
                result = generator.generate_from_type(df, ChartType.LINE, config)
                self.add_chart(result.figure, title="Revenue Trend")
            
            # Category breakdown
            if cat_cols and numeric_cols:
                agg_df = df.groupby(cat_cols[0])[numeric_cols[0]].sum().reset_index()
                config = ChartConfig(x=cat_cols[0], y=numeric_cols[0], title=f"Revenue by {cat_cols[0]}")
                result = generator.generate_from_type(agg_df, ChartType.BAR_HORIZONTAL, config)
                self.add_chart(result.figure, title=f"By {cat_cols[0]}")
        
        # Add filters
        for col in cat_cols[:3]:
            self.add_filter(col, col, df[col].unique().tolist())
    
    def _apply_financial_template(self, df: pd.DataFrame, **kwargs):
        """Apply financial dashboard template"""
        self.set_title("Financial Overview", "Key financial metrics and analysis")
        self.set_layout(DashboardLayout.EXECUTIVE)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if numeric_cols:
            self.add_kpi("Total", df[numeric_cols[0]].sum(), prefix="$", icon="💵")
            self.add_kpi("Average", df[numeric_cols[0]].mean(), prefix="$", icon="📈")
            self.add_kpi("Maximum", df[numeric_cols[0]].max(), prefix="$", icon="⬆️")
            self.add_kpi("Minimum", df[numeric_cols[0]].min(), prefix="$", icon="⬇️")
    
    def _apply_marketing_template(self, df: pd.DataFrame, **kwargs):
        """Apply marketing dashboard template"""
        self.set_title("Marketing Analytics", "Campaign performance and metrics")
        self.set_layout(DashboardLayout.KPI_TOP)
    
    def _apply_executive_template(self, df: pd.DataFrame, **kwargs):
        """Apply executive summary template"""
        self.set_title("Executive Summary", "High-level business overview")
        self.set_layout(DashboardLayout.EXECUTIVE)
    
    def _apply_generic_template(self, df: pd.DataFrame, **kwargs):
        """Apply generic dashboard template"""
        self.set_title("Data Dashboard", "Automated data analysis")
        self.set_layout(DashboardLayout.KPI_TOP)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Add basic KPIs
        self.add_kpi("Records", len(df), icon="📋")
        self.add_kpi("Columns", len(df.columns), icon="📊")
        
        if numeric_cols:
            self.add_kpi(f"Sum ({numeric_cols[0]})", df[numeric_cols[0]].sum(), icon="➕")
            self.add_kpi(f"Avg ({numeric_cols[0]})", df[numeric_cols[0]].mean(), icon="📈")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def clear(self) -> 'DashboardBuilder':
        """Clear all widgets"""
        self._kpis.clear()
        self._charts.clear()
        self._filters.clear()
        self._text_widgets.clear()
        self._widget_counter = 0
        return self
    
    def get_summary(self) -> Dict[str, Any]:
        """Get dashboard summary"""
        return {
            "title": self.config.title,
            "layout": self.config.layout.value,
            "theme": self.config.theme.value,
            "kpi_count": len(self._kpis),
            "chart_count": len(self._charts),
            "filter_count": len(self._filters),
            "text_count": len(self._text_widgets)
        }


# =============================================================================
# QUICK DASHBOARD FUNCTIONS
# =============================================================================

def quick_dashboard(
    df: pd.DataFrame,
    title: str = "Data Dashboard",
    template: Optional[DashboardTemplate] = None
) -> Dashboard:
    """
    Quickly create a dashboard from a DataFrame.
    
    Args:
        df: Source DataFrame
        title: Dashboard title
        template: Optional template to use
        
    Returns:
        Dashboard object
    """
    if template:
        builder = DashboardBuilder.from_template(template, df)
    else:
        builder = DashboardBuilder()
        builder._apply_generic_template(df)
    
    builder.set_title(title)
    return builder.build()


def create_kpi_dashboard(
    kpis: List[Dict[str, Any]],
    title: str = "KPI Dashboard"
) -> Dashboard:
    """
    Create a simple KPI-only dashboard.
    
    Args:
        kpis: List of KPI dictionaries with keys: title, value, delta, prefix, suffix
        title: Dashboard title
        
    Returns:
        Dashboard object
    """
    builder = DashboardBuilder()
    builder.set_title(title)
    builder.set_layout(DashboardLayout.KPI_TOP)
    
    for kpi in kpis:
        builder.add_kpi(**kpi)
    
    return builder.build()


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'DashboardBuilder',
    
    # Result classes
    'Dashboard',
    'DashboardConfig',
    'KPICard',
    'ChartWidget',
    'FilterWidget',
    'TextWidget',
    
    # Support classes
    'KPICardBuilder',
    'LayoutEngine',
    
    # Enums
    'DashboardLayout',
    'DashboardTemplate',
    'WidgetType',
    'KPITrend',
    'FilterType',
    
    # Convenience functions
    'quick_dashboard',
    'create_kpi_dashboard',
]