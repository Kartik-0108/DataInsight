"""
Report Generator
Generates styled PDF reports using ReportLab with analysis results,
embedded matplotlib charts, and AI insights.
"""
import io
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportGenerator:
    """Generates professional PDF reports from analysis data."""

    PRIMARY = colors.HexColor('#6366f1')
    SECONDARY = colors.HexColor('#f472b6')
    DARK = colors.HexColor('#0f172a')
    LIGHT_BG = colors.HexColor('#f1f5f9')
    TEXT_COLOR = colors.HexColor('#1e293b')
    MUTED = colors.HexColor('#64748b')

    # Matplotlib colors matching the brand palette
    MPL_PRIMARY = '#6366f1'
    MPL_SECONDARY = '#f472b6'
    MPL_ACCENT = '#22d3ee'
    MPL_BG = '#f8fafc'

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            'ReportTitle', parent=self.styles['Heading1'],
            fontSize=24, textColor=self.PRIMARY, spaceAfter=20, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            'SectionTitle', parent=self.styles['Heading2'],
            fontSize=16, textColor=self.PRIMARY, spaceBefore=20, spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            'SubSection', parent=self.styles['Heading3'],
            fontSize=12, textColor=self.TEXT_COLOR, spaceBefore=12, spaceAfter=6,
        ))
        # Override the built-in 'BodyText' style instead of adding a duplicate
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].textColor = self.TEXT_COLOR
        self.styles['BodyText'].spaceAfter = 6
        self.styles['BodyText'].leading = 14
        self.styles.add(ParagraphStyle(
            'InsightText', parent=self.styles['Normal'],
            fontSize=10, textColor=self.TEXT_COLOR, spaceAfter=8, leftIndent=15, leading=14,
        ))
        self.styles.add(ParagraphStyle(
            'FooterStyle', parent=self.styles['Normal'],
            fontSize=8, textColor=self.MUTED, alignment=TA_CENTER,
        ))

    # ───────────────────────────────────────
    # Main entry point
    # ───────────────────────────────────────

    def generate(self, dataset_name: str, analysis_results: dict,
                 insights: list, output_path: str) -> str:
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=25*mm, bottomMargin=20*mm,
        )

        story = []
        story.extend(self._build_title_page(dataset_name))
        story.append(PageBreak())
        story.extend(self._build_toc())
        story.append(Spacer(1, 20))
        story.extend(self._build_overview_section(analysis_results))
        story.extend(self._build_statistics_section(analysis_results))
        story.extend(self._build_correlation_section(analysis_results))
        story.extend(self._build_outlier_section(analysis_results))
        story.extend(self._build_trend_section(analysis_results))
        story.extend(self._build_insights_section(insights))

        # Footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", color=self.MUTED))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f'Report generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")} | Auto Data Insights Generator',
            self.styles['FooterStyle']
        ))
        doc.build(story)
        return output_path

    # ───────────────────────────────────────
    # Chart helpers (matplotlib → BytesIO)
    # ───────────────────────────────────────

    def _fig_to_image(self, fig, width=5.5*inch, height=3*inch):
        """Convert a matplotlib figure to a ReportLab Image flowable."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor=self.MPL_BG, edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=width, height=height)

    def _make_distribution_chart(self, numeric_stats: dict):
        """Bar chart of mean values across numeric columns."""
        cols = list(numeric_stats.keys())[:8]
        means = [numeric_stats[c].get('mean', 0) for c in cols]

        fig, ax = plt.subplots(figsize=(7, 3.5))
        bars = ax.bar(range(len(cols)), means, color=self.MPL_PRIMARY, edgecolor='white', linewidth=0.5)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(cols, rotation=30, ha='right', fontsize=8)
        ax.set_ylabel('Mean Value', fontsize=9)
        ax.set_title('Mean Values Across Variables', fontsize=11, fontweight='bold', color='#1e293b')
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        return self._fig_to_image(fig)

    def _make_correlation_heatmap(self, correlation: dict):
        """Heatmap of top correlations."""
        top_corrs = correlation.get('top_correlations', [])
        if not top_corrs:
            return None

        # Build a small matrix from the top pairs
        all_cols = list(set(c['col1'] for c in top_corrs[:8]) | set(c['col2'] for c in top_corrs[:8]))
        all_cols = all_cols[:6]  # limit
        n = len(all_cols)
        matrix = np.eye(n)
        col_idx = {c: i for i, c in enumerate(all_cols)}

        for c in top_corrs:
            if c['col1'] in col_idx and c['col2'] in col_idx:
                i, j = col_idx[c['col1']], col_idx[c['col2']]
                matrix[i][j] = c['value']
                matrix[j][i] = c['value']

        fig, ax = plt.subplots(figsize=(5, 4))
        im = ax.imshow(matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(all_cols, rotation=45, ha='right', fontsize=7)
        ax.set_yticklabels(all_cols, fontsize=7)
        # Add values
        for i in range(n):
            for j in range(n):
                color = 'white' if abs(matrix[i][j]) > 0.5 else 'black'
                ax.text(j, i, f'{matrix[i][j]:.2f}', ha='center', va='center', fontsize=7, color=color)
        ax.set_title('Correlation Heatmap', fontsize=11, fontweight='bold', color='#1e293b')
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        return self._fig_to_image(fig, width=4.5*inch, height=3.5*inch)

    def _make_trend_chart(self, trends: dict):
        """Line chart showing trend slopes."""
        trend_items = [(col, t) for col, t in trends.items()
                       if isinstance(t, dict) and 'slope' in t]
        if not trend_items:
            return None

        trend_items.sort(key=lambda x: abs(x[1]['slope']), reverse=True)
        trend_items = trend_items[:8]

        cols = [t[0] for t in trend_items]
        slopes = [t[1]['slope'] for t in trend_items]
        bar_colors = [self.MPL_PRIMARY if s >= 0 else self.MPL_SECONDARY for s in slopes]

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.barh(range(len(cols)), slopes, color=bar_colors, edgecolor='white', linewidth=0.5)
        ax.set_yticks(range(len(cols)))
        ax.set_yticklabels(cols, fontsize=8)
        ax.set_xlabel('Slope', fontsize=9)
        ax.set_title('Trend Slopes by Variable', fontsize=11, fontweight='bold', color='#1e293b')
        ax.axvline(x=0, color='#94a3b8', linewidth=0.5)
        ax.grid(axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.tight_layout()
        return self._fig_to_image(fig)

    # ───────────────────────────────────────
    # Page builders
    # ───────────────────────────────────────

    def _build_title_page(self, dataset_name: str) -> list:
        elements = []
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph('Data Analysis Report', self.styles['ReportTitle']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(dataset_name, ParagraphStyle(
            'DatasetName', parent=self.styles['Heading2'],
            alignment=TA_CENTER, textColor=self.MUTED, fontSize=14
        )))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f'Generated: {datetime.now().strftime("%B %d, %Y")}',
            ParagraphStyle('DateStyle', parent=self.styles['Normal'],
                           alignment=TA_CENTER, textColor=self.MUTED, fontSize=10)
        ))
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="60%", color=self.PRIMARY, thickness=2))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(
            'Automated analysis powered by AI - Auto Data Insights Generator',
            ParagraphStyle('Tagline', parent=self.styles['Normal'],
                           alignment=TA_CENTER, textColor=self.MUTED, fontSize=9)
        ))
        return elements

    def _build_toc(self) -> list:
        elements = []
        elements.append(Paragraph('Table of Contents', self.styles['SectionTitle']))
        for item in [
            '1. Dataset Overview', '2. Descriptive Statistics',
            '3. Correlation Analysis', '4. Outlier Detection',
            '5. Trend Analysis', '6. AI-Generated Insights',
        ]:
            elements.append(Paragraph(item, self.styles['BodyText']))
        return elements

    def _build_overview_section(self, results: dict) -> list:
        elements = []
        elements.append(Paragraph('1. Dataset Overview', self.styles['SectionTitle']))
        desc = results.get('descriptive_stats', {})
        shape = desc.get('shape', {})
        missing = results.get('missing_data', {})

        data = [
            ['Metric', 'Value'],
            ['Total Rows', str(shape.get('rows', 'N/A'))],
            ['Total Columns', str(shape.get('columns', 'N/A'))],
            ['Data Completeness', f"{missing.get('completeness', 100)}%"],
            ['Total Missing Cells', str(missing.get('total_missing_cells', 0))],
        ]
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.LIGHT_BG),
            ('GRID', (0, 0), (-1, -1), 0.5, self.MUTED),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        return elements

    def _build_statistics_section(self, results: dict) -> list:
        elements = []
        elements.append(Paragraph('2. Descriptive Statistics', self.styles['SectionTitle']))
        desc = results.get('descriptive_stats', {})
        numeric = desc.get('numeric', desc.get('numeric_stats', {}))

        if numeric:
            # Chart
            try:
                chart_img = self._make_distribution_chart(numeric)
                elements.append(chart_img)
                elements.append(Spacer(1, 10))
            except Exception:
                pass

            # Table
            cols = list(numeric.keys())[:6]
            stat_keys = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
            header = ['Statistic'] + cols
            data = [header]
            for key in stat_keys:
                row = [key]
                for col in cols:
                    val = numeric.get(col, {}).get(key, 'N/A')
                    if isinstance(val, float):
                        val = f"{val:.2f}"
                    row.append(str(val))
                data.append(row)

            col_width = min(6*inch / len(header), 1.5*inch)
            table = Table(data, colWidths=[1*inch] + [col_width]*len(cols))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, self.MUTED),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph('No numeric statistics available.', self.styles['BodyText']))

        elements.append(Spacer(1, 10))
        return elements

    def _build_correlation_section(self, results: dict) -> list:
        elements = []
        elements.append(Paragraph('3. Correlation Analysis', self.styles['SectionTitle']))
        corr = results.get('correlation', {})
        top_corrs = corr.get('top_correlations', [])

        # Chart
        try:
            heatmap = self._make_correlation_heatmap(corr)
            if heatmap:
                elements.append(heatmap)
                elements.append(Spacer(1, 10))
        except Exception:
            pass

        if top_corrs:
            data = [['Variable 1', 'Variable 2', 'Correlation', 'Strength']]
            for c in top_corrs[:8]:
                data.append([c['col1'], c['col2'], f"{c['value']:.4f}", c['strength']])

            table = Table(data, colWidths=[1.8*inch, 1.8*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, self.MUTED),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph(
                corr.get('message', 'No significant correlations found.'), self.styles['BodyText']
            ))

        elements.append(Spacer(1, 10))
        return elements

    def _build_outlier_section(self, results: dict) -> list:
        elements = []
        elements.append(Paragraph('4. Outlier Detection', self.styles['SectionTitle']))
        outliers = results.get('outliers', {})
        iqr = outliers.get('iqr_method', {})

        if iqr:
            data = [['Column', 'Outliers', 'Percentage', 'Lower Bound', 'Upper Bound']]
            for col, info in iqr.items():
                if isinstance(info, dict) and 'count' in info:
                    data.append([
                        col, str(info['count']), f"{info['percentage']}%",
                        f"{info['lower_bound']:.2f}", f"{info['upper_bound']:.2f}",
                    ])

            if len(data) > 1:
                table = Table(data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.25*inch, 1.25*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.MUTED),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(table)
        else:
            elements.append(Paragraph('No outlier data available.', self.styles['BodyText']))

        iso = outliers.get('isolation_forest', {})
        if iso and 'total_outliers' in iso:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(
                f'<b>Isolation Forest:</b> Detected {iso["total_outliers"]} multivariate outliers ({iso["percentage"]}% of data)',
                self.styles['BodyText']
            ))

        elements.append(Spacer(1, 10))
        return elements

    def _build_trend_section(self, results: dict) -> list:
        elements = []
        elements.append(Paragraph('5. Trend Analysis', self.styles['SectionTitle']))
        trends = results.get('trends', {})

        # Chart
        try:
            trend_chart = self._make_trend_chart(trends)
            if trend_chart:
                elements.append(trend_chart)
                elements.append(Spacer(1, 10))
        except Exception:
            pass

        if trends:
            for col, trend in trends.items():
                if isinstance(trend, dict):
                    direction = trend.get('direction', 'N/A')
                    slope = trend.get('slope', 0)
                    icon = 'UP' if direction == 'increasing' else 'DOWN' if direction == 'decreasing' else 'FLAT'
                    elements.append(Paragraph(
                        f'[{icon}] <b>{col}</b>: {direction.capitalize()} trend (slope: {slope:.6f})',
                        self.styles['BodyText']
                    ))
        else:
            elements.append(Paragraph('No trend data available.', self.styles['BodyText']))

        elements.append(Spacer(1, 10))
        return elements

    def _build_insights_section(self, insights: list) -> list:
        elements = []
        elements.append(Paragraph('6. AI-Generated Insights', self.styles['SectionTitle']))

        if insights:
            icons = {'trend': '[TREND]', 'correlation': '[CORR]', 'anomaly': '[ALERT]',
                     'recommendation': '[TIP]', 'summary': '[INFO]'}
            for i, insight in enumerate(insights, 1):
                title = insight.get('title', f'Insight {i}')
                text = insight.get('insight_text', '')
                category = insight.get('category', 'summary')
                confidence = insight.get('confidence', 0)

                icon = icons.get(category, '[INFO]')
                elements.append(Paragraph(
                    f'{icon} <b>{title}</b> <font color="#64748b">(Confidence: {confidence:.0%})</font>',
                    self.styles['SubSection']
                ))
                elements.append(Paragraph(text, self.styles['InsightText']))
                elements.append(Spacer(1, 4))
        else:
            elements.append(Paragraph(
                'No insights available. Generate insights from the insights page.',
                self.styles['BodyText']
            ))

        return elements
