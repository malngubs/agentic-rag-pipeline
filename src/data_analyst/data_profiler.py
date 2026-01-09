"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         DATA PROFILER MODULE                                 ║
║              Intelligent Data Analysis & Quality Assessment                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Analyzes DataFrames to understand structure, quality, and characteristics   ║
║  Features: Type detection, quality scoring, statistics, correlations         ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📊 Type Detection    - Auto-detect column types (numeric, categorical, datetime, etc.)
🔍 Quality Analysis  - Missing values, duplicates, outliers, invalid data
📈 Statistics        - Descriptive stats, distributions, percentiles
🔗 Correlations      - Detect relationships between columns
📋 Data Summary      - Human-readable overview for AI explanations

USAGE:
------
    from data_analyst import DataProfiler, FileIngestor
    
    # Extract data first
    ingestor = FileIngestor()
    result = await ingestor.extract("sales.xlsx")
    df = result.get_dataframe()
    
    # Profile the data
    profiler = DataProfiler()
    profile = profiler.profile(df)
    
    # Access profile information
    print(f"Rows: {profile.row_count}")
    print(f"Quality Score: {profile.quality_score}")
    
    for col in profile.columns:
        print(f"{col.name}: {col.dtype} - {col.missing_percent:.1f}% missing")

ARCHITECTURE:
-------------
DataProfiler (main class)
    ├── TypeDetector         - Infer semantic column types
    ├── QualityAnalyzer      - Assess data quality
    ├── StatisticsCalculator - Compute descriptive statistics
    ├── DistributionAnalyzer - Analyze value distributions
    ├── CorrelationAnalyzer  - Find column relationships
    └── SummaryGenerator     - Create human-readable summaries
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Statistical functions
try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not installed - advanced statistics disabled")

# Configure logging
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ColumnType(Enum):
    """
    Semantic types for data columns.
    
    These represent the MEANING of the data, not just the storage type.
    For example, a column stored as int64 might semantically be a "year" or "category".
    """
    # Numeric Types
    NUMERIC_CONTINUOUS = "numeric_continuous"    # Floating point, measurements
    NUMERIC_DISCRETE = "numeric_discrete"        # Integers, counts
    NUMERIC_PERCENTAGE = "numeric_percentage"    # Values 0-100 or 0-1
    NUMERIC_CURRENCY = "numeric_currency"        # Money values
    
    # Categorical Types
    CATEGORICAL = "categorical"                  # General categories
    CATEGORICAL_BINARY = "categorical_binary"    # Yes/No, True/False, 0/1
    CATEGORICAL_ORDINAL = "categorical_ordinal"  # Ordered categories (Low/Med/High)
    
    # Date/Time Types
    DATETIME = "datetime"                        # Full datetime
    DATE = "date"                                # Date only
    TIME = "time"                                # Time only
    YEAR = "year"                                # Year values
    
    # Text Types
    TEXT_SHORT = "text_short"                    # Names, titles (<50 chars avg)
    TEXT_LONG = "text_long"                      # Descriptions, comments
    
    # Identifier Types
    ID_NUMERIC = "id_numeric"                    # Numeric IDs
    ID_STRING = "id_string"                      # String IDs, codes
    
    # Special Types
    EMAIL = "email"                              # Email addresses
    URL = "url"                                  # Web URLs
    PHONE = "phone"                              # Phone numbers
    BOOLEAN = "boolean"                          # True/False
    CONSTANT = "constant"                        # Single value column
    EMPTY = "empty"                              # All null/empty
    UNKNOWN = "unknown"                          # Cannot determine


class QualityLevel(Enum):
    """Quality assessment levels for columns and datasets"""
    EXCELLENT = "excellent"    # 95%+ quality score
    GOOD = "good"              # 80-95% quality score
    FAIR = "fair"              # 60-80% quality score
    POOR = "poor"              # 40-60% quality score
    CRITICAL = "critical"      # <40% quality score


class OutlierMethod(Enum):
    """Methods for detecting outliers"""
    IQR = "iqr"                # Interquartile range method
    ZSCORE = "zscore"          # Z-score method (requires scipy)
    MODIFIED_ZSCORE = "modified_zscore"  # Modified Z-score (MAD-based)


# =============================================================================
# DATA CLASSES - Column Profile
# =============================================================================

@dataclass
class ColumnStatistics:
    """
    Statistical summary for a numeric column.
    
    Contains all common descriptive statistics needed for analysis.
    """
    count: int = 0
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[Any] = None
    q1: Optional[float] = None          # 25th percentile
    q3: Optional[float] = None          # 75th percentile
    iqr: Optional[float] = None         # Interquartile range
    skewness: Optional[float] = None    # Distribution skew
    kurtosis: Optional[float] = None    # Distribution kurtosis
    variance: Optional[float] = None
    sum: Optional[float] = None
    range: Optional[float] = None       # max - min
    cv: Optional[float] = None          # Coefficient of variation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, rounding floats"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, float):
                result[key] = round(value, 4) if value is not None else None
            else:
                result[key] = value
        return result


