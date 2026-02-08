#!/usr/bin/env python3
"""
merge_responsive.py — Merge desktop/mobile duplicate sections into single responsive layout.

Removes 9 mobile-only sections (keeping desktop versions), strips desktop-only classes,
removes dead CSS for removed sections, adds responsive overrides, normalizes CTA links.

Expected result: 23 sections → 14 sections, ~13% HTML size reduction.
"""

import re
import shutil
import os

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(SITE_DIR, "index.html")
BACKUP_PATH = os.path.join(SITE_DIR, "index.html.pre-merge")

# 9 mobile-only section IDs to remove
MOBILE_SECTIONS_TO_REMOVE = [
    "section-zcTQG6mMON",   # mobile header
    "section-grGkaPPcTK",   # mobile hero
    "section-BFSQAbkk13",   # mobile sales pitch
    "section-_GnYZtBI4o",   # mobile mega sales letter
    "section-To-q1ypEMs",   # mobile CTA block
    "section-k_vj1pLUJV",   # mobile "also getting"
    "section-UFWCT63ZiY",   # mobile bonuses
    "section-kGFLVwZNUJ",   # mobile guarantee (duplicate of universal sec 21)
    "section-I55y7eLVLD",   # mobile FAQ
]

# Component IDs associated with mobile sections (for CSS cleanup)
# These are the IDs found in the CSS style blocks that reference removed mobile sections
MOBILE_COMPONENT_IDS = [
    # section-zcTQG6mMON (mobile header)
    "zcTQG6mMON", "xAr1nd1FVi", "qnlNYTNm0h", "vWZCP58FjA",
    # section-grGkaPPcTK (mobile hero)
    "grGkaPPcTK", "a1vtZ1Nc5V", "8sER3Pu7s_", "7L2HE5zJVI", "W0BidVw7rl",
    "mWUxalHLAM", "zjEGWjDlHx", "fvHPSD_imM", "_n_zp6h1cF", "yleGArvhki",
    "KvFKlEe_pq", "VxbsSMPgk6",
    # section-BFSQAbkk13 (mobile sales pitch)
    "BFSQAbkk13", "bTHdQ2KpZz", "6NwYa8nSA0", "tqoj8HlQQn", "0QXx5-7nGl",
    "QAlde4iZA3", "a17cEfEECt", "o0YQTk-Paf", "pZLrI_7tj-", "GITzCyHlMj",
    "SFEhJghodZ", "0uG6vR6fKd", "BQoU9Tw4Gb", "pXTacIo3ao",
    "zFWKe0l5vV", "t3FDiKGLIj", "i1zMkSWX5K", "LUF4bPa-Sv", "LaHdPQHY8N",
    "x9Rjf1sV2D", "2SEqCyhTBp", "hw5YOE0186", "fo27K1S0lE", "bvcpPVeFX7",
    "S7sDCaZ3kE", "hRsQ8tKh6H",
    "xf68kwd-Do", "8vXbV3JkLP", "pfdZJnHVcK", "6WF7LQ7Vmv", "8QMF2zIWxO",
    "_UI4r7iz6s", "BkUDIDcBmb", "cwaXzuYN2z", "5OwSPHtRly", "NFCO5rvhFD",
    "DLDMFrJg21", "TAOhzkUcSw", "EBPJUh1Qjh", "-Q68iHIVo9", "iSwAAgFRUE",
    "HGNUmw01v2", "SnLml0tTjX", "ErRzoT_ygw", "BsMFvctrdi", "2sg_G_Cuox",
    "jAkIpW-eRS", "v2Czo-3cxq", "zWyUsM1Kdl", "0ifrO5vGoD", "ZB5BPSbNcQ",
    "ojCDRsHQ9q", "u1UQiEayuS", "l1G6R0Tuai",
    # section-_GnYZtBI4o (mobile mega sales letter)
    "_GnYZtBI4o",
    # section-To-q1ypEMs (mobile CTA block)
    "To-q1ypEMs",
    # section-k_vj1pLUJV (mobile "also getting")
    "k_vj1pLUJV",
    # section-UFWCT63ZiY (mobile bonuses)
    "UFWCT63ZiY",
    # section-kGFLVwZNUJ (mobile guarantee)
    "kGFLVwZNUJ",
    # section-I55y7eLVLD (mobile FAQ)
    "I55y7eLVLD",
]

