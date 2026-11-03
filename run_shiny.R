# ==============================================================================
# HEALYTICS: One-Click Shiny Localhost Server Launcher
# ==============================================================================

if (!requireNamespace("shiny", quietly = TRUE)) {
  stop("The 'shiny' package is required. Install it using: install.packages('shiny')")
}

cat("====================================================================\n")
cat(" Starting Healytics Shiny Dashboard on localhost:3838\n")
cat(" URL: http://localhost:3838\n")
cat("====================================================================\n")

shiny::runApp(
  appDir = "app",
  host = "127.0.0.1",
  port = 3838,
  launch.browser = TRUE
)
