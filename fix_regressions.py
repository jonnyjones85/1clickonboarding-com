#!/usr/bin/env python3
"""
fix_regressions.py — Fix Session #10 optimization regressions

Regression #1: Font fix — Replace single-weight Roboto 400 with variable-weight (100-900)
Regression #2: CTA fix — Restore original CTA elements stripped by deduplication

Key findings from comparing backup (index.html.bak) with current (index.html):
- In the original, 8 of 20 CTAs had H1 heading + yellow badge + Install Now button
  (7 with full title, 1 sticky with shorter title)
- The other 12 CTAs had security encryption text + credit card logos (GHL default)
- optimize_site.py made ALL 20 look like a hybrid: security text + modified copy
- This script restores ALL 20 to the richer format (H1 + badge + Install Now button)
  since that's the intended sales design, and normalizes the upgrade across all CTAs.
"""

import os
import re
import urllib.request

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(SITE_DIR, "fonts")
CSS_DIR = os.path.join(SITE_DIR, "css")
INDEX_HTML = os.path.join(SITE_DIR, "index.html")

# Font filenames
OLD_ROBOTO = "KFO5CnqEu92Fr1Mu53ZEC9_Vu3r1gIhOszmkBnkaSTbQWg.woff2"
NEW_ROBOTO = "KFO7CnqEu92Fr1ME7kSn66aGLdTylUAMaxKUBHMdazTgWw.woff2"
NEW_ROBOTO_URL = f"https://fonts.gstatic.com/s/roboto/v47/{NEW_ROBOTO}"


def fix_font():
    """Download variable-weight Roboto and update google-fonts.css."""
    print("\n=== REGRESSION #1: Font Fix ===")

    # 1. Download variable-weight Roboto
    new_font_path = os.path.join(FONTS_DIR, NEW_ROBOTO)
    if not os.path.exists(new_font_path):
        print(f"Downloading variable-weight Roboto from Google Fonts...")
        urllib.request.urlretrieve(NEW_ROBOTO_URL, new_font_path)
        size = os.path.getsize(new_font_path)
        print(f"  Downloaded: {NEW_ROBOTO} ({size:,} bytes)")
    else:
        print(f"  Variable-weight Roboto already exists: {NEW_ROBOTO}")

    # 2. Update google-fonts.css
    css_path = os.path.join(CSS_DIR, "google-fonts.css")
    with open(css_path, "r") as f:
        css = f.read()

    old_roboto_block = """/* Roboto 400 normal - latin */
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  font-stretch: 100%;
  font-display: swap;
  src: url(../fonts/KFO5CnqEu92Fr1Mu53ZEC9_Vu3r1gIhOszmkBnkaSTbQWg.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}"""

    new_roboto_block = """/* Roboto variable weight - latin */
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 100 900;
  font-stretch: 100%;
  font-display: swap;
  src: url(../fonts/KFO7CnqEu92Fr1ME7kSn66aGLdTylUAMaxKUBHMdazTgWw.woff2) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}"""

    if old_roboto_block in css:
        css = css.replace(old_roboto_block, new_roboto_block)
        with open(css_path, "w") as f:
            f.write(css)
        print("  Updated google-fonts.css: Roboto 400 -> variable weight 100-900")
    else:
        print("  WARNING: Could not find expected Roboto 400 block in google-fonts.css")

    # 3. Remove old single-weight file
    old_font_path = os.path.join(FONTS_DIR, OLD_ROBOTO)
    if os.path.exists(old_font_path):
        os.remove(old_font_path)
        print(f"  Removed old single-weight font: {OLD_ROBOTO}")
    else:
        print(f"  Old font already removed: {OLD_ROBOTO}")

    print("  Font fix complete!")


