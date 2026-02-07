#!/usr/bin/env python3
"""
Extract webarchive HTML, clean GHL bloat, copy static assets.
Creates a deployable static site from the 1clickonboarding.com webarchive.

Usage:
    python extract_and_clean.py

Reads from:
    ../1 Click Onboarding Install Pack.webarchive  (Safari webarchive)
    ../1clickonboarding-com/                       (static site scrape)

Writes to:
    ./index.html      (cleaned HTML)
    ./css/             (stylesheets)
    ./fonts/           (font files)
    ./images/          (base images from static scrape)
    ./assets/          (SVGs/resources from webarchive)
"""

import os
import re
import shutil
import plistlib
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
WEBARCHIVE_PATH = SCRIPT_DIR.parent / "1 Click Onboarding Install Pack.webarchive"
STATIC_SCRAPE_DIR = SCRIPT_DIR.parent / "1clickonboarding-com"
OUTPUT_DIR = SCRIPT_DIR

# Output subdirectories
CSS_DIR = OUTPUT_DIR / "css"
FONTS_DIR = OUTPUT_DIR / "fonts"
IMAGES_DIR = OUTPUT_DIR / "images"
ASSETS_DIR = OUTPUT_DIR / "assets"


def extract_webarchive():
    """Parse webarchive and return main HTML + subresources."""
    print(f"Reading webarchive: {WEBARCHIVE_PATH}")
    with open(WEBARCHIVE_PATH, "rb") as f:
        data = plistlib.load(f)

    html_bytes = data["WebMainResource"]["WebResourceData"]
    html = html_bytes.decode("utf-8", errors="replace")
    print(f"  Main HTML: {len(html):,} chars")

    subresources = data.get("WebSubresources", [])
    print(f"  Subresources: {len(subresources)}")

    return html, subresources


def save_webarchive_assets(subresources):
    """Save useful assets from webarchive (SVGs, images not in static scrape)."""
    ASSETS_DIR.mkdir(exist_ok=True)
    saved = {}

    for sub in subresources:
        url = sub.get("WebResourceURL", "")
        mime = sub.get("WebResourceMIMEType", "")
        data = sub.get("WebResourceData", b"")

        # Skip scripts, tracking, forms
        if any(skip in url for skip in [
            "clarity.ms", "googletagmanager", "facebook.net",
            "cloudflareinsights", "leadconnectorhq.com/_preview/BnKGewzO",
            "leadconnectorhq.com/v1/lst", "cdn-cgi/scripts",
        ]):
            continue

        # Save SVGs from Google Cloud Storage
        if "storage.googleapis.com" in url and "svg" in mime:
            filename = url.split("/")[-1]
            # Clean up the .svg+xml extension
            if filename.endswith(".svg+xml"):
                filename = filename.replace(".svg+xml", ".svg")
            filepath = ASSETS_DIR / filename
            with open(filepath, "wb") as f:
                f.write(data)
            saved[url] = f"assets/{filename}"
            print(f"  Saved SVG: {filename} ({len(data):,} bytes)")

        # Save images from storage.googleapis.com not in static scrape
        elif "storage.googleapis.com" in url and mime.startswith("image/"):
            filename = url.split("/")[-1]
            # Check if it exists in static scrape images
            if not (STATIC_SCRAPE_DIR / "images" / filename).exists():
                filepath = ASSETS_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(data)
                saved[url] = f"assets/{filename}"
                print(f"  Saved image: {filename} ({len(data):,} bytes)")

        # Save images from assets.cdn.filesafe.space
        elif "assets.cdn.filesafe.space" in url and mime.startswith("image/"):
            filename = url.split("/")[-1]
            if not (STATIC_SCRAPE_DIR / "images" / filename).exists():
                filepath = ASSETS_DIR / filename
                with open(filepath, "wb") as f:
                    f.write(data)
                saved[url] = f"assets/{filename}"
                print(f"  Saved filesafe image: {filename} ({len(data):,} bytes)")

        # Save Vimeo thumbnails
        elif "i.vimeocdn.com" in url and mime.startswith("image/"):
            filename = url.split("/")[-1]
            filepath = ASSETS_DIR / filename
            with open(filepath, "wb") as f:
                f.write(data)
            saved[url] = f"assets/{filename}"
            print(f"  Saved Vimeo thumb: {filename} ({len(data):,} bytes)")

        # Save the Video CSS
        elif "Video.s2mmLl8o.css" in url:
            CSS_DIR.mkdir(exist_ok=True)
            filepath = CSS_DIR / "Video.s2mmLl8o.css"
            with open(filepath, "wb") as f:
                f.write(data)
            saved[url] = "css/Video.s2mmLl8o.css"
            print(f"  Saved Video CSS ({len(data):,} bytes)")

        # Save Google Fonts CSS
        elif "fonts.googleapis.com" in url and mime == "text/css":
            filepath = CSS_DIR / "google-fonts.css"
            with open(filepath, "wb") as f:
                f.write(data)
            saved[url] = "css/google-fonts.css"
            print(f"  Saved Google Fonts CSS ({len(data):,} bytes)")

        # Save Google font files (woff2)
        elif "fonts.gstatic.com" in url and mime.startswith("font/"):
            filename = url.split("/")[-1]
            FONTS_DIR.mkdir(exist_ok=True)
            filepath = FONTS_DIR / filename
            with open(filepath, "wb") as f:
                f.write(data)
            saved[url] = f"fonts/{filename}"
            print(f"  Saved Google font: {filename} ({len(data):,} bytes)")

    return saved


