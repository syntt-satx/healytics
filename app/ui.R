# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Shiny Application: User Interface (Cyber-Noir Lavender Theme)
# File: app/ui.R
# ==============================================================================

source("global.R")

ui <- page_fluid(
  theme = healytics_theme,
  lang = "en",
  title = "Healytics | Executive Hospital NLP & Sentiment Command Center",
  
  # Custom Stylesheet and External Fonts (Cinzel, JetBrains Mono, Inter)
  tags$head(
    tags$link(rel = "preconnect", href = "https://fonts.googleapis.com"),
    tags$link(rel = "preconnect", href = "https://fonts.gstatic.com", crossorigin = NA),
    tags$link(href = "https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap", rel = "stylesheet"),
    tags$link(rel = "stylesheet", type = "text/css", href = "styles.css")
  ),
  
  # Top Navbar Header
  div(
    class = "navbar d-flex justify-content-between align-items-center mb-0",
    div(
      class = "navbar-brand",
      tags$span(style = "color: #E6C594; font-size: 1.4rem; margin-right: 6px;", "\u2726"),
      span("HEALYTICS", style = "font-weight: 800; letter-spacing: -0.02em; color: #F8FAFC;"),
      span("EXECUTIVE SUITE", class = "brand-badge ms-2"),
      span("Obsidian & Gold Intelligence Terminal", style = "font-size: 0.82rem; color: #94A3B8; margin-left: 14px; font-family: 'Cinzel', serif;")
    ),
    div(
      class = "d-flex align-items-center gap-3",
      span(class = "badge-pill badge-pos", "\u25CF Terminal Online"),
      span(style = "font-size: 0.8rem; color: #E6C594; font-family: 'JetBrains Mono', monospace;", format(Sys.Date(), "%B %Y"))
    )
  ),

  # Editorial Quote Ribbon
  div(
    class = "quote-ribbon mb-3",
    span("\u201CStar ratings conceal the truth; aspect-level clarity reveals where healing begins.\u201D"),
    span(class = "mx-2", "\u2022"),
    span("\u201CData without direction is noise. Healytics turns patient sentiment into executive precision.\u201D")
  ),
  
  # Main Layout: Sidebar Filters + Tabset Body
  layout_sidebar(
    sidebar = sidebar(
      width = 280,
      title = div(
        tags$span(style = "color: #E6C594;", "\u2699 "),
        span("EXECUTIVE SCOPE", class = "sidebar-title")
      ),
      
      selectInput(
        inputId = "filter_hospital",
        label = "Hospital Facility",
        choices = c("All Hospitals" = "all", setNames(hospital_choices, hospital_choices)),
        selected = "all"
      ),
      
      selectInput(
        inputId = "filter_department",
        label = "Clinical Department",
        choices = c("All Departments" = "all", setNames(department_choices, department_choices)),
        selected = "all"
      ),
      
      dateRangeInput(
        inputId = "filter_dates",
        label = "Review Date Window",
        start = as.Date("2025-01-01"),
        end   = as.Date("2026-10-31"),
        min   = as.Date("2025-01-01"),
        max   = as.Date("2026-10-31")
      ),
      
      selectInput(
        inputId = "filter_aspect",
        label = "Aspect Domain",
        choices = aspect_choices,
        selected = "all"
      ),
      
      hr(style = "border-color: #1E293B; margin: 1.2rem 0;"),
      
      actionButton(
        inputId = "reset_filters",
        label = "Reset All Filters",
        icon = icon("rotate-left"),
        class = "btn-outline w-100"
      ),
      
      div(
        class = "mt-4 pt-3 text-muted",
        style = "font-size: 0.75rem; border-top: 1px solid #1E293B;",
        p(strong("Architecture:"), " Precomputed .rds layer"),
        p(strong("Lexicons:"), " Bing, AFINN & valence-aware NLP"),
        p(strong("Version:"), " 2.4.0 (Cyber-Noir Edition)")
      )
    ),
    
    # Navigation Tabs
    navset_card_tab(
      id = "main_nav",
      
      # ------------------------------------------------------------------------
      # Tab 1: Overview
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Overview",
        icon = icon("gauge-high"),
        
        # Bento KPI Cards Row
        layout_column_wrap(
          width = 1/4,
          class = "mb-3",
          
          div(
            class = "bento-card kpi-container",
            div(class = "card-title", "Total Analyzed Reviews", span(class = "kpi-badge badge-gold", "Volume")),
            div(class = "kpi-number", textOutput("kpi_total_reviews")),
            div(class = "kpi-subtext", textOutput("kpi_total_sentences"), " scored sentences")
          ),
          
          div(
            class = "bento-card kpi-container",
            div(class = "card-title", "Average Star Rating", span(class = "kpi-badge badge-gold", "1 - 5 Stars")),
            div(class = "kpi-number", textOutput("kpi_avg_rating")),
            div(class = "kpi-subtext", uiOutput("kpi_rating_stars"))
          ),
          
          div(
            class = "bento-card kpi-container",
            div(class = "card-title", "Patient Experience Index", span(class = "kpi-badge badge-pos", "PEI 0-100")),
            div(class = "kpi-number", textOutput("kpi_pei")),
            div(class = "kpi-subtext", "Multi-lexicon satisfaction index")
          ),
          
          div(
            class = "bento-card kpi-container",
            div(class = "card-title", "Net Sentiment Balance", span(class = "kpi-badge badge-pos", "% Pos - % Neg")),
            div(class = "kpi-number", textOutput("kpi_net_sentiment")),
            div(class = "kpi-subtext", textOutput("kpi_pos_neg_ratio"))
          )
        ),
        
        # Charts Row: Rating Distribution & Sentiment Split
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Star Rating Distribution"),
            plotlyOutput("plot_rating_distribution", height = "320px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Overall Sentiment Classification (Bing / AFINN)"),
            plotlyOutput("plot_sentiment_breakdown", height = "320px")
          )
        ),
        
        # Bottom Summary: Core Aspect Quick Overview
        div(
          class = "bento-card",
          div(class = "card-title", "Core Hospital Dimensions: Snapshot Performance"),
          plotlyOutput("plot_overview_aspect_bars", height = "260px")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 2: Aspect Analysis
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Aspect Analysis",
        icon = icon("layer-group"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Aspect Net Sentiment (% Pos - % Neg)"),
            plotlyOutput("plot_aspect_net_sentiment", height = "330px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Aspect Sentiment Polarity Breakdown"),
            plotlyOutput("plot_aspect_polarity_split", height = "330px")
          )
        ),
        
        # Real Patient Sentence Drill-Down Table
        div(
          class = "bento-card",
          div(
            class = "card-title d-flex justify-content-between align-items-center",
            span("Patient Voice Drill-Down: Real Scored Sentences"),
            span(class = "kpi-badge badge-gold", "Valence-Aware Sentimentr Engine")
          ),
          p(style = "color: #94A3B8; font-size: 0.82rem; margin-bottom: 1rem;",
            "Review sentence-level extractions matching the current filters. Each sentence was evaluated for valence shifters, negations, and domain terminology."),
          DTOutput("table_aspect_sentences")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 3: Priority Matrix
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Priority Matrix",
        icon = icon("bullseye"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Importance vs. Performance Matrix"),
            p(style = "color: #94A3B8; font-size: 0.8rem; margin-bottom: 0.8rem;",
              "X-axis: Satisfaction Performance (% Pos). Y-axis: Driver Model Impact Weight (%). Top-Left is the 'Fix First' critical zone."),
            plotlyOutput("plot_priority_matrix", height = "380px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Auto-Generated Plain-English Executive Insights"),
            
            div(
              class = "zone-alert-box mb-3",
              h5("\u26A0 Critical Target: Fix First Zone"),
              textOutput("fix_first_summary_text")
            ),
            
            h6(style = "color: #E6C594; font-weight: 700; margin-top: 1rem; margin-bottom: 0.6rem; font-size: 0.85rem;", "KEY OPERATIONAL SHIFTS & VELOCITY:"),
            uiOutput("ui_bullet_alerts"),
            
            h6(style = "color: #E6C594; font-weight: 700; margin-top: 1.2rem; margin-bottom: 0.6rem; font-size: 0.85rem;", "STRATEGIC RECOMMENDATIONS:"),
            uiOutput("ui_strategic_takeaways")
          )
        ),
        
        # Quadrant Action Table
        div(
          class = "bento-card",
          div(class = "card-title", "Aspect Priority Allocations & Driver Model Weights"),
          DTOutput("table_priority_matrix")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 4: Trends & Alerts
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Trends & Alerts",
        icon = icon("chart-line"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Monthly Sentiment Trajectory by Aspect"),
            plotlyOutput("plot_monthly_trends", height = "340px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Weekly Negative Complaint Volume & Anomaly Flags"),
            plotlyOutput("plot_weekly_anomalies", height = "340px")
          )
        ),
        
        # 4-Week Forward Forecast Panel
        div(
          class = "bento-card",
          div(
            class = "card-title d-flex justify-content-between align-items-center",
            span("4-Week Time-Series Forward Forecast (ARIMA / ETS Model)"),
            span(class = "kpi-badge badge-pos", "Projections with 80% & 95% Confidence Intervals")
          ),
          p(style = "color: #94A3B8; font-size: 0.82rem; margin-bottom: 0.8rem;",
            "Predictive forward outlook of weekly negative complaint rates per aspect to assist operational staffing and risk mitigation."),
          plotlyOutput("plot_forecast_panel", height = "360px")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 5: Topics
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Topics (LDA)",
        icon = icon("brain"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Latent Dirichlet Allocation: Top Topic Terms (\u03B2)"),
            plotlyOutput("plot_lda_terms", height = "380px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Topic Prevalence Longitudinal Shift (\u03B3)"),
            plotlyOutput("plot_topic_prevalence", height = "380px")
          )
        ),
        
        div(
          class = "bento-card",
          div(class = "card-title", "Clinical Topic Semantic Dictionary"),
          DTOutput("table_topic_terms")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 6: Compare
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Compare",
        icon = icon("code-compare"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Peer Benchmarking: Net Sentiment by Hospital"),
            plotlyOutput("plot_compare_hospitals", height = "360px")
          ),
          
          div(
            class = "bento-card",
            div(class = "card-title", "Department-Level Aspect Performance Heatmap"),
            plotlyOutput("plot_compare_departments", height = "360px")
          )
        ),
        
        div(
          class = "bento-card",
          div(class = "card-title", "Institutional Scorecard & Ranking Table"),
          DTOutput("table_compare_rankings")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 7: Try It (Live Analyzer / "X-Ray Lens")
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Try It (Live Analyzer)",
        icon = icon("wand-magic-sparkles"),
        
        layout_column_wrap(
          width = 1/2,
          class = "mb-3",
          
          div(
            class = "bento-card",
            div(class = "card-title", "Live Patient Review Input"),
            p(style = "color: #94A3B8; font-size: 0.82rem; margin-bottom: 0.8rem;",
              "Paste any real or synthetic review text below. Healytics will run live sentence tokenization, aspect mapping, and negation-aware sentiment scoring."),
            
            textAreaInput(
              inputId = "live_review_input",
              label = "Patient Feedback Text:",
              value = "The attending doctor was exceptionally compassionate and explained every surgical detail with great patience. However, the waiting time in the emergency lobby exceeded four hours, and our room was not sanitized when we arrived.",
              rows = 5,
              width = "100%"
            ),
            
            actionButton(
              inputId = "btn_analyze_live",
              label = "Analyze Feedback with X-Ray Lens",
              icon = icon("magnifying-glass-chart"),
              class = "btn-primary mt-2"
            )
          ),
          
          div(
            class = "bento-card",
            div(
              class = "card-title d-flex justify-content-between align-items-center",
              span("X-Ray Sentiment Lens Output"),
              span(class = "kpi-badge badge-pos", "Real-Time Highlighter")
            ),
            p(style = "color: #94A3B8; font-size: 0.82rem; margin-bottom: 0.6rem;",
              "Sentences highlighted in luminous green (Positive) or sharp rose (Negative) with valence resolution:"),
            uiOutput("xray_annotated_text")
          )
        ),
        
        div(
          class = "bento-card",
          div(class = "card-title", "Live Extracted Aspect Metrics"),
          DTOutput("table_live_aspect_breakdown")
        )
      ),
      
      # ------------------------------------------------------------------------
      # Tab 8: Management Report
      # ------------------------------------------------------------------------
      nav_panel(
        title = "Report",
        icon = icon("file-lines"),
        
        div(
          class = "bento-card",
          div(
            class = "card-title d-flex justify-content-between align-items-center",
            span("Executive Management Summary Report"),
            downloadButton("download_report_csv", "Export Executive Data (.CSV)", class = "btn-primary")
          ),
          p(style = "color: #94A3B8; font-size: 0.85rem; margin-bottom: 1.2rem;",
            "Review the synthesized executive decision support briefing generated from current operational filters."),
          
          div(
            style = "background: #0B0D17; border: 1px solid #1E293B; border-radius: 10px; padding: 1.5rem; line-height: 1.7;",
            uiOutput("ui_report_preview")
          )
        )
      )
    )
  )
)
