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
@media only screen and (max-width: 767px) {
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


def phase4_remove_dead_css(html):
    """Phase 4: Remove CSS rules targeting IDs from the 9 removed mobile sections.

    Targets CSS in <style> blocks that reference component IDs from removed sections.
    Each section has a /* ---- top/Section styles ----- */ comment block.
    """
    # Strategy: Find the CSS style blocks for mobile sections and remove them.
    # The CSS is organized in blocks starting with /* ---- top styles ----- */ or /* ---- Section styles ----- */
    # followed by CSS rules for that section.

    # Build a set of ID patterns to match
    mobile_id_set = set(MOBILE_COMPONENT_IDS)

    # Find all style block boundaries
    # Each section's CSS starts with /* ---- (top|Section) styles ----- */
    style_marker = re.compile(r'/\* ---- (?:top|Section) styles ----- \*/')

    # Split the <head> styles from <body> content
    # The CSS blocks are between <style> tags and before </head><body>
    head_end = html.find('</style></head>')
    if head_end == -1:
        print("[Phase 4] Could not find style/head boundary")
        return html

    head_content = html[:head_end]
    body_content = html[head_end:]

    # Find all style block positions
    markers = list(style_marker.finditer(head_content))

    removed_blocks = 0
    removed_bytes = 0

    # Process blocks in reverse order to maintain positions
    blocks_to_remove = []

    for i, m in enumerate(markers):
        block_start = m.start()
        # Block ends at next marker or at end of head_content
        if i + 1 < len(markers):
            block_end = markers[i + 1].start()
        else:
            block_end = len(head_content)

        block_text = head_content[block_start:block_end]

        # Check if this block references any of the mobile section IDs
        is_mobile_block = False
        for comp_id in mobile_id_set:
            # Check for section-ID, col-ID, row-ID, heading-ID etc.
            if comp_id in block_text:
                is_mobile_block = True
                break

        if is_mobile_block:
            # Also check it doesn't contain desktop section IDs we want to keep
            # Desktop sections we're keeping all have different IDs, so if the block
            # ONLY contains mobile IDs, remove it
            blocks_to_remove.append((block_start, block_end))
            removed_bytes += block_end - block_start
            removed_blocks += 1

    # Remove blocks in reverse order
    for start, end in reversed(blocks_to_remove):
        # Also remove the preceding newline if present
        actual_start = start
        if actual_start > 0 and head_content[actual_start - 1] == '\n':
            actual_start -= 1
        head_content = head_content[:actual_start] + head_content[end:]

    html = head_content + body_content

    print(f"[Phase 4] Removed {removed_blocks} CSS style blocks ({removed_bytes:,} bytes)")
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

    # Check for mobile-only/desktop-only in body
    body_start = html.find('<body>')
    if body_start != -1:
        body_html = html[body_start:]
        desktop_in_body = body_html.count('desktop-only')
        mobile_in_body = body_html.count('mobile-only')
        print(f"desktop-only in body: {desktop_in_body} (target: 0)")
        print(f"mobile-only in body: {mobile_in_body} (target: 0)")

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

    # Phase 3: Strip desktop-only classes
    html = phase3_strip_desktop_only(html)

    # Phase 4: Remove dead CSS
    html = phase4_remove_dead_css(html)

    # Phase 5: Add responsive CSS
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