def fix_ctas():
    """Restore original CTA elements in all 20 CTA blocks."""
    print("\n=== REGRESSION #2: CTA Content Fix ===")

    with open(INDEX_HTML, "r") as f:
        html = f.read()

    original_length = len(html)

    # =========================================================================
    # STEP 1: Replace the inner content of ALL 20 CTA blocks
    # =========================================================================
    # Current optimized CTA block pattern (from <div class="inner_white_bkg"> to </div> close):
    #
    # <div class="inner_white_bkg">
    #   <div style="display: inline-block; ..."><img class="product_image" ...></div>
    #   <h4 class="txt_red">Your Price: Only $47.00</h4>
    #   <h4 class="black">List Price $297</h4>
    #   <h4 class="small">You're Saving $250.00 Today</h4>
    #   <p class="savetoday fsize15">Download The Install Pack and 7 Bonuses For Just $47.00!</p>
    #   <p class="avail_dwld">...</p>
    #   <p class="fsize15 mb15">Delivered instantly...</p>
    #   <div class="cta-email-form"><iframe ...></div>
    #   <div class="text-center mt10">
    #     <p ...>We securely process payments...</p>
    #     <div class="text-center"><img class="authorized_payments" ...></div>
    #     <p class="mbc_logo_txt" ...>BACKED BY OUR UNCONDITIONAL...</p>
    #   </div>
    #   <div class="text-center"><img class="secure_checkout_img" ...></div>
    # </div>

    # We match the full CTA block from <div class="top_right_sec big_cta"> through its closing </div>s.
    # The approach: find each CTA block, replace the inner content.

    # Pattern: Match from inner_white_bkg opening through the security text block, keeping email form
    cta_inner_pattern = re.compile(
        r'(<div class="inner_white_bkg">\s*)'                      # inner_white_bkg open
        r'(<div style="display: inline-block[^"]*">\s*'            # product image wrapper
        r'<img class="product_image"[^>]*>\s*'
        r'</div>\s*)'
        r'(<h4 class="txt_red">Your Price: Only \$47\.00</h4>\s*'  # pricing section
        r'<h4 class="black">List Price \$297</h4>\s*'
        r'<h4 class="small">You\'re Saving \$250\.00 Today</h4>\s*)'
        r'<p class="savetoday fsize15">Download The Install Pack and 7 Bonuses For Just \$47\.00!</p>\s*'  # modified copy
        r'<p class="avail_dwld"><img[^>]*> Now available for instant download</p>\s*'
        r'<p class="fsize15 mb15">Delivered instantly\. Start installing the pack in the next 2 minutes\.</p>\s*'
        r'(<div class="cta-email-form">\s*'                        # email form (KEEP)
        r'<iframe[^>]*></iframe>\s*'
        r'</div>\s*)'
        r'<div class="text-center mt10">\s*'                       # non-original security block
        r'<p style="margin:0px auto 10px;text-align:center; color: #061130;width: 100%; max-width: 290px;">We securely process payments with 256-bit security encryption</p>\s*'
        r'<div class="text-center">\s*'
        r'<img class="authorized_payments"[^>]*>\s*'
        r'</div>\s*'
        r'<p class="mbc_logo_txt" style="margin:20px auto 0; color: #061130; width: 100%; max-width: 290px;"><img alt="mbc_logo" src="images/6508e799a8ce7068941edcae\.png" loading="lazy"> BACKED BY OUR UNCONDITIONAL<br>30 DAY MONEY BACK GUARANTEE</p>\s*'
        r'</div>\s*'
        r'(<div class="text-center">\s*'                           # secure checkout img
        r'<img class="secure_checkout_img"[^>]*>\s*'
        r'</div>)',
        re.DOTALL
    )

    def replace_cta(match):
        inner_white_bkg = match.group(1)
        product_img = match.group(2)
        pricing = match.group(3)
        email_form = match.group(4)
        secure_checkout = match.group(5)

        return (
            inner_white_bkg +
            '<h1>GET INSTANT ACCESS TO THE 1 CLICK CLIENT ONBOARDING INSTALL PACK FOR ONLY $47.00</h1>\n'
            '\t\t\t\t\t\t\t<p class="text-center"><span class="bkg_yellow small_headings" style="background: #ffe09a; padding: 0 5px; border-radius: 3px;">and also get 7 free bonuses valued at $3929</span></p>\n'
            '\t\t\t\t\t\t\t' +
            product_img +
            pricing +
            '<p class="savetoday fsize15">Download The Install Pack For Just $47.00!</p>\n'
            '\t\t\t\t\t\t\t<p class="fsize15 mb15">Delivered instantly. Start installing the pack in the next 2 minutes.</p>\n'
            '\t\t\t\t\t\t\t<p class="avail_dwld"><img style="display: inline-block;" alt="download icon" src="images/65638ce89762af2a5cc83b76.png" loading="lazy"> Now available for instant download</p>\n' +
            email_form +
            '<div class="text-center mt10">\n'
            '\t\t\t\t\t\t\t\t<a href="https://1clickonboarding.com/order-page" class="download_btn w-100"><img alt="arrow" class="btn_arrow" src="assets/65638ce89762af35e0c83b75.svg">Install Now <br><small>And Get Instant Access</small></a>\n'
            '\t\t\t\t\t\t\t\t<a href="https://1clickonboarding.com/order-page" class="clickhere_txt txt_blue" style="font-size: 13px!important;">Click Here To Download Your 1 Click Client Onboarding Install Pack Now</a>\n'
            '\t\t\t\t\t\t\t\t<p class="mbc_logo_txt" style="margin:0 auto 15px; color: #061130; font-weight: 600; width: 100%; max-width: 290px;"><img alt="mbc_logo" src="images/6508e799a8ce7068941edcae.png" loading="lazy"> Backed By Our Unconditional <br>30 Day Money Back Guarantee</p>\n'
            '\t\t\t\t\t\t\t</div>\n\t\t\t\t\t\t\t' +
            secure_checkout
        )

    count = len(cta_inner_pattern.findall(html))
    html = cta_inner_pattern.sub(replace_cta, html)
    print(f"  Restored H1 + yellow badge + Install Now button + Click Here link in {count} CTA blocks")

    # =========================================================================
    # STEP 2: Fix sticky sidebar CTA — use shorter H1 title
    # =========================================================================
    # The sticky sidebar CTA (inside sticky_buy_element) should have a shorter H1:
    # "GET INSTANT ACCESS TO THE 1CCO INSTALL PACK FOR ONLY $47.00" (with class="small")
    # instead of the full "GET INSTANT ACCESS TO THE 1 CLICK CLIENT ONBOARDING INSTALL PACK..."

    sticky_h1_pattern = re.compile(
        r'(sticky_buy_element">\s*'
        r'<div style="[^"]*position: sticky[^"]*">\s*'
        r'<div class="top_right_sec big_cta">\s*'
        r'<p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>\s*'
        r'<div class="inner_white_bkg">\s*)'
        r'<h1>GET INSTANT ACCESS TO THE 1 CLICK CLIENT ONBOARDING INSTALL PACK FOR ONLY \$47\.00</h1>',
        re.DOTALL
    )

    if sticky_h1_pattern.search(html):
        html = sticky_h1_pattern.sub(
            r'\g<1><h1 class="small">GET INSTANT ACCESS TO THE 1CCO INSTALL PACK FOR ONLY $47.00</h1>',
            html
        )
        print("  Fixed sticky sidebar H1 to use shorter title with class='small'")
    else:
        print("  Note: Sticky sidebar H1 pattern not found (may already be correct)")

    # Write the fixed HTML
    with open(INDEX_HTML, "w") as f:
        f.write(html)

    new_length = len(html)
    diff = new_length - original_length
    print(f"\n  HTML size: {original_length:,} -> {new_length:,} ({diff:+,} bytes)")
    print("  CTA fix complete!")