def copy_static_assets():
    """Copy CSS, fonts, and base images from the static scrape."""
    # CSS
    CSS_DIR.mkdir(exist_ok=True)
    src_css = STATIC_SCRAPE_DIR / "css" / "entry.IgpDOq8p.css"
    if src_css.exists():
        shutil.copy2(src_css, CSS_DIR / "entry.IgpDOq8p.css")
        print(f"  Copied CSS: entry.IgpDOq8p.css")

    # FontAwesome fonts from static scrape
    FONTS_DIR.mkdir(exist_ok=True)
    src_fonts = STATIC_SCRAPE_DIR / "fonts"
    if src_fonts.exists():
        for f in src_fonts.iterdir():
            shutil.copy2(f, FONTS_DIR / f.name)
        print(f"  Copied {len(list(src_fonts.iterdir()))} FontAwesome font files")

    # Base images only (no _1, _2, etc. variants which are srcset duplicates)
    IMAGES_DIR.mkdir(exist_ok=True)
    src_images = STATIC_SCRAPE_DIR / "images"
    copied = 0
    if src_images.exists():
        for f in sorted(src_images.iterdir()):
            # Skip responsive variants (_1.png, _2.png, etc.)
            if re.match(r".*_\d+\.\w+$", f.name):
                continue
            shutil.copy2(f, IMAGES_DIR / f.name)
            copied += 1
    print(f"  Copied {copied} base images (skipped responsive variants)")