RESPONSIVE_CSS = """
/* === Responsive overrides (merged from mobile sections) === */

/* After removing mobile-only sections, desktop sections must show on mobile */
@media only screen and (max-width: 767px) {
  .desktop-only { display: block !important; }

  /* Hero: tighter margin */
  .hl_page-preview--content .section-Y44Z2WH865 { margin-bottom: -10px; }

  /* Mega sales letter: remove negative top margin */
  .hl_page-preview--content .section-51HYL80S4E { margin-top: 0; padding-bottom: 20px; }

  /* CTA block: tighter padding */
  .hl_page-preview--content .section-561M4VJ0Q0 { padding-top: 10px; padding-bottom: 0; }

  /* Bonuses: tighter padding */
  .hl_page-preview--content .section-8Q4F1SUW66 { padding-bottom: 0; }

  /* FAQ: tighter padding */
  .hl_page-preview--content .section-LMKIGKCNJC { padding-top: 20px; padding-bottom: 40px; padding-left: 30px; }

  /* Hero custom-code font sizes (desktop 44px -> mobile 24px) */
  #custom-code-BoGDpFK3rd h1 { font-size: 24px !important; }
  #custom-code-kU7OgPDUZv div div { font-size: 12px !important; padding: 5px 10px !important; }
  #custom-code-gHMMtdgX5Y h1 { font-size: 25px !important; }
}
"""


def phase1_backup():
    """Phase 1: Create backup."""
    shutil.copy2(INDEX_PATH, BACKUP_PATH)
    print(f"[Phase 1] Backup created: {BACKUP_PATH}")
    print(f"  Original size: {os.path.getsize(INDEX_PATH):,} bytes")


def phase2_remove_mobile_sections(html):
    """Phase 2: Remove 9 mobile-only sections from body HTML.

    Uses regex to find all <div and </div> tags, then tracks depth to find
    the matching closing tag for each section.
    """
    removed_count = 0

    # Precompile regex for finding div open/close tags
    div_tag_re = re.compile(r'<div[\s>]|</div>')

    for section_id in MOBILE_SECTIONS_TO_REMOVE:
        # Find the section start marker
        marker = f'id="{section_id}"'
        start_idx = html.find(marker)

        if start_idx == -1:
            print(f"  WARNING: Section {section_id} not found in HTML")
            continue

        # Walk backwards to find the opening <div that contains this id
        div_start = html.rfind('<div', 0, start_idx)
        if div_start == -1:
            print(f"  WARNING: Could not find opening <div for {section_id}")
            continue

        # Use regex to find all div tags from div_start onwards
        depth = 0
        end_pos = -1

        for m in div_tag_re.finditer(html, div_start):
            tag = m.group()
            if tag.startswith('</'):
                depth -= 1
                if depth == 0:
                    end_pos = m.end()
                    break
            else:
                depth += 1

        if end_pos == -1:
            print(f"  WARNING: Could not find matching </div> for {section_id}")
            continue

        # Remove the section
        removed_bytes = end_pos - div_start
        html = html[:div_start] + html[end_pos:]
        removed_count += 1
        print(f"  Removed: {section_id} ({removed_bytes:,} bytes)")

    print(f"[Phase 2] Removed {removed_count} mobile-only sections")
    return html


