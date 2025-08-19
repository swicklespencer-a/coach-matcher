# Coach Matcher

A python tool for matching debate coaches to student groups at tournaments. It scores coaches based on past drill sessions, recency, coverage, time spent, and event specialties.

## Overview

Coach Matcher reviews past coaching data and recommends the best coaches for a group of students. It uses a weighted scoring system that considers:

* **Recency**: How recently coaches worked with the group (with decay over time)
* **Volume**: Number of sessions with group members
* **Coverage**: Percentage of group coached
* **Minutes**: Total coaching time
* **Specialty**: Event expertise and rating

## Features

* **Multi-factor Scoring**: Customizable weights for each factor
* **Recency Scoring**: Time-decay system with adjustable half-life
* **Coverage Analysis**: Measures how many group members a coach has worked with
* **Specialty Matching**: LD, PF, CX, etc.
* **Detailed Output**: Breakdown of scoring for transparency

## Installation

### Prerequisites

* **Python 3.6+**
* **pip**

### Required Packages

```bash
pip install pandas numpy
```

Or create a `requirements.txt`:

```
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

### Advanced Usage

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

## Input Files

1. **drills\_log.csv** – past sessions

   * `student`, `coach`, `date`, `minutes`, `drill_type`
2. **group\_roster.csv** – tournament students

   * `student`
3. **coaches.csv** – coach data

   * `coach`, `specialties`, `rating`

## Command-Line Arguments

* **--drills**: Path to drills log CSV *(required)*
* **--roster**: Path to roster CSV *(required)*
* **--coaches**: Path to coach data CSV *(required)*
* **--tournament**: Tournament name *(required)*
* **--event**: Event type (LD, PF, CX) *(optional)*
* **--output**: Output CSV *(required)*
* **--as\_of**: Date for recency calculations *(default: today)*
* **--half\_life\_days**: Half-life for recency *(default: 30)*
* **--min\_sessions**: Minimum sessions *(default: 1)*
* **--weights**: JSON weights for scoring
* **--debug**: Show debug output

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

## Output

The tool generates a CSV with:

* **coach**, **tournament**, **event**
* **sessions**, **students\_covered**, **total\_minutes**
* **recency\_score**, **volume\_score**, **coverage\_score**, **minutes\_score**, **specialty\_score**
* **combined\_score**, **percent\_of\_group\_covered**, **notes**

## Scoring

### Recency

Exponential decay:

```
weight = 0.5^(days_ago / half_life_days)
```

### Coverage

```
coverage = students_coached_in_group / total_group_students
```

### Specialty

```
specialty = 0.7 * event_match + 0.3 * normalized_rating
```

### Combined

Weighted sum of all scores.

## Examples

**Example 1 – Basic Match**

```bash
python coach_matcher.py --drills drills_log.csv --roster group_roster.csv \
--coaches coaches.csv --tournament "Greenhill 2025" --event "LD" \
--output greenhill_ld_coaches.csv
```

**Example 2 – Emphasize Recency**

```bash
python coach_matcher.py --drills drills_log.csv --roster group_roster.csv \
--coaches coaches.csv --tournament "Yale 2025" --event "PF" \
--output yale_pf_coaches.csv --half_life_days 15 \
--weights '{"recency":0.6,"volume":0.2,"coverage":0.1,"minutes":0.05,"specialty":0.05}'
```

**Example 3 – Require Minimum Experience**

```bash
python coach_matcher.py --drills drills_log.csv --roster group_roster.csv \
--coaches coaches.csv --tournament "TOC 2025" --event "LD" \
--output toc_experienced_coaches.csv --min_sessions 3
```

## Troubleshooting

* **Missing columns**: Check CSV headers
* **Empty recommendations**: Ensure roster names match drills log
* **Date errors**: Use YYYY-MM-DD format
* **No coaches found**: Lower `--min_sessions`

## Author

**Spencer Swickle**
