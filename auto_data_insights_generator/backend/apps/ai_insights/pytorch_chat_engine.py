"""
PyTorch NLP Chat Engine - Data Analyst Assistant
LSTM-based intent classifier with hybrid response generation.
"""
import os, json, re, hashlib, collections, difflib
import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

try:
    from nltk.stem.porter import PorterStemmer
    _stemmer = PorterStemmer()
except Exception:
    _stemmer = None

# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------
def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())

def stem(word):
    if _stemmer:
        return _stemmer.stem(word)
    return word.lower()

def bag_of_words(tokens, vocab):
    stems = [stem(w) for w in tokens]
    return np.array([1.0 if v in stems else 0.0 for v in vocab], dtype=np.float32)

def extract_column_entity(text, columns):
    """Find the best-matching column name in a user query."""
    if not columns:
        return None
    text_lower = text.lower()
    # Exact substring match first
    for col in columns:
        if col.lower() in text_lower:
            return col
    # Fuzzy match on individual words
    tokens = re.findall(r"[a-zA-Z0-9_]+", text_lower)
    col_lower_map = {c.lower(): c for c in columns}
    for token in tokens:
        matches = difflib.get_close_matches(token, col_lower_map.keys(), n=1, cutoff=0.7)
        if matches:
            return col_lower_map[matches[0]]
    return None

# ---------------------------------------------------------------------------
# Training data
# ---------------------------------------------------------------------------
INTENT_DATA = {
    "overview": [
        "give me an overview", "summarize the data", "describe this dataset",
        "tell me about the data", "what is this dataset", "dataset summary",
        "show me a summary", "what does the data look like", "overview of data",
        "general information", "brief summary", "data description",
        "what can you tell me", "explain the dataset", "data overview please",
        "how big is the dataset", "dataset info", "show dataset details",
    ],
    "correlation": [
        "what are the correlations", "show correlations", "which variables are related",
        "relationship between columns", "correlation analysis", "are any columns correlated",
        "which features depend on each other", "connected variables", "correlation matrix",
        "strongest relationship", "how are variables related", "dependency analysis",
        "what impacts what", "related features", "association between variables",
        "which columns move together", "pairwise correlation", "feature relationships",
    ],
    "outlier": [
        "show me the outliers", "any anomalies", "unusual data points",
        "extreme values", "detect outliers", "weird values", "strange data",
        "anomaly detection", "find unusual patterns", "data anomalies",
        "outlier report", "which values are extreme", "abnormal data",
        "are there any outliers", "show anomalies", "extreme observations",
        "data points that dont fit", "suspicious values", "unexpected values",
    ],
    "trend": [
        "what are the trends", "show trends", "is revenue increasing",
        "why is revenue decreasing", "growth pattern", "declining values",
        "trend analysis", "increasing or decreasing", "direction of change",
        "upward trend", "downward trend", "slope analysis", "time series trend",
        "which has the steepest trend", "highest slope", "trend direction",
        "is there a pattern", "data movement over time", "trajectory",
    ],
    "missing_data": [
        "any missing values", "data quality", "incomplete data", "null values",
        "missing data report", "how clean is the data", "empty cells",
        "data completeness", "which columns have gaps", "missing information",
        "are there nulls", "data integrity", "incomplete records",
        "how much data is missing", "quality assessment", "data gaps",
    ],
    "distribution": [
        "what is the distribution", "show distributions", "is data normal",
        "skewness analysis", "data spread", "histogram analysis",
        "distribution shape", "how is data distributed", "normality test",
        "bell curve", "skewed data", "kurtosis", "distribution of values",
        "data range and spread", "frequency distribution", "value distribution",
    ],
    "statistics": [
        "show statistics", "what is the mean", "average values",
        "max and min", "standard deviation", "descriptive statistics",
        "median values", "data range", "statistical summary",
        "key numbers", "numeric summary", "central tendency",
        "show me the numbers", "basic stats", "variance analysis",
        "quantile values", "percentiles", "count and average",
    ],
    "feature_importance": [
        "which feature impacts sales the most", "most important variable",
        "feature importance", "key drivers", "what affects revenue",
        "which column matters most", "predictive features", "main factors",
        "what drives the outcome", "strongest predictor", "important variables",
        "which features are significant", "key influencers", "impact analysis",
    ],
    "comparison": [
        "compare columns", "difference between", "which is higher",
        "compare values", "contrast variables", "side by side comparison",
        "how do they differ", "column comparison", "versus analysis",
        "which one is better", "compare categories", "relative performance",
    ],
    "recommendation": [
        "what should I do", "any recommendations", "suggest next steps",
        "how to improve", "what action to take", "advice on data",
        "best approach", "suggestions please", "recommended actions",
        "what do you recommend", "improvement ideas", "optimization tips",
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon",
        "howdy", "greetings", "hi there", "hey there", "whats up",
    ],
    "help": [
        "help", "what can you do", "how to use", "available commands",
        "show options", "menu", "guide me", "instructions", "capabilities",
        "what questions can I ask", "how does this work", "usage guide",
    ],
    "data_shape": [
        "how many rows", "how many columns", "dataset size", "shape of data",
        "number of records", "how large is the data", "row count", "column count",
        "dimensions of the dataset", "how many entries", "total records",
    ],
    "sample_data": [
        "show me sample data", "preview the data", "first few rows",
        "head of the dataset", "example rows", "show raw data",
        "what does the data look like", "display some records", "data preview",
        "show me some rows", "sample records", "top rows",
    ],
    "column_list": [
        "list the columns", "what columns are there", "show columns",
        "column names", "what fields exist", "available columns",
        "which variables", "feature names", "all columns", "show fields",
    ],
    "specific_stat": [
        "tell me about column", "stats for", "details on",
        "what is the average of", "mean of", "max of", "min of",
        "standard deviation of", "info about", "describe column",
        "statistics for", "breakdown of", "analyze column",
    ],
}