def clean_html(html, asset_map):
    """Remove GHL bloat, rewrite URLs to local paths."""

    # 1. Remove all <script> tags (GHL runtime, tracking, analytics, NUXT)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)

    # 2. Remove ALL <link as="script"> preload hints (GHL JS modules)
    html = re.sub(r'<link\s[^>]*as="script"[^>]*/?\s*>', "", html)

    # 3. Remove GTM noscript block and its containing div
    html = re.sub(
        r'<div id="gb-track-hl-custom-code">.*?</div>',
        "",
        html,
        flags=re.DOTALL,
    )

    # 4. Remove hidden GTM iframe
    html = re.sub(
        r'<iframe\s+height="0"\s+width="0"\s+style="display:\s*none;\s*visibility:\s*hidden;"[^>]*></iframe>',
        "",
        html,
    )

    # 5. Remove GHL form iframes (lead capture forms) — may not be self-closing
    html = re.sub(
        r'<iframe\s+src="https://api\.leadconnectorhq\.com/widget/form/[^"]*"[^>]*>.*?</iframe>',
        "",
        html,
        flags=re.DOTALL,
    )

    # 6. Remove Nuxt comment markers <!--[--> and <!--]--> and <!---->
    html = re.sub(r"<!--\[-->", "", html)
    html = re.sub(r"<!--\]-->", "", html)
    html = re.sub(r"<!---->", "", html)

    # 7. Remove <div id="teleports"></div>
    html = re.sub(r'<div id="teleports"></div>', "", html)

    # 8. Remove data-nuxt attributes
    html = re.sub(r'\s+data-nuxt-[a-z-]*="[^"]*"', "", html)

    # 9. Remove data-v- (Vue scoped style) attributes - keep for CSS matching
    # Actually keep these - the CSS selectors may depend on them

    # 10. Rewrite CSS URLs
    # entry.IgpDOq8p.css -> local
    html = html.replace(
        "https://stcdn.leadconnectorhq.com/_preview/entry.IgpDOq8p.css",
        "css/entry.IgpDOq8p.css",
    )
    # Video CSS -> local
    html = html.replace(
        "https://stcdn.leadconnectorhq.com/_preview/Video.s2mmLl8o.css",
        "css/Video.s2mmLl8o.css",
    )

    # 11. Rewrite Google Fonts CSS URL to local
    # Match the fonts.googleapis.com CSS link (there are multiple, replace all)
    html = re.sub(
        r'href="https://fonts\.googleapis\.com/css\?family=[^"]*"',
        'href="css/google-fonts.css"',
        html,
    )

    # 12. Rewrite font URLs in the Google Fonts CSS is handled below in fix_google_fonts_css

    # 13. Rewrite storage.googleapis.com image/SVG URLs to local
    def rewrite_storage_url(match):
        url = match.group(0)
        filename = url.split("/")[-1]
        # SVG files
        if filename.endswith(".svg+xml"):
            clean_name = filename.replace(".svg+xml", ".svg")
            return f"assets/{clean_name}"
        # Check if in static images
        if (IMAGES_DIR / filename).exists() or (STATIC_SCRAPE_DIR / "images" / filename).exists():
            return f"images/{filename}"
        # Check if in assets
        if (ASSETS_DIR / filename).exists():
            return f"assets/{filename}"
        return url  # Keep original if not found locally

    html = re.sub(
        r"https://storage\.googleapis\.com/msgsndr/[a-zA-Z0-9]+/media/[a-zA-Z0-9._+-]+",
        rewrite_storage_url,
        html,
    )

    # 14. Rewrite assets.cdn.filesafe.space URLs to local
    def rewrite_filesafe_url(match):
        url = match.group(0)
        filename = url.split("/")[-1]
        if (IMAGES_DIR / filename).exists() or (STATIC_SCRAPE_DIR / "images" / filename).exists():
            return f"images/{filename}"
        if (ASSETS_DIR / filename).exists():
            return f"assets/{filename}"
        return url

    html = re.sub(
        r"https://assets\.cdn\.filesafe\.space/[a-zA-Z0-9]+/media/[a-zA-Z0-9._-]+",
        rewrite_filesafe_url,
        html,
    )

    # 15. Rewrite images.leadconnectorhq.com CDN proxy URLs to direct local paths
    # After steps 13-14, inner URLs may already be rewritten to images/FILENAME or assets/FILENAME
    # Pattern now: https://images.leadconnectorhq.com/image/f_webp/q_80/r_XXXX/u_images/FILENAME.ext
    # Or original: https://images.leadconnectorhq.com/image/f_webp/q_80/r_XXXX/u_https://assets.cdn.filesafe.space/.../FILENAME.ext
    def rewrite_cdn_proxy_url(match):
        full_url = match.group(0)
        # Try already-rewritten pattern: /u_images/FILENAME or /u_assets/FILENAME
        local_match = re.search(r"/u_((?:images|assets)/[a-zA-Z0-9._-]+)", full_url)
        if local_match:
            return local_match.group(1)
        # Try original pattern with media/FILENAME
        inner_match = re.search(r"media/([a-zA-Z0-9._-]+)", full_url)
        if inner_match:
            filename = inner_match.group(1)
            if (IMAGES_DIR / filename).exists() or (STATIC_SCRAPE_DIR / "images" / filename).exists():
                return f"images/{filename}"
            if (ASSETS_DIR / filename).exists():
                return f"assets/{filename}"
        return full_url

    html = re.sub(
        r"https://images\.leadconnectorhq\.com/image/f_webp/q_80/r_\d+/u_[^\s\"')]+",
        rewrite_cdn_proxy_url,
        html,
    )

    # 16. Rewrite Vimeo thumbnail URLs to local
    def rewrite_vimeo_url(match):
        url = match.group(0)
        filename = url.split("/")[-1]
        if (ASSETS_DIR / filename).exists():
            return f"assets/{filename}"
        return url

    html = re.sub(
        r"https://i\.vimeocdn\.com/video/[a-zA-Z0-9_-]+-[a-zA-Z0-9]+-d_\d+\.[a-z]+",
        rewrite_vimeo_url,
        html,
    )

    # 17. Rewrite favicon
    html = re.sub(
        r'href="https://storage\.googleapis\.com/msgsndr/[^"]*?65302924325af3028f886576\.png"',
        'href="images/65302924325af3028f886576.png"',
        html,
    )

    # 18. Remove the preload link for Google Fonts (already loaded via stylesheet)
    html = re.sub(
        r'<link\s+rel="preload"\s+as="style"\s+href="css/google-fonts\.css"[^>]*/?>',
        "",
        html,
    )

    # 19. Remove duplicate Google Fonts stylesheet links (keep only the first)
    font_link = '<link rel="stylesheet" href="css/google-fonts.css"'
    first_idx = html.find(font_link)
    if first_idx >= 0:
        # Find and remove any subsequent occurrences
        search_from = first_idx + len(font_link)
        while True:
            next_idx = html.find(font_link, search_from)
            if next_idx < 0:
                break
            # Find the end of this tag
            end_idx = html.find(">", next_idx) + 1
            html = html[:next_idx] + html[end_idx:]

    # 20. Remove Google Fonts preconnect (fonts are local now)
    html = re.sub(
        r'<link\s+rel="preconnect"\s+href="https://fonts\.gstatic\.com/"[^>]*/?>',
        "",
        html,
    )

    # 21. Clean up excessive whitespace / empty lines
    html = re.sub(r"\n{3,}", "\n\n", html)

    return html


