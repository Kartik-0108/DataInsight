"""
Automated Data Visualization Engine
Uses Pandas, NumPy, and Matplotlib to auto-generate comprehensive visualizations.
"""
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")
matplotlib.rcParams.update({
    "figure.facecolor": "#0f0f1a",
    "axes.facecolor": "#1a1a2e",
    "axes.edgecolor": "#444466",
    "axes.labelcolor": "#c8c8e8",
    "xtick.color": "#9999bb",
    "ytick.color": "#9999bb",
    "text.color": "#e0e0f0",
    "grid.color": "#2a2a4a",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "figure.titlesize": 15,
    "axes.titlesize": 13,
    "axes.labelsize": 10,
    "legend.facecolor": "#1a1a2e",
    "legend.edgecolor": "#444466",
    "font.family": "DejaVu Sans",
})

PALETTE = ["#7c5cbf", "#5b8dee", "#3ecf8e", "#f7b731", "#fc5c65",
           "#fd9644", "#45aaf2", "#26de81", "#a55eea", "#fd79a8"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_color(n: int):
    return [PALETTE[i % len(PALETTE)] for i in range(n)]


def _savefig(fig, save_dir: str, name: str):
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f"{name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        print(f"  [saved] {path}")


# ---------------------------------------------------------------------------
# Main Class
# ---------------------------------------------------------------------------

class AutomatedVisualizer:
    """
    Loads, preprocesses, and auto-generates Matplotlib visualizations for any
    CSV or Excel dataset.

    Usage
    -----
    viz = AutomatedVisualizer.from_file("data.csv")
    viz.generate_all_insights(save_dir="plots/", show=True)
    """

    # ------------------------------------------------------------------ init
    def __init__(self, df: pd.DataFrame):
        self.raw_df = df.copy()
        self.df = self._preprocess(df)
        self._classify_columns()

    # ---------------------------------------------------------- class methods
    @classmethod
    def from_file(cls, path: str) -> "AutomatedVisualizer":
        ext = os.path.splitext(path)[-1].lower()
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        print(f"[load] {os.path.basename(path)}: {df.shape[0]} rows × {df.shape[1]} cols")
        return cls(df)

    # ----------------------------------------------------------- preprocessing
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        if before != after:
            print(f"[preprocess] Removed {before - after} duplicate rows.")

        # Try to parse object columns as datetime
        for col in df.select_dtypes(include="object").columns:
            try:
                parsed = pd.to_datetime(df[col], infer_datetime_format=True)
                if parsed.notna().sum() > 0.8 * len(df):
                    df[col] = parsed
            except Exception:
                pass

        # Impute missing values
        for col in df.columns:
            n_missing = df[col].isna().sum()
            if n_missing == 0:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)
                print(f"[preprocess] '{col}': filled {n_missing} NaN with median.")
            elif pd.api.types.is_object_dtype(df[col]):
                mode = df[col].mode()
                df[col].fillna(mode.iloc[0] if not mode.empty else "Unknown", inplace=True)
                print(f"[preprocess] '{col}': filled {n_missing} NaN with mode.")
        return df

    def _classify_columns(self):
        self.numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
        self.cat_cols = self.df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.dt_cols = self.df.select_dtypes(include="datetime64").columns.tolist()

    # ------------------------------------------------------------------ plots

    def plot_line(self, save_dir="", show=True):
        """Line plot — numeric columns over an index or datetime axis."""
        if not self.numeric_cols:
            return
        x_col = self.dt_cols[0] if self.dt_cols else None
        cols = self.numeric_cols[:4]
        fig, ax = plt.subplots(figsize=(11, 5))
        for i, col in enumerate(cols):
            x = self.df[x_col] if x_col else np.arange(len(self.df))
            ax.plot(x, self.df[col], color=PALETTE[i], linewidth=2, label=col, alpha=0.9)
        ax.set_title("Line Plot — Trends Over Time")
        ax.set_xlabel(x_col or "Index")
        ax.legend()
        ax.grid(True)
        fig.tight_layout()
        print("\n[insight] Line Plot:")
        for col in cols:
            slope = float(np.polyfit(np.arange(len(self.df)), self.df[col].values, 1)[0])
            direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            print(f"  {col}: {direction} (slope={slope:.4f})")
        _savefig(fig, save_dir, "line_plot")
        if show: plt.show()
        plt.close(fig)

    def plot_bar(self, save_dir="", show=True):
        """Bar chart — top categories vs a numeric column."""
        if not self.cat_cols or not self.numeric_cols:
            return
        cat, num = self.cat_cols[0], self.numeric_cols[0]
        grouped = self.df.groupby(cat)[num].mean().nlargest(12)
        fig, ax = plt.subplots(figsize=(11, 5))
        bars = ax.bar(grouped.index.astype(str), grouped.values,
                      color=_safe_color(len(grouped)), edgecolor="#333355")
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                    f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=8)
        ax.set_title(f"Bar Chart — Mean {num} by {cat}")
        ax.set_xlabel(cat); ax.set_ylabel(f"Mean {num}")
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        top = grouped.idxmax()
        print(f"\n[insight] Bar Chart: Highest mean {num} -> '{top}' ({grouped[top]:.2f})")
        _savefig(fig, save_dir, "bar_chart")
        if show: plt.show()
        plt.close(fig)

    def plot_horizontal_bar(self, save_dir="", show=True):
        """Horizontal bar chart."""
        if not self.cat_cols or not self.numeric_cols:
            return
        cat, num = self.cat_cols[0], self.numeric_cols[0]
        grouped = self.df.groupby(cat)[num].mean().nlargest(10).sort_values()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(grouped.index.astype(str), grouped.values,
                color=_safe_color(len(grouped)), edgecolor="#333355")
        ax.set_title(f"Horizontal Bar — Mean {num} by {cat}")
        ax.set_xlabel(f"Mean {num}")
        fig.tight_layout()
        print(f"\n[insight] Horizontal Bar: '{grouped.idxmax()}' leads in mean {num}.")
        _savefig(fig, save_dir, "horizontal_bar")
        if show: plt.show()
        plt.close(fig)

    def plot_histogram(self, save_dir="", show=True):
        """Histogram — distribution of numeric columns."""
        if not self.numeric_cols:
            return
        cols = self.numeric_cols[:6]
        ncols = min(3, len(cols)); nrows = (len(cols) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
        axes = np.array(axes).flatten()
        for i, col in enumerate(cols):
            data = self.df[col].dropna()
            axes[i].hist(data, bins=20, color=PALETTE[i % len(PALETTE)], edgecolor="#0f0f1a", alpha=0.85)
            axes[i].axvline(data.mean(), color="#f7b731", linestyle="--", linewidth=1.5, label=f"Mean={data.mean():.1f}")
            axes[i].set_title(f"{col} Distribution"); axes[i].legend(fontsize=8)
        for j in range(i + 1, len(axes)): axes[j].set_visible(False)
        fig.suptitle("Histograms — Numeric Distributions", y=1.01)
        fig.tight_layout()
        print("\n[insight] Histograms:")
        for col in cols:
            sk = float(self.df[col].skew())
            skew_str = "right-skewed" if sk > 0.5 else "left-skewed" if sk < -0.5 else "approx. normal"
            print(f"  {col}: {skew_str} (skew={sk:.2f})")
        _savefig(fig, save_dir, "histograms")
        if show: plt.show()
        plt.close(fig)

    def plot_scatter(self, save_dir="", show=True):
        """Scatter plots — top correlated numeric pairs."""
        if len(self.numeric_cols) < 2:
            return
        corr_matrix = self.df[self.numeric_cols].corr().abs()
        pairs = []
        cols = self.numeric_cols
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                pairs.append((cols[i], cols[j], corr_matrix.iloc[i, j]))
        pairs.sort(key=lambda x: x[2], reverse=True)
        pairs = pairs[:4]
        ncols = min(2, len(pairs)); nrows = (len(pairs) + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
        axes = np.array(axes).flatten()
        for i, (c1, c2, r) in enumerate(pairs):
            sample = self.df[[c1, c2]].dropna().sample(min(300, len(self.df)), random_state=42)
            axes[i].scatter(sample[c1], sample[c2], color=PALETTE[i], alpha=0.6, s=20)
            m, b = np.polyfit(sample[c1], sample[c2], 1)
            xl = np.linspace(sample[c1].min(), sample[c1].max(), 100)
            axes[i].plot(xl, m * xl + b, color="#f7b731", linewidth=1.5, linestyle="--")
            axes[i].set_title(f"{c1} vs {c2}  (r={r:.2f})")
            axes[i].set_xlabel(c1); axes[i].set_ylabel(c2)
        for j in range(i + 1, len(axes)): axes[j].set_visible(False)
        fig.suptitle("Scatter Plots — Variable Relationships", y=1.01)
        fig.tight_layout()
        print("\n[insight] Scatter Plots:")
        for c1, c2, r in pairs:
            strength = "strong" if r > 0.6 else "moderate" if r > 0.3 else "weak"
            print(f"  {c1} vs {c2}: r={r:.2f} ({strength})")
        _savefig(fig, save_dir, "scatter_plots")
        if show: plt.show()
        plt.close(fig)

    def plot_pie(self, save_dir="", show=True):
        """Pie charts — categorical columns with few unique values."""
        pie_cols = [c for c in self.cat_cols if self.df[c].nunique() <= 10]
        if not pie_cols:
            print("[skip] Pie chart: no categorical column with <=10 unique values.")
            return
        cols = pie_cols[:4]
        ncols = min(2, len(cols)); nrows = (len(cols) + 1) // 2
        fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
        axes = np.array(axes).flatten()
        for i, col in enumerate(cols):
            vc = self.df[col].value_counts()
            axes[i].pie(vc.values, labels=vc.index.astype(str), autopct="%1.1f%%",
                        colors=_safe_color(len(vc)), startangle=140,
                        wedgeprops={"edgecolor": "#0f0f1a", "linewidth": 1.2})
            axes[i].set_title(f"{col} — Proportions")
        for j in range(i + 1, len(axes)): axes[j].set_visible(False)
        fig.suptitle("Pie Charts — Category Proportions", y=1.01)
        fig.tight_layout()
        print("\n[insight] Pie Charts:")
        for col in cols:
            top = self.df[col].value_counts().idxmax()
            pct = self.df[col].value_counts(normalize=True).max() * 100
            print(f"  {col}: dominant = '{top}' ({pct:.1f}%)")
        _savefig(fig, save_dir, "pie_charts")
        if show: plt.show()
        plt.close(fig)

    def plot_box(self, save_dir="", show=True):
        """Box plots — spread and outliers of numeric columns."""
        if not self.numeric_cols:
            return
        cols = self.numeric_cols[:8]
        fig, ax = plt.subplots(figsize=(max(10, len(cols) * 1.4), 6))
        data = [self.df[c].dropna().values for c in cols]
        bp = ax.boxplot(data, patch_artist=True, notch=False,
                        medianprops={"color": "#f7b731", "linewidth": 2})
        for patch, color in zip(bp["boxes"], _safe_color(len(cols))):
            patch.set_facecolor(color); patch.set_alpha(0.75)
        ax.set_xticks(range(1, len(cols) + 1)); ax.set_xticklabels(cols, rotation=30, ha="right")
        ax.set_title("Box Plots — Distribution & Outliers")
        ax.grid(True, axis="y")
        fig.tight_layout()
        print("\n[insight] Box Plots:")
        for col in cols:
            q1, q3 = self.df[col].quantile([0.25, 0.75])
            iqr = q3 - q1
            out = ((self.df[col] < q1 - 1.5 * iqr) | (self.df[col] > q3 + 1.5 * iqr)).sum()
            print(f"  {col}: IQR={iqr:.2f}, outliers={out}")
        _savefig(fig, save_dir, "box_plots")
        if show: plt.show()
        plt.close(fig)

    def plot_area(self, save_dir="", show=True):
        """Area plot — stacked areas for numeric columns."""
        if not self.numeric_cols:
            return
        cols = self.numeric_cols[:4]
        x_col = self.dt_cols[0] if self.dt_cols else None
        fig, ax = plt.subplots(figsize=(11, 5))
        x = self.df[x_col].values if x_col else np.arange(len(self.df))
        for i, col in enumerate(cols):
            ax.fill_between(x, self.df[col].values, alpha=0.45, color=PALETTE[i], label=col)
            ax.plot(x, self.df[col].values, color=PALETTE[i], linewidth=1.2)
        ax.set_title("Area Plot — Cumulative Trends")
        ax.set_xlabel(x_col or "Index"); ax.legend(); ax.grid(True)
        fig.tight_layout()
        print("\n[insight] Area Plot: shows cumulative coverage for", ", ".join(cols))
        _savefig(fig, save_dir, "area_plot")
        if show: plt.show()
        plt.close(fig)

    def plot_heatmap(self, save_dir="", show=True):
        """Correlation heatmap using Matplotlib imshow (no Seaborn)."""
        if len(self.numeric_cols) < 2:
            return
        corr = self.df[self.numeric_cols].corr().values
        labels = self.numeric_cols
        n = len(labels)
        fig, ax = plt.subplots(figsize=(max(7, n * 0.9), max(6, n * 0.8)))
        cmap = plt.cm.RdYlGn
        im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_xticks(range(n)); ax.set_yticks(range(n))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(labels, fontsize=9)
        for i in range(n):
            for j in range(n):
                val = corr[i, j]
                color = "black" if abs(val) < 0.5 else "white"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)
        ax.set_title("Correlation Heatmap")
        fig.tight_layout()
        # Print top correlations
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((labels[i], labels[j], corr[i, j]))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        print("\n[insight] Heatmap - Top Correlations:")
        for c1, c2, r in pairs[:5]:
            print(f"  {c1} <-> {c2}: r={r:.3f}")
        _savefig(fig, save_dir, "heatmap")
        if show: plt.show()
        plt.close(fig)

    def plot_stacked_bar(self, save_dir="", show=True):
        """Stacked bar chart — two categorical columns or cat + numeric."""
        if len(self.cat_cols) >= 2:
            cat1, cat2 = self.cat_cols[0], self.cat_cols[1]
            pivot = self.df.groupby([cat1, cat2]).size().unstack(fill_value=0)
            title = f"Stacked Bar — {cat1} × {cat2} Counts"
        elif self.cat_cols and self.numeric_cols:
            cat1 = self.cat_cols[0]
            num_cols = self.numeric_cols[:4]
            pivot = self.df.groupby(cat1)[num_cols].mean()
            title = f"Stacked Bar — {cat1} by Numeric Means"
        else:
            return
        pivot = pivot.head(12)
        colors = _safe_color(len(pivot.columns))
        fig, ax = plt.subplots(figsize=(12, 6))
        bottom = np.zeros(len(pivot))
        for i, col in enumerate(pivot.columns):
            ax.bar(pivot.index.astype(str), pivot[col].values,
                   bottom=bottom, label=str(col), color=colors[i], edgecolor="#0f0f1a")
            bottom += pivot[col].values
        ax.set_title(title); ax.legend(loc="upper right", fontsize=8)
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        print(f"\n[insight] Stacked Bar: '{pivot.stack().idxmax()[0]}' has the largest total.")
        _savefig(fig, save_dir, "stacked_bar")
        if show: plt.show()
        plt.close(fig)

    def plot_subplots(self, save_dir="", show=True):
        """Dashboard subplot — combines 6 key charts in one figure."""
        fig = plt.figure(figsize=(18, 14))
        gs = GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.4)

        # 1 — Line / trend (top-left 2 cols)
        ax1 = fig.add_subplot(gs[0, :2])
        if self.numeric_cols:
            for i, col in enumerate(self.numeric_cols[:3]):
                x = np.arange(len(self.df))
                ax1.plot(x, self.df[col].values, color=PALETTE[i], linewidth=1.8, label=col)
            ax1.set_title("Trends"); ax1.legend(fontsize=7); ax1.grid(True)

        # 2 — Pie (top-right)
        ax2 = fig.add_subplot(gs[0, 2])
        pie_cols = [c for c in self.cat_cols if self.df[c].nunique() <= 10]
        if pie_cols:
            vc = self.df[pie_cols[0]].value_counts().head(6)
            ax2.pie(vc.values, labels=vc.index.astype(str), autopct="%1.0f%%",
                    colors=_safe_color(len(vc)), startangle=90,
                    wedgeprops={"edgecolor": "#0f0f1a"})
            ax2.set_title(pie_cols[0])

        # 3 — Histogram (mid-left)
        ax3 = fig.add_subplot(gs[1, 0])
        if self.numeric_cols:
            col = self.numeric_cols[0]
            ax3.hist(self.df[col].dropna(), bins=18, color=PALETTE[0], edgecolor="#0f0f1a", alpha=0.85)
            ax3.set_title(f"{col} Dist"); ax3.grid(True)

        # 4 — Bar (mid-center)
        ax4 = fig.add_subplot(gs[1, 1])
        if self.cat_cols and self.numeric_cols:
            g = self.df.groupby(self.cat_cols[0])[self.numeric_cols[0]].mean().nlargest(8)
            ax4.bar(g.index.astype(str), g.values, color=_safe_color(len(g)))
            ax4.set_title(f"Mean {self.numeric_cols[0]}"); plt.setp(ax4.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)

        # 5 — Scatter (mid-right)
        ax5 = fig.add_subplot(gs[1, 2])
        if len(self.numeric_cols) >= 2:
            c1, c2 = self.numeric_cols[0], self.numeric_cols[1]
            s = self.df[[c1, c2]].dropna().sample(min(200, len(self.df)), random_state=1)
            ax5.scatter(s[c1], s[c2], color=PALETTE[2], alpha=0.55, s=15)
            ax5.set_title(f"{c1} vs {c2}"); ax5.set_xlabel(c1, fontsize=7); ax5.set_ylabel(c2, fontsize=7)

        # 6 — Box plots (bottom full width)
        ax6 = fig.add_subplot(gs[2, :])
        if self.numeric_cols:
            cols = self.numeric_cols[:8]
            data = [self.df[c].dropna().values for c in cols]
            bp = ax6.boxplot(data, patch_artist=True, medianprops={"color": "#f7b731", "linewidth": 1.5})
            for patch, color in zip(bp["boxes"], _safe_color(len(cols))):
                patch.set_facecolor(color); patch.set_alpha(0.7)
            ax6.set_xticks(range(1, len(cols) + 1)); ax6.set_xticklabels(cols, rotation=25, ha="right", fontsize=8)
            ax6.set_title("Box Plots — Spread & Outliers"); ax6.grid(True, axis="y")

        fig.suptitle("Dataset Analysis Dashboard", fontsize=18, fontweight="bold", y=1.01)
        print("\n[insight] Dashboard: Combined overview of trends, distribution, relationships, and outliers.")
        _savefig(fig, save_dir, "dashboard_subplots")
        if show: plt.show()
        plt.close(fig)

    # ------------------------------------------------- auto-insight generator
    def generate_all_insights(self, save_dir: str = "", show: bool = True):
        """
        Auto-detects applicable chart types and generates all relevant plots.

        Parameters
        ----------
        save_dir : str
            Directory to save PNG files. Empty string = don't save.
        show : bool
            Whether to call plt.show() after each plot.
        """
        print("\n" + "=" * 60)
        print(" AUTO DATA INSIGHTS GENERATOR")
        print("=" * 60)
        print(f"Rows: {len(self.df)} | Numeric cols: {len(self.numeric_cols)} "
              f"| Categorical cols: {len(self.cat_cols)} | Datetime cols: {len(self.dt_cols)}")
        print("Numeric  :", self.numeric_cols)
        print("Categoric:", self.cat_cols)
        print("Datetime :", self.dt_cols)
        print("-" * 60)

        generated = []

        if self.numeric_cols:
            print("\n>> Line Plot"); self.plot_line(save_dir, show); generated.append("line")
            print("\n>> Histogram"); self.plot_histogram(save_dir, show); generated.append("histogram")
            print("\n>> Area Plot"); self.plot_area(save_dir, show); generated.append("area")
            print("\n>> Box Plot"); self.plot_box(save_dir, show); generated.append("box")

        if len(self.numeric_cols) >= 2:
            print("\n>> Scatter Plot"); self.plot_scatter(save_dir, show); generated.append("scatter")
            print("\n>> Heatmap"); self.plot_heatmap(save_dir, show); generated.append("heatmap")

        if self.cat_cols and self.numeric_cols:
            print("\n>> Bar Chart"); self.plot_bar(save_dir, show); generated.append("bar")
            print("\n>> Horizontal Bar"); self.plot_horizontal_bar(save_dir, show); generated.append("hbar")
            print("\n>> Stacked Bar"); self.plot_stacked_bar(save_dir, show); generated.append("stacked_bar")

        if self.cat_cols:
            print("\n>> Pie Chart"); self.plot_pie(save_dir, show); generated.append("pie")

        print("\n>> Dashboard Subplots"); self.plot_subplots(save_dir, show); generated.append("subplots")

        print("\n" + "=" * 60)
        print(f" Generated {len(generated)} charts: {', '.join(generated)}")
        if save_dir:
            print(f" Saved to: {os.path.abspath(save_dir)}")
        print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Standalone usage example
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visualization_engine.py <path_to_csv_or_excel> [output_dir]")
        sys.exit(1)
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "plots"
    visualizer = AutomatedVisualizer.from_file(file_path)
    visualizer.generate_all_insights(save_dir=output_dir, show=True)
