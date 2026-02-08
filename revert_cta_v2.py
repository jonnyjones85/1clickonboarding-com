#!/usr/bin/env python3
"""
revert_cta_v2.py — Revert all 20 CTA blocks to match original GHL site.

FIXED: The v1 script added an extra </div> for top_right_sec in the replacement,
but the regex only consumed up through inner_white_bkg close. The original
top_right_sec close was left as an orphan, breaking layout (20 orphaned </div> tags).

FIX: The replacement now ends at inner_white_bkg close (matching what the regex
consumes). The original top_right_sec close remains in place.
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

# The NEW canonical CTA inner content matching original GHL site.
# This starts AFTER <div class="top_right_sec big_cta"> and ends with
# </div> closing inner_white_bkg. It does NOT include </div> for top_right_sec
# because the regex preserves the original closing tag.
NEW_CTA_INNER = '''<p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>
						<div class="inner_white_bkg">
							<div style="display: inline-block; height: auto; margin-bottom: 0px !important; margin-top: 0px !important;">
								<img class="product_image" src="images/656b079ee33f7cbc7b2c7467.png" loading="lazy">
							</div>
							<h4 class="txt_red">Your Price: Only $47.00</h4>
							<h4 class="black">List Price $297</h4>
							<h4 class="small">You're Saving $250.00 Today</h4>
							<p class="savetoday fsize15">Download The Install Pack For Just $47.00!</p>
							<p class="fsize15 mb15">Delivered instantly. Start installing the pack in the next 2 minutes.</p>
							<p class="avail_dwld"><img style="display: inline-block;" alt="download icon" src="images/65638ce89762af2a5cc83b76.png" loading="lazy"> Now available for instant download</p>
							<iframe src="https://api.leadconnectorhq.com/widget/form/JfoVUQbTOONUDr9Jraq7" style="width:100%;border:none;border-radius:3px;overflow:visible;height:188px;" id="inline-JfoVUQbTOONUDr9Jraq7" data-layout="{'id':'INLINE'}" data-trigger-type="alwaysShow" data-trigger-value="" data-activation-type="alwaysActivated" data-activation-value="" data-deactivation-type="neverDeactivate" data-deactivation-value="" data-form-name="Email-Opt In 1CCO Funnel" data-height="432" data-layout-iframe-id="inline-JfoVUQbTOONUDr9Jraq7" data-form-id="JfoVUQbTOONUDr9Jraq7" title="Email-Opt In 1CCO Funnel" scrolling="no">
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


def main():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    original_len = len(html)

    # Step 1: Replace all CTA block contents
    # The regex matches from <div class="top_right_sec big_cta"> through the
    # FIRST pair of consecutive </div> tags (non-greedy). This consumes:
    #   - Opening: <div class="top_right_sec big_cta">
    #   - All inner content
    #   - Two closing </div>: close-last-text-center + close-inner_white_bkg
    # It does NOT consume the </div> for top_right_sec itself.
    cta_pattern = re.compile(
        r'(<div class="top_right_sec big_cta">)\s*'
        r'<p class="toptxt">DIGITAL DOWNLOAD NOW AVAILABLE</p>'
        r'.*?'  # All inner content (non-greedy)
        r'</div>\s*</div>',  # Close last-text-center + close inner_white_bkg
        re.DOTALL
    )

    matches = list(cta_pattern.finditer(html))
    print(f"Found {len(matches)} CTA blocks")

    if len(matches) < 15:
        print(f"ERROR: Expected ~20 CTAs, found {len(matches)}. Aborting.")
        return

    # Replace backwards to preserve positions
    # KEY FIX: replacement does NOT include </div> for top_right_sec.
    # The original </div> after the regex match handles that.
    for match in reversed(matches):
        start = match.start()
        end = match.end()
        replacement = f'<div class="top_right_sec big_cta">\n{NEW_CTA_INNER}'
        html = html[:start] + replacement + html[end:]

    # Verify replacement
    count_after = html.count('DIGITAL DOWNLOAD NOW AVAILABLE')
    print(f"After replacement: {count_after} CTA blocks")

    # Step 2: Remove .cta-email-form CSS blocks
    css_pattern = re.compile(
        r'\n*\.cta-email-form\s*\{[^}]*\}\s*',
        re.DOTALL
    )
    css_matches = list(css_pattern.finditer(html))
    print(f"Found {len(css_matches)} .cta-email-form CSS blocks to remove")
    html = css_pattern.sub('\n', html)

    # Verification
    print(f"\nVerification:")
    print(f"  '256-bit security encryption': {html.count('256-bit security encryption')}")
    print(f"  'authorized_payments': {html.count('authorized_payments')}")
    print(f"  'BACKED BY OUR UNCONDITIONAL': {html.count('BACKED BY OUR UNCONDITIONAL')}")
    print(f"  'height:188px': {html.count('height:188px')}")
    print(f"  'data-height=\"432\"': {html.count('data-height=\"432\"')}")
    print(f"  'cta-email-form': {html.count('cta-email-form')}")

    # Write
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    new_len = len(html)
    print(f"\nFile size: {original_len:,} -> {new_len:,} chars ({new_len - original_len:+,})")
    print("Done!")


if __name__ == "__main__":
    main()
