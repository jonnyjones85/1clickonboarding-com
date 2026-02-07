#!/usr/bin/env python3
"""
Apply layout fixes, safe HTML cleanup, and font size reduction (85%) to index.html.

Operates on the restored backup (2570 lines). Does NOT touch google-fonts.css.

Steps:
  1. Layout fix: #hl_main_popup width 960px -> 100%;max-width:1280px
  2. Layout fix: mobile width 380px -> 100%
  3. Layout fix: sticky sidebar max-height + overflow
  4. Safe cleanup: empty class/style/data-animation-class attributes
  5. Safe cleanup: simplify <picture> to <img>
  6. Font size reduction: all font-size:Xpx -> ceil(X * 0.85)px

SKIPS dangerous operations that broke colors in the previous cleanup:
  - font-weight:undefined removal
  - content:'\\' pattern removal
  - empty CSS rule cleanup
"""

import re
import os
import math

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(SITE_DIR, "index.html")


def apply_layout_fixes(html):
    """Apply the 2 layout fixes that were correct."""
    changes = []

    # Fix 1: #hl_main_popup width: 960px -> width:100%;max-width:1280px
    old = "width:960px}"
    new = "width:100%;max-width:1280px}"
    if old in html:
        html = html.replace(old, new, 1)
        changes.append("Fixed #hl_main_popup width: 960px -> 100%;max-width:1280px")

    # Fix 2: Mobile width: 380px!important -> 100%!important
    old = "width:380px!important"
    new = "width:100%!important"
    if old in html:
        html = html.replace(old, new, 1)
        changes.append("Fixed mobile width: 380px -> 100%")

    # Fix 3: Sticky sidebar - add max-height and overflow
    old_sticky = "position: sticky; top: 0px; z-index: 9999;padding-top:15px;"
    new_sticky = "position: sticky; top: 0px; z-index: 9999;padding-top:15px;max-height:100vh;overflow-y:auto;"
    if old_sticky in html:
        html = html.replace(old_sticky, new_sticky, 1)
        changes.append("Added max-height:100vh;overflow-y:auto to sticky sidebar")

    return html, changes


def safe_cleanup(html):
    """Only safe HTML cleanup operations that don't risk breaking colors."""
    changes = []

    # 1. Simplify <picture> elements to <img>
    def simplify_picture(match):
        full = match.group(0)
        img_match = re.search(r'<img\s[^>]+>', full)
        if img_match:
            return img_match.group(0)
        return full

    count_before = len(re.findall(r'<picture\b', html))
    html = re.sub(
        r'<picture[^>]*>.*?</picture>',
        simplify_picture,
        html,
        flags=re.DOTALL
    )
    changes.append(f"Simplified {count_before} <picture> elements to <img>")

    # 2. Remove empty class="" attributes
    count = len(re.findall(r'\sclass=""', html))
    html = re.sub(r'\sclass=""', '', html)
    changes.append(f"Removed {count} empty class=\"\" attributes")

    # 3. Remove empty style="" attributes
    count = len(re.findall(r'\sstyle=""', html))
    html = re.sub(r'\sstyle=""', '', html)
    changes.append(f"Removed {count} empty style=\"\" attributes")

    # 4. Remove empty data-animation-class="" attributes
    count = len(re.findall(r'\sdata-animation-class=""', html))
    html = re.sub(r'\sdata-animation-class=""', '', html)
    changes.append(f"Removed {count} empty data-animation-class=\"\" attributes")

    # 5. Remove empty <div></div>
    count = len(re.findall(r'<div></div>', html))
    html = re.sub(r'<div></div>', '', html)
    changes.append(f"Removed {count} empty <div></div> elements")

    return html, changes


def reduce_font_sizes(html, factor=0.85):
    """Reduce all font-size:Xpx declarations to ceil(X * factor)px."""
    changes = []
    count = 0

    def replace_font_size(match):
        nonlocal count
        prefix = match.group(1)  # "font-size:" possibly with spaces
        value = float(match.group(2))
        new_value = math.ceil(value * factor)
        count += 1
        return f"{prefix}{new_value}px"

    # Match font-size:Xpx (with optional spaces, in both style attrs and CSS)
    html = re.sub(
        r'(font-size:\s*)(\d+(?:\.\d+)?)px',
        replace_font_size,
        html
    )

    changes.append(f"Reduced {count} font-size declarations to {int(factor*100)}% (rounded up)")
    return html, changes


def main():
    print("=" * 60)
    print("Apply Fixes: Layout + Safe Cleanup + Font Size Reduction")
    print("=" * 60)

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    original_size = len(html.encode("utf-8"))
    all_changes = []

    # Step 1: Layout fixes
    print("\n--- Layout Fixes ---")
    html, changes = apply_layout_fixes(html)
    all_changes.extend(changes)
    for c in changes:
        print(f"  ✓ {c}")

    # Step 2: Safe cleanup
    print("\n--- Safe HTML Cleanup ---")
    html, changes = safe_cleanup(html)
    all_changes.extend(changes)
    for c in changes:
        print(f"  ✓ {c}")

    # Step 3: Font size reduction
    print("\n--- Font Size Reduction (85%) ---")
    html, changes = reduce_font_sizes(html, 0.85)
    all_changes.extend(changes)
    for c in changes:
        print(f"  ✓ {c}")

    # Write result
    new_size = len(html.encode("utf-8"))
    savings = original_size - new_size

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n{'=' * 60}")
    print(f"HTML: {original_size:,} → {new_size:,} bytes (saved {savings:,} bytes, {savings/original_size*100:.1f}%)")
    print(f"Total changes: {len(all_changes)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
