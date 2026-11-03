# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Module 01: Data Ingestion, Synthetic Generation, and Preprocessing
# File: R/01_clean.R
# ==============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(janitor)
  library(stringr)
  library(tidytext)
  library(lubridate)
})

# Optional lemmatization helper (falls back gracefully if textstem is not present)
lemmatize_words <- function(words) {
  if (requireNamespace("textstem", quietly = TRUE)) {
    return(textstem::lemmatize_words(words))
  } else {
    # Lightweight rule-based suffix normalization fallback
    words <- stringr::str_replace(words, "ies$", "y")
    words <- stringr::str_replace(words, "ves$", "f")
    words <- stringr::str_replace(words, "(s|ed|ing)$", "")
    return(words)
  }
}

# ------------------------------------------------------------------------------
# 1. Dataset Generation or Loading
# ------------------------------------------------------------------------------
generate_mock_reviews <- function(n = 2000, seed = 42) {
  set.seed(seed)
  
  hospitals <- c(
    "St. Jude Memorial Hospital",
    "Metro General Medical Center",
    "Prestige University Hospital",
    "Oakwood Community Health",
    "Horizon Valley Clinic"
  )
  
  departments <- c(
    "Emergency",
    "Cardiology",
    "Oncology",
    "Pediatrics",
    "Orthopedics",
    "Maternity / OB-GYN"
  )
  
  # Templates for aspect-rich sentence fragments with varied valence and negations
  doctor_pos <- c(
    "The attending physician Dr. Vance explained the procedure clearly and put my anxiety at ease.",
    "The doctor was extremely attentive, listened to all my symptoms, and was not rushed at all.",
    "Outstanding bedside manner from the cardiologist who walked me through every detail.",
    "The surgical team showed immense expertise and compassionate care throughout my stay.",
    "The doctor was very knowledgeable and patient, answering all our family's questions."
  )
  doctor_neg <- c(
    "The doctor barely spent two minutes in the room and seemed completely dismissive of my pain.",
    "The physician was not helpful, ignored my medical history, and felt very arrogant.",
    "I felt rushed by the consulting doctor who didn't listen to my concerns.",
    "The doctor seemed disorganized and gave conflicting diagnoses between rounds.",
    "Dr. Harris lacked empathy and was not attentive to my post-operative symptoms."
  )
  
  nurse_pos <- c(
    "The nurses were absolute angels, checking on me regularly and keeping my pain well managed.",
    "Nursing staff responded promptly whenever I pressed the call button, day or night.",
    "Incredible compassion from nurse Sarah who made my recovery so much smoother.",
    "The night shift nurses were warm, professional, and took vitals with gentle precision.",
    "The triage nurses were supportive, empathetic, and exceptionally kind."
  )
  nurse_neg <- c(
    "The nursing staff was inattentive and took over forty-five minutes to answer the call light.",
    "Nurses seemed overwhelmed and careless, forgetting to administer pain medication on schedule.",
    "The nurse was rude and not gentle when changing my IV lines.",
    "Staff at the nursing station were loudly chatting while patients were ringing for help.",
    "The nursing care was not compassionate and felt cold and indifferent."
  )
  
  clean_pos <- c(
    "The patient room and bathroom were spotless, disinfected, and thoroughly sanitized.",
    "Impressed by the immaculate cleanliness of the surgical ward and fresh linens daily.",
    "Hospital facilities were spotless, smelled fresh, and felt very hygienic.",
    "Housekeeping kept our room completely tidy and sanitized touchpoints multiple times a day.",
    "Very clean environment, pristine waiting area, and sterile examination rooms."
  )
  clean_neg <- c(
    "The room was dirty, with sticky floors and an overflowing trash can from the previous patient.",
    "The bathroom smelled foul and was not sanitized during our entire 36-hour stay.",
    "Disappointed by dusty equipment and stained bed sheets in the emergency cubicle.",
    "The waiting room was untidy, with dirty tissue dispensers and uncleaned chairs.",
    "Cleanliness was definitely below standards; room hygiene felt neglected."
  )
  
  wait_pos <- c(
    "Check-in was seamless and we were called into triage within ten minutes of arriving.",
    "Minimal wait times; the appointment started exactly on schedule without any delay.",
    "Swift intake process in the ER despite a busy Friday evening.",
    "The registration desk was swift, efficient, and got us seen by a provider right away.",
    "Virtually zero waiting time; lab results and scans were completed in record time."
  )
  wait_neg <- c(
    "We endured an excruciating four-hour wait in the emergency lobby before seeing a triage nurse.",
    "The appointment was delayed by two hours with zero updates or explanations from staff.",
    "Waiting times were unbearable and the reception staff offered no transparency.",
    "Spent nearly five hours sitting in uncomfortable waiting chairs while in severe distress.",
    "Severe delays across radiology and pharmacy; we waited endless hours just for discharge papers."
  )
  
  bill_pos <- c(
    "Billing was completely transparent with zero unexpected surprise charges on our statement.",
    "The financial counselor clearly explained what insurance covered before any procedure.",
    "Itemized billing was accurate, reasonable, and processed quickly through our insurer.",
    "Prompt and helpful customer service from the billing department regarding our copay.",
    "No hidden fees or unexpected charges; billing was honest and straightforward."
  )
  bill_neg <- c(
    "Received an outrageous surprise bill with exorbitant charges not covered by insurance.",
    "Billing department was impossible to reach and sent aggressive collection notices in error.",
    "Charged twice for standard blood work with zero explanation or willingness to correct it.",
    "Financial counseling was misleading and left us with huge unexpected out-of-pocket costs.",
    "Disputed charges on the invoice were met with stubborn, unhelpful billing representatives."
  )
  
  start_date <- as.Date("2025-01-01")
  end_date   <- as.Date("2026-10-31")
  date_pool  <- seq.Date(start_date, end_date, by = "day")
  
  # Generate reviews
  reviews_list <- vector("list", n)
  
  for (i in seq_len(n)) {
    hosp <- sample(hospitals, 1, prob = c(0.24, 0.22, 0.20, 0.18, 0.16))
    dept <- sample(departments, 1, prob = c(0.30, 0.18, 0.14, 0.14, 0.12, 0.12))
    rev_date <- sample(date_pool, 1)
    
    # Base hospital & dept satisfaction skew
    base_prob_pos <- 0.65
    if (hosp == "Oakwood Community Health") base_prob_pos <- 0.52
    if (hosp == "Metro General Medical Center" && dept == "Emergency") base_prob_pos <- 0.40
    if (hosp == "Prestige University Hospital") base_prob_pos <- 0.78
    if (dept == "Billing" || dept == "Emergency") base_prob_pos <- base_prob_pos - 0.10
    base_prob_pos <- max(0.25, min(0.85, base_prob_pos))
    
    # Pick 2 to 4 aspects to talk about
    num_aspects <- sample(2:4, 1)
    aspects_chosen <- sample(c("doctor", "nurse", "clean", "wait", "bill"), num_aspects)
    
    sentence_vec <- character(num_aspects)
    aspect_sentiments <- numeric(num_aspects)
    
    for (k in seq_along(aspects_chosen)) {
      asp <- aspects_chosen[k]
      is_pos <- runif(1) < base_prob_pos
      
      # Specific aspect tilts
      if (asp == "wait" && dept == "Emergency") is_pos <- runif(1) < 0.35
      if (asp == "bill") is_pos <- runif(1) < 0.45
      if (asp == "doctor" && hosp == "Prestige University Hospital") is_pos <- runif(1) < 0.85
      
      if (asp == "doctor") {
        sentence_vec[k] <- if (is_pos) sample(doctor_pos, 1) else sample(doctor_neg, 1)
      } else if (asp == "nurse") {
        sentence_vec[k] <- if (is_pos) sample(nurse_pos, 1) else sample(nurse_neg, 1)
      } else if (asp == "clean") {
        sentence_vec[k] <- if (is_pos) sample(clean_pos, 1) else sample(clean_neg, 1)
      } else if (asp == "wait") {
        sentence_vec[k] <- if (is_pos) sample(wait_pos, 1) else sample(wait_neg, 1)
      } else if (asp == "bill") {
        sentence_vec[k] <- if (is_pos) sample(bill_pos, 1) else sample(bill_neg, 1)
      }
      aspect_sentiments[k] <- if (is_pos) 1 else -1
    }
    
    full_text <- paste(sentence_vec, collapse = " ")
    
    # Overall rating (1-5) strongly correlates with average aspect sentiment
    mean_sent <- mean(aspect_sentiments)
    if (mean_sent >= 0.75) {
      rating <- sample(c(4, 5), 1, prob = c(0.15, 0.85))
    } else if (mean_sent >= 0.2) {
      rating <- sample(c(3, 4, 5), 1, prob = c(0.2, 0.6, 0.2))
    } else if (mean_sent >= -0.2) {
      rating <- sample(c(2, 3, 4), 1, prob = c(0.3, 0.5, 0.2))
    } else if (mean_sent >= -0.7) {
      rating <- sample(c(1, 2, 3), 1, prob = c(0.5, 0.4, 0.1))
    } else {
      rating <- sample(c(1, 2), 1, prob = c(0.85, 0.15))
    }
    
    reviews_list[[i]] <- tibble(
      review_id = sprintf("REV-%05d", i),
      date = rev_date,
      hospital = hosp,
      department = dept,
      rating = as.integer(rating),
      text = full_text
    )
  }
  
  bind_rows(reviews_list)
}

