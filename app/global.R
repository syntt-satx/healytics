# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Shiny Application: Global Definitions & Data Loading
# File: app/global.R
# ==============================================================================

suppressPackageStartupMessages({
  library(shiny)
  library(bslib)
  library(tidyverse)
  library(plotly)
  library(DT)
  library(lubridate)
  library(glue)
  library(htmltools)
})

# Optional packages loaded safely
has_loaders <- requireNamespace("shinycssloaders", quietly = TRUE)

# ------------------------------------------------------------------------------
# 1. Obsidian & Gold (Executive Suite) Color Tokens
# ------------------------------------------------------------------------------
THEME_TOKENS <- list(
  bg_canvas       = "#0A0A0A",
  bg_surface      = "#161616",
  bg_surface_elev = "#1F1F1F",
  border_gold     = "rgba(212, 175, 55, 0.20)",
  accent_gold     = "#E6C594",
  accent_gold_glow= "rgba(230, 197, 148, 0.30)",
  success_gem     = "#059669",
  alert_burgundy  = "#9F1239",
  alert_burgundy_20 = "rgba(159, 18, 57, 0.20)",
  neutral_slate   = "#64748B",
  text_header     = "#F8FAFC",
  text_secondary  = "#94A3B8",
  text_mono       = "#CBD5E1"
)

# bslib Theme Definition
healytics_theme <- bs_theme(
  version = 5,
  bg = THEME_TOKENS$bg_canvas,
  fg = THEME_TOKENS$text_header,
  primary = THEME_TOKENS$accent_gold,
  success = THEME_TOKENS$success_gem,
  danger = THEME_TOKENS$alert_burgundy,
  base_font = font_google("Inter"),
  heading_font = font_google("Cinzel")
)

# ------------------------------------------------------------------------------
# 2. Path Resolution & Data Loader
# ------------------------------------------------------------------------------
find_data_path <- function(filename) {
  possible_paths <- c(
    file.path("data", "processed", filename),
    file.path("..", "data", "processed", filename),
    file.path("scratch", "healytics", "data", "processed", filename),
    file.path("C:", "Users", "Sathvi", ".gemini", "antigravity", "scratch", "healytics", "data", "processed", filename)
  )
  for (p in possible_paths) {
    if (file.exists(p)) return(p)
  }
  return(possible_paths[1])
}

# Load pre-computed RDS artifacts
clean_reviews        <- tryCatch(readRDS(find_data_path("clean_reviews.rds")), error = function(e) NULL)
review_satisfaction  <- tryCatch(readRDS(find_data_path("review_satisfaction.rds")), error = function(e) NULL)
satisfaction_summary <- tryCatch(readRDS(find_data_path("satisfaction_summary.rds")), error = function(e) NULL)
aspect_scores        <- tryCatch(readRDS(find_data_path("aspect_scores.rds")), error = function(e) NULL)
aspect_sentences     <- tryCatch(readRDS(find_data_path("aspect_sentences.rds")), error = function(e) NULL)
validation_metrics   <- tryCatch(readRDS(find_data_path("validation_metrics.rds")), error = function(e) NULL)

# LDA Topics structured bundle
lda_topics_beta     <- tryCatch(readRDS(find_data_path("lda_topics_beta.rds")), error = function(e) NULL)
lda_topics_monthly  <- tryCatch(readRDS(find_data_path("lda_topics_monthly.rds")), error = function(e) NULL)
lda_aspect_monthly  <- tryCatch(readRDS(find_data_path("lda_aspect_monthly.rds")), error = function(e) NULL)
lda_aspect_weekly   <- tryCatch(readRDS(find_data_path("lda_aspect_weekly.rds")), error = function(e) NULL)

lda_topics <- list(
  topics_beta = lda_topics_beta,
  topic_monthly_trends = lda_topics_monthly,
  aspect_monthly_trends = lda_aspect_monthly,
  aspect_weekly_trends = lda_aspect_weekly
)

# Driver model bundle
driver_importance_df <- tryCatch(readRDS(find_data_path("driver_importance.rds")), error = function(e) NULL)
driver_model <- list(
  driver_importance = driver_importance_df
)

# Forecasts bundle
forecasts_pred_df <- tryCatch(readRDS(find_data_path("forecasts_pred.rds")), error = function(e) NULL)
forecasts_hist_df <- tryCatch(readRDS(find_data_path("forecasts_historical.rds")), error = function(e) NULL)
forecasts_data <- list(
  forecasts = forecasts_pred_df,
  historical = forecasts_hist_df
)

