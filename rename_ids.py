#!/usr/bin/env python3
"""
Phase 1: Rename structural GHL IDs to semantic names.

Renames ~100 structural IDs (14 sections + 32 rows + 54 columns) from random
GHL-generated strings to human-readable semantic names. Leaf-level IDs
(headings, paragraphs, images, buttons) are left untouched.

For each ID, replaces all 4 occurrence patterns:
  - HTML attribute: id="section-OLD"
  - CSS ID selector: #section-OLD
  - CSS class selector: .section-OLD
  - CSS bg class: .bg-section-OLD

Creates backup before writing and outputs id_map.json for reference.
"""

import json
import os
import re
import shutil
from datetime import datetime

HTML_PATH = os.path.join(os.path.dirname(__file__), "index.html")

# =============================================================================
# ID MAPPING: old GHL ID → new semantic name
# =============================================================================

SECTION_MAP = {
    # Section 1: Top navigation bar (help/contact + logo)
    "section-qV2_UC8cuJ":  "section-top-bar",
    # Section 2: Hero — headline, video, main CTA box
    "section-Y44Z2WH865":  "section-hero",
    # Section 3: Value proposition — "ultimate shortcut" + how it works
    "section-6SUAQ42AZ7":  "section-value-prop",
    # Section 4: Sales letter — Katie's story + case studies
    "section-51HYL80S4E":  "section-sales-letter",
    # Section 5: What you get — $47 breakdown + install CTA
    "section-561M4VJ0Q0":  "section-what-you-get",
    # Section 6: Alex Hormozi quote
    "section-FUumsrh8V6":  "section-hormozi-quote",
    # Section 7: Sticky sidebar CTA bar
    "section-CDQ2SBB9N7":  "section-sticky-sidebar",
    # Section 8: Sneak peek inside the product
    "section-IIMKLUNCA4":  "section-sneak-peek",
    # Section 9: Additional features (onboarding form, CRM, etc.)
    "section-A3U1E0VEK3":  "section-also-getting",
    # Section 10: 7 bonus items ($3929 value)
    "section-8Q4F1SUW66":  "section-bonuses",
    # Section 11: FAQ
    "section-LMKIGKCNJC":  "section-faq",
    # Section 12: Money-back guarantee
    "section-9UjOKfxdKL":  "section-guarantee",
    # Section 13: Visual divider between guarantee and footer
    "section-IOEG4LUEAX":  "section-divider",
    # Section 14: Footer — copyright + final CTA
    "section-VH3FYUTL6N":  "section-footer",
}

ROW_MAP = {
    # --- section-top-bar ---
    "row-yC5ItBRw00":  "row-topbar-main",

    # --- section-hero ---
    "row-P4NKRR2R2T":  "row-hero-headline",
    "row-CBVN4XZ7A8":  "row-hero-content",

    # --- section-value-prop ---
    "row-R2YZSZCH6G":  "row-vp-two-col",
    "row-AqKLpkBU9z":  "row-vp-body",

    # --- section-sales-letter ---
    "row-Vg7u0DQ9Ei":  "row-letter-intro",
    "row-SSHCD4XFHF":  "row-letter-main",

    # --- section-what-you-get ---
    "row-J1DBS7P7RM":  "row-wyg-headline",
    "row-2wLlCAW356":  "row-wyg-product-1",
    "row-VXMg8i0I8l":  "row-wyg-product-2",
    "row-iOn21cYK2j":  "row-wyg-product-3",
    "row-RVuv1eCx52":  "row-wyg-product-4",
    "row-LAC9EAXH09":  "row-wyg-cta",

    # --- section-hormozi-quote ---
    "row-Dn_JXSHHRE":  "row-quote-main",

    # --- section-sticky-sidebar ---
    "row-NRC9YYOQEF":  "row-sticky-main",

    # --- section-sneak-peek ---
    "row-7FZ6XKZQHV":  "row-peek-main",

    # --- section-also-getting ---
    "row-FN4SUQ8LKJ":  "row-also-headline",
    "row-HQ8JR3C10P":  "row-also-features",
    "row-2CKWYN2ZPO":  "row-also-cta",

    # --- section-bonuses ---
    "row-GFBR7CJK1M":  "row-bonuses-headline",
    "row-Q5WBX2I4H8":  "row-bonus-1",
    "row-GsEZeIxWVE":  "row-bonus-2",
    "row-WzeQFEz0G3":  "row-bonus-3",
    "row-HjscSlIxP9":  "row-bonus-4",
    "row-H7RUW2GR98":  "row-bonus-5-6",
    "row-d4hennPZDy":  "row-bonus-7",

    # --- section-faq ---
    "row-UFFNZ9J6R3":  "row-faq-headline",
    "row-sg-naKtU9j":  "row-faq-items",

    # --- section-guarantee ---
    "row-0si9fSlsdD":  "row-guarantee-main",

    # --- section-divider ---
    "row-GXXCYXY3LN":  "row-divider-main",

    # --- section-footer ---
    "row-rYsbHTx2-XU":  "row-footer-cta",
    "row-lByUkbZ6ikv":  "row-footer-legal",
}