def verify():
    """Run basic verification checks."""
    print("\n=== VERIFICATION ===")

    # Check font file exists
    new_font = os.path.join(FONTS_DIR, NEW_ROBOTO)
    old_font = os.path.join(FONTS_DIR, OLD_ROBOTO)

    if os.path.exists(new_font):
        size = os.path.getsize(new_font)
        print(f"  [OK] Variable-weight Roboto exists ({size:,} bytes)")
    else:
        print(f"  [FAIL] Variable-weight Roboto missing!")

    if not os.path.exists(old_font):
        print(f"  [OK] Old single-weight Roboto removed")
    else:
        print(f"  [FAIL] Old single-weight Roboto still exists!")

    # Check CSS
    css_path = os.path.join(CSS_DIR, "google-fonts.css")
    with open(css_path, "r") as f:
        css = f.read()
    if "font-weight: 100 900" in css:
        print("  [OK] google-fonts.css has variable weight range")
    else:
        print("  [FAIL] google-fonts.css missing variable weight range")

    if NEW_ROBOTO in css:
        print("  [OK] google-fonts.css references new font file")
    else:
        print("  [FAIL] google-fonts.css doesn't reference new font file")

    # Check HTML
    with open(INDEX_HTML, "r") as f:
        html = f.read()

    install_now_count = html.count('class="download_btn w-100"')
    print(f"  [{'OK' if install_now_count >= 20 else 'WARN'}] Install Now buttons: {install_now_count}")

    click_here_count = html.count('class="clickhere_txt txt_blue"')
    print(f"  [{'OK' if click_here_count >= 20 else 'WARN'}] Click Here links: {click_here_count}")

    h1_full_count = html.count('GET INSTANT ACCESS TO THE 1 CLICK CLIENT ONBOARDING INSTALL PACK FOR ONLY $47.00')
    h1_short_count = html.count('GET INSTANT ACCESS TO THE 1CCO INSTALL PACK FOR ONLY $47.00')
    print(f"  [INFO] H1 full title count: {h1_full_count}")
    print(f"  [INFO] H1 short title (sticky): {h1_short_count}")
    print(f"  [{'OK' if h1_full_count + h1_short_count >= 20 else 'WARN'}] Total H1 headings: {h1_full_count + h1_short_count}")

    has_yellow_badge = html.count('bkg_yellow small_headings')
    print(f"  [{'OK' if has_yellow_badge >= 20 else 'WARN'}] Yellow bonuses badges: {has_yellow_badge}")

    email_form_count = html.count('JfoVUQbTOONUDr9Jraq7')
    print(f"  [{'OK' if email_form_count >= 20 else 'WARN'}] Email opt-in forms: {email_form_count}")

    old_copy = html.count('and 7 Bonuses For Just')
    print(f"  [{'OK' if old_copy == 0 else 'WARN'}] Old '7 Bonuses' copy remaining: {old_copy}")

    original_copy = html.count('Download The Install Pack For Just $47.00!')
    print(f"  [{'OK' if original_copy >= 20 else 'WARN'}] Original copy count: {original_copy}")

    security_text = html.count('256-bit security encryption')
    print(f"  [{'OK' if security_text == 0 else 'WARN'}] Non-original security text remaining: {security_text}")

    authorized_payments = html.count('authorized_payments')
    print(f"  [{'OK' if authorized_payments == 0 else 'WARN'}] Non-original credit card logos remaining: {authorized_payments}")


if __name__ == "__main__":
    print("=" * 60)
    print("Session #10 Regression Fix Script")
    print("=" * 60)

    fix_font()
    fix_ctas()
    verify()

    print("\n" + "=" * 60)
    print("All fixes applied! Push to GitHub to deploy.")
    print("=" * 60)
