"""
Core Analysis Engine
Performs automated statistical analysis on datasets using Pandas, NumPy, and Scikit-learn.
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnalysisEngine:
    """Performs comprehensive data analysis on a pandas DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

    def run_full_analysis(self) -> dict:
        """Run all analysis types and return combined results."""
        results = {
            'descriptive_stats': self.descriptive_statistics(),
            'correlation': self.correlation_analysis(),
            'outliers': self.outlier_detection(),
            'distribution': self.distribution_analysis(),
            'missing_data': self.missing_data_analysis(),
            'trends': self.trend_detection(),
        }
        results['charts'] = self.generate_chart_data(results)
        results['summary'] = self.generate_summary(results)
        return results

    def descriptive_statistics(self) -> dict:
        """Calculate descriptive statistics for all columns."""
        stats = {}

        if self.numeric_cols:
            numeric_stats = self.df[self.numeric_cols].describe().to_dict()
            # Convert numpy types for JSON serialization
            for col in numeric_stats:
                for key in numeric_stats[col]:
                    val = numeric_stats[col][key]
                    if pd.isna(val):
                        numeric_stats[col][key] = None
                    elif isinstance(val, (np.integer, np.int64)):
                        numeric_stats[col][key] = int(val)
                    elif isinstance(val, (np.floating, np.float64)):
                        numeric_stats[col][key] = round(float(val), 4)
            stats['numeric'] = numeric_stats

        if self.categorical_cols:
            cat_stats = {}
            for col in self.categorical_cols:
                value_counts = self.df[col].value_counts().head(10)
                cat_stats[col] = {
                    'unique_count': int(self.df[col].nunique()),
                    'top_values': {str(k): int(v) for k, v in value_counts.items()},
                    'mode': str(self.df[col].mode().iloc[0]) if not self.df[col].mode().empty else None,
                }
            stats['categorical'] = cat_stats

        stats['shape'] = {'rows': int(self.df.shape[0]), 'columns': int(self.df.shape[1])}
        return stats

    def correlation_analysis(self) -> dict:
        """Calculate correlation matrix for numeric columns."""
        if len(self.numeric_cols) < 2:
            return {'message': 'Need at least 2 numeric columns for correlation analysis'}

        corr_matrix = self.df[self.numeric_cols].corr()

        # Find top correlations
        top_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                val = round(float(corr_matrix.iloc[i, j]), 4)
                if abs(val) > 0.3:  # Only significant correlations
                    top_correlations.append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'value': val,
                        'strength': self._correlation_strength(val),
                    })

        top_correlations.sort(key=lambda x: abs(x['value']), reverse=True)

        return {
            'matrix': {
                col: {str(k): round(float(v), 4) for k, v in row.items()}
                for col, row in corr_matrix.to_dict().items()
            },
            'top_correlations': top_correlations[:10],
            'columns': self.numeric_cols,
        }

    def outlier_detection(self) -> dict:
        """Detect outliers using IQR and Isolation Forest methods."""
        if not self.numeric_cols:
            return {'message': 'No numeric columns for outlier detection'}

        outliers = {}

        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) == 0:
                continue

            Q1 = float(data.quantile(0.25))
            Q3 = float(data.quantile(0.75))
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outlier_mask = (data < lower_bound) | (data > upper_bound)
            outlier_count = int(outlier_mask.sum())

            outliers[col] = {
                'count': outlier_count,
                'percentage': round(outlier_count / len(data) * 100, 2),
                'lower_bound': round(lower_bound, 4),
                'upper_bound': round(upper_bound, 4),
                'Q1': round(Q1, 4),
                'Q3': round(Q3, 4),
                'IQR': round(IQR, 4),
            }

        # Isolation Forest for multivariate outlier detection
        iso_forest_result = {}
        if len(self.numeric_cols) >= 2:
            try:
                numeric_data = self.df[self.numeric_cols].dropna()
                if len(numeric_data) > 10:
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(numeric_data)
                    iso_forest = IsolationForest(contamination=0.1, random_state=42)
                    predictions = iso_forest.fit_predict(scaled_data)
                    outlier_count = int((predictions == -1).sum())
                    iso_forest_result = {
                        'total_outliers': outlier_count,
                        'percentage': round(outlier_count / len(numeric_data) * 100, 2),
                    }
            except Exception:
                iso_forest_result = {'message': 'Could not run Isolation Forest'}

        return {'iqr_method': outliers, 'isolation_forest': iso_forest_result}

    def distribution_analysis(self) -> dict:
        """Analyze the distribution of numeric columns."""
        if not self.numeric_cols:
            return {'message': 'No numeric columns for distribution analysis'}

        distributions = {}
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) == 0:
                continue

            distributions[col] = {
                'mean': round(float(data.mean()), 4),
                'median': round(float(data.median()), 4),
                'std': round(float(data.std()), 4),
                'skewness': round(float(data.skew()), 4),
                'kurtosis': round(float(data.kurtosis()), 4),
                'min': round(float(data.min()), 4),
                'max': round(float(data.max()), 4),
            }

            # Histogram data (10 bins)
            counts, bin_edges = np.histogram(data, bins=10)
            distributions[col]['histogram'] = {
                'counts': [int(c) for c in counts],
                'bin_edges': [round(float(e), 4) for e in bin_edges],
            }

        return distributions

    def missing_data_analysis(self) -> dict:
        """Analyze missing data patterns."""
        missing = self.df.isnull().sum()
        total = len(self.df)

        missing_info = {}
        for col in self.df.columns:
            count = int(missing[col])
            if count > 0:
                missing_info[col] = {
                    'count': count,
                    'percentage': round(count / total * 100, 2),
                }

        return {
            'columns_with_missing': missing_info,
            'total_missing_cells': int(missing.sum()),
            'total_cells': int(total * len(self.df.columns)),
            'completeness': round((1 - missing.sum() / (total * len(self.df.columns))) * 100, 2),
        }

    def trend_detection(self) -> dict:
        """Detect trends in numeric time-series data."""
        trends = {}

        for col in self.numeric_cols:
            data = self.df[col].dropna().reset_index(drop=True)
            if len(data) < 5:
                continue

            # Simple moving average
            window = min(5, len(data) // 3) or 1
            moving_avg = data.rolling(window=window).mean().dropna()

            # Linear trend
            x = np.arange(len(data))
            try:
                coeffs = np.polyfit(x, data.values, 1)
                slope = float(coeffs[0])
                trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'

                trends[col] = {
                    'direction': trend_direction,
                    'slope': round(slope, 6),
                    'moving_average': [round(float(v), 4) for v in moving_avg.tail(20).tolist()],
                    'recent_values': [round(float(v), 4) for v in data.tail(20).tolist()],
                }
            except Exception:
                continue

        return trends

    def generate_chart_data(self, results: dict) -> dict:
        """Generate Chart.js-compatible configuration data."""
        charts = {}

        # Correlation heatmap data
        if 'matrix' in results.get('correlation', {}):
            corr = results['correlation']
            charts['correlation_heatmap'] = {
                'labels': corr['columns'],
                'data': [
                    [corr['matrix'][col1].get(col2, 0) for col2 in corr['columns']]
                    for col1 in corr['columns']
                ],
            }

        # Distribution bar charts
        if isinstance(results.get('distribution'), dict):
            for col, dist in results['distribution'].items():
                if isinstance(dist, dict) and 'histogram' in dist:
                    hist = dist['histogram']
                    labels = [f"{hist['bin_edges'][i]:.1f}-{hist['bin_edges'][i+1]:.1f}"
                              for i in range(len(hist['counts']))]
                    charts[f'distribution_{col}'] = {
                        'type': 'bar',
                        'labels': labels,
                        'data': hist['counts'],
                        'label': col,
                    }

        # Outlier box plot data
        if 'iqr_method' in results.get('outliers', {}):
            box_data = {}
            for col, info in results['outliers']['iqr_method'].items():
                if isinstance(info, dict) and 'Q1' in info:
                    data = self.df[col].dropna()
                    box_data[col] = {
                        'min': round(float(data.min()), 4),
                        'Q1': info['Q1'],
                        'median': round(float(data.median()), 4),
                        'Q3': info['Q3'],
                        'max': round(float(data.max()), 4),
                        'outlier_count': info['count'],
                    }
            charts['box_plots'] = box_data

        # Scatter plot data (top correlation pairs)
        if 'top_correlations' in results.get('correlation', {}):
            scatter_data = {}
            for tc in results['correlation']['top_correlations'][:3]:
                col1, col2 = tc['col1'], tc['col2']
                pair_data = self.df[[col1, col2]].dropna()
                sample = pair_data.sample(min(200, len(pair_data)), random_state=42)
                scatter_data[f'{col1}_vs_{col2}'] = {
                    'x': [round(float(v), 4) for v in sample[col1].tolist()],
                    'y': [round(float(v), 4) for v in sample[col2].tolist()],
                    'x_label': col1,
                    'y_label': col2,
                    'correlation': tc['value'],
                }
            charts['scatter_plots'] = scatter_data

        # Trend line charts
        if isinstance(results.get('trends'), dict):
            for col, trend in results['trends'].items():
                if isinstance(trend, dict) and 'recent_values' in trend:
                    charts[f'trend_{col}'] = {
                        'type': 'line',
                        'labels': list(range(len(trend['recent_values']))),
                        'datasets': [
                            {'label': col, 'data': trend['recent_values']},
                            {'label': f'{col} (Moving Avg)', 'data': trend['moving_average']},
                        ],
                    }

        return charts

    def generate_summary(self, results: dict) -> str:
        """Generate a human-readable summary of the analysis."""
        lines = []
        lines.append(f"📊 Dataset Overview: {self.df.shape[0]} rows × {self.df.shape[1]} columns")
        lines.append(f"   Numeric columns: {len(self.numeric_cols)} | Categorical columns: {len(self.categorical_cols)}")

        # Missing data
        missing = results.get('missing_data', {})
        completeness = missing.get('completeness', 100)
        lines.append(f"\n📋 Data Completeness: {completeness}%")

        # Top correlations
        corr = results.get('correlation', {})
        top_corrs = corr.get('top_correlations', [])
        if top_corrs:
            lines.append(f"\n🔗 Top Correlations:")
            for tc in top_corrs[:3]:
                lines.append(f"   {tc['col1']} ↔ {tc['col2']}: {tc['value']} ({tc['strength']})")

        # Outliers
        outliers = results.get('outliers', {}).get('iqr_method', {})
        if outliers:
            total_outliers = sum(v.get('count', 0) for v in outliers.values() if isinstance(v, dict))
            lines.append(f"\n⚠️ Outliers Detected: {total_outliers} across {len(outliers)} columns")

        # Trends
        trends = results.get('trends', {})
        if trends:
            lines.append(f"\n📈 Trend Analysis:")
            for col, trend in list(trends.items())[:3]:
                if isinstance(trend, dict):
                    lines.append(f"   {col}: {trend.get('direction', 'N/A')} (slope: {trend.get('slope', 0)})")

        return '\n'.join(lines)

    def get_sample_data(self, n: int = 5) -> dict:
        """Return the first n rows as a JSON-safe dictionary for data preview."""
        sample = self.df.head(n)
        # Convert to list-of-dicts, handling numpy types
        records = []
        for _, row in sample.iterrows():
            record = {}
            for col in sample.columns:
                val = row[col]
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (np.integer, np.int64)):
                    record[col] = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    record[col] = round(float(val), 4)
                else:
                    record[col] = str(val)
            records.append(record)
        return {
            'columns': list(sample.columns),
            'rows': records,
            'total_rows': int(len(self.df)),
        }

    @staticmethod
    def _correlation_strength(value: float) -> str:
        """Classify correlation strength."""
        abs_val = abs(value)
        if abs_val >= 0.8:
            return 'Very Strong'
        elif abs_val >= 0.6:
            return 'Strong'
        elif abs_val >= 0.4:
            return 'Moderate'
        elif abs_val >= 0.3:
            return 'Weak'
        return 'Very Weak'
