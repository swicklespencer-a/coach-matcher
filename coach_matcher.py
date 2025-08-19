#!/usr/bin/env python3
"""
Coach Matcher
-------------
Given:
  1) drills_log.csv: records of drills between students and coaches
  2) group_roster.csv: the student roster for the target tournament group
  3) coaches.csv: coach metadata (specialties, ratings, availability)

Outputs:
  - Ranked list of coaches best suited for this group at a given tournament, 
    based on how often and how recently group students drilled with them, 
    breadth of student coverage, total minutes, and specialty fit.

Usage:
  python coach_matcher.py \
      --drills drills_log.csv \
      --roster group_roster.csv \
      --coaches coaches.csv \
      --tournament "Greenhill 2025" \
      --event "LD" \
      --output recommendations.csv
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import math
import json

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--drills", required=True)
    p.add_argument("--roster", required=True)
    p.add_argument("--coaches", required=True)
    p.add_argument("--tournament", required=True)
    p.add_argument("--event", required=False, default=None, help="e.g., LD, PF, CX")
    p.add_argument("--output", required=True)
    p.add_argument("--as_of", required=False, default=None)
    p.add_argument("--half_life_days", type=float, default=30.0)
    p.add_argument("--min_sessions", type=int, default=1)
    p.add_argument("--weights", required=False, default=None, help="JSON dict of component weights")
    p.add_argument("--debug", action="store_true")
    return p.parse_args()

def load_data(drills_path, roster_path, coaches_path):
    drills = pd.read_csv(drills_path)
    roster = pd.read_csv(roster_path)
    coaches = pd.read_csv(coaches_path)
    drills.columns = [c.strip().lower() for c in drills.columns]
    roster.columns = [c.strip().lower() for c in roster.columns]
    coaches.columns = [c.strip().lower() for c in coaches.columns]
    return drills, roster, coaches

def ensure_columns(drills, roster, coaches):
    req_drills = {"student","coach","date","minutes","drill_type"}
    req_roster = {"student"}
    req_coaches = {"coach","specialties","rating"}
    if not req_drills.issubset(drills.columns):
        missing = req_drills - set(drills.columns)
        raise ValueError(f"Missing columns in drills: {missing}")
    if not req_roster.issubset(roster.columns):
        missing = req_roster - set(roster.columns)
        raise ValueError(f"Missing columns in roster: {missing}")
    if not req_coaches.issubset(coaches.columns):
        missing = req_coaches - set(coaches.columns)
        raise ValueError(f"Missing columns in coaches: {missing}")

def coerce_types(drills):
    drills = drills.copy()
    drills["date"] = pd.to_datetime(drills["date"], errors="coerce")
    drills["minutes"] = pd.to_numeric(drills["minutes"], errors="coerce").fillna(0)
    return drills

def exponential_recency_weight(days_ago, half_life_days):
    return 0.5 ** (days_ago / max(half_life_days, 0.0001))

def compute_scores(drills, roster, coaches, as_of_date, half_life_days, event=None, min_sessions=1, weights=None, debug=False):
    if weights is None:
        weights = {"recency":0.4, "volume":0.3, "coverage":0.15, "minutes":0.1, "specialty":0.05}

    roster_students = set(roster["student"].str.strip().str.lower().unique())
    d = drills[drills["student"].str.strip().str.lower().isin(roster_students)].copy()
    if d.empty:
        return pd.DataFrame(columns=[
            "coach","sessions","students_covered","total_minutes","recency_score",
            "volume_score","coverage_score","minutes_score","specialty_score","combined_score"
        ])

    d["days_ago"] = (as_of_date - d["date"]).dt.days.clip(lower=0)
    d["recency_w"] = d["days_ago"].apply(lambda x: exponential_recency_weight(x, half_life_days))

    grp = d.groupby("coach").agg(
        sessions=("student","count"),
        students_covered=("student", lambda s: len(set(s.str.lower()))),
        total_minutes=("minutes","sum"),
        recency_sum=("recency_w","sum"),
    ).reset_index()

    def norm(col):
        maxv = grp[col].max()
        if maxv <= 0:
            return np.zeros(len(grp))
        return grp[col] / maxv

    grp["recency_score"] = norm("recency_sum")
    grp["volume_score"] = norm("sessions")
    grp["coverage_score"] = grp["students_covered"] / max(len(roster_students), 1)
    grp["minutes_score"] = norm("total_minutes")

    coaches_local = coaches.copy()
    coaches_local["coach"] = coaches_local["coach"].astype(str)
    if event is not None:
        coaches_local["specialty_match"] = coaches_local["specialties"].fillna("").str.lower().apply(
            lambda s: int(event.lower() in [x.strip() for x in s.split(",") if x.strip()])
        )
    else:
        coaches_local["specialty_match"] = 0

    grp = grp.merge(coaches_local["coach specialty_match rating".split()], on="coach", how="left")

    if "rating" in grp.columns:
        r = grp["rating"].fillna(0).astype(float)
        r_norm = (r - r.min()) / (r.max() - r.min()) if r.max() > r.min() else np.zeros(len(r))
        spec_raw = grp["specialty_match"].fillna(0)*0.7 + r_norm*0.3
    else:
        spec_raw = grp["specialty_match"].fillna(0).astype(float)

    grp["specialty_score"] = (spec_raw / spec_raw.max()) if spec_raw.max() > 0 else 0.0
    grp = grp[grp["sessions"] >= min_sessions].copy()

    w = {**{"recency":0.4, "volume":0.3, "coverage":0.15, "minutes":0.1, "specialty":0.05}, **weights}
    grp["combined_score"] = (
        w["recency"]*grp["recency_score"] +
        w["volume"]*grp["volume_score"] +
        w["coverage"]*grp["coverage_score"] +
        w["minutes"]*grp["minutes_score"] +
        w["specialty"]*grp["specialty_score"]
    )

    grp = grp.sort_values("combined_score", ascending=False).reset_index(drop=True)

    cols = ["coach","sessions","students_covered","total_minutes","recency_score",
            "volume_score","coverage_score","minutes_score","specialty_score","combined_score"]

    grp["percent_of_group_covered"] = (grp["coverage_score"]*100).round(1)
    grp["notes"] = np.where(
        grp["students_covered"]>=max(1,int(0.5*len(roster_students))),
        "Worked with majority of group recently",
        ""
    )
    return grp[cols + ["percent_of_group_covered","notes"]]

def main():
    args = parse_args()
    drills, roster, coaches = load_data(args.drills, args.roster, args.coaches)
    ensure_columns(drills, roster, coaches)
    drills = coerce_types(drills)
    as_of_date = pd.to_datetime(args.as_of) if args.as_of else pd.Timestamp.today().normalize()
    weights = json.loads(args.weights) if args.weights else None
    result = compute_scores(
        drills=drills,
        roster=roster,
        coaches=coaches,
        as_of_date=as_of_date,
        half_life_days=args.half_life_days,
        event=args.event,
        min_sessions=args.min_sessions,
        weights=weights,
    )
    result.insert(1, "tournament", args.tournament)
    if args.event:
        result.insert(2, "event", args.event)
    result.to_csv(args.output, index=False)

    print("Top Recommendations:")
    print(result.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
