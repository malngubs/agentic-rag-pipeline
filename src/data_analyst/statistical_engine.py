"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       STATISTICAL ENGINE MODULE                              ║
║              Advanced Analytics for BI Platform                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Provides: Forecasting, Time Series, Regression, Hypothesis Testing         ║
║  Powers: Predictive insights, trend analysis, statistical validation        ║
╚══════════════════════════════════════════════════════════════════════════════╝

CAPABILITIES:
-------------
📈 Time Series Analysis  - Trend detection, seasonality, decomposition
🔮 Forecasting          - Multiple methods (Moving Avg, Exponential, Holt-Winters)
📊 Regression           - Linear, polynomial, multiple regression
🧪 Hypothesis Testing   - t-test, chi-square, ANOVA, correlation tests
📉 Trend Analysis       - Growth rates, moving averages, change detection

USAGE:
------
    from data_analyst import StatisticalEngine
    
    engine = StatisticalEngine()
    
    # Forecast future values
    forecast = engine.forecast(df, date_col='Date', value_col='Sales', periods=12)
    print(f"Next 12 periods: {forecast.predictions}")
    
    # Analyze time series
    ts_result = engine.analyze_time_series(df, date_col='Date', value_col='Revenue')
    print(f"Trend: {ts_result.trend_direction}")
    print(f"Seasonality: {ts_result.has_seasonality}")
    
    # Run regression
    reg_result = engine.regression(df, target='Sales', features=['Marketing', 'Price'])
    print(f"R²: {reg_result.r_squared}")
    
    # Hypothesis test
    test_result = engine.t_test(group1_data, group2_data)
    print(f"Significant difference: {test_result.is_significant}")

ARCHITECTURE:
-------------
StatisticalEngine (main class)
    ├── TimeSeriesAnalyzer   - Decomposition, trend, seasonality
    ├── ForecastEngine       - Multiple forecasting methods
    ├── RegressionAnalyzer   - Linear and polynomial regression
    ├── HypothesisTester     - Statistical significance tests
    └── TrendAnalyzer        - Growth rates, change points
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Statistical libraries
try:
    from scipy import stats as scipy_stats
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not installed - statistical tests disabled")

# Sklearn for regression (optional but commonly available)
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("sklearn not installed - advanced regression disabled")

# Statsmodels for advanced time series (optional)
try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.stattools import adfuller, acf, pacf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.debug("statsmodels not installed - advanced time series disabled")

# Configure logging
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


# =============================================================================
# ENUMERATIONS
# =============================================================================