# ---------------------------------------------------------------------------
# PyTorch model
# ---------------------------------------------------------------------------
class IntentDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.from_numpy(X)
        self.y = torch.from_numpy(y).long()
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

class IntentClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.bn2 = nn.BatchNorm1d(hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        x = self.dropout(self.relu(self.bn1(self.fc1(x))))
        x = self.dropout(self.relu(self.bn2(self.fc2(x))))
        return self.fc3(x)

# ---------------------------------------------------------------------------
# Conversation memory
# ---------------------------------------------------------------------------
class ConversationMemory:
    def __init__(self, max_turns=10):
        self._sessions = {}
        self._max = max_turns
        self._focus_column = {}  # tracks last discussed column per session

    def add(self, session_id, role, text):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append({"role": role, "text": text})
        self._sessions[session_id] = self._sessions[session_id][-self._max * 2:]

    def get(self, session_id):
        return self._sessions.get(session_id, [])

    def set_focus_column(self, session_id, col):
        if col:
            self._focus_column[session_id] = col

    def get_focus_column(self, session_id):
        return self._focus_column.get(session_id)

    def clear(self, session_id):
        self._sessions.pop(session_id, None)
        self._focus_column.pop(session_id, None)

# ---------------------------------------------------------------------------
# Main chatbot
# ---------------------------------------------------------------------------
class DataAnalystChatBot:
    """PyTorch-powered data analyst assistant."""

    def __init__(self, model_dir="media/nlp_model"):
        self.model_dir = model_dir
        self.model = None
        self.vocab = None
        self.intents = None
        self.memory = ConversationMemory()
        self._ensure_model()

    # -- model lifecycle --
    def _ensure_model(self):
        os.makedirs(self.model_dir, exist_ok=True)
        model_path = os.path.join(self.model_dir, "intent_model.pth")
        if os.path.exists(model_path):
            try:
                self._load_model(model_path)
                return
            except Exception:
                pass
        self._train_and_save(model_path)

    def _build_vocab(self):
        all_words = []
        for patterns in INTENT_DATA.values():
            for p in patterns:
                all_words.extend([stem(w) for w in tokenize(p)])
        ignore = {"?", "!", ".", ",", "'", '"'}
        vocab = sorted(set(w for w in all_words if w not in ignore))
        return vocab

    def _train_and_save(self, path):
        print("[NLP] Training intent classifier...")
        self.intents = list(INTENT_DATA.keys())
        self.vocab = self._build_vocab()

        X_train, y_train = [], []
        for idx, intent in enumerate(self.intents):
            for pattern in INTENT_DATA[intent]:
                bow = bag_of_words(tokenize(pattern), self.vocab)
                X_train.append(bow)
                y_train.append(idx)

        X_train = np.array(X_train)
        y_train = np.array(y_train)

        dataset = IntentDataset(X_train, y_train)
        loader = DataLoader(dataset, batch_size=16, shuffle=True)

        input_size = len(self.vocab)
        hidden_size = 128
        num_classes = len(self.intents)

        self.model = IntentClassifier(input_size, hidden_size, num_classes)
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

        self.model.train()
        for epoch in range(200):
            total_loss = 0
            for X_batch, y_batch in loader:
                out = self.model(X_batch)
                loss = criterion(out, y_batch)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            if (epoch + 1) % 50 == 0:
                print(f"  epoch {epoch+1}/200  loss={total_loss/len(loader):.4f}")

        torch.save({
            "model_state": self.model.state_dict(),
            "input_size": input_size,
            "hidden_size": hidden_size,
            "num_classes": num_classes,
            "vocab": self.vocab,
            "intents": self.intents,
        }, path)
        self.model.eval()
        print("[NLP] Model trained and saved.")

    def _load_model(self, path):
        data = torch.load(path, map_location="cpu", weights_only=False)
        self.vocab = data["vocab"]
        self.intents = data["intents"]
        self.model = IntentClassifier(data["input_size"], data["hidden_size"], data["num_classes"])
        self.model.load_state_dict(data["model_state"])
        self.model.eval()

    # -- classification --
    def classify_intent(self, text):
        tokens = tokenize(text)
        bow = bag_of_words(tokens, self.vocab)
        inp = torch.from_numpy(bow).unsqueeze(0)
        with torch.no_grad():
            output = self.model(inp)
            probs = torch.softmax(output, dim=1)
            confidence, idx = torch.max(probs, dim=1)
        return self.intents[idx.item()], confidence.item()

    # -- public API --
    def chat(self, question, analysis_results, dataset_name="Dataset", session_id="default"):
        self.memory.add(session_id, "user", question)
        intent, confidence = self.classify_intent(question)
        context = self.memory.get(session_id)

        # Extract column entity from the question
        all_columns = list(analysis_results.get("descriptive_stats", {}).get("numeric", {}).keys()) + \
                      list(analysis_results.get("descriptive_stats", {}).get("categorical", {}).keys())
        col_entity = extract_column_entity(question, all_columns)
        if col_entity:
            self.memory.set_focus_column(session_id, col_entity)
        focus_col = self.memory.get_focus_column(session_id)

        if confidence < 0.35:
            answer = self._fallback_response(question, dataset_name)
            suggested_actions = []
        else:
            answer, suggested_actions = self._generate_response(
                intent, confidence, question, analysis_results, dataset_name, context, focus_col
            )

        self.memory.add(session_id, "bot", answer)
        return {
            "answer": answer,
            "intent": intent,
            "confidence": round(confidence, 3),
            "context_turns": len(context) // 2,
            "focus_column": focus_col,
            "suggested_actions": suggested_actions,
        }

    def get_history(self, session_id):
        return self.memory.get(session_id)

    # -- response generation --
    def _generate_response(self, intent, confidence, question, ar, name, ctx, focus_col):
        handlers = {
            "overview": self._resp_overview,
            "correlation": self._resp_correlation,
            "outlier": self._resp_outlier,
            "trend": self._resp_trend,
            "missing_data": self._resp_missing,
            "distribution": self._resp_distribution,
            "statistics": self._resp_statistics,
            "feature_importance": self._resp_feature_importance,
            "comparison": self._resp_comparison,
            "recommendation": self._resp_recommendation,
            "greeting": self._resp_greeting,
            "help": self._resp_help,
            "data_shape": self._resp_data_shape,
            "sample_data": self._resp_sample_data,
            "column_list": self._resp_column_list,
            "specific_stat": self._resp_specific_stat,
        }
        handler = handlers.get(intent, self._resp_help)
        return handler(ar, name, question, ctx, focus_col)

    # -- individual response handlers --
    def _resp_overview(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        shape = ds.get("shape", {})
        missing = ar.get("missing_data", {})
        corr = ar.get("correlation", {})
        rows = shape.get("rows", "?")
        cols = shape.get("columns", "?")
        comp = missing.get("completeness", 100)
        num_c = len(ds.get("numeric", {}))
        cat_c = len(ds.get("categorical", {}))
        tc = corr.get("top_correlations", [])
        corr_line = ""
        if tc:
            c = tc[0]
            corr_line = f"\n\n**Strongest relationship:** {c['col1']} and {c['col2']} (r={c['value']:.2f}, {c.get('strength','')})."
        answer = (
            f"**Dataset Overview: {name}**\n\n"
            f"Your dataset contains **{rows:,} rows** and **{cols} columns** "
            f"({num_c} numeric, {cat_c} categorical).\n\n"
            f"**Data completeness:** {comp}%{corr_line}\n\n"
            f"Ask me about correlations, trends, outliers, or statistics for deeper analysis!"
        )
        return answer, ["Show correlations", "Show trends", "Any outliers?"]

    def _resp_correlation(self, ar, name, q, ctx, focus_col):
        corr = ar.get("correlation", {})
        tc = corr.get("top_correlations", [])
        if not tc:
            return "No significant correlations were found between numeric columns in your dataset.", []
        lines = ["**Correlation Analysis**\n", "Here are the strongest relationships found:\n"]
        for i, c in enumerate(tc[:5], 1):
            d = "move together" if c["value"] > 0 else "move oppositely"
            strength = c.get("strength", "")
            lines.append(f"{i}. **{c['col1']}** <-> **{c['col2']}**: r={c['value']:.3f} ({strength} - they {d})")
        if abs(tc[0]["value"]) > 0.7:
            lines.append(f"\n**Key insight:** The {tc[0]['col1']}-{tc[0]['col2']} relationship is strong enough for predictive modeling.")
        else:
            lines.append(f"\n**Note:** No correlation exceeds 0.7, so relationships are moderate at best.")
        return "\n".join(lines), ["Show outliers", "Feature importance", "Recommendations"]

    def _resp_outlier(self, ar, name, q, ctx, focus_col):
        iqr = ar.get("outliers", {}).get("iqr_method", {})
        cols = [(k, v) for k, v in iqr.items() if isinstance(v, dict) and v.get("count", 0) > 0]
        if not cols:
            return "No significant outliers were detected - your data looks clean!", []
        total = sum(v["count"] for _, v in cols)
        lines = [f"**Outlier Report** - {total} unusual values found\n"]
        for col, d in sorted(cols, key=lambda x: x[1]["percentage"], reverse=True):
            pct = d["percentage"]
            sev = "HIGH" if pct > 10 else "MEDIUM" if pct > 5 else "LOW"
            lines.append(f"- **{col}**: {d['count']} outliers ({pct}%) [{sev}] - bounds: [{d['lower_bound']:.1f}, {d['upper_bound']:.1f}]")
        lines.append(f"\n**Tip:** Columns with >10% outliers may indicate data quality issues. Values below 5% are usually normal variation.")
        return "\n".join(lines), ["Show distributions", "Recommendations", "Data quality"]

    def _resp_trend(self, ar, name, q, ctx, focus_col):
        trends = ar.get("trends", {})
        valid = [(c, t) for c, t in trends.items() if isinstance(t, dict) and "direction" in t]
        if not valid:
            return "No significant trends were detected in this dataset.", []
        valid.sort(key=lambda x: abs(x[1].get("slope", 0)), reverse=True)
        lines = ["**Trend Analysis**\n", "Variables ranked by strength of directional movement:\n"]
        for i, (col, t) in enumerate(valid, 1):
            d = t["direction"]
            s = t.get("slope", 0)
            icon = "(+)" if d == "increasing" else "(-)" if d == "decreasing" else "(=)"
            lines.append(f"{i}. {icon} **{col}**: {d} (slope: {s:.4f})")

        # Check if question asks "why"
        if "why" in q.lower():
            winner = valid[0]
            corr = ar.get("correlation", {}).get("top_correlations", [])
            related = [c for c in corr if winner[0] in (c["col1"], c["col2"])]
            if related:
                r = related[0]
                other = r["col2"] if r["col1"] == winner[0] else r["col1"]
                lines.append(f"\n**Possible explanation:** {winner[0]} is correlated with {other} (r={r['value']:.2f}). Changes in {other} may be driving this trend.")
            else:
                lines.append(f"\n**Note:** No strong correlations found to explain the {winner[1]['direction']} trend in {winner[0]}. External factors may be involved.")

        best = valid[0]
        lines.append(f"\n**Steepest change:** {best[0]} with a slope of {best[1].get('slope', 0):.4f}")
        return "\n".join(lines), ["Show correlations", "Feature importance", "Recommendations"]

    def _resp_missing(self, ar, name, q, ctx, focus_col):
        missing = ar.get("missing_data", {})
        comp = missing.get("completeness", 100)
        cols = missing.get("columns_with_missing", {})
        if not cols:
            return f"Your dataset is **100% complete** - no missing values found anywhere!", []
        lines = [f"**Data Quality Report** - {comp}% complete\n"]
        for col, info in sorted(cols.items(), key=lambda x: x[1].get("percentage", 0), reverse=True):
            pct = info.get("percentage", 0)
            sev = "CRITICAL" if pct > 20 else "WARNING" if pct > 5 else "OK"
            lines.append(f"- **{col}**: {info.get('count', 0)} missing ({pct}%) [{sev}]")
        lines.append(f"\n**Recommendation:** Fill gaps using median values for numeric columns or mode for categorical columns.")
        return "\n".join(lines), ["Show outliers", "Recommendations"]

    def _resp_distribution(self, ar, name, q, ctx, focus_col):
        dist = ar.get("distribution", {})
        if not dist:
            return "No distribution data available. Please run the full analysis first.", []
        lines = ["**Distribution Analysis**\n"]
        for col, d in list(dist.items())[:6]:
            if not isinstance(d, dict):
                continue
            skew = d.get("skewness", 0)
            kurt = d.get("kurtosis", 0)
            if abs(skew) > 1:
                label = "Highly skewed"
            elif abs(skew) > 0.5:
                label = "Moderately skewed"
            else:
                label = "Nearly normal"
            lines.append(f"- **{col}**: {label} (skewness: {skew:.2f}, kurtosis: {kurt:.2f})")
        lines.append(f"\n**Tip:** Skewness > 1 means data is heavily lopsided. Consider log-transformation for better modeling.")
        return "\n".join(lines), ["Show statistics", "Show outliers"]

    def _resp_statistics(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        ns = ds.get("numeric", {})
        if not ns:
            return "No numeric statistics available yet. Please run the analysis first.", []
        lines = ["**Key Statistics**\n"]
        for col, s in list(ns.items())[:8]:
            if not isinstance(s, dict):
                continue
            try:
                mean = float(s.get("mean", 0))
                med = float(s.get("50%", s.get("median", 0)))
                mn = float(s.get("min", 0))
                mx = float(s.get("max", 0))
                std = float(s.get("std", 0))
                lines.append(f"- **{col}**: avg={mean:.1f}, median={med:.1f}, range=[{mn:.1f}, {mx:.1f}], std={std:.1f}")
            except (ValueError, TypeError):
                lines.append(f"- **{col}**: mean={s.get('mean')}, min={s.get('min')}, max={s.get('max')}")
        lines.append(f"\n**Tip:** When mean differs significantly from median, the data is skewed and median is more reliable.")
        return "\n".join(lines), ["Show distributions", "Compare columns"]

    def _resp_feature_importance(self, ar, name, q, ctx, focus_col):
        corr = ar.get("correlation", {}).get("top_correlations", [])
        trends = ar.get("trends", {})
        if not corr and not trends:
            return "Not enough data to determine feature importance. Run analysis first.", []
        lines = ["**Feature Importance Analysis**\n"]
        if corr:
            lines.append("Based on correlation strength, the most impactful relationships are:\n")
            for i, c in enumerate(corr[:5], 1):
                imp = "HIGH" if abs(c["value"]) > 0.6 else "MEDIUM" if abs(c["value"]) > 0.3 else "LOW"
                lines.append(f"{i}. **{c['col1']}** -> **{c['col2']}**: impact={imp} (r={c['value']:.3f})")
        if trends:
            valid = [(c, t) for c, t in trends.items() if isinstance(t, dict) and "slope" in t]
            if valid:
                valid.sort(key=lambda x: abs(x[1]["slope"]), reverse=True)
                lines.append(f"\n**Most dynamic variable:** {valid[0][0]} (slope: {valid[0][1]['slope']:.4f})")
        lines.append(f"\n**Note:** True feature importance requires a trained predictive model. These rankings are based on statistical correlation and trend strength.")
        return "\n".join(lines), ["Show correlations", "Recommendations"]

    def _resp_comparison(self, ar, name, q, ctx, focus_col):
        ns = ar.get("descriptive_stats", {}).get("numeric", {})
        if not ns or len(ns) < 2:
            return "Need at least 2 numeric columns for comparison.", []
        lines = ["**Column Comparison**\n"]
        lines.append(f"{'Column':<20} {'Mean':>12} {'Std':>12} {'Min':>12} {'Max':>12}")
        lines.append("-" * 70)
        for col, s in list(ns.items())[:8]:
            if isinstance(s, dict):
                try:
                    lines.append(f"**{col:<18}** {float(s.get('mean',0)):>12.1f} {float(s.get('std',0)):>12.1f} {float(s.get('min',0)):>12.1f} {float(s.get('max',0)):>12.1f}")
                except (ValueError, TypeError):
                    pass
        return "\n".join(lines), ["Show distributions", "Recommendations"]

    def _resp_recommendation(self, ar, name, q, ctx, focus_col):
        recs = []
        missing = ar.get("missing_data", {})
        if missing.get("total_missing_cells", 0) > 0:
            recs.append("**Data cleaning:** Handle missing values using imputation before modeling.")
        iqr = ar.get("outliers", {}).get("iqr_method", {})
        high_outliers = [k for k, v in iqr.items() if isinstance(v, dict) and v.get("percentage", 0) > 10]
        if high_outliers:
            recs.append(f"**Outlier treatment:** Investigate high outlier rates in: {', '.join(high_outliers)}.")
        corr = ar.get("correlation", {}).get("top_correlations", [])
        strong = [c for c in corr if abs(c["value"]) > 0.7]
        if strong:
            recs.append(f"**Multicollinearity warning:** Highly correlated features ({strong[0]['col1']}, {strong[0]['col2']}) may cause issues in regression models. Consider removing one.")
        dist = ar.get("distribution", {})
        skewed = [k for k, v in dist.items() if isinstance(v, dict) and abs(v.get("skewness", 0)) > 1]
        if skewed:
            recs.append(f"**Transform skewed data:** Apply log/sqrt transformation to: {', '.join(skewed[:3])}.")
        if not recs:
            recs.append("Your dataset looks clean and well-structured. You can proceed directly to modeling!")
        answer = "**Recommendations for Your Dataset**\n\n" + "\n\n".join(f"{i}. {r}" for i, r in enumerate(recs, 1))
        return answer, ["Overview", "Show statistics"]

    def _resp_greeting(self, ar, name, q, ctx, focus_col):
        turn_count = len(ctx) // 2
        if turn_count > 1:
            return f"Welcome back! We've had {turn_count} exchanges so far. What else would you like to know about **{name}**?", []
        return f"Hello! I'm your AI data analyst assistant. I've analyzed **{name}** and I'm ready to answer your questions.\n\nTry asking about trends, correlations, outliers, or statistics!", ["Give me an overview", "Show trends", "List columns"]

    def _resp_help(self, ar, name, q, ctx, focus_col):
        answer = (
            "**I can help you explore your data!**\n\n"
            "Here are some things you can ask:\n\n"
            "- **\"Give me an overview\"** - dataset summary\n"
            "- **\"What are the correlations?\"** - variable relationships\n"
            "- **\"Show me the trends\"** - increasing/decreasing patterns\n"
            "- **\"Are there any outliers?\"** - unusual data points\n"
            "- **\"What is the data quality?\"** - missing values report\n"
            "- **\"Show me the statistics\"** - mean, median, range\n"
            "- **\"Which feature impacts sales?\"** - feature importance\n"
            "- **\"What should I do?\"** - recommendations\n"
            "- **\"List the columns\"** - see all variables\n"
            "- **\"Show sample data\"** - preview raw data\n"
            "- **\"Tell me about [column]\"** - column-specific stats\n\n"
            f"Try one of these to explore **{name}**!"
        )
        return answer, ["Overview", "Show trends", "List columns"]

    # -- new handlers --
    def _resp_data_shape(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        shape = ds.get("shape", {})
        rows = shape.get("rows", "?")
        cols = shape.get("columns", "?")
        num_c = len(ds.get("numeric", {}))
        cat_c = len(ds.get("categorical", {}))
        answer = (
            f"**Dataset Dimensions: {name}**\n\n"
            f"- **Rows:** {rows:,}\n"
            f"- **Columns:** {cols} ({num_c} numeric, {cat_c} categorical)\n"
            f"- **Total cells:** {rows * cols if isinstance(rows, int) and isinstance(cols, int) else '?':,}"
        )
        return answer, ["Show statistics", "List columns", "Sample data"]

    def _resp_sample_data(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        all_cols = list(ds.get("numeric", {}).keys()) + list(ds.get("categorical", {}).keys())
        if not all_cols:
            return "No data columns found. Run analysis first.", []
        ns = ds.get("numeric", {})
        lines = ["**Data Preview (from statistics)**\n"]
        lines.append("| Column | Mean | Min | Max |")
        lines.append("|--------|------|-----|-----|")
        for col, s in list(ns.items())[:8]:
            if isinstance(s, dict):
                try:
                    lines.append(f"| {col} | {float(s.get('mean',0)):.2f} | {float(s.get('min',0)):.2f} | {float(s.get('max',0)):.2f} |")
                except (ValueError, TypeError):
                    lines.append(f"| {col} | {s.get('mean')} | {s.get('min')} | {s.get('max')} |")
        cat = ds.get("categorical", {})
        if cat:
            lines.append(f"\n**Categorical columns:** {', '.join(list(cat.keys())[:5])}")
        return "\n".join(lines), ["Show statistics", "Overview"]

    def _resp_column_list(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        num_cols = list(ds.get("numeric", {}).keys())
        cat_cols = list(ds.get("categorical", {}).keys())
        lines = [f"**Columns in {name}**\n"]
        if num_cols:
            lines.append(f"**Numeric ({len(num_cols)}):** {', '.join(num_cols)}")
        if cat_cols:
            lines.append(f"**Categorical ({len(cat_cols)}):** {', '.join(cat_cols)}")
        if not num_cols and not cat_cols:
            return "No column information available. Run analysis first.", []
        suggestions = [f"Stats for {num_cols[0]}"] if num_cols else []
        suggestions.append("Show statistics")
        return "\n".join(lines), suggestions

    def _resp_specific_stat(self, ar, name, q, ctx, focus_col):
        ds = ar.get("descriptive_stats", {})
        ns = ds.get("numeric", {})
        cat = ds.get("categorical", {})
        col = focus_col
        if not col:
            return "Which column would you like details on? Try: **\"Tell me about [column name]\"**", ["List columns"]
        # Numeric column
        if col in ns and isinstance(ns[col], dict):
            s = ns[col]
            try:
                lines = [f"**Column Deep-Dive: {col}**\n"]
                mean = float(s.get("mean", 0))
                med = float(s.get("50%", s.get("median", 0)))
                mn = float(s.get("min", 0))
                mx = float(s.get("max", 0))
                std = float(s.get("std", 0))
                lines.append(f"| Metric | Value |")
                lines.append(f"|--------|-------|")
                lines.append(f"| Mean | {mean:.2f} |")
                lines.append(f"| Median | {med:.2f} |")
                lines.append(f"| Std Dev | {std:.2f} |")
                lines.append(f"| Min | {mn:.2f} |")
                lines.append(f"| Max | {mx:.2f} |")
                # Add distribution info if available
                dist = ar.get("distribution", {}).get(col, {})
                if dist and isinstance(dist, dict):
                    skew = dist.get("skewness", 0)
                    lines.append(f"| Skewness | {skew:.2f} |")
                # Add outlier info if available
                iqr = ar.get("outliers", {}).get("iqr_method", {}).get(col, {})
                if iqr and isinstance(iqr, dict):
                    lines.append(f"| Outliers | {iqr.get('count', 0)} ({iqr.get('percentage', 0)}%) |")
                return "\n".join(lines), [f"Outliers for {col}", f"Trends for {col}", "Compare columns"]
            except (ValueError, TypeError):
                pass
        # Categorical column
        if col in cat and isinstance(cat[col], dict):
            c = cat[col]
            lines = [f"**Column Deep-Dive: {col}** (categorical)\n"]
            lines.append(f"- **Unique values:** {c.get('unique_count', '?')}")
            lines.append(f"- **Mode:** {c.get('mode', '?')}")
            top = c.get("top_values", {})
            if top:
                lines.append(f"\n**Top values:**")
                for val, count in list(top.items())[:5]:
                    lines.append(f"- {val}: {count}")
            return "\n".join(lines), ["Overview", "Show statistics"]
        return f"Column **{col}** not found in the analysis results. Use **\"List columns\"** to see available columns.", ["List columns"]

    def _fallback_response(self, question, name):
        return (
            f"I'm not quite sure what you're asking about. My confidence was too low to give a reliable answer.\n\n"
            f"Try rephrasing, or ask one of these:\n"
            f"- \"Show me the trends\"\n"
            f"- \"What are the correlations?\"\n"
            f"- \"Are there outliers?\"\n"
            f"- \"Give me an overview\"\n\n"
            f"I'm here to help you understand **{name}**!"
        )


# Singleton for the Django process
_chatbot_instance = None

def get_chatbot():
    global _chatbot_instance
    if not TORCH_AVAILABLE:
        return None
    if _chatbot_instance is None:
        _chatbot_instance = DataAnalystChatBot()
    return _chatbot_instance