def phase3_strip_desktop_only(html):
    """Phase 3: Strip 'desktop-only' and 'mobile-only' classes from all remaining elements."""

    # Count before
    desktop_count = html.count('desktop-only')
    mobile_count = html.count('mobile-only')

    # Remove ' desktop-only' and ' mobile-only' from class attributes
    # Handle cases: class="... desktop-only ...", class="desktop-only ...", class="... desktop-only"
    html = re.sub(r'\s+desktop-only(?=[\s"])', '', html)
    html = re.sub(r'desktop-only\s+', '', html)
    html = re.sub(r'\s+mobile-only(?=[\s"])', '', html)
    html = re.sub(r'mobile-only\s+', '', html)

    # Clean up any remaining standalone instances
    html = html.replace(' desktop-only"', '"')
    html = html.replace('"desktop-only"', '""')
    html = html.replace(' mobile-only"', '"')
    html = html.replace('"mobile-only"', '""')

    remaining = html.count('desktop-only') + html.count('mobile-only')
    # Check if remaining are only in CSS (e.g., inside <style> or class selectors)
    # Those in CSS rule bodies are fine — they're selectors being defined, not usage

    print(f"[Phase 3] Stripped desktop-only ({desktop_count}) and mobile-only ({mobile_count}) class references")
    if remaining > 0:
        print(f"  Note: {remaining} references remain (likely in CSS selectors targeting removed sections)")

    return html


def _extract_ids_from_css(css_text):
    """Extract all GHL component IDs referenced in CSS text."""
    id_re = re.compile(
        r'(?:section|row|col|heading|sub-heading|custom-code|video|paragraph|'
        r'image|button|c-button|form|bg-section|cheading|csub-heading|cvideo|'
        r'cparagraph|cimage|cbutton)-([A-Za-z0-9_-]{6,})'
    )
    return set(id_re.findall(css_text))


def _filter_mobile_rules(block_text, mobile_id_set):
    """Remove individual CSS rules that reference ONLY mobile IDs from a mixed block.

    Parses minified CSS by tracking brace depth. Handles @media wrappers.
    Returns the filtered block text and count of bytes removed.
    """
    # Tokenize into top-level CSS chunks: rules and @media blocks
    # A top-level rule ends at } when depth returns to 0
    # An @media block ends at } when depth returns to 0 (contains nested rules)
    chunks = []
    i = 0
    length = len(block_text)

    # Skip leading comment marker + :root block
    # We want to preserve the comment and :root{} declarations
    while i < length:
        # Skip whitespace
        if block_text[i] in ' \t\n\r':
            i += 1
            continue
        # Skip comments
        if block_text[i:i+2] == '/*':
            end = block_text.find('*/', i)
            if end == -1:
                break
            chunks.append(('comment', block_text[i:end+2]))
            i = end + 2
            continue
        # Found start of a rule or @-rule
        break

    # Now parse individual CSS rules/blocks
    while i < length:
        # Skip whitespace
        start = i
        while i < length and block_text[i] in ' \t\n\r':
            i += 1
        if i >= length:
            break

        # Check for @media or @-rule
        if block_text[i] == '@':
            # Find the opening brace of the @-rule
            brace_pos = block_text.find('{', i)
            if brace_pos == -1:
                chunks.append(('other', block_text[start:]))
                break
            # Now track nested braces to find the matching close
            depth = 1
            j = brace_pos + 1
            while j < length and depth > 0:
                if block_text[j] == '{':
                    depth += 1
                elif block_text[j] == '}':
                    depth -= 1
                j += 1
            rule_text = block_text[start:j]
            chunks.append(('at-rule', rule_text))
            i = j
            continue

        # Check for :root or regular rule — find opening {
        if block_text[i:i+5] == ':root':
            # :root{...} block — always keep (CSS variables)
            brace_pos = block_text.find('{', i)
            if brace_pos == -1:
                chunks.append(('other', block_text[start:]))
                break
            depth = 1
            j = brace_pos + 1
            while j < length and depth > 0:
                if block_text[j] == '{':
                    depth += 1
                elif block_text[j] == '}':
                    depth -= 1
                j += 1
            chunks.append(('root', block_text[start:j]))
            i = j
            continue

        # Regular CSS rule: selector { properties }
        brace_pos = block_text.find('{', i)
        if brace_pos == -1:
            # Remaining text (trailing whitespace, etc.)
            chunks.append(('other', block_text[start:]))
            break

        # Track braces for the rule body
        depth = 1
        j = brace_pos + 1
        while j < length and depth > 0:
            if block_text[j] == '{':
                depth += 1
            elif block_text[j] == '}':
                depth -= 1
            j += 1
        rule_text = block_text[start:j]
        chunks.append(('rule', rule_text))
        i = j

    # Now filter: remove rules/at-rules where ALL referenced IDs are mobile-only
    kept = []
    removed_bytes = 0

    for chunk_type, chunk_text in chunks:
        if chunk_type in ('comment', 'root', 'other'):
            kept.append(chunk_text)
            continue

        ids_in_chunk = _extract_ids_from_css(chunk_text)

        if not ids_in_chunk:
            # No GHL IDs — keep (generic CSS)
            kept.append(chunk_text)
            continue

        # If ALL IDs in this rule are mobile-only, remove it
        if ids_in_chunk.issubset(mobile_id_set):
            removed_bytes += len(chunk_text)
        else:
            kept.append(chunk_text)

    return ''.join(kept), removed_bytes