# ------------------------------------------------------------------------------
# 2. Main Cleaning & Preprocessing Pipeline
# ------------------------------------------------------------------------------
clean_and_preprocess <- function(raw_csv_path = "data/raw/reviews.csv",
                                 output_dir = "data/processed") {
  dir.create(dirname(raw_csv_path), recursive = TRUE, showWarnings = FALSE)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  
  # Check if raw data exists, else generate synthetic mock reviews
  if (file.exists(raw_csv_path)) {
    message("Loading existing raw review dataset from: ", raw_csv_path)
    raw_df <- read_csv(raw_csv_path, show_col_types = FALSE)
  } else {
    message("Generating 2,000 realistic synthetic hospital reviews...")
    raw_df <- generate_mock_reviews(n = 2000, seed = 2026)
    write_csv(raw_df, raw_csv_path)
    message("Saved raw reviews to: ", raw_csv_path)
  }
  
  # Standardize and clean fields
  clean_reviews <- raw_df %>%
    clean_names() %>%
    filter(!is.na(text), str_trim(text) != "") %>%
    mutate(
      review_id = as.character(review_id),
      date = as.Date(date),
      hospital = as.character(hospital),
      department = as.character(department),
      rating = as.integer(rating),
      text_clean = text %>%
        str_to_lower() %>%
        str_replace_all("[^a-z0-9\\s\\.\\,\\!\\?\\-]", " ") %>%
        str_squish(),
      char_count = nchar(text),
      word_count = str_count(text, "\\w+")
    )
  
  # Tokenization and Stopword Filtering + Lemmatization
  data("stop_words", package = "tidytext")
  
  clean_tokens <- clean_reviews %>%
    select(review_id, hospital, department, date, rating, text_clean) %>%
    unnest_tokens(word, text_clean, token = "words") %>%
    anti_join(stop_words, by = "word") %>%
    filter(str_detect(word, "^[a-z]{2,}$")) %>%
    mutate(lemma = lemmatize_words(word))
  
  # Save RDS outputs
  clean_reviews_path <- file.path(output_dir, "clean_reviews.rds")
  clean_tokens_path  <- file.path(output_dir, "clean_tokens.rds")
  
  saveRDS(clean_reviews, clean_reviews_path)
  saveRDS(clean_tokens, clean_tokens_path)
  
  message("Preprocessing completed successfully.")
  message("  -> ", clean_reviews_path, " (", nrow(clean_reviews), " reviews)")
  message("  -> ", clean_tokens_path, " (", nrow(clean_tokens), " tokens)")
  
  invisible(list(reviews = clean_reviews, tokens = clean_tokens))
}

# Run module if executed directly as script
if (sys.nframe() == 0) {
  clean_and_preprocess()
}
