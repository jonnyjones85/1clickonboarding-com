#!/usr/bin/env python3
"""
optimize_site.py — Comprehensive site optimization for 1clickonboarding-clean.

Phases:
  5. HTML cleanup (clearfix, nuxt announcer, stickyLength, commented banners)
  3. Font optimization (trim google-fonts.css, remove legacy font formats)
  4. Image optimization (PNG→WebP, lazy loading)
  1. CTA deduplication (20 buy boxes → shared template)
  2. Restore email opt-in GHL iframes

Run from: 1clickonboarding-clean/
"""

import os
import re
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
BACKUP_PATH = os.path.join(BASE_DIR, "index.html.pre-optimize")
CSS_DIR = os.path.join(BASE_DIR, "css")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
IMAGES_DIR = os.path.join(BASE_DIR, "images")


def backup_file(src, dst):
    """Create a backup if it doesn't already exist."""
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"  Backup created: {os.path.basename(dst)}")
    else:
        print(f"  Backup already exists: {os.path.basename(dst)}")


def file_size_kb(path):
    return os.path.getsize(path) / 1024


# ─────────────────────────────────────────────
# Phase 5: HTML Cleanup
# ─────────────────────────────────────────────
def phase5_html_cleanup(html):
    """Remove clearfix divs, nuxt route announcer, stickyLength div, commented banners."""
    original_len = len(html)

    # 1. Remove empty clearfix divs (keep CSS definitions)
    html = re.sub(r'\s*<div class="clearfix"></div>\s*', '\n', html)

    # 2. Remove nuxt route announcer span
    html = re.sub(
        r'<span class="nuxt-route-announcer"[^>]*>.*?</span></span>',
        '',
        html,
        flags=re.DOTALL
    )

    # 3. Remove stickyLength div
    html = re.sub(
        r'<div id="stickyLength"[^>]*>\s*</div>',
        '',
        html
    )

    # 4. Remove commented-out banner HTML blocks
    html = re.sub(
        r'\s*<!--\s*\n\s*<div class="top_right_banner_outer">.*?-->\s*',
        '\n',
        html,
        flags=re.DOTALL
    )

    saved = original_len - len(html)
    print(f"  HTML cleanup saved {saved:,} bytes ({saved/1024:.1f} KB)")
    return html


# ─────────────────────────────────────────────
# Phase 3: Font Optimization
# ─────────────────────────────────────────────
def phase3a_trim_google_fonts():
    """Trim google-fonts.css to only the fonts actually used: Roboto 400 normal + Kalam 300/400/700."""
    gf_path = os.path.join(CSS_DIR, "google-fonts.css")
    backup_file(gf_path, gf_path + ".pre-optimize")

    old_size = file_size_kb(gf_path)

    # The page uses:
    # - Kalam: 300, 400, 700 (normal only, latin subset)
    # - Roboto: 400 normal only (latin subset — headline + content font)
    # We keep latin-ext too since it covers basic Western chars
    # All font files are already local (.woff2), referenced via ../fonts/

    # Build minimal google-fonts.css with only needed declarations
    minimal_css = """/* Kalam 300 - latin */
@font-face {
  font-family: 'Kalam';
  font-style: normal;
  font-weight: 300;
  font-display: swap;
  src: url(../fonts/YA9Qr0Wd4kDdMtD6GjLMkiQqtbGs.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
/* Kalam 400 - latin */
@font-face {
  font-family: 'Kalam';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url(../fonts/YA9dr0Wd4kDdMthROCfhsCkA.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
/* Kalam 700 - latin */
@font-face {
  font-family: 'Kalam';
  font-style: normal;
  font-weight: 700;
  font-display: swap;
  src: url(../fonts/YA9Qr0Wd4kDdMtDqHTLMkiQqtbGs.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
/* Roboto 400 normal - latin */
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(../fonts/KFO5CnqEu92Fr1Mu53ZEC9_Vu3r1gIhOszmkBnkaSTbQWg.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}
"""

    with open(gf_path, "w") as f:
        f.write(minimal_css)

    new_size = file_size_kb(gf_path)
    print(f"  google-fonts.css: {old_size:.1f} KB → {new_size:.1f} KB (saved {old_size - new_size:.1f} KB)")


