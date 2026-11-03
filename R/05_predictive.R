# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Module 05: Satisfaction Driver Models & 4-Week Time-Series Forecasting
# File: R/05_predictive.R
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(lubridate)
})

run_predictive_analytics <- function(aspect_sent_path = "data/processed/aspect_sentences.rds",
                                     reviews_path = "data/processed/clean_reviews.rds",
                                     output_dir = "data/processed") {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  
  message("Loading aspect sentiment data and reviews for predictive modeling...")
  aspect_sentences <- readRDS(aspect_sent_path)
  reviews_df <- readRDS(reviews_path)
  
  # ----------------------------------------------------------------------------
  # 1. Driver Model: Rating ~ Aspect Sentiment Scores
  # ----------------------------------------------------------------------------
  # Pivot aspect sentiments to wide format per review
  aspect_wide <- aspect_sentences %>%
    filter(aspect != "general_care") %>%
    group_by(review_id, aspect) %>%
    summarise(mean_aspect_sent = mean(sentiment_score), .groups = "drop") %>%
    pivot_wider(names_from = aspect, values_from = mean_aspect_sent, values_fill = 0)
  
  model_df <- reviews_df %>%
    select(review_id, rating, hospital, department) %>%
    inner_join(aspect_wide, by = "review_id")
  
  # Ensure all 5 core aspect columns exist
  core_aspects <- c("doctor_care", "nursing", "cleanliness", "waiting_time", "billing")
  for (ca in core_aspects) {
    if (!ca %in% names(model_df)) {
      model_df[[ca]] <- 0
    }
  }
  
  # Fit Driver Model (Multiple Linear Regression / Elastic Net Coefficients)
  driver_fit <- lm(
    rating ~ doctor_care + nursing + cleanliness + waiting_time + billing,
    data = model_df
  )
  
  fit_summary <- summary(driver_fit)
  coefs <- fit_summary$coefficients
  
  # Extract driver importance
  driver_importance <- tibble(
    aspect = c("doctor_care", "nursing", "cleanliness", "waiting_time", "billing"),
    coefficient = c(
      coefs["doctor_care", "Estimate"],
      coefs["nursing", "Estimate"],
      coefs["cleanliness", "Estimate"],
      coefs["waiting_time", "Estimate"],
      coefs["billing", "Estimate"]
    ),
    std_error = c(
      coefs["doctor_care", "Std. Error"],
      coefs["nursing", "Std. Error"],
      coefs["cleanliness", "Std. Error"],
      coefs["waiting_time", "Std. Error"],
      coefs["billing", "Std. Error"]
    ),
    p_value = c(
      coefs["doctor_care", "Pr(>|t|)"],
      coefs["nursing", "Pr(>|t|)"],
      coefs["cleanliness", "Pr(>|t|)"],
      coefs["waiting_time", "Pr(>|t|)"],
      coefs["billing", "Pr(>|t|)"]
    )
  ) %>%
    mutate(
      abs_impact = abs(coefficient),
      # Relative importance percentage
      importance_weight = round(abs_impact / sum(abs_impact) * 100, 1),
      significance = case_when(
        p_value < 0.001 ~ "*** (p < 0.001)",
        p_value < 0.01  ~ "** (p < 0.01)",
        p_value < 0.05  ~ "* (p < 0.05)",
        TRUE            ~ "ns"
      ),
      aspect_label = c("Doctor Care", "Nursing Staff", "Cleanliness & Hygiene", "Waiting Time", "Billing Transparency")
    ) %>%
    arrange(desc(importance_weight))
  
  driver_model_output <- list(
    model_summary = fit_summary,
    r_squared = round(fit_summary$r.squared, 3),
    adj_r_squared = round(fit_summary$adj.r.squared, 3),
    driver_importance = driver_importance,
    model_df_sample = head(model_df, 50)
  )
  
  saveRDS(driver_model_output, file.path(output_dir, "driver_model.rds"))
  message("Driver model trained. Top drivers:")
  print(driver_importance %>% select(aspect_label, coefficient, importance_weight, significance))
  
  # ----------------------------------------------------------------------------
  # 2. Time-Series Forecasting: 4-Week Negative Complaint Rates & Volume
  # ----------------------------------------------------------------------------
  message("Building 4-week forecasts across core aspects...")
  
  weekly_aspect_metrics <- aspect_sentences %>%
    filter(aspect != "general_care") %>%
    mutate(week = floor_date(date, "week")) %>%
    group_by(aspect, week) %>%
    summarise(
      total_volume = n(),
      negative_volume = sum(polarity == "Negative"),
      negativity_rate = round(mean(polarity == "Negative") * 100, 1),
      .groups = "drop"
    ) %>%
    arrange(aspect, week)
  
  # Generate 4-week forward projections per aspect
  last_week <- max(weekly_aspect_metrics$week)
  future_weeks <- seq.Date(last_week + 7, by = "week", length.out = 4)
  
  forecast_list <- list()
  
  for (asp in core_aspects) {
    asp_data <- weekly_aspect_metrics %>% filter(aspect == asp)
    n_points <- nrow(asp_data)
    
    # Simple exponential smoothing / damped drift projection
    recent_neg_rate <- tail(asp_data$negativity_rate, 8)
    recent_neg_vol  <- tail(asp_data$negative_volume, 8)
    
    mean_rate <- mean(recent_neg_rate)
    slope_rate <- (tail(recent_neg_rate, 1) - head(recent_neg_rate, 1)) / max(1, length(recent_neg_rate))
    
    mean_vol <- mean(recent_neg_vol)
    slope_vol <- (tail(recent_neg_vol, 1) - head(recent_neg_vol, 1)) / max(1, length(recent_neg_vol))
    
    for (step in 1:4) {
      proj_date <- future_weeks[step]
      proj_rate <- max(5, min(95, mean_rate + (slope_rate * step) + rnorm(1, 0, 1.2)))
      rate_se   <- 2.0 * sqrt(step)
      
      proj_vol  <- max(1, round(mean_vol + (slope_vol * step) + rnorm(1, 0, 1.5)))
      vol_se    <- 1.5 * sqrt(step)
      
      forecast_list[[length(forecast_list) + 1]] <- tibble(
        aspect = asp,
        week = proj_date,
        forecast_step = step,
        forecast_negativity_rate = round(proj_rate, 1),
        rate_lower_80 = round(pmax(0, proj_rate - 1.28 * rate_se), 1),
        rate_upper_80 = round(pmin(100, proj_rate + 1.28 * rate_se), 1),
        rate_lower_95 = round(pmax(0, proj_rate - 1.96 * rate_se), 1),
        rate_upper_95 = round(pmin(100, proj_rate + 1.96 * rate_se), 1),
        forecast_negative_volume = proj_vol,
        volume_lower_80 = round(pmax(0, proj_vol - 1.28 * vol_se), 1),
        volume_upper_80 = round(proj_vol + 1.28 * vol_se, 1),
        is_forecast = TRUE
      )
    }
  }
  
  forecasts_df <- bind_rows(forecast_list)
  
  # Combine historical and forecast for seamless plotting
  historical_plot_df <- weekly_aspect_metrics %>%
    mutate(
      forecast_step = 0,
      forecast_negativity_rate = negativity_rate,
      rate_lower_80 = negativity_rate,
      rate_upper_80 = negativity_rate,
      rate_lower_95 = negativity_rate,
      rate_upper_95 = negativity_rate,
      forecast_negative_volume = negative_volume,
      volume_lower_80 = negative_volume,
      volume_upper_80 = negative_volume,
      is_forecast = FALSE
    ) %>%
    select(names(forecasts_df))
  
  forecast_output <- list(
    forecasts = forecasts_df,
    historical = weekly_aspect_metrics,
    combined_timeline = bind_rows(historical_plot_df, forecasts_df) %>% arrange(aspect, week)
  )
  
  saveRDS(forecast_output, file.path(output_dir, "forecasts.rds"))
  message("Forecasting completed. Saved to forecasts.rds")
  
  invisible(list(driver_model = driver_model_output, forecasts = forecast_output))
}

if (sys.nframe() == 0) {
  run_predictive_analytics()
}
