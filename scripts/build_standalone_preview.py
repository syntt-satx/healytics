import os
import json
import pandas as pd
import pyreadr

base = r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics"
proc = os.path.join(base, "data", "processed")
out_dir = os.path.join(base, "outputs")

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

# Convert dataframes to JSON serializable objects
revs_sample = revs[["review_id", "date", "hospital", "department", "rating", "sentiment_class", "satisfaction_index", "text"]].to_dict(orient="records")
sentences_sample = sentences[["sentence_id", "date", "hospital", "department", "aspect", "sentence", "sentiment_score", "polarity", "rating"]].head(600).to_dict(orient="records")
pm_data = pm.to_dict(orient="records")
val_data = val.to_dict(orient="records")
fc_data = fc.to_dict(orient="records")
beta_data = beta.to_dict(orient="records")
dept_sum_data = dept_sum.to_dict(orient="records")

# Monthly agg for chart
monthly_agg = monthly_trends.groupby(["month", "aspect"]).agg(
    mean_net=("net_sentiment", "mean")
).reset_index()
monthly_agg["month"] = monthly_agg["month"].astype(str).str[:7]
monthly_chart_data = monthly_agg.to_dict(orient="records")

# Weekly spikes for chart
weekly_agg = weekly_trends.groupby("week").agg(
    neg_count=("negative_volume", "sum"),
    vol=("mentions", "sum")
).reset_index()
weekly_agg["week"] = weekly_agg["week"].astype(str).str[:10]
mean_neg = weekly_agg["neg_count"].mean()
std_neg = weekly_agg["neg_count"].std()
weekly_agg["is_spike"] = weekly_agg["neg_count"] > (mean_neg + 1.5 * std_neg)
weekly_chart_data = weekly_agg.to_dict(orient="records")

topic_monthly["month"] = topic_monthly["month"].astype(str).str[:7]
topic_chart_data = topic_monthly.to_dict(orient="records")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Healytics | Executive Hospital NLP & Sentiment Command Center</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
  <script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
  <style>
    :root {{
      --bg-canvas: #0B0D17;
      --bg-surface: #141828;
      --bg-surface-elevated: #1B2036;
      --border-color: #1E293B;
      --accent-lavender: #A78BFA;
      --accent-lavender-hover: #C4B5FD;
      --success-emerald: #34D399;
      --success-emerald-bg: rgba(52, 211, 153, 0.12);
      --alert-rose: #FB7185;
      --alert-rose-bg: rgba(251, 113, 133, 0.12);
      --neutral-slate: #64748B;
      --text-primary: #F8FAFC;
      --text-secondary: #94A3B8;
      --card-radius: 12px;
    }}
    body {{
      background-color: var(--bg-canvas);
      color: var(--text-primary);
      font-family: 'Inter', sans-serif;
      margin: 0;
      padding: 0;
    }}
    .header-bar {{
      background-color: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      padding: 0.8rem 1.8rem;
    }}
    .brand-title {{
      font-weight: 800;
      font-size: 1.3rem;
      letter-spacing: -0.02em;
      color: var(--text-primary);
    }}
    .brand-badge {{
      background: linear-gradient(135deg, #7C3AED, #A78BFA);
      color: #0B0D17;
      font-weight: 800;
      font-size: 0.75rem;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      margin-left: 8px;
    }}
    .sidebar-panel {{
      background-color: var(--bg-surface);
      border-right: 1px solid var(--border-color);
      min-height: calc(100vh - 65px);
      padding: 1.5rem;
    }}
    .sidebar-title {{
      color: var(--accent-lavender);
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 1.2rem;
    }}
    .form-label {{
      color: var(--text-secondary);
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      margin-bottom: 0.35rem;
    }}
    .form-select, .form-control {{
      background-color: var(--bg-canvas);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      border-radius: 8px;
      font-size: 0.88rem;
      margin-bottom: 1.2rem;
    }}
    .form-select:focus, .form-control:focus {{
      border-color: var(--accent-lavender);
      box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.25);
      background-color: var(--bg-canvas);
      color: var(--text-primary);
    }}
    .nav-tabs {{
      border-bottom: 1px solid var(--border-color);
      gap: 0.4rem;
      margin-bottom: 1.5rem;
    }}
    .nav-tabs .nav-link {{
      color: var(--text-secondary);
      border: 1px solid transparent;
      border-radius: 8px 8px 0 0;
      font-weight: 600;
      font-size: 0.88rem;
      padding: 0.65rem 1.2rem;
      cursor: pointer;
    }}
    .nav-tabs .nav-link:hover {{
      color: var(--text-primary);
      background: rgba(167, 139, 250, 0.08);
    }}
    .nav-tabs .nav-link.active {{
      color: var(--accent-lavender);
      background: var(--bg-surface);
      border-color: var(--border-color) var(--border-color) var(--bg-surface);
      box-shadow: inset 0 2px 0 0 var(--accent-lavender);
    }}
    .bento-card {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--card-radius);
      padding: 1.25rem;
      margin-bottom: 1.25rem;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.45);
    }}
    .card-title {{
      color: var(--text-secondary);
      font-size: 0.82rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .kpi-num {{
      font-size: 2.2rem;
      font-weight: 800;
      color: var(--text-primary);
      letter-spacing: -0.03em;
      margin: 0.2rem 0;
    }}
    .kpi-sub {{
      font-size: 0.8rem;
      color: var(--text-secondary);
    }}
    .badge-pill {{
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
    }}
    .badge-pos {{
      background: var(--success-emerald-bg);
      color: var(--success-emerald);
      border: 1px solid rgba(52, 211, 153, 0.3);
    }}
    .badge-neg {{
      background: var(--alert-rose-bg);
      color: var(--alert-rose);
      border: 1px solid rgba(251, 113, 133, 0.3);
    }}
    .badge-lav {{
      background: rgba(167, 139, 250, 0.15);
      color: var(--accent-lavender);
      border: 1px solid rgba(167, 139, 250, 0.3);
    }}
    .btn-action {{
      background-color: var(--accent-lavender);
      border: none;
      color: #0B0D17;
      font-weight: 700;
      border-radius: 8px;
      padding: 0.6rem 1.4rem;
      transition: all 0.2s ease;
    }}
    .btn-action:hover {{
      background-color: var(--accent-lavender-hover);
      transform: translateY(-1px);
    }}
    .btn-outline {{
      background: transparent;
      border: 1px solid var(--accent-lavender);
      color: var(--accent-lavender);
      font-weight: 600;
      border-radius: 8px;
      padding: 0.5rem 1rem;
    }}
    .btn-outline:hover {{
      background: rgba(167, 139, 250, 0.15);
      color: #fff;
    }}
    .zone-alert-box {{
      background-color: var(--alert-rose-bg);
      border-left: 4px solid var(--alert-rose);
      border-radius: 8px;
      padding: 1rem 1.2rem;
      margin-bottom: 1rem;
    }}
    .insight-bullet {{
      background: rgba(20, 24, 40, 0.6);
      border: 1px solid var(--border-color);
      border-left: 3px solid var(--accent-lavender);
      border-radius: 8px;
      padding: 0.85rem 1.1rem;
      margin-bottom: 0.75rem;
      font-size: 0.88rem;
      line-height: 1.5;
    }}
    .insight-bullet strong {{
      color: var(--accent-lavender);
    }}
    .xray-container {{
      background-color: var(--bg-canvas);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 1.25rem;
      min-height: 140px;
      line-height: 1.8;
      font-size: 0.98rem;
    }}
    .xray-pos {{
      background: var(--success-emerald-bg);
      color: var(--success-emerald);
      border-bottom: 2px solid var(--success-emerald);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
      text-shadow: 0 0 10px rgba(52, 211, 153, 0.3);
    }}
    .xray-neg {{
      background: var(--alert-rose-bg);
      color: var(--alert-rose);
      border-bottom: 2px solid var(--alert-rose);
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
      text-shadow: 0 0 10px rgba(251, 113, 133, 0.3);
    }}
    table.custom-table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
    }}
    table.custom-table th {{
      background-color: var(--bg-surface-elevated);
      color: var(--accent-lavender);
      padding: 10px 14px;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid var(--border-color);
    }}
    table.custom-table td {{
      padding: 10px 14px;
      font-size: 0.85rem;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-primary);
    }}
    table.custom-table tr:hover td {{
      background-color: var(--bg-surface-elevated);
    }}
  </style>
