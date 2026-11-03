# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Module 02: Overall Satisfaction & Lexicon Sentiment Analysis
# File: R/02_satisfaction.R
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(tidytext)
})

run_satisfaction_analysis <- function(tokens_path = "data/processed/clean_tokens.rds",
                                      reviews_path = "data/processed/clean_reviews.rds",
                                      output_dir = "data/processed") {
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  
  message("Loading tokens and reviews for lexicon satisfaction scoring...")
  tokens_df  <- readRDS(tokens_path)
  reviews_df <- readRDS(reviews_path)
  
  # Standard Bing lexicon mapping (fallback embedded if lexicon package unavailable)
  bing_lexicon <- tryCatch({
    get_sentiments("bing")
  }, error = function(e) {
    tibble(
      word = c(
        "excellent", "outstanding", "great", "good", "compassionate", "attentive",
        "clean", "spotless", "swift", "seamless", "helpful", "gentle", "pristine",
        "poor", "bad", "terrible", "awful", "rude", "horrible", "delayed", "dirty",
        "foul", "unbearable", "arrogant", "inattentive", "careless", "outrageous",
        "confusing", "painful", "expensive", "hidden"
      ),
      sentiment = c(rep("positive", 13), rep("negative", 18))
    )
  })
  
  # AFINN lexicon mapping (-5 to +5)
  afinn_lexicon <- tryCatch({
    get_sentiments("afinn")
  }, error = function(e) {
    tibble(
      word = c(
        "excellent", "outstanding", "great", "good", "compassionate", "attentive",
        "clean", "spotless", "swift", "seamless", "helpful", "gentle",
        "poor", "bad", "terrible", "awful", "rude", "horrible", "delayed", "dirty",
        "foul", "unbearable", "arrogant", "inattentive", "careless", "outrageous"
      ),
      value = c(5, 5, 4, 3, 4, 3, 3, 4, 3, 3, 3, 3, -2, -3, -4, -4, -3, -5, -2, -3, -3, -4, -3, -3, -3, -4)
    )
  })
  
  # 1. Bing sentiment aggregation per review
  bing_review_scores <- tokens_df %>%
    inner_join(bing_lexicon, by = "word") %>%
    count(review_id, sentiment) %>%
    pivot_wider(names_from = sentiment, values_from = n, values_fill = 0) %>%
    mutate(
      positive_count = if ("positive" %in% names(.)) positive else 0,
      negative_count = if ("negative" %in% names(.)) negative else 0,
      bing_net = positive_count - negative_count
    ) %>%
    select(review_id, positive_count, negative_count, bing_net)
  
  # 2. AFINN sentiment score per review
  afinn_review_scores <- tokens_df %>%
    inner_join(afinn_lexicon, by = "word") %>%
    group_by(review_id) %>%
    summarise(
      afinn_score = sum(value, na.rm = TRUE),
      afinn_word_count = n(),
      .groups = "drop"
    )
  
  # 3. Combine with original reviews
  review_satisfaction <- reviews_df %>%
    left_join(bing_review_scores, by = "review_id") %>%
    left_join(afinn_review_scores, by = "review_id") %>%
    mutate(
      positive_count = replace_na(positive_count, 0),
      negative_count = replace_na(negative_count, 0),
      bing_net = replace_na(bing_net, 0),
      afinn_score = replace_na(afinn_score, 0),
      afinn_word_count = replace_na(afinn_word_count, 0),
      # Compound classification
      sentiment_class = case_when(
        rating >= 4 | bing_net >= 1 | afinn_score >= 2 ~ "Positive",
        rating <= 2 | bing_net <= -1 | afinn_score <= -2 ~ "Negative",
        TRUE ~ "Neutral"
      ),
      # Normalized satisfaction index (0 to 100 scale)
      satisfaction_index = round(pmax(0, pmin(100, (rating / 5 * 60) + (pmin(pmax(bing_net, -3), 3) + 3) / 6 * 40)), 1)
    )
  
  # 4. Department and Hospital Level Aggregations
  satisfaction_summary <- review_satisfaction %>%
    group_by(hospital, department) %>%
    summarise(
      total_reviews = n(),
      avg_rating = round(mean(rating), 2),
      avg_satisfaction_index = round(mean(satisfaction_index), 1),
      pct_positive = round(mean(sentiment_class == "Positive") * 100, 1),
      pct_neutral  = round(mean(sentiment_class == "Neutral") * 100, 1),
      pct_negative = round(mean(sentiment_class == "Negative") * 100, 1),
      net_promoter_proxy = round((pct_positive - pct_negative), 1),
      .groups = "drop"
    )
  
  # Save RDS outputs
  satisfaction_rds_path <- file.path(output_dir, "review_satisfaction.rds")
  summary_rds_path      <- file.path(output_dir, "satisfaction_summary.rds")
  
  saveRDS(review_satisfaction, satisfaction_rds_path)
  saveRDS(satisfaction_summary, summary_rds_path)
  
  message("Satisfaction analysis completed.")
  message("  -> ", satisfaction_rds_path, " (", nrow(review_satisfaction), " rows)")
  message("  -> ", summary_rds_path, " (", nrow(satisfaction_summary), " hospital-dept groups)")
  
  invisible(list(review_satisfaction = review_satisfaction, summary = satisfaction_summary))
}

if (sys.nframe() == 0) {
  run_satisfaction_analysis()
}