def phase4_remove_dead_css(html):
    """Phase 4: Remove CSS rules targeting IDs from the 9 removed mobile sections.

    Two strategies:
    - Pure mobile blocks (all IDs are mobile): remove the entire block
    - Mixed blocks (has both mobile + desktop IDs): remove individual rules only
    """
    mobile_id_set = set(MOBILE_COMPONENT_IDS)
    style_marker = re.compile(r'/\* ---- (?:top|Section) styles ----- \*/')

    head_end = html.find('</style></head>')
    if head_end == -1:
        print("[Phase 4] Could not find style/head boundary")
        return html

    head_content = html[:head_end]
    body_content = html[head_end:]

    markers = list(style_marker.finditer(head_content))

    removed_blocks = 0
    removed_rules_bytes = 0
    removed_block_bytes = 0

    # Process blocks in reverse order to maintain positions
    changes = []  # (start, end, replacement_or_None)

    for i, m in enumerate(markers):
        block_start = m.start()
        block_end = markers[i + 1].start() if i + 1 < len(markers) else len(head_content)
        block_text = head_content[block_start:block_end]

        # Extract all IDs in this block
        ids_in_block = _extract_ids_from_css(block_text)
        mobile_ids_in_block = ids_in_block & mobile_id_set
        desktop_ids_in_block = ids_in_block - mobile_id_set

        if not mobile_ids_in_block:
            # No mobile IDs — skip entirely
            continue

        if not desktop_ids_in_block:
            # Pure mobile block — remove entirely
            changes.append((block_start, block_end, None))
            removed_block_bytes += block_end - block_start
            removed_blocks += 1
        else:
            # Mixed block — filter at rule level
            filtered, bytes_removed = _filter_mobile_rules(block_text, mobile_id_set)
            if bytes_removed > 0:
                changes.append((block_start, block_end, filtered))
                removed_rules_bytes += bytes_removed

    # Apply changes in reverse order
    for start, end, replacement in reversed(changes):
        actual_start = start
        if replacement is None:
            # Full removal — also eat preceding newline
            if actual_start > 0 and head_content[actual_start - 1] == '\n':
                actual_start -= 1
            head_content = head_content[:actual_start] + head_content[end:]
        else:
            head_content = head_content[:start] + replacement + head_content[end:]

    html = head_content + body_content

    total_removed = removed_block_bytes + removed_rules_bytes
    print(f"[Phase 4] Removed {removed_blocks} pure-mobile CSS blocks ({removed_block_bytes:,} bytes)")
    print(f"  + filtered mobile rules from mixed blocks ({removed_rules_bytes:,} bytes)")
    print(f"  Total CSS removed: {total_removed:,} bytes")
    return html


