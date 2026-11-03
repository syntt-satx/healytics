import os
import json
import pandas as pd
import pyreadr

base = r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics"
proc = os.path.join(base, "data", "processed")
out_dir = os.path.join(base, "outputs")
app_dir = os.path.join(base, "app")

# Ingest all pre-computed RDS files
revs = pyreadr.read_r(os.path.join(proc, "review_satisfaction.rds"))[None]
sentences = pyreadr.read_r(os.path.join(proc, "aspect_sentences.rds"))[None]
pm = pyreadr.read_r(os.path.join(proc, "priority_matrix.rds"))[None]
val = pyreadr.read_r(os.path.join(proc, "validation_metrics.rds"))[None]
fc = pyreadr.read_r(os.path.join(proc, "forecasts_pred.rds"))[None]
hist = pyreadr.read_r(os.path.join(proc, "forecasts_historical.rds"))[None]
beta = pyreadr.read_r(os.path.join(proc, "lda_topics_beta.rds"))[None]
dept_sum = pyreadr.read_r(os.path.join(proc, "satisfaction_summary.rds"))[None]
monthly_trends = pyreadr.read_r(os.path.join(proc, "lda_aspect_monthly.rds"))[None]
weekly_trends = pyreadr.read_r(os.path.join(proc, "lda_aspect_weekly.rds"))[None]
topic_monthly = pyreadr.read_r(os.path.join(proc, "lda_topics_monthly.rds"))[None]

# Clean up date strings for JSON
revs["date"] = revs["date"].astype(str)
sentences["date"] = sentences["date"].astype(str)
monthly_trends["month"] = monthly_trends["month"].astype(str).str[:7]
weekly_trends["week"] = weekly_trends["week"].astype(str).str[:10]
hist["week"] = hist["week"].astype(str).str[:10]
fc["week"] = fc["week"].astype(str).str[:10]
topic_monthly["month"] = topic_monthly["month"].astype(str).str[:7]

# Serialize complete data
all_reviews = revs[["review_id", "date", "hospital", "department", "rating", "sentiment_class", "satisfaction_index", "text"]].to_dict(orient="records")
all_sentences = sentences[["sentence_id", "review_id", "date", "hospital", "department", "rating", "aspect", "sentence", "sentiment_score", "polarity"]].to_dict(orient="records")

# Color mapping for priority matrix
pm_records = []
for r in pm.to_dict(orient="records"):
    if "Fix First" in r["quadrant"]:
        r["zone_color"] = "#9F1239" # Velvet Burgundy
    elif "Maintain Excellence" in r["quadrant"]:
        r["zone_color"] = "#059669" # Emerald Gem
    elif "Secondary" in r["quadrant"]:
        r["zone_color"] = "#D97706" # Amber
    else:
        r["zone_color"] = "#64748B" # Slate
    pm_records.append(r)

priority_data = pm_records
val_metrics = val.to_dict(orient="records")
topic_beta = beta.to_dict(orient="records")
dept_summaries = dept_sum.to_dict(orient="records")
forecasts_pred = fc.to_dict(orient="records")
forecasts_hist = hist.to_dict(orient="records")
topic_monthly_records = topic_monthly.to_dict(orient="records")

print(f"Data Loaded: {len(all_reviews)} reviews, {len(all_sentences)} sentences, {len(dept_summaries)} dept summaries")
