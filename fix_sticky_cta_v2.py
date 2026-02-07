#!/usr/bin/env python3
"""
fix_sticky_cta_v2.py — Revert v1's "move CTA to top" and use flex-grow instead.

V1 moved the sticky CTA to be the first child of col-8A1V8YCH9N > .inner,
which broke the layout (CTA covers all 121 content elements).

V2 moves the CTA back into custom-code-FfSGpAGpKG > custom-code-container
(before #stickyLength), and adds CSS flex:1 + height:100% so the container
stretches to fill remaining column height, giving position:sticky a tall parent.
"""

INPUT = "index.html"
OUTPUT = "index.html"

with open(INPUT, "r", encoding="utf-8") as f:
    html = f.read()

# =============================================================================
# Step 1: Find and extract the sticky CTA div from its current position
# =============================================================================
# Currently it's the first child of .inner inside col-8A1V8YCH9N:
#   ...id="col-8A1V8YCH9N"><div class="radius10 noBorder bg bgCover vertical inner"><div style="  position: sticky;...">
#     <div class="top_right_sec big_cta">...</div>
#   </div><div id="image-71G3Z99SAZ"...

inner_marker = 'id="col-8A1V8YCH9N"><div class="radius10 noBorder bg bgCover vertical inner">'
inner_pos = html.find(inner_marker)
if inner_pos == -1:
    print("ERROR: Could not find col-8A1V8YCH9N inner div")
    exit(1)

# The sticky CTA starts right after the inner marker
cta_start = inner_pos + len(inner_marker)

# The sticky CTA div opens with <div style="  position: sticky; ...">
# and closes with </div> right before the first content element <div id="image-71G3Z99SAZ"
sticky_open = '<div style="  position: sticky; top: 0px; z-index: 9999;padding-top:15px;max-height:100vh;overflow-y:auto;">'
if not html[cta_start:cta_start + len(sticky_open)] == sticky_open:
    print("ERROR: Expected sticky CTA div right after .inner opening")
    print(f"Found: {html[cta_start:cta_start+100]!r}")
    exit(1)

# Find where this sticky div ends — it's right before <div id="image-71G3Z99SAZ"
first_content = '<div id="image-71G3Z99SAZ"'
cta_end_search = html.find(first_content, cta_start)
if cta_end_search == -1:
    print("ERROR: Could not find image-71G3Z99SAZ (first content element after CTA)")
    exit(1)

# The sticky CTA HTML is everything from cta_start to just before the first content element
sticky_cta_html = html[cta_start:cta_end_search]

# Verify it contains the expected content
assert 'top_right_sec big_cta' in sticky_cta_html, "Sticky CTA doesn't contain expected class"
assert 'secure_checkout_img' in sticky_cta_html, "Sticky CTA doesn't contain checkout image"

print(f"Found sticky CTA: {len(sticky_cta_html)} chars")
print(f"Starts with: {sticky_cta_html[:80]!r}")
print(f"Ends with: {sticky_cta_html[-80:]!r}")

# =============================================================================
# Step 2: Remove the sticky CTA from its current position
# =============================================================================
html = html[:cta_start] + html[cta_end_search:]
print(f"\nRemoved sticky CTA from col-8A1V8YCH9N .inner first-child position")

# =============================================================================
# Step 3: Insert CTA into custom-code-FfSGpAGpKG > custom-code-container
# =============================================================================
# Target: <div class="custom-code-container ccustom-code-FfSGpAGpKG sticky_buy_element">
#           {INSERT CTA HERE}
#           <div id="stickyLength" style="display:none;">
container_marker = '<div class="custom-code-container ccustom-code-FfSGpAGpKG sticky_buy_element">'
# Also check with id= variant
container_marker_alt = 'class="custom-code-container ccustom-code-FfSGpAGpKG sticky_buy_element"'

container_pos = html.find(container_marker)
if container_pos == -1:
    container_pos = html.find(container_marker_alt)
    if container_pos == -1:
        print("ERROR: Could not find custom-code-container for FfSGpAGpKG")
        exit(1)
    # Find the > that closes this tag
    tag_close = html.find('>', container_pos)
    insert_pos = tag_close + 1
else:
    insert_pos = container_pos + len(container_marker)

# Find #stickyLength to verify we're inserting in the right place
stickylen_pos = html.find('<div id="stickyLength"', insert_pos)
if stickylen_pos == -1:
    print("ERROR: Could not find #stickyLength after container")
    exit(1)

# Insert the CTA before #stickyLength
html = html[:insert_pos] + "\n" + sticky_cta_html + "\n" + html[insert_pos:]
print(f"Inserted sticky CTA back into custom-code-FfSGpAGpKG container")

# =============================================================================
# Step 4: Add CSS rules for flex-grow stretching
# =============================================================================
# Add near the existing #col-8A1V8YCH9N CSS block (around line 247 area)
css_target = """#col-8A1V8YCH9N {
    position: relative;
    Left: 20px;
 /* Adjust this value to control the vertical overlap */
    z-index: 2;
}"""

css_addition = """
#custom-code-FfSGpAGpKG.c-custom-code { flex: 1; }
.ccustom-code-FfSGpAGpKG { height: 100%; }"""

css_replacement = css_target + css_addition

if css_target not in html:
    print("ERROR: Could not find #col-8A1V8YCH9N CSS block to add rules near")
    exit(1)

html = html.replace(css_target, css_replacement, 1)
print(f"Added flex:1 and height:100% CSS rules")

# =============================================================================
# Step 5: Write output
# =============================================================================
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone! Wrote {len(html)} chars to {OUTPUT}")

# =============================================================================
# Verification
# =============================================================================
# 1. Sticky CTA should be inside custom-code-FfSGpAGpKG, not first child of .inner
inner_pos2 = html.find(inner_marker)
after_inner = html[inner_pos2 + len(inner_marker):inner_pos2 + len(inner_marker) + 50]
if 'position: sticky' in after_inner:
    print("\nVERIFICATION FAILED: Sticky CTA is still first child of .inner!")
else:
    print("\nVERIFICATION PASSED: Sticky CTA is no longer first child of .inner")

# 2. Sticky CTA should be inside custom-code-FfSGpAGpKG container
container_pos2 = html.find('ccustom-code-FfSGpAGpKG sticky_buy_element')
stickylen_pos2 = html.find('<div id="stickyLength"', container_pos2)
sticky_pos2 = html.find('position: sticky; top: 0px; z-index: 9999', container_pos2)
if container_pos2 < sticky_pos2 < stickylen_pos2:
    print("VERIFICATION PASSED: Sticky CTA is inside custom-code container before #stickyLength")
else:
    print("VERIFICATION FAILED: CTA position is wrong relative to container/stickyLength")

# 3. CSS rules should exist
if '#custom-code-FfSGpAGpKG.c-custom-code { flex: 1; }' in html:
    print("VERIFICATION PASSED: flex:1 CSS rule present")
else:
    print("VERIFICATION FAILED: flex:1 CSS rule missing")

if '.ccustom-code-FfSGpAGpKG { height: 100%; }' in html:
    print("VERIFICATION PASSED: height:100% CSS rule present")
else:
    print("VERIFICATION FAILED: height:100% CSS rule missing")

# 4. First content element (image-71G3Z99SAZ) should still be in the right column
img_pos = html.find('id="image-71G3Z99SAZ"')
if img_pos > 0:
    print("VERIFICATION PASSED: image-71G3Z99SAZ still present")
else:
    print("VERIFICATION FAILED: image-71G3Z99SAZ missing!")
