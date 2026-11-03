files = [
    r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics\app\index.html",
    r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics\outputs\healytics_dashboard_preview.html"
]

old_tag = '<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>'
new_tag = '<script src="www/plotly.min.js"></script>\n  <script>if(typeof Plotly==="undefined"){document.write(\'<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"><\\/script>\');}</script>'

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        text = fh.read()
    if old_tag in text:
        text = text.replace(old_tag, new_tag)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("Updated Plotly tag in:", f)
    else:
        print("Tag already updated in:", f)
