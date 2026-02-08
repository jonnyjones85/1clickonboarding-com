#!/usr/bin/env python3
"""
Phase 2: Font Size Harmonization.

Maps 36 unique font sizes (including fractional values like 16.5px, 19.5px,
44.8px) to a clean 9-stop type scale using CSS custom properties.

Approach:
  1. Defines CSS variables (:root block) prepended to the first <style> tag
  2. Replaces font-size:XXpx values inline throughout all <style> blocks
     with var(--fs-*) equivalents
  3. Leaves inline style="" attributes untouched (only 17 occurrences, not
     worth the risk of breaking layout)

This is a value-only change — no selectors, blocks, or class attributes are
touched. Safe per session 12 lessons.
"""

import os
import re
import shutil

HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")

# =============================================================================
# TYPE SCALE: 9 stops
# =============================================================================

TYPE_SCALE = {
    "xs":   13,   # fine print, badges (9-13px → 13px)
    "sm":   15,   # small body, captions (14-16px → 15px)
    "base": 17,   # secondary body (16.5-18px → 17px)
    "lg":   20,   # primary body text — most common (19-21px → 20px)
    "xl":   24,   # sub-headings (22-25px → 24px)
    "2xl":  28,   # section headings (26-29px → 28px)
    "3xl":  32,   # major headings (30-35px → 32px)
    "4xl":  44,   # hero headings (36-46px → 44px)
    "5xl":  52,   # display text (50-64px → 52px)
}

# Mapping: original px value → scale token name
# Manually verified against the 36 unique sizes found in the file
SIZE_TO_TOKEN = {
    9:    "xs",
    12:   "xs",
    13:   "xs",
    14:   "sm",
    15:   "sm",
    16:   "sm",
    16.5: "base",
    17:   "base",
    18:   "base",
    19:   "lg",
    19.5: "lg",
    20:   "lg",
    21:   "lg",
    22:   "xl",
    23:   "xl",
    24:   "xl",
    25:   "xl",
    26:   "2xl",
    27:   "2xl",
    28:   "2xl",
    30:   "3xl",
    31:   "3xl",
    32:   "3xl",
    34:   "3xl",
    35:   "3xl",
    36:   "4xl",
    38:   "4xl",
    40:   "4xl",
    42:   "4xl",
    44.8: "4xl",
    46:   "4xl",
    50:   "5xl",
    52:   "5xl",
    56:   "5xl",
    60:   "5xl",
    64:   "5xl",
}

# CSS variable definitions
CSS_VARS = """/* === Type Scale (Phase 2: Font Harmonization) === */
:root {
  --fs-xs: 13px;
  --fs-sm: 15px;
  --fs-base: 17px;
  --fs-lg: 20px;
  --fs-xl: 24px;
  --fs-2xl: 28px;
  --fs-3xl: 32px;
  --fs-4xl: 44px;
  --fs-5xl: 52px;
}
"""


def harmonize_fonts(html_path=HTML_PATH):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_size = len(content)

    # Create backup
    backup_path = html_path + ".pre-harmonize"
    shutil.copy2(html_path, backup_path)
    print(f"Backup: {backup_path}")

    # Step 1: Inject CSS variables into the first <style> tag
    first_style = content.find("<style")
    if first_style == -1:
        print("ERROR: No <style> tag found!")
        return
    # Find the end of the opening <style...> tag
    style_open_end = content.find(">", first_style) + 1
    content = content[:style_open_end] + "\n" + CSS_VARS + content[style_open_end:]
    print(f"Injected CSS variables after first <style> tag")

    # Step 2: Replace font-size values in <style> blocks only
    # We need to be careful to only replace inside <style>...</style>, not in
    # inline style="" attributes in the body

    total_replacements = 0
    token_counts = {t: 0 for t in TYPE_SCALE}
    unmatched = []

    def replace_font_size(match):
        nonlocal total_replacements
        full = match.group(0)        # e.g., "font-size:20px" or "font-size: 16.5px"
        val_str = match.group(1)     # e.g., "20" or "16.5"
        val = float(val_str)

        # Convert int-like floats
        if val == int(val):
            val = int(val)

        if val in SIZE_TO_TOKEN:
            token = SIZE_TO_TOKEN[val]
            token_counts[token] += 1
            total_replacements += 1
            return f"font-size:var(--fs-{token})"
        else:
            unmatched.append(val)
            return full

    # Process each <style> block
    def process_style_block(m):
        tag_open = m.group(1)  # <style...>
        css_content = m.group(2)
        tag_close = m.group(3)  # </style>

        # Replace font-size declarations within CSS
        css_content = re.sub(
            r'font-size:\s*([\d.]+)px',
            replace_font_size,
            css_content
        )
        return tag_open + css_content + tag_close

    content = re.sub(
        r'(<style[^>]*>)(.*?)(</style>)',
        process_style_block,
        content,
        flags=re.DOTALL
    )

    # Write
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_size = len(content)

    print(f"\nResults:")
    print(f"  Total replacements: {total_replacements}")
    print(f"  File size: {original_size:,} → {new_size:,} bytes ({new_size - original_size:+,})")
    print(f"\nToken distribution:")
    for token, count in token_counts.items():
        px = TYPE_SCALE[token]
        print(f"  --fs-{token:4s} ({px:2d}px): {count:4d} declarations")
    if unmatched:
        print(f"\nUnmatched sizes (left as-is): {set(unmatched)}")
    else:
        print(f"\nAll font sizes mapped to scale tokens.")


if __name__ == "__main__":
    harmonize_fonts()
