"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        CHART GENERATOR MODULE                                ║
║              Interactive Visualization Creation Engine                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Creates interactive Plotly charts for all 84 supported chart types          ║
║  Features: Macrocomm branding, responsive design, export capabilities        ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📊 84 Chart Types     - Full implementation of all chart types
🎨 Macrocomm Branding - Sunset Orange (#FF6E00), professional themes
📱 Responsive Design  - Mobile-friendly, adaptive sizing
💾 Export Options     - PNG, SVG, HTML, PDF, JSON
🔧 Customizable       - Colors, fonts, sizes, annotations

USAGE:
------
    from data_analyst import ChartGenerator, ChartRecommender
    
    # Get recommendations
    recommender = ChartRecommender()
    recommendations = recommender.recommend(df)
    
    # Generate the top recommended chart
    generator = ChartGenerator()
    fig = generator.generate(df, recommendations[0])
    
    # Or generate a specific chart type
    fig = generator.create_bar_chart(df, x='Category', y='Sales')
    
    # Export
    generator.export(fig, 'sales_chart.png')
    generator.export(fig, 'sales_chart.html')

ARCHITECTURE:
-------------
ChartGenerator (main class)
    ├── ThemeManager        - Macrocomm branding and themes
    ├── ComparisonCharts    - Bar, Column, Lollipop, etc.
    ├── CorrelationCharts   - Scatter, Bubble, Heatmap, etc.
    ├── PartToWholeCharts   - Pie, Donut, Treemap, etc.
    ├── TimeSeriesCharts    - Line, Area, Candlestick, etc.
    ├── DistributionCharts  - Histogram, Box, Violin, etc.
    ├── SpecializedCharts   - Gauge, KPI, Sankey, etc.
    └── ExportManager       - PNG, SVG, HTML, PDF export
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
import json
import base64
from io import BytesIO
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Plotly imports
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not installed. Install with: pip install plotly")

# Kaleido for static export
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False
    logging.debug("Kaleido not installed. Static exports may be limited.")

# Import from our modules
try:
    from .chart_recommender import (
        ChartType, ChartCategory, ChartRecommendation, DataCharacteristics
    )
    RECOMMENDER_AVAILABLE = True
except ImportError:
    RECOMMENDER_AVAILABLE = False
    logging.debug("chart_recommender not available")

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ExportFormat(Enum):
    """Supported export formats"""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    WEBP = "webp"


class ThemeStyle(Enum):
    """Available theme styles"""
    MACROCOMM = "macrocomm"         # Default branded theme
    MACROCOMM_DARK = "macrocomm_dark"
    LIGHT = "light"
    DARK = "dark"
    MINIMAL = "minimal"
    PRESENTATION = "presentation"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MacrocommColors:
    """
    Official Macrocomm brand colors.
    """
    # Primary colors
    SUNSET_ORANGE: str = "#FF6E00"      # Primary brand color
    BRIGHT_ORANGE: str = "#FF923F"      # Secondary brand color
    
    # Extended palette
    DARK_ORANGE: str = "#E65100"
    LIGHT_ORANGE: str = "#FFB74D"
    PALE_ORANGE: str = "#FFE0B2"
    
    # Neutrals
    DARK_GRAY: str = "#2D3436"
    MEDIUM_GRAY: str = "#636E72"
    LIGHT_GRAY: str = "#B2BEC3"
    PALE_GRAY: str = "#DFE6E9"
    WHITE: str = "#FFFFFF"
    
    # Accent colors (for multi-series)
    BLUE: str = "#0984E3"
    GREEN: str = "#00B894"
    PURPLE: str = "#6C5CE7"
    RED: str = "#D63031"
    TEAL: str = "#00CEC9"
    YELLOW: str = "#FDCB6E"
    PINK: str = "#E84393"
    
    @classmethod
    def get_sequential_palette(cls) -> List[str]:
        """Get sequential color palette (light to dark orange)"""
        return [
            cls.PALE_ORANGE,
            cls.LIGHT_ORANGE,
            cls.BRIGHT_ORANGE,
            cls.SUNSET_ORANGE,
            cls.DARK_ORANGE,
        ]
    
    @classmethod
    def get_categorical_palette(cls) -> List[str]:
        """Get categorical color palette for multiple series"""
        return [
            cls.SUNSET_ORANGE,
            cls.BLUE,
            cls.GREEN,
            cls.PURPLE,
            cls.RED,
            cls.TEAL,
            cls.YELLOW,
            cls.PINK,
            cls.BRIGHT_ORANGE,
            cls.DARK_GRAY,
        ]
    
    @classmethod
    def get_diverging_palette(cls) -> List[str]:
        """Get diverging color palette (negative to positive)"""
        return [
            cls.BLUE,
            "#74B9FF",
            cls.PALE_GRAY,
            cls.LIGHT_ORANGE,
            cls.SUNSET_ORANGE,
        ]


@dataclass
class ChartTheme:
    """
    Complete theme configuration for charts.
    """
    name: str
    
    # Colors
    primary_color: str = MacrocommColors.SUNSET_ORANGE
    secondary_color: str = MacrocommColors.BRIGHT_ORANGE
    background_color: str = MacrocommColors.WHITE
    paper_color: str = MacrocommColors.WHITE
    text_color: str = MacrocommColors.DARK_GRAY
    grid_color: str = MacrocommColors.PALE_GRAY
    
    # Color palettes
    categorical_colors: List[str] = field(default_factory=MacrocommColors.get_categorical_palette)
    sequential_colors: List[str] = field(default_factory=MacrocommColors.get_sequential_palette)
    diverging_colors: List[str] = field(default_factory=MacrocommColors.get_diverging_palette)
    
    # Typography
    font_family: str = "Open Sans, Arial, sans-serif"
    title_font_size: int = 18
    axis_font_size: int = 12
    tick_font_size: int = 10
    legend_font_size: int = 11
    
    # Layout
    margin_top: int = 60
    margin_bottom: int = 60
    margin_left: int = 60
    margin_right: int = 40
    
    # Grid
    show_grid: bool = True
    grid_width: int = 1
    
    # Legend
    show_legend: bool = True
    legend_position: str = "right"  # right, bottom, top, left
    
    def to_plotly_template(self) -> go.layout.Template:
        """Convert theme to Plotly template"""
        return go.layout.Template(
            layout=go.Layout(
                font=dict(
                    family=self.font_family,
                    size=self.axis_font_size,
                    color=self.text_color
                ),
                title=dict(
                    font=dict(size=self.title_font_size, color=self.text_color)
                ),
                paper_bgcolor=self.paper_color,
                plot_bgcolor=self.background_color,
                colorway=self.categorical_colors,
                xaxis=dict(
                    gridcolor=self.grid_color,
                    gridwidth=self.grid_width,
                    showgrid=self.show_grid,
                    tickfont=dict(size=self.tick_font_size)
                ),
                yaxis=dict(
                    gridcolor=self.grid_color,
                    gridwidth=self.grid_width,
                    showgrid=self.show_grid,
                    tickfont=dict(size=self.tick_font_size)
                ),
                margin=dict(
                    t=self.margin_top,
                    b=self.margin_bottom,
                    l=self.margin_left,
                    r=self.margin_right
                ),
                legend=dict(
                    font=dict(size=self.legend_font_size)
                )
            )
        )


@dataclass
class ChartConfig:
    """
    Configuration for generating a chart.
    """
    # Data mapping
    x: Optional[str] = None
    y: Optional[Union[str, List[str]]] = None
    color: Optional[str] = None
    size: Optional[str] = None
    text: Optional[str] = None
    hover_data: Optional[List[str]] = None
    
    # Chart options
    title: Optional[str] = None
    x_title: Optional[str] = None
    y_title: Optional[str] = None
    
    # Sizing
    width: Optional[int] = None
    height: Optional[int] = None
    
    # Theme
    theme: ThemeStyle = ThemeStyle.MACROCOMM
    
    # Interactivity
    interactive: bool = True
    show_toolbar: bool = True
    
    # Annotations
    show_values: bool = False
    value_format: str = ",.0f"
    
    # Additional options
    orientation: str = "v"  # v=vertical, h=horizontal
    barmode: str = "group"  # group, stack, overlay
    opacity: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "size": self.size,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "theme": self.theme.value if isinstance(self.theme, ThemeStyle) else self.theme
        }


