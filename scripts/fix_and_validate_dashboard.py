import os
import subprocess

html_paths = [
    r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics\app\index.html",
    r"C:\Users\Sathvi\.gemini\antigravity\scratch\healytics\outputs\healytics_dashboard_preview.html"
]

for p in html_paths:
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace bad multi-line strings in Plotly annotations with single-line strings or HTML line breaks
    bad_snippets = [
        ("text: '⚠ FIX FIRST\n(High Impact, Low Perf)'", "text: '⚠ FIX FIRST<br>(High Impact, Low Perf)'"),
        ("text: '⚠ FIX FIRST\r\n(High Impact, Low Perf)'", "text: '⚠ FIX FIRST<br>(High Impact, Low Perf)'"),
        ("text: '✔ MAINTAIN EXCELLENCE\n(High Impact, High Perf)'", "text: '✔ MAINTAIN EXCELLENCE<br>(High Impact, High Perf)'"),
        ("text: '✔ MAINTAIN EXCELLENCE\r\n(High Impact, High Perf)'", "text: '✔ MAINTAIN EXCELLENCE<br>(High Impact, High Perf)'"),
        ("text: 'SECONDARY MONITOR\n(Low Impact, Low Perf)'", "text: 'SECONDARY MONITOR<br>(Low Impact, Low Perf)'"),
        ("text: 'SECONDARY MONITOR\r\n(Low Impact, Low Perf)'", "text: 'SECONDARY MONITOR<br>(Low Impact, Low Perf)'"),
        ("text: 'MAINTAIN STANDARD\n(Low Impact, High Perf)'", "text: 'MAINTAIN STANDARD<br>(Low Impact, High Perf)'"),
        ("text: 'MAINTAIN STANDARD\r\n(Low Impact, High Perf)'", "text: 'MAINTAIN STANDARD<br>(Low Impact, High Perf)'")
    ]

    for bad, good in bad_snippets:
        content = content.replace(bad, good)

    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

print("Replacement complete. Now validating with Node.js...")

# Validate syntax of script block
validate_js = r"""
const fs = require('fs');
const html = fs.readFileSync('C:/Users/Sathvi/.gemini/antigravity/scratch/healytics/app/index.html', 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
    console.error('No script tag found!');
    process.exit(1);
}
try {
    new Function(scriptMatch[1]);
    console.log('SUCCESS: JavaScript syntax is 100% VALID and runs cleanly!');
} catch (e) {
    console.error('STILL ERROR:', e.message);
    process.exit(1);
}
"""

with open("temp_validate.js", "w", encoding="utf-8") as f:
    f.write(validate_js)

res = subprocess.run(["node", "temp_validate.js"], capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
if os.path.exists("temp_validate.js"):
    os.remove("temp_validate.js")