def phase5_add_responsive_css(html):
    """Phase 5: Inject responsive CSS overrides before </style></head>."""

    insert_point = html.find('</style></head>')
    if insert_point == -1:
        print("[Phase 5] Could not find </style></head> insertion point")
        return html

    html = html[:insert_point] + RESPONSIVE_CSS + html[insert_point:]
    print(f"[Phase 5] Added responsive CSS overrides ({len(RESPONSIVE_CSS)} bytes)")
    return html


def phase6_normalize_cta_links(html):
    """Phase 6: Replace any remaining order_page_ URLs with order-page."""

    count_before = html.count('order_page_')
    html = html.replace('1clickonboarding.com/order_page_', '1clickonboarding.com/order-page')
    count_after = html.count('order_page_')

    replaced = count_before - count_after
    print(f"[Phase 6] Normalized {replaced} CTA links (order_page_ → order-page)")
    if count_after > 0:
        print(f"  Note: {count_after} order_page_ references remain (may be in removed content)")

    return html


def verify(html):
    """Verify the merge results."""
    print("\n=== Verification ===")

    # Count sections
    section_count = len(re.findall(r'id="section-[^"]+', html))
    print(f"Section count: {section_count} (target: 14)")

    # Check for mobile-only/desktop-only in body (kept intact, CSS override handles mobile)
    body_start = html.find('<body>')
    if body_start != -1:
        body_html = html[body_start:]
        desktop_in_body = body_html.count('desktop-only')
        mobile_in_body = body_html.count('mobile-only')
        print(f"desktop-only in body: {desktop_in_body} (preserved, CSS override in Phase 5)")
        print(f"mobile-only in body: {mobile_in_body} (preserved)")

    # Check CTA links
    order_page_underscore = html.count('order_page_')
    order_page_dash = html.count('order-page')
    print(f"order_page_ links: {order_page_underscore} (target: 0)")
    print(f"order-page links: {order_page_dash}")

    # Check GHL form
    ghl_form_count = html.count('JfoVUQbTOONUDr9Jraq7')
    print(f"GHL email form iframes: {ghl_form_count}")

    # File size
    size = len(html.encode('utf-8'))
    original = os.path.getsize(BACKUP_PATH)
    reduction = (1 - size / original) * 100
    print(f"\nFile size: {size:,} bytes (was {original:,}, -{reduction:.1f}%)")

    # Check for removed section IDs (should be 0)
    for sid in MOBILE_SECTIONS_TO_REMOVE:
        if f'id="{sid}"' in html:
            print(f"  ERROR: {sid} still present in HTML!")


def main():
    print("=" * 60)
    print("merge_responsive.py — Desktop/Mobile Merge")
    print("=" * 60)

    # Phase 1: Backup
    phase1_backup()

    # Read the file
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    original_size = len(html.encode('utf-8'))

    # Phase 2: Remove mobile sections
    html = phase2_remove_mobile_sections(html)

    # Phase 3: SKIPPED — keeping desktop-only/mobile-only classes intact
    # entry.css uses these for responsive visibility. Instead of stripping,
    # Phase 5 adds a CSS override to show desktop-only elements on mobile.
    print("[Phase 3] Skipped (classes preserved, CSS override in Phase 5)")

    # Phase 4: SKIPPED — dead CSS doesn't affect rendering, only file size.
    # Removing CSS blocks risks breaking :root variable cascade and desktop styling.
    print("[Phase 4] Skipped (dead CSS preserved for layout safety)")

    # Phase 5: Add responsive CSS (includes .desktop-only visibility override)
    html = phase5_add_responsive_css(html)

    # Phase 6: Normalize CTA links
    html = phase6_normalize_cta_links(html)

    # Write output
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(html)

    # Verify
    verify(html)

    print("\n" + "=" * 60)
    print("DONE. Review the site at localhost or deploy to verify visually.")
    print(f"Backup at: {BACKUP_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
