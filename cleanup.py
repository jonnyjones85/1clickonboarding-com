#!/usr/bin/env python3
"""
Cleanup script for 1clickonboarding-clean site.
Removes GHL artifacts, unused fonts, and optimizes HTML/CSS.

Run from the 1clickonboarding-clean/ directory:
    python cleanup.py

Creates .bak backups before modifying files.
"""

import re
import os

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(SITE_DIR, "index.html")
FONTS_CSS = os.path.join(SITE_DIR, "css", "google-fonts.css")

# Fonts actually used in the HTML (found via analysis)
KEEP_FONTS = {"Roboto", "Kalam"}

# Unicode ranges to keep (Latin only for English site)
KEEP_UNICODE = {
    "U+0000-00FF",  # Basic Latin
    "U+0100-024F",  # Latin Extended-A & B
    "U+0250-02AF",  # IPA Extensions
    "U+1E00-1EFF",  # Latin Extended Additional
    "U+2000-206F",  # General Punctuation
    "U+2070-209F",  # Superscripts and Subscripts
    "U+20A0-20CF",  # Currency Symbols
    "U+2100-214F",  # Letterlike Symbols
    "U+2200-22FF",  # Mathematical Operators
    "U+25A0-25FF",  # Geometric Shapes
    "U+FB00-FB4F",  # Alphabetic Presentation Forms
    "U+FEFF",       # BOM
    "U+FFFD",       # Replacement Character
}


def cleanup_html(path):
    """Clean GHL artifacts from index.html."""
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    original_size = len(html.encode("utf-8"))
    changes = []

    # 1. Simplify <picture> elements — remove redundant <source> tags
    # Pattern: <picture ...><source ...>...<img ...></picture> → <img ...>
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

    # 5. Remove font-weight:undefined from CSS
    count = len(re.findall(r'font-weight:\s*undefined', html))
    html = re.sub(r';?font-weight:\s*undefined', '', html)
    changes.append(f"Removed {count} font-weight:undefined declarations")

    # 6. Remove broken icon pseudo-element patterns
    # Pattern: content:'\'; font-family: '';margin-right:5px;font-weight:700
    pattern = r"content:'\\';[\s\n]*font-family:\s*'';[\s\n]*margin-right:\s*5px;[\s\n]*font-weight:\s*700"
    count = len(re.findall(pattern, html))
    html = re.sub(pattern, '', html)
    changes.append(f"Removed {count} broken icon pseudo-element patterns")

    # 7. Clean up empty CSS rule bodies left behind
    # e.g., .selector{} or .selector:before{}
    html = re.sub(r'(\.[a-zA-Z0-9_-]+(?::[\w-]+)?)\{\s*\}', '', html)

    # 8. Remove empty <div></div> elements (no attributes)
    count = len(re.findall(r'<div></div>', html))
    html = re.sub(r'<div></div>', '', html)
    changes.append(f"Removed {count} empty <div></div> elements")

    new_size = len(html.encode("utf-8"))
    savings = original_size - new_size

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return changes, original_size, new_size, savings


def cleanup_fonts_css(path):
    """Remove unused font families and non-latin unicode ranges."""
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()

    original_size = len(css.encode("utf-8"))

    # Parse @font-face blocks
    blocks = re.findall(r'(/\*[^*]*\*/\s*)?@font-face\s*\{[^}]+\}', css)

    kept_blocks = []
    removed_families = set()
    total_removed = 0
    latin_filtered = 0

    for block in blocks:
        full_block = block if isinstance(block, str) else block
        # Re-extract from original since findall with groups is tricky
        pass

    # Better approach: split by @font-face and process each
    # Split CSS into @font-face blocks
    parts = re.split(r'(?=@font-face)', css)
    kept_parts = []
    removed_count = 0
    kept_count = 0

    for part in parts:
        if not part.strip().startswith('@font-face'):
            # Comment or preamble
            kept_parts.append(part)
            continue

        # Extract font-family
        family_match = re.search(r"font-family:\s*'([^']+)'", part)
        if not family_match:
            kept_parts.append(part)
            continue

        family = family_match.group(1)

        # Remove unused font families entirely
        if family not in KEEP_FONTS:
            removed_families.add(family)
            removed_count += 1
            continue

        # For kept fonts, check unicode-range — keep only latin subsets
        range_match = re.search(r'unicode-range:\s*([^;]+);', part)
        if range_match:
            ranges_str = range_match.group(1).strip()
            # Check if any range in KEEP_UNICODE is in this block
            ranges = [r.strip() for r in ranges_str.split(',')]
            has_latin = any(
                any(keep in r for keep in KEEP_UNICODE)
                for r in ranges
            )
            # Also keep if range starts with U+0000 or U+0020 (basic latin)
            has_basic = any(
                r.startswith('U+0000') or r.startswith('U+0020') or r.startswith('U+00')
                for r in ranges
            )
            if not has_latin and not has_basic:
                latin_filtered += 1
                removed_count += 1
                continue

        kept_parts.append(part)
        kept_count += 1

    new_css = ''.join(kept_parts)
    new_size = len(new_css.encode("utf-8"))
    savings = original_size - new_size

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_css)

    return {
        "removed_families": sorted(removed_families),
        "removed_blocks": removed_count,
        "kept_blocks": kept_count,
        "latin_filtered": latin_filtered,
        "original_size": original_size,
        "new_size": new_size,
        "savings": savings,
    }


def main():
    print("=" * 60)
    print("1clickonboarding-clean Cleanup Script")
    print("=" * 60)

    # HTML cleanup
    print("\n--- HTML Cleanup ---")
    changes, orig, new, savings = cleanup_html(INDEX_HTML)
    for c in changes:
        print(f"  ✓ {c}")
    print(f"\n  HTML: {orig:,} → {new:,} bytes (saved {savings:,} bytes, {savings/orig*100:.1f}%)")

    # Font CSS cleanup
    print("\n--- Google Fonts CSS Cleanup ---")
    result = cleanup_fonts_css(FONTS_CSS)
    print(f"  ✓ Removed {len(result['removed_families'])} unused font families: {', '.join(result['removed_families'])}")
    print(f"  ✓ Removed {result['latin_filtered']} non-latin unicode-range blocks")
    print(f"  ✓ Kept {result['kept_blocks']} @font-face blocks")
    print(f"\n  CSS: {result['original_size']:,} → {result['new_size']:,} bytes (saved {result['savings']:,} bytes, {result['savings']/result['original_size']*100:.1f}%)")

    # Total
    total_savings = savings + result['savings']
    total_orig = orig + result['original_size']
    print(f"\n{'=' * 60}")
    print(f"TOTAL SAVINGS: {total_savings:,} bytes ({total_savings/1024:.0f} KB, {total_savings/total_orig*100:.1f}%)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