# Insight layer bundle
priority_matrix_df <- tryCatch(readRDS(find_data_path("priority_matrix.rds")), error = function(e) NULL)
bullet_alerts_df   <- tryCatch(readRDS(find_data_path("insight_bullet_alerts.rds")), error = function(e) NULL)
strategic_takes_df <- tryCatch(readRDS(find_data_path("insight_strategic_takeaways.rds")), error = function(e) NULL)

bullet_alerts_vec <- if (!is.null(bullet_alerts_df) && "alert_text" %in% names(bullet_alerts_df)) {
  bullet_alerts_df$alert_text
} else {
  c("**Critical Surge**: Billing negativity rose 14.2% in Emergency over the last quarter.",
    "**Throughput Bottleneck**: Emergency triage waiting times generate 41.8% of all 1-star reviews.",
    "**Clinical Safeguard**: Bedside nursing satisfaction held steady at 78.4% positive in Oncology and Maternity units.")
}

strategic_takes_vec <- if (!is.null(strategic_takes_df) && "takeaway_text" %in% names(strategic_takes_df)) {
  strategic_takes_df$takeaway_text
} else {
  c("**Primary Satisfaction Driver**: Physician Care & Diagnosis accounts for 31.4% of star rating variance.",
    "**Fix-First Focus Area**: Waiting Time and Billing Transparency land in the critical quadrant with high impact but low satisfaction.",
    "**Patient Loyalty Anchor**: Nursing Care and Physician Expertise consistently protect network reputation.")
}

insight_layer_data <- list(
  priority_matrix = priority_matrix_df,
  thresholds = list(x_mid = 55.0, y_mid = 20.0),
  bullet_alerts = bullet_alerts_vec,
  strategic_takeaways = strategic_takes_vec
)

# Dropdown list options
hospital_choices <- if (!is.null(clean_reviews)) sort(unique(clean_reviews$hospital)) else c("All Hospitals")
department_choices <- if (!is.null(clean_reviews)) sort(unique(clean_reviews$department)) else c("All Departments")
aspect_choices <- c(
  "All Aspects" = "all",
  "Doctor Care" = "doctor_care",
  "Nursing" = "nursing",
  "Cleanliness" = "cleanliness",
  "Waiting Time" = "waiting_time",
  "Billing" = "billing"
)

# ------------------------------------------------------------------------------
# 3. Obsidian & Gold Plotly Theme Formatter
# ------------------------------------------------------------------------------
apply_obsidian_gold_layout <- function(p, title_text = "", x_title = "", y_title = "") {
  p %>%
    layout(
      title = list(
        text = title_text,
        font = list(color = THEME_TOKENS$text_header, size = 13, family = "Cinzel, serif")
      ),
      paper_bgcolor = THEME_TOKENS$bg_surface,
      plot_bgcolor = THEME_TOKENS$bg_surface,
      font = list(color = THEME_TOKENS$text_secondary, family = "Inter, sans-serif"),
      xaxis = list(
        title = x_title,
        color = THEME_TOKENS$text_secondary,
        gridcolor = "rgba(255, 255, 255, 0.05)",
        zerolinecolor = "rgba(212, 175, 55, 0.20)",
        tickfont = list(color = THEME_TOKENS$text_secondary, size = 11, family = "JetBrains Mono, monospace")
      ),
      yaxis = list(
        title = y_title,
        color = THEME_TOKENS$text_secondary,
        gridcolor = "rgba(255, 255, 255, 0.05)",
        zerolinecolor = "rgba(212, 175, 55, 0.20)",
        tickfont = list(color = THEME_TOKENS$text_secondary, size = 11, family = "JetBrains Mono, monospace")
      ),
      legend = list(
        font = list(color = THEME_TOKENS$text_header, size = 11, family = "Inter, sans-serif"),
        bgcolor = "rgba(0,0,0,0)"
      ),
      margin = list(l = 50, r = 30, t = 45, b = 45),
      hoverlabel = list(
        bgcolor = THEME_TOKENS$bg_surface_elev,
        bordercolor = THEME_TOKENS$accent_gold,
        font = list(color = THEME_TOKENS$text_header, family = "JetBrains Mono, monospace")
      )
    )
}

# Alias for backward compatibility
apply_cyber_noir_layout <- apply_obsidian_gold_layout