@dataclass
class ColumnQuality:
    """
    Quality metrics for a single column.
    """
    missing_count: int = 0
    missing_percent: float = 0.0
    duplicate_count: int = 0
    duplicate_percent: float = 0.0
    outlier_count: int = 0
    outlier_percent: float = 0.0
    invalid_count: int = 0              # Values that don't match expected type
    invalid_percent: float = 0.0
    quality_score: float = 100.0        # Overall quality 0-100
    quality_level: QualityLevel = QualityLevel.EXCELLENT
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "missing_count": self.missing_count,
            "missing_percent": round(self.missing_percent, 2),
            "duplicate_count": self.duplicate_count,
            "duplicate_percent": round(self.duplicate_percent, 2),
            "outlier_count": self.outlier_count,
            "outlier_percent": round(self.outlier_percent, 2),
            "invalid_count": self.invalid_count,
            "invalid_percent": round(self.invalid_percent, 2),
            "quality_score": round(self.quality_score, 1),
            "quality_level": self.quality_level.value,
            "issues": self.issues
        }


@dataclass
class ColumnProfile:
    """
    Complete profile for a single column.
    
    Contains type information, statistics, quality metrics, and sample values.
    """
    name: str
    dtype: ColumnType
    pandas_dtype: str                    # Original pandas dtype
    
    # Cardinality
    unique_count: int = 0
    unique_percent: float = 0.0
    is_unique: bool = False              # All values unique (potential ID)
    
    # Statistics (for numeric columns)
    statistics: Optional[ColumnStatistics] = None
    
    # Quality metrics
    quality: ColumnQuality = field(default_factory=ColumnQuality)
    
    # Value distribution
    top_values: List[Tuple[Any, int]] = field(default_factory=list)  # (value, count)
    sample_values: List[Any] = field(default_factory=list)
    
    # For datetime columns
    date_range: Optional[Tuple[datetime, datetime]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "dtype": self.dtype.value,
            "pandas_dtype": self.pandas_dtype,
            "unique_count": self.unique_count,
            "unique_percent": round(self.unique_percent, 2),
            "is_unique": self.is_unique,
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "quality": self.quality.to_dict(),
            "top_values": [{"value": str(v), "count": c} for v, c in self.top_values[:10]],
            "sample_values": [str(v) for v in self.sample_values[:5]],
            "date_range": {
                "min": self.date_range[0].isoformat() if self.date_range else None,
                "max": self.date_range[1].isoformat() if self.date_range else None
            } if self.date_range else None,
            "metadata": self.metadata
        }


# =============================================================================
# DATA CLASSES - Dataset Profile
# =============================================================================

@dataclass
class DatasetQuality:
    """
    Overall quality assessment for the entire dataset.
    """
    row_count: int = 0
    column_count: int = 0
    total_cells: int = 0
    missing_cells: int = 0
    missing_percent: float = 0.0
    duplicate_rows: int = 0
    duplicate_percent: float = 0.0
    complete_rows: int = 0              # Rows with no missing values
    complete_percent: float = 0.0
    quality_score: float = 100.0
    quality_level: QualityLevel = QualityLevel.EXCELLENT
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "total_cells": self.total_cells,
            "missing_cells": self.missing_cells,
            "missing_percent": round(self.missing_percent, 2),
            "duplicate_rows": self.duplicate_rows,
            "duplicate_percent": round(self.duplicate_percent, 2),
            "complete_rows": self.complete_rows,
            "complete_percent": round(self.complete_percent, 2),
            "quality_score": round(self.quality_score, 1),
            "quality_level": self.quality_level.value,
            "issues": self.issues,
            "recommendations": self.recommendations
        }


@dataclass
class CorrelationResult:
    """
    Correlation between two columns.
    """
    column1: str
    column2: str
    correlation: float
    method: str = "pearson"             # pearson, spearman, or cramers_v
    strength: str = "weak"              # weak, moderate, strong, very_strong
    p_value: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "column1": self.column1,
            "column2": self.column2,
            "correlation": round(self.correlation, 4),
            "method": self.method,
            "strength": self.strength,
            "p_value": round(self.p_value, 4) if self.p_value else None
        }


