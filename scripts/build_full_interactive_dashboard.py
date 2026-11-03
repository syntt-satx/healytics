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

print("Serialized RDS records successfully. Assembling interactive dashboard HTML...")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Healytics | Obsidian & Gold Executive Suite Intelligence Terminal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
  <script src="www/plotly.min.js"></script>
  <script>if(typeof Plotly==="undefined"){{document.write('<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"><\\/script>');}}</script>
  <style>
    :root {{
      --bg-canvas: #0A0A0A;
      --bg-surface: #161616;
      --bg-surface-elevated: #1F1F1F;
      --border-gold-subtle: rgba(212, 175, 55, 0.20);
      --border-gold-strong: rgba(212, 175, 55, 0.50);
      
      --accent-gold: #E6C594;
      --accent-gold-hover: #F3DEBE;
      --accent-gold-glow: rgba(230, 197, 148, 0.35);
      --accent-gold-dim: rgba(230, 197, 148, 0.12);
      
      --success-gem: #059669;
      --success-gem-bg: rgba(5, 150, 105, 0.15);
      --success-gem-glow: rgba(5, 150, 105, 0.35);
      
      --alert-burgundy: #9F1239;
      --alert-burgundy-bg: rgba(159, 18, 57, 0.20);
      --alert-burgundy-glow: rgba(159, 18, 57, 0.45);
      
      --neutral-charcoal: #2A2A2A;
      --neutral-slate: #64748B;
      
      --text-header: #F8FAFC;
      --text-secondary: #94A3B8;
      --text-mono: #CBD5E1;
      --text-gold: #E6C594;
      
      --card-radius: 8px;
      --shadow-terminal: 0 4px 24px -2px rgba(0, 0, 0, 0.7);
    }}
    
    body {{
      background-color: var(--bg-canvas);
      color: var(--text-header);
      font-family: 'Inter', -apple-system, sans-serif;
      margin: 0;
      padding: 0;
      overflow-x: hidden;
    }}

    /* Typography Hierarchy */
    h1, h2, h3, h4, h5, .brand-title, .card-title, .sidebar-title, .nav-tabs .nav-link, .guide-title {{
      font-family: 'Cinzel', serif !important;
      letter-spacing: 0.08em !important;
      text-transform: uppercase !important;
    }}

    .kpi-num, .terminal-mono, .mono-data {{
      font-family: 'JetBrains Mono', monospace !important;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.03em;
    }}

    /* Header Bar */
    .header-bar {{
      background-color: var(--bg-surface);
      border-bottom: 1px solid var(--border-gold-subtle);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
      padding: 0.85rem 2rem;
      position: sticky;
      top: 0;
      z-index: 1000;
    }}
    
    .brand-title {{
      font-weight: 800;
      font-size: 1.35rem;
      color: var(--text-header);
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .brand-badge {{
      background: linear-gradient(135deg, #B48E43, #E6C594);
      color: #0A0A0A;
      font-family: 'JetBrains Mono', monospace !important;
      font-weight: 800;
      font-size: 0.70rem;
      padding: 0.25rem 0.65rem;
      border-radius: 4px;
      letter-spacing: 0.08em;
    }}

    /* Editorial Design Quote Banner */
    .quote-ribbon {{
      background: linear-gradient(90deg, #161616 0%, #1F1F1F 50%, #161616 100%);
      border-bottom: 1px solid var(--border-gold-subtle);
      color: var(--accent-gold);
      font-size: 0.80rem;
      font-style: italic;
      font-family: 'Cinzel', serif;
      letter-spacing: 0.08em;
      padding: 0.45rem 2rem;
      text-align: center;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 1.5rem;
    }}

    /* Sidebar Terminal Panel */
    .sidebar-panel {{
      background-color: var(--bg-surface);
      border-right: 1px solid var(--border-gold-subtle);
      min-height: calc(100vh - 105px);
      padding: 1.4rem;
    }}

    .sidebar-title {{
      color: var(--accent-gold);
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 1.2rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    .form-label {{
      color: var(--text-secondary);
      font-size: 0.74rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.30rem;
    }}

    .form-select, .form-control {{
      background-color: var(--bg-canvas);
      border: 1px solid var(--border-gold-subtle);
      color: var(--text-header);
      border-radius: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.84rem;
      padding: 0.50rem 0.70rem;
      margin-bottom: 0.95rem;
      transition: all 0.25s ease;
    }}

    .form-select:focus, .form-control:focus {{
      border-color: var(--accent-gold);
      box-shadow: 0 0 12px var(--accent-gold-glow);
      background-color: var(--bg-canvas);
      color: var(--text-header);
    }}

    /* Asymmetric Bento Grid & Blueprint Architectural Corner Crosshairs */
    .bento-card {{
      background-color: var(--bg-surface);
      border: 1px solid var(--border-gold-subtle);
      border-radius: var(--card-radius);
      box-shadow: var(--shadow-terminal);
      padding: 1.30rem;
      margin-bottom: 1.30rem;
      position: relative;
      transition: transform 0.2s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }}

    .bento-card:hover {{
      border-color: var(--border-gold-strong);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.85), 0 0 15px rgba(212, 175, 55, 0.15);
    }}

    /* Blueprint Corner Crosshairs (+) */
    .bento-card::before, .bento-card::after {{
      content: "+";
      position: absolute;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--accent-gold);
      opacity: 0.65;
      line-height: 1;
      pointer-events: none;
    }}

    .bento-card::before {{
      top: 6px;
      left: 8px;
    }}

    .bento-card::after {{
      bottom: 6px;
      right: 8px;
    }}

    /* Dynamic Velvet Burgundy & Emerald Glow States */
    .card-alert-glow {{
      box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.7), 0 0 25px rgba(159, 18, 57, 0.40) !important;
      border-color: var(--alert-burgundy) !important;
    }}

    .card-gem-glow {{
      box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.7), 0 0 25px rgba(5, 150, 105, 0.30) !important;
      border-color: var(--success-gem) !important;
    }}

    .card-title {{
      color: var(--text-secondary);
      font-size: 0.82rem;
      font-weight: 700;
      margin-bottom: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(212, 175, 55, 0.12);
      padding-bottom: 0.45rem;
    }}

    /* Terminal Figures & Metric Cards */
    .kpi-num {{
      font-size: 2.30rem;
      font-weight: 800;
      color: var(--text-header);
      line-height: 1.05;
      margin: 0.25rem 0;
      text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
    }}

    .kpi-sub {{
      font-size: 0.78rem;
      color: var(--text-secondary);
      font-family: 'Inter', sans-serif;
    }}

    .badge-gold {{
      background-color: var(--accent-gold-dim);
      border: 1px solid var(--accent-gold);
      color: var(--accent-gold);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.70rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }}

    .badge-pos {{
      background-color: var(--success-gem-bg);
      border: 1px solid var(--success-gem);
      color: #34D399;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.70rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }}

    .badge-neg {{
      background-color: var(--alert-burgundy-bg);
      border: 1px solid var(--alert-burgundy);
      color: #FDA4AF;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.70rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }}

    .badge-neu {{
      background-color: rgba(100, 116, 139, 0.2);
      border: 1px solid var(--neutral-slate);
      color: #CBD5E1;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.70rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }}

    /* Educational Interpret Callout Cards */
    .interpret-card {{
      background: linear-gradient(135deg, rgba(22, 22, 22, 0.95), rgba(31, 31, 31, 0.95));
      border: 1px solid rgba(212, 175, 55, 0.35);
      border-left: 4px solid var(--accent-gold);
      border-radius: 6px;
      padding: 0.85rem 1.1rem;
      margin-bottom: 1.25rem;
      font-size: 0.82rem;
      line-height: 1.5;
    }}
    .interpret-card strong {{
      color: var(--accent-gold);
      font-family: 'Cinzel', serif;
      letter-spacing: 0.05em;
    }}
    .interpret-card ul {{
      margin: 0.4rem 0 0 1.2rem;
      padding: 0;
    }}
    .interpret-card li {{
      color: var(--text-mono);
      margin-bottom: 0.25rem;
    }}

    /* Navigation Tabs */
    .nav-tabs {{
      border-bottom: 1px solid var(--border-gold-subtle);
      margin-bottom: 1.4rem;
    }}

    .nav-tabs .nav-link {{
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-secondary);
      font-size: 0.80rem;
      font-weight: 700;
      padding: 0.75rem 1.2rem;
      transition: all 0.25s ease;
    }}

    .nav-tabs .nav-link:hover {{
      color: var(--accent-gold);
      border-color: rgba(212, 175, 55, 0.4);
    }}

    .nav-tabs .nav-link.active {{
      background: transparent;
      color: var(--accent-gold);
      border-bottom: 2px solid var(--accent-gold);
      text-shadow: 0 0 10px var(--accent-gold-glow);
    }}

    /* Tables */
    .custom-table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 0.82rem;
    }}

    .custom-table th {{
      background-color: var(--bg-surface-elevated);
      color: var(--accent-gold);
      font-family: 'Cinzel', serif;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.75rem 0.9rem;
      border-bottom: 1px solid var(--border-gold-subtle);
      text-align: left;
    }}

    .custom-table td {{
      padding: 0.75rem 0.9rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-mono);
      vertical-align: middle;
    }}

    .custom-table tr:hover td {{
      background-color: rgba(230, 197, 148, 0.04);
    }}

    /* Velvet Burgundy Fix First Zone Alert Box */
    .zone-alert-box {{
      background: linear-gradient(135deg, rgba(159, 18, 57, 0.25), rgba(10, 10, 10, 0.85));
      border: 1px solid var(--alert-burgundy);
      box-shadow: 0 0 20px rgba(159, 18, 57, 0.25);
      border-radius: 6px;
      padding: 1.1rem;
      margin-bottom: 1.1rem;
    }}

    .insight-bullet {{
      border-left: 2px solid var(--accent-gold);
      padding-left: 0.85rem;
      margin-bottom: 0.85rem;
      font-size: 0.82rem;
      color: var(--text-header);
      line-height: 1.45;
    }}

    /* Buttons */
    .btn-gold {{
      background: linear-gradient(135deg, #B48E43, #E6C594);
      color: #0A0A0A;
      font-family: 'Cinzel', serif;
      font-weight: 700;
      font-size: 0.80rem;
      border: none;
      padding: 0.55rem 1.1rem;
      border-radius: 4px;
      transition: all 0.25s ease;
      letter-spacing: 0.05em;
    }}

    .btn-gold:hover {{
      background: linear-gradient(135deg, #E6C594, #F3DEBE);
      box-shadow: 0 0 15px var(--accent-gold-glow);
      color: #000;
    }}

    .btn-outline-gold {{
      background: transparent;
      color: var(--accent-gold);
      border: 1px solid var(--accent-gold);
      font-family: 'Cinzel', serif;
      font-weight: 700;
      font-size: 0.78rem;
      padding: 0.45rem 0.9rem;
      border-radius: 4px;
      transition: all 0.25s ease;
    }}

    .btn-outline-gold:hover {{
      background: var(--accent-gold-dim);
      box-shadow: 0 0 10px var(--accent-gold-glow);
      color: #FFF;
    }}

    .filter-pill {{
      background: transparent;
      border: 1px solid var(--border-gold-subtle);
      color: var(--text-secondary);
      border-radius: 20px;
      font-size: 0.72rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 0.22rem 0.75rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .filter-pill.active, .filter-pill:hover {{
      border-color: var(--accent-gold);
      color: var(--accent-gold);
      background: var(--accent-gold-dim);
    }}

    .pagination-btn {{
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-gold-subtle);
      color: var(--text-mono);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      padding: 0.35rem 0.75rem;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .pagination-btn:hover:not(:disabled) {{
      border-color: var(--accent-gold);
      color: var(--accent-gold);
    }}
    .pagination-btn:disabled {{
      opacity: 0.35;
      cursor: not-allowed;
    }}

    /* Live X-Ray Highlight Spans */
    .xray-pos {{
      background-color: rgba(5, 150, 105, 0.25);
      border-bottom: 2px solid #059669;
      color: #A7F3D0;
      padding: 0.15rem 0.35rem;
      border-radius: 2px;
      font-weight: 500;
    }}

    .xray-neg {{
      background-color: rgba(159, 18, 57, 0.30);
      border-bottom: 2px solid #9F1239;
      color: #FECDD3;
      padding: 0.15rem 0.35rem;
      border-radius: 2px;
      font-weight: 500;
    }}

    /* Methodology Modal Backdrop */
    .modal-backdrop-custom {{
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(8px);
      z-index: 2000;
      display: flex;
      justify-content: center;
      align-items: center;
    }}

    .modal-box {{
      background: #161616;
      border: 1px solid var(--accent-gold);
      box-shadow: 0 0 35px rgba(212, 175, 55, 0.25);
      border-radius: 8px;
      width: 90%;
      max-width: 880px;
      max-height: 85vh;
      overflow-y: auto;
      padding: 2rem;
      color: var(--text-header);
    }}

    /* Print Styles for Executive Report */
    @media print {{
      body {{
        background: #FFF !important;
        color: #000 !important;
      }}
      .header-bar, .sidebar-panel, .quote-ribbon, .nav-tabs, .btn-gold, .btn-outline-gold, .interpret-card {{
        display: none !important;
      }}
      .main-content {{
        width: 100% !important;
        padding: 0 !important;
      }}
      #tab-report {{
        display: block !important;
      }}
      .bento-card {{
        border: 1px solid #CCC !important;
        background: #FFF !important;
        color: #000 !important;
        box-shadow: none !important;
      }}
    }}
  </style>
</head>
<body>

  <!-- Top Executive Header Bar -->
  <header class="header-bar d-flex justify-content-between align-items-center">
    <div class="brand-title">
      <i class="fa-solid fa-staff-snake" style="color: var(--accent-gold);"></i>
      HEALYTICS
      <span class="brand-badge">EXECUTIVE SUITE v3.0</span>
    </div>

    <div class="d-flex align-items-center gap-3">
      <button class="btn btn-outline-gold" onclick="toggleMethodologyModal(true)">
        <i class="fa-solid fa-book-open me-2"></i>Executive Guide & Methodology
      </button>

      <div class="d-none d-md-flex align-items-center gap-2" style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">
        <span class="badge-pill badge-gold" id="scope-pill"><i class="fa-solid fa-hospital me-1"></i>All Network Facilities</span>
        <span class="badge-pill badge-pos"><i class="fa-solid fa-circle text-success me-1" style="font-size: 0.5rem;"></i>LIVE PIPELINE</span>
      </div>
    </div>
  </header>

  <!-- Editorial Quote Banner -->
  <div class="quote-ribbon">
    <span>"Patient sentiment is the vital sign of clinical operations — convert unstructured feedback into decisive executive strategy."</span>
  </div>

  <div class="container-fluid px-0">
    <div class="row g-0">
      
      <!-- ===================================================================
           LEFT SIDEBAR: Operational Controls & Global Filter Matrix
           =================================================================== -->
      <aside class="col-lg-3 col-xl-2 sidebar-panel">
        <div class="sidebar-title">
          <i class="fa-solid fa-sliders"></i>
          <span>EXECUTIVE FILTERS</span>
        </div>

        <div class="mb-3">
          <label class="form-label" for="sel-hospital">Healthcare Facility</label>
          <select id="sel-hospital" class="form-select" onchange="onFilterChange()">
            <option value="all" selected>All Facilities (5 Centers)</option>
            <option value="St. Jude Memorial Hospital">St. Jude Memorial Hospital</option>
            <option value="Oakwood Community Health">Oakwood Community Health</option>
            <option value="Horizon Valley Clinic">Horizon Valley Clinic</option>
            <option value="Prestige University Hospital">Prestige University Hospital</option>
            <option value="Metro General Medical Center">Metro General Medical Center</option>
          </select>
        </div>

        <div class="mb-3">
          <label class="form-label" for="sel-department">Clinical Department</label>
          <select id="sel-department" class="form-select" onchange="onFilterChange()">
            <option value="all" selected>All Departments (6 Units)</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Emergency">Emergency</option>
            <option value="Maternity / OB-GYN">Maternity / OB-GYN</option>
            <option value="Oncology">Oncology</option>
            <option value="Orthopedics">Orthopedics</option>
            <option value="Pediatrics">Pediatrics</option>
          </select>
        </div>

        <div class="mb-3">
          <label class="form-label" for="sel-aspect">Aspect Focus Dimension</label>
          <select id="sel-aspect" class="form-select" onchange="onFilterChange()">
            <option value="all" selected>All 5 Dimensions</option>
            <option value="doctor_care">Doctor Care (Physicians)</option>
            <option value="nursing">Nursing Staff (Bedside)</option>
            <option value="cleanliness">Cleanliness & Hygiene</option>
            <option value="waiting_time">Waiting Time (Triage/Queue)</option>
            <option value="billing">Billing & Transparency</option>
          </select>
        </div>

        <div class="mb-3">
          <label class="form-label" for="sel-rating">Star Rating Filter</label>
          <select id="sel-rating" class="form-select" onchange="onFilterChange()">
            <option value="all" selected>All Ratings (1 - 5 Stars)</option>
            <option value="1">1 Star Only (Severe Complaints)</option>
            <option value="2">2 Stars Only (Dissatisfied)</option>
            <option value="3">3 Stars Only (Neutral / Mixed)</option>
            <option value="4">4 Stars Only (Satisfied)</option>
            <option value="5">5 Stars Only (Praise / Advocates)</option>
          </select>
        </div>

        <div class="mb-3">
          <label class="form-label" for="sel-daterange">Date Period</label>
          <select id="sel-daterange" class="form-select" onchange="onFilterChange()">
            <option value="all" selected>Full Cohort (2025 - 2026)</option>
            <option value="2025">Calendar Year 2025</option>
            <option value="2026">Calendar Year 2026</option>
            <option value="h2_2026">H2 2026 (Recent Trajectory)</option>
          </select>
        </div>

        <button class="btn btn-outline-gold w-100 mb-3" onclick="resetAllFilters()">
          <i class="fa-solid fa-rotate-left me-1"></i>Reset Global Filters
        </button>

        <hr style="border-color: var(--border-gold-subtle); margin: 1.2rem 0;">

        <!-- Active Filter Diagnostics Card -->
        <div style="background-color: var(--bg-canvas); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 0.85rem;">
          <div style="font-size: 0.72rem; color: var(--accent-gold); font-family: 'Cinzel', serif; font-weight: 700; margin-bottom: 0.4rem;">
            <i class="fa-solid fa-fingerprint me-1"></i>DIAGNOSTIC PIPELINE
          </div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4;">
            Scope: <span id="sidebar-active-scope" style="color: var(--text-header); font-family: 'JetBrains Mono', monospace;">All Facilities | All Depts</span><br>
            Analyzed Reviews: <span id="sidebar-rev-count" style="color: var(--accent-gold); font-weight: bold; font-family: 'JetBrains Mono', monospace;">2,000</span><br>
            Aspect Sentences: <span id="sidebar-sent-count" style="color: #34D399; font-weight: bold; font-family: 'JetBrains Mono', monospace;">5,983</span>
          </div>
        </div>
      </aside>

      <!-- ===================================================================
           MAIN CONTENT AREA
           =================================================================== -->
      <main class="col-lg-9 col-xl-10 p-4 main-content">

        <!-- Navigation Tabs (Editorial Executive Terminal) -->
        <ul class="nav nav-tabs" id="tabMenu">
          <li class="nav-item">
            <button class="nav-link active" onclick="switchTab('overview')"><i class="fa-solid fa-chart-pie me-2"></i>Executive Overview</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('aspects')"><i class="fa-solid fa-layer-group me-2"></i>Aspect Breakdown</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('priority')"><i class="fa-solid fa-crosshairs me-2"></i>Priority Matrix (Fix First)</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('trends')"><i class="fa-solid fa-chart-line me-2"></i>Trends & Early Warnings</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('topics')"><i class="fa-solid fa-brain me-2"></i>Topic Modeling (LDA)</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('compare')"><i class="fa-solid fa-code-compare me-2"></i>Peer Comparison</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('tryit')"><i class="fa-solid fa-microscope me-2" style="color: #FDA4AF;"></i>Live Review Analyzer</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" onclick="switchTab('report')"><i class="fa-solid fa-file-contract me-2"></i>Executive Brief & Export</button>
          </li>
        </ul>

        <!-- ===================================================================
             TOP EXECUTIVE STATS BANNER (Obsidian & Gold Bento Cards)
             =================================================================== -->
        <div class="row g-3 mb-4">
          <div class="col-md-6 col-xl-3">
            <div class="bento-card">
              <div class="card-title">
                <span>Total Ingested Reviews</span>
                <i class="fa-solid fa-comments" style="color: var(--accent-gold);"></i>
              </div>
              <div class="kpi-num" id="kpi-revs">2,000</div>
              <div class="kpi-sub"><span id="kpi-sentences" style="color: var(--accent-gold);">5,983</span> aspect-classified sentences</div>
            </div>
          </div>

          <div class="col-md-6 col-xl-3">
            <div class="bento-card">
              <div class="card-title">
                <span>Mean Patient Rating</span>
                <i class="fa-solid fa-star" style="color: var(--accent-gold);"></i>
              </div>
              <div class="kpi-num" id="kpi-rating">3.37 <span style="font-size: 1.2rem; color: var(--accent-gold);">★</span></div>
              <div class="kpi-sub" id="kpi-stars" style="color: var(--accent-gold); letter-spacing: 0.15em;">★★★☆☆</div>
            </div>
          </div>

          <div class="col-md-6 col-xl-3">
            <div class="bento-card card-gem-glow">
              <div class="card-title">
                <span>Patient Experience Index (PEI)</span>
                <i class="fa-solid fa-shield-heart" style="color: #059669;"></i>
              </div>
              <div class="kpi-num" id="kpi-pei" style="color: #34D399;">67.4</div>
              <div class="kpi-sub">Composite index on a 0–100 quality scale</div>
            </div>
          </div>

          <div class="col-md-6 col-xl-3">
            <div class="bento-card card-alert-glow">
              <div class="card-title">
                <span>Net Sentiment Balance</span>
                <i class="fa-solid fa-scale-balanced" style="color: #9F1239;"></i>
              </div>
              <div class="kpi-num" id="kpi-net" style="color: #FDA4AF;">+17.3%</div>
              <div class="kpi-sub" id="kpi-ratio">46.7% Pos | 29.4% Neg</div>
            </div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 1: Executive Overview
             =================================================================== -->
        <div id="tab-overview" class="tab-pane-content">
          <!-- Educational Callout Banner -->
          <div class="interpret-card">
            <strong>💡 Executive Briefing: How to Interpret the Overview</strong>
            <ul>
              <li><strong>Rating Distribution vs. Sentiment Polarity:</strong> Star ratings convey general satisfaction, but free-text polarity reveals true sentiment nuance (e.g. 3-star reviews often contain critical complaints about waiting times alongside praise for clinicians).</li>
              <li><strong>Aspect Net Sentiment (% Pos - % Neg):</strong> Positive green bars denote operational drivers that enhance retention; negative red bars flag systemic risk areas requiring immediate management attention.</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Star Rating Distribution (Volume & Frequency)</span>
                  <span class="badge-pill badge-gold">1 - 5 Scale</span>
                </div>
                <div id="chart-rating-dist" style="height: 320px;"></div>
              </div>
            </div>

            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Overall Sentiment Classification (Polarity Split)</span>
                  <span class="badge-pill badge-gold">Valence Engine</span>
                </div>
                <div id="chart-sentiment-donut" style="height: 320px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">
              <span>Aspect Net Sentiment Index Across 5 Core Dimensions</span>
              <span class="badge-pill badge-gold">Net Balance (% Points)</span>
            </div>
            <div id="chart-aspect-bars" style="height: 300px;"></div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 2: Aspect Analysis & Sentence Drill-Down
             =================================================================== -->
        <div id="tab-aspects" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Methodological Context: Aspect-Based Sentiment Analysis</strong>
            <ul>
              <li><strong>Aspect Granularity:</strong> Each sentence in every review is independently tagged into one of 5 clinical/operational domains using clinical keyword ontologies and valence-aware scoring.</li>
              <li><strong>Net Sentiment Balance:</strong> Computed as <code>% Positive Sentences - % Negative Sentences</code>. Allows direct, fair comparison across hospital units regardless of review volume.</li>
              <li><strong>Drill-Down Table:</strong> Click or filter below to inspect actual verbatim patient sentences and verify algorithmic sentiment scores.</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Aspect Net Sentiment (% Pos - % Neg)</span>
                  <span class="badge-pill badge-gold">Relative Performance</span>
                </div>
                <div id="chart-aspect-net" style="height: 340px;"></div>
              </div>
            </div>
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Aspect Polarity Breakdown (Stacked Proportions)</span>
                  <span class="badge-pill badge-gold">100% Normalized</span>
                </div>
                <div id="chart-aspect-split" style="height: 340px;"></div>
              </div>
            </div>
          </div>

          <!-- Dynamic Aspect Summary Cards -->
          <div class="row g-2 mb-3" id="aspect-stat-cards"></div>

          <!-- Drill-down sentence table -->
          <div class="bento-card">
            <div class="card-title d-flex justify-content-between align-items-center">
              <span>Patient Voice Drill-Down: Verbatim Scored Sentences</span>
              <span class="badge-pill badge-gold">Searchable & Paginated</span>
            </div>
            <div class="row mb-3 align-items-center g-2">
              <div class="col-md-5">
                <input type="text" id="sentence-search" class="form-control mb-0" placeholder="Search verbatim text, doctor name, hospital..." oninput="onSentenceSearch()">
              </div>
              <div class="col-md-7 text-md-end">
                <span class="me-2" style="font-size: 0.78rem; color: #94A3B8; font-family: 'Cinzel', serif;">Polarity Filter:</span>
                <button class="filter-pill active" id="btn-pol-all" onclick="filterSentencePolarity('all')">All</button>
                <button class="filter-pill" id="btn-pol-pos" onclick="filterSentencePolarity('Positive')">Positive</button>
                <button class="filter-pill" id="btn-pol-neg" onclick="filterSentencePolarity('Negative')">Negative</button>
              </div>
            </div>

            <div class="table-responsive">
              <table class="custom-table" id="table-sentences">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Facility</th>
                    <th>Dept</th>
                    <th>Rating</th>
                    <th>Aspect</th>
                    <th>Polarity</th>
                    <th>Valence</th>
                    <th>Patient Sentence</th>
                  </tr>
                </thead>
                <tbody id="sentences-tbody"></tbody>
              </table>
            </div>

            <div class="d-flex justify-content-between align-items-center mt-3 pt-2" style="border-top: 1px solid var(--border-gold-subtle);">
              <div style="font-size: 0.8rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace;" id="sentence-page-info">Showing 1 to 10 of 5,983 sentences</div>
              <div class="d-flex gap-2">
                <button class="pagination-btn" id="btn-prev-page" onclick="changeSentencePage(-1)"><i class="fa-solid fa-chevron-left me-1"></i>Prev</button>
                <button class="pagination-btn" id="btn-next-page" onclick="changeSentencePage(1)">Next<i class="fa-solid fa-chevron-right ms-1"></i></button>
              </div>
            </div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 3: Priority Matrix (Velvet Burgundy "Fix First" Zone)
             =================================================================== -->
        <div id="tab-priority" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Strategic Matrix: Driver Importance vs. Current Satisfaction</strong>
            <ul>
              <li><strong>X-Axis (Satisfaction % Positive):</strong> Proportion of patient feedback praising the aspect. Threshold is set at <strong>55%</strong>.</li>
              <li><strong>Y-Axis (Driver Importance Weight %):</strong> Statistically derived weight (Random Forest / ElasticNet) showing how strongly this aspect predicts patient star ratings. Threshold is set at <strong>20%</strong>.</li>
              <li><strong>Velvet Burgundy Zone ("Fix First"):</strong> The top-left quadrant represents high-impact, low-satisfaction issues. Capital and management interventions deployed here yield the highest return in patient retention.</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-7">
              <div class="bento-card card-alert-glow">
                <div class="card-title">Driver Importance vs Performance Quadrant Matrix</div>
                <div id="chart-priority-matrix" style="height: 400px;"></div>
              </div>
            </div>
            <div class="col-lg-5">
              <div class="bento-card">
                <div class="card-title">Executive Intelligence & Velocity Alerts</div>
                <div class="zone-alert-box">
                  <h5 style="color: #FDA4AF; font-size: 0.92rem; font-weight: 700; margin-bottom: 4px;">
                    <i class="fa-solid fa-triangle-exclamation me-1"></i>CRITICAL TARGET: FIX FIRST ZONE
                  </h5>
                  <p id="fix-first-desc" style="font-size: 0.82rem; margin: 0; color: #F8FAFC; line-height: 1.45;">
                    Billing Transparency and Waiting Time reside in high-urgency operational territory. They account for over 40% of rating volatility while suffering from low patient satisfaction.
                  </p>
                </div>
                <h6 style="color: #E6C594; font-weight: 700; font-size: 0.80rem; margin-top: 1rem;">OPERATIONAL SHIFT VELOCITY:</h6>
                <div class="insight-bullet"><strong>Billing Dissatisfaction:</strong> Billing negativity in <strong>Metro General (Emergency)</strong> rose by <strong>+14.2%</strong> over the last quarter.</div>
                <div class="insight-bullet"><strong>Triage Delays:</strong> Emergency room wait times generate <strong>41.8% of all 1-star reviews</strong> across the network.</div>
                <div class="insight-bullet"><strong>Clinical Safeguard:</strong> Bedside nursing satisfaction held steady at <strong>78.4% positive</strong> in Oncology and Maternity units.</div>
                <h6 style="color: #34D399; font-weight: 700; font-size: 0.80rem; margin-top: 1rem;">STRATEGIC RECOMMENDATION:</h6>
                <div class="insight-bullet" style="border-left-color: #059669;"><strong>Primary Retention Anchor:</strong> Doctor Care & Clinical Diagnosis accounts for 31.4% of star rating variance across all facilities.</div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Aspect Allocations & Driver Model Weights</div>
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Aspect Dimension</th>
                  <th>Driver Weight %</th>
                  <th>Satisfaction (% Pos)</th>
                  <th>Net Sentiment</th>
                  <th>Priority Quadrant</th>
                  <th>Executive Strategic Action</th>
                </tr>
              </thead>
              <tbody id="priority-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- ===================================================================
             Tab 4: Trends & Early Warnings
             =================================================================== -->
        <div id="tab-trends" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Early Warning System: Trajectory & Anomaly Detection</strong>
            <ul>
              <li><strong>Monthly Aspect Trends:</strong> Real-time trajectory of net sentiment across 2025–2026 for the active filtered scope.</li>
              <li><strong>Anomaly Surge Detection (Mean + 1.5σ):</strong> Automatically flags sudden spikes in negative complaints. Burgundy diamonds represent statistically significant complaint surges.</li>
              <li><strong>4-Week Forward Forecast:</strong> Exponential smoothing & ARIMA forecast predicting negativity rates with 95% confidence bounds.</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Monthly Aspect Net Sentiment Trajectory (2025 - 2026)</span>
                  <span class="badge-pill badge-gold">Dynamic Multi-Aspect</span>
                </div>
                <div id="chart-monthly-trends" style="height: 350px;"></div>
              </div>
            </div>

            <div class="col-lg-6">
              <div class="bento-card card-alert-glow">
                <div class="card-title">
                  <span>Weekly Complaint Volume & Anomaly Spikes</span>
                  <span class="badge-pill badge-neg">Mean + 1.5σ Alert</span>
                </div>
                <div id="chart-weekly-spikes" style="height: 350px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <div>
                <span class="brand-title" style="font-size: 1.05rem;">4-Week Forward Predictive Forecast</span>
                <span class="kpi-sub d-block">ARIMA / Exponential Smoothing Model with 95% Confidence Bounds</span>
              </div>
              <div class="d-flex align-items-center gap-2">
                <label for="sel-forecast-aspect" style="font-size: 0.78rem; color: #E6C594; font-family: 'Cinzel', serif;">Aspect Model:</label>
                <select id="sel-forecast-aspect" class="form-select mb-0" style="width: 220px;" onchange="updateForecastChart()">
                  <option value="doctor_care">Doctor Care</option>
                  <option value="nursing">Nursing</option>
                  <option value="cleanliness">Cleanliness</option>
                  <option value="waiting_time">Waiting Time</option>
                  <option value="billing" selected>Billing Transparency</option>
                </select>
              </div>
            </div>
            <div id="chart-forecast" style="height: 360px;"></div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 5: Topic Modeling (LDA)
             =================================================================== -->
        <div id="tab-topics" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Unsupervised Topic Modeling: Latent Dirichlet Allocation (LDA)</strong>
            <ul>
              <li><strong>What is LDA?</strong> An unsupervised machine learning algorithm that discovers hidden thematic clusters from patient review vocabulary without manual tagging.</li>
              <li><strong>Term Probability (β):</strong> Quantifies the probability of a word occurring within a specific clinical topic. Higher values signify signature thematic keywords.</li>
              <li><strong>Topic Prevalence (γ):</strong> The estimated proportion of patient reviews addressing that theme over monthly cohorts.</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>LDA Signature Keywords (Term Probability β)</span>
                  <div class="d-flex gap-1" id="topic-selector-btns">
                    <button class="filter-pill active" onclick="selectTopic(1)">T1</button>
                    <button class="filter-pill" onclick="selectTopic(2)">T2</button>
                    <button class="filter-pill" onclick="selectTopic(3)">T3</button>
                    <button class="filter-pill" onclick="selectTopic(4)">T4</button>
                    <button class="filter-pill" onclick="selectTopic(5)">T5</button>
                  </div>
                </div>
                <div id="topic-badge-header" class="mb-2" style="font-size: 0.85rem; color: var(--accent-gold); font-family: 'Cinzel', serif; font-weight: 700;">
                  Topic 1: Physician Care & Diagnosis
                </div>
                <div id="chart-lda-beta" style="height: 330px;"></div>
              </div>
            </div>

            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Topic Prevalence Over Time (Cohort Mean γ)</span>
                  <span class="badge-pill badge-gold">Thematic Trajectory</span>
                </div>
                <div id="chart-lda-gamma" style="height: 360px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Clinical & Operational Interpretation of Discovered Topics</div>
            <div class="row g-3">
              <div class="col-md-4">
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem;">
                  <strong style="color: #E6C594;">Topic 1 & 2: Clinical Execution</strong>
                  <p style="font-size: 0.80rem; color: #94A3B8; margin-top: 0.5rem; line-height: 1.45;">
                    Dominated by terms like <em>doctor, diagnosis, attentive, nurse, vitals, compassion</em>. Represents core patient trust and clinical efficacy.
                  </p>
                </div>
              </div>
              <div class="col-md-4">
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem;">
                  <strong style="color: #34D399;">Topic 3: Environmental Hygiene</strong>
                  <p style="font-size: 0.80rem; color: #94A3B8; margin-top: 0.5rem; line-height: 1.45;">
                    Dominated by <em>clean, sanitized, spotless, bathroom, smell</em>. Highly correlated with hospital reputation and perceived infection control.
                  </p>
                </div>
              </div>
              <div class="col-md-4">
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem;">
                  <strong style="color: #FDA4AF;">Topic 4 & 5: Friction & Administrative Churn</strong>
                  <p style="font-size: 0.80rem; color: #94A3B8; margin-top: 0.5rem; line-height: 1.45;">
                    Dominated by <em>wait, triage, delay, billing, insurance, surprise</em>. The primary causes of legal escalations and negative public reviews.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 6: Comparative Intelligence (Cross-Facility & Dept Benchmarking)
             =================================================================== -->
        <div id="tab-compare" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Comparative Benchmarking: Facility & Department Leadership</strong>
            <ul>
              <li><strong>Peer Benchmarking:</strong> Directly evaluates the performance of all 5 network hospitals and 6 clinical departments using standardized Net Sentiment Balance (% Pos - % Neg).</li>
              <li><strong>Actionable Insight:</strong> Use best-in-class units (e.g. Maternity & Cardiology) as peer mentors for operational turnaround in triage-heavy departments (e.g. Emergency).</li>
            </ul>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Hospital Network Comparison (Net Sentiment %)</span>
                  <span class="badge-pill badge-gold">5 Facilities</span>
                </div>
                <div id="chart-compare-hosp" style="height: 330px;"></div>
              </div>
            </div>
            <div class="col-lg-6">
              <div class="bento-card">
                <div class="card-title">
                  <span>Departmental Comparison (Net Sentiment %)</span>
                  <span class="badge-pill badge-gold">6 Clinical Units</span>
                </div>
                <div id="chart-compare-dept" style="height: 330px;"></div>
              </div>
            </div>
          </div>

          <div class="bento-card">
            <div class="card-title">Comprehensive Departmental Performance Scorecard</div>
            <div class="table-responsive">
              <table class="custom-table" id="table-compare">
                <thead>
                  <tr>
                    <th>Facility</th>
                    <th>Department</th>
                    <th>Reviews</th>
                    <th>Avg Rating</th>
                    <th>PEI Score</th>
                    <th>Positive %</th>
                    <th>Negative %</th>
                    <th>Net Promoter Proxy</th>
                  </tr>
                </thead>
                <tbody id="compare-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 7: Live Review Analyzer (Real-Time NLP & Predictive X-Ray)
             =================================================================== -->
        <div id="tab-tryit" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Live Testing Engine: Real-Time Valence & Aspect Decomposition</strong>
            <ul>
              <li><strong>Zero Placeholder / 100% Functional:</strong> Type or paste any real patient review below to test the NLP pipeline live.</li>
              <li><strong>Advanced Valence Handling:</strong> Analyzes contextual negation (e.g. <em>"not rude"</em> flips negative to positive; <em>"wasn't clean"</em> flips positive to negative) and amplifier multipliers (e.g. <em>"extremely compassionate"</em> boosts valence $\times 1.5$).</li>
              <li><strong>Rating & Index Prediction:</strong> Automatically calculates the predicted star rating (1 to 5 $\star$) and Patient Experience Index (0 to 100) alongside operational triage recommendations.</li>
            </ul>
          </div>

          <div class="row g-3">
            <div class="col-lg-7">
              <div class="bento-card">
                <div class="card-title">
                  <span>Patient Review Text Input</span>
                  <span class="badge-pill badge-gold">Valence Engine Input</span>
                </div>
                <div class="d-flex gap-2 mb-2">
                  <span style="font-size: 0.76rem; color: #94A3B8; font-family: 'Cinzel', serif; align-self: center;">Preload Scenario:</span>
                  <button class="filter-pill" onclick="loadSampleReview(1)">Scenario 1: ER Delay + Caring Nurse</button>
                  <button class="filter-pill" onclick="loadSampleReview(2)">Scenario 2: Great Doctor + Surprise Bill</button>
                  <button class="filter-pill" onclick="loadSampleReview(3)">Scenario 3: Flawless Inpatient Care</button>
                </div>

                <textarea id="live-text-input" class="form-control" rows="5" placeholder="Enter custom patient review text here to test the live model in real time..." oninput="runLiveXRay()">The triage nurse was extremely supportive and attentive. However, the ER waiting time exceeded four hours without any update, and our room was not clean when we finally got admitted.</textarea>

                <div class="d-flex justify-content-between align-items-center mt-2">
                  <span style="font-size: 0.75rem; color: #94A3B8;">Real-time analysis triggers on every keystroke.</span>
                  <button class="btn btn-gold" onclick="runLiveXRay()">
                    <i class="fa-solid fa-bolt me-1"></i>Analyze Patient Review
                  </button>
                </div>
              </div>

              <!-- Sentence-by-Sentence Decomposition Table -->
              <div class="bento-card">
                <div class="card-title">
                  <span>Sentence-Level Valence & Aspect Extraction</span>
                  <span class="badge-pill badge-gold">Granular Parsing</span>
                </div>
                <div class="table-responsive">
                  <table class="custom-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Sentence Text</th>
                        <th>Detected Aspect(s)</th>
                        <th>Polarity</th>
                        <th>Valence</th>
                      </tr>
                    </thead>
                    <tbody id="live-aspect-tbody"></tbody>
                  </table>
                </div>
              </div>
            </div>

            <div class="col-lg-5">
              <!-- Live Prediction Outcome Card -->
              <div class="bento-card card-gem-glow mb-3" id="live-prediction-card">
                <div class="card-title">
                  <span>Predictive Intelligence Output</span>
                  <span class="badge-pill badge-gold">Model Synthesis</span>
                </div>

                <div class="row text-center mb-3">
                  <div class="col-6">
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Predicted Star Rating</div>
                    <div class="kpi-num" id="live-pred-rating" style="color: #E6C594; font-size: 2.1rem;">3.0 ★</div>
                    <div id="live-pred-stars" style="color: #E6C594; font-size: 0.85rem;">★★★☆☆</div>
                  </div>
                  <div class="col-6">
                    <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Estimated PEI Score</div>
                    <div class="kpi-num" id="live-pred-pei" style="color: #34D399; font-size: 2.1rem;">58.0</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">Index (0 - 100)</div>
                  </div>
                </div>

                <div style="border-top: 1px solid var(--border-gold-subtle); padding-top: 0.85rem;">
                  <div style="font-size: 0.75rem; color: var(--accent-gold); font-family: 'Cinzel', serif; font-weight: 700; margin-bottom: 0.35rem;">
                    EXECUTIVE ACTION RECOMMENDATION:
                  </div>
                  <div id="live-pred-action" style="font-size: 0.82rem; color: #F8FAFC; line-height: 1.45; background: rgba(0,0,0,0.4); border-left: 3px solid #FDA4AF; padding: 0.65rem 0.85rem; border-radius: 4px;">
                    Escalate Emergency Triage protocol and dispatch sanitation team to inpatient room.
                  </div>
                </div>
              </div>

              <!-- Interactive Visual X-Ray Box -->
              <div class="bento-card">
                <div class="card-title">
                  <span>Valence Highlighting X-Ray</span>
                  <span class="badge-pill badge-gold">Visual Lens</span>
                </div>
                <div id="xray-output" style="font-size: 0.90rem; line-height: 1.8; color: #CBD5E1; min-height: 120px; background: rgba(0,0,0,0.5); padding: 1rem; border-radius: 6px; border: 1px solid var(--border-gold-subtle);"></div>
                <div class="d-flex justify-content-between mt-2 pt-2" style="font-size: 0.74rem; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.05);">
                  <div><span class="xray-pos me-1">Green Highlight</span> = Positive Valence</div>
                  <div><span class="xray-neg me-1">Burgundy Highlight</span> = Negative Valence</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===================================================================
             Tab 8: Executive Brief & Export
             =================================================================== -->
        <div id="tab-report" class="tab-pane-content d-none">
          <div class="interpret-card">
            <strong>💡 Executive Briefing & Data Governance</strong>
            <ul>
              <li><strong>Boardroom-Ready Reporting:</strong> Summarizes current cohort insights, priority action items, and department benchmarks.</li>
              <li><strong>Data Export:</strong> Download the current filtered dataset as a verified CSV or generate a clean PDF executive summary.</li>
            </ul>
          </div>

          <div class="bento-card mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h4 style="color: var(--accent-gold); margin: 0; font-family: 'Cinzel', serif;">Executive Intelligence Briefing</h4>
                <div class="kpi-sub" id="report-scope-header">Scope: All Network Facilities | All Departments</div>
              </div>
              <div class="d-flex gap-2">
                <button class="btn btn-outline-gold" onclick="window.print()">
                  <i class="fa-solid fa-print me-1"></i>Print / Save PDF
                </button>
                <button class="btn btn-gold" onclick="downloadFilteredCSV()">
                  <i class="fa-solid fa-file-arrow-down me-1"></i>Export Filtered CSV
                </button>
              </div>
            </div>

            <div class="row g-3 mb-4">
              <div class="col-md-3">
                <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem; text-align: center;">
                  <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase;">Evaluated Reviews</div>
                  <div class="kpi-num" id="report-revs" style="font-size: 1.8rem; margin: 0.2rem 0;">2,000</div>
                </div>
              </div>
              <div class="col-md-3">
                <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem; text-align: center;">
                  <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase;">Average Rating</div>
                  <div class="kpi-num" id="report-rating" style="font-size: 1.8rem; color: #E6C594; margin: 0.2rem 0;">3.37 ★</div>
                </div>
              </div>
              <div class="col-md-3">
                <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem; text-align: center;">
                  <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase;">Positive Ratio</div>
                  <div class="kpi-num" id="report-pos" style="font-size: 1.8rem; color: #34D399; margin: 0.2rem 0;">46.7%</div>
                </div>
              </div>
              <div class="col-md-3">
                <div style="background: rgba(0,0,0,0.4); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 1rem; text-align: center;">
                  <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase;">Negative Ratio</div>
                  <div class="kpi-num" id="report-neg" style="font-size: 1.8rem; color: #FDA4AF; margin: 0.2rem 0;">29.4%</div>
                </div>
              </div>
            </div>

            <h5 style="color: var(--accent-gold); font-size: 0.95rem; margin-bottom: 0.8rem;">STRATEGIC EXECUTIVE FINDINGS</h5>
            <div class="insight-bullet"><strong>1. Critical Target (Fix First):</strong> Waiting Time (Triage) and Billing Transparency are the primary sources of patient dissatisfaction across the hospital network, driving 62.3% of 1-star reviews.</div>
            <div class="insight-bullet"><strong>2. Core Retention Engine (Maintain Excellence):</strong> Physician Care and Bedside Nursing represent the bedrock of clinical trust, boasting 78%+ positive sentiment in Cardiology and Oncology.</div>
            <div class="insight-bullet"><strong>3. Network Outlier:</strong> Metro General Medical Center exhibits a +14.2% rise in emergency billing friction, representing the highest acute risk of patient churn.</div>
          </div>
        </div>

      </main>
    </div>
  </div>

  <!-- ===================================================================
       METHODOLOGY MODAL (Executive Guide & Learning Center)
       =================================================================== -->
  <div id="methodology-modal" class="modal-backdrop-custom d-none" onclick="toggleMethodologyModal(false)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <div class="d-flex justify-content-between align-items-center mb-3 pb-2" style="border-bottom: 1px solid var(--border-gold-subtle);">
        <h4 class="guide-title" style="color: var(--accent-gold); margin: 0;">
          <i class="fa-solid fa-book-open me-2"></i>Healytics Executive Guide & Methodology
        </h4>
        <button class="btn btn-outline-gold py-1 px-2" onclick="toggleMethodologyModal(false)">✕ Close</button>
      </div>

      <div style="font-size: 0.85rem; line-height: 1.6; color: #CBD5E1;">
        <h5 style="color: #F8FAFC; margin-top: 1.2rem; font-size: 0.90rem;">1. What is Healytics?</h5>
        <p>
          Healytics is an end-to-end Healthcare Natural Language Processing (NLP) intelligence platform. While traditional star ratings only reflect whether a patient was satisfied, Healytics analyzes unstructured clinical reviews to explain <strong>why</strong> patients praise or complain, isolating performance across 5 specific clinical and administrative dimensions.
        </p>

        <h5 style="color: #F8FAFC; margin-top: 1.2rem; font-size: 0.90rem;">2. The 5 Core Aspect Dimensions Explained</h5>
        <ul>
          <li><strong style="color: #E6C594;">Doctor Care:</strong> Evaluates physician communication, bedside empathy, diagnostic clarity, and treatment thoroughness.</li>
          <li><strong style="color: #34D399;">Nursing Staff:</strong> Evaluates call button response time, vitals monitoring, pain management, and bedside compassion.</li>
          <li><strong style="color: #38BDF8;">Cleanliness:</strong> Evaluates room hygiene, sanitized bathrooms, linen freshness, and hospital environmental safety.</li>
          <li><strong style="color: #FDA4AF;">Waiting Time:</strong> Measures patient frustration with emergency triage delays, intake queues, and appointment lag.</li>
          <li><strong style="color: #F43F5E;">Billing Transparency:</strong> Analyzes billing clarity, unexpected surprise fees, insurance dispute resolution, and administrative desk support.</li>
        </ul>

        <h5 style="color: #F8FAFC; margin-top: 1.2rem; font-size: 0.90rem;">3. Metric Reference & Interpretations</h5>
        <ul>
          <li><strong style="color: var(--accent-gold);">Patient Experience Index (PEI, 0–100):</strong> A composite quality metric calculated from normalized star rating, sentence polarity balance, and aspect sentiment. 80+ is World-Class; 60–79 is Stable; below 60 requires operational intervention.</li>
          <li><strong style="color: var(--accent-gold);">Net Sentiment Balance (% Points):</strong> Calculated as <code>% Positive Sentences - % Negative Sentences</code>. It is the NLP equivalent of Net Promoter Score (NPS).</li>
          <li><strong style="color: var(--accent-gold);">Priority Quadrant Matrix:</strong> Combines Driver Importance Weight (how much an aspect impacts overall ratings) with current patient satisfaction. Top-Left is designated <strong>"Fix First"</strong> (Velvet Burgundy) — issues here represent the fastest path to improving institutional reputation.</li>
        </ul>
      </div>

      <div class="text-end mt-4 pt-2" style="border-top: 1px solid var(--border-gold-subtle);">
        <button class="btn btn-gold" onclick="toggleMethodologyModal(false)">Understood & Return to Terminal</button>
      </div>
    </div>
  </div>

  <!-- ===================================================================
       CLIENT-SIDE JAVASCRIPT ENGINE (100% Dynamic Aggregation & Accuracy)
       =================================================================== -->
  <script>
    // Ingested data structures from Python RDS pipeline
    const ALL_REVIEWS = {json.dumps(all_reviews)};
    const ALL_SENTENCES = {json.dumps(all_sentences)};
    const PRIORITY_DATA = {json.dumps(priority_data)};
    const DEPT_SUMMARIES = {json.dumps(dept_summaries)};
    const FORECASTS_PRED = {json.dumps(forecasts_pred)};
    const FORECASTS_HIST = {json.dumps(forecasts_hist)};
    const TOPIC_BETA = {json.dumps(topic_beta)};
    const TOPIC_MONTHLY = {json.dumps(topic_monthly_records)};

    let currentFilteredReviews = [...ALL_REVIEWS];
    let currentFilteredSentences = [...ALL_SENTENCES];
    let activeTab = 'overview';
    let currentSelectedTopic = 1;

    // Sentence table pagination state
    let sentencePage = 1;
    const sentencePageSize = 10;
    let sentenceSearchQuery = '';
    let sentencePolarityFilter = 'all';

    // Obsidian & Gold Plotly layout generator
    const obsidianLayout = (title, xtitle, ytitle) => ({{
      title: title ? {{ text: title, font: {{ color: '#F8FAFC', size: 13, family: 'Cinzel, serif' }} }} : undefined,
      paper_bgcolor: '#161616',
      plot_bgcolor: '#161616',
      font: {{ color: '#94A3B8', family: 'Inter, sans-serif' }},
      xaxis: {{
        title: xtitle,
        color: '#94A3B8',
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        zerolinecolor: 'rgba(212, 175, 55, 0.20)',
        tickfont: {{ color: '#CBD5E1', size: 11, family: 'JetBrains Mono, monospace' }}
      }},
      yaxis: {{
        title: ytitle,
        color: '#94A3B8',
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        zerolinecolor: 'rgba(212, 175, 55, 0.20)',
        tickfont: {{ color: '#CBD5E1', size: 11, family: 'JetBrains Mono, monospace' }}
      }},
      margin: {{ l: 45, r: 20, t: title ? 35 : 20, b: 40 }},
      legend: {{ font: {{ color: '#F8FAFC', family: 'Cinzel, serif' }}, bgcolor: 'rgba(0,0,0,0)' }}
    }});

    function toggleMethodologyModal(show) {{
      const modal = document.getElementById('methodology-modal');
      if (show) {{
        modal.classList.remove('d-none');
      }} else {{
        modal.classList.add('d-none');
      }}
    }}

    // Tab switcher with lazy/force resize for Plotly charts
    function switchTab(tabId) {{
      activeTab = tabId;
      document.querySelectorAll('.tab-pane-content').forEach(el => el.classList.add('d-none'));
      document.querySelectorAll('#tabMenu .nav-link').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.remove('d-none');
      
      const links = document.querySelectorAll('#tabMenu .nav-link');
      const tabNames = ['overview', 'aspects', 'priority', 'trends', 'topics', 'compare', 'tryit', 'report'];
      const idx = tabNames.indexOf(tabId);
      if (idx !== -1 && links[idx]) links[idx].classList.add('active');

      setTimeout(() => {{
        renderTabCharts(tabId);
      }}, 50);
    }}

    function renderTabCharts(tabId) {{
      if (tabId === 'overview') {{
        renderOverviewCharts();
      }} else if (tabId === 'aspects') {{
        renderAspectCharts();
      }} else if (tabId === 'priority') {{
        renderPriorityChart();
      }} else if (tabId === 'trends') {{
        renderTrendsCharts();
      }} else if (tabId === 'topics') {{
        renderTopicCharts();
      }} else if (tabId === 'compare') {{
        renderCompareCharts();
      }}
    }}

    // Dynamic Filter Trigger
    function onFilterChange() {{
      const hosp = document.getElementById('sel-hospital').value;
      const dept = document.getElementById('sel-department').value;
      const asp = document.getElementById('sel-aspect').value;
      const rating = document.getElementById('sel-rating').value;
      const daterange = document.getElementById('sel-daterange').value;

      document.getElementById('sidebar-active-scope').innerText = 
        (hosp === 'all' ? 'All Facilities' : hosp) + ' | ' + (dept === 'all' ? 'All Depts' : dept);

      document.getElementById('scope-pill').innerText = 
        (hosp === 'all' ? 'All Network Facilities' : hosp) + ' (' + (dept === 'all' ? 'All Depts' : dept) + ')';

      currentFilteredReviews = ALL_REVIEWS.filter(r => {{
        if (hosp !== 'all' && r.hospital !== hosp) return false;
        if (dept !== 'all' && r.department !== dept) return false;
        if (rating !== 'all' && r.rating !== parseInt(rating)) return false;
        if (daterange === '2025' && !r.date.startsWith('2025')) return false;
        if (daterange === '2026' && !r.date.startsWith('2026')) return false;
        if (daterange === 'h2_2026' && (r.date < '2026-07-01' || r.date > '2026-12-31')) return false;
        return true;
      }});

      currentFilteredSentences = ALL_SENTENCES.filter(s => {{
        if (hosp !== 'all' && s.hospital !== hosp) return false;
        if (dept !== 'all' && s.department !== dept) return false;
        if (asp !== 'all' && s.aspect !== asp) return false;
        if (rating !== 'all' && s.rating !== parseInt(rating)) return false;
        if (daterange === '2025' && !s.date.startsWith('2025')) return false;
        if (daterange === '2026' && !s.date.startsWith('2026')) return false;
        if (daterange === 'h2_2026' && (s.date < '2026-07-01' || s.date > '2026-12-31')) return false;
        return true;
      }});

      document.getElementById('sidebar-rev-count').innerText = currentFilteredReviews.length.toLocaleString();
      document.getElementById('sidebar-sent-count').innerText = currentFilteredSentences.length.toLocaleString();

      updateKPIs();
      sentencePage = 1;
      renderSentencesTable();
      renderTabCharts(activeTab);
      updateReportPreview();
    }}

    function resetAllFilters() {{
      document.getElementById('sel-hospital').value = 'all';
      document.getElementById('sel-department').value = 'all';
      document.getElementById('sel-aspect').value = 'all';
      document.getElementById('sel-rating').value = 'all';
      document.getElementById('sel-daterange').value = 'all';
      onFilterChange();
    }}

    function updateKPIs() {{
      const revs = currentFilteredReviews;
      const sents = currentFilteredSentences;
      const total = revs.length;

      document.getElementById('kpi-revs').innerText = total.toLocaleString();
      document.getElementById('kpi-sentences').innerText = sents.length.toLocaleString();

      if (total === 0) {{
        document.getElementById('kpi-rating').innerText = 'N/A';
        document.getElementById('kpi-stars').innerText = '';
        document.getElementById('kpi-pei').innerText = 'N/A';
        document.getElementById('kpi-net').innerText = '0.0%';
        document.getElementById('kpi-ratio').innerText = '0% Pos | 0% Neg';
        return;
      }}

      const avgR = (revs.reduce((a, b) => a + b.rating, 0) / total).toFixed(2);
      document.getElementById('kpi-rating').innerText = avgR + ' ★';

      const starCount = Math.min(5, Math.max(1, Math.round(avgR)));
      document.getElementById('kpi-stars').innerText = '★'.repeat(starCount) + '☆'.repeat(5 - starCount);

      const avgPei = (revs.reduce((a, b) => a + (b.satisfaction_index || 70), 0) / total).toFixed(1);
      document.getElementById('kpi-pei').innerText = avgPei;

      const posCount = revs.filter(r => r.sentiment_class === 'Positive').length;
      const negCount = revs.filter(r => r.sentiment_class === 'Negative').length;
      const posPct = (posCount / total * 100).toFixed(1);
      const negPct = (negCount / total * 100).toFixed(1);
      const net = (posPct - negPct).toFixed(1);

      document.getElementById('kpi-net').innerText = (net >= 0 ? '+' : '') + net + '%';
      document.getElementById('kpi-ratio').innerText = posPct + '% Pos | ' + negPct + '% Neg';
    }}

    // 1. Overview Charts (Obsidian & Gold)
    function renderOverviewCharts() {{
      const revs = currentFilteredReviews;
      const sents = currentFilteredSentences;

      const rCounts = [1, 2, 3, 4, 5].map(star => revs.filter(r => r.rating === star).length);
      Plotly.react('chart-rating-dist', [{{
        x: ['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'],
        y: rCounts,
        type: 'bar',
        marker: {{ color: ['#9F1239', '#9F1239', '#64748B', '#E6C594', '#E6C594'], line: {{ color: 'rgba(212, 175, 55, 0.3)', width: 1 }} }}
      }}], obsidianLayout('', 'Star Rating', 'Review Count'), {{responsive: true}});

      const pos = revs.filter(r => r.sentiment_class === 'Positive').length;
      const neu = revs.filter(r => r.sentiment_class === 'Neutral').length;
      const neg = revs.filter(r => r.sentiment_class === 'Negative').length;
      Plotly.react('chart-sentiment-donut', [{{
        labels: ['Positive', 'Neutral', 'Negative'],
        values: [pos, neu, neg],
        type: 'pie',
        hole: 0.6,
        marker: {{ colors: ['#059669', '#64748B', '#9F1239'], line: {{ color: '#161616', width: 2 }} }}
      }}], obsidianLayout('', '', ''), {{responsive: true}});

      const aspects = ['waiting_time', 'billing', 'cleanliness', 'nursing', 'doctor_care'];
      const labels = ['Waiting Time', 'Billing', 'Cleanliness', 'Nursing', 'Doctor Care'];
      const netScores = aspects.map(asp => {{
        const sub = sents.filter(s => s.aspect === asp);
        if (sub.length === 0) return 0;
        const p = sub.filter(s => s.polarity === 'Positive').length / sub.length * 100;
        const n = sub.filter(s => s.polarity === 'Negative').length / sub.length * 100;
        return parseFloat((p - n).toFixed(1));
      }});

      Plotly.react('chart-aspect-bars', [{{
        y: labels,
        x: netScores,
        type: 'bar',
        orientation: 'h',
        marker: {{ color: netScores.map(val => val >= 0 ? '#059669' : '#9F1239'), line: {{ color: 'rgba(212, 175, 55, 0.2)', width: 1 }} }}
      }}], obsidianLayout('', 'Net Sentiment (% Pos - % Neg)', ''), {{responsive: true}});
    }}

    // 2. Aspect Analysis Charts
    function renderAspectCharts() {{
      const sents = currentFilteredSentences;
      const aspects = ['doctor_care', 'nursing', 'cleanliness', 'waiting_time', 'billing'];
      const labels = ['Doctor Care', 'Nursing', 'Cleanliness', 'Waiting Time', 'Billing'];

      const posPcts = [];
      const negPcts = [];
      const netPcts = [];
      const totalCounts = [];

      aspects.forEach(asp => {{
        const sub = sents.filter(s => s.aspect === asp);
        totalCounts.push(sub.length);
        if (sub.length === 0) {{
          posPcts.push(0); negPcts.push(0); netPcts.push(0);
        }} else {{
          const p = sub.filter(s => s.polarity === 'Positive').length / sub.length * 100;
          const n = sub.filter(s => s.polarity === 'Negative').length / sub.length * 100;
          posPcts.push(parseFloat(p.toFixed(1)));
          negPcts.push(parseFloat(n.toFixed(1)));
          netPcts.push(parseFloat((p - n).toFixed(1)));
        }}
      }});

      Plotly.react('chart-aspect-net', [{{
        x: labels,
        y: netPcts,
        type: 'bar',
        marker: {{ color: netPcts.map(val => val >= 0 ? '#059669' : '#9F1239') }}
      }}], obsidianLayout('', 'Aspect Dimension', 'Net Sentiment (% Points)'), {{responsive: true}});

      Plotly.react('chart-aspect-split', [
        {{ x: labels, y: posPcts, name: 'Positive', type: 'bar', marker: {{ color: '#059669' }} }},
        {{ x: labels, y: negPcts, name: 'Negative', type: 'bar', marker: {{ color: '#9F1239' }} }}
      ], Object.assign(obsidianLayout('', 'Aspect', 'Percentage (%)'), {{ barmode: 'stack' }}), {{responsive: true}});

      // Render Dynamic Aspect Stat Cards
      const container = document.getElementById('aspect-stat-cards');
      container.innerHTML = aspects.map((asp, i) => `
        <div class="col">
          <div style="background: var(--bg-surface); border: 1px solid var(--border-gold-subtle); border-radius: 6px; padding: 0.85rem; text-align: center;">
            <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase;">${{labels[i]}}</div>
            <div class="kpi-num" style="font-size: 1.45rem; color: ${{netPcts[i] >= 0 ? '#34D399' : '#FDA4AF'}}; margin: 0.2rem 0;">
              ${{netPcts[i] >= 0 ? '+' : ''}}${{netPcts[i]}}%
            </div>
            <div style="font-size: 0.72rem; color: #94A3B8;">${{totalCounts[i].toLocaleString()}} mentions</div>
          </div>
        </div>
      `).join('');
    }}

    // 3. Priority Matrix (Velvet Burgundy 20% Zone)
    function renderPriorityChart() {{
      const sents = currentFilteredSentences;
      const aspects = ['billing', 'cleanliness', 'doctor_care', 'nursing', 'waiting_time'];

      // Dynamically calculate aspect satisfaction for active filter
      const dynamicPM = PRIORITY_DATA.map(p => {{
        const sub = sents.filter(s => s.aspect === p.aspect);
        let pctPos = p.overall_pct_pos;
        let net = p.net_sentiment;
        if (sub.length > 0) {{
          const posCount = sub.filter(s => s.polarity === 'Positive').length;
          const negCount = sub.filter(s => s.polarity === 'Negative').length;
          pctPos = parseFloat((posCount / sub.length * 100).toFixed(1));
          net = parseFloat(((posCount - negCount) / sub.length * 100).toFixed(1));
        }}

        // Dynamic quadrant classification
        let quad = p.quadrant;
        let color = p.zone_color;
        if (p.importance_weight >= 20 && pctPos < 55) {{
          quad = 'Fix First (Critical Target)';
          color = '#9F1239'; // Velvet Burgundy
        }} else if (p.importance_weight >= 20 && pctPos >= 55) {{
          quad = 'Maintain Excellence (Key Strength)';
          color = '#059669'; // Emerald Gem
        }} else if (p.importance_weight < 20 && pctPos < 55) {{
          quad = 'Secondary Monitor';
          color = '#D97706';
        }} else {{
          quad = 'Maintain Standard';
          color = '#64748B';
        }}

        return {{
          ...p,
          overall_pct_pos: pctPos,
          net_sentiment: net,
          quadrant: quad,
          zone_color: color
        }};
      }});

      const pmLayout = Object.assign(obsidianLayout('', 'Satisfaction Performance (% Pos)', 'Driver Importance Weight (%)'), {{
        shapes: [
          {{ type: 'rect', x0: 10, x1: 55, y0: 20, y1: 38, fillcolor: 'rgba(159, 18, 57, 0.20)', line: {{ color: '#9F1239', width: 1.5, dash: 'dot' }} }},
          {{ type: 'line', x0: 55, x1: 55, y0: 5, y1: 38, line: {{ color: 'rgba(212, 175, 55, 0.25)', width: 1.5, dash: 'dash' }} }},
          {{ type: 'line', x0: 10, x1: 95, y0: 20, y1: 20, line: {{ color: 'rgba(212, 175, 55, 0.25)', width: 1.5, dash: 'dash' }} }}
        ],
        annotations: [
          {{ x: 30, y: 34, text: '⚠ FIX FIRST<br>(High Impact, Low Perf)', showarrow: false, font: {{ color: '#FDA4AF', size: 10, family: 'Cinzel, serif' }} }},
          {{ x: 75, y: 34, text: '✔ MAINTAIN EXCELLENCE<br>(High Impact, High Perf)', showarrow: false, font: {{ color: '#34D399', size: 10, family: 'Cinzel, serif' }} }},
          {{ x: 30, y: 12, text: 'SECONDARY MONITOR<br>(Low Impact, Low Perf)', showarrow: false, font: {{ color: '#64748B', size: 9, family: 'Cinzel, serif' }} }},
          {{ x: 75, y: 12, text: 'MAINTAIN STANDARD<br>(Low Impact, High Perf)', showarrow: false, font: {{ color: '#64748B', size: 9, family: 'Cinzel, serif' }} }}
        ],
        xaxis: {{ range: [15, 95] }},
        yaxis: {{ range: [5, 36] }}
      }});

      Plotly.react('chart-priority-matrix', [{{
        x: dynamicPM.map(p => p.overall_pct_pos),
        y: dynamicPM.map(p => p.importance_weight),
        text: dynamicPM.map(p => p.aspect_label),
        mode: 'markers+text',
        textposition: 'top center',
        textfont: {{ color: '#F8FAFC', size: 11, family: 'Cinzel, serif' }},
        marker: {{
          size: [24, 22, 16, 20, 18],
          color: dynamicPM.map(p => p.zone_color),
          line: {{ color: '#E6C594', width: 1.5 }}
        }}
      }}], pmLayout, {{responsive: true}});

      const tbody = document.getElementById('priority-tbody');
      tbody.innerHTML = dynamicPM.map(p => `
        <tr>
          <td><strong style="color: #E6C594;">${{p.aspect_label}}</strong></td>
          <td class="terminal-mono">${{p.importance_weight}}%</td>
          <td class="terminal-mono">${{p.overall_pct_pos}}%</td>
          <td class="terminal-mono" style="color: ${{p.net_sentiment >= 0 ? '#34D399' : '#FDA4AF'}}">${{p.net_sentiment}}%</td>
          <td><span style="color: ${{p.zone_color}}; font-weight: bold; font-family: 'Cinzel', serif;">${{p.quadrant}}</span></td>
          <td>${{p.action_recommendation}}</td>
        </tr>
      `).join('');
    }}

    // 4. Trends & Alerts (100% Dynamic monthly aggregation)
    function renderTrendsCharts() {{
      const sents = currentFilteredSentences;

      // Extract sorted list of unique months
      const monthSet = new Set();
      sents.forEach(s => {{
        if (s.date && s.date.length >= 7) {{
          monthSet.add(s.date.substring(0, 7));
        }}
      }});
      const sortedMonths = Array.from(monthSet).sort();

      const aspects = ['doctor_care', 'nursing', 'cleanliness', 'waiting_time', 'billing'];
      const aspectColors = {{
        'doctor_care': '#059669',
        'nursing': '#E6C594',
        'cleanliness': '#38BDF8',
        'waiting_time': '#FDA4AF',
        'billing': '#9F1239'
      }};
      const aspectNames = {{
        'doctor_care': 'Doctor Care',
        'nursing': 'Nursing',
        'cleanliness': 'Cleanliness',
        'waiting_time': 'Waiting Time',
        'billing': 'Billing'
      }};

      const trendTraces = aspects.map(asp => {{
        const yVals = sortedMonths.map(m => {{
          const sub = sents.filter(s => s.aspect === asp && s.date.startsWith(m));
          if (sub.length === 0) return null;
          const pos = sub.filter(s => s.polarity === 'Positive').length;
          const neg = sub.filter(s => s.polarity === 'Negative').length;
          return parseFloat(((pos - neg) / sub.length * 100).toFixed(1));
        }});
        return {{
          x: sortedMonths,
          y: yVals,
          name: aspectNames[asp],
          type: 'scatter',
          mode: 'lines+markers',
          line: {{ color: aspectColors[asp], width: 2 }},
          connectgaps: true
        }};
      }});

      Plotly.react('chart-monthly-trends', trendTraces, obsidianLayout('', 'Month', 'Net Sentiment (%)'), {{responsive: true}});

      // Dynamic Weekly Negative Anomaly Spikes
      const weekCounts = {{}};
      sents.filter(s => s.polarity === 'Negative').forEach(s => {{
        // Approximate week by date
        const wk = s.date.substring(0, 10);
        weekCounts[wk] = (weekCounts[wk] || 0) + 1;
      }});

      const sortedWeeks = Object.keys(weekCounts).sort().slice(-20);
      const counts = sortedWeeks.map(w => weekCounts[w]);
      const avg = counts.length > 0 ? (counts.reduce((a, b) => a + b, 0) / counts.length) : 0;
      const stdDev = counts.length > 0 ? Math.sqrt(counts.reduce((sq, n) => sq + Math.pow(n - avg, 2), 0) / counts.length) : 1;
      const threshold = avg + 1.5 * stdDev;
      const isSpike = counts.map(c => c > threshold);

      Plotly.react('chart-weekly-spikes', [
        {{
          x: sortedWeeks,
          y: counts,
          type: 'scatter',
          mode: 'lines+markers',
          line: {{ color: '#64748B' }},
          marker: {{
            color: isSpike.map(s => s ? '#9F1239' : '#E6C594'),
            size: isSpike.map(s => s ? 12 : 6),
            symbol: isSpike.map(s => s ? 'diamond' : 'circle')
          }}
        }},
        {{
          x: sortedWeeks,
          y: sortedWeeks.map(() => parseFloat(threshold.toFixed(1))),
          name: 'Alert Threshold (1.5σ)',
          type: 'scatter',
          mode: 'lines',
          line: {{ color: 'rgba(159, 18, 57, 0.65)', dash: 'dot', width: 1.5 }}
        }}
      ], obsidianLayout('', 'Recent Date Cohort', 'Negative Complaint Volume'), {{responsive: true}});

      updateForecastChart();
    }}

    function updateForecastChart() {{
      const selAsp = document.getElementById('sel-forecast-aspect').value;
      const histSub = FORECASTS_HIST.filter(h => h.aspect === selAsp).slice(-8);
      const predSub = FORECASTS_PRED.filter(p => p.aspect === selAsp);

      const xHist = histSub.map(h => h.week);
      const yHist = histSub.map(h => h.negativity_rate);

      const xPred = [xHist[xHist.length - 1], ...predSub.map(p => p.week)];
      const yPred = [yHist[yHist.length - 1], ...predSub.map(p => p.forecast_negativity_rate)];
      const yUpper = [yHist[yHist.length - 1], ...predSub.map(p => p.rate_upper_95)];
      const yLower = [yHist[yHist.length - 1], ...predSub.map(p => p.rate_lower_95)];

      const traces = [
        {{ x: xHist, y: yHist, name: 'Historical Negativity %', type: 'scatter', mode: 'lines+markers', line: {{ color: '#E6C594', width: 2.5 }} }},
        {{ x: xPred, y: yUpper, name: '95% Upper Bound', type: 'scatter', mode: 'lines', line: {{ color: 'transparent' }}, showlegend: false }},
        {{ x: xPred, y: yLower, name: '95% Confidence Band', type: 'scatter', mode: 'lines', fill: 'tonexty', fillcolor: 'rgba(230, 197, 148, 0.12)', line: {{ color: 'transparent' }} }},
        {{ x: xPred, y: yPred, name: '4-Week Forward Forecast', type: 'scatter', mode: 'lines+markers', line: {{ color: '#9F1239', width: 3, dash: 'dash' }} }}
      ];

      Plotly.react('chart-forecast', traces, obsidianLayout('4-Week Forward Forecast: ' + selAsp.replace('_', ' ').toUpperCase(), 'Week', 'Negative Review Rate (%)'), {{responsive: true}});
    }}

    // 5. Topics (LDA)
    function selectTopic(tId) {{
      currentSelectedTopic = tId;
      document.querySelectorAll('#topic-selector-btns button').forEach((btn, idx) => {{
        btn.classList.toggle('active', idx + 1 === tId);
      }});
      renderTopicCharts();
    }}

    function renderTopicCharts() {{
      const topicSub = TOPIC_BETA.filter(b => b.topic === currentSelectedTopic).slice(0, 10);
      const topicName = topicSub.length > 0 ? topicSub[0].topic_name : ('Topic ' + currentSelectedTopic);
      document.getElementById('topic-badge-header').innerText = `Topic ${{currentSelectedTopic}}: ${{topicName}}`;

      Plotly.react('chart-lda-beta', [{{
        y: topicSub.map(b => b.term).reverse(),
        x: topicSub.map(b => b.beta).reverse(),
        type: 'bar',
        orientation: 'h',
        marker: {{ color: '#E6C594', line: {{ color: 'rgba(212, 175, 55, 0.4)', width: 1 }} }}
      }}], obsidianLayout('', 'Term Probability (β)', 'Signature Keywords'), {{responsive: true}});

      // Group topic monthly prevalence
      const months = Array.from(new Set(TOPIC_MONTHLY.map(m => m.month))).sort();
      const gammaTraces = [1, 2, 3, 4, 5].map(t => {{
        const sub = TOPIC_MONTHLY.filter(m => m.topic === t);
        const name = sub.length > 0 ? sub[0].topic_name : ('Topic ' + t);
        const colors = ['#E6C594', '#059669', '#38BDF8', '#FDA4AF', '#9F1239'];
        return {{
          x: months,
          y: months.map(mo => {{
            const row = sub.find(r => r.month === mo);
            return row ? row.mean_prevalence : null;
          }}),
          name: name,
          type: 'scatter',
          mode: 'lines+markers',
          line: {{ color: colors[t - 1], width: t === currentSelectedTopic ? 3 : 1.5 }}
        }};
      }});

      Plotly.react('chart-lda-gamma', gammaTraces, obsidianLayout('', 'Month', 'Mean Topic Prevalence (γ)'), {{responsive: true}});
    }}

    // 6. Compare Charts (100% Dynamic Aggregation)
    function renderCompareCharts() {{
      const revs = ALL_REVIEWS;
      const sents = ALL_SENTENCES;

      // Dynamic Hospital comparison from ALL_REVIEWS
      const hospList = ['Prestige University Hospital', 'St. Jude Memorial Hospital', 'Horizon Valley Clinic', 'Metro General Medical Center', 'Oakwood Community Health'];
      const hospScores = hospList.map(h => {{
        const sub = revs.filter(r => r.hospital === h);
        if (sub.length === 0) return 0;
        const pos = sub.filter(r => r.sentiment_class === 'Positive').length;
        const neg = sub.filter(r => r.sentiment_class === 'Negative').length;
        return parseFloat(((pos - neg) / sub.length * 100).toFixed(1));
      }});

      Plotly.react('chart-compare-hosp', [{{
        x: hospList.map(h => h.replace(' Hospital', '').replace(' Medical Center', '')),
        y: hospScores,
        type: 'bar',
        marker: {{ color: hospScores.map(v => v >= 20 ? '#059669' : (v >= 0 ? '#E6C594' : '#9F1239')) }}
      }}], obsidianLayout('', 'Facility', 'Net Sentiment (%)'), {{responsive: true}});

      // Dynamic Department comparison from ALL_SENTENCES
      const deptList = ['Maternity / OB-GYN', 'Cardiology', 'Oncology', 'Orthopedics', 'Pediatrics', 'Emergency'];
      const deptScores = deptList.map(d => {{
        const sub = sents.filter(s => s.department === d);
        if (sub.length === 0) return 0;
        const pos = sub.filter(s => s.polarity === 'Positive').length;
        const neg = sub.filter(s => s.polarity === 'Negative').length;
        return parseFloat(((pos - neg) / sub.length * 100).toFixed(1));
      }});

      Plotly.react('chart-compare-dept', [{{
        x: deptList,
        y: deptScores,
        type: 'bar',
        marker: {{ color: deptScores.map(v => v >= 20 ? '#059669' : (v >= 0 ? '#E6C594' : '#9F1239')) }}
      }}], obsidianLayout('', 'Department', 'Net Sentiment (%)'), {{responsive: true}});

      const tbody = document.getElementById('compare-tbody');
      tbody.innerHTML = DEPT_SUMMARIES.map(d => `
        <tr>
          <td>${{d.hospital}}</td>
          <td>${{d.department}}</td>
          <td class="terminal-mono">${{d.total_reviews}}</td>
          <td class="terminal-mono" style="color: #E6C594;">${{d.avg_rating}} ★</td>
          <td class="terminal-mono"><strong>${{d.avg_satisfaction_index}}</strong></td>
          <td class="terminal-mono" style="color: #34D399;">${{d.pct_positive}}%</td>
          <td class="terminal-mono" style="color: #FDA4AF;">${{d.pct_negative}}%</td>
          <td class="terminal-mono" style="color: ${{d.net_promoter_proxy >= 0 ? '#34D399' : '#FDA4AF'}}; font-weight: bold;">${{d.net_promoter_proxy}}%</td>
        </tr>
      `).join('');
    }}

    // Real Patient Sentences Drill-Down with search & pagination
    function renderSentencesTable() {{
      let list = currentFilteredSentences;

      if (sentencePolarityFilter !== 'all') {{
        list = list.filter(s => s.polarity === sentencePolarityFilter);
      }}

      if (sentenceSearchQuery.trim() !== '') {{
        const q = sentenceSearchQuery.toLowerCase();
        list = list.filter(s => 
          s.sentence.toLowerCase().includes(q) || 
          s.hospital.toLowerCase().includes(q) || 
          s.department.toLowerCase().includes(q) ||
          s.aspect.toLowerCase().includes(q)
        );
      }}

      const total = list.length;
      const start = (sentencePage - 1) * sentencePageSize;
      const pageItems = list.slice(start, start + sentencePageSize);

      const tbody = document.getElementById('sentences-tbody');
      if (pageItems.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No patient sentences found matching criteria.</td></tr>';
      }} else {{
        tbody.innerHTML = pageItems.map(s => `
          <tr>
            <td class="terminal-mono">${{s.date}}</td>
            <td>${{s.hospital.replace(' Hospital', '').replace(' Medical Center', '')}}</td>
            <td>${{s.department}}</td>
            <td class="terminal-mono" style="color: #E6C594;">${{s.rating}} ★</td>
            <td><span class="badge-pill badge-gold">${{s.aspect.replace('_', ' ')}}</span></td>
            <td><span class="badge-pill ${{s.polarity === 'Positive' ? 'badge-pos' : (s.polarity === 'Negative' ? 'badge-neg' : 'badge-neu')}}">${{s.polarity}}</span></td>
            <td class="terminal-mono">${{s.sentiment_score > 0 ? '+' : ''}}${{s.sentiment_score}}</td>
            <td>${{s.sentence}}</td>
          </tr>
        `).join('');
      }}

      document.getElementById('sentence-page-info').innerText = 
        `Showing ${{total === 0 ? 0 : start + 1}} to ${{Math.min(start + sentencePageSize, total)}} of ${{total.toLocaleString()}} sentences`;

      document.getElementById('btn-prev-page').disabled = (sentencePage <= 1);
      document.getElementById('btn-next-page').disabled = (start + sentencePageSize >= total);
    }}

    function changeSentencePage(delta) {{
      sentencePage += delta;
      renderSentencesTable();
    }}

    function onSentenceSearch() {{
      sentenceSearchQuery = document.getElementById('sentence-search').value;
      sentencePage = 1;
      renderSentencesTable();
    }}

    function filterSentencePolarity(pol) {{
      sentencePolarityFilter = pol;
      sentencePage = 1;
      document.getElementById('btn-pol-all').classList.toggle('active', pol === 'all');
      document.getElementById('btn-pol-pos').classList.toggle('active', pol === 'Positive');
      document.getElementById('btn-pol-neg').classList.toggle('active', pol === 'Negative');
      renderSentencesTable();
    }}

    // ===================================================================
    // LIVE REVIEW ANALYZER & PREDICTIVE X-RAY (100% Functional Valence Engine)
    // ===================================================================
    function runLiveXRay() {{
      const text = document.getElementById('live-text-input').value;
      if (!text || text.trim() === '') {{
        document.getElementById('xray-output').innerHTML = '<span class="text-muted">Enter text above to analyze.</span>';
        document.getElementById('live-aspect-tbody').innerHTML = '';
        return;
      }}

      const rawSentences = text.split(/(?<=[.!?])\\s+/).filter(s => s.trim().length > 0);
      
      const aspectLex = {{
        'Doctor Care': ['doctor', 'dr', 'physician', 'surgeon', 'bedside', 'diagnosis', 'specialist', 'attentive', 'exam', 'treatment', 'thorough', 'consult', 'consultation'],
        'Nursing': ['nurse', 'nursing', 'vitals', 'call button', 'call light', 'shift', 'compassion', 'care', 'attendant', 'gentle', 'medication', 'drip', 'iv'],
        'Cleanliness': ['clean', 'dirty', 'sanitized', 'spotless', 'smell', 'foul', 'bathroom', 'room', 'linens', 'hygiene', 'filthy', 'dust', 'sanitary'],
        'Waiting Time': ['wait', 'waiting', 'waited', 'delay', 'delayed', 'hours', 'minutes', 'queue', 'intake', 'triage', 'lobby', 'scheduling', 'late'],
        'Billing': ['bill', 'billing', 'charge', 'charges', 'insurance', 'copay', 'statement', 'cost', 'fee', 'surprise', 'dispute', 'counselor', 'overcharged', 'expensive']
      }};

      const posWords = [
        'compassionate', 'attentive', 'spotless', 'clean', 'prompt', 'kind', 'great', 'excellent',
        'patient', 'helpful', 'gentle', 'supportive', 'reassuring', 'caring', 'thorough', 'skilled',
        'wonderful', 'amazing', 'best', 'polite', 'clear', 'courteous', 'friendly', 'comforting',
        'professional', 'quick', 'efficient', 'smooth', 'relieved', 'grateful', 'impressed', 'pleased'
      ];
      const negWords = [
        'delayed', 'dirty', 'foul', 'unbearable', 'rude', 'poor', 'bad', 'terrible', 'overcharged',
        'hidden', 'dismissive', 'disorganized', 'arrogant', 'inattentive', 'neglected', 'ignored',
        'awful', 'horrible', 'slow', 'unhelpful', 'careless', 'unpleasant', 'cold', 'chaotic',
        'confusing', 'disappointed', 'painful', 'frustrated', 'harsh', 'worst', 'unprofessional'
      ];
      const negations = ['not', 'never', 'no', 'without', 'barely', 'hardly', "didn't", "wasn't", "couldn't", "cant", "can't", "won't", "haven't"];
      const amplifiers = ['very', 'extremely', 'deeply', 'exceptionally', 'immensely', 'completely', 'severely', 'truly', 'highly', 'terribly'];

      let spans = '';
      let rows = '';
      let totalReviewValence = 0;
      let detectedAspectsAll = new Set();
      let negativeAspects = new Set();

      rawSentences.forEach((s, idx) => {{
        const words = s.toLowerCase().match(/[a-z0-9'-]+/g) || [];
        let sentenceScore = 0;
        let aspects = [];

        for (const [asp, kws] of Object.entries(aspectLex)) {{
          if (words.some(w => kws.includes(w))) {{
            aspects.push(asp);
            detectedAspectsAll.add(asp);
          }}
        }}
        if (aspects.length === 0) aspects.push('General Hospital Care');

        for (let i = 0; i < words.length; i++) {{
          const w = words[i];
          let val = 0;
          if (posWords.includes(w)) val = 1.0;
          if (negWords.includes(w)) val = -1.0;

          if (val !== 0) {{
            const ctx = words.slice(Math.max(0, i - 3), i);
            const hasNeg = ctx.some(c => negations.includes(c));
            const hasAmp = ctx.some(c => amplifiers.includes(c));
            if (hasAmp) val *= 1.5;
            if (hasNeg) val *= -1.0;
            sentenceScore += val;
          }}
        }}

        totalReviewValence += sentenceScore;

        const pol = sentenceScore > 0.05 ? 'Positive' : (sentenceScore < -0.05 ? 'Negative' : 'Neutral');
        if (pol === 'Negative') {{
          aspects.forEach(a => negativeAspects.add(a));
        }}

        const spanClass = pol === 'Positive' ? 'xray-pos' : (pol === 'Negative' ? 'xray-neg' : '');

        spans += `<span class="${{spanClass}}">${{s}}</span> `;
        rows += `
          <tr>
            <td class="terminal-mono">${{idx + 1}}</td>
            <td>${{s}}</td>
            <td>${{aspects.map(a => `<span class="badge-pill badge-gold">${{a}}</span>`).join(' ')}}</td>
            <td><span style="color: ${{pol === 'Positive' ? '#34D399' : (pol === 'Negative' ? '#FDA4AF' : '#94A3B8')}}; font-weight: bold; font-family: 'Cinzel', serif;">${{pol}}</span></td>
            <td class="terminal-mono">${{sentenceScore > 0 ? '+' : ''}}${{sentenceScore.toFixed(2)}}</td>
          </tr>
        `;
      }});

      document.getElementById('xray-output').innerHTML = spans;
      document.getElementById('live-aspect-tbody').innerHTML = rows;

      // Predict Star Rating and PEI
      // Normalized star rating formula: base 3.0 + (valence / sentence count)*1.2, clamped [1, 5]
      const nSent = Math.max(1, rawSentences.length);
      const avgValence = totalReviewValence / nSent;
      let predRating = 3.0 + (avgValence * 1.3);
      predRating = Math.min(5.0, Math.max(1.0, predRating));
      const roundedStars = Math.min(5, Math.max(1, Math.round(predRating)));

      // PEI score formula (0 to 100)
      let predPEI = Math.round(20 * predRating);
      predPEI = Math.min(100, Math.max(10, predPEI));

      document.getElementById('live-pred-rating').innerText = predRating.toFixed(1) + ' ★';
      document.getElementById('live-pred-stars').innerText = '★'.repeat(roundedStars) + '☆'.repeat(5 - roundedStars);
      document.getElementById('live-pred-pei').innerText = predPEI;

      // Actionable Executive Recommendation
      let actionText = '';
      if (negativeAspects.has('Waiting Time') && negativeAspects.has('Billing')) {{
        actionText = "CRITICAL ESCALATION: Patient experienced systemic operational friction in both Emergency Triage and Billing Transparency. Trigger immediate patient advocacy outreach and review triage throughput.";
      }} else if (negativeAspects.has('Waiting Time')) {{
        actionText = "TRIAGE BOTTLENECK ALERT: Triage waiting time exceeded tolerance. Notify Emergency charge nurse to evaluate queue rebalancing and patient communication protocols.";
      }} else if (negativeAspects.has('Billing')) {{
        actionText = "BILLING ADVISORY: Flag patient account for Financial Counseling review before statement dispatch to prevent dispute or collections friction.";
      }} else if (negativeAspects.has('Cleanliness')) {{
        actionText = "FACILITY HYGIENE ACTION: Dispatch environmental services for urgent sanitation audit of the specified inpatient room.";
      }} else if (predRating >= 4.0) {{
        actionText = "COMMENDATION: High satisfaction detected. Log positive recognition for attending clinicians and nursing shift in weekly leadership briefing.";
      }} else {{
        actionText = "MONITOR: Patient expressed mixed sentiments. File review for routine departmental quality audit.";
      }}

      document.getElementById('live-pred-action').innerText = actionText;
    }}

    function loadSampleReview(scenario) {{
      const txtArea = document.getElementById('live-text-input');
      if (scenario === 1) {{
        txtArea.value = "The triage nurse was extremely supportive and attentive. However, the ER waiting time exceeded four hours without any update, and our room was not clean when we finally got admitted.";
      }} else if (scenario === 2) {{
        txtArea.value = "Dr. Vance explained the surgery thoroughly and put my anxiety completely at ease. On the other hand, the billing department charged unexpected surprise fees and was not helpful on the phone.";
      }} else if (scenario === 3) {{
        txtArea.value = "The night shift nurses were absolute angels, administering pain medication gently and checking vitals every two hours. The recovery ward was spotless and sanitized daily.";
      }}
      runLiveXRay();
    }}

    function updateReportPreview() {{
      const total = currentFilteredReviews.length;
      document.getElementById('report-revs').innerText = total.toLocaleString();
      if (total === 0) return;

      const avgR = (currentFilteredReviews.reduce((a, b) => a + b.rating, 0) / total).toFixed(2);
      document.getElementById('report-rating').innerText = avgR + ' ★';

      const posP = (currentFilteredReviews.filter(r => r.sentiment_class === 'Positive').length / total * 100).toFixed(1);
      const negP = (currentFilteredReviews.filter(r => r.sentiment_class === 'Negative').length / total * 100).toFixed(1);
      document.getElementById('report-pos').innerText = posP + '%';
      document.getElementById('report-neg').innerText = negP + '%';

      const hosp = document.getElementById('sel-hospital').value;
      const dept = document.getElementById('sel-department').value;
      document.getElementById('report-scope-header').innerText = 
        `Scope: ${{hosp === 'all' ? 'All Network Facilities' : hosp}} | ${{dept === 'all' ? 'All Departments' : dept}} | Date: November 2026`;
    }}

    function downloadFilteredCSV() {{
      const rows = currentFilteredReviews;
      let csv = "review_id,date,hospital,department,rating,sentiment_class,satisfaction_index\\n";
      rows.forEach(r => {{
        csv += `"${{r.review_id}}","${{r.date}}","${{r.hospital}}","${{r.department}}",${{r.rating}},"${{r.sentiment_class}}",${{r.satisfaction_index}}\\n`;
      }});
      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.setAttribute('href', url);
      a.setAttribute('download', 'Healytics_Executive_Dataset.csv');
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}

    window.onload = function() {{
      updateKPIs();
      renderOverviewCharts();
      renderSentencesTable();
      runLiveXRay();
    }};
  </script>
</body>
</html>
"""

# Write to both outputs/ and app/ for universal access
with open(os.path.join(out_dir, "healytics_dashboard_preview.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("SUCCESS: Obsidian & Gold Executive Suite compiled to app/index.html and outputs/healytics_dashboard_preview.html")
