# Coach Matcher

A Python tool for intelligently matching debate coaches to student groups for tournaments based on historical drill sessions, recency, coverage, and coach specialties.

## Overview

Coach Matcher analyzes past coaching sessions to recommend the best coaches for a specific group of students at an upcoming tournament. It uses a weighted scoring system that considers:

- **Recency**: How recently coaches worked with group students (with exponential decay)
- **Volume**: Total number of sessions with group members
- **Coverage**: Percentage of group students the coach has worked with
- **Minutes**: Total coaching time with group members
- **Specialty**: Coach's expertise match with the event type and overall rating

## Features

- Multi-factor scoring algorithm with customizable weights
- Time-decay recency scoring with configurable half-life
- Student coverage analysis across the group
- Event specialty matching (LD, PF, CX, etc.)
- Detailed scoring breakdowns for transparency

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Required Python Packages

```bash
pip install pandas numpy
```

Or create a `requirements.txt` file:

```txt
pandas>=1.3.0
numpy>=1.21.0
```

Then install with:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python coach_matcher.py \
    --drills drills_log.csv \
    --roster group_roster.csv \
    --coaches coaches.csv \
    --tournament "Greenhill 2025" \
    --event "LD" \
    --output recommendations.csv
```

### Advanced Usage with Custom Parameters

```bash
python coach_matcher.py \
    --drills drills_log.csv \
    --roster group_roster.csv \
    --coaches coaches.csv \
    --tournament "Greenhill 2025" \
    --event "LD" \
    --output recommendations.csv \
    --as_of 2025-08-20 \
    --half_life_days 45 \
    --min_sessions 2 \
    --weights '{"recency":0.5,"volume":0.25,"coverage":0.15,"minutes":0.05,"specialty":0.05}' \
    --debug
```

## Input File Formats

### 1. `drills_log.csv` - Historical Coaching Sessions
Required columns:
- `student`: Student name
- `coach`: Coach name
- `date`: Session date (YYYY-MM-DD format)
- `minutes`: Session duration in minutes
- `drill_type`: Type of drill/event (e.g., LD, PF)

### 2. `group_roster.csv` - Tournament Group Students
Required columns:
- `student`: Student name (must match names in drills_log.csv)

### 3. `coaches.csv` - Coach Information
Required columns:
- `coach`: Coach name
- `specialties`: Comma-separated list of event specialties
- `rating`: Coach rating (numeric, e.g., 1-5)

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--drills` | Yes | - | Path to drills log CSV file |
| `--roster` | Yes | - | Path to group roster CSV file |
| `--coaches` | Yes | - | Path to coaches metadata CSV file |
| `--tournament` | Yes | - | Tournament name (e.g., "Greenhill 2025") |
| `--event` | No | None | Event type (e.g., "LD", "PF", "CX") |
| `--output` | Yes | - | Path for output recommendations CSV |
| `--as_of` | No | Today | Reference date for recency calculations (YYYY-MM-DD) |
| `--half_life_days` | No | 30 | Half-life for exponential decay in recency scoring |
| `--min_sessions` | No | 1 | Minimum sessions required for coach consideration |
| `--weights` | No | See below | JSON string of scoring component weights |
| `--debug` | No | False | Enable debug output |

### Default Weights
```json
{
  "recency": 0.4,
  "volume": 0.3,
  "coverage": 0.15,
  "minutes": 0.1,
  "specialty": 0.05
}
```

## Output Format

The tool generates a CSV file with the following columns:

- `coach`: Coach name
- `tournament`: Tournament name
- `event`: Event type (if specified)
- `sessions`: Total sessions with group members
- `students_covered`: Number of unique group students coached
- `total_minutes`: Total coaching minutes with group
- `recency_score`: Normalized recency score (0-1)
- `volume_score`: Normalized volume score (0-1)
- `coverage_score`: Percentage of group covered (0-1)
- `minutes_score`: Normalized minutes score (0-1)
- `specialty_score`: Combined specialty and rating score (0-1)
- `combined_score`: Weighted final score
- `percent_of_group_covered`: Coverage as percentage
- `notes`: Additional insights (e.g., "Worked with majority of group recently")

## Scoring Algorithm

### Recency Score
Uses exponential decay based on days since last session:
```
weight = 0.5^(days_ago / half_life_days)
```

### Coverage Score
Percentage of group students the coach has worked with:
```
coverage = students_coached_in_group / total_group_students
```

### Specialty Score
Weighted combination of event match (70%) and coach rating (30%):
```
specialty = 0.7 * event_match + 0.3 * normalized_rating
```

### Combined Score
Weighted sum of all component scores based on configured weights.

## Examples

### Example 1: Basic Tournament Matching
```bash
# Find best coaches for LD students at Greenhill
python coach_matcher.py \
    --drills drills_log.csv \
    --roster group_roster.csv \
    --coaches coaches.csv \
    --tournament "Greenhill 2025" \
    --event "LD" \
    --output greenhill_ld_coaches.csv
```

### Example 2: Emphasize Recent Experience
```bash
# Weight recency more heavily with shorter half-life
python coach_matcher.py \
    --drills drills_log.csv \
    --roster group_roster.csv \
    --coaches coaches.csv \
    --tournament "Yale 2025" \
    --event "PF" \
    --output yale_pf_coaches.csv \
    --half_life_days 15 \
    --weights '{"recency":0.6,"volume":0.2,"coverage":0.1,"minutes":0.05,"specialty":0.05}'
```

### Example 3: Require Minimum Experience
```bash
# Only consider coaches with at least 3 sessions
python coach_matcher.py \
    --drills drills_log.csv \
    --roster group_roster.csv \
    --coaches coaches.csv \
    --tournament "TOC 2025" \
    --event "LD" \
    --output toc_experienced_coaches.csv \
    --min_sessions 3
```

## Troubleshooting

### Common Issues

1. **"Missing columns" error**: Ensure your CSV files have all required columns (case-insensitive)
2. **Empty recommendations**: Check that student names in roster match those in drills_log
3. **Date parsing errors**: Ensure dates are in YYYY-MM-DD format
4. **No coaches meet criteria**: Try lowering `--min_sessions` requirement

## Author

Spencer Swickle