@dataclass
class DataProfile:
    """
    Complete profile of a dataset.
    
    This is the main output of the DataProfiler, containing all analysis results.
    """
    # Basic info
    name: str = "Untitled"
    row_count: int = 0
    column_count: int = 0
    memory_usage_mb: float = 0.0
    
    # Column profiles
    columns: List[ColumnProfile] = field(default_factory=list)
    
    # Column type summary
    type_counts: Dict[str, int] = field(default_factory=dict)
    
    # Quality assessment
    quality: DatasetQuality = field(default_factory=DatasetQuality)
    
    # Correlations
    correlations: List[CorrelationResult] = field(default_factory=list)
    
    # Summary for AI
    summary_text: str = ""
    
    # Profiling metadata
    profiled_at: datetime = field(default_factory=datetime.now)
    profiling_time_seconds: float = 0.0
    
    def get_column(self, name: str) -> Optional[ColumnProfile]:
        """Get column profile by name"""
        for col in self.columns:
            if col.name == name:
                return col
        return None
    
    def get_numeric_columns(self) -> List[ColumnProfile]:
        """Get all numeric columns"""
        numeric_types = {
            ColumnType.NUMERIC_CONTINUOUS,
            ColumnType.NUMERIC_DISCRETE,
            ColumnType.NUMERIC_PERCENTAGE,
            ColumnType.NUMERIC_CURRENCY
        }
        return [c for c in self.columns if c.dtype in numeric_types]
    
    def get_categorical_columns(self) -> List[ColumnProfile]:
        """Get all categorical columns"""
        cat_types = {
            ColumnType.CATEGORICAL,
            ColumnType.CATEGORICAL_BINARY,
            ColumnType.CATEGORICAL_ORDINAL
        }
        return [c for c in self.columns if c.dtype in cat_types]
    
    def get_datetime_columns(self) -> List[ColumnProfile]:
        """Get all datetime columns"""
        dt_types = {
            ColumnType.DATETIME,
            ColumnType.DATE,
            ColumnType.TIME,
            ColumnType.YEAR
        }
        return [c for c in self.columns if c.dtype in dt_types]
    
    def get_columns_by_quality(self, level: QualityLevel) -> List[ColumnProfile]:
        """Get columns matching a quality level"""
        return [c for c in self.columns if c.quality.quality_level == level]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "columns": [c.to_dict() for c in self.columns],
            "type_counts": self.type_counts,
            "quality": self.quality.to_dict(),
            "correlations": [c.to_dict() for c in self.correlations],
            "summary_text": self.summary_text,
            "profiled_at": self.profiled_at.isoformat(),
            "profiling_time_seconds": round(self.profiling_time_seconds, 3)
        }


# =============================================================================
# TYPE DETECTOR
# =============================================================================