COL_MAP = {
    # --- section-top-bar ---
    "col-ffamN81DtU":  "col-topbar-help-text",
    "col-daf3pRQXk2":  "col-topbar-logo",
    "col-v-nmvAAbMf":  "col-topbar-spacer",

    # --- section-hero ---
    "col-ZATJ6EDP2Q":  "col-hero-headline",
    "col-TJRQHE290L":  "col-hero-video",
    "col-EDGB6PRHYY":  "col-hero-cta-box",

    # --- section-value-prop ---
    "col-DEF929UAPF":  "col-vp-content-left",
    "col-WFFPKR4Y96":  "col-vp-sidebar-right",
    "col-Y0MOGnG6vg":  "col-vp-mobile-placeholder",
    "col-LKA7lEMgSC":  "col-vp-body-full",

    # --- section-sales-letter ---
    "col-fkUT0gXxkT":  "col-letter-intro",
    "col-VOX0NNA4P7":  "col-letter-main",
    "col-8A1V8YCH9N":  "col-letter-sidebar",

    # --- section-what-you-get ---
    "col-KQMY3E81Q3":  "col-wyg-headline",
    "col-9CdrOWhLhj":  "col-wyg-prod1-left",
    "col-_ntxnRd4Ac":  "col-wyg-prod1-right",
    "col-A2cvSfrhL_":  "col-wyg-prod2-left",
    "col-hp4YHx57ci":  "col-wyg-prod2-right",
    "col-XTej-wzHVA":  "col-wyg-prod3-left",
    "col-mJvt03nue6":  "col-wyg-prod3-right",
    "col-8e-V4wM_0d":  "col-wyg-prod4-left",
    "col-OM4Xt2FbSC":  "col-wyg-prod4-right",
    "col-S5P1RDGMBI":  "col-wyg-cta",

    # --- section-hormozi-quote ---
    "col-bToQ1bvk3Q":  "col-quote-main",

    # --- section-sticky-sidebar ---
    "col-GRDOWR503X":  "col-sticky-left",
    "col-ZZ7NPNTS94":  "col-sticky-center",
    "col-2PWWW0UB0B":  "col-sticky-right",

    # --- section-sneak-peek ---
    "col-R2SJPUXA3J":  "col-peek-main",

    # --- section-also-getting ---
    "col-E0L70SD2FM":  "col-also-headline",
    "col-GP1XRB35OW":  "col-also-feat-left",
    "col-7V5RBHXAAZ":  "col-also-feat-right",
    "col-1S7PWCMTZJ":  "col-also-cta-left",
    "col-FEH7MNWUN2":  "col-also-cta-right",

    # --- section-bonuses ---
    "col-8DF6QJMYSA":  "col-bonuses-headline",
    "col-H3J852SB9U":  "col-bonus1-left",
    "col-HT9YTCNOGV":  "col-bonus1-right",
    "col-7CgJ78et10":  "col-bonus2-left",
    "col-qt6CYL-69j":  "col-bonus2-right",
    "col-f9Q7CY4jVD":  "col-bonus3-left",
    "col-TdsnMVVZw-":  "col-bonus3-right",
    "col-1PEpCai4bi":  "col-bonus4-left",
    "col-1dGnX-uPVX":  "col-bonus4-right",
    "col-FZXHWZ1UBU":  "col-bonus56-main",
    "col-Ti5TZUJHU2":  "col-bonus7-main",

    # --- section-faq ---
    "col-A4FAASQ708":  "col-faq-headline",
    "col-K9XDv0mOIb":  "col-faq-items",
    "col-A44MPNTKza":  "col-faq-cta",

    # --- section-guarantee ---
    "col-weWKAimxS_":  "col-guarantee-main",

    # --- section-divider ---
    "col-TIDZUE9XBP":  "col-divider-main",

    # --- section-footer ---
    "col-92gXuDHR0zN":  "col-footer-cta-left",
    "col-3wsNkCrd2Ah":  "col-footer-cta-right",
    "col-ARnPqPYRL9d":  "col-footer-copyright",
    "col-Kcq9nAviRsW":  "col-footer-links-left",
    "col-__kop0A63Sx":  "col-footer-links-right",
}


def rename_ids(html_path=HTML_PATH):
    """Perform the ID rename across the entire file."""
    # Read original
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_size = len(content)

    # Create backup
    backup_path = html_path + ".pre-rename"
    shutil.copy2(html_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Combine all maps
    all_maps = {}
    all_maps.update(SECTION_MAP)
    all_maps.update(ROW_MAP)
    all_maps.update(COL_MAP)

    total_replacements = 0

    # Simple global string replace — these GHL IDs are unique enough
    # that a plain replace catches all contexts:
    #   id="section-OLD", #section-OLD, .section-OLD, .bg-section-OLD,
    #   and class="... section-OLD ..."
    for old_id, new_id in all_maps.items():
        count = content.count(old_id)
        content = content.replace(old_id, new_id)

        if count > 0:
            print(f"  {old_id} → {new_id}  ({count} replacements)")
        else:
            print(f"  {old_id} → {new_id}  (WARNING: 0 replacements — check ID)")

        total_replacements += count

    # Write modified file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_size = len(content)

    # Output the mapping as JSON for reference
    map_path = os.path.join(os.path.dirname(html_path), "id_map.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "total_ids_renamed": len(all_maps),
            "total_replacements": total_replacements,
            "sections": SECTION_MAP,
            "rows": ROW_MAP,
            "columns": COL_MAP,
        }, f, indent=2)

    print(f"\nDone!")
    print(f"  IDs renamed: {len(all_maps)}")
    print(f"  Total replacements: {total_replacements}")
    print(f"  File size: {original_size:,} → {new_size:,} bytes ({new_size - original_size:+,})")
    print(f"  Backup: {backup_path}")
    print(f"  Map: {map_path}")


if __name__ == "__main__":
    rename_ids()