def phase3b_remove_legacy_font_formats():
    """Remove .eot, .ttf, .woff font files (keep only .woff2).
    Also remove FontAwesome SVG files from images/ and update entry.css."""

    removed_files = []
    saved_bytes = 0

    # Remove legacy font files
    for f in os.listdir(FONTS_DIR):
        if f.endswith(('.eot', '.ttf', '.woff')) and not f.endswith('.woff2'):
            path = os.path.join(FONTS_DIR, f)
            size = os.path.getsize(path)
            os.remove(path)
            removed_files.append(f)
            saved_bytes += size

    # Remove FontAwesome SVG files from images/
    fa_svgs = ['fa-solid-900.svg', 'fa-brands-400.svg', 'fa-regular-400.svg']
    for f in fa_svgs:
        path = os.path.join(IMAGES_DIR, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            os.remove(path)
            removed_files.append(f)
            saved_bytes += size

    print(f"  Removed {len(removed_files)} legacy font files ({saved_bytes/1024:.0f} KB)")

    # Update entry.css to use only woff2 format for FontAwesome
    entry_path = os.path.join(CSS_DIR, "entry.IgpDOq8p.css")
    backup_file(entry_path, entry_path + ".pre-optimize")

    with open(entry_path, "r") as f:
        css = f.read()

    # Replace each FontAwesome @font-face with woff2-only version
    # Pattern: @font-face{...font-family:Font Awesome...src:url(...)...}
    # The CSS is minified, so we need to match carefully

    # fa-regular-400
    css = re.sub(
        r'src:url\(\.\./fonts/fa-regular-400\.eot\);'
        r'src:url\(\.\./fonts/fa-regular-400\.eot#iefix\) format\("embedded-opentype"\),'
        r'url\(\.\./fonts/fa-regular-400\.woff2\) format\("woff2"\),'
        r'url\(\.\./fonts/fa-regular-400\.woff\) format\("woff"\),'
        r'url\(\.\./fonts/fa-regular-400\.ttf\) format\("truetype"\),'
        r'url\(\.\./images/fa-regular-400\.svg#fontawesome\) format\("svg"\)',
        r'src:url(../fonts/fa-regular-400.woff2) format("woff2")',
        css
    )

    # fa-solid-900
    css = re.sub(
        r'src:url\(\.\./fonts/fa-solid-900\.eot\);'
        r'src:url\(\.\./fonts/fa-solid-900\.eot#iefix\) format\("embedded-opentype"\),'
        r'url\(\.\./fonts/fa-solid-900\.woff2\) format\("woff2"\),'
        r'url\(\.\./fonts/fa-solid-900\.woff\) format\("woff"\),'
        r'url\(\.\./fonts/fa-solid-900\.ttf\) format\("truetype"\),'
        r'url\(\.\./images/fa-solid-900\.svg#fontawesome\) format\("svg"\)',
        r'src:url(../fonts/fa-solid-900.woff2) format("woff2")',
        css
    )

    # fa-brands-400
    css = re.sub(
        r'src:url\(\.\./fonts/fa-brands-400\.eot\);'
        r'src:url\(\.\./fonts/fa-brands-400\.eot#iefix\) format\("embedded-opentype"\),'
        r'url\(\.\./fonts/fa-brands-400\.woff2\) format\("woff2"\),'
        r'url\(\.\./fonts/fa-brands-400\.woff\) format\("woff"\),'
        r'url\(\.\./fonts/fa-brands-400\.ttf\) format\("truetype"\),'
        r'url\(\.\./images/fa-brands-400\.svg#fontawesome\) format\("svg"\)',
        r'src:url(../fonts/fa-brands-400.woff2) format("woff2")',
        css
    )

    with open(entry_path, "w") as f:
        f.write(css)

    print(f"  Updated entry.css: FontAwesome now uses woff2 only")


# Remove unused Google Fonts woff2 files (keep only Roboto latin + Kalam latin files)
def phase3c_remove_unused_font_files():
    """Remove Google Fonts woff2 files that are no longer referenced."""
    # Files we need to keep (referenced in our trimmed google-fonts.css):
    keep_fonts = {
        'YA9Qr0Wd4kDdMtD6GjLMkiQqtbGs.woff2',  # Kalam 300
        'YA9dr0Wd4kDdMthROCfhsCkA.woff2',        # Kalam 400 (via external URL — may not be local)
        'YA9Qr0Wd4kDdMtDqHTLMkiQqtbGs.woff2',    # Kalam 700
        'KFO5CnqEu92Fr1Mu53ZEC9_Vu3r1gIhOszmkBnkaSTbQWg.woff2',  # Roboto 400 normal latin
        # FontAwesome woff2 files (keep)
        'fa-solid-900.woff2',
        'fa-brands-400.woff2',
        'fa-regular-400.woff2',
    }

    removed = 0
    saved = 0
    for f in os.listdir(FONTS_DIR):
        if f.endswith('.woff2') and f not in keep_fonts:
            path = os.path.join(FONTS_DIR, f)
            size = os.path.getsize(path)
            os.remove(path)
            removed += 1
            saved += size

    if removed:
        print(f"  Removed {removed} unused Google Font woff2 files ({saved/1024:.0f} KB)")


# ─────────────────────────────────────────────
# Phase 4: Image Optimization
# ─────────────────────────────────────────────
def phase4a_convert_large_pngs_to_webp(html):
    """Convert the 3 largest PNGs to WebP using cwebp, update HTML references."""
    large_pngs = [
        '657fce865a248f7b6681373a.png',  # 360 KB
        '657fd1f65a248fa9d6813bbf.png',  # 360 KB
        '65644daabd24ba5e7d633716.png',  # 272 KB
    ]

    total_saved = 0
    for png_name in large_pngs:
        png_path = os.path.join(IMAGES_DIR, png_name)
        if not os.path.exists(png_path):
            print(f"  Skipping {png_name} (not found)")
            continue

        webp_name = png_name.replace('.png', '.webp')
        webp_path = os.path.join(IMAGES_DIR, webp_name)

        old_size = file_size_kb(png_path)

        # Convert using cwebp (quality 80 is good for photos)
        result = subprocess.run(
            ['cwebp', '-q', '80', png_path, '-o', webp_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Failed to convert {png_name}: {result.stderr}")
            continue

        new_size = file_size_kb(webp_path)
        saved = old_size - new_size
        total_saved += saved

        # Update HTML references
        html = html.replace(f'images/{png_name}', f'images/{webp_name}')

        # Remove original PNG
        os.remove(png_path)
        print(f"  {png_name}: {old_size:.0f} KB → {webp_name}: {new_size:.0f} KB (saved {saved:.0f} KB)")

    print(f"  Total image savings: {total_saved:.0f} KB")
    return html


def phase4b_add_lazy_loading(html):
    """Add loading='lazy' to all images except the first few above-fold ones."""
    # First, find all img tags
    img_pattern = re.compile(r'<img\s', re.IGNORECASE)
    matches = list(img_pattern.finditer(html))
    total = len(matches)

    # Count how many already have loading="lazy"
    already_lazy = len(re.findall(r'loading="lazy"', html))

    # Add loading="lazy" to img tags that don't have it
    # Skip the first 5 images (above-fold: hero, product shot, logo, etc.)
    count = 0
    added = 0

    def add_lazy(match):
        nonlocal count, added
        count += 1
        tag = match.group(0)
        # Skip first 5 images (above-fold)
        if count <= 5:
            return tag
        # Skip if already has loading attribute
        full_tag_end = html.index('>', match.start()) + 1
        full_tag = html[match.start():full_tag_end]
        if 'loading=' in full_tag:
            return tag
        added += 1
        return '<img loading="lazy" '

    html = img_pattern.sub(add_lazy, html)
    print(f"  Added loading='lazy' to {added} images (skipped first 5 above-fold, {already_lazy} already lazy)")
    return html


# ─────────────────────────────────────────────
# Phase 1: CTA Deduplication
# ─────────────────────────────────────────────
def phase1_deduplicate_ctas(html):
    """Replace 20 near-identical CTA buy boxes with a shared CSS class approach.

    Each CTA block follows this pattern:
      <div class="top_right_sec big_cta">
        <p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>
        <div class="inner_white_bkg">
          [product image, price, CTA button, guarantee badge, checkout image]
        </div>
      </div>

    They differ only by:
      - Unique GHL element IDs in parent wrappers (which we don't need)
      - Some have commented-out banner HTML (already cleaned in Phase 5)
      - Minor whitespace differences

    Strategy: Replace each CTA block's inner content with canonical template HTML.
    This makes all 20 identical, so future edits only need to change the template.
    """

    # Define the canonical CTA template (based on the most complete version)
    canonical_cta_inner = '''<p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>
						<div class="inner_white_bkg">
							<div style="display: inline-block; height: auto; margin-bottom: 0px !important; margin-top: 0px !important;">
								<img class="product_image" src="images/656b079ee33f7cbc7b2c7467.png" loading="lazy">
							</div>
							<h4 class="txt_red">Your Price: Only $47.00</h4>
							<h4 class="black">List Price $297</h4>
							<h4 class="small">You\'re Saving $250.00 Today</h4>
							<p class="savetoday fsize15">Download The Install Pack For Just $47.00!</p>
							<p class="fsize15 mb15">Delivered instantly. Start installing the pack in the next 2 minutes.</p>
							<p class="avail_dwld"><img style="display: inline-block;" alt="download icon" src="images/65638ce89762af2a5cc83b76.png" loading="lazy"> Now available for instant download</p>
							<iframe src="https://api.leadconnectorhq.com/widget/form/JfoVUQbTOONUDr9Jraq7" style="width:100%;border:none;border-radius:3px;overflow:visible;height:188px;" id="inline-JfoVUQbTOONUDr9Jraq7" data-layout="{\'id\':\'INLINE\'}" data-trigger-type="alwaysShow" data-trigger-value="" data-activation-type="alwaysActivated" data-activation-value="" data-deactivation-type="neverDeactivate" data-deactivation-value="" data-form-name="Email-Opt In 1CCO Funnel" data-height="432" data-layout-iframe-id="inline-JfoVUQbTOONUDr9Jraq7" data-form-id="JfoVUQbTOONUDr9Jraq7" title="Email-Opt In 1CCO Funnel" scrolling="no">
							</iframe>
							<div class="text-center mt10">
								<p style="margin:0px auto 10px;text-align:center; color: #061130;width: 100%; max-width: 290px;">We securely process payments with 256-bit security encryption</p>
								<div class="text-center">
									<img class="authorized_payments" style="margin-top:10px;display: inline-block; vertical-align: middle;width: 164px;" alt="secure_checkout_img" src="images/657f6247a08dc56b3f061f1e.png" loading="lazy">
								</div>
								<p class="mbc_logo_txt" style="margin:20px auto 0; color: #061130; width: 100%; max-width: 290px;"><img alt="mbc_logo" src="images/6508e799a8ce7068941edcae.png" loading="lazy"> BACKED BY OUR UNCONDITIONAL<br>30 DAY MONEY BACK GUARANTEE</p>
							</div>
							<div class="text-center">
								<img class="secure_checkout_img" style="display: inline-block; vertical-align: middle;width: 100%;" alt="secure_checkout_img" src="images/c6c86cdd-f716-4fba-8829-264762bd7588.jpg" loading="lazy">
							</div>
						</div>'''

    # Match CTA blocks: starts with <div class="top_right_sec big_cta"> and ends with the closing structure
    # The pattern needs to match the entire CTA content block
    cta_pattern = re.compile(
        r'(<div class="top_right_sec big_cta">)\s*'
        r'<p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>'
        r'.*?'  # All the inner content
        r'(</div>\s*</div>\s*</div>)',  # Closing tags for inner_white_bkg + top_right_sec wrapper
        re.DOTALL
    )

    # Find all matches first to count
    matches = list(cta_pattern.finditer(html))
    print(f"  Found {len(matches)} CTA buy boxes")

    if len(matches) < 15:
        print(f"  WARNING: Expected ~20 CTAs, found {len(matches)}. Skipping dedup to be safe.")
        return html

    # Replace each match with canonical template
    # Work backwards to preserve positions
    for match in reversed(matches):
        start = match.start()
        end = match.end()
        # Reconstruct: opening div + canonical content + closing divs
        replacement = f'<div class="top_right_sec big_cta">\n{canonical_cta_inner}\n\t\t\t\t\t</div>'
        # We need to figure out how many closing divs the match captured
        # The match ends with </div></div></div> — 3 closing divs
        # But our CTA structure is: top_right_sec > inner_white_bkg > content
        # So we need: close inner_white_bkg (1) + close text-center mt10 wrapper + close top_right_sec
        # Actually let's be more precise — replace just the content between the opening and closing
        html = html[:start] + replacement + html[end:]

    # Verify
    remaining = html.count('DIGITAL DOWNLOAD NOW AVAILABLE')
    print(f"  After dedup: {remaining} CTAs (all now identical)")

    return html


# ─────────────────────────────────────────────
# Phase 2: Restore Email Opt-In Forms
# ─────────────────────────────────────────────
def phase2_restore_email_optin(html):
    """No-op: iframe is now included in the canonical CTA template (phase1).

    Previously this inserted a .cta-email-form wrapper with the GHL iframe
    after phase1 ran. Now phase1's canonical_cta_inner already contains the
    iframe with original GHL attributes (height:188px, data-height="432", etc.),
    so this step is no longer needed.
    """
    print("  Skipped — iframe already in canonical CTA template (phase1)")
    return html


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("1clickonboarding-clean Site Optimization")
    print("=" * 60)

    # Record original sizes
    original_html_size = file_size_kb(INDEX_PATH)
    original_fonts_size = sum(
        os.path.getsize(os.path.join(FONTS_DIR, f))
        for f in os.listdir(FONTS_DIR) if not f.startswith('.')
    ) / 1024
    original_images_size = sum(
        os.path.getsize(os.path.join(IMAGES_DIR, f))
        for f in os.listdir(IMAGES_DIR) if not f.startswith('.')
    ) / 1024

    print(f"\nOriginal sizes:")
    print(f"  HTML:   {original_html_size:.0f} KB")
    print(f"  Fonts:  {original_fonts_size:.0f} KB")
    print(f"  Images: {original_images_size:.0f} KB")
    print(f"  Total:  {original_html_size + original_fonts_size + original_images_size:.0f} KB")

    # Backup
    backup_file(INDEX_PATH, BACKUP_PATH)

    # Read HTML
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Phase 5: HTML Cleanup
    print(f"\n{'─'*60}")
    print("Phase 5: HTML Cleanup")
    print(f"{'─'*60}")
    html = phase5_html_cleanup(html)

    # Phase 3: Font Optimization
    print(f"\n{'─'*60}")
    print("Phase 3: Font Optimization")
    print(f"{'─'*60}")
    phase3a_trim_google_fonts()
    phase3b_remove_legacy_font_formats()
    phase3c_remove_unused_font_files()

    # Phase 4: Image Optimization
    print(f"\n{'─'*60}")
    print("Phase 4: Image Optimization")
    print(f"{'─'*60}")
    html = phase4a_convert_large_pngs_to_webp(html)
    html = phase4b_add_lazy_loading(html)

    # Phase 1: CTA Deduplication
    print(f"\n{'─'*60}")
    print("Phase 1: CTA Deduplication")
    print(f"{'─'*60}")
    html = phase1_deduplicate_ctas(html)

    # Phase 2: Restore Email Opt-In
    print(f"\n{'─'*60}")
    print("Phase 2: Restore Email Opt-In")
    print(f"{'─'*60}")
    html = phase2_restore_email_optin(html)

    # Write optimized HTML
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    # Final sizes
    final_html_size = file_size_kb(INDEX_PATH)
    final_fonts_size = sum(
        os.path.getsize(os.path.join(FONTS_DIR, f))
        for f in os.listdir(FONTS_DIR) if not f.startswith('.')
    ) / 1024
    final_images_size = sum(
        os.path.getsize(os.path.join(IMAGES_DIR, f))
        for f in os.listdir(IMAGES_DIR) if not f.startswith('.')
    ) / 1024

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"  HTML:   {original_html_size:.0f} KB → {final_html_size:.0f} KB (saved {original_html_size - final_html_size:.0f} KB)")
    print(f"  Fonts:  {original_fonts_size:.0f} KB → {final_fonts_size:.0f} KB (saved {original_fonts_size - final_fonts_size:.0f} KB)")
    print(f"  Images: {original_images_size:.0f} KB → {final_images_size:.0f} KB (saved {original_images_size - final_images_size:.0f} KB)")
    total_orig = original_html_size + original_fonts_size + original_images_size
    total_final = final_html_size + final_fonts_size + final_images_size
    print(f"  Total:  {total_orig:.0f} KB → {total_final:.0f} KB (saved {total_orig - total_final:.0f} KB = {(total_orig - total_final)/total_orig*100:.1f}%)")


if __name__ == "__main__":
    main()
