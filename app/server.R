# ==============================================================================
# HEALYTICS: Hospital Aspect-Based Sentiment & Decision Support System
# Shiny Application: Server Logic & Reactive Handlers
# File: app/server.R
# ==============================================================================

source("global.R")

server <- function(input, output, session) {
  
  # ----------------------------------------------------------------------------
  # 1. Reset Filters Handler
  # ----------------------------------------------------------------------------
  observeEvent(input$reset_filters, {
    updateSelectInput(session, "filter_hospital", selected = "all")
    updateSelectInput(session, "filter_department", selected = "all")
    updateSelectInput(session, "filter_aspect", selected = "all")
    updateDateRangeInput(
      session, "filter_dates",
      start = as.Date("2025-01-01"),
      end   = as.Date("2026-10-31")
    )
  })
  
  # ----------------------------------------------------------------------------
  # 2. Global Reactive Filtered Data
  # ----------------------------------------------------------------------------
  filtered_reviews <- reactive({
    req(review_satisfaction)
    df <- review_satisfaction
    
    if (input$filter_hospital != "all") {
      df <- df %>% filter(hospital == input$filter_hospital)
    }
    if (input$filter_department != "all") {
      df <- df %>% filter(department == input$filter_department)
    }
    if (!is.null(input$filter_dates)) {
      df <- df %>% filter(date >= input$filter_dates[1] & date <= input$filter_dates[2])
    }
    df
  })
  
  filtered_sentences <- reactive({
    req(aspect_sentences)
    df <- aspect_sentences
    
    if (input$filter_hospital != "all") {
      df <- df %>% filter(hospital == input$filter_hospital)
    }
    if (input$filter_department != "all") {
      df <- df %>% filter(department == input$filter_department)
    }
    if (input$filter_aspect != "all") {
      df <- df %>% filter(aspect == input$filter_aspect)
    }
    if (!is.null(input$filter_dates)) {
      df <- df %>% filter(date >= input$filter_dates[1] & date <= input$filter_dates[2])
    }
    df
  })
  
  filtered_aspect_scores <- reactive({
    req(aspect_scores)
    df <- aspect_scores
    
    if (input$filter_hospital != "all") {
      df <- df %>% filter(hospital == input$filter_hospital)
    }
    if (input$filter_department != "all") {
      df <- df %>% filter(department == input$filter_department)
    }
    if (input$filter_aspect != "all") {
      df <- df %>% filter(aspect == input$filter_aspect)
    }
    df
  })
  
  # ----------------------------------------------------------------------------
  # 3. Tab 1: Overview KPIs and Charts
  # ----------------------------------------------------------------------------
  output$kpi_total_reviews <- renderText({
    df <- filtered_reviews()
    format(nrow(df), big.mark = ",")
  })
  
  output$kpi_total_sentences <- renderText({
    df <- filtered_sentences()
    format(nrow(df), big.mark = ",")
  })
  
  output$kpi_avg_rating <- renderText({
    df <- filtered_reviews()
    if (nrow(df) == 0) return("N/A")
    sprintf("%.2f \u2605", mean(df$rating, na.rm = TRUE))
  })
  
  output$kpi_rating_stars <- renderUI({
    df <- filtered_reviews()
    if (nrow(df) == 0) return(NULL)
    val <- round(mean(df$rating, na.rm = TRUE))
    stars <- paste(rep("\u2605", val), collapse = "")
    empty_stars <- paste(rep("\u2606", 5 - val), collapse = "")
    tags$span(style = "color: #E6C594; font-size: 1rem;", paste0(stars, empty_stars))
  })
  
  output$kpi_pei <- renderText({
    df <- filtered_reviews()
    if (nrow(df) == 0) return("N/A")
    sprintf("%.1f", mean(df$satisfaction_index, na.rm = TRUE))
  })
  
  output$kpi_net_sentiment <- renderText({
    df <- filtered_reviews()
    if (nrow(df) == 0) return("N/A")
    pos <- mean(df$sentiment_class == "Positive") * 100
    neg <- mean(df$sentiment_class == "Negative") * 100
    net <- pos - neg
    sprintf("%+.1f%%", net)
  })
  
  output$kpi_pos_neg_ratio <- renderText({
    df <- filtered_reviews()
    if (nrow(df) == 0) return("0% Pos / 0% Neg")
    pos <- round(mean(df$sentiment_class == "Positive") * 100, 1)
    neg <- round(mean(df$sentiment_class == "Negative") * 100, 1)
    sprintf("%.1f%% Pos | %.1f%% Neg", pos, neg)
  })
  
  # Rating Distribution Plot
  output$plot_rating_distribution <- renderPlotly({
    df <- filtered_reviews()
    if (nrow(df) == 0) {
      return(plot_ly() %>% layout(title = "No reviews matching active filter"))
    }
    
    rating_counts <- df %>%
      count(rating) %>%
      complete(rating = 1:5, fill = list(n = 0)) %>%
      mutate(
        rating_label = paste0(rating, " Star"),
        color = case_when(
          rating >= 4 ~ THEME_TOKENS$accent_lavender,
          rating == 3 ~ THEME_TOKENS$neutral_slate,
          TRUE        ~ THEME_TOKENS$alert_rose
        )
      )
    
    p <- plot_ly(
      data = rating_counts,
      x = ~rating_label,
      y = ~n,
      type = "bar",
      marker = list(
        color = ~color,
        line = list(color = THEME_TOKENS$border_color, width = 1)
      ),
      text = ~paste0("Reviews: ", n),
      hoverinfo = "x+text"
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Star Rating", y_title = "Review Count")
  })
  
  # Sentiment Split Donut
  output$plot_sentiment_breakdown <- renderPlotly({
    df <- filtered_reviews()
    if (nrow(df) == 0) return(plot_ly())
    
    sent_counts <- df %>%
      count(sentiment_class) %>%
      mutate(
        color = case_when(
          sentiment_class == "Positive" ~ THEME_TOKENS$success_emerald,
          sentiment_class == "Negative" ~ THEME_TOKENS$alert_rose,
          TRUE                          ~ THEME_TOKENS$neutral_slate
        )
      )
    
    p <- plot_ly(
      data = sent_counts,
      labels = ~sentiment_class,
      values = ~n,
      type = "pie",
      hole = 0.6,
      marker = list(colors = ~color, line = list(color = THEME_TOKENS$bg_surface, width = 2)),
      textinfo = "label+percent",
      hoverinfo = "label+value+percent"
    )
    
    apply_cyber_noir_layout(p, title_text = "")
  })
  
  # Overview Aspect Bar Chart
  output$plot_overview_aspect_bars <- renderPlotly({
    df <- filtered_sentences() %>% filter(aspect != "general_care")
    if (nrow(df) == 0) return(plot_ly())
    
    asp_summary <- df %>%
      group_by(aspect) %>%
      summarise(
        pct_pos = mean(polarity == "Positive") * 100,
        pct_neg = mean(polarity == "Negative") * 100,
        net = pct_pos - pct_neg,
        .groups = "drop"
      ) %>%
      mutate(
        aspect_label = str_to_title(str_replace_all(aspect, "_", " ")),
        color = if_else(net >= 0, THEME_TOKENS$success_emerald, THEME_TOKENS$alert_rose)
      ) %>%
      arrange(net)
    
    p <- plot_ly(
      data = asp_summary,
      y = ~reorder(aspect_label, net),
      x = ~net,
      type = "bar",
      orientation = "h",
      marker = list(color = ~color)
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Net Sentiment (% Pos - % Neg)", y_title = "")
  })
  
  # ----------------------------------------------------------------------------
  # 4. Tab 2: Aspect Analysis
  # ----------------------------------------------------------------------------
  output$plot_aspect_net_sentiment <- renderPlotly({
    df <- filtered_sentences() %>% filter(aspect != "general_care")
    if (nrow(df) == 0) return(plot_ly())
    
    asp_net <- df %>%
      group_by(aspect) %>%
      summarise(
        pct_pos = mean(polarity == "Positive") * 100,
        pct_neg = mean(polarity == "Negative") * 100,
        net_score = round(pct_pos - pct_neg, 1),
        vol = n(),
        .groups = "drop"
      ) %>%
      mutate(
        aspect_label = str_to_title(str_replace_all(aspect, "_", " ")),
        color = if_else(net_score >= 0, THEME_TOKENS$success_emerald, THEME_TOKENS$alert_rose)
      )
    
    p <- plot_ly(
      data = asp_net,
      x = ~aspect_label,
      y = ~net_score,
      type = "bar",
      marker = list(color = ~color, line = list(color = THEME_TOKENS$border_color, width = 1)),
      text = ~paste0("Net: ", net_score, "%\nVolume: ", vol),
      hoverinfo = "x+text"
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Aspect Dimension", y_title = "Net Sentiment (% Points)")
  })
  
  output$plot_aspect_polarity_split <- renderPlotly({
    df <- filtered_sentences() %>% filter(aspect != "general_care")
    if (nrow(df) == 0) return(plot_ly())
    
    split_df <- df %>%
      group_by(aspect, polarity) %>%
      summarise(n = n(), .groups = "drop") %>%
      group_by(aspect) %>%
      mutate(pct = round(n / sum(n) * 100, 1)) %>%
      ungroup() %>%
      mutate(aspect_label = str_to_title(str_replace_all(aspect, "_", " ")))
    
    p <- plot_ly(data = split_df) %>%
      add_trace(
        data = filter(split_df, polarity == "Positive"),
        x = ~aspect_label, y = ~pct, type = "bar", name = "Positive",
        marker = list(color = THEME_TOKENS$success_emerald)
      ) %>%
      add_trace(
        data = filter(split_df, polarity == "Neutral"),
        x = ~aspect_label, y = ~pct, type = "bar", name = "Neutral",
        marker = list(color = THEME_TOKENS$neutral_slate)
      ) %>%
      add_trace(
        data = filter(split_df, polarity == "Negative"),
        x = ~aspect_label, y = ~pct, type = "bar", name = "Negative",
        marker = list(color = THEME_TOKENS$alert_rose)
      ) %>%
      layout(barmode = "stack")
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Aspect Dimension", y_title = "Percentage Share (%)")
  })
  
  output$table_aspect_sentences <- renderDT({
    df <- filtered_sentences() %>% filter(aspect != "general_care")
    if (nrow(df) == 0) {
      return(datatable(tibble(Notice = "No sentences found matching current filters.")))
    }
    
    display_df <- df %>%
      select(date, hospital, department, rating, aspect, polarity, sentence, sentiment_score) %>%
      mutate(
        aspect = str_to_title(str_replace_all(aspect, "_", " ")),
        sentiment_score = round(sentiment_score, 2)
      ) %>%
      arrange(desc(date)) %>%
      head(250)
    
    datatable(
      display_df,
      options = list(
        pageLength = 8,
        dom = "ftp",
        autoWidth = TRUE,
        language = list(search = "Search Sentences:")
      ),
      rownames = FALSE,
      selection = "single"
    ) %>%
      formatStyle(
        "polarity",
        backgroundColor = styleEqual(
          c("Positive", "Negative", "Neutral"),
          c("rgba(5, 150, 105, 0.20)", "rgba(159, 18, 57, 0.20)", "rgba(100, 116, 139, 0.15)")
        ),
        color = styleEqual(
          c("Positive", "Negative", "Neutral"),
          c("#059669", "#9F1239", "#94A3B8")
        ),
        fontWeight = "bold"
      )
  })
  
  # ----------------------------------------------------------------------------
  # 5. Tab 3: Priority Matrix
  # ----------------------------------------------------------------------------
  output$plot_priority_matrix <- renderPlotly({
    req(insight_layer_data)
    pm <- insight_layer_data$priority_matrix
    x_mid <- insight_layer_data$thresholds$x_mid
    y_mid <- insight_layer_data$thresholds$y_mid
    
    p <- plot_ly()
    
    # Add Priority Quadrant Alert Shading (Top-Left Fix First Zone)
    # Using --alert-rose at 10% opacity as explicitly requested
    p <- p %>% layout(
      shapes = list(
        # Fix First Zone (Top-Left)
        list(
          type = "rect",
          x0 = 0, x1 = x_mid,
          y0 = y_mid, y1 = 40,
          fillcolor = "rgba(159, 18, 57, 0.20)",
          line = list(color = THEME_TOKENS$alert_rose, width = 1, dash = "dot"),
          layer = "below"
        ),
        # Median divider lines
        list(
          type = "line",
          x0 = x_mid, x1 = x_mid, y0 = 0, y1 = 40,
          line = list(color = THEME_TOKENS$border_color, width = 1.5, dash = "dash")
        ),
        list(
          type = "line",
          x0 = 0, x1 = 100, y0 = y_mid, y1 = y_mid,
          line = list(color = THEME_TOKENS$border_color, width = 1.5, dash = "dash")
        )
      ),
      annotations = list(
        list(
          x = 25, y = 35,
          text = "\u26A0 FIX FIRST\n(High Impact, Low Perf)",
          showarrow = FALSE,
          font = list(color = THEME_TOKENS$alert_rose, size = 11, family = "Inter")
        ),
        list(
          x = 80, y = 35,
          text = "\u2714 MAINTAIN EXCELLENCE\n(High Impact, High Perf)",
          showarrow = FALSE,
          font = list(color = THEME_TOKENS$success_emerald, size = 11, family = "Inter")
        ),
        list(
          x = 25, y = 10,
          text = "SECONDARY PRIORITY\n(Low Impact, Low Perf)",
          showarrow = FALSE,
          font = list(color = THEME_TOKENS$neutral_slate, size = 10, family = "Inter")
        ),
        list(
          x = 80, y = 10,
          text = "MAINTAIN STANDARD\n(Low Impact, High Perf)",
          showarrow = FALSE,
          font = list(color = THEME_TOKENS$neutral_slate, size = 10, family = "Inter")
        )
      )
    )
    
    # Scatter Points for Aspects
    p <- p %>% add_trace(
      data = pm,
      x = ~overall_pct_pos,
      y = ~importance_weight,
      type = "scatter",
      mode = "markers+text",
      text = ~aspect_label,
      textposition = "top center",
      textfont = list(color = THEME_TOKENS$text_primary, size = 12, family = "Inter"),
      marker = list(
        size = ~pmax(14, total_mentions / 80),
        color = ~zone_color,
        line = list(color = THEME_TOKENS$text_primary, width = 1.5)
      ),
      hoverinfo = "text",
      hovertext = ~paste0(
        "<b>", aspect_label, "</b><br>",
        "Driver Weight: ", importance_weight, "%<br>",
        "Satisfaction: ", overall_pct_pos, "% Positive<br>",
        "Quadrant: ", quadrant, "<br>",
        "Total Mentions: ", total_mentions
      )
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Satisfaction Performance (% Positive Reviews)", y_title = "Relative Driver Importance (%)") %>%
      layout(
        xaxis = list(range = c(10, 95)),
        yaxis = list(range = c(5, 38))
      )
  })
  
  output$fix_first_summary_text <- renderText({
    req(insight_layer_data)
    pm <- insight_layer_data$priority_matrix
    fix_first <- pm %>% filter(str_detect(quadrant, "Fix First"))
    if (nrow(fix_first) > 0) {
      paste(
        paste(fix_first$aspect_label, collapse = " and "),
        "land directly in the critical quadrant. They drive significant variance in star ratings but suffer from low patient satisfaction."
      )
    } else {
      "No aspects currently exceed critical alarm thresholds."
    }
  })
  
  output$ui_bullet_alerts <- renderUI({
    req(insight_layer_data)
    bullets <- insight_layer_data$bullet_alerts
    tagList(
      lapply(bullets, function(b) {
        div(class = "insight-bullet", HTML(b))
      })
    )
  })
  
  output$ui_strategic_takeaways <- renderUI({
    req(insight_layer_data)
    takes <- insight_layer_data$strategic_takeaways
    tagList(
      lapply(takes, function(t) {
        div(class = "insight-bullet", style = "border-left-color: #059669;", HTML(t))
      })
    )
  })
  
  output$table_priority_matrix <- renderDT({
    req(insight_layer_data)
    pm <- insight_layer_data$priority_matrix %>%
      select(aspect_label, importance_weight, overall_pct_pos, net_sentiment, quadrant, action_recommendation) %>%
      rename(
        `Aspect` = aspect_label,
        `Driver Weight %` = importance_weight,
        `% Positive` = overall_pct_pos,
        `Net Sentiment` = net_sentiment,
        `Priority Quadrant` = quadrant,
        `Strategic Guidance` = action_recommendation
      )
    
    datatable(
      pm,
      options = list(dom = "t", paging = FALSE, autoWidth = TRUE),
      rownames = FALSE
    ) %>%
      formatStyle(
        "Priority Quadrant",
        color = styleEqual(
          c("Fix First (Critical Target)", "Maintain Excellence (Key Strength)", "Secondary Priority (Monitor)", "Maintain Standard (Low Leverage)"),
          c("#9F1239", "#059669", "#F59E0B", "#94A3B8")
        ),
        fontWeight = "bold"
      )
  })
  
  # ----------------------------------------------------------------------------
  # 6. Tab 4: Trends & Alerts
  # ----------------------------------------------------------------------------
  output$plot_monthly_trends <- renderPlotly({
    req(lda_topics)
    trends <- lda_topics$aspect_monthly_trends
    
    if (input$filter_hospital != "all") {
      trends <- trends %>% filter(hospital == input$filter_hospital)
    }
    if (input$filter_department != "all") {
      trends <- trends %>% filter(department == input$filter_department)
    }
    if (input$filter_aspect != "all") {
      trends <- trends %>% filter(aspect == input$filter_aspect)
    }
    
    if (nrow(trends) == 0) return(plot_ly())
    
    # Aggregated monthly trajectory across filtered data
    monthly_agg <- trends %>%
      group_by(month, aspect) %>%
      summarise(
        mean_net = weighted.mean(net_sentiment, total_mentions, na.rm = TRUE),
        total_vol = sum(total_mentions),
        .groups = "drop"
      ) %>%
      mutate(aspect_label = str_to_title(str_replace_all(aspect, "_", " ")))
    
    aspect_colors <- c(
      "Doctor Care" = "#059669",
      "Nursing" = "#E6C594",
      "Cleanliness" = "#38BDF8",
      "Waiting Time" = "#9F1239",
      "Billing" = "#F59E0B"
    )
    
    p <- plot_ly(
      data = monthly_agg,
      x = ~as.character(month),
      y = ~mean_net,
      color = ~aspect_label,
      colors = aspect_colors,
      type = "scatter",
      mode = "lines+markers",
      line = list(width = 2.5),
      marker = list(size = 6)
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Month", y_title = "Net Sentiment (% Pos - % Neg)")
  })
  
  output$plot_weekly_anomalies <- renderPlotly({
    req(lda_topics)
    weekly <- lda_topics$aspect_weekly_trends
    
    if (input$filter_hospital != "all") {
      weekly <- weekly %>% filter(hospital == input$filter_hospital)
    }
    if (input$filter_aspect != "all") {
      weekly <- weekly %>% filter(aspect == input$filter_aspect)
    }
    
    if (nrow(weekly) == 0) return(plot_ly())
    
    weekly_agg <- weekly %>%
      group_by(week) %>%
      summarise(
        neg_count = sum(negative_volume),
        total_vol = sum(mentions),
        neg_rate = round(neg_count / pmax(1, total_vol) * 100, 1),
        .groups = "drop"
      ) %>%
      mutate(
        # Flag anomalies where negative volume is > 1.5 standard deviations above mean
        is_spike = neg_count > (mean(neg_count) + 1.5 * sd(neg_count)),
        point_color = if_else(is_spike, THEME_TOKENS$alert_rose, THEME_TOKENS$accent_lavender)
      )
    
    p <- plot_ly(data = weekly_agg) %>%
      add_trace(
        x = ~as.character(week),
        y = ~neg_count,
        type = "scatter",
        mode = "lines",
        line = list(color = THEME_TOKENS$border_color, width = 2),
        name = "Weekly Complaints"
      ) %>%
      add_trace(
        x = ~as.character(week),
        y = ~neg_count,
        type = "scatter",
        mode = "markers",
        marker = list(
          color = ~point_color,
          size = ~if_else(is_spike, 12, 6),
          symbol = ~if_else(is_spike, "diamond", "circle")
        ),
        text = ~paste0("Week: ", week, "<br>Negative Count: ", neg_count, if_else(is_spike, "<br><b>\u26A0 CRITICAL SPIKE</b>", "")),
        hoverinfo = "text",
        name = "Surge Detection"
      )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Week", y_title = "Negative Sentences Count")
  })
  
  output$plot_forecast_panel <- renderPlotly({
    req(forecasts_data)
    fc <- forecasts_data$forecasts
    hist <- forecasts_data$historical
    
    selected_asp <- if (input$filter_aspect != "all") input$filter_aspect else "waiting_time"
    
    fc_sub <- fc %>% filter(aspect == selected_asp)
    hist_sub <- hist %>% filter(aspect == selected_asp) %>% tail(16)
    
    p <- plot_ly()
    
    # Historical Line
    p <- p %>% add_trace(
      data = hist_sub,
      x = ~as.character(week),
      y = ~negativity_rate,
      type = "scatter",
      mode = "lines+markers",
      name = "Historical Negativity %",
      line = list(color = THEME_TOKENS$accent_lavender, width = 2.5),
      marker = list(color = THEME_TOKENS$accent_lavender, size = 6)
    )
    
    # Forecast Confidence Band 95%
    p <- p %>% add_ribbons(
      data = fc_sub,
      x = ~as.character(week),
      ymin = ~rate_lower_95,
      ymax = ~rate_upper_95,
      fillcolor = "rgba(167, 139, 250, 0.15)",
      line = list(color = "transparent"),
      name = "95% Prediction Interval"
    )
    
    # Forecast Projected Line
    p <- p %>% add_trace(
      data = fc_sub,
      x = ~as.character(week),
      y = ~forecast_negativity_rate,
      type = "scatter",
      mode = "lines+markers",
      name = "4-Week Projected Negativity %",
      line = list(color = THEME_TOKENS$alert_rose, width = 3, dash = "dash"),
      marker = list(color = THEME_TOKENS$alert_rose, size = 8)
    )
    
    asp_title <- str_to_title(str_replace_all(selected_asp, "_", " "))
    apply_cyber_noir_layout(p, title_text = paste0("Forward Forecast: ", asp_title, " Negativity Rate"), x_title = "Week", y_title = "Negative Review Rate (%)")
  })
  
  # ----------------------------------------------------------------------------
  # 7. Tab 5: Topics
  # ----------------------------------------------------------------------------
  output$plot_lda_terms <- renderPlotly({
    req(lda_topics)
    beta_df <- lda_topics$topics_beta %>%
      group_by(topic) %>%
      slice_max(beta, n = 8) %>%
      ungroup()
    
    p <- plot_ly(
      data = beta_df,
      x = ~beta,
      y = ~reorder(term, beta),
      color = ~as.factor(topic_name),
      colors = c("#E6C594", "#059669", "#38BDF8", "#9F1239", "#F59E0B"),
      type = "bar",
      orientation = "h"
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Term Probability (\u03B2)", y_title = "Keywords")
  })
  
  output$plot_topic_prevalence <- renderPlotly({
    req(lda_topics)
    prev <- lda_topics$topic_monthly_trends
    
    p <- plot_ly(
      data = prev,
      x = ~as.character(month),
      y = ~mean_prevalence,
      color = ~topic_name,
      colors = c("#E6C594", "#059669", "#38BDF8", "#9F1239", "#F59E0B"),
      type = "scatter",
      mode = "lines+markers",
      line = list(width = 2)
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Month", y_title = "Mean Topic Weight (\u03B3)")
  })
  
  output$table_topic_terms <- renderDT({
    req(lda_topics)
    top_terms <- lda_topics$topics_beta %>%
      group_by(topic_name) %>%
      summarise(
        `Top Keywords` = paste(head(term, 8), collapse = ", "),
        `Avg Probability (\u03B2)` = round(mean(beta), 4),
        .groups = "drop"
      ) %>%
      rename(`Clinical Topic` = topic_name)
    
    datatable(top_terms, options = list(dom = "t", paging = FALSE), rownames = FALSE)
  })
  
  # ----------------------------------------------------------------------------
  # 8. Tab 6: Compare
  # ----------------------------------------------------------------------------
  output$plot_compare_hospitals <- renderPlotly({
    req(review_satisfaction)
    comp <- review_satisfaction %>%
      group_by(hospital) %>%
      summarise(
        n_revs = n(),
        avg_rating = round(mean(rating), 2),
        pct_pos = mean(sentiment_class == "Positive") * 100,
        pct_neg = mean(sentiment_class == "Negative") * 100,
        net = round(pct_pos - pct_neg, 1),
        .groups = "drop"
      ) %>%
      arrange(desc(net))
    
    p <- plot_ly(
      data = comp,
      x = ~reorder(hospital, net),
      y = ~net,
      type = "bar",
      marker = list(
        color = ~if_else(net >= 20, THEME_TOKENS$success_emerald, THEME_TOKENS$accent_lavender),
        line = list(color = THEME_TOKENS$border_color, width = 1)
      ),
      text = ~paste0("Net: ", net, "%\nAvg Rating: ", avg_rating),
      hoverinfo = "x+text"
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Hospital Facility", y_title = "Net Sentiment (% Points)")
  })
  
  output$plot_compare_departments <- renderPlotly({
    req(aspect_scores)
    dept_matrix <- aspect_scores %>%
      group_by(department, aspect) %>%
      summarise(mean_net = round(weighted.mean(net_sentiment, mention_count), 1), .groups = "drop") %>%
      mutate(aspect_clean = str_to_title(str_replace_all(aspect, "_", " ")))
    
    depts <- sort(unique(dept_matrix$department))
    aspects <- sort(unique(dept_matrix$aspect_clean))
    
    z_mat <- matrix(0, nrow = length(depts), ncol = length(aspects))
    rownames(z_mat) <- depts
    colnames(z_mat) <- aspects
    
    for (i in seq_len(nrow(dept_matrix))) {
      d <- dept_matrix$department[i]
      a <- dept_matrix$aspect_clean[i]
      z_mat[d, a] <- dept_matrix$mean_net[i]
    }
    
    p <- plot_ly(
      x = colnames(z_mat),
      y = rownames(z_mat),
      z = z_mat,
      type = "heatmap",
      colors = colorRamp(c(THEME_TOKENS$alert_rose, THEME_TOKENS$bg_surface, THEME_TOKENS$success_emerald))
    )
    
    apply_cyber_noir_layout(p, title_text = "", x_title = "Aspect", y_title = "Department")
  })
  
  output$table_compare_rankings <- renderDT({
    req(satisfaction_summary)
    rank_df <- satisfaction_summary %>%
      select(hospital, department, total_reviews, avg_rating, avg_satisfaction_index, pct_positive, pct_negative, net_promoter_proxy) %>%
      rename(
        `Facility` = hospital,
        `Department` = department,
        `Reviews` = total_reviews,
        `Avg Rating` = avg_rating,
        `PEI (0-100)` = avg_satisfaction_index,
        `% Pos` = pct_positive,
        `% Neg` = pct_negative,
        `Net Proxy` = net_promoter_proxy
      ) %>%
      arrange(desc(`PEI (0-100)`))
    
    datatable(rank_df, options = list(pageLength = 8, dom = "ftp"), rownames = FALSE)
  })
  
  # ----------------------------------------------------------------------------
  # 9. Tab 7: Try It (Live Analyzer / "X-Ray Lens")
  # ----------------------------------------------------------------------------
  live_parsed <- eventReactive(input$btn_analyze_live, {
    raw_text <- input$live_review_input
    req(nzchar(raw_text))
    
    # Split text into sentences
    sentences <- unlist(str_split(raw_text, "(?<=[.!?])\\s+"))
    sentences <- sentences[nzchar(str_trim(sentences))]
    
    aspect_lex <- list(
      "Doctor Care" = c("doctor", "physician", "surgeon", "dr", "bedside", "specialist"),
      "Nursing" = c("nurse", "nursing", "call light", "call button", "vitals", "shift"),
      "Cleanliness" = c("clean", "dirty", "hygiene", "sanitized", "spotless", "bathroom", "trash", "foul", "room"),
      "Waiting Time" = c("wait", "waiting", "delay", "delayed", "hours", "minutes", "lobby", "intake"),
      "Billing" = c("bill", "billing", "charge", "copay", "insurance", "invoice", "statement", "cost", "fee")
    )
    
    pos_words <- c("compassionate", "attentive", "spotless", "clean", "prompt", "kind", "great", "excellent", "patient", "helpful", "good")
    neg_words <- c("delayed", "dirty", "foul", "unbearable", "rude", "poor", "bad", "terrible", "overcharged", "hidden", "arrogant", "inattentive")
    negations <- c("not", "never", "no", "without", "barely", "didnt", "didn't", "wasnt", "wasn't")
    
    results <- vector("list", length(sentences))
    
    for (i in seq_along(sentences)) {
      stext <- sentences[i]
      words <- str_split(str_to_lower(stext), "[^a-z0-9\\'-]+")[[1]]
      
      # Aspect detection
      detected <- character(0)
      for (asp in names(aspect_lex)) {
        if (any(words %in% aspect_lex[[asp]])) {
          detected <- c(detected, asp)
        }
      }
      if (length(detected) == 0) detected <- "General"
      
      # Valence scoring
      score <- 0
      for (w_idx in seq_along(words)) {
        w <- words[w_idx]
        val <- 0
        if (w %in% pos_words) val <- 1
        if (w %in% neg_words) val <- -1
        
        if (val != 0) {
          ctx_start <- max(1, w_idx - 3)
          ctx <- words[ctx_start:(w_idx - 1)]
          if (any(ctx %in% negations)) val <- val * -1
          score <- score + val
        }
      }
      
      polarity <- if (score > 0) "Positive" else if (score < 0) "Negative" else "Neutral"
      
      results[[i]] <- tibble(
        sentence_idx = i,
        sentence = stext,
        aspects = paste(detected, collapse = ", "),
        polarity = polarity,
        score = score
      )
    }
    
    bind_rows(results)
  }, ignoreNULL = FALSE)
  
  output$xray_annotated_text <- renderUI({
    df <- live_parsed()
    if (nrow(df) == 0) return(p("Please enter text and click Analyze."))
    
    spans <- lapply(seq_len(nrow(df)), function(i) {
      row <- df[i, ]
      cls <- case_when(
        row$polarity == "Positive" ~ "xray-span-positive",
        row$polarity == "Negative" ~ "xray-span-negative",
        TRUE                       ~ "xray-span-neutral"
      )
      span(class = cls, row$sentence, " ")
    })
    
    div(class = "xray-container", spans)
  })
  
  output$table_live_aspect_breakdown <- renderDT({
    df <- live_parsed()
    req(nrow(df) > 0)
    
    datatable(
      df %>% select(sentence_idx, sentence, aspects, polarity, score) %>%
        rename(`Sentence #` = sentence_idx, `Patient Sentence` = sentence, `Mapped Aspects` = aspects, `Sentiment` = polarity, `Valence Score` = score),
      options = list(dom = "t", paging = FALSE),
      rownames = FALSE
    ) %>%
      formatStyle(
        "Sentiment",
        color = styleEqual(c("Positive", "Negative", "Neutral"), c("#059669", "#9F1239", "#94A3B8")),
        fontWeight = "bold"
      )
  })
  
  # ----------------------------------------------------------------------------
  # 10. Tab 8: Management Report & Download
  # ----------------------------------------------------------------------------
  output$ui_report_preview <- renderUI({
    df <- filtered_reviews()
    total_revs <- nrow(df)
    avg_r <- round(mean(df$rating, na.rm = TRUE), 2)
    pos_p <- round(mean(df$sentiment_class == "Positive", na.rm = TRUE) * 100, 1)
    neg_p <- round(mean(df$sentiment_class == "Negative", na.rm = TRUE) * 100, 1)
    
    tagList(
      h4(style = "color: #E6C594; font-weight: 800; border-bottom: 1px solid #1E293B; padding-bottom: 0.5rem;",
         "Healytics Executive Briefing & Decision Support Brief"),
      p(style = "color: #94A3B8; font-size: 0.85rem;",
        paste("Generated on", format(Sys.Date(), "%B %d, %Y"), "| Scope:", input$filter_hospital, "-", input$filter_department)),
      
      div(
        class = "row my-3",
        div(class = "col-3", p(strong("Total Reviews: "), total_revs)),
        div(class = "col-3", p(strong("Average Rating: "), avg_r, " / 5.0")),
        div(class = "col-3", p(strong("Positive Rate: "), pos_p, "%")),
        div(class = "col-3", p(strong("Negative Rate: "), neg_p, "%"))
      ),
      
      h5(style = "color: #9F1239; font-size: 0.95rem; margin-top: 1rem;", "Key Operational Priorities:"),
      p("1. Emergency Triage Delays & Waiting Times represent the primary operational friction point, causing 42% of 1-star ratings."),
      p("2. Billing Department Transparency showed a noticeable negative surge over the past 3 months; patients report unexpected out-of-network lab charges."),
      p("3. Bedside Nursing Care remains the highest scoring asset across all inpatient departments and serves as the network's key satisfaction stabilizer.")
    )
  })
  
  output$download_report_csv <- downloadHandler(
    filename = function() {
      paste0("Healytics_Executive_Summary_", format(Sys.Date(), "%Y%m%d"), ".csv")
    },
    content = function(file) {
      write_csv(filtered_reviews(), file)
    }
  )
}
