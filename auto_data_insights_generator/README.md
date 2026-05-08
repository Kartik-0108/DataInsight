# 🚀 Auto Data Insights Generator

**AI-Powered Mini Data Analyst System**

A web-based application that allows users to upload datasets (CSV or Excel) and automatically generates meaningful insights, visualizations, and reports using data analysis techniques and artificial intelligence.

## ✨ Features

- **📁 Data Upload** — Drag-and-drop CSV/Excel upload with automatic parsing
- **📊 Automated Analysis** — Trend detection, correlation analysis, anomaly detection
- **📉 Data Visualization** — Line charts, bar charts, heatmaps, box plots via Chart.js
- **🤖 AI-Powered Insights** — Natural language summaries via Google Gemini API
- **📄 Report Generation** — Downloadable PDF reports with stats, charts & insights
- **🧠 Smart Query** — Ask questions about your data (optional advanced feature)

## 🏗️ Architecture

```
Frontend (HTML, CSS, JavaScript)
        ↓
Django Backend (REST APIs, Business Logic)
        ↓
PostgreSQL / SQLite Database
        ↓
Data Processing Layer (Pandas, NumPy)
        ↓
AI Engine (Google Gemini)
        ↓
Report Generator (ReportLab)
```

## 🛠️ Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Frontend         | HTML, CSS, JavaScript, Chart.js     |
| Backend          | Django, Django REST Framework        |
| Database         | SQLite (dev) / PostgreSQL (prod)    |
| Data Processing  | Pandas, NumPy                       |
| ML & Analysis    | Scikit-learn                        |
| AI/NLP           | Google Gemini API                   |
| Reports          | ReportLab                           |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# Clone and navigate
cd auto_data_insights_generator

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env with your settings and API keys

# Run migrations
cd backend
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to get started.

## 📂 Project Structure

```
auto_data_insights_generator/
├── frontend/          # Static frontend (HTML/CSS/JS)
├── backend/           # Django project & apps
│   ├── apps/
│   │   ├── users/           # Authentication & profiles
│   │   ├── data_upload/     # Dataset upload & management
│   │   ├── data_analysis/   # Statistical analysis engine
│   │   ├── ai_insights/     # AI-powered insight generation
│   │   └── reports/         # PDF report generation
│   └── templates/           # Global templates
├── data/              # Uploaded & processed datasets
├── docs/              # Documentation
└── tests/             # Test suites
```

## 📄 License

This project is for educational and portfolio purposes.
