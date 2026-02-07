#!/usr/bin/env python3
"""
Move the sticky CTA div from inside custom-code-FfSGpAGpKG to be the first child
of col-8A1V8YCH9N > .inner, so position:sticky works (parent is tall enough).
"""
import re

INPUT = "index.html"
OUTPUT = "index.html"

with open(INPUT, "r", encoding="utf-8") as f:
    html = f.read()

# --- Step 1: Find and extract the sticky CTA div ---
# The sticky CTA starts with: <div style="  position: sticky; top: 0px; z-index: 9999;...">
# and ends right before <div id="stickyLength"
# It's inside: <div class="custom-code-container ccustom-code-FfSGpAGpKG sticky_buy_element">

# Find the sticky CTA div (from position:sticky to closing </div> before stickyLength)
sticky_start_marker = '<div style="  position: sticky; top: 0px; z-index: 9999;padding-top:15px;max-height:100vh;overflow-y:auto;">'
sticky_end_marker = '\n\n<div id="stickyLength"'

start_idx = html.find(sticky_start_marker)
if start_idx == -1:
    print("ERROR: Could not find sticky CTA start marker")
    exit(1)

# Find the end - look for stickyLength div after the start
end_search_start = start_idx
stickylen_idx = html.find('<div id="stickyLength"', end_search_start)
if stickylen_idx == -1:
    print("ERROR: Could not find stickyLength marker")
    exit(1)

# The sticky CTA div content is from start_idx to stickylen_idx
# But we need to find where the sticky div actually closes.
# Looking at the structure:
# <div style="position:sticky...">   <- line 2106
#   <div class="top_right_sec big_cta"> <- line 2107
#     ...content...
#   </div>                             <- line 2151
# </div>                               <- line 2152
#
# Then newlines, then <div id="stickyLength"...>

# Extract the sticky CTA div (everything from the sticky div through its closing </div>)
sticky_cta = html[start_idx:stickylen_idx].rstrip()

print(f"Found sticky CTA at position {start_idx}, length {len(sticky_cta)} chars")
print(f"First 100 chars: {sticky_cta[:100]}")
print(f"Last 100 chars: {sticky_cta[-100:]}")

# --- Step 2: Remove the sticky CTA from its current location ---
# Replace the sticky CTA with empty string (keep the stickyLength div and its container)
html_modified = html[:start_idx] + "\n" + html[stickylen_idx:]

# --- Step 3: Insert the sticky CTA as first child of col-8A1V8YCH9N > .inner ---
# The column opening looks like:
# <div class="c-column c-wrapper col-8A1V8YCH9N desktop-only" id="col-8A1V8YCH9N">
#   <div class="radius10 noBorder bg bgCover vertical inner">
# We need to insert right after that inner div opening

inner_marker = 'id="col-8A1V8YCH9N"><div class="radius10 noBorder bg bgCover vertical inner">'
insert_pos = html_modified.find(inner_marker)
if insert_pos == -1:
    print("ERROR: Could not find col-8A1V8YCH9N inner div")
    exit(1)

insert_pos += len(inner_marker)
print(f"\nInserting sticky CTA at position {insert_pos}")
print(f"Context around insert point: ...{html_modified[insert_pos-20:insert_pos]}[INSERT]{html_modified[insert_pos:insert_pos+80]}...")

# Insert the sticky CTA right after the inner div opening
html_final = html_modified[:insert_pos] + sticky_cta + html_modified[insert_pos:]

# --- Step 4: Write output ---
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"\nDone! Wrote {len(html_final)} bytes to {OUTPUT}")
print(f"Original: {len(html)} bytes")
print(f"Difference: {len(html_final) - len(html)} bytes")

# Verify the sticky CTA is now before image-71G3Z99SAZ (first content element)
verify_pos = html_final.find('position: sticky; top: 0px; z-index: 9999')
image_pos = html_final.find('id="image-71G3Z99SAZ"')
if verify_pos < image_pos:
    print("\nVERIFICATION PASSED: Sticky CTA is now before the first content element")
else:
    print("\nVERIFICATION FAILED: Sticky CTA is NOT before image-71G3Z99SAZ")
