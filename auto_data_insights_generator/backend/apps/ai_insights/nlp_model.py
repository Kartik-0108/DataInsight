"""
AI/NLP Model for Generating Data Insights
Enhanced rule-based engine that produces rich, user-friendly natural language
answers from structured analysis results. No external API required.
"""
import json


class NLPInsightGenerator:
    """Generates human-readable insights from data analysis results."""

    def generate_insights(self, analysis_results: dict, dataset_name: str = 'Dataset') -> list:
        """Generate insights from analysis results."""
        return self._generate_rule_based_insights(analysis_results, dataset_name)

    # ──────────────────────────────────────────────
    # INSIGHT GENERATION (for Generate Insights btn)
    # ──────────────────────────────────────────────

    def _generate_rule_based_insights(self, analysis_results: dict, dataset_name: str) -> list:
        """Generate detailed, user-friendly insights using rule-based logic."""
        insights = []
        desc_stats = analysis_results.get('descriptive_stats', {})
        shape = desc_stats.get('shape', {})
        missing = analysis_results.get('missing_data', {})
        correlation = analysis_results.get('correlation', {})
        outliers = analysis_results.get('outliers', {})
        trends = analysis_results.get('trends', {})
        distribution = analysis_results.get('distribution', {})

        # 1 — Dataset overview
        if shape:
            rows = shape.get('rows', 0)
            cols = shape.get('columns', 0)
            size_label = 'large' if rows > 1000 else 'moderate' if rows > 100 else 'small'
            insights.append({
                'title': 'Dataset Overview',
                'insight_text': (
                    f'Your dataset "{dataset_name}" contains {rows:,} records across {cols} variables. '
                    f'This is a {size_label} dataset, which {"provides strong statistical reliability" if rows > 1000 else "is sufficient for initial analysis but larger samples would improve confidence" if rows > 100 else "may be too small for reliable conclusions"}.'
                ),
                'category': 'summary',
                'confidence': 0.95,
            })

        # 2 — Data quality
        completeness = missing.get('completeness', 100)
        cols_missing = missing.get('columns_with_missing', {})
        if cols_missing:
            worst = max(cols_missing.items(), key=lambda x: x[1].get('percentage', 0))
            insights.append({
                'title': '⚠️ Data Quality Issue',
                'insight_text': (
                    f'Overall data completeness is {completeness}%. '
                    f'The column "{worst[0]}" has the most gaps with {worst[1].get("count", 0)} missing values '
                    f'({worst[1].get("percentage", 0)}%). Consider filling these gaps using median imputation '
                    f'or investigating why the data is missing before drawing conclusions.'
                ),
                'category': 'recommendation',
                'confidence': 0.9,
            })
        else:
            insights.append({
                'title': '✅ Perfect Data Quality',
                'insight_text': (
                    'Great news — your dataset has 100% completeness with zero missing values. '
                    'This means every analysis result is based on the full dataset, giving you maximum reliability.'
                ),
                'category': 'summary',
                'confidence': 0.95,
            })

        # 3 — Top correlation
        top_corrs = correlation.get('top_correlations', [])
        if top_corrs:
            best = top_corrs[0]
            val = best['value']
            direction = 'positive' if val > 0 else 'negative'
            strength = best.get('strength', 'Strong')
            insights.append({
                'title': f'🔗 {strength} Correlation: {best["col1"]} ↔ {best["col2"]}',
                'insight_text': (
                    f'A {strength.lower()} {direction} correlation of {val:.2f} was found between '
                    f'"{best["col1"]}" and "{best["col2"]}". This means when {best["col1"]} '
                    f'{"goes up" if val > 0 else "goes down"}, {best["col2"]} tends to '
                    f'{"go up" if val > 0 else "go down"} as well. '
                    f'{"This is a very strong relationship — consider using one to predict the other." if abs(val) > 0.7 else "This relationship is notable but not strong enough alone for prediction."}'
                ),
                'category': 'correlation',
                'confidence': min(abs(val), 0.95),
            })

        # 4 — Outliers
        iqr = outliers.get('iqr_method', {})
        outlier_cols = [(k, v) for k, v in iqr.items() if isinstance(v, dict) and v.get('count', 0) > 0]
        if outlier_cols:
            total = sum(v['count'] for _, v in outlier_cols)
            worst = max(outlier_cols, key=lambda x: x[1]['percentage'])
            insights.append({
                'title': f'⚡ {total} Outliers Found',
                'insight_text': (
                    f'{total} unusual data points were detected across {len(outlier_cols)} columns. '
                    f'The column "{worst[0]}" has the highest outlier rate at {worst[1]["percentage"]}% '
                    f'({worst[1]["count"]} values). These could be data entry errors, rare events, '
                    f'or genuinely extreme values worth investigating individually.'
                ),
                'category': 'anomaly',
                'confidence': 0.85,
            })

        # 5 — Trends
        if trends:
            for col, trend in list(trends.items())[:2]:
                if isinstance(trend, dict) and 'direction' in trend:
                    d = trend['direction']
                    slope = trend.get('slope') or 0
                    emoji = '📈' if d == 'increasing' else '📉' if d == 'decreasing' else '➡️'
                    insights.append({
                        'title': f'{emoji} {d.capitalize()} Trend in {col}',
                        'insight_text': (
                            f'"{col}" shows a clear {d} pattern (slope: {slope:.4f}). '
                            f'{"This upward movement suggests growth or escalation over the observed period. Monitor this closely for acceleration." if d == "increasing" else "This downward movement could indicate improvement or decline depending on context. Investigate the cause." if d == "decreasing" else "Values are relatively stable with no significant directional change."}'
                        ),
                        'category': 'trend',
                        'confidence': 0.75,
                    })

        # 6 — Distribution skew
        for col, dist in list(distribution.items())[:1]:
            if isinstance(dist, dict) and abs(dist.get('skewness', 0)) > 1:
                skew = dist['skewness']
                direction = 'right (many low values, few high)' if skew > 0 else 'left (many high values, few low)'
                insights.append({
                    'title': f'📊 Skewed Distribution: {col}',
                    'insight_text': (
                        f'"{col}" has a skewness of {skew:.2f}, meaning the data leans to the {direction}. '
                        f'Standard averages may be misleading — consider using the median instead of the mean '
                        f'for more accurate analysis of this variable.'
                    ),
                    'category': 'recommendation',
                    'confidence': 0.8,
                })

        return insights

    # ──────────────────────────────────────────────
    # SMART QUERY (for Ask button)
    # ──────────────────────────────────────────────

    def ask_question(self, question: str, analysis_results: dict, dataset_name: str) -> str:
        """Answer a natural language question about the data using intelligent rule matching."""
        return self._answer_smart(question, analysis_results, dataset_name)

    def _answer_smart(self, question: str, analysis_results: dict, dataset_name: str) -> str:
        """Produce a rich, user-friendly answer to common data questions."""
        q = question.lower().strip()
        desc_stats = analysis_results.get('descriptive_stats', {})
        correlation = analysis_results.get('correlation', {})
        outliers = analysis_results.get('outliers', {})
        missing = analysis_results.get('missing_data', {})
        trends = analysis_results.get('trends', {})
        distribution = analysis_results.get('distribution', {})
        numeric_stats = desc_stats.get('numeric_stats', desc_stats.get('numeric', {}))
        shape = desc_stats.get('shape', {})

        # ── Overview / summary ──
        if any(kw in q for kw in ['overview', 'summary', 'describe', 'about', 'tell me', 'what is this']):
            rows = shape.get('rows', '?')
            cols = shape.get('columns', '?')
            completeness = missing.get('completeness', '?')
            top_corrs = correlation.get('top_correlations', [])
            corr_summary = ''
            if top_corrs:
                c = top_corrs[0]
                corr_summary = f'\n\n🔗 **Strongest relationship:** {c["col1"]} and {c["col2"]} have a {c.get("strength", "notable").lower()} correlation of {c["value"]:.2f}.'
            return (
                f'📊 **Dataset Summary: {dataset_name}**\n\n'
                f'Your dataset has **{rows} rows** and **{cols} columns** with '
                f'**{completeness}% data completeness**.\n'
                f'{corr_summary}\n\n'
                f'Ask me about specific topics like "correlations", "trends", "outliers", or "statistics" for deeper analysis!'
            )

        # ── Correlation ──
        if any(kw in q for kw in ['correlation', 'correlat', 'relationship', 'related', 'connect', 'depend']):
            top_corrs = correlation.get('top_correlations', [])
            if top_corrs:
                lines = ['🔗 **Correlation Analysis**\n',
                         'Here are the strongest relationships found between your variables:\n']
                for i, c in enumerate(top_corrs[:5], 1):
                    direction = '↑ together' if c['value'] > 0 else '↓ opposite'
                    bar = '█' * int(abs(c['value']) * 10)
                    lines.append(f'{i}. **{c["col1"]}** ↔ **{c["col2"]}**: `{c["value"]:.2f}` ({c.get("strength", "")} — {direction}) {bar}')
                lines.append(f'\n💡 **What this means:** Variables with correlation > 0.7 move strongly together. Consider using the stronger pairs for prediction models.')
                return '\n'.join(lines)
            return '🔍 No significant correlations were found between numeric columns in your dataset.'

        # ── Outliers ──
        if any(kw in q for kw in ['outlier', 'anomal', 'unusual', 'extreme', 'weird', 'strange']):
            iqr = outliers.get('iqr_method', {})
            outlier_cols = [(k, v) for k, v in iqr.items() if isinstance(v, dict) and v.get('count', 0) > 0]
            if outlier_cols:
                total = sum(v['count'] for _, v in outlier_cols)
                lines = [f'⚡ **Outlier Report** — {total} unusual values found\n']
                for col, data in sorted(outlier_cols, key=lambda x: x[1]['percentage'], reverse=True):
                    pct = data['percentage']
                    severity = '🔴' if pct > 10 else '🟡' if pct > 5 else '🟢'
                    lines.append(f'{severity} **{col}**: {data["count"]} outliers ({pct}%)')
                lines.append(f'\n💡 **Tip:** Outliers above 10% (🔴) may indicate data quality issues. Values below 5% (🟢) are usually normal variation.')
                return '\n'.join(lines)
            return '✅ No significant outliers were detected — your data looks clean!'

        # ── Trends ──
        if any(kw in q for kw in ['trend', 'increasing', 'decreasing', 'growth', 'decline', 'direction', 'slope', 'highest slope']):
            if trends:
                sorted_trends = sorted(
                    [(col, t) for col, t in trends.items() if isinstance(t, dict) and 'direction' in t],
                    key=lambda x: abs(x[1].get('slope') or 0),
                    reverse=True
                )
                if sorted_trends:
                    lines = ['📈 **Trend Analysis**\n',
                             'Variables ranked by the strength of their directional movement:\n']
                    for i, (col, trend) in enumerate(sorted_trends, 1):
                        d = trend['direction']
                        slope = trend.get('slope') or 0
                        emoji = '📈' if d == 'increasing' else '📉' if d == 'decreasing' else '➡️'
                        lines.append(f'{i}. {emoji} **{col}**: {d} (slope: {slope:.4f})')
                    winner = sorted_trends[0]
                    slope_val = winner[1].get("slope") or 0
                    lines.append(f'\n🏆 **Steepest change:** "{winner[0]}" with a slope of {slope_val:.4f}')
                    return '\n'.join(lines)
            return '📊 No significant trends were detected in this dataset.'

        # ── Missing data / quality ──
        if any(kw in q for kw in ['missing', 'null', 'empty', 'incomplete', 'quality', 'clean']):
            completeness = missing.get('completeness', 100)
            cols_missing = missing.get('columns_with_missing', {})
            if cols_missing:
                lines = [f'📋 **Data Quality Report** — {completeness}% complete\n']
                for col, info in sorted(cols_missing.items(), key=lambda x: x[1].get('percentage', 0), reverse=True):
                    pct = info.get('percentage', 0)
                    severity = '🔴' if pct > 20 else '🟡' if pct > 5 else '🟢'
                    lines.append(f'{severity} **{col}**: {info.get("count", 0)} missing ({pct}%)')
                lines.append(f'\n💡 **Recommendation:** Fill gaps using median values for numeric columns or mode for categorical columns.')
                return '\n'.join(lines)
            return f'✅ Your dataset is **100% complete** — no missing values found anywhere. Great data quality!'

        # ── Distribution ──
        if any(kw in q for kw in ['distribution', 'skew', 'normal', 'spread', 'shape']):
            if distribution:
                lines = ['📊 **Distribution Analysis**\n']
                for col, dist in list(distribution.items())[:6]:
                    if isinstance(dist, dict):
                        skew = dist.get('skewness', 0)
                        kurt = dist.get('kurtosis', 0)
                        label = '⚠️ Highly skewed' if abs(skew) > 1 else '📐 Moderately skewed' if abs(skew) > 0.5 else '✅ Nearly normal'
                        lines.append(f'• **{col}**: {label} (skewness: {skew:.2f}, kurtosis: {kurt:.2f})')
                lines.append(f'\n💡 **Tip:** Skewness > 1 means the data is heavily lopsided. Consider log-transformation for better modeling.')
                return '\n'.join(lines)
            return 'No distribution data is available. Try running the full analysis first.'

        # ── Statistics / mean / max / min ──
        if any(kw in q for kw in ['mean', 'average', 'max', 'min', 'statistic', 'stat', 'median', 'std', 'range', 'number']):
            if numeric_stats:
                lines = ['📐 **Key Statistics**\n']
                for col, stats in list(numeric_stats.items())[:6]:
                    if isinstance(stats, dict):
                        mean = stats.get('mean', 0)
                        median = stats.get('50%', stats.get('median', 0))
                        mn = stats.get('min', 0)
                        mx = stats.get('max', 0)
                        std = stats.get('std', 0)
                        try:
                            lines.append(
                                f'• **{col}**: avg = {float(mean):.1f}, median = {float(median):.1f}, '
                                f'range = {float(mn):.1f} → {float(mx):.1f}, std = {float(std):.1f}'
                            )
                        except (ValueError, TypeError):
                            lines.append(f'• **{col}**: mean={mean}, min={mn}, max={mx}')
                lines.append(f'\n💡 **Tip:** When mean ≠ median, the data is skewed. The median is more reliable in those cases.')
                return '\n'.join(lines)
            return 'No numeric statistics are available yet. Please run the analysis first.'

        # ── Catch-all: helpful fallback ──
        return (
            f'🤖 **I can help you explore your data!**\n\n'
            f'Here are some questions I can answer:\n\n'
            f'• **"Give me an overview"** — dataset summary\n'
            f'• **"What are the correlations?"** — relationship between variables\n'
            f'• **"Show me the trends"** — increasing/decreasing patterns\n'
            f'• **"Are there any outliers?"** — unusual data points\n'
            f'• **"What is the data quality?"** — missing values report\n'
            f'• **"Show me the statistics"** — mean, median, range for all columns\n'
            f'• **"What about distributions?"** — skewness and normality\n'
            f'• **"Which has the highest slope?"** — strongest trend\n\n'
            f'💡 Try one of these to explore your "{dataset_name}" dataset!'
        )
