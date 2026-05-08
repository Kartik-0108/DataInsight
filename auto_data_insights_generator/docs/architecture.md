# System Architecture

## Overview

The Auto Data Insights Generator is a full-stack web application built with Django and vanilla HTML/CSS/JS. It processes uploaded datasets through a multi-stage pipeline: parsing → analysis → AI insights → report generation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend Layer                       │
│   HTML/CSS/JS  ·  Chart.js  ·  Drag & Drop Upload       │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / REST API
┌───────────────────────▼─────────────────────────────────┐
│                   Django Backend                         │
│ ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│ │   Users      │ │ Data Upload  │ │  Data Analysis     │ │
│ │   App        │ │ App          │ │  App               │ │
│ │ - Auth       │ │ - CSV/Excel  │ │ - AnalysisEngine   │ │
│ │ - Profiles   │ │ - Parsing    │ │ - Pandas/NumPy     │ │
│ │ - Sessions   │ │ - Validation │ │ - Scikit-learn     │ │
│ └─────────────┘ └──────────────┘ └────────────────────┘ │
│ ┌──────────────────────┐ ┌─────────────────────────────┐│
│ │   AI Insights App     │ │     Reports App             ││
│ │ - Gemini API          │ │ - ReportLab PDF             ││
│ │ - Rule-based fallback │ │ - Statistics tables         ││
│ │ - Smart Query NLP     │ │ - AI insight summaries      ││
│ └──────────────────────┘ └─────────────────────────────┘│
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Data Layer                             │
│   SQLite (dev) / PostgreSQL (prod)                       │
│   File Storage: /media/datasets/ · /media/reports/       │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Upload** → User uploads CSV/Excel via drag-and-drop
2. **Parse** → Pandas reads file, extracts metadata (rows, cols, types)
3. **Analyze** → AnalysisEngine runs: descriptive stats, correlation, outliers, trends, distributions
4. **Visualize** → Chart.js renders interactive charts from analysis JSON
5. **AI Insights** → NLPInsightGenerator (Gemini API or rule-based) generates natural-language insights
6. **Report** → ReportGenerator creates styled PDF with all results

## App Responsibilities

| App              | Purpose                                              |
|------------------|------------------------------------------------------|
| `users`          | Authentication, profile management, roles            |
| `data_upload`    | File upload, validation, metadata extraction         |
| `data_analysis`  | Statistical analysis engine, chart data generation   |
| `ai_insights`    | AI-powered insights, smart query system              |
| `reports`        | PDF report generation and download                   |