class TrendDirection(Enum):
    """Direction of trend in time series"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class ForecastMethod(Enum):
    """Available forecasting methods"""
    SIMPLE_MOVING_AVERAGE = "simple_moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    DOUBLE_EXPONENTIAL = "double_exponential"
    HOLT_WINTERS = "holt_winters"
    LINEAR_TREND = "linear_trend"
    AUTO = "auto"  # Automatically select best method


class SeasonalityType(Enum):
    """Types of seasonality"""
    NONE = "none"
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"


class RegressionType(Enum):
    """Types of regression analysis"""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    MULTIPLE = "multiple"


class TestType(Enum):
    """Types of hypothesis tests"""
    T_TEST_INDEPENDENT = "t_test_independent"
    T_TEST_PAIRED = "t_test_paired"
    ONE_SAMPLE_T = "one_sample_t"
    ANOVA = "anova"
    CHI_SQUARE = "chi_square"
    CORRELATION = "correlation"
    NORMALITY = "normality"
    MANN_WHITNEY = "mann_whitney"


# =============================================================================
# DATA CLASSES - Time Series Results
# =============================================================================

@dataclass
class TrendResult:
    """
    Results of trend analysis.
    """
    direction: TrendDirection
    slope: float                          # Rate of change per period
    slope_percent: float                  # Percentage change per period
    r_squared: float                      # How well trend fits data
    start_value: float
    end_value: float
    total_change: float
    total_change_percent: float
    is_significant: bool                  # Statistically significant trend
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "slope": round(self.slope, 4),
            "slope_percent": round(self.slope_percent, 2),
            "r_squared": round(self.r_squared, 4),
            "start_value": round(self.start_value, 2),
            "end_value": round(self.end_value, 2),
            "total_change": round(self.total_change, 2),
            "total_change_percent": round(self.total_change_percent, 2),
            "is_significant": self.is_significant,
            "p_value": round(self.p_value, 4) if self.p_value else None
        }


@dataclass
class SeasonalityResult:
    """
    Results of seasonality detection.
    """
    has_seasonality: bool
    seasonality_type: SeasonalityType
    period: Optional[int] = None          # Length of seasonal cycle
    strength: float = 0.0                 # 0-1, how strong is seasonality
    seasonal_peaks: List[int] = field(default_factory=list)
    seasonal_troughs: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_seasonality": self.has_seasonality,
            "seasonality_type": self.seasonality_type.value,
            "period": self.period,
            "strength": round(self.strength, 3),
            "seasonal_peaks": self.seasonal_peaks,
            "seasonal_troughs": self.seasonal_troughs
        }


@dataclass
class TimeSeriesAnalysis:
    """
    Complete time series analysis results.
    """
    # Basic stats
    length: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    frequency: Optional[str] = None       # Daily, Weekly, Monthly, etc.
    
    # Components
    trend: Optional[TrendResult] = None
    seasonality: Optional[SeasonalityResult] = None
    
    # Statistics
    mean: float = 0.0
    std: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    volatility: float = 0.0               # Coefficient of variation
    
    # Stationarity
    is_stationary: bool = False
    adf_statistic: Optional[float] = None
    adf_p_value: Optional[float] = None
    
    # Change detection
    change_points: List[int] = field(default_factory=list)
    anomalies: List[int] = field(default_factory=list)
    
    # Decomposed components (if available)
    trend_component: Optional[pd.Series] = None
    seasonal_component: Optional[pd.Series] = None
    residual_component: Optional[pd.Series] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self.length,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "frequency": self.frequency,
            "trend": self.trend.to_dict() if self.trend else None,
            "seasonality": self.seasonality.to_dict() if self.seasonality else None,
            "mean": round(self.mean, 2),
            "std": round(self.std, 2),
            "min_value": round(self.min_value, 2),
            "max_value": round(self.max_value, 2),
            "volatility": round(self.volatility, 2),
            "is_stationary": self.is_stationary,
            "change_points": self.change_points[:10],  # Limit for JSON
            "anomalies": self.anomalies[:10]
        }


# =============================================================================
# DATA CLASSES - Forecast Results
# =============================================================================

@dataclass
class ForecastResult:
    """
    Results of forecasting operation.
    """
    method: ForecastMethod
    periods: int
    predictions: List[float]
    prediction_dates: Optional[List[datetime]] = None
    
    # Confidence intervals
    lower_bound: Optional[List[float]] = None
    upper_bound: Optional[List[float]] = None
    confidence_level: float = 0.95
    
    # Model metrics (on training data)
    mape: Optional[float] = None          # Mean Absolute Percentage Error
    rmse: Optional[float] = None          # Root Mean Square Error
    mae: Optional[float] = None           # Mean Absolute Error
    
    # Metadata
    model_params: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "periods": self.periods,
            "predictions": [round(p, 2) for p in self.predictions],
            "prediction_dates": [d.isoformat() for d in self.prediction_dates] if self.prediction_dates else None,
            "lower_bound": [round(b, 2) for b in self.lower_bound] if self.lower_bound else None,
            "upper_bound": [round(b, 2) for b in self.upper_bound] if self.upper_bound else None,
            "confidence_level": self.confidence_level,
            "mape": round(self.mape, 2) if self.mape else None,
            "rmse": round(self.rmse, 2) if self.rmse else None,
            "mae": round(self.mae, 2) if self.mae else None,
            "model_params": self.model_params,
            "warnings": self.warnings
        }


# =============================================================================
# DATA CLASSES - Regression Results
# =============================================================================

@dataclass
class RegressionResult:
    """
    Results of regression analysis.
    """
    regression_type: RegressionType
    target_column: str
    feature_columns: List[str]
    
    # Model performance
    r_squared: float
    adjusted_r_squared: Optional[float] = None
    rmse: float = 0.0
    mae: float = 0.0
    
    # Coefficients
    intercept: float = 0.0
    coefficients: Dict[str, float] = field(default_factory=dict)
    
    # Statistical significance
    p_values: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # Predictions
    predictions: Optional[pd.Series] = None
    residuals: Optional[pd.Series] = None
    
    # Model quality
    is_significant: bool = False
    f_statistic: Optional[float] = None
    f_p_value: Optional[float] = None
    
    # Interpretation
    interpretation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "regression_type": self.regression_type.value,
            "target_column": self.target_column,
            "feature_columns": self.feature_columns,
            "r_squared": round(self.r_squared, 4),
            "adjusted_r_squared": round(self.adjusted_r_squared, 4) if self.adjusted_r_squared else None,
            "rmse": round(self.rmse, 4),
            "mae": round(self.mae, 4),
            "intercept": round(self.intercept, 4),
            "coefficients": {k: round(v, 4) for k, v in self.coefficients.items()},
            "is_significant": self.is_significant,
            "interpretation": self.interpretation
        }


# =============================================================================
# DATA CLASSES - Hypothesis Test Results
# =============================================================================

@dataclass
class HypothesisTestResult:
    """
    Results of a hypothesis test.
    """
    test_type: TestType
    test_name: str
    
    # Core results
    statistic: float
    p_value: float
    is_significant: bool
    
    # Configuration
    alpha: float = 0.05                   # Significance level
    alternative: str = "two-sided"        # two-sided, greater, less
    
    # Effect size
    effect_size: Optional[float] = None
    effect_interpretation: str = ""       # small, medium, large
    
    # Confidence interval
    confidence_interval: Optional[Tuple[float, float]] = None
    
    # Group statistics
    group_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Interpretation
    interpretation: str = ""
    conclusion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type.value,
            "test_name": self.test_name,
            "statistic": round(self.statistic, 4),
            "p_value": round(self.p_value, 6),
            "is_significant": self.is_significant,
            "alpha": self.alpha,
            "alternative": self.alternative,
            "effect_size": round(self.effect_size, 4) if self.effect_size else None,
            "effect_interpretation": self.effect_interpretation,
            "group_stats": self.group_stats,
            "interpretation": self.interpretation,
            "conclusion": self.conclusion
        }


# =============================================================================
# TIME SERIES ANALYZER
# =============================================================================

class TimeSeriesAnalyzer:
    """
    Analyzes time series data for trends, seasonality, and patterns.
    """
    
    def analyze(
        self,
        data: pd.Series,
        dates: Optional[pd.Series] = None,
        frequency: Optional[str] = None
    ) -> TimeSeriesAnalysis:
        """
        Perform comprehensive time series analysis.
        
        Args:
            data: Time series values
            dates: Optional datetime index
            frequency: Expected frequency (D, W, M, Q, Y)
            
        Returns:
            TimeSeriesAnalysis with all components
        """
        result = TimeSeriesAnalysis(length=len(data))
        
        # Clean data
        clean_data = data.dropna()
        if len(clean_data) < 4:
            return result
        
        # Basic statistics
        result.mean = float(clean_data.mean())
        result.std = float(clean_data.std())
        result.min_value = float(clean_data.min())
        result.max_value = float(clean_data.max())
        
        # Volatility (coefficient of variation)
        if result.mean != 0:
            result.volatility = (result.std / abs(result.mean)) * 100
        
        # Date range
        if dates is not None:
            dates_clean = pd.to_datetime(dates.dropna())
            if len(dates_clean) > 0:
                result.start_date = dates_clean.min()
                result.end_date = dates_clean.max()
                result.frequency = self._detect_frequency(dates_clean)
        
        # Trend analysis
        result.trend = self._analyze_trend(clean_data)
        
        # Seasonality detection
        result.seasonality = self._detect_seasonality(clean_data, frequency)
        
        # Stationarity test (requires scipy)
        if STATSMODELS_AVAILABLE and len(clean_data) >= 20:
            try:
                adf_result = adfuller(clean_data, autolag='AIC')
                result.adf_statistic = float(adf_result[0])
                result.adf_p_value = float(adf_result[1])
                result.is_stationary = result.adf_p_value < 0.05
            except:
                pass
        
        # Decomposition (requires statsmodels)
        if STATSMODELS_AVAILABLE and len(clean_data) >= 4:
            self._decompose(clean_data, result)
        
        # Anomaly detection
        result.anomalies = self._detect_anomalies(clean_data)
        
        # Change point detection
        result.change_points = self._detect_change_points(clean_data)
        
        return result
    
    def _analyze_trend(self, data: pd.Series) -> TrendResult:
        """Analyze the trend component"""
        n = len(data)
        x = np.arange(n)
        y = data.values
        
        # Linear regression for trend
        if SCIPY_AVAILABLE:
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
        else:
            # Fallback simple calculation
            x_mean, y_mean = x.mean(), y.mean()
            slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
            intercept = y_mean - slope * x_mean
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)
            r_value = np.sqrt(1 - ss_res / ss_tot) if ss_tot > 0 else 0
            p_value = None
        
        # Calculate metrics
        start_value = float(data.iloc[0])
        end_value = float(data.iloc[-1])
        total_change = end_value - start_value
        total_change_percent = (total_change / start_value * 100) if start_value != 0 else 0
        
        # Determine direction
        if abs(slope) < 0.001 * abs(data.mean()) if data.mean() != 0 else 0.001:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for high volatility
        if data.std() / abs(data.mean()) > 0.5 if data.mean() != 0 else data.std() > 0.5:
            if abs(r_value) < 0.5:
                direction = TrendDirection.VOLATILE
        
        slope_percent = (slope / abs(data.mean()) * 100) if data.mean() != 0 else 0
        
        return TrendResult(
            direction=direction,
            slope=float(slope),
            slope_percent=float(slope_percent),
            r_squared=float(r_value ** 2),
            start_value=start_value,
            end_value=end_value,
            total_change=float(total_change),
            total_change_percent=float(total_change_percent),
            is_significant=p_value < 0.05 if p_value else abs(r_value) > 0.5,
            p_value=float(p_value) if p_value else None
        )
    
    def _detect_seasonality(
        self,
        data: pd.Series,
        frequency: Optional[str] = None
    ) -> SeasonalityResult:
        """Detect seasonality in the data"""
        result = SeasonalityResult(
            has_seasonality=False,
            seasonality_type=SeasonalityType.NONE
        )
        
        if len(data) < 8:
            return result
        
        # Try to detect seasonal period
        potential_periods = [4, 7, 12, 24, 52]  # Quarter, Week, Month, Hour, Weekly in year
        
        best_period = None
        best_strength = 0
        
        for period in potential_periods:
            if len(data) < period * 2:
                continue
            
            strength = self._calculate_seasonal_strength(data, period)
            if strength > best_strength and strength > 0.3:
                best_strength = strength
                best_period = period
        
        if best_period:
            result.has_seasonality = True
            result.period = best_period
            result.strength = best_strength
            
            # Determine additive vs multiplicative
            if data.min() > 0 and data.std() / data.mean() > 0.3:
                result.seasonality_type = SeasonalityType.MULTIPLICATIVE
            else:
                result.seasonality_type = SeasonalityType.ADDITIVE
        
        return result
    
    def _calculate_seasonal_strength(self, data: pd.Series, period: int) -> float:
        """Calculate strength of seasonality for a given period"""
        try:
            if STATSMODELS_AVAILABLE:
                decomposition = seasonal_decompose(
                    data, model='additive', period=period, extrapolate_trend='freq'
                )
                seasonal_var = decomposition.seasonal.var()
                residual_var = decomposition.resid.var()
                
                if seasonal_var + residual_var > 0:
                    return max(0, 1 - residual_var / (seasonal_var + residual_var))
            
            # Fallback: autocorrelation at lag = period
            if len(data) > period:
                autocorr = data.autocorr(lag=period)
                return abs(autocorr) if not pd.isna(autocorr) else 0
                
        except:
            pass
        
        return 0
    
    def _decompose(self, data: pd.Series, result: TimeSeriesAnalysis):
        """Decompose time series into trend, seasonal, residual"""
        try:
            period = result.seasonality.period if result.seasonality and result.seasonality.period else 4
            
            if len(data) >= period * 2:
                model = 'multiplicative' if data.min() > 0 else 'additive'
                decomposition = seasonal_decompose(
                    data, model=model, period=period, extrapolate_trend='freq'
                )
                result.trend_component = decomposition.trend
                result.seasonal_component = decomposition.seasonal
                result.residual_component = decomposition.resid
        except:
            pass
    
    def _detect_anomalies(self, data: pd.Series, threshold: float = 3.0) -> List[int]:
        """Detect anomalies using Z-score method"""
        if len(data) < 10:
            return []
        
        mean = data.mean()
        std = data.std()
        
        if std == 0:
            return []
        
        z_scores = np.abs((data - mean) / std)
        anomaly_indices = np.where(z_scores > threshold)[0].tolist()
        
        return anomaly_indices[:20]  # Limit to 20 anomalies
    
    def _detect_change_points(self, data: pd.Series, threshold: float = 2.0) -> List[int]:
        """Detect significant change points in the series"""
        if len(data) < 10:
            return []
        
        # Calculate rolling statistics
        window = max(5, len(data) // 10)
        rolling_mean = data.rolling(window=window, center=True).mean()
        
        # Calculate changes
        diff = rolling_mean.diff().abs()
        diff_std = diff.std()
        
        if diff_std == 0 or pd.isna(diff_std):
            return []
        
        # Find significant changes
        change_points = np.where(diff > threshold * diff_std)[0].tolist()
        
        return change_points[:10]
    
    def _detect_frequency(self, dates: pd.Series) -> str:
        """Detect the frequency of the time series"""
        if len(dates) < 2:
            return "unknown"
        
        # Calculate median difference between consecutive dates
        diffs = dates.sort_values().diff().dropna()
        median_diff = diffs.median()
        
        if pd.isna(median_diff):
            return "unknown"
        
        days = median_diff.days
        
        if days <= 1:
            return "daily"
        elif days <= 7:
            return "weekly"
        elif days <= 31:
            return "monthly"
        elif days <= 92:
            return "quarterly"
        else:
            return "yearly"


# =============================================================================
# FORECAST ENGINE
# =============================================================================

class ForecastEngine:
    """
    Generates forecasts using various methods.
    """
    
    def forecast(
        self,
        data: pd.Series,
        periods: int,
        method: ForecastMethod = ForecastMethod.AUTO,
        seasonality: Optional[SeasonalityResult] = None,
        dates: Optional[pd.Series] = None,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Generate forecast for future periods.
        
        Args:
            data: Historical time series data
            periods: Number of periods to forecast
            method: Forecasting method to use
            seasonality: Pre-calculated seasonality info
            dates: Date index for predictions
            confidence_level: Confidence level for intervals
            
        Returns:
            ForecastResult with predictions
        """
        clean_data = data.dropna()
        
        if len(clean_data) < 4:
            return ForecastResult(
                method=method,
                periods=periods,
                predictions=[float(clean_data.mean())] * periods if len(clean_data) > 0 else [0] * periods,
                warnings=["Insufficient data for reliable forecast"]
            )
        
        # Auto-select method if requested
        if method == ForecastMethod.AUTO:
            method = self._select_best_method(clean_data, seasonality)
        
        # Generate forecast based on method
        if method == ForecastMethod.SIMPLE_MOVING_AVERAGE:
            result = self._simple_moving_average(clean_data, periods)
        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            result = self._exponential_smoothing(clean_data, periods)
        elif method == ForecastMethod.DOUBLE_EXPONENTIAL:
            result = self._double_exponential(clean_data, periods)
        elif method == ForecastMethod.HOLT_WINTERS:
            result = self._holt_winters(clean_data, periods, seasonality)
        elif method == ForecastMethod.LINEAR_TREND:
            result = self._linear_trend(clean_data, periods)
        else:
            result = self._simple_moving_average(clean_data, periods)
        
        result.method = method
        result.periods = periods
        result.confidence_level = confidence_level
        
        # Generate prediction dates if dates provided
        if dates is not None and len(dates) > 0:
            result.prediction_dates = self._generate_future_dates(dates, periods)
        
        # Calculate confidence intervals
        self._add_confidence_intervals(clean_data, result, confidence_level)
        
        # Calculate error metrics on training data
        self._calculate_metrics(clean_data, result)
        
        return result
    
    def _select_best_method(
        self,
        data: pd.Series,
        seasonality: Optional[SeasonalityResult] = None
    ) -> ForecastMethod:
        """Automatically select the best forecasting method"""
        
        # If strong seasonality detected, use Holt-Winters
        if seasonality and seasonality.has_seasonality and seasonality.strength > 0.5:
            if STATSMODELS_AVAILABLE:
                return ForecastMethod.HOLT_WINTERS
        
        # Check for trend
        n = len(data)
        x = np.arange(n)
        if SCIPY_AVAILABLE:
            slope, _, r_value, _, _ = scipy_stats.linregress(x, data.values)
            
            # Strong linear trend
            if abs(r_value) > 0.8:
                return ForecastMethod.LINEAR_TREND
            
            # Moderate trend
            elif abs(r_value) > 0.5:
                return ForecastMethod.DOUBLE_EXPONENTIAL
        
        # Default to exponential smoothing
        return ForecastMethod.EXPONENTIAL_SMOOTHING
    
    def _simple_moving_average(self, data: pd.Series, periods: int, window: int = None) -> ForecastResult:
        """Simple moving average forecast"""
        if window is None:
            window = min(5, len(data) // 2)
        
        last_avg = data.tail(window).mean()
        predictions = [float(last_avg)] * periods
        
        return ForecastResult(
            method=ForecastMethod.SIMPLE_MOVING_AVERAGE,
            periods=periods,
            predictions=predictions,
            model_params={"window": window}
        )
    
    def _exponential_smoothing(self, data: pd.Series, periods: int, alpha: float = 0.3) -> ForecastResult:
        """Single exponential smoothing"""
        values = data.values
        n = len(values)
        
        # Calculate smoothed values
        smoothed = np.zeros(n)
        smoothed[0] = values[0]
        
        for i in range(1, n):
            smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i-1]
        
        # Forecast is last smoothed value
        predictions = [float(smoothed[-1])] * periods
        
        return ForecastResult(
            method=ForecastMethod.EXPONENTIAL_SMOOTHING,
            periods=periods,
            predictions=predictions,
            model_params={"alpha": alpha}
        )
    
    def _double_exponential(self, data: pd.Series, periods: int, alpha: float = 0.3, beta: float = 0.1) -> ForecastResult:
        """Double exponential smoothing (Holt's method)"""
        values = data.values
        n = len(values)
        
        # Initialize
        level = np.zeros(n)
        trend = np.zeros(n)
        
        level[0] = values[0]
        trend[0] = values[1] - values[0] if n > 1 else 0
        
        # Calculate smoothed values
        for i in range(1, n):
            level[i] = alpha * values[i] + (1 - alpha) * (level[i-1] + trend[i-1])
            trend[i] = beta * (level[i] - level[i-1]) + (1 - beta) * trend[i-1]
        
        # Forecast
        predictions = []
        for i in range(1, periods + 1):
            predictions.append(float(level[-1] + i * trend[-1]))
        
        return ForecastResult(
            method=ForecastMethod.DOUBLE_EXPONENTIAL,
            periods=periods,
            predictions=predictions,
            model_params={"alpha": alpha, "beta": beta}
        )
    
    def _holt_winters(
        self,
        data: pd.Series,
        periods: int,
        seasonality: Optional[SeasonalityResult] = None
    ) -> ForecastResult:
        """Holt-Winters exponential smoothing"""
        warnings_list = []
        
        if not STATSMODELS_AVAILABLE:
            warnings_list.append("statsmodels not installed, using double exponential instead")
            return self._double_exponential(data, periods)
        
        try:
            # Determine seasonal period
            seasonal_period = seasonality.period if seasonality and seasonality.period else 4
            
            if len(data) < seasonal_period * 2:
                warnings_list.append(f"Insufficient data for seasonality period {seasonal_period}")
                return self._double_exponential(data, periods)
            
            # Fit model
            seasonal_type = 'mul' if data.min() > 0 else 'add'
            model = ExponentialSmoothing(
                data,
                seasonal_periods=seasonal_period,
                trend='add',
                seasonal=seasonal_type
            )
            fitted = model.fit()
            
            # Forecast
            forecast = fitted.forecast(periods)
            predictions = forecast.tolist()
            
            return ForecastResult(
                method=ForecastMethod.HOLT_WINTERS,
                periods=periods,
                predictions=predictions,
                model_params={
                    "seasonal_period": seasonal_period,
                    "seasonal_type": seasonal_type
                },
                warnings=warnings_list
            )
            
        except Exception as e:
            warnings_list.append(f"Holt-Winters failed: {str(e)}")
            return self._double_exponential(data, periods)
    
    def _linear_trend(self, data: pd.Series, periods: int) -> ForecastResult:
        """Linear trend extrapolation"""
        n = len(data)
        x = np.arange(n)
        y = data.values
        
        # Fit linear model
        if SCIPY_AVAILABLE:
            slope, intercept, _, _, _ = scipy_stats.linregress(x, y)
        else:
            x_mean, y_mean = x.mean(), y.mean()
            slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
            intercept = y_mean - slope * x_mean
        
        # Forecast
        predictions = []
        for i in range(n, n + periods):
            predictions.append(float(slope * i + intercept))
        
        return ForecastResult(
            method=ForecastMethod.LINEAR_TREND,
            periods=periods,
            predictions=predictions,
            model_params={"slope": slope, "intercept": intercept}
        )
    
    def _generate_future_dates(self, dates: pd.Series, periods: int) -> List[datetime]:
        """Generate future dates based on detected frequency"""
        dates_sorted = pd.to_datetime(dates).sort_values()
        last_date = dates_sorted.iloc[-1]
        
        # Detect frequency
        if len(dates_sorted) >= 2:
            median_diff = dates_sorted.diff().median()
        else:
            median_diff = timedelta(days=1)
        
        future_dates = []
        for i in range(1, periods + 1):
            future_dates.append(last_date + i * median_diff)
        
        return future_dates
    
    def _add_confidence_intervals(
        self,
        data: pd.Series,
        result: ForecastResult,
        confidence_level: float
    ):
        """Add confidence intervals to forecast"""
        # Use historical standard deviation for intervals
        std = data.std()
        
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_level, 1.96)
        
        # Widen intervals for further predictions
        lower = []
        upper = []
        
        for i, pred in enumerate(result.predictions):
            margin = z * std * np.sqrt(1 + i * 0.1)  # Increasing uncertainty
            lower.append(pred - margin)
            upper.append(pred + margin)
        
        result.lower_bound = lower
        result.upper_bound = upper
    
    def _calculate_metrics(self, data: pd.Series, result: ForecastResult):
        """Calculate error metrics on training data"""
        if len(data) < 4:
            return
        
        # Simple backtest: use last few values
        n_test = min(5, len(data) // 4)
        train = data.iloc[:-n_test]
        test = data.iloc[-n_test:]
        
        # Generate predictions for test period
        if result.method == ForecastMethod.SIMPLE_MOVING_AVERAGE:
            test_pred = [train.tail(5).mean()] * n_test
        elif result.method == ForecastMethod.LINEAR_TREND:
            slope = result.model_params.get('slope', 0)
            intercept = result.model_params.get('intercept', 0)
            test_pred = [slope * (len(train) + i) + intercept for i in range(n_test)]
        else:
            test_pred = [train.iloc[-1]] * n_test
        
        test_actual = test.values
        test_pred = np.array(test_pred)
        
        # Calculate metrics
        result.mae = float(np.mean(np.abs(test_actual - test_pred)))
        result.rmse = float(np.sqrt(np.mean((test_actual - test_pred) ** 2)))
        
        # MAPE (avoid division by zero)
        non_zero = test_actual != 0
        if non_zero.any():
            result.mape = float(np.mean(np.abs((test_actual[non_zero] - test_pred[non_zero]) / test_actual[non_zero])) * 100)


# =============================================================================
# REGRESSION ANALYZER
# =============================================================================

class RegressionAnalyzer:
    """
    Performs regression analysis.
    """
    
    def analyze(
        self,
        df: pd.DataFrame,
        target: str,
        features: List[str],
        regression_type: RegressionType = RegressionType.LINEAR,
        polynomial_degree: int = 2
    ) -> RegressionResult:
        """
        Perform regression analysis.
        
        Args:
            df: DataFrame with data
            target: Target column name
            features: Feature column names
            regression_type: Type of regression
            polynomial_degree: Degree for polynomial regression
            
        Returns:
            RegressionResult with model details
        """
        result = RegressionResult(
            regression_type=regression_type,
            target_column=target,
            feature_columns=features
        )
        
        # Validate columns
        if target not in df.columns:
            result.interpretation = f"Target column '{target}' not found"
            return result
        
        missing_features = [f for f in features if f not in df.columns]
        if missing_features:
            result.interpretation = f"Feature columns not found: {missing_features}"
            return result
        
        # Prepare data
        data = df[[target] + features].dropna()
        if len(data) < len(features) + 2:
            result.interpretation = "Insufficient data for regression"
            return result
        
        X = data[features].values
        y = data[target].values
        
        # Perform regression based on type
        if regression_type == RegressionType.LINEAR and len(features) == 1:
            result = self._simple_linear_regression(X.flatten(), y, target, features[0])
        elif regression_type == RegressionType.POLYNOMIAL:
            result = self._polynomial_regression(X.flatten(), y, target, features[0], polynomial_degree)
        else:
            result = self._multiple_regression(X, y, target, features)
        
        return result
    
    def _simple_linear_regression(
        self,
        x: np.ndarray,
        y: np.ndarray,
        target: str,
        feature: str
    ) -> RegressionResult:
        """Simple linear regression with one feature"""
        result = RegressionResult(
            regression_type=RegressionType.LINEAR,
            target_column=target,
            feature_columns=[feature]
        )
        
        if SCIPY_AVAILABLE:
            slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
            
            result.intercept = float(intercept)
            result.coefficients = {feature: float(slope)}
            result.r_squared = float(r_value ** 2)
            result.p_values = {feature: float(p_value)}
            result.is_significant = p_value < 0.05
            
            # Predictions and residuals
            predictions = slope * x + intercept
            residuals = y - predictions
            
            result.predictions = pd.Series(predictions)
            result.residuals = pd.Series(residuals)
            result.rmse = float(np.sqrt(np.mean(residuals ** 2)))
            result.mae = float(np.mean(np.abs(residuals)))
            
            # Generate interpretation
            direction = "increases" if slope > 0 else "decreases"
            result.interpretation = (
                f"For each unit increase in {feature}, {target} {direction} by {abs(slope):.2f}. "
                f"R² = {result.r_squared:.3f} means {result.r_squared*100:.1f}% of variance is explained. "
                f"{'Statistically significant (p < 0.05).' if result.is_significant else 'Not statistically significant.'}"
            )
        else:
            # Fallback calculation
            x_mean, y_mean = x.mean(), y.mean()
            slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
            intercept = y_mean - slope * x_mean
            
            result.intercept = float(intercept)
            result.coefficients = {feature: float(slope)}
            
            predictions = slope * x + intercept
            ss_res = np.sum((y - predictions) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)
            result.r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0
            
            result.interpretation = f"Linear relationship: {target} = {slope:.2f} × {feature} + {intercept:.2f}"
        
        return result
    
    def _polynomial_regression(
        self,
        x: np.ndarray,
        y: np.ndarray,
        target: str,
        feature: str,
        degree: int
    ) -> RegressionResult:
        """Polynomial regression"""
        result = RegressionResult(
            regression_type=RegressionType.POLYNOMIAL,
            target_column=target,
            feature_columns=[feature]
        )
        
        if not SKLEARN_AVAILABLE:
            result.interpretation = "sklearn required for polynomial regression"
            return result
        
        # Create polynomial features
        x_reshaped = x.reshape(-1, 1)
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        x_poly = poly.fit_transform(x_reshaped)
        
        # Fit model
        model = LinearRegression()
        model.fit(x_poly, y)
        
        # Predictions
        predictions = model.predict(x_poly)
        residuals = y - predictions
        
        result.intercept = float(model.intercept_)
        result.coefficients = {f"{feature}^{i+1}": float(c) for i, c in enumerate(model.coef_)}
        result.r_squared = float(r2_score(y, predictions))
        result.rmse = float(np.sqrt(mean_squared_error(y, predictions)))
        result.mae = float(mean_absolute_error(y, predictions))
        result.predictions = pd.Series(predictions)
        result.residuals = pd.Series(residuals)
        
        result.interpretation = (
            f"Polynomial regression (degree {degree}): R² = {result.r_squared:.3f}. "
            f"This explains {result.r_squared*100:.1f}% of the variance in {target}."
        )
        
        return result
    
    def _multiple_regression(
        self,
        X: np.ndarray,
        y: np.ndarray,
        target: str,
        features: List[str]
    ) -> RegressionResult:
        """Multiple linear regression"""
        result = RegressionResult(
            regression_type=RegressionType.MULTIPLE,
            target_column=target,
            feature_columns=features
        )
        
        if not SKLEARN_AVAILABLE:
            result.interpretation = "sklearn required for multiple regression"
            return result
        
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predictions
        predictions = model.predict(X)
        residuals = y - predictions
        
        result.intercept = float(model.intercept_)
        result.coefficients = {f: float(c) for f, c in zip(features, model.coef_)}
        result.r_squared = float(r2_score(y, predictions))
        result.rmse = float(np.sqrt(mean_squared_error(y, predictions)))
        result.mae = float(mean_absolute_error(y, predictions))
        result.predictions = pd.Series(predictions)
        result.residuals = pd.Series(residuals)
        
        # Adjusted R²
        n = len(y)
        p = len(features)
        result.adjusted_r_squared = 1 - (1 - result.r_squared) * (n - 1) / (n - p - 1)
        
        # Identify most important features
        sorted_coefs = sorted(result.coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
        top_features = [f"{name} ({coef:+.2f})" for name, coef in sorted_coefs[:3]]
        
        result.interpretation = (
            f"Multiple regression with {len(features)} features. "
            f"R² = {result.r_squared:.3f}, Adjusted R² = {result.adjusted_r_squared:.3f}. "
            f"Most important features: {', '.join(top_features)}."
        )
        
        return result


# =============================================================================
# HYPOTHESIS TESTER
# =============================================================================

class HypothesisTester:
    """
    Performs various hypothesis tests.
    """
    
    def t_test_independent(
        self,
        group1: pd.Series,
        group2: pd.Series,
        alpha: float = 0.05,
        alternative: str = "two-sided"
    ) -> HypothesisTestResult:
        """
        Independent samples t-test.
        
        Tests if two groups have different means.
        """
        result = HypothesisTestResult(
            test_type=TestType.T_TEST_INDEPENDENT,
            test_name="Independent Samples T-Test",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha,
            alternative=alternative
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for t-test"
            return result
        
        # Clean data
        g1 = group1.dropna()
        g2 = group2.dropna()
        
        if len(g1) < 2 or len(g2) < 2:
            result.interpretation = "Insufficient data for t-test"
            return result
        
        # Perform test
        statistic, p_value = scipy_stats.ttest_ind(g1, g2, alternative=alternative)
        
        result.statistic = float(statistic)
        result.p_value = float(p_value)
        result.is_significant = p_value < alpha
        
        # Group statistics
        result.group_stats = {
            "group1": {"mean": float(g1.mean()), "std": float(g1.std()), "n": len(g1)},
            "group2": {"mean": float(g2.mean()), "std": float(g2.std()), "n": len(g2)}
        }
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(g1)-1)*g1.std()**2 + (len(g2)-1)*g2.std()**2) / (len(g1)+len(g2)-2))
        if pooled_std > 0:
            result.effect_size = float((g1.mean() - g2.mean()) / pooled_std)
            
            # Interpret effect size
            abs_effect = abs(result.effect_size)
            if abs_effect < 0.2:
                result.effect_interpretation = "negligible"
            elif abs_effect < 0.5:
                result.effect_interpretation = "small"
            elif abs_effect < 0.8:
                result.effect_interpretation = "medium"
            else:
                result.effect_interpretation = "large"
        
        # Generate interpretation
        mean_diff = g1.mean() - g2.mean()
        if result.is_significant:
            result.interpretation = (
                f"There IS a statistically significant difference between the groups "
                f"(t={result.statistic:.2f}, p={result.p_value:.4f}). "
                f"Group 1 mean ({g1.mean():.2f}) is {'higher' if mean_diff > 0 else 'lower'} "
                f"than Group 2 mean ({g2.mean():.2f}) by {abs(mean_diff):.2f}."
            )
            result.conclusion = "Reject null hypothesis: The groups are significantly different."
        else:
            result.interpretation = (
                f"There is NO statistically significant difference between the groups "
                f"(t={result.statistic:.2f}, p={result.p_value:.4f})."
            )
            result.conclusion = "Fail to reject null hypothesis: No significant difference found."
        
        return result
    
    def t_test_paired(
        self,
        before: pd.Series,
        after: pd.Series,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Paired samples t-test.
        
        Tests if there's a significant change between paired measurements.
        """
        result = HypothesisTestResult(
            test_type=TestType.T_TEST_PAIRED,
            test_name="Paired Samples T-Test",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for t-test"
            return result
        
        # Clean data (must have same length)
        valid = before.notna() & after.notna()
        b = before[valid]
        a = after[valid]
        
        if len(b) < 2:
            result.interpretation = "Insufficient paired data"
            return result
        
        # Perform test
        statistic, p_value = scipy_stats.ttest_rel(b, a)
        
        result.statistic = float(statistic)
        result.p_value = float(p_value)
        result.is_significant = p_value < alpha
        
        # Statistics
        diff = a - b
        result.group_stats = {
            "before": {"mean": float(b.mean()), "std": float(b.std()), "n": len(b)},
            "after": {"mean": float(a.mean()), "std": float(a.std()), "n": len(a)},
            "difference": {"mean": float(diff.mean()), "std": float(diff.std())}
        }
        
        # Effect size
        if diff.std() > 0:
            result.effect_size = float(diff.mean() / diff.std())
        
        # Interpretation
        if result.is_significant:
            direction = "increased" if diff.mean() > 0 else "decreased"
            result.interpretation = (
                f"There IS a significant change. Values {direction} by {abs(diff.mean()):.2f} on average "
                f"(t={result.statistic:.2f}, p={result.p_value:.4f})."
            )
            result.conclusion = "Reject null hypothesis: Significant change detected."
        else:
            result.interpretation = (
                f"There is NO significant change "
                f"(t={result.statistic:.2f}, p={result.p_value:.4f})."
            )
            result.conclusion = "Fail to reject null hypothesis: No significant change."
        
        return result
    
    def anova(
        self,
        *groups: pd.Series,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        One-way ANOVA test.
        
        Tests if there are differences among three or more group means.
        """
        result = HypothesisTestResult(
            test_type=TestType.ANOVA,
            test_name="One-Way ANOVA",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for ANOVA"
            return result
        
        # Clean groups
        clean_groups = [g.dropna() for g in groups]
        valid_groups = [g for g in clean_groups if len(g) >= 2]
        
        if len(valid_groups) < 2:
            result.interpretation = "Need at least 2 valid groups for ANOVA"
            return result
        
        # Perform ANOVA
        statistic, p_value = scipy_stats.f_oneway(*valid_groups)
        
        result.statistic = float(statistic)
        result.p_value = float(p_value)
        result.is_significant = p_value < alpha
        
        # Group statistics
        for i, g in enumerate(valid_groups):
            result.group_stats[f"group_{i+1}"] = {
                "mean": float(g.mean()),
                "std": float(g.std()),
                "n": len(g)
            }
        
        # Interpretation
        if result.is_significant:
            result.interpretation = (
                f"There ARE significant differences among the {len(valid_groups)} groups "
                f"(F={result.statistic:.2f}, p={result.p_value:.4f}). "
                f"At least one group mean differs from the others."
            )
            result.conclusion = "Reject null hypothesis: Groups have different means."
        else:
            result.interpretation = (
                f"There are NO significant differences among the groups "
                f"(F={result.statistic:.2f}, p={result.p_value:.4f})."
            )
            result.conclusion = "Fail to reject null hypothesis: No significant differences."
        
        return result
    
    def chi_square(
        self,
        observed: pd.DataFrame,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Chi-square test of independence.
        
        Tests if two categorical variables are independent.
        """
        result = HypothesisTestResult(
            test_type=TestType.CHI_SQUARE,
            test_name="Chi-Square Test of Independence",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for chi-square test"
            return result
        
        try:
            chi2, p_value, dof, expected = scipy_stats.chi2_contingency(observed)
            
            result.statistic = float(chi2)
            result.p_value = float(p_value)
            result.is_significant = p_value < alpha
            
            # Effect size (Cramér's V)
            n = observed.sum().sum()
            min_dim = min(observed.shape) - 1
            if min_dim > 0 and n > 0:
                result.effect_size = float(np.sqrt(chi2 / (n * min_dim)))
            
            if result.is_significant:
                result.interpretation = (
                    f"The variables ARE associated (χ²={result.statistic:.2f}, p={result.p_value:.4f}). "
                    f"They are NOT independent."
                )
                result.conclusion = "Reject null hypothesis: Variables are related."
            else:
                result.interpretation = (
                    f"The variables are NOT significantly associated "
                    f"(χ²={result.statistic:.2f}, p={result.p_value:.4f})."
                )
                result.conclusion = "Fail to reject null hypothesis: Variables appear independent."
                
        except Exception as e:
            result.interpretation = f"Chi-square test failed: {str(e)}"
        
        return result
    
    def correlation_test(
        self,
        x: pd.Series,
        y: pd.Series,
        method: str = "pearson",
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Test if correlation is statistically significant.
        """
        result = HypothesisTestResult(
            test_type=TestType.CORRELATION,
            test_name=f"{method.capitalize()} Correlation Test",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for correlation test"
            return result
        
        # Clean data
        valid = x.notna() & y.notna()
        x_clean = x[valid]
        y_clean = y[valid]
        
        if len(x_clean) < 3:
            result.interpretation = "Insufficient data for correlation test"
            return result
        
        # Calculate correlation
        if method == "pearson":
            corr, p_value = scipy_stats.pearsonr(x_clean, y_clean)
        elif method == "spearman":
            corr, p_value = scipy_stats.spearmanr(x_clean, y_clean)
        else:
            corr, p_value = scipy_stats.kendalltau(x_clean, y_clean)
        
        result.statistic = float(corr)
        result.p_value = float(p_value)
        result.is_significant = p_value < alpha
        result.effect_size = float(corr)
        
        # Interpret strength
        abs_corr = abs(corr)
        if abs_corr < 0.3:
            result.effect_interpretation = "weak"
        elif abs_corr < 0.7:
            result.effect_interpretation = "moderate"
        else:
            result.effect_interpretation = "strong"
        
        direction = "positive" if corr > 0 else "negative"
        
        if result.is_significant:
            result.interpretation = (
                f"There IS a significant {result.effect_interpretation} {direction} correlation "
                f"(r={result.statistic:.3f}, p={result.p_value:.4f})."
            )
            result.conclusion = f"Variables are significantly correlated ({direction})."
        else:
            result.interpretation = (
                f"There is NO significant correlation "
                f"(r={result.statistic:.3f}, p={result.p_value:.4f})."
            )
            result.conclusion = "No significant correlation found."
        
        return result
    
    def normality_test(
        self,
        data: pd.Series,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Test if data follows normal distribution (Shapiro-Wilk test).
        """
        result = HypothesisTestResult(
            test_type=TestType.NORMALITY,
            test_name="Shapiro-Wilk Normality Test",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            alpha=alpha
        )
        
        if not SCIPY_AVAILABLE:
            result.interpretation = "scipy required for normality test"
            return result
        
        clean_data = data.dropna()
        
        if len(clean_data) < 3:
            result.interpretation = "Insufficient data for normality test"
            return result
        
        # Shapiro-Wilk test (best for n < 5000)
        if len(clean_data) <= 5000:
            statistic, p_value = scipy_stats.shapiro(clean_data)
        else:
            # Use D'Agostino-Pearson for larger samples
            statistic, p_value = scipy_stats.normaltest(clean_data)
        
        result.statistic = float(statistic)
        result.p_value = float(p_value)
        result.is_significant = p_value < alpha  # Significant = NOT normal
        
        result.group_stats = {
            "data": {
                "mean": float(clean_data.mean()),
                "std": float(clean_data.std()),
                "skewness": float(scipy_stats.skew(clean_data)),
                "kurtosis": float(scipy_stats.kurtosis(clean_data)),
                "n": len(clean_data)
            }
        }
        
        if result.is_significant:
            result.interpretation = (
                f"Data does NOT follow a normal distribution "
                f"(W={result.statistic:.4f}, p={result.p_value:.4f}). "
                f"Consider using non-parametric tests."
            )
            result.conclusion = "Reject normality: Data is not normally distributed."
        else:
            result.interpretation = (
                f"Data appears to follow a normal distribution "
                f"(W={result.statistic:.4f}, p={result.p_value:.4f}). "
                f"Parametric tests are appropriate."
            )
            result.conclusion = "Cannot reject normality: Data may be normally distributed."
        
        return result


# =============================================================================
# MAIN STATISTICAL ENGINE CLASS
# =============================================================================

class StatisticalEngine:
    """
    Main class for statistical analysis.
    
    Combines all statistical components for comprehensive analysis.
    
    Usage:
        engine = StatisticalEngine()
        
        # Time series analysis
        ts_result = engine.analyze_time_series(df['Sales'], df['Date'])
        
        # Forecasting
        forecast = engine.forecast(df['Sales'], periods=12)
        
        # Regression
        reg_result = engine.regression(df, 'Sales', ['Marketing', 'Price'])
        
        # Hypothesis testing
        t_result = engine.t_test(group1, group2)
    """
    
    def __init__(self):
        """Initialize the statistical engine."""
        self.ts_analyzer = TimeSeriesAnalyzer()
        self.forecast_engine = ForecastEngine()
        self.regression_analyzer = RegressionAnalyzer()
        self.hypothesis_tester = HypothesisTester()
        
        logger.info("StatisticalEngine initialized")
        logger.info(f"  scipy available: {SCIPY_AVAILABLE}")
        logger.info(f"  sklearn available: {SKLEARN_AVAILABLE}")
        logger.info(f"  statsmodels available: {STATSMODELS_AVAILABLE}")
    
    # =========================================================================
    # Time Series Methods
    # =========================================================================
    
    def analyze_time_series(
        self,
        data: pd.Series,
        dates: Optional[pd.Series] = None,
        frequency: Optional[str] = None
    ) -> TimeSeriesAnalysis:
        """
        Perform comprehensive time series analysis.
        
        Args:
            data: Time series values
            dates: Optional datetime index
            frequency: Expected frequency (D, W, M, Q, Y)
            
        Returns:
            TimeSeriesAnalysis with all components
        """
        return self.ts_analyzer.analyze(data, dates, frequency)
    
    # =========================================================================
    # Forecasting Methods
    # =========================================================================
    
    def forecast(
        self,
        data: pd.Series,
        periods: int,
        method: ForecastMethod = ForecastMethod.AUTO,
        dates: Optional[pd.Series] = None,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Generate forecast for future periods.
        
        Args:
            data: Historical time series data
            periods: Number of periods to forecast
            method: Forecasting method (or AUTO)
            dates: Date index for predictions
            confidence_level: Confidence level for intervals
            
        Returns:
            ForecastResult with predictions
        """
        # Get seasonality info for better forecasting
        ts_analysis = self.ts_analyzer.analyze(data, dates)
        
        return self.forecast_engine.forecast(
            data=data,
            periods=periods,
            method=method,
            seasonality=ts_analysis.seasonality,
            dates=dates,
            confidence_level=confidence_level
        )
    
    # =========================================================================
    # Regression Methods
    # =========================================================================
    
    def regression(
        self,
        df: pd.DataFrame,
        target: str,
        features: List[str],
        regression_type: RegressionType = RegressionType.LINEAR,
        polynomial_degree: int = 2
    ) -> RegressionResult:
        """
        Perform regression analysis.
        
        Args:
            df: DataFrame with data
            target: Target column name
            features: Feature column names
            regression_type: Type of regression
            polynomial_degree: Degree for polynomial regression
            
        Returns:
            RegressionResult with model details
        """
        return self.regression_analyzer.analyze(
            df, target, features, regression_type, polynomial_degree
        )
    
    def simple_regression(
        self,
        df: pd.DataFrame,
        target: str,
        feature: str
    ) -> RegressionResult:
        """Convenience method for simple linear regression."""
        return self.regression(df, target, [feature], RegressionType.LINEAR)
    
    def polynomial_regression(
        self,
        df: pd.DataFrame,
        target: str,
        feature: str,
        degree: int = 2
    ) -> RegressionResult:
        """Convenience method for polynomial regression."""
        return self.regression(df, target, [feature], RegressionType.POLYNOMIAL, degree)
    
    # =========================================================================
    # Hypothesis Testing Methods
    # =========================================================================
    
    def t_test(
        self,
        group1: pd.Series,
        group2: pd.Series,
        paired: bool = False,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Perform t-test.
        
        Args:
            group1: First group data
            group2: Second group data
            paired: If True, use paired t-test
            alpha: Significance level
            
        Returns:
            HypothesisTestResult
        """
        if paired:
            return self.hypothesis_tester.t_test_paired(group1, group2, alpha)
        else:
            return self.hypothesis_tester.t_test_independent(group1, group2, alpha)
    
    def anova(self, *groups: pd.Series, alpha: float = 0.05) -> HypothesisTestResult:
        """Perform one-way ANOVA."""
        return self.hypothesis_tester.anova(*groups, alpha=alpha)
    
    def chi_square(self, contingency_table: pd.DataFrame, alpha: float = 0.05) -> HypothesisTestResult:
        """Perform chi-square test."""
        return self.hypothesis_tester.chi_square(contingency_table, alpha)
    
    def correlation_test(
        self,
        x: pd.Series,
        y: pd.Series,
        method: str = "pearson",
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """Test if correlation is significant."""
        return self.hypothesis_tester.correlation_test(x, y, method, alpha)
    
    def normality_test(self, data: pd.Series, alpha: float = 0.05) -> HypothesisTestResult:
        """Test if data is normally distributed."""
        return self.hypothesis_tester.normality_test(data, alpha)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about available capabilities."""
        return {
            "scipy_available": SCIPY_AVAILABLE,
            "sklearn_available": SKLEARN_AVAILABLE,
            "statsmodels_available": STATSMODELS_AVAILABLE,
            "forecast_methods": [m.value for m in ForecastMethod],
            "regression_types": [r.value for r in RegressionType],
            "hypothesis_tests": [t.value for t in TestType],
            "features": {
                "time_series_analysis": True,
                "forecasting": True,
                "regression": SKLEARN_AVAILABLE or SCIPY_AVAILABLE,
                "hypothesis_testing": SCIPY_AVAILABLE,
                "advanced_forecasting": STATSMODELS_AVAILABLE
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_trend(data: pd.Series) -> TrendResult:
    """Quick trend analysis."""
    analyzer = TimeSeriesAnalyzer()
    result = analyzer.analyze(data)
    return result.trend


def quick_forecast(data: pd.Series, periods: int) -> List[float]:
    """Quick forecast without full analysis."""
    engine = ForecastEngine()
    result = engine.forecast(data, periods, ForecastMethod.AUTO)
    return result.predictions


def compare_groups(group1: pd.Series, group2: pd.Series) -> HypothesisTestResult:
    """Quick comparison of two groups."""
    tester = HypothesisTester()
    return tester.t_test_independent(group1, group2)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Main class
    'StatisticalEngine',
    
    # Component classes
    'TimeSeriesAnalyzer',
    'ForecastEngine',
    'RegressionAnalyzer',
    'HypothesisTester',
    
    # Result classes
    'TimeSeriesAnalysis',
    'TrendResult',
    'SeasonalityResult',
    'ForecastResult',
    'RegressionResult',
    'HypothesisTestResult',
    
    # Enums
    'TrendDirection',
    'ForecastMethod',
    'SeasonalityType',
    'RegressionType',
    'TestType',
    
    # Convenience functions
    'analyze_trend',
    'quick_forecast',
    'compare_groups',
]