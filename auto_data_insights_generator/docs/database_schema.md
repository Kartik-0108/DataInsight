# Database Schema

## ER Diagram

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────────┐
│     User     │     │   UploadedDataset  │     │  AnalysisResult  │
│ (Django Auth)│     │                    │     │                  │
├──────────────┤     ├────────────────────┤     ├──────────────────┤
│ id (PK)      │──┐  │ id (PK)            │──┐  │ id (PK)          │
│ username     │  │  │ user (FK→User)     │  │  │ dataset (FK)     │
│ email        │  │  │ name               │  │  │ analysis_type    │
│ password     │  │  │ description        │  │  │ results (JSON)   │
└──────────────┘  │  │ file               │  │  │ summary          │
                  │  │ file_type          │  │  │ charts_data(JSON)│
┌──────────────┐  │  │ file_size          │  │  │ created_at       │
│  UserProfile │  │  │ row_count          │  │  └──────────────────┘
├──────────────┤  │  │ column_count       │  │
│ id (PK)      │  │  │ columns (JSON)     │  │  ┌──────────────────┐
│ user (FK)  ──┘  │  │ status             │  ├──│    AIInsight     │
│ bio          │  │  │ uploaded_at        │  │  ├──────────────────┤
│ profile_pic  │  │  │ updated_at         │  │  │ id (PK)          │
│ role         │  │  └────────────────────┘  │  │ dataset (FK)     │
│ organization │  │                          │  │ title            │
│ created_at   │  │                          │  │ insight_text     │
└──────────────┘  │                          │  │ category         │
                  │                          │  │ confidence       │
                  │  ┌────────────────────┐  │  │ metadata (JSON)  │
                  │  │      Report        │  │  │ created_at       │
                  │  ├────────────────────┤  │  └──────────────────┘
                  │  │ id (PK)            │  │
                  └──│ dataset (FK)     ──┘  │
                     │ title              │
                     │ file               │
                     │ format             │
                     │ file_size          │
                     │ includes_analysis  │
                     │ includes_insights  │
                     │ created_at         │
                     └────────────────────┘
```

## Model Details

### UserProfile
| Field           | Type          | Description                     |
|-----------------|---------------|---------------------------------|
| user            | OneToOne(User)| Links to Django auth User       |
| bio             | TextField     | User biography                  |
| profile_picture | ImageField    | Avatar image                    |
| role            | CharField     | analyst/manager/viewer/admin    |
| organization    | CharField     | Company or team name            |

### UploadedDataset
| Field        | Type          | Description                       |
|--------------|---------------|-----------------------------------|
| user         | FK(User)      | Owner of the dataset              |
| name         | CharField     | Display name                      |
| file         | FileField     | Uploaded CSV/Excel file           |
| file_type    | CharField     | csv or excel                      |
| row_count    | Integer       | Number of rows                    |
| column_count | Integer       | Number of columns                 |
| columns      | JSONField     | List of column names              |
| status       | CharField     | pending/processing/completed/failed|

### AnalysisResult
| Field         | Type          | Description                      |
|---------------|---------------|----------------------------------|
| dataset       | FK(Dataset)   | Analyzed dataset                 |
| analysis_type | CharField     | descriptive/correlation/full etc |
| results       | JSONField     | Full analysis output             |
| summary       | TextField     | Human-readable summary           |
| charts_data   | JSONField     | Chart.js configuration           |

### AIInsight
| Field        | Type          | Description                       |
|--------------|---------------|-----------------------------------|
| dataset      | FK(Dataset)   | Source dataset                    |
| title        | CharField     | Insight headline                  |
| insight_text | TextField     | Full insight explanation          |
| category     | CharField     | trend/correlation/anomaly/etc     |
| confidence   | FloatField    | 0-1 confidence score              |

### Report
| Field             | Type          | Description                  |
|-------------------|---------------|------------------------------|
| dataset           | FK(Dataset)   | Source dataset               |
| title             | CharField     | Report title                 |
| file              | FileField     | Generated PDF                |
| format            | CharField     | pdf                          |
| includes_analysis | Boolean       | Contains analysis data       |
| includes_insights | Boolean       | Contains AI insights         |