def fix_google_fonts_css(asset_map):
    """Rewrite font URLs in the Google Fonts CSS to point to local files."""
    css_path = CSS_DIR / "google-fonts.css"
    if not css_path.exists():
        return

    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        css = f.read()

    # Rewrite font URLs to local paths
    def rewrite_font_url(match):
        url = match.group(1)
        filename = url.split("/")[-1]
        if (FONTS_DIR / filename).exists():
            return f"url(../fonts/{filename})"
        return match.group(0)

    css = re.sub(
        r"url\((https://fonts\.gstatic\.com/[^)]+)\)",
        rewrite_font_url,
        css,
    )

    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)
    print("  Rewrote font URLs in google-fonts.css")


def fix_entry_css():
    """Rewrite font URLs in entry.IgpDOq8p.css to local paths."""
    css_path = CSS_DIR / "entry.IgpDOq8p.css"
    if not css_path.exists():
        return

    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        css = f.read()

    # Rewrite FontAwesome font URLs from /funnel/fontawesome/webfonts/ to ../fonts/
    css = re.sub(
        r"url\(['\"]?/funnel/fontawesome/webfonts/([^)\"']+)['\"]?\)",
        r"url(../fonts/\1)",
        css,
    )

    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)
    print("  Rewrote FontAwesome URLs in entry.IgpDOq8p.css")


def main():
    print("=" * 60)
    print("1clickonboarding.com - Extract & Clean")
    print("=" * 60)

    # Step 1: Extract webarchive
    print("\n[1/5] Extracting webarchive...")
    html, subresources = extract_webarchive()

    # Step 2: Copy static assets
    print("\n[2/5] Copying static assets...")
    copy_static_assets()

    # Step 3: Save webarchive assets
    print("\n[3/5] Saving webarchive assets...")
    asset_map = save_webarchive_assets(subresources)

    # Step 4: Clean HTML
    print("\n[4/5] Cleaning HTML...")
    html = clean_html(html, asset_map)

    # Write cleaned HTML
    output_html = OUTPUT_DIR / "index.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Wrote {output_html} ({len(html):,} chars)")

    # Step 5: Fix CSS font paths
    print("\n[5/5] Fixing CSS font paths...")
    fix_google_fonts_css(asset_map)
    fix_entry_css()

    # Summary
    print("\n" + "=" * 60)
    print("Done! Output in:", OUTPUT_DIR)
    print(f"  index.html:  {os.path.getsize(output_html):,} bytes")
    print(f"  css/:        {sum(f.stat().st_size for f in CSS_DIR.iterdir()):,} bytes")
    print(f"  fonts/:      {len(list(FONTS_DIR.iterdir()))} files")
    print(f"  images/:     {len(list(IMAGES_DIR.iterdir()))} files")
    print(f"  assets/:     {len(list(ASSETS_DIR.iterdir()))} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