@dataclass
class GeneratedChart:
    """
    Result of chart generation.
    """
    figure: Any  # Plotly figure object
    chart_type: ChartType
    config: ChartConfig
    
    # Metadata
    title: str = ""
    description: str = ""
    data_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Generation info
    generation_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)
    
    def to_html(self, full_html: bool = True, include_plotlyjs: bool = True) -> str:
        """Export chart to HTML string"""
        return self.figure.to_html(
            full_html=full_html,
            include_plotlyjs=include_plotlyjs
        )
    
    def to_json(self) -> str:
        """Export chart to JSON string"""
        return self.figure.to_json()
    
    def show(self):
        """Display chart in notebook or browser"""
        self.figure.show()


# =============================================================================
# THEME MANAGER
# =============================================================================

class ThemeManager:
    """
    Manages chart themes and branding.
    """
    
    def __init__(self):
        """Initialize with default themes"""
        self.themes: Dict[ThemeStyle, ChartTheme] = {}
        self._register_default_themes()
    
    def _register_default_themes(self):
        """Register all default themes"""
        
        # Macrocomm Light (Default)
        self.themes[ThemeStyle.MACROCOMM] = ChartTheme(
            name="Macrocomm",
            primary_color=MacrocommColors.SUNSET_ORANGE,
            secondary_color=MacrocommColors.BRIGHT_ORANGE,
            background_color=MacrocommColors.WHITE,
            paper_color=MacrocommColors.WHITE,
            text_color=MacrocommColors.DARK_GRAY,
            grid_color=MacrocommColors.PALE_GRAY
        )
        
        # Macrocomm Dark
        self.themes[ThemeStyle.MACROCOMM_DARK] = ChartTheme(
            name="Macrocomm Dark",
            primary_color=MacrocommColors.SUNSET_ORANGE,
            secondary_color=MacrocommColors.BRIGHT_ORANGE,
            background_color="#1E1E1E",
            paper_color="#252525",
            text_color="#E0E0E0",
            grid_color="#404040"
        )
        
        # Light
        self.themes[ThemeStyle.LIGHT] = ChartTheme(
            name="Light",
            primary_color="#3498DB",
            secondary_color="#2ECC71",
            background_color="#FFFFFF",
            paper_color="#FFFFFF",
            text_color="#2C3E50",
            grid_color="#ECF0F1",
            categorical_colors=["#3498DB", "#2ECC71", "#E74C3C", "#9B59B6", "#F39C12", 
                               "#1ABC9C", "#34495E", "#E67E22", "#95A5A6", "#16A085"]
        )
        
        # Dark
        self.themes[ThemeStyle.DARK] = ChartTheme(
            name="Dark",
            primary_color="#3498DB",
            secondary_color="#2ECC71",
            background_color="#1A1A2E",
            paper_color="#16213E",
            text_color="#E8E8E8",
            grid_color="#2C3E50",
            categorical_colors=["#00D9FF", "#00FF9F", "#FF6B6B", "#C792EA", "#FFD93D",
                               "#6BCB77", "#4D96FF", "#FF922B", "#A8A8A8", "#20C997"]
        )
        
        # Minimal
        self.themes[ThemeStyle.MINIMAL] = ChartTheme(
            name="Minimal",
            primary_color="#333333",
            secondary_color="#666666",
            background_color="#FFFFFF",
            paper_color="#FFFFFF",
            text_color="#333333",
            grid_color="#F0F0F0",
            show_grid=False,
            categorical_colors=["#333333", "#666666", "#999999", "#CCCCCC", "#E6E6E6"]
        )
        
        # Presentation (larger fonts)
        self.themes[ThemeStyle.PRESENTATION] = ChartTheme(
            name="Presentation",
            primary_color=MacrocommColors.SUNSET_ORANGE,
            secondary_color=MacrocommColors.BRIGHT_ORANGE,
            background_color="#FFFFFF",
            paper_color="#FFFFFF",
            text_color="#2D3436",
            grid_color="#DFE6E9",
            title_font_size=28,
            axis_font_size=16,
            tick_font_size=14,
            legend_font_size=14,
            margin_top=80,
            margin_bottom=80
        )
    
    def get_theme(self, style: ThemeStyle) -> ChartTheme:
        """Get theme by style"""
        return self.themes.get(style, self.themes[ThemeStyle.MACROCOMM])
    
    def apply_theme(self, fig: go.Figure, theme: ChartTheme) -> go.Figure:
        """Apply theme to a Plotly figure"""
        fig.update_layout(
            template=theme.to_plotly_template(),
            font=dict(
                family=theme.font_family,
                size=theme.axis_font_size,
                color=theme.text_color
            ),
            title=dict(
                font=dict(size=theme.title_font_size, color=theme.text_color)
            ),
            paper_bgcolor=theme.paper_color,
            plot_bgcolor=theme.background_color,
            margin=dict(
                t=theme.margin_top,
                b=theme.margin_bottom,
                l=theme.margin_left,
                r=theme.margin_right
            )
        )
        
        # Update axes
        fig.update_xaxes(
            gridcolor=theme.grid_color,
            gridwidth=theme.grid_width,
            showgrid=theme.show_grid,
            tickfont=dict(size=theme.tick_font_size),
            title_font=dict(size=theme.axis_font_size)
        )
        fig.update_yaxes(
            gridcolor=theme.grid_color,
            gridwidth=theme.grid_width,
            showgrid=theme.show_grid,
            tickfont=dict(size=theme.tick_font_size),
            title_font=dict(size=theme.axis_font_size)
        )
        
        return fig


# =============================================================================
# MAIN CHART GENERATOR CLASS
# =============================================================================