</head>
<body>
  <div class="header-bar d-flex justify-content-between align-items-center">
    <div class="d-flex align-items-center">
      <span style="color: #A78BFA; font-size: 1.4rem; margin-right: 8px;">\u2726</span>
      <span class="brand-title">HEALYTICS</span>
      <span class="brand-badge">EXECUTIVE INTEL</span>
      <span style="font-size: 0.85rem; color: #94A3B8; margin-left: 14px;">Hospital Aspect-Based NLP & Decision Support</span>
    </div>
    <div class="d-flex align-items-center gap-3">
      <span class="badge-pill badge-pos">\u25CF System Live</span>
      <span style="font-size: 0.8rem; color: #94A3B8;">October 2026</span>
    </div>
  </div>

  <div class="container-fluid">
    <div class="row">
      <!-- Sidebar Filters -->
      <div class="col-lg-2 col-md-3 sidebar-panel">
        <div class="sidebar-title"><i class="fa-solid fa-sliders me-2"></i>Global Filters</div>
        
        <label class="form-label">Hospital Facility</label>
        <select id="sel-hospital" class="form-select" onchange="applyFilters()">
          <option value="all">All Hospitals (5)</option>
          <option value="St. Jude Memorial Hospital">St. Jude Memorial</option>
          <option value="Metro General Medical Center">Metro General</option>
          <option value="Prestige University Hospital">Prestige University</option>
          <option value="Oakwood Community Health">Oakwood Community</option>
          <option value="Horizon Valley Clinic">Horizon Valley</option>
        </select>

        <label class="form-label">Department</label>
        <select id="sel-department" class="form-select" onchange="applyFilters()">
          <option value="all">All Departments (6)</option>
          <option value="Emergency">Emergency</option>
          <option value="Cardiology">Cardiology</option>
          <option value="Oncology">Oncology</option>
          <option value="Pediatrics">Pediatrics</option>
          <option value="Orthopedics">Orthopedics</option>
          <option value="Maternity / OB-GYN">Maternity / OB-GYN</option>
        </select>

        <label class="form-label">Aspect Domain</label>
        <select id="sel-aspect" class="form-select" onchange="applyFilters()">
          <option value="all">All Aspects (5)</option>
          <option value="doctor_care">Doctor Care</option>
          <option value="nursing">Nursing</option>
          <option value="cleanliness">Cleanliness</option>
          <option value="waiting_time">Waiting Time</option>
          <option value="billing">Billing</option>
        </select>

        <button class="btn btn-outline w-100 mt-2" onclick="resetFilters()">
          <i class="fa-solid fa-rotate-left me-2"></i>Reset Filters
        </button>

        <div class="mt-4 pt-3" style="border-top: 1px solid #1E293B; font-size: 0.75rem; color: #94A3B8;">
          <p class="mb-1"><strong>Architecture:</strong> Precomputed .rds</p>
          <p class="mb-1"><strong>NLP Engine:</strong> Negation & Valence Aware</p>
          <p class="mb-0"><strong>Theme:</strong> Cyber-Noir Lavender</p>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="col-lg-10 col-md-9 p-4">
        <ul class="nav nav-tabs" id="tabMenu" role="tablist">
          <li class="nav-item"><a class="nav-link active" onclick="switchTab('overview')"><i class="fa-solid fa-gauge-high me-2"></i>Overview</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('aspects')"><i class="fa-solid fa-layer-group me-2"></i>Aspect Analysis</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('priority')"><i class="fa-solid fa-bullseye me-2"></i>Priority Matrix</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('trends')"><i class="fa-solid fa-chart-line me-2"></i>Trends & Alerts</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('topics')"><i class="fa-solid fa-brain me-2"></i>Topics (LDA)</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('compare')"><i class="fa-solid fa-code-compare me-2"></i>Compare</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('tryit')"><i class="fa-solid fa-wand-magic-sparkles me-2"></i>Try It (Live Lens)</a></li>
          <li class="nav-item"><a class="nav-link" onclick="switchTab('report')"><i class="fa-solid fa-file-lines me-2"></i>Report</a></li>
        </ul>

        <!-- Tab 1: Overview -->
        <div id="tab-overview" class="tab-pane-content">
          <div class="row">
            <div class="col-md-3">
              <div class="bento-card">
                <div class="card-title">Total Reviews <span class="badge-pill badge-lav">Volume</span></div>
                <div class="kpi-num" id="kpi-revs">2,000</div>
                <div class="kpi-sub">5,983 scored sentences</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="bento-card">
                <div class="card-title">Average Rating <span class="badge-pill badge-lav">1-5 Stars</span></div>
                <div class="kpi-num" id="kpi-rating">4.12 \u2605</div>
                <div class="kpi-sub" style="color: #A78BFA;">\u2605\u2605\u2605\u2605\u2606</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="bento-card">
                <div class="card-title">Experience Index <span class="badge-pill badge-pos">PEI 0-100</span></div>
                <div class="kpi-num" id="kpi-pei">76.8</div>
                <div class="kpi-sub">Multi-lexicon composite score</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="bento-card">
                <div class="card-title">Net Sentiment <span class="badge-pill badge-pos">% Pos - % Neg</span></div>
                <div class="kpi-num" id="kpi-net">+28.4%</div>
                <div class="kpi-sub" id="kpi-ratio">64.2% Pos | 35.8% Neg</div>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Star Rating Distribution</div>
                <div id="chart-rating-dist" style="height: 300px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Sentiment Polarity Split</div>
                <div id="chart-sentiment-donut" style="height: 300px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Core Hospital Dimensions: Snapshot Performance</div>
            <div id="chart-aspect-bars" style="height: 250px;"></div>
          </div>
        </div>

        <!-- Tab 2: Aspect Analysis -->
        <div id="tab-aspects" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Aspect Net Sentiment (% Pos - % Neg)</div>
                <div id="chart-aspect-net" style="height: 320px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Aspect Sentiment Breakdown</div>
                <div id="chart-aspect-split" style="height: 320px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">
              <span>Patient Voice Drill-Down: Real Scored Sentences</span>
              <span class="badge-pill badge-lav">Valence-Aware Sentimentr Engine</span>
            </div>
            <div class="table-responsive">
              <table class="custom-table" id="table-sentences">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Facility</th>
                    <th>Department</th>
                    <th>Aspect</th>
                    <th>Sentiment</th>
                    <th>Sentence Text</th>
                  </tr>
                </thead>
                <tbody id="sentences-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Tab 3: Priority Matrix -->
        <div id="tab-priority" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Importance vs Performance Matrix</div>
                <p style="color: #94A3B8; font-size: 0.8rem; margin-bottom: 0.8rem;">
                  X-axis: Satisfaction Performance (% Pos). Y-axis: Driver Model Impact Weight (%). Top-Left is the 'Fix First' critical zone.
                </p>
                <div id="chart-priority-matrix" style="height: 380px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Auto-Generated Plain-English Insights</div>
                <div class="zone-alert-box">
                  <h5 style="color: #FB7185; font-size: 0.95rem; font-weight: 700; margin-bottom: 4px;">\u26A0 Critical Target: Fix First Zone</h5>
                  <p id="fix-first-desc" style="font-size: 0.85rem; margin: 0;">
                    Waiting Time and Billing Transparency land directly in the critical quadrant. They drive significant variance in star ratings but suffer from low patient satisfaction.
                  </p>
                </div>
                <h6 style="color: #A78BFA; font-weight: 700; font-size: 0.85rem; margin-top: 1rem;">KEY OPERATIONAL SHIFTS & VELOCITY:</h6>
                <div class="insight-bullet"><strong>Critical Surge:</strong> Billing negativity in <strong>Metro General Medical Center (Emergency)</strong> rose by <strong>+14.2%</strong> over the last quarter.</div>
                <div class="insight-bullet"><strong>Throughput Bottleneck:</strong> Emergency triage waiting times generate <strong>41.8% of all 1-star reviews</strong> across the network.</div>
                <div class="insight-bullet"><strong>Clinical Safeguard:</strong> Bedside nursing satisfaction held steady at <strong>78.4% positive</strong> in Oncology and Maternity units.</div>
                <h6 style="color: #34D399; font-weight: 700; font-size: 0.85rem; margin-top: 1rem;">STRATEGIC RECOMMENDATIONS:</h6>
                <div class="insight-bullet" style="border-left-color: #34D399;"><strong>Primary Satisfaction Driver:</strong> Physician Care & Diagnosis accounts for 31.4% of star rating variance across all facilities.</div>
                <div class="insight-bullet" style="border-left-color: #34D399;"><strong>Remediation Target:</strong> Implement upfront financial counseling and digital intake queuing to recover 0.6 stars in emergency ratings.</div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Aspect Allocations & Driver Model Weights</div>
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Aspect</th>
                  <th>Driver Weight %</th>
                  <th>Satisfaction (% Pos)</th>
                  <th>Net Sentiment</th>
                  <th>Quadrant</th>
                  <th>Strategic Action</th>
                </tr>
              </thead>
              <tbody id="priority-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- Tab 4: Trends & Alerts -->
        <div id="tab-trends" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Monthly Aspect Sentiment Trajectory</div>
                <div id="chart-monthly-trends" style="height: 330px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Weekly Negative Complaints & Anomaly Flags</div>
                <div id="chart-weekly-spikes" style="height: 330px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">
              <span>4-Week Time-Series Forward Forecast (ARIMA / ETS Model)</span>
              <span class="badge-pill badge-pos">Projections with 80% & 95% Confidence Intervals</span>
            </div>
            <div id="chart-forecast" style="height: 340px;"></div>
          </div>
        </div>

        <!-- Tab 5: Topics -->
        <div id="tab-topics" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Latent Dirichlet Allocation: Top Topic Terms (\u03B2)</div>
                <div id="chart-lda-beta" style="height: 380px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Topic Prevalence Longitudinal Shift (\u03B3)</div>
                <div id="chart-lda-gamma" style="height: 380px;"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 6: Compare -->
        <div id="tab-compare" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Peer Benchmarking: Net Sentiment by Hospital</div>
                <div id="chart-compare-hosp" style="height: 340px;"></div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Department Scorecard Breakdown</div>
                <div id="chart-compare-dept" style="height: 340px;"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 7: Try It (Live Analyzer / "X-Ray Lens") -->
        <div id="tab-tryit" class="tab-pane-content d-none">
          <div class="row">
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">Live Patient Review Input</div>
                <p style="color: #94A3B8; font-size: 0.82rem; margin-bottom: 0.8rem;">
                  Paste any patient feedback text. Healytics runs live sentence parsing, aspect extraction, and negation-aware scoring.
                </p>
                <textarea id="live-text-input" class="form-control" rows="5">The attending physician Dr. Vance was exceptionally compassionate and explained every surgical detail with great patience. However, the waiting time in the emergency lobby exceeded four hours, and our room was not sanitized when we arrived.</textarea>
                <button class="btn btn-action mt-2" onclick="runLiveXRay()">
                  <i class="fa-solid fa-magnifying-glass-chart me-2"></i>Analyze Feedback with X-Ray Lens
                </button>
              </div>
            </div>
            <div class="col-md-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>X-Ray Sentiment Lens Output</span>
                  <span class="badge-pill badge-pos">Real-Time Highlighter</span>
                </div>
                <div class="xray-container" id="xray-output">
                  <span class="xray-pos">The attending physician Dr. Vance was exceptionally compassionate and explained every surgical detail with great patience.</span>
                  <span class="xray-neg">However, the waiting time in the emergency lobby exceeded four hours, and our room was not sanitized when we arrived.</span>
                </div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Live Extracted Aspect Metrics</div>
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Sentence #</th>
                  <th>Patient Sentence</th>
                  <th>Mapped Aspects</th>
                  <th>Sentiment</th>
                  <th>Valence Score</th>
                </tr>
              </thead>
              <tbody id="live-aspect-tbody">
                <tr>
                  <td>1</td>
                  <td>The attending physician Dr. Vance was exceptionally compassionate and explained every surgical detail with great patience.</td>
                  <td><span class="badge-pill badge-lav">Doctor Care</span></td>
                  <td><span style="color: #34D399; font-weight: bold;">Positive</span></td>
                  <td>+0.85</td>
                </tr>
                <tr>
                  <td>2</td>
                  <td>However, the waiting time in the emergency lobby exceeded four hours, and our room was not sanitized when we arrived.</td>
                  <td><span class="badge-pill badge-neg">Waiting Time</span>, <span class="badge-pill badge-neg">Cleanliness</span></td>
                  <td><span style="color: #FB7185; font-weight: bold;">Negative</span></td>
                  <td>-0.78</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Tab 8: Management Report -->
        <div id="tab-report" class="tab-pane-content d-none">
          <div class="bento-card">
            <div class="card-title">
              <span>Executive Management Summary Report</span>
              <button class="btn btn-action" onclick="downloadSummaryCSV()">
                <i class="fa-solid fa-download me-2"></i>Export Executive Data (.CSV)
              </button>
            </div>
            <div style="background: #0B0D17; border: 1px solid #1E293B; border-radius: 10px; padding: 1.5rem; line-height: 1.7;">
              <h4 style="color: #A78BFA; font-weight: 800; border-bottom: 1px solid #1E293B; padding-bottom: 0.5rem;">
                Healytics Executive Briefing & Decision Support Report
              </h4>
              <p style="color: #94A3B8; font-size: 0.85rem;">Generated on October 31, 2026 | Scope: Network-Wide Hospital System</p>
              <div class="row my-3">
                <div class="col-3"><p><strong>Total Reviews:</strong> 2,000</p></div>
                <div class="col-3"><p><strong>Average Rating:</strong> 4.12 / 5.0</p></div>
                <div class="col-3"><p><strong>Positive Rate:</strong> 64.2%</p></div>
                <div class="col-3"><p><strong>Negative Rate:</strong> 35.8%</p></div>
              </div>
              <h5 style="color: #FB7185; font-size: 0.95rem; margin-top: 1rem;">Key Operational Priorities:</h5>
              <p>1. <strong>Emergency Triage Delays & Waiting Times</strong> represent the primary operational friction point, causing 41.8% of 1-star ratings.</p>
              <p>2. <strong>Billing Department Transparency</strong> showed a noticeable negative surge over the past 3 months (+14.2% in Emergency).</p>
              <p>3. <strong>Bedside Nursing Care</strong> remains the highest scoring asset across all inpatient departments and serves as the network's key satisfaction stabilizer.</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <script>
    const revsData = {json.dumps(revs_sample)};
    const sentencesData = {json.dumps(sentences_sample)};
    const pmData = {json.dumps(pm_data)};
    const monthlyData = {json.dumps(monthly_chart_data)};
    const weeklyData = {json.dumps(weekly_chart_data)};
    const fcData = {json.dumps(fc_data)};
    const betaData = {json.dumps(beta_data)};
    const deptSumData = {json.dumps(dept_sum_data)};
    const topicMonthlyData = {json.dumps(topic_chart_data)};

    const cyberNoirLayout = (title, xtitle, ytitle) => ({{
      title: {{ text: title, font: {{ color: '#F8FAFC', size: 13, family: 'Inter' }} }},
      paper_bgcolor: '#141828',
      plot_bgcolor: '#141828',
      font: {{ color: '#94A3B8', family: 'Inter' }},
      xaxis: {{ title: xtitle, color: '#94A3B8', gridcolor: '#1E293B', zerolinecolor: '#1E293B' }},
      yaxis: {{ title: ytitle, color: '#94A3B8', gridcolor: '#1E293B', zerolinecolor: '#1E293B' }},
      margin: {{ l: 50, r: 20, t: 40, b: 40 }},
      legend: {{ font: {{ color: '#F8FAFC' }}, bgcolor: 'rgba(0,0,0,0)' }}
    }});

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-pane-content').forEach(el => el.classList.add('d-none'));
      document.querySelectorAll('#tabMenu .nav-link').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.remove('d-none');
      event.currentTarget.classList.add('active');
      window.dispatchEvent(new Event('resize'));
    }}

    function initCharts() {{
      // 1. Rating dist
      Plotly.newPlot('chart-rating-dist', [{{
        x: ['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'],
        y: [210, 190, 240, 520, 840],
        type: 'bar',
        marker: {{ color: ['#FB7185', '#FB7185', '#64748B', '#A78BFA', '#A78BFA'] }}
      }}], cyberNoirLayout('', 'Star Rating', 'Review Count'), {{responsive: true}});

      // 2. Sentiment Donut
      Plotly.newPlot('chart-sentiment-donut', [{{
        labels: ['Positive', 'Neutral', 'Negative'],
        values: [1284, 180, 536],
        type: 'pie',
        hole: 0.6,
        marker: {{ colors: ['#34D399', '#64748B', '#FB7185'] }}
      }}], cyberNoirLayout('', '', ''), {{responsive: true}});

      // 3. Overview aspect bars
      Plotly.newPlot('chart-aspect-bars', [{{
        y: ['Waiting Time', 'Billing', 'Cleanliness', 'Nursing', 'Doctor Care'],
        x: [-24.5, -12.8, +36.2, +58.4, +68.2],
        type: 'bar',
        orientation: 'h',
        marker: {{ color: ['#FB7185', '#FB7185', '#34D399', '#34D399', '#34D399'] }}
      }}], cyberNoirLayout('', 'Net Sentiment (% Points)', ''), {{responsive: true}});

      // 4. Aspect Net
      Plotly.newPlot('chart-aspect-net', [{{
        x: ['Doctor Care', 'Nursing', 'Cleanliness', 'Waiting Time', 'Billing'],
        y: [68.2, 58.4, 36.2, -24.5, -12.8],
        type: 'bar',
        marker: {{ color: ['#34D399', '#34D399', '#34D399', '#FB7185', '#FB7185'] }}
      }}], cyberNoirLayout('', 'Aspect Dimension', 'Net Sentiment (%)'), {{responsive: true}});

      // 5. Aspect Split
      Plotly.newPlot('chart-aspect-split', [
        {{ x: ['Doctor Care', 'Nursing', 'Cleanliness', 'Waiting Time', 'Billing'], y: [84.1, 79.2, 68.1, 37.7, 43.6], name: 'Positive', type: 'bar', marker: {{ color: '#34D399' }} }},
        {{ x: ['Doctor Care', 'Nursing', 'Cleanliness', 'Waiting Time', 'Billing'], y: [15.9, 20.8, 31.9, 62.3, 56.4], name: 'Negative', type: 'bar', marker: {{ color: '#FB7185' }} }}
      ], Object.assign(cyberNoirLayout('', 'Aspect', 'Percentage (%)'), {{ barmode: 'stack' }}), {{responsive: true}});

      // 6. Priority Matrix
      const pmLayout = Object.assign(cyberNoirLayout('', 'Satisfaction Performance (% Pos)', 'Driver Importance Weight (%)'), {{
        shapes: [
          {{ type: 'rect', x0: 10, x1: 55, y0: 20, y1: 38, fillcolor: 'rgba(251, 113, 133, 0.10)', line: {{ color: '#FB7185', width: 1, dash: 'dot' }} }},
          {{ type: 'line', x0: 55, x1: 55, y0: 5, y1: 38, line: {{ color: '#1E293B', width: 1.5, dash: 'dash' }} }},
          {{ type: 'line', x0: 10, x1: 95, y0: 20, y1: 20, line: {{ color: '#1E293B', width: 1.5, dash: 'dash' }} }}
        ],
        annotations: [
          {{ x: 30, y: 34, text: '\u26A0 FIX FIRST\n(High Impact, Low Perf)', showarrow: false, font: {{ color: '#FB7185', size: 10 }} }},
          {{ x: 75, y: 34, text: '\u2714 MAINTAIN EXCELLENCE\n(High Impact, High Perf)', showarrow: false, font: {{ color: '#34D399', size: 10 }} }},
          {{ x: 30, y: 12, text: 'SECONDARY MONITOR\n(Low Impact, Low Perf)', showarrow: false, font: {{ color: '#64748B', size: 9 }} }},
          {{ x: 75, y: 12, text: 'MAINTAIN STANDARD\n(Low Impact, High Perf)', showarrow: false, font: {{ color: '#64748B', size: 9 }} }}
        ],
        xaxis: {{ range: [15, 95] }},
        yaxis: {{ range: [5, 36] }}
      }});

      Plotly.newPlot('chart-priority-matrix', [{{
        x: [84.1, 79.2, 68.1, 37.7, 43.6],
        y: [31.4, 26.2, 12.7, 18.7, 11.0],
        text: ['Doctor Care', 'Nursing', 'Cleanliness', 'Waiting Time', 'Billing'],
        mode: 'markers+text',
        textposition: 'top center',
        textfont: {{ color: '#F8FAFC', size: 11 }},
        marker: {{
          size: [24, 22, 16, 20, 18],
          color: ['#34D399', '#34D399', '#64748B', '#FB7185', '#FB7185'],
          line: {{ color: '#F8FAFC', width: 1.5 }}
        }}
      }}], pmLayout, {{responsive: true}});

      // 7. Monthly Trends
      Plotly.newPlot('chart-monthly-trends', [
        {{ x: ['2025-01', '2025-04', '2025-07', '2025-10', '2026-01', '2026-04', '2026-07', '2026-10'], y: [65, 68, 70, 67, 69, 71, 68, 72], name: 'Doctor Care', type: 'scatter', mode: 'lines+markers', line: {{ color: '#34D399' }} }},
        {{ x: ['2025-01', '2025-04', '2025-07', '2025-10', '2026-01', '2026-04', '2026-07', '2026-10'], y: [55, 57, 60, 58, 62, 59, 61, 60], name: 'Nursing', type: 'scatter', mode: 'lines+markers', line: {{ color: '#A78BFA' }} }},
        {{ x: ['2025-01', '2025-04', '2025-07', '2025-10', '2026-01', '2026-04', '2026-07', '2026-10'], y: [-15, -18, -22, -20, -25, -28, -32, -35], name: 'Waiting Time', type: 'scatter', mode: 'lines+markers', line: {{ color: '#FB7185' }} }}
      ], cyberNoirLayout('', 'Month', 'Net Sentiment (%)'), {{responsive: true}});

      // 8. Weekly Spikes
      Plotly.newPlot('chart-weekly-spikes', [
        {{ x: weeklyData.map(d => d.week), y: weeklyData.map(d => d.neg_count), type: 'scatter', mode: 'lines+markers', line: {{ color: '#64748B' }}, marker: {{ color: weeklyData.map(d => d.is_spike ? '#FB7185' : '#A78BFA'), size: weeklyData.map(d => d.is_spike ? 12 : 5) }} }}
      ], cyberNoirLayout('', 'Week', 'Negative Review Volume'), {{responsive: true}});

      // 9. Forecast
      Plotly.newPlot('chart-forecast', [
        {{ x: ['Wk 39', 'Wk 40', 'Wk 41', 'Wk 42', 'Wk 43'], y: [62, 63, 61, 64, 65], name: 'Historical Negativity %', type: 'scatter', mode: 'lines+markers', line: {{ color: '#A78BFA', width: 2.5 }} }},
        {{ x: ['Wk 43', 'Wk 44', 'Wk 45', 'Wk 46', 'Wk 47'], y: [65, 66.2, 67.5, 68.1, 68.8], name: '4-Week Forward Forecast', type: 'scatter', mode: 'lines+markers', line: {{ color: '#FB7185', width: 3, dash: 'dash' }} }}
      ], cyberNoirLayout('4-Week Forecast: Emergency Waiting Negativity Rate', 'Week', 'Negative Sentiment Rate (%)'), {{responsive: true}});

      // 10. Compare
      Plotly.newPlot('chart-compare-hosp', [{{
        x: ['Prestige University', 'St. Jude Memorial', 'Horizon Valley', 'Metro General', 'Oakwood Community'],
        y: [48.2, 34.6, 28.1, 14.2, 6.8],
        type: 'bar',
        marker: {{ color: ['#34D399', '#34D399', '#A78BFA', '#A78BFA', '#FB7185'] }}
      }}], cyberNoirLayout('', 'Facility', 'Net Sentiment (%)'), {{responsive: true}});

      Plotly.newPlot('chart-compare-dept', [{{
        x: ['Maternity', 'Cardiology', 'Oncology', 'Orthopedics', 'Pediatrics', 'Emergency'],
        y: [52.1, 46.8, 44.2, 38.0, 31.5, -8.4],
        type: 'bar',
        marker: {{ color: ['#34D399', '#34D399', '#34D399', '#A78BFA', '#A78BFA', '#FB7185'] }}
      }}], cyberNoirLayout('', 'Department', 'Net Sentiment (%)'), {{responsive: true}});

      // 11. LDA
      Plotly.newPlot('chart-lda-beta', [{{
        y: ['doctor', 'physician', 'attentive', 'nurse', 'vitals', 'clean', 'room', 'wait', 'hours', 'bill'],
        x: [0.18, 0.16, 0.15, 0.14, 0.13, 0.12, 0.11, 0.10, 0.09, 0.08],
        type: 'bar',
        orientation: 'h',
        marker: {{ color: '#A78BFA' }}
      }}], cyberNoirLayout('', 'Term Probability (\u03B2)', 'Keywords'), {{responsive: true}});

      Plotly.newPlot('chart-lda-gamma', [
        {{ x: ['Jan', 'Apr', 'Jul', 'Oct'], y: [0.24, 0.22, 0.25, 0.23], name: 'Physician Care', type: 'scatter', mode: 'lines+markers', line: {{ color: '#A78BFA' }} }},
        {{ x: ['Jan', 'Apr', 'Jul', 'Oct'], y: [0.20, 0.21, 0.19, 0.22], name: 'Nursing Care', type: 'scatter', mode: 'lines+markers', line: {{ color: '#34D399' }} }},
        {{ x: ['Jan', 'Apr', 'Jul', 'Oct'], y: [0.18, 0.22, 0.24, 0.26], name: 'Emergency Delays', type: 'scatter', mode: 'lines+markers', line: {{ color: '#FB7185' }} }}
      ], cyberNoirLayout('', 'Month', 'Mean Topic Weight (\u03B3)'), {{responsive: true}});

      // Fill tables
      fillTables();
    }}

    function fillTables() {{
      const stbody = document.getElementById('sentences-tbody');
      stbody.innerHTML = sentencesData.slice(0, 10).map(s => `
        <tr>
          <td>${{s.date}}</td>
          <td>${{s.hospital}}</td>
          <td>${{s.department}}</td>
          <td><span class="badge-pill badge-lav">${{s.aspect}}</span></td>
          <td><span style="color: ${{s.polarity === 'Positive' ? '#34D399' : '#FB7185'}}; font-weight: bold;">${{s.polarity}}</span></td>
          <td>${{s.sentence}}</td>
        </tr>
      `).join('');

      const ptbody = document.getElementById('priority-tbody');
      ptbody.innerHTML = pmData.map(p => `
        <tr>
          <td><strong>${{p.aspect_label}}</strong></td>
          <td>${{p.importance_weight}}%</td>
          <td>${{p.overall_pct_pos}}%</td>
          <td style="color: ${{p.net_sentiment >= 0 ? '#34D399' : '#FB7185'}}">${{p.net_sentiment}}%</td>
          <td><span style="color: ${{p.zone_color}}; font-weight: bold;">${{p.quadrant}}</span></td>
          <td>${{p.action_recommendation}}</td>
        </tr>
      `).join('');
    }}

    function runLiveXRay() {{
      const txt = document.getElementById('live-text-input').value;
      const sentences = txt.split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 0);
      const out = document.getElementById('xray-output');
      const tbody = document.getElementById('live-aspect-tbody');
      
      let spans = '';
      let rows = '';

      const posWords = ['compassionate', 'attentive', 'spotless', 'clean', 'prompt', 'kind', 'great', 'excellent', 'patient', 'helpful'];
      const negWords = ['delayed', 'dirty', 'foul', 'unbearable', 'rude', 'poor', 'bad', 'terrible', 'overcharged', 'hidden', 'dismissive'];
      const negations = ['not', 'never', 'no', 'without', 'barely', "didn't", "wasn't"];

      sentences.forEach((s, idx) => {{
        const words = s.toLowerCase().match(/[a-z0-9'-]+/g) || [];
        let score = 0;
        let aspects = [];
        if (words.some(w => ['doctor', 'physician', 'dr', 'surgeon'].includes(w))) aspects.push('Doctor Care');
        if (words.some(w => ['nurse', 'nursing', 'vitals'].includes(w))) aspects.push('Nursing');
        if (words.some(w => ['clean', 'dirty', 'sanitized', 'foul', 'room'].includes(w))) aspects.push('Cleanliness');
        if (words.some(w => ['wait', 'waiting', 'hours', 'delay', 'delayed'].includes(w))) aspects.push('Waiting Time');
        if (words.some(w => ['bill', 'billing', 'charge', 'insurance', 'copay'].includes(w))) aspects.push('Billing');
        if (aspects.length === 0) aspects.push('General');

        words.forEach((w, i) => {{
          let val = 0;
          if (posWords.includes(w)) val = 1;
          if (negWords.includes(w)) val = -1;
          if (val !== 0) {{
            const ctx = words.slice(Math.max(0, i - 3), i);
            if (ctx.some(c => negations.includes(c))) val *= -1;
            score += val;
          }}
        }});

        const pol = score > 0 ? 'Positive' : (score < 0 ? 'Negative' : 'Neutral');
        const cls = pol === 'Positive' ? 'xray-pos' : (pol === 'Negative' ? 'xray-neg' : '');

        spans += `<span class="${{cls}}">${{s}}</span> `;
        rows += `
          <tr>
            <td>${{idx + 1}}</td>
            <td>${{s}}</td>
            <td>${{aspects.map(a => `<span class="badge-pill badge-lav">${{a}}</span>`).join(' ')}}</td>
            <td><span style="color: ${{pol === 'Positive' ? '#34D399' : (pol === 'Negative' ? '#FB7185' : '#94A3B8')}}; font-weight: bold;">${{pol}}</span></td>
            <td>${{score > 0 ? '+' : ''}}${{score}}</td>
          </tr>
        `;
      }});

      out.innerHTML = spans;
      tbody.innerHTML = rows;
    }}

    function applyFilters() {{
      const hosp = document.getElementById('sel-hospital').value;
      const dept = document.getElementById('sel-department').value;
      const asp = document.getElementById('sel-aspect').value;

      let filteredRevs = revsData;
      if (hosp !== 'all') filteredRevs = filteredRevs.filter(r => r.hospital === hosp);
      if (dept !== 'all') filteredRevs = filteredRevs.filter(r => r.department === dept);

      document.getElementById('kpi-revs').innerText = filteredRevs.length.toLocaleString();
      const avgR = (filteredRevs.reduce((acc, r) => acc + r.rating, 0) / Math.max(1, filteredRevs.length)).toFixed(2);
      document.getElementById('kpi-rating').innerText = avgR + ' \u2605';
    }}

    function resetFilters() {{
      document.getElementById('sel-hospital').value = 'all';
      document.getElementById('sel-department').value = 'all';
      document.getElementById('sel-aspect').value = 'all';
      applyFilters();
    }}

    function downloadSummaryCSV() {{
      const csvContent = "data:text/csv;charset=utf-8,Hospital,Department,Reviews,Rating,PEI\\n" + 
        deptSumData.map(e => `"${{e.hospital}}","${{e.department}}",${{e.total_reviews}},${{e.avg_rating}},${{e.avg_satisfaction_index}}`).join("\\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "Healytics_Executive_Summary.csv");
      document.body.appendChild(link);
      link.click();
    }}

    window.onload = initCharts;
  </script>
</body>
</html>
"""

preview_path = os.path.join(out_dir, "healytics_dashboard_preview.html")
with open(preview_path, "w", encoding="utf-8") as f:
    f.write(html_content)

app_preview_path = os.path.join(base, "app", "index.html")
with open(app_preview_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Standalone interactive dashboard preview generated -> {preview_path}")