class TypeDetector:
    """
    Detects semantic types for DataFrame columns.
    
    Goes beyond pandas dtypes to understand the MEANING of the data.
    """
    
    # Regex patterns for special types
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://[^\s]+$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]{7,20}$')
    
    # Keywords for ordinal detection
    ORDINAL_KEYWORDS = {
        'low', 'medium', 'high',
        'small', 'large',
        'poor', 'fair', 'good', 'excellent',
        'never', 'rarely', 'sometimes', 'often', 'always',
        'strongly disagree', 'disagree', 'neutral', 'agree', 'strongly agree',
        '1st', '2nd', '3rd', 'first', 'second', 'third'
    }
    
    def detect(self, series: pd.Series, column_name: str) -> ColumnType:
        """
        Detect the semantic type of a pandas Series.
        
        Args:
            series: The data to analyze
            column_name: Name of the column (used for hints)
            
        Returns:
            Detected ColumnType
        """
        # Handle empty/all-null columns
        if series.isna().all():
            return ColumnType.EMPTY
        
        # Get non-null values for analysis
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return ColumnType.EMPTY
        
        # Check for constant column
        if non_null.nunique() == 1:
            return ColumnType.CONSTANT
        
        # Get pandas dtype
        dtype = series.dtype
        
        # Datetime detection
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return self._classify_datetime(series, column_name)
        
        # Boolean detection
        if pd.api.types.is_bool_dtype(dtype):
            return ColumnType.BOOLEAN
        
        # Numeric detection
        if pd.api.types.is_numeric_dtype(dtype):
            return self._classify_numeric(series, column_name)
        
        # Object/String detection
        if dtype == 'object' or pd.api.types.is_string_dtype(dtype):
            return self._classify_string(series, column_name)
        
        return ColumnType.UNKNOWN
    
    def _classify_numeric(self, series: pd.Series, column_name: str) -> ColumnType:
        """Classify numeric columns"""
        non_null = series.dropna()
        col_lower = column_name.lower()
        
        # Check for year
        if 'year' in col_lower:
            if non_null.min() >= 1900 and non_null.max() <= 2100:
                return ColumnType.YEAR
        
        # Check for percentage
        if 'percent' in col_lower or 'pct' in col_lower or '%' in column_name:
            return ColumnType.NUMERIC_PERCENTAGE
        if non_null.min() >= 0 and non_null.max() <= 100:
            if non_null.max() <= 1 and 'rate' in col_lower:
                return ColumnType.NUMERIC_PERCENTAGE
        
        # Check for currency
        currency_keywords = ['price', 'cost', 'amount', 'revenue', 'salary', 
                           'income', 'profit', 'expense', 'fee', 'total', 'sum']
        if any(kw in col_lower for kw in currency_keywords):
            return ColumnType.NUMERIC_CURRENCY
        
        # Check for ID
        id_keywords = ['id', 'code', 'key', 'number', 'num', 'no']
        unique_ratio = non_null.nunique() / len(non_null)
        if any(col_lower.endswith(kw) or col_lower.startswith(kw) for kw in id_keywords):
            if unique_ratio > 0.9:  # Mostly unique
                return ColumnType.ID_NUMERIC
        
        # Check discrete vs continuous
        if pd.api.types.is_integer_dtype(series.dtype):
            if non_null.nunique() < 20:  # Few unique values
                return ColumnType.NUMERIC_DISCRETE
            return ColumnType.NUMERIC_DISCRETE
        
        return ColumnType.NUMERIC_CONTINUOUS
    
    def _classify_string(self, series: pd.Series, column_name: str) -> ColumnType:
        """Classify string/object columns"""
        non_null = series.dropna().astype(str)
        col_lower = column_name.lower()
        
        if len(non_null) == 0:
            return ColumnType.EMPTY
        
        # Sample for pattern detection (max 1000)
        sample = non_null.head(1000)
        
        # Check for boolean-like
        unique_vals = set(non_null.str.lower().unique())
        bool_pairs = [
            {'yes', 'no'}, {'y', 'n'}, {'true', 'false'}, {'t', 'f'},
            {'1', '0'}, {'on', 'off'}, {'active', 'inactive'}
        ]
        for pair in bool_pairs:
            if unique_vals.issubset(pair) or unique_vals == pair:
                return ColumnType.CATEGORICAL_BINARY
        
        # Check for email
        if 'email' in col_lower or 'mail' in col_lower:
            if sample.str.match(self.EMAIL_PATTERN).mean() > 0.8:
                return ColumnType.EMAIL
        
        # Check for URL
        if 'url' in col_lower or 'link' in col_lower or 'website' in col_lower:
            if sample.str.match(self.URL_PATTERN).mean() > 0.8:
                return ColumnType.URL
        
        # Check for phone
        if 'phone' in col_lower or 'tel' in col_lower or 'mobile' in col_lower:
            if sample.str.match(self.PHONE_PATTERN).mean() > 0.5:
                return ColumnType.PHONE
        
        # Check for datetime (stored as string)
        try:
            pd.to_datetime(sample.head(100), errors='raise')
            return ColumnType.DATETIME
        except:
            pass
        
        # Check for ID
        id_keywords = ['id', 'code', 'key', 'sku', 'uuid']
        unique_ratio = non_null.nunique() / len(non_null)
        if any(col_lower.endswith(kw) or col_lower.startswith(kw) for kw in id_keywords):
            if unique_ratio > 0.9:
                return ColumnType.ID_STRING
        
        # Check for ordinal
        lower_unique = set(v.lower() for v in non_null.unique())
        if lower_unique.intersection(self.ORDINAL_KEYWORDS):
            return ColumnType.CATEGORICAL_ORDINAL
        
        # Check text length for short vs long
        avg_length = non_null.str.len().mean()
        if avg_length > 100:
            return ColumnType.TEXT_LONG
        elif avg_length > 50:
            return ColumnType.TEXT_SHORT
        
        # Default to categorical
        unique_count = non_null.nunique()
        if unique_count <= 50 or unique_count / len(non_null) < 0.5:
            return ColumnType.CATEGORICAL
        
        return ColumnType.TEXT_SHORT
    
    def _classify_datetime(self, series: pd.Series, column_name: str) -> ColumnType:
        """Classify datetime columns"""
        non_null = series.dropna()
        col_lower = column_name.lower()
        
        # Check if only dates (no time component)
        if hasattr(non_null.dt, 'time'):
            times = non_null.dt.time
            if (times == pd.Timestamp('00:00:00').time()).all():
                return ColumnType.DATE
        
        # Check if only time
        if 'time' in col_lower and 'date' not in col_lower:
            return ColumnType.TIME
        
        return ColumnType.DATETIME


# =============================================================================
# QUALITY ANALYZER
# =============================================================================