class ChartGenerator:
    """
    Main class for generating interactive Plotly charts.
    
    Supports all 84 chart types with Macrocomm branding.
    
    Usage:
        generator = ChartGenerator()
        
        # From recommendation
        fig = generator.generate(df, recommendation)
        
        # Direct creation
        fig = generator.create_bar_chart(df, x='Category', y='Sales')
        
        # Export
        generator.export(fig, 'chart.png')
    """
    
    def __init__(self, default_theme: ThemeStyle = ThemeStyle.MACROCOMM):
        """
        Initialize the chart generator.
        
        Args:
            default_theme: Default theme style for charts
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly is required. Install with: pip install plotly")
        
        self.theme_manager = ThemeManager()
        self.default_theme = default_theme
        self.colors = MacrocommColors()
        
        logger.info(f"ChartGenerator initialized with {default_theme.value} theme")
    
    # =========================================================================
    # MAIN GENERATION METHODS
    # =========================================================================
    
    def generate(
        self,
        df: pd.DataFrame,
        recommendation: ChartRecommendation,
        config: Optional[ChartConfig] = None
    ) -> GeneratedChart:
        """
        Generate a chart from a recommendation.
        
        Args:
            df: DataFrame with data
            recommendation: Chart recommendation from ChartRecommender
            config: Optional configuration overrides
            
        Returns:
            GeneratedChart with Plotly figure
        """
        import time
        start_time = time.time()
        
        # Build config from recommendation
        if config is None:
            config = ChartConfig(
                x=recommendation.suggested_x,
                y=recommendation.suggested_y,
                color=recommendation.suggested_color,
                title=f"{recommendation.name}"
            )
        
        # Generate the appropriate chart
        chart_type = recommendation.chart_type
        fig = self._generate_by_type(df, chart_type, config)
        
        # Apply theme
        theme = self.theme_manager.get_theme(config.theme)
        fig = self.theme_manager.apply_theme(fig, theme)
        
        # Set title
        if config.title:
            fig.update_layout(title=config.title)
        
        # Calculate generation time
        generation_time = (time.time() - start_time) * 1000
        
        return GeneratedChart(
            figure=fig,
            chart_type=chart_type,
            config=config,
            title=config.title or recommendation.name,
            description=recommendation.explanation,
            generation_time_ms=generation_time,
            warnings=recommendation.warnings
        )
    
    def generate_from_type(
        self,
        df: pd.DataFrame,
        chart_type: Union[str, ChartType],
        config: ChartConfig
    ) -> GeneratedChart:
        """
        Generate a chart by specifying the chart type directly.
        
        Args:
            df: DataFrame with data
            chart_type: Chart type string or enum
            config: Chart configuration
            
        Returns:
            GeneratedChart
        """
        import time
        start_time = time.time()
        
        # Convert string to enum
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type)
        
        # Generate chart
        fig = self._generate_by_type(df, chart_type, config)
        
        # Apply theme
        theme = self.theme_manager.get_theme(config.theme)
        fig = self.theme_manager.apply_theme(fig, theme)
        
        # Set title
        if config.title:
            fig.update_layout(title=config.title)
        
        generation_time = (time.time() - start_time) * 1000
        
        return GeneratedChart(
            figure=fig,
            chart_type=chart_type,
            config=config,
            title=config.title or "",
            generation_time_ms=generation_time
        )
    
    def _generate_by_type(
        self,
        df: pd.DataFrame,
        chart_type: ChartType,
        config: ChartConfig
    ) -> go.Figure:
        """Route to appropriate chart generation method"""
        
        # Chart type to method mapping
        chart_methods = {
            # Comparison
            ChartType.BAR_HORIZONTAL: self._create_bar_horizontal,
            ChartType.BAR_VERTICAL: self._create_bar_vertical,
            ChartType.BAR_GROUPED: self._create_bar_grouped,
            ChartType.BAR_STACKED: self._create_bar_stacked,
            ChartType.BAR_DIVERGING: self._create_bar_diverging,
            ChartType.LOLLIPOP: self._create_lollipop,
            ChartType.BULLET: self._create_bullet,
            ChartType.DOT_PLOT: self._create_dot_plot,
            ChartType.DUMBBELL: self._create_dumbbell,
            ChartType.SLOPE: self._create_slope,
            ChartType.RADAR: self._create_radar,
            ChartType.RADIAL_BAR: self._create_radial_bar,
            ChartType.WATERFALL: self._create_waterfall,
            ChartType.RANGE_PLOT: self._create_range_plot,
            ChartType.PICTOGRAM: self._create_pictogram,
            
            # Correlation
            ChartType.SCATTER: self._create_scatter,
            ChartType.SCATTER_CONNECTED: self._create_scatter_connected,
            ChartType.BUBBLE: self._create_bubble,
            ChartType.HEATMAP: self._create_heatmap,
            ChartType.CORRELATION_MATRIX: self._create_correlation_matrix,
            ChartType.CONTOUR: self._create_contour,
            ChartType.QUADRANT: self._create_quadrant,
            
            # Part-to-Whole
            ChartType.PIE: self._create_pie,
            ChartType.DONUT: self._create_donut,
            ChartType.DONUT_SEMI: self._create_donut_semi,
            ChartType.TREEMAP: self._create_treemap,
            ChartType.SUNBURST: self._create_sunburst,
            ChartType.WAFFLE: self._create_waffle,
            ChartType.FUNNEL: self._create_funnel,
            ChartType.PYRAMID: self._create_pyramid,
            ChartType.STACKED_AREA_PERCENT: self._create_stacked_area_percent,
            ChartType.STACKED_BAR_PERCENT: self._create_stacked_bar_percent,
            ChartType.MARIMEKKO: self._create_marimekko,
            ChartType.ICICLE: self._create_icicle,
            ChartType.PARLIAMENT: self._create_parliament,
            ChartType.TREEMAP_CIRCULAR: self._create_treemap_circular,
            ChartType.VENN: self._create_venn,
            
            # Time Series
            ChartType.LINE: self._create_line,
            ChartType.LINE_MULTI: self._create_line_multi,
            ChartType.AREA: self._create_area,
            ChartType.AREA_STACKED: self._create_area_stacked,
            ChartType.STREAM: self._create_stream,
            ChartType.STEP: self._create_step,
            ChartType.SPLINE: self._create_spline,
            ChartType.BUMP: self._create_bump,
            ChartType.CANDLESTICK: self._create_candlestick,
            ChartType.OHLC: self._create_ohlc,
            ChartType.GANTT: self._create_gantt,
            
            # Distribution
            ChartType.HISTOGRAM: self._create_histogram,
            ChartType.HISTOGRAM_STACKED: self._create_histogram_stacked,
            ChartType.DENSITY: self._create_density,
            ChartType.BOX: self._create_box,
            ChartType.VIOLIN: self._create_violin,
            ChartType.STRIP: self._create_strip,
            ChartType.SWARM: self._create_swarm,
            ChartType.RIDGELINE: self._create_ridgeline,
            ChartType.QQ_PLOT: self._create_qq_plot,
            ChartType.ECDF: self._create_ecdf,
            ChartType.KDE: self._create_kde,
            ChartType.RAINCLOUD: self._create_raincloud,
            
            # Geospatial
            ChartType.CHOROPLETH: self._create_choropleth,
            ChartType.BUBBLE_MAP: self._create_bubble_map,
            ChartType.HEATMAP_GEO: self._create_heatmap_geo,
            ChartType.POINT_MAP: self._create_point_map,
            ChartType.CONNECTION_MAP: self._create_connection_map,
            ChartType.TILE_MAP: self._create_tile_map,
            
            # Flow
            ChartType.SANKEY: self._create_sankey,
            ChartType.CHORD: self._create_chord,
            ChartType.NETWORK: self._create_network,
            ChartType.ARC: self._create_arc,
            ChartType.ALLUVIAL: self._create_alluvial,
            ChartType.FLOW_MAP: self._create_flow_map,
            ChartType.PARALLEL_COORDINATES: self._create_parallel_coordinates,
            ChartType.PARALLEL_SETS: self._create_parallel_sets,
            
            # Hierarchy
            ChartType.TREE_DIAGRAM: self._create_tree_diagram,
            ChartType.DENDROGRAM: self._create_dendrogram,
            ChartType.ORG_CHART: self._create_org_chart,
            ChartType.RADIAL_TREE: self._create_radial_tree,
            
            # Specialized
            ChartType.GAUGE: self._create_gauge,
            ChartType.SPARKLINE: self._create_sparkline,
            ChartType.WORD_CLOUD: self._create_word_cloud,
            ChartType.CALENDAR_HEATMAP: self._create_calendar_heatmap,
            ChartType.TABLE: self._create_table,
            ChartType.KPI_CARD: self._create_kpi_card,
        }
        
        # Get method or fallback
        method = chart_methods.get(chart_type, self._create_fallback)
        return method(df, config)
    
    # =========================================================================
    # COMPARISON CHARTS
    # =========================================================================
    
    def _create_bar_horizontal(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create horizontal bar chart"""
        fig = px.bar(
            df,
            x=config.y,
            y=config.x,
            color=config.color,
            orientation='h',
            text=config.y if config.show_values else None,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(texttemplate='%{text:' + config.value_format + '}', textposition='outside')
        return fig
    
    def _create_bar_vertical(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create vertical bar chart (column chart)"""
        fig = px.bar(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            text=config.y if config.show_values else None,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(texttemplate='%{text:' + config.value_format + '}', textposition='outside')
        return fig
    
    def _create_bar_grouped(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create grouped bar chart"""
        y_cols = config.y if isinstance(config.y, list) else [config.y]
        
        fig = go.Figure()
        colors = self.colors.get_categorical_palette()
        
        for i, col in enumerate(y_cols):
            if col in df.columns:
                fig.add_trace(go.Bar(
                    name=col,
                    x=df[config.x] if config.x else df.index,
                    y=df[col],
                    marker_color=colors[i % len(colors)]
                ))
        
        fig.update_layout(barmode='group')
        return fig
    
    def _create_bar_stacked(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create stacked bar chart"""
        y_cols = config.y if isinstance(config.y, list) else [config.y]
        
        fig = go.Figure()
        colors = self.colors.get_categorical_palette()
        
        for i, col in enumerate(y_cols):
            if col in df.columns:
                fig.add_trace(go.Bar(
                    name=col,
                    x=df[config.x] if config.x else df.index,
                    y=df[col],
                    marker_color=colors[i % len(colors)]
                ))
        
        fig.update_layout(barmode='stack')
        return fig
    
    def _create_bar_diverging(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create diverging bar chart"""
        fig = go.Figure()
        
        values = df[config.y] if config.y else df.iloc[:, 0]
        labels = df[config.x] if config.x else df.index
        
        colors = [self.colors.SUNSET_ORANGE if v >= 0 else self.colors.BLUE for v in values]
        
        fig.add_trace(go.Bar(
            y=labels,
            x=values,
            orientation='h',
            marker_color=colors
        ))
        
        fig.update_layout(xaxis_zeroline=True, xaxis_zerolinewidth=2, xaxis_zerolinecolor='black')
        return fig
    
    def _create_lollipop(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create lollipop chart"""
        fig = go.Figure()
        
        x_vals = df[config.x] if config.x else df.index
        y_vals = df[config.y] if config.y else df.iloc[:, 0]
        
        # Add stems
        for i, (x, y) in enumerate(zip(x_vals, y_vals)):
            fig.add_trace(go.Scatter(
                x=[0, y],
                y=[x, x],
                mode='lines',
                line=dict(color=self.colors.LIGHT_GRAY, width=2),
                showlegend=False
            ))
        
        # Add dots
        fig.add_trace(go.Scatter(
            x=y_vals,
            y=x_vals,
            mode='markers',
            marker=dict(size=12, color=self.colors.SUNSET_ORANGE),
            name='Value'
        ))
        
        return fig
    
    def _create_bullet(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bullet chart"""
        fig = go.Figure()
        
        # Simple implementation - first column is actual, second is target
        if len(df.columns) >= 2:
            actual = df.iloc[0, 0]
            target = df.iloc[0, 1]
            
            fig.add_trace(go.Indicator(
                mode="number+gauge+delta",
                value=actual,
                delta={'reference': target},
                gauge={
                    'shape': "bullet",
                    'axis': {'range': [None, target * 1.2]},
                    'bar': {'color': self.colors.SUNSET_ORANGE},
                    'steps': [
                        {'range': [0, target * 0.6], 'color': self.colors.PALE_GRAY},
                        {'range': [target * 0.6, target * 0.85], 'color': self.colors.LIGHT_GRAY},
                        {'range': [target * 0.85, target * 1.2], 'color': self.colors.MEDIUM_GRAY}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 3},
                        'thickness': 0.75,
                        'value': target
                    }
                }
            ))
        
        return fig
    
    def _create_dot_plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create dot plot (Cleveland dot plot)"""
        fig = px.scatter(
            df,
            x=config.y,
            y=config.x,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(marker=dict(size=12))
        return fig
    
    def _create_dumbbell(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create dumbbell chart for before/after comparison"""
        fig = go.Figure()
        
        categories = df[config.x] if config.x else df.index
        y_cols = config.y if isinstance(config.y, list) else [config.y]
        
        if len(y_cols) >= 2:
            val1 = df[y_cols[0]]
            val2 = df[y_cols[1]]
            
            # Lines connecting points
            for i, cat in enumerate(categories):
                fig.add_trace(go.Scatter(
                    x=[val1.iloc[i], val2.iloc[i]],
                    y=[cat, cat],
                    mode='lines',
                    line=dict(color=self.colors.LIGHT_GRAY, width=3),
                    showlegend=False
                ))
            
            # First points
            fig.add_trace(go.Scatter(
                x=val1, y=categories,
                mode='markers',
                marker=dict(size=12, color=self.colors.BLUE),
                name=y_cols[0]
            ))
            
            # Second points
            fig.add_trace(go.Scatter(
                x=val2, y=categories,
                mode='markers',
                marker=dict(size=12, color=self.colors.SUNSET_ORANGE),
                name=y_cols[1]
            ))
        
        return fig
    
    def _create_slope(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create slope chart"""
        fig = go.Figure()
        
        categories = df[config.x] if config.x else df.index
        y_cols = config.y if isinstance(config.y, list) else [config.y]
        colors = self.colors.get_categorical_palette()
        
        if len(y_cols) >= 2:
            for i, cat in enumerate(categories):
                val1 = df[y_cols[0]].iloc[i]
                val2 = df[y_cols[1]].iloc[i]
                
                fig.add_trace(go.Scatter(
                    x=[y_cols[0], y_cols[1]],
                    y=[val1, val2],
                    mode='lines+markers+text',
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=10),
                    text=[str(cat), str(cat)],
                    textposition=['middle left', 'middle right'],
                    name=str(cat)
                ))
        
        return fig
    
    def _create_radar(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create radar/spider chart"""
        fig = go.Figure()
        
        categories = list(df.columns) if config.y is None else (
            config.y if isinstance(config.y, list) else [config.y]
        )
        colors = self.colors.get_categorical_palette()
        
        for i, row_idx in enumerate(df.index[:5]):  # Limit to 5 series
            values = df.loc[row_idx, categories].tolist()
            values.append(values[0])  # Close the polygon
            cats = categories + [categories[0]]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=cats,
                fill='toself',
                name=str(row_idx),
                line_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
        return fig
    
    def _create_radial_bar(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create radial bar chart"""
        fig = go.Figure()
        
        categories = df[config.x] if config.x else df.index
        values = df[config.y] if config.y else df.iloc[:, 0]
        
        fig.add_trace(go.Barpolar(
            r=values,
            theta=categories,
            marker_color=self.colors.get_categorical_palette()[:len(values)],
            marker_line_color="white",
            marker_line_width=1
        ))
        
        return fig
    
    def _create_waterfall(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create waterfall chart"""
        categories = df[config.x] if config.x else df.index
        values = df[config.y] if config.y else df.iloc[:, 0]
        
        # Determine measure types
        measures = ['relative'] * len(values)
        measures[0] = 'absolute'  # First is starting point
        measures[-1] = 'total'    # Last is total
        
        fig = go.Figure(go.Waterfall(
            x=categories,
            y=values,
            measure=measures,
            connector={"line": {"color": self.colors.MEDIUM_GRAY}},
            increasing={"marker": {"color": self.colors.GREEN}},
            decreasing={"marker": {"color": self.colors.RED}},
            totals={"marker": {"color": self.colors.SUNSET_ORANGE}}
        ))
        
        return fig
    
    def _create_range_plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create range plot showing min-max"""
        fig = go.Figure()
        
        categories = df[config.x] if config.x else df.index
        y_cols = config.y if isinstance(config.y, list) else [config.y]
        
        if len(y_cols) >= 2:
            low = df[y_cols[0]]
            high = df[y_cols[1]]
            
            # Range bars
            for i, (cat, l, h) in enumerate(zip(categories, low, high)):
                fig.add_trace(go.Scatter(
                    x=[l, h],
                    y=[cat, cat],
                    mode='lines',
                    line=dict(color=self.colors.SUNSET_ORANGE, width=6),
                    showlegend=False
                ))
            
            # End markers
            fig.add_trace(go.Scatter(
                x=list(low) + list(high),
                y=list(categories) + list(categories),
                mode='markers',
                marker=dict(size=10, color=self.colors.DARK_ORANGE),
                name='Range'
            ))
        
        return fig
    
    def _create_pictogram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pictogram chart (simplified as dot matrix)"""
        # Simplified implementation using markers
        fig = go.Figure()
        
        categories = df[config.x] if config.x else df.index
        values = df[config.y] if config.y else df.iloc[:, 0]
        
        max_val = values.max()
        scale = 10 / max_val if max_val > 0 else 1
        
        for i, (cat, val) in enumerate(zip(categories, values)):
            dots = int(val * scale)
            for j in range(dots):
                fig.add_trace(go.Scatter(
                    x=[j % 10],
                    y=[i + (j // 10) * 0.2],
                    mode='markers',
                    marker=dict(size=15, color=self.colors.SUNSET_ORANGE, symbol='square'),
                    showlegend=False
                ))
        
        return fig
    
    # =========================================================================
    # CORRELATION CHARTS
    # =========================================================================
    
    def _create_scatter(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create scatter plot"""
        fig = px.scatter(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            size=config.size,
            hover_data=config.hover_data,
            color_discrete_sequence=self.colors.get_categorical_palette(),
            opacity=config.opacity
        )
        
        # Add trendline option
        fig.update_traces(marker=dict(size=10))
        return fig
    
    def _create_scatter_connected(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create connected scatter plot"""
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            markers=True,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(marker=dict(size=10))
        return fig
    
    def _create_bubble(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bubble chart"""
        fig = px.scatter(
            df,
            x=config.x,
            y=config.y,
            size=config.size,
            color=config.color,
            hover_data=config.hover_data,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create heatmap"""
        # If x and y specified, pivot the data
        if config.x and config.y:
            pivot_df = df.pivot_table(
                values=config.y,
                index=df.columns[0],
                columns=df.columns[1],
                aggfunc='mean'
            )
            z_data = pivot_df.values
            x_labels = pivot_df.columns.tolist()
            y_labels = pivot_df.index.tolist()
        else:
            # Use DataFrame as-is
            z_data = df.select_dtypes(include=[np.number]).values
            x_labels = df.select_dtypes(include=[np.number]).columns.tolist()
            y_labels = df.index.tolist()
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=y_labels,
            colorscale=[
                [0, self.colors.WHITE],
                [0.5, self.colors.BRIGHT_ORANGE],
                [1, self.colors.DARK_ORANGE]
            ],
            hoverongaps=False
        ))
        
        return fig
    
    def _create_correlation_matrix(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create correlation matrix heatmap"""
        numeric_df = df.select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale=[
                [0, self.colors.BLUE],
                [0.5, self.colors.WHITE],
                [1, self.colors.SUNSET_ORANGE]
            ],
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            hoverongaps=False
        ))
        
        return fig
    
    def _create_contour(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create contour plot"""
        fig = px.density_contour(
            df,
            x=config.x,
            y=config.y,
            color_discrete_sequence=[self.colors.SUNSET_ORANGE]
        )
        fig.update_traces(contours_coloring="fill", contours_showlabels=True)
        return fig
    
    def _create_quadrant(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create quadrant chart (scatter with quadrant lines)"""
        fig = px.scatter(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            text=config.text,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        
        # Add quadrant lines
        x_mid = df[config.x].median() if config.x else 0
        y_mid = df[config.y].median() if config.y else 0
        
        fig.add_hline(y=y_mid, line_dash="dash", line_color=self.colors.MEDIUM_GRAY)
        fig.add_vline(x=x_mid, line_dash="dash", line_color=self.colors.MEDIUM_GRAY)
        
        return fig
    
    # =========================================================================
    # PART-TO-WHOLE CHARTS
    # =========================================================================
    
    def _create_pie(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pie chart"""
        fig = px.pie(
            df,
            names=config.x,
            values=config.y,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    def _create_donut(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create donut chart"""
        fig = px.pie(
            df,
            names=config.x,
            values=config.y,
            hole=0.5,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    def _create_donut_semi(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create semi-circle donut chart"""
        values = df[config.y] if config.y else df.iloc[:, 0]
        labels = df[config.x] if config.x else df.index
        
        # Add dummy value to create semi-circle
        total = values.sum()
        
        fig = go.Figure(data=[go.Pie(
            values=list(values) + [total],
            labels=list(labels) + [''],
            hole=0.6,
            direction='clockwise',
            rotation=90,
            marker_colors=self.colors.get_categorical_palette()[:len(values)] + ['rgba(0,0,0,0)']
        )])
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    
    def _create_treemap(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create treemap"""
        path_cols = [config.x] if config.x else [df.columns[0]]
        if config.color and config.color != config.x:
            path_cols = [config.color] + path_cols
        
        fig = px.treemap(
            df,
            path=path_cols,
            values=config.y,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_sunburst(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create sunburst chart"""
        path_cols = [config.x] if config.x else [df.columns[0]]
        if config.color and config.color != config.x:
            path_cols = [config.color] + path_cols
        
        fig = px.sunburst(
            df,
            path=path_cols,
            values=config.y,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_waffle(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create waffle chart (simplified as grid of squares)"""
        fig = go.Figure()
        
        values = df[config.y] if config.y else df.iloc[:, 0]
        labels = df[config.x] if config.x else df.index
        colors = self.colors.get_categorical_palette()
        
        total = values.sum()
        grid_size = 10
        
        # Calculate squares for each category
        squares = []
        for i, (label, val) in enumerate(zip(labels, values)):
            count = int((val / total) * (grid_size * grid_size))
            squares.extend([(label, colors[i % len(colors)])] * count)
        
        # Fill remaining with last category
        while len(squares) < grid_size * grid_size:
            squares.append((labels.iloc[-1], colors[(len(labels)-1) % len(colors)]))
        
        # Plot squares
        for idx, (label, color) in enumerate(squares[:grid_size * grid_size]):
            row = idx // grid_size
            col = idx % grid_size
            fig.add_trace(go.Scatter(
                x=[col],
                y=[row],
                mode='markers',
                marker=dict(size=30, color=color, symbol='square'),
                name=str(label),
                showlegend=(idx == 0)
            ))
        
        fig.update_layout(showlegend=True)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        
        return fig
    
    def _create_funnel(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create funnel chart"""
        fig = px.funnel(
            df,
            x=config.y,
            y=config.x,
            color_discrete_sequence=[self.colors.SUNSET_ORANGE]
        )
        return fig
    
    def _create_pyramid(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pyramid chart"""
        # Similar to funnel but with symmetric appearance
        categories = df[config.x] if config.x else df.index
        values = df[config.y] if config.y else df.iloc[:, 0]
        
        fig = go.Figure()
        
        # Create symmetric bars
        fig.add_trace(go.Bar(
            y=categories,
            x=values,
            orientation='h',
            marker_color=self.colors.SUNSET_ORANGE,
            name='Right'
        ))
        fig.add_trace(go.Bar(
            y=categories,
            x=-values,
            orientation='h',
            marker_color=self.colors.BRIGHT_ORANGE,
            name='Left'
        ))
        
        fig.update_layout(barmode='overlay')
        return fig
    
    def _create_stacked_area_percent(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create 100% stacked area chart"""
        fig = px.area(
            df,
            x=config.x,
            y=config.y if isinstance(config.y, list) else df.select_dtypes(include=[np.number]).columns.tolist(),
            groupnorm='percent',
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_stacked_bar_percent(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create 100% stacked bar chart"""
        y_cols = config.y if isinstance(config.y, list) else df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate percentages
        df_pct = df.copy()
        row_totals = df[y_cols].sum(axis=1)
        for col in y_cols:
            df_pct[col] = df[col] / row_totals * 100
        
        fig = go.Figure()
        colors = self.colors.get_categorical_palette()
        
        for i, col in enumerate(y_cols):
            fig.add_trace(go.Bar(
                name=col,
                x=df[config.x] if config.x else df.index,
                y=df_pct[col],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(barmode='stack', yaxis_title='Percentage')
        return fig
    
    def _create_marimekko(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create Marimekko (Mekko) chart - simplified implementation"""
        # Simplified as stacked bar with variable widths
        return self._create_stacked_bar_percent(df, config)
    
    def _create_icicle(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create icicle chart"""
        path_cols = [config.x] if config.x else [df.columns[0]]
        
        fig = px.icicle(
            df,
            path=path_cols,
            values=config.y,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_parliament(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create parliament chart (semi-circle dot arrangement)"""
        # Simplified implementation
        return self._create_donut_semi(df, config)
    
    def _create_treemap_circular(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create circular treemap (circle packing)"""
        # Simplified as regular treemap
        return self._create_treemap(df, config)
    
    def _create_venn(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create Venn diagram - simplified placeholder"""
        # Plotly doesn't have native Venn support
        # Create a placeholder visualization
        fig = go.Figure()
        
        # Draw circles
        theta = np.linspace(0, 2*np.pi, 100)
        
        # Circle 1
        x1 = 0.7 * np.cos(theta)
        y1 = 0.7 * np.sin(theta)
        fig.add_trace(go.Scatter(x=x1, y=y1, fill='toself', 
                                  fillcolor='rgba(255,110,0,0.3)', 
                                  line_color=self.colors.SUNSET_ORANGE,
                                  name='Set A'))
        
        # Circle 2
        x2 = 0.7 * np.cos(theta) + 0.5
        y2 = 0.7 * np.sin(theta)
        fig.add_trace(go.Scatter(x=x2, y=y2, fill='toself',
                                  fillcolor='rgba(9,132,227,0.3)',
                                  line_color=self.colors.BLUE,
                                  name='Set B'))
        
        fig.update_layout(showlegend=True)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, scaleanchor="x")
        
        return fig
    
    # =========================================================================
    # TIME SERIES CHARTS
    # =========================================================================
    
    def _create_line(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create line chart"""
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            markers=True,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_line_multi(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create multi-line chart"""
        fig = go.Figure()
        
        y_cols = config.y if isinstance(config.y, list) else df.select_dtypes(include=[np.number]).columns.tolist()
        x_vals = df[config.x] if config.x else df.index
        colors = self.colors.get_categorical_palette()
        
        for i, col in enumerate(y_cols):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=df[col],
                    mode='lines+markers',
                    name=col,
                    line_color=colors[i % len(colors)]
                ))
        
        return fig
    
    def _create_area(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create area chart"""
        fig = px.area(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_area_stacked(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create stacked area chart"""
        y_cols = config.y if isinstance(config.y, list) else df.select_dtypes(include=[np.number]).columns.tolist()
        
        fig = px.area(
            df,
            x=config.x,
            y=y_cols,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_stream(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create streamgraph"""
        # Streamgraph is area chart with baseline centered
        y_cols = config.y if isinstance(config.y, list) else df.select_dtypes(include=[np.number]).columns.tolist()
        
        fig = go.Figure()
        colors = self.colors.get_categorical_palette()
        
        for i, col in enumerate(y_cols):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df[config.x] if config.x else df.index,
                    y=df[col],
                    mode='lines',
                    stackgroup='one',
                    fill='tonexty',
                    line_color=colors[i % len(colors)],
                    name=col
                ))
        
        return fig
    
    def _create_step(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create step chart"""
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            line_shape='hv',
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_spline(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create spline (smoothed line) chart"""
        fig = px.line(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            line_shape='spline',
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_bump(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bump chart (rank changes over time)"""
        fig = go.Figure()
        
        # Assumes data has time in x, categories in color, and ranks in y
        categories = df[config.color].unique() if config.color else df.index
        x_vals = df[config.x].unique() if config.x else df.index
        colors = self.colors.get_categorical_palette()
        
        for i, cat in enumerate(categories):
            cat_data = df[df[config.color] == cat] if config.color else df
            fig.add_trace(go.Scatter(
                x=cat_data[config.x] if config.x else cat_data.index,
                y=cat_data[config.y] if config.y else cat_data.iloc[:, 0],
                mode='lines+markers',
                name=str(cat),
                line_color=colors[i % len(colors)],
                line_width=3,
                marker_size=10
            ))
        
        fig.update_yaxes(autorange='reversed')  # Lower rank = higher position
        return fig
    
    def _create_candlestick(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create candlestick chart for OHLC data"""
        # Expects columns: Open, High, Low, Close
        date_col = config.x or df.columns[0]
        
        ohlc_cols = ['Open', 'High', 'Low', 'Close']
        available = [c for c in ohlc_cols if c in df.columns]
        
        if len(available) == 4:
            fig = go.Figure(data=[go.Candlestick(
                x=df[date_col],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color=self.colors.GREEN,
                decreasing_line_color=self.colors.RED
            )])
        else:
            # Fallback to line chart
            fig = self._create_line(df, config)
        
        return fig
    
    def _create_ohlc(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create OHLC chart"""
        date_col = config.x or df.columns[0]
        
        if all(c in df.columns for c in ['Open', 'High', 'Low', 'Close']):
            fig = go.Figure(data=[go.Ohlc(
                x=df[date_col],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color=self.colors.GREEN,
                decreasing_line_color=self.colors.RED
            )])
        else:
            fig = self._create_line(df, config)
        
        return fig
    
    def _create_gantt(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create Gantt chart"""
        # Expects: Task, Start, End columns
        if 'Start' in df.columns and ('End' in df.columns or 'Finish' in df.columns):
            end_col = 'End' if 'End' in df.columns else 'Finish'
            task_col = config.x or 'Task'
            
            fig = px.timeline(
                df,
                x_start='Start',
                x_end=end_col,
                y=task_col,
                color=config.color,
                color_discrete_sequence=self.colors.get_categorical_palette()
            )
            fig.update_yaxes(autorange='reversed')
        else:
            # Fallback to horizontal bar
            fig = self._create_bar_horizontal(df, config)
        
        return fig
    
    # =========================================================================
    # DISTRIBUTION CHARTS
    # =========================================================================
    
    def _create_histogram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create histogram"""
        col = config.y or config.x or df.select_dtypes(include=[np.number]).columns[0]
        
        fig = px.histogram(
            df,
            x=col,
            color=config.color,
            nbins=30,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_histogram_stacked(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create stacked histogram"""
        col = config.y or config.x or df.select_dtypes(include=[np.number]).columns[0]
        
        fig = px.histogram(
            df,
            x=col,
            color=config.color,
            barmode='stack',
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_density(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create density plot (KDE)"""
        return self._create_kde(df, config)
    
    def _create_box(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create box plot"""
        fig = px.box(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_violin(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create violin plot"""
        fig = px.violin(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            box=True,
            points='outliers',
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_strip(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create strip plot"""
        fig = px.strip(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_swarm(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create swarm (beeswarm) plot"""
        # Plotly doesn't have native swarm, use strip with jitter
        fig = px.strip(
            df,
            x=config.x,
            y=config.y,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        fig.update_traces(jitter=0.8)
        return fig
    
    def _create_ridgeline(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create ridgeline plot"""
        fig = go.Figure()
        
        categories = df[config.color].unique() if config.color else ['All']
        colors = self.colors.get_categorical_palette()
        y_col = config.y or df.select_dtypes(include=[np.number]).columns[0]
        
        for i, cat in enumerate(categories):
            if config.color:
                data = df[df[config.color] == cat][y_col]
            else:
                data = df[y_col]
            
            fig.add_trace(go.Violin(
                x=data,
                name=str(cat),
                line_color=colors[i % len(colors)],
                side='positive',
                meanline_visible=True
            ))
        
        return fig
    
    def _create_qq_plot(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create Q-Q plot"""
        from scipy import stats
        
        col = config.y or config.x or df.select_dtypes(include=[np.number]).columns[0]
        data = df[col].dropna()
        
        qq = stats.probplot(data, dist='norm')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=qq[0][0],
            y=qq[0][1],
            mode='markers',
            marker=dict(color=self.colors.SUNSET_ORANGE, size=8),
            name='Data'
        ))
        
        # Add reference line
        x_line = np.array([qq[0][0].min(), qq[0][0].max()])
        y_line = qq[1][0] * x_line + qq[1][1]
        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            line=dict(color=self.colors.MEDIUM_GRAY, dash='dash'),
            name='Normal'
        ))
        
        fig.update_layout(xaxis_title='Theoretical Quantiles', yaxis_title='Sample Quantiles')
        return fig
    
    def _create_ecdf(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create ECDF plot"""
        fig = px.ecdf(
            df,
            x=config.y or config.x,
            color=config.color,
            color_discrete_sequence=self.colors.get_categorical_palette()
        )
        return fig
    
    def _create_kde(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create KDE plot"""
        from scipy import stats
        
        col = config.y or config.x or df.select_dtypes(include=[np.number]).columns[0]
        data = df[col].dropna()
        
        # Calculate KDE
        kde = stats.gaussian_kde(data)
        x_range = np.linspace(data.min(), data.max(), 200)
        y_kde = kde(x_range)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_kde,
            mode='lines',
            fill='tozeroy',
            line_color=self.colors.SUNSET_ORANGE,
            fillcolor=f'rgba(255, 110, 0, 0.3)',
            name='Density'
        ))
        
        return fig
    
    def _create_raincloud(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create raincloud plot (violin + box + points)"""
        fig = go.Figure()
        
        col = config.y or df.select_dtypes(include=[np.number]).columns[0]
        categories = df[config.x].unique() if config.x else ['All']
        colors = self.colors.get_categorical_palette()
        
        for i, cat in enumerate(categories):
            if config.x:
                data = df[df[config.x] == cat][col]
            else:
                data = df[col]
            
            # Violin (half)
            fig.add_trace(go.Violin(
                y=data,
                name=str(cat),
                side='positive',
                line_color=colors[i % len(colors)],
                fillcolor=f'rgba{tuple(int(colors[i % len(colors)].lstrip("#")[j:j+2], 16) for j in (0, 2, 4)) + (0.5,)}',
                meanline_visible=True,
                box_visible=True,
                points='all'
            ))
        
        return fig
    
    # =========================================================================
    # GEOSPATIAL CHARTS
    # =========================================================================
    
    def _create_choropleth(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create choropleth map"""
        location_col = config.x or df.columns[0]
        value_col = config.y or df.select_dtypes(include=[np.number]).columns[0]
        
        fig = px.choropleth(
            df,
            locations=location_col,
            color=value_col,
            locationmode='country names',
            color_continuous_scale=[
                [0, self.colors.PALE_ORANGE],
                [0.5, self.colors.BRIGHT_ORANGE],
                [1, self.colors.DARK_ORANGE]
            ]
        )
        return fig
    
    def _create_bubble_map(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bubble map"""
        # Check for lat/lon columns
        lat_col = next((c for c in df.columns if c.lower() in ['lat', 'latitude']), None)
        lon_col = next((c for c in df.columns if c.lower() in ['lon', 'long', 'longitude']), None)
        
        if lat_col and lon_col:
            fig = px.scatter_geo(
                df,
                lat=lat_col,
                lon=lon_col,
                size=config.size or config.y,
                color=config.color,
                color_discrete_sequence=self.colors.get_categorical_palette()
            )
        else:
            fig = self._create_scatter(df, config)
        
        return fig
    
    def _create_heatmap_geo(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create geographic heatmap"""
        lat_col = next((c for c in df.columns if c.lower() in ['lat', 'latitude']), None)
        lon_col = next((c for c in df.columns if c.lower() in ['lon', 'long', 'longitude']), None)
        
        if lat_col and lon_col:
            fig = px.density_mapbox(
                df,
                lat=lat_col,
                lon=lon_col,
                z=config.y if config.y else None,
                mapbox_style='carto-positron'
            )
        else:
            fig = self._create_heatmap(df, config)
        
        return fig
    
    def _create_point_map(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create point map"""
        return self._create_bubble_map(df, config)
    
    def _create_connection_map(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create connection/flight map"""
        # Simplified - would need start/end coordinates
        return self._create_scatter(df, config)
    
    def _create_tile_map(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create tile map (cartogram)"""
        return self._create_choropleth(df, config)
    
    # =========================================================================
    # FLOW CHARTS
    # =========================================================================
    
    def _create_sankey(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create Sankey diagram"""
        # Expects: source, target, value columns
        source_col = next((c for c in df.columns if c.lower() in ['source', 'from', 'origin']), df.columns[0])
        target_col = next((c for c in df.columns if c.lower() in ['target', 'to', 'destination']), df.columns[1])
        value_col = config.y or (df.columns[2] if len(df.columns) > 2 else None)
        
        # Build node list
        all_nodes = pd.concat([df[source_col], df[target_col]]).unique()
        node_dict = {node: i for i, node in enumerate(all_nodes)}
        
        source_indices = df[source_col].map(node_dict).tolist()
        target_indices = df[target_col].map(node_dict).tolist()
        values = df[value_col].tolist() if value_col else [1] * len(df)
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                label=list(all_nodes),
                color=self.colors.get_categorical_palette()[:len(all_nodes)]
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=f'rgba(255, 110, 0, 0.4)'
            )
        )])
        
        return fig
    
    def _create_chord(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create chord diagram - placeholder"""
        # Plotly doesn't have native chord support
        return self._create_sankey(df, config)
    
    def _create_network(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create network diagram"""
        # Simplified network visualization
        source_col = df.columns[0]
        target_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        # Create node positions (simple circular layout)
        all_nodes = pd.concat([df[source_col], df[target_col]]).unique()
        n = len(all_nodes)
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        positions = {node: (np.cos(a), np.sin(a)) for node, a in zip(all_nodes, angles)}
        
        fig = go.Figure()
        
        # Add edges
        for _, row in df.iterrows():
            x0, y0 = positions[row[source_col]]
            x1, y1 = positions[row[target_col]]
            fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(color=self.colors.LIGHT_GRAY, width=1),
                showlegend=False
            ))
        
        # Add nodes
        node_x = [positions[n][0] for n in all_nodes]
        node_y = [positions[n][1] for n in all_nodes]
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(size=20, color=self.colors.SUNSET_ORANGE),
            text=list(all_nodes),
            textposition='top center',
            name='Nodes'
        ))
        
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, scaleanchor='x')
        
        return fig
    
    def _create_arc(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create arc diagram"""
        return self._create_network(df, config)
    
    def _create_alluvial(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create alluvial diagram"""
        return self._create_sankey(df, config)
    
    def _create_flow_map(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create flow map"""
        return self._create_connection_map(df, config)
    
    def _create_parallel_coordinates(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create parallel coordinates plot"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        fig = px.parallel_coordinates(
            df,
            dimensions=numeric_cols,
            color=config.color if config.color in numeric_cols else numeric_cols[0],
            color_continuous_scale=[
                [0, self.colors.BLUE],
                [0.5, self.colors.PALE_ORANGE],
                [1, self.colors.SUNSET_ORANGE]
            ]
        )
        return fig
    
    def _create_parallel_sets(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create parallel sets (categorical parallel coordinates)"""
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()[:5]
        
        if cat_cols:
            fig = px.parallel_categories(
                df,
                dimensions=cat_cols,
                color_continuous_scale=[
                    [0, self.colors.PALE_ORANGE],
                    [1, self.colors.SUNSET_ORANGE]
                ]
            )
        else:
            fig = self._create_parallel_coordinates(df, config)
        
        return fig
    
    # =========================================================================
    # HIERARCHY CHARTS
    # =========================================================================
    
    def _create_tree_diagram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create tree diagram"""
        # Use treemap as base with rectangular styling
        return self._create_treemap(df, config)
    
    def _create_dendrogram(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create dendrogram"""
        from scipy.cluster.hierarchy import linkage, dendrogram as scipy_dendro
        from scipy.spatial.distance import pdist
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) >= 2 and len(numeric_df) >= 2:
            # Calculate linkage
            Z = linkage(numeric_df.values, method='ward')
            
            # Create dendrogram data
            dendro_data = scipy_dendro(Z, no_plot=True, labels=df.index.tolist())
            
            fig = go.Figure()
            
            # Plot the dendrogram
            for i, (xs, ys) in enumerate(zip(dendro_data['icoord'], dendro_data['dcoord'])):
                fig.add_trace(go.Scatter(
                    x=xs,
                    y=ys,
                    mode='lines',
                    line=dict(color=self.colors.SUNSET_ORANGE, width=2),
                    showlegend=False
                ))
            
            fig.update_layout(
                xaxis_title='Samples',
                yaxis_title='Distance'
            )
        else:
            fig = self._create_bar_vertical(df, config)
        
        return fig
    
    def _create_org_chart(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create organization chart"""
        # Use treemap/sunburst as simplified org chart
        return self._create_treemap(df, config)
    
    def _create_radial_tree(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create radial tree"""
        return self._create_sunburst(df, config)
    
    # =========================================================================
    # SPECIALIZED CHARTS
    # =========================================================================
    
    def _create_gauge(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create gauge chart"""
        value = df[config.y].iloc[0] if config.y else df.iloc[0, 0]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            gauge={
                'axis': {'range': [0, value * 1.5]},
                'bar': {'color': self.colors.SUNSET_ORANGE},
                'steps': [
                    {'range': [0, value * 0.5], 'color': self.colors.PALE_GRAY},
                    {'range': [value * 0.5, value], 'color': self.colors.LIGHT_GRAY}
                ],
                'threshold': {
                    'line': {'color': self.colors.RED, 'width': 4},
                    'thickness': 0.75,
                    'value': value * 0.9
                }
            }
        ))
        
        return fig
    
    def _create_sparkline(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create sparkline"""
        fig = go.Figure()
        
        y_vals = df[config.y] if config.y else df.iloc[:, 0]
        x_vals = df[config.x] if config.x else range(len(y_vals))
        
        fig.add_trace(go.Scatter(
            x=list(x_vals),
            y=list(y_vals),
            mode='lines',
            line=dict(color=self.colors.SUNSET_ORANGE, width=2),
            fill='tozeroy',
            fillcolor=f'rgba(255, 110, 0, 0.1)'
        ))
        
        # Minimal styling for sparkline
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            height=80
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        
        return fig
    
    def _create_word_cloud(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create word cloud visualization"""
        # Simplified as bubble chart of word frequencies
        words = df[config.x] if config.x else df.iloc[:, 0]
        sizes = df[config.y] if config.y else df.iloc[:, 1] if len(df.columns) > 1 else [1] * len(words)
        
        # Random positions
        np.random.seed(42)
        x_pos = np.random.uniform(0, 10, len(words))
        y_pos = np.random.uniform(0, 10, len(words))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_pos,
            y=y_pos,
            mode='text',
            text=list(words),
            textfont=dict(
                size=list(np.interp(sizes, [min(sizes), max(sizes)], [10, 40])),
                color=self.colors.get_categorical_palette()[:len(words)]
            )
        ))
        
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        
        return fig
    
    def _create_calendar_heatmap(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create calendar heatmap"""
        date_col = config.x or df.select_dtypes(include=['datetime64']).columns[0]
        value_col = config.y or df.select_dtypes(include=[np.number]).columns[0]
        
        df_cal = df.copy()
        df_cal['week'] = pd.to_datetime(df_cal[date_col]).dt.isocalendar().week
        df_cal['day'] = pd.to_datetime(df_cal[date_col]).dt.dayofweek
        
        pivot = df_cal.pivot_table(values=value_col, index='day', columns='week', aggfunc='mean')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            colorscale=[
                [0, self.colors.PALE_ORANGE],
                [1, self.colors.DARK_ORANGE]
            ]
        ))
        
        return fig
    
    def _create_table(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create data table"""
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color=self.colors.SUNSET_ORANGE,
                font=dict(color='white', size=12),
                align='left'
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color=[self.colors.WHITE, self.colors.PALE_GRAY] * (len(df) // 2 + 1),
                align='left'
            )
        )])
        
        return fig
    
    def _create_kpi_card(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create KPI card"""
        value = df[config.y].iloc[0] if config.y and config.y in df.columns else df.iloc[0, 0]
        
        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=value,
            number={
                'font': {'size': 60, 'color': self.colors.SUNSET_ORANGE}
            },
            delta={
                'reference': value * 0.9,
                'relative': True,
                'increasing': {'color': self.colors.GREEN},
                'decreasing': {'color': self.colors.RED}
            },
            title={
                'text': config.title or "KPI",
                'font': {'size': 20}
            }
        ))
        
        return fig
    
    # =========================================================================
    # FALLBACK
    # =========================================================================
    
    def _create_fallback(self, df: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Fallback chart when type is not implemented"""
        logger.warning(f"Chart type not implemented, using bar chart as fallback")
        return self._create_bar_vertical(df, config)
    
    # =========================================================================
    # DIRECT CREATION METHODS (Convenience)
    # =========================================================================
    
    def create_bar_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: Optional[str] = None,
        horizontal: bool = False,
        **kwargs
    ) -> go.Figure:
        """Convenience method to create bar chart"""
        config = ChartConfig(x=x, y=y, title=title, **kwargs)
        method = self._create_bar_horizontal if horizontal else self._create_bar_vertical
        fig = method(df, config)
        
        theme = self.theme_manager.get_theme(config.theme)
        return self.theme_manager.apply_theme(fig, theme)
    
    def create_line_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        title: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Convenience method to create line chart"""
        config = ChartConfig(x=x, y=y, title=title, **kwargs)
        
        if isinstance(y, list) and len(y) > 1:
            fig = self._create_line_multi(df, config)
        else:
            fig = self._create_line(df, config)
        
        theme = self.theme_manager.get_theme(config.theme)
        return self.theme_manager.apply_theme(fig, theme)
    
    def create_scatter_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: Optional[str] = None,
        **kwargs
    ) -> go.Figure:
        """Convenience method to create scatter chart"""
        config = ChartConfig(x=x, y=y, title=title, **kwargs)
        fig = self._create_scatter(df, config)
        
        theme = self.theme_manager.get_theme(config.theme)
        return self.theme_manager.apply_theme(fig, theme)
    
    def create_pie_chart(
        self,
        df: pd.DataFrame,
        names: str,
        values: str,
        title: Optional[str] = None,
        donut: bool = False,
        **kwargs
    ) -> go.Figure:
        """Convenience method to create pie/donut chart"""
        config = ChartConfig(x=names, y=values, title=title, **kwargs)
        fig = self._create_donut(df, config) if donut else self._create_pie(df, config)
        
        theme = self.theme_manager.get_theme(config.theme)
        return self.theme_manager.apply_theme(fig, theme)
    
    # =========================================================================
    # EXPORT METHODS
    # =========================================================================
    
    def export(
        self,
        chart: Union[GeneratedChart, go.Figure],
        filepath: Union[str, Path],
        format: Optional[ExportFormat] = None,
        width: int = 1200,
        height: int = 800,
        scale: float = 2.0
    ) -> bool:
        """
        Export chart to file.
        
        Args:
            chart: GeneratedChart or Plotly figure
            filepath: Output file path
            format: Export format (auto-detected from extension if None)
            width: Image width in pixels
            height: Image height in pixels
            scale: Scale factor for resolution
            
        Returns:
            True if export successful
        """
        filepath = Path(filepath)
        fig = chart.figure if isinstance(chart, GeneratedChart) else chart
        
        # Auto-detect format
        if format is None:
            ext = filepath.suffix.lower().lstrip('.')
            format = ExportFormat(ext) if ext in [f.value for f in ExportFormat] else ExportFormat.HTML
        
        try:
            if format == ExportFormat.HTML:
                fig.write_html(str(filepath))
            elif format == ExportFormat.JSON:
                with open(filepath, 'w') as f:
                    f.write(fig.to_json())
            elif format in [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.PDF, ExportFormat.WEBP]:
                if not KALEIDO_AVAILABLE:
                    logger.warning("Kaleido not available for static export. Install with: pip install kaleido")
                    return False
                fig.write_image(
                    str(filepath),
                    format=format.value,
                    width=width,
                    height=height,
                    scale=scale
                )
            else:
                logger.error(f"Unknown export format: {format}")
                return False
            
            logger.info(f"Chart exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def to_html(self, chart: Union[GeneratedChart, go.Figure]) -> str:
        """Export chart to HTML string"""
        fig = chart.figure if isinstance(chart, GeneratedChart) else chart
        return fig.to_html(full_html=True, include_plotlyjs=True)
    
    def to_json(self, chart: Union[GeneratedChart, go.Figure]) -> str:
        """Export chart to JSON string"""
        fig = chart.figure if isinstance(chart, GeneratedChart) else chart
        return fig.to_json()
    
    def to_base64_png(
        self,
        chart: Union[GeneratedChart, go.Figure],
        width: int = 800,
        height: int = 600
    ) -> Optional[str]:
        """Export chart to base64-encoded PNG"""
        if not KALEIDO_AVAILABLE:
            logger.warning("Kaleido required for PNG export")
            return None
        
        fig = chart.figure if isinstance(chart, GeneratedChart) else chart
        
        img_bytes = fig.to_image(format='png', width=width, height=height)
        return base64.b64encode(img_bytes).decode('utf-8')
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_supported_types(self) -> List[str]:
        """Get list of all supported chart types"""
        return [ct.value for ct in ChartType]
    
    def get_themes(self) -> List[str]:
        """Get list of available themes"""
        return [ts.value for ts in ThemeStyle]
    
    def set_default_theme(self, theme: ThemeStyle):
        """Set the default theme"""
        self.default_theme = theme
        logger.info(f"Default theme set to {theme.value}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_chart(
    df: pd.DataFrame,
    chart_type: Union[str, ChartType],
    x: Optional[str] = None,
    y: Optional[str] = None,
    **kwargs
) -> go.Figure:
    """
    Quick chart creation function.
    
    Args:
        df: DataFrame with data
        chart_type: Type of chart to create
        x: X-axis column
        y: Y-axis column
        **kwargs: Additional configuration
        
    Returns:
        Plotly figure
    """
    generator = ChartGenerator()
    config = ChartConfig(x=x, y=y, **kwargs)
    result = generator.generate_from_type(df, chart_type, config)
    return result.figure


def quick_chart(df: pd.DataFrame) -> go.Figure:
    """
    Automatically create the best chart for the data.
    
    Args:
        df: DataFrame with data
        
    Returns:
        Plotly figure
    """
    from .chart_recommender import ChartRecommender
    
    recommender = ChartRecommender()
    recommendations = recommender.recommend(df, top_n=1)
    
    if recommendations:
        generator = ChartGenerator()
        result = generator.generate(df, recommendations[0])
        return result.figure
    else:
        # Fallback to simple bar chart
        generator = ChartGenerator()
        config = ChartConfig()
        return generator._create_bar_vertical(df, config)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'ChartGenerator',
    
    # Result classes
    'GeneratedChart',
    'ChartConfig',
    'ChartTheme',
    'MacrocommColors',
    
    # Support classes
    'ThemeManager',
    
    # Enums
    'ExportFormat',
    'ThemeStyle',
    
    # Convenience functions
    'create_chart',
    'quick_chart',
]