class QualityAnalyzer:
    """
    Analyzes data quality for columns and datasets.
    """
    
    def __init__(self, outlier_method: OutlierMethod = OutlierMethod.IQR):
        """
        Initialize quality analyzer.
        
        Args:
            outlier_method: Method to use for outlier detection
        """
        self.outlier_method = outlier_method
    
    def analyze_column(
        self, 
        series: pd.Series, 
        column_type: ColumnType
    ) -> ColumnQuality:
        """
        Analyze quality of a single column.
        
        Args:
            series: Column data
            column_type: Detected column type
            
        Returns:
            ColumnQuality with metrics
        """
        quality = ColumnQuality()
        total_count = len(series)
        
        if total_count == 0:
            return quality
        
        # Missing values
        quality.missing_count = series.isna().sum()
        quality.missing_percent = (quality.missing_count / total_count) * 100
        
        # Duplicates
        quality.duplicate_count = series.duplicated().sum()
        quality.duplicate_percent = (quality.duplicate_count / total_count) * 100
        
        # Outliers (for numeric columns)
        if column_type in {ColumnType.NUMERIC_CONTINUOUS, ColumnType.NUMERIC_DISCRETE,
                          ColumnType.NUMERIC_CURRENCY, ColumnType.NUMERIC_PERCENTAGE}:
            outliers = self._detect_outliers(series)
            quality.outlier_count = outliers.sum()
            quality.outlier_percent = (quality.outlier_count / total_count) * 100
        
        # Calculate quality score
        quality.quality_score = self._calculate_quality_score(quality, column_type)
        quality.quality_level = self._score_to_level(quality.quality_score)
        
        # Generate issues
        quality.issues = self._generate_issues(quality, column_type)
        
        return quality
    
    def analyze_dataset(self, df: pd.DataFrame) -> DatasetQuality:
        """
        Analyze overall dataset quality.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            DatasetQuality with metrics
        """
        quality = DatasetQuality()
        
        quality.row_count = len(df)
        quality.column_count = len(df.columns)
        quality.total_cells = quality.row_count * quality.column_count
        
        if quality.total_cells == 0:
            return quality
        
        # Missing cells
        quality.missing_cells = df.isna().sum().sum()
        quality.missing_percent = (quality.missing_cells / quality.total_cells) * 100
        
        # Duplicate rows
        quality.duplicate_rows = df.duplicated().sum()
        quality.duplicate_percent = (quality.duplicate_rows / quality.row_count) * 100
        
        # Complete rows (no missing values)
        quality.complete_rows = len(df.dropna())
        quality.complete_percent = (quality.complete_rows / quality.row_count) * 100
        
        # Overall quality score
        quality.quality_score = self._calculate_dataset_quality_score(quality)
        quality.quality_level = self._score_to_level(quality.quality_score)
        
        # Generate issues and recommendations
        quality.issues = self._generate_dataset_issues(quality)
        quality.recommendations = self._generate_recommendations(quality, df)
        
        return quality
    
    def _detect_outliers(self, series: pd.Series) -> pd.Series:
        """Detect outliers using configured method"""
        non_null = series.dropna()
        
        if len(non_null) < 10:
            return pd.Series([False] * len(series), index=series.index)
        
        if self.outlier_method == OutlierMethod.IQR:
            q1 = non_null.quantile(0.25)
            q3 = non_null.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            return (series < lower) | (series > upper)
        
        elif self.outlier_method == OutlierMethod.ZSCORE and SCIPY_AVAILABLE:
            z_scores = np.abs(scipy_stats.zscore(non_null, nan_policy='omit'))
            outlier_mask = pd.Series([False] * len(series), index=series.index)
            outlier_mask.loc[non_null.index] = z_scores > 3
            return outlier_mask
        
        elif self.outlier_method == OutlierMethod.MODIFIED_ZSCORE:
            median = non_null.median()
            mad = np.abs(non_null - median).median()
            if mad == 0:
                return pd.Series([False] * len(series), index=series.index)
            modified_z = 0.6745 * (series - median) / mad
            return np.abs(modified_z) > 3.5
        
        return pd.Series([False] * len(series), index=series.index)
    
    def _calculate_quality_score(
        self, 
        quality: ColumnQuality, 
        column_type: ColumnType
    ) -> float:
        """Calculate overall quality score 0-100"""
        score = 100.0
        
        # Penalize missing values (up to -40 points)
        score -= min(40, quality.missing_percent * 0.8)
        
        # Penalize outliers for numeric columns (up to -20 points)
        if column_type in {ColumnType.NUMERIC_CONTINUOUS, ColumnType.NUMERIC_DISCRETE}:
            score -= min(20, quality.outlier_percent * 0.4)
        
        # Penalize high duplicate rate (unless it's categorical)
        if column_type not in {ColumnType.CATEGORICAL, ColumnType.CATEGORICAL_BINARY,
                               ColumnType.CATEGORICAL_ORDINAL, ColumnType.BOOLEAN}:
            score -= min(20, quality.duplicate_percent * 0.2)
        
        return max(0, score)
    
    def _calculate_dataset_quality_score(self, quality: DatasetQuality) -> float:
        """Calculate overall dataset quality score"""
        score = 100.0
        
        # Missing data penalty (up to -40)
        score -= min(40, quality.missing_percent * 0.8)
        
        # Duplicate rows penalty (up to -20)
        score -= min(20, quality.duplicate_percent * 0.5)
        
        # Bonus for complete rows
        if quality.complete_percent > 90:
            score += 5
        
        return max(0, min(100, score))
    
    def _score_to_level(self, score: float) -> QualityLevel:
        """Convert numeric score to quality level"""
        if score >= 95:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.FAIR
        elif score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _generate_issues(
        self, 
        quality: ColumnQuality, 
        column_type: ColumnType
    ) -> List[str]:
        """Generate list of quality issues"""
        issues = []
        
        if quality.missing_percent > 50:
            issues.append(f"Critical: {quality.missing_percent:.1f}% missing values")
        elif quality.missing_percent > 20:
            issues.append(f"Warning: {quality.missing_percent:.1f}% missing values")
        elif quality.missing_percent > 5:
            issues.append(f"Note: {quality.missing_percent:.1f}% missing values")
        
        if quality.outlier_percent > 10:
            issues.append(f"High outlier rate: {quality.outlier_percent:.1f}%")
        elif quality.outlier_percent > 5:
            issues.append(f"Moderate outliers: {quality.outlier_percent:.1f}%")
        
        return issues
    
    def _generate_dataset_issues(self, quality: DatasetQuality) -> List[str]:
        """Generate list of dataset-level issues"""
        issues = []
        
        if quality.missing_percent > 30:
            issues.append(f"High missing data rate: {quality.missing_percent:.1f}%")
        
        if quality.duplicate_percent > 10:
            issues.append(f"Significant duplicate rows: {quality.duplicate_percent:.1f}%")
        
        if quality.complete_percent < 50:
            issues.append(f"Only {quality.complete_percent:.1f}% of rows are complete")
        
        return issues
    
    def _generate_recommendations(
        self, 
        quality: DatasetQuality,
        df: pd.DataFrame
    ) -> List[str]:
        """Generate recommendations for data improvement"""
        recommendations = []
        
        if quality.missing_percent > 20:
            recommendations.append("Consider imputing missing values or filtering incomplete rows")
        
        if quality.duplicate_percent > 5:
            recommendations.append("Review and potentially remove duplicate rows")
        
        if quality.row_count < 100:
            recommendations.append("Small dataset - statistical analysis may be limited")
        
        if quality.column_count > 50:
            recommendations.append("Many columns - consider feature selection")
        
        return recommendations


# =============================================================================
# STATISTICS CALCULATOR
# =============================================================================

class StatisticsCalculator:
    """
    Calculates descriptive statistics for numeric columns.
    """
    
    def calculate(self, series: pd.Series) -> Optional[ColumnStatistics]:
        """
        Calculate all statistics for a numeric series.
        
        Args:
            series: Numeric pandas Series
            
        Returns:
            ColumnStatistics or None if not calculable
        """
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return None
        
        if not pd.api.types.is_numeric_dtype(non_null):
            try:
                non_null = pd.to_numeric(non_null, errors='coerce').dropna()
                if len(non_null) == 0:
                    return None
            except:
                return None
        
        stats = ColumnStatistics()
        
        # Basic stats
        stats.count = len(non_null)
        stats.mean = float(non_null.mean())
        stats.std = float(non_null.std()) if len(non_null) > 1 else 0.0
        stats.min = float(non_null.min())
        stats.max = float(non_null.max())
        stats.median = float(non_null.median())
        stats.sum = float(non_null.sum())
        stats.variance = float(non_null.var()) if len(non_null) > 1 else 0.0
        stats.range = stats.max - stats.min
        
        # Mode (most common value)
        mode_result = non_null.mode()
        stats.mode = float(mode_result.iloc[0]) if len(mode_result) > 0 else None
        
        # Quartiles
        stats.q1 = float(non_null.quantile(0.25))
        stats.q3 = float(non_null.quantile(0.75))
        stats.iqr = stats.q3 - stats.q1
        
        # Coefficient of variation
        if stats.mean != 0:
            stats.cv = (stats.std / abs(stats.mean)) * 100
        
        # Distribution shape (requires scipy)
        if SCIPY_AVAILABLE and len(non_null) >= 8:
            try:
                stats.skewness = float(scipy_stats.skew(non_null))
                stats.kurtosis = float(scipy_stats.kurtosis(non_null))
            except:
                pass
        
        return stats


# =============================================================================
# CORRELATION ANALYZER
# =============================================================================

class CorrelationAnalyzer:
    """
    Analyzes correlations between columns.
    """
    
    def analyze(
        self, 
        df: pd.DataFrame,
        numeric_columns: List[str],
        threshold: float = 0.5
    ) -> List[CorrelationResult]:
        """
        Find significant correlations between numeric columns.
        
        Args:
            df: DataFrame to analyze
            numeric_columns: List of numeric column names
            threshold: Minimum absolute correlation to include
            
        Returns:
            List of CorrelationResult for significant correlations
        """
        correlations = []
        
        if len(numeric_columns) < 2:
            return correlations
        
        # Calculate correlation matrix
        try:
            corr_matrix = df[numeric_columns].corr(method='pearson')
        except:
            return correlations
        
        # Extract significant correlations
        for i, col1 in enumerate(numeric_columns):
            for col2 in numeric_columns[i+1:]:
                corr_value = corr_matrix.loc[col1, col2]
                
                if pd.isna(corr_value):
                    continue
                
                if abs(corr_value) >= threshold:
                    # Calculate p-value if scipy available
                    p_value = None
                    if SCIPY_AVAILABLE:
                        try:
                            _, p_value = scipy_stats.pearsonr(
                                df[col1].dropna(),
                                df[col2].dropna()
                            )
                        except:
                            pass
                    
                    correlations.append(CorrelationResult(
                        column1=col1,
                        column2=col2,
                        correlation=float(corr_value),
                        method="pearson",
                        strength=self._correlation_strength(corr_value),
                        p_value=float(p_value) if p_value else None
                    ))
        
        # Sort by absolute correlation (strongest first)
        correlations.sort(key=lambda x: abs(x.correlation), reverse=True)
        
        return correlations
    
    def _correlation_strength(self, corr: float) -> str:
        """Classify correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return "very_strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        else:
            return "weak"


# =============================================================================
# SUMMARY GENERATOR
# =============================================================================

class SummaryGenerator:
    """
    Generates human-readable summaries for AI explanations.
    """
    
    def generate(self, profile: DataProfile) -> str:
        """
        Generate a natural language summary of the data profile.
        
        Args:
            profile: Complete data profile
            
        Returns:
            Human-readable summary string
        """
        lines = []
        
        # Dataset overview
        lines.append(f"📊 DATASET OVERVIEW: {profile.name}")
        lines.append(f"   • {profile.row_count:,} rows × {profile.column_count} columns")
        lines.append(f"   • Memory: {profile.memory_usage_mb:.1f} MB")
        lines.append(f"   • Quality Score: {profile.quality.quality_score:.0f}/100 ({profile.quality.quality_level.value})")
        lines.append("")
        
        # Column type breakdown
        lines.append("📋 COLUMN TYPES:")
        for dtype, count in sorted(profile.type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"   • {dtype}: {count} columns")
        lines.append("")
        
        # Quality issues
        if profile.quality.issues:
            lines.append("⚠️ QUALITY ISSUES:")
            for issue in profile.quality.issues:
                lines.append(f"   • {issue}")
            lines.append("")
        
        # Top correlations
        if profile.correlations:
            lines.append("🔗 KEY CORRELATIONS:")
            for corr in profile.correlations[:5]:
                direction = "positive" if corr.correlation > 0 else "negative"
                lines.append(f"   • {corr.column1} ↔ {corr.column2}: {corr.correlation:.2f} ({direction}, {corr.strength})")
            lines.append("")
        
        # Recommendations
        if profile.quality.recommendations:
            lines.append("💡 RECOMMENDATIONS:")
            for rec in profile.quality.recommendations:
                lines.append(f"   • {rec}")
            lines.append("")
        
        # Column highlights
        numeric_cols = profile.get_numeric_columns()
        if numeric_cols:
            lines.append("📈 NUMERIC COLUMN HIGHLIGHTS:")
            for col in numeric_cols[:5]:
                if col.statistics:
                    lines.append(f"   • {col.name}: range [{col.statistics.min:.2f} - {col.statistics.max:.2f}], mean={col.statistics.mean:.2f}")
        
        return "\n".join(lines)


# =============================================================================
# MAIN DATA PROFILER CLASS
# =============================================================================

class DataProfiler:
    """
    Main class for profiling DataFrames.
    
    Combines all analysis components to generate comprehensive data profiles.
    
    Usage:
        profiler = DataProfiler()
        profile = profiler.profile(df, name="Sales Data")
        
        # Access results
        print(profile.summary_text)
        print(f"Quality: {profile.quality.quality_score}")
        
        for col in profile.columns:
            print(f"{col.name}: {col.dtype.value}")
    """
    
    def __init__(
        self,
        outlier_method: OutlierMethod = OutlierMethod.IQR,
        correlation_threshold: float = 0.5,
        max_categories_for_frequency: int = 50
    ):
        """
        Initialize the DataProfiler.
        
        Args:
            outlier_method: Method for detecting outliers
            correlation_threshold: Minimum correlation to report
            max_categories_for_frequency: Max categories to show in top_values
        """
        self.type_detector = TypeDetector()
        self.quality_analyzer = QualityAnalyzer(outlier_method)
        self.stats_calculator = StatisticsCalculator()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.summary_generator = SummaryGenerator()
        
        self.correlation_threshold = correlation_threshold
        self.max_categories = max_categories_for_frequency
    
    def profile(
        self, 
        df: pd.DataFrame,
        name: str = "Untitled"
    ) -> DataProfile:
        """
        Generate complete profile for a DataFrame.
        
        Args:
            df: DataFrame to profile
            name: Name for the dataset
            
        Returns:
            DataProfile with all analysis results
        """
        import time
        start_time = time.time()
        
        # Initialize profile
        profile = DataProfile(name=name)
        profile.row_count = len(df)
        profile.column_count = len(df.columns)
        profile.memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Profile each column
        type_counts: Dict[str, int] = {}
        numeric_columns: List[str] = []
        
        for col_name in df.columns:
            col_profile = self._profile_column(df[col_name], col_name)
            profile.columns.append(col_profile)
            
            # Track type counts
            dtype_str = col_profile.dtype.value
            type_counts[dtype_str] = type_counts.get(dtype_str, 0) + 1
            
            # Track numeric columns for correlation
            if col_profile.dtype in {
                ColumnType.NUMERIC_CONTINUOUS, ColumnType.NUMERIC_DISCRETE,
                ColumnType.NUMERIC_CURRENCY, ColumnType.NUMERIC_PERCENTAGE
            }:
                numeric_columns.append(col_name)
        
        profile.type_counts = type_counts
        
        # Analyze dataset quality
        profile.quality = self.quality_analyzer.analyze_dataset(df)
        
        # Calculate correlations
        if len(numeric_columns) >= 2:
            profile.correlations = self.correlation_analyzer.analyze(
                df, numeric_columns, self.correlation_threshold
            )
        
        # Generate summary
        profile.summary_text = self.summary_generator.generate(profile)
        
        # Record timing
        profile.profiling_time_seconds = time.time() - start_time
        profile.profiled_at = datetime.now()
        
        return profile
    
    def _profile_column(self, series: pd.Series, col_name: str) -> ColumnProfile:
        """Profile a single column"""
        
        # Detect type
        col_type = self.type_detector.detect(series, col_name)
        
        # Create profile
        profile = ColumnProfile(
            name=col_name,
            dtype=col_type,
            pandas_dtype=str(series.dtype)
        )
        
        # Cardinality
        profile.unique_count = series.nunique()
        profile.unique_percent = (profile.unique_count / len(series) * 100) if len(series) > 0 else 0
        profile.is_unique = profile.unique_count == len(series)
        
        # Quality analysis
        profile.quality = self.quality_analyzer.analyze_column(series, col_type)
        
        # Statistics (for numeric columns)
        if col_type in {ColumnType.NUMERIC_CONTINUOUS, ColumnType.NUMERIC_DISCRETE,
                        ColumnType.NUMERIC_CURRENCY, ColumnType.NUMERIC_PERCENTAGE}:
            profile.statistics = self.stats_calculator.calculate(series)
        
        # Top values (frequency)
        try:
            value_counts = series.value_counts().head(self.max_categories)
            profile.top_values = list(value_counts.items())
        except:
            pass
        
        # Sample values
        non_null = series.dropna()
        if len(non_null) > 0:
            profile.sample_values = non_null.head(5).tolist()
        
        # Date range (for datetime columns)
        if col_type in {ColumnType.DATETIME, ColumnType.DATE}:
            try:
                if pd.api.types.is_datetime64_any_dtype(series):
                    profile.date_range = (series.min(), series.max())
            except:
                pass
        
        return profile
    
    def quick_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a quick, lightweight profile.
        
        Useful for large datasets where full profiling would be slow.
        
        Args:
            df: DataFrame to profile
            
        Returns:
            Dictionary with basic profile information
        """
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
            "missing_percent": (df.isna().sum().sum() / df.size * 100) if df.size > 0 else 0,
            "duplicate_rows": df.duplicated().sum(),
            "columns": {
                col: {
                    "dtype": str(df[col].dtype),
                    "missing": df[col].isna().sum(),
                    "unique": df[col].nunique()
                }
                for col in df.columns
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def profile_dataframe(
    df: pd.DataFrame,
    name: str = "Untitled"
) -> DataProfile:
    """
    Convenience function to profile a DataFrame.
    
    Args:
        df: DataFrame to profile
        name: Name for the dataset
        
    Returns:
        DataProfile
    
    Example:
        profile = profile_dataframe(df, "Sales Data")
        print(profile.summary_text)
    """
    profiler = DataProfiler()
    return profiler.profile(df, name)


def quick_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Quick profile for large datasets.
    
    Args:
        df: DataFrame to profile
        
    Returns:
        Dictionary with basic stats
    """
    profiler = DataProfiler()
    return profiler.quick_profile(df)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'DataProfiler',
    
    # Data classes
    'DataProfile',
    'ColumnProfile',
    'ColumnStatistics',
    'ColumnQuality',
    'DatasetQuality',
    'CorrelationResult',
    
    # Enums
    'ColumnType',
    'QualityLevel',
    'OutlierMethod',
    
    # Component classes
    'TypeDetector',
    'QualityAnalyzer',
    'StatisticsCalculator',
    'CorrelationAnalyzer',
    'SummaryGenerator',
    
    # Convenience functions
    'profile_dataframe',
    'quick_profile',
]