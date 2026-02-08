#!/usr/bin/env python3
"""
create_nbs.py — Generate nbs.html from index.html

Reads 1clickonboarding-clean/index.html as a template and produces nbs.html
for the Neutral Basal System ($29 ebook) product page.

Strategy:
  1. Remove 3 sections: value-prop, hormozi-quote, sneak-peek
  2. Swap content in remaining 11 sections (top-bar, hero, sales-letter, etc.)
  3. Replace all product images with gray SVG placeholders
  4. Update pricing: $47→$29, $297→$97, save $250→save $68
  5. Update CTA links: order-page URLs → #checkout
  6. Update title/meta

Reproducible — re-run anytime the base template changes.
"""

import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'index.html')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'nbs.html')

# Gray placeholder SVG data URI
PLACEHOLDER_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='400' height='300'%3E%3Crect width='400' height='300' "
    "fill='%23e0e0e0'/%3E%3Ctext x='200' y='155' text-anchor='middle' "
    "font-family='sans-serif' font-size='14' fill='%23999'%3E"
    "Placeholder%3C/text%3E%3C/svg%3E"
)


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def remove_section(html, section_id):
    """Remove a GHL section by its id attribute.

    Sections are structured as:
      <div ... id="section-NAME" ...>...</div><div ... id="section-NEXT" ...>

    We find the opening tag and then track div depth to find the matching close.
    """
    # Find the section start
    pattern = rf'<div[^>]*\bid="{re.escape(section_id)}"[^>]*>'
    match = re.search(pattern, html)
    if not match:
        print(f"  WARNING: Section '{section_id}' not found")
        return html

    start = match.start()

    # Track div depth to find closing </div>
    depth = 0
    pos = start
    while pos < len(html):
        open_match = re.match(r'<div[\s>]', html[pos:])
        close_match = re.match(r'</div>', html[pos:])

        if open_match:
            depth += 1
            pos += open_match.end()
        elif close_match:
            depth -= 1
            if depth == 0:
                end = pos + len('</div>')
                removed = html[start:end]
                print(f"  Removed section '{section_id}' ({len(removed):,} chars)")
                return html[:start] + html[end:]
            pos += close_match.end()
        else:
            pos += 1

    print(f"  WARNING: Could not find closing tag for '{section_id}'")
    return html


def replace_images_with_placeholders(html):
    """Replace all image src attributes pointing to images/ with placeholder SVG."""
    count = 0

    def replacer(match):
        nonlocal count
        full = match.group(0)
        src = match.group(1)
        # Only replace images/ paths (product images), not assets/ or external URLs
        if src.startswith('images/'):
            count += 1
            return full.replace(f'src="{src}"', f'src="{PLACEHOLDER_SVG}"')
        return full

    # Match <img tags with src attributes
    result = re.sub(r'<img[^>]*\bsrc="([^"]*)"[^>]*>', replacer, html)
    print(f"  Replaced {count} image src attributes with placeholders")
    return result


def replace_background_images_with_placeholders(html):
    """Replace CSS background-image references to images/ with placeholder."""
    count = 0

    def replacer(match):
        nonlocal count
        url = match.group(1)
        if 'images/' in url:
            count += 1
            return match.group(0).replace(url, PLACEHOLDER_SVG)
        return match.group(0)

    result = re.sub(r'url\(&quot;([^&]*?)&quot;\)', replacer, html)
    result = re.sub(r'url\("([^"]*?)"\)', replacer, result)
    result = re.sub(r"url\('([^']*?)'\)", replacer, result)
    print(f"  Replaced {count} background-image URLs with placeholders")
    return result


def update_title(html):
    """Update the page title."""
    html = html.replace(
        '<title>1 Click Onboarding Install Pack</title>',
        '<title>Neutral Basal System | Lose 2-3kg/Month Sustainably | $29</title>'
    )
    print("  Updated page title")
    return html


def update_pricing(html):
    """Replace all pricing references."""
    replacements = [
        # CTA box pricing
        ('Your Price: Only $47.00', 'Your Price: Only $29'),
        ('List Price $297', 'List Price $97'),
        ("You're Saving $250.00 Today", "You're Saving $68 Today"),
        # Button text
        ('Install Now For Only $47.00', 'Download Now For Only $29'),
        ('Install Now For Only  $47.00', 'Download Now For Only $29'),
        # CTA box headings
        ('GET INSTANT ACCESS TO THE 1 CLICK CLIENT ONBOARDING INSTALL PACK FOR ONLY $47.00',
         'GET INSTANT ACCESS TO THE NEUTRAL BASAL SYSTEM BOOK FOR ONLY $29'),
        # Download text
        ('Download The Install Pack and 7 Bonuses For Just $47.00!',
         'Download The Book and 10 Bonuses For Just $29!'),
        ('Download The Install Pack For Just $47.00!',
         'Download The Book For Just $29!'),
        # Bonus values
        ('and also get 7 free bonuses valued at $3929',
         'and also get 10 free bonuses valued at $214'),
        ('7 free bonuses valued at $3929',
         '10 free bonuses valued at $214'),
        # Misc pricing
        ('for <u>under $50 </u>', 'for <u>only $29</u>'),
        ('for under $50', 'for only $29'),
    ]

    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  Pricing: '{old[:50]}...' → '{new[:50]}...'")

    return html


def update_cta_links(html):
    """Replace CTA links with #checkout placeholder."""
    count = 0

    # Replace order-page URLs
    for url in [
        'https://1clickonboarding.com/order-page',
        'https://1clickonboarding.com/order_page',
    ]:
        occurrences = html.count(url)
        if occurrences > 0:
            html = html.replace(url, '#checkout')
            count += occurrences

    print(f"  Replaced {count} CTA links with #checkout")
    return html


def update_cta_button_text(html):
    """Update CTA button text from install pack to book."""
    replacements = [
        ('Click Here To Get 1 Click Client Onboarding',
         'Click Here To Get Your Book'),
        ('Click Here To Get Your Install Pack',
         'Click Here To Get Your Book'),
        ('Click Here To Download Your 1 Click Client Onboarding Install Pack Now',
         'Click Here To Download Your Neutral Basal System Book Now'),
        # Button sub-text
        ('And Get Instant Access', 'And Get Instant Access'),
        # Download delivery text
        ('Delivered instantly. Start installing the pack in the next 2 minutes.',
         'Delivered instantly. Start reading in the next 2 minutes.'),
        ('Now available for instant download',
         'Now available for instant download'),
        # Install → Download in buttons
        ('> Install Now <br>', '> Download Now <br>'),
        ('>Install Now <br>', '>Download Now <br>'),
    ]

    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new)
            print(f"  CTA text: '{old[:50]}...' → '{new[:50]}...'")

    return html


def update_top_bar(html):
    """Update top bar section with NBS branding."""
    replacements = [
        ('info@8figuresystems.io', 'kele@neutralbasalsystem.com'),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  Top bar: '{old}' → '{new}'")
    return html


def update_hero_section(html):
    """Update hero section with NBS content."""
    replacements = [
        # Blue banner text
        ('For Any Agency or Coaching Business Looking To Fully Streamline Their Client Onboarding Process In 2024...',
         'DISCOVERY: How I Lost 12 Kilos in 4 Months Without Exercise, Without Dieting, Without Counting Calories'),
        # Main headline
        ('How To <span style="color: #fe9706;"> Streamline Client Onboarding </span> For your Coaching or Agency Business\nBy <span style="color: #fe9706;"> Installing An Automated &amp; FoolProof System</span> Used by 7 Figure Businesses',
         '&quot;New Book Reveals a Counter-Intuitive Approach That Helps You <span style="color: #fe9706;">Lose 2-3kg/Month</span>&quot;\nWhile <span style="color: #fe9706;">Saving Money, Saving Time</span>, and Keeping Your Social Life'),
        # Sub-headline (the <u> text)
        ('<strong><u>Without</u> hiring assistants or changing anything else in your business, <u>even if </u>you have no expertise </strong></h1><h1><strong>in systems, <u>while saving thousands</u> of $$$ on unnecessary tasks.</strong>',
         '<strong><u>Without</u> exercise, <u>without</u> dieting, <u>without</u> counting calories, <u>even if</u> you have no expertise in nutrition, <u>while keeping</u> your social life intact.</strong>'),
        # "What is the..." heading
        ('<span style="color: #fe9706;">1 Click Client Onboarding Install Pack?</span>',
         '<span style="color: #fe9706;">Neutral Basal System?</span>'),
        ('What is the <span style="color: #fe9706;">Neutral Basal System?</span>',
         'What is the <span style="color: #fe9706;">Neutral Basal System?</span>'),
        # Description paragraph
        ('The 1 Click Client Onboarding Install Pack is a counterintuitive client onboarding approach to onboard clients without complicated systems, expensive software, or managing assistants.</p><p></p><p>We achieve this by finding the onboarding steps that are repetitive for every client and leveraging automations that do the work for you.</p><p></p><p>And as a result...this frees you up to focus on working ON your business and NOT IN the business - this is the 1 Click Client Onboarding Install Pack.</p><p></p><p><u>This Install Pack works with all website &amp; funnel builders</u> - Wordpress, Clickfunnels, GoHighlevel, Webflow... <strong>without changing anything to your current setup!</strong></p><p></p><hr style="border:none;border-top:1px solid #ddd;margin:20px 0;">',
         'The Neutral Basal System is a counter-intuitive approach to weight loss that helps you lose 2-3kg per month sustainably.</p><p></p><p>We achieve this by optimizing your basal metabolism to create natural weight loss conditions, instead of fighting your body with restrictive diets and exhausting exercise.</p><p></p><p>And as a result...you lose weight while keeping your social life, saving money, and saving time - this is the Neutral Basal System.</p><p></p><p><u>This system works for anyone</u> - whether you\'re busy, social, or have no nutrition expertise... <strong>without changing your lifestyle!</strong></p><p></p><hr style="border:none;border-top:1px solid #ddd;margin:20px 0;">'),
        # Hero CTA box - product name
        ('DIGITAL DOWNLOAD NOW AVAILABLE', 'DIGITAL DOWNLOAD NOW AVAILABLE'),
    ]
    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new)
            print(f"  Hero: replaced '{old[:60]}...'")
    return html


def update_sales_letter(html):
    """Update sales letter section with NBS content.

    This is the longest section. We replace the key headings and paragraphs.
    """
    replacements = [
        # Main sales letter heading
        ("Here's How I Went from Spending Hours Doing Tedious Tasks To Fully Perfecting Client Onboarding By Ignoring The Common Wisdom, Breaking All The Rules, And Turning The Coaching &amp; Agency Model Upside Down",
         "How I Went From 89 Kilos to 76.3 Kilos by Ignoring Conventional Wisdom, Breaking All the Rules, and Completely Flipping the Weight Loss Model"),
        # Sub-heading
        ("This Is Something Completely New, Completely Different, Completely Unlike Anything</strong></h1><h1><strong>You've Ever Heard of Before - Read The Story Below To Discover The 1 Click Client Onboarding Install Pack",
         "This Is Something Completely New, Completely Different, Completely Different From Anything You've Ever Heard - Read the Story Below to Discover the Neutral Basal System"),
        # Dear future owner
        ("<strong>Dear Future 1 Click Client Onboarding </strong>Install Pack<strong> Owner</strong>",
         "<strong>Dear Future Owner of the Neutral Basal System</strong>"),
        # Author line
        ("<strong>From:</strong>&nbsp;The laptop of Katie Bani",
         "<strong>From:</strong>&nbsp;Kele Diabat\u00e9's laptop"),
        # Re: line
        ("<strong>Re: Your Automated Client Onboarding </strong>Install Pack</h1><h1><strong>(and why this is your only way out)</strong>",
         "<strong>Re: Losing 2-3kg per month sustainably</strong></h1><h1><strong>(and why this is your only way out)</strong>"),
        # Surprised paragraph
        ("Surprised to hear that I was able to <strong>onboard 10+ clients within a couple of minutes</strong> using the systems shared in this install pack?",
         "Hello, my name is Kele Diabat\u00e9.</p><p></p><p>Would it surprise you to learn that I lost 12 kilos in 4 months using the information revealed in this 40-page book?"),
        ("Would it surprise you even more to learn that <strong><u>you'll be able to automate the tedious onboarding tasks for your coaching or agency clients and gain back time in your life</u></strong> using the exact same system that I'm about to show you?</p><p></p><p>Or that you'll be able to get access to it for <u>under $50 </u>?</p><p></p><p>Skeptical?</p><p></p><p><u>You should be.&nbsp;</u></p><p></p><p>After all, you can't believe everything you read on the internet :-)</p>",
         "Skeptical?</p><p></p><p>You should be.</p><p></p><p>After all, you can't believe everything you read on the Internet.</p><p></p><p>So let me prove it to you.</p><p></p><p>But first, read this disclaimer:</p><p></p><p>I have the advantage of having been a high-level athlete for 20 years. I missed Olympic qualification twice in the finals. I have a deep understanding of the human body and its mechanisms.</p><p></p><p>The average person who buys \"how-to\" information gets little to no results. I use these references as examples only.</p><p></p><p>Your results will vary and depend on many factors... including, but not limited to, your background, your experience, and your work ethic.</p><p></p><p>Any purchase involves risks as well as massive and constant effort and action. If you're not ready to accept this, please DO NOT GET THIS BOOK.</p><p></p><p>And yes, it took me time and energy to get my results.</p><p></p><p>That said... let me show you directly...</p>"),
        # "so let me prove it to you" heading
        ('<font color="#cc0000"><strong>so let me prove it to you</strong></font>',
         '<font color="#cc0000"><strong>How I Went From 89 Kilos to 76.3 Kilos</strong></font>'),
        # "It took me years" paragraph
        ("It took me years and energy to build the systems.</p><p></p><p>With that said\u2026let me jump right in and show you just a small fraction of what it did for our clients...",
         "And I Did It Using a Completely Counter-Intuitive Model That I'm About to Share With You On This Very Page...</p><p></p><p>The same Neutral Basal System model that men around the world are now using to lose weight...</p><p></p><p>...And in turn lose faster than ever before...</p><p></p><p>...While saving money so they can focus on WHAT THEY WANT...</p><p></p><p>...And best of all, keeping their social life intact."),
        # "And I Did It By Using" heading
        ('<font color="#cc0000"><strong>And I Did It By Using A <u>Completely Counterintuitive</u>&nbsp;Model&nbsp;That I\'m About To Share&nbsp;</strong></font><strong>With You On This Very Page\u2026</strong>',
         '<font color="#cc0000"><strong>This Neutral Basal System is different from any method you\'ve heard of before...</strong></font>'),
        # Step-by-step demo highlight text
        ('<span class="highlight">Here\'s a quick step-by-step demo of how it all works</span> (and then I\'ll show you the rest of the case studies, testimonials and details on the rest of the page below)...',
         '<span class="highlight">...It\'s something completely different, because...</span>'),
        # The bullet list about what we don't focus on
        ("<strong>We don't focus on changing your habits and turning you into an organized freak</strong></p></li></ul><ul><li><p><strong>We don't focus on doing more to maybe get recognition for it.</strong></p></li></ul><ul><li><p><strong>We don't focus on creating a complicated process that only a smart few understand.</strong></p></li></ul><ul><li><p><strong>We don't focus on shiny software that costs you hundreds per month.</strong>",
         "<strong>We don't focus on intensive exercise</strong></p></li></ul><ul><li><p><strong>We don't focus on calorie counting</strong></p></li></ul><ul><li><p><strong>We don't focus on restrictive diets</strong></p></li></ul><ul><li><p><strong>We don't focus on dietary supplements</strong></p></li></ul><ul><li><p><strong>We don't focus on social sacrifices</strong>"),
        # "rarely build without knowing"
        ("In fact: we rarely (if ever) build systems without knowing that they will be simple to use\u2026",
         "In fact: we rarely (if ever) do what the fitness industry tells you to do."),
        # "Instead we leverage..."
        ("<strong>Instead We Leverage A Standard Process that Creates An Amazing Client Experience By Installing Simple Automations</strong></h1><h1><strong>That Run On Autopilot\u2026</strong>",
         "<strong>Instead, we use the Neutral Basal System...</strong></h1><h1><strong>As I said...</strong></h1><h1><strong>It's something completely different and it has the power to change everything for you...</strong>"),
        # Client onboarding specific content - bullet list about BS
        ("<ul><li><p>Like worrying if you sent all emails, documents, and links</p></li><li><p>Using expensive software that shrinks your profits.</p></li><li><p>Following processes with a lot of steps and checklists.</p></li><li><p>Managing unreliable assistants.</p></li><li><p>Or dealing with clients that made you want to pull your hair out.</p></li></ul>",
         "<ul><li><p>Spending hours at the gym</p></li><li><p>Counting every calorie consumed</p></li><li><p>Following complicated diets with 47 rules</p></li><li><p>Buying overpriced foods</p></li><li><p>Sacrificing my social life</p></li></ul>"),
        # "The 1-Click Client Onboarding Install Pack Frees You..."
        ("<strong>The 1-Click Client Onboarding Install Pack Frees You From All That And It Allows You To Onboard Clients On Autopilot And Have The Freedom To Remove Yourself From \u039fperations</strong>",
         "<strong>The Neutral Basal System Freed Me From All That and Allowed Me to Lose 12 Kilos in 4 Months</strong>"),
        # "Here's what life used to look like..."
        ("<strong><u>Here's what life used to look like before the 1 Click Client Onboarding Install Pack (and if you signed up clients before, then I'm sure you can relate)\u2026</u></strong></h1><p><br><br>I call this the \"Client Onboarding Of Doom\":",
         "<strong><u>Here's what my life looked like before (and if you've ever tried to lose weight, then I'm sure you can relate)...</u></strong></h1><p><br><br>I call it the \"Failure Cycle\":"),
        # Steps 1-8 (the doom cycle)
        ("<strong>Step 1</strong> - Close the deal and collect the payment.",
         "<strong>Step 1</strong> - Decide to lose weight with motivation"),
        ("<strong>Step 2</strong> -<strong>&nbsp;</strong>Manually create the contract and fill it out carefully.",
         "<strong>Step 2</strong> - Search for THE miracle method on the Internet"),
        ("<strong>Step 3</strong> - Message the client to welcome them.",
         "<strong>Step 3</strong> - Start a strict diet and exercise program"),
        ("<strong>Step 4</strong> - Create the client materials (folder, documents, and links).",
         "<strong>Step 4</strong> - Hold on for 2-3 weeks with a lot of effort"),
        ("<strong>Step 5</strong> - Send an email to the client with the next steps.",
         "<strong>Step 5</strong> - Break during a social event or from fatigue"),
        ("<strong>Step 6</strong> - Ask the client if they received the logins and emails.",
         "<strong>Step 6</strong> - Feel guilty and tell yourself you lack willpower"),
        ("<strong>Step 7</strong>&nbsp;-&nbsp;Add all upcoming payments to a calendar to charge the client in the future.",
         "<strong>Step 7</strong> - Regain the lost weight (and sometimes more)"),
        ("<strong>Step 8</strong>&nbsp;-&nbsp;Start over",
         "<strong>Step 8</strong> - Start over"),
        # "Client Onboarding Of Doom not only sucks..."
        ("The Client Onboarding Of Doom not only sucks, but it keeps you stuck for years - forcing you to spread yourself thin, invest in the wrong hires, while working hard to scale your business.",
         "The Failure Cycle not only sucked, but kept me stuck for years - forcing me to stay frustrated with my weight while working hard."),
        # John's story → Kele's story
        ("...Business owners, like John, almost give up the idea of scaling their business.",
         "...I almost gave up on this whole idea of losing weight easily."),
        ("...But before giving up.</p><p></p><p>John wanted to try something.",
         "...But before giving up.</p><p></p><p>I wanted to try something."),
        # "And I Put This Entire System..."
        ("<strong>And I Put This Entire System In An Install Pack Called The \"1 Click Client Onboarding\"</strong></h1><h1><strong>And You Can Start Using It In Just</strong></h1><h1><strong>A Few Moments From Now\u2026</strong>",
         "<strong>And I Put This Entire System Into a 40-Page Book Called \"Neutral Basal System\"</strong></h1><h1><strong>And You Can Start Reading It In Just</strong></h1><h1><strong>A Few Moments From Now...</strong>"),
        # "I'd like to introduce myself..."
        ("I'd like to introduce myself and tell you about how all this came to be.",
         "I'd like to introduce myself and tell you about how this all happened."),
        # "Let Me Explain..." heading
        ("<strong>Let Me Explain To You How This All Came To Be, So That You Fully Understand Why It Works In The First Place\u2026</strong>",
         "<strong>My name is Kele Diabat\u00e9...</strong>"),
        # Author bio
        ("<strong>My name is Katie Bani\u2026</strong></p><p></p><p>You probably haven't heard that name before. That's because I always stayed in the shadows of business.</p><p></p><p>In 2020, I was working as an operations manager in a consulting firm that rapidly scaled from $80,0000/mo to $500,000/mo.&nbsp;</p><p></p><p>Soon after I got promoted to the COO.</p><p></p><p>I consulted business to scale at 7 Figures with systems.</p><p></p><p>And I made multiple 6 figures and pretty much I lived and breathed systems.",
         "You've probably never heard this name before. That's intentional.</p><p></p><p>My life is pretty good... I was an international fencer for 20 years, representing Mali. I was twice a finalist in Olympic qualifications. I developed a unique expertise of the human body and its adaptation capabilities.</p><p></p><p>As I write this, I currently live in Paris."),
        # "Here are some pictures..." heading
        ("Here are some pictures capturing exactly these moments...",
         "As We Get to Know Each Other... You'll Quickly Realize That I'm the Luckiest Person on Earth - So Let's Talk About Where I Was in March 2024"),
        # John's story about watching movies → Kele at 89kg
        ("One of my first few clients, John (not his real name), came to us after trying to fix his systems himself, working with consultants, and even trying to hire assistants.</p><p></p><p>Nothing worked.</p><p></p><p>He had multiple clients to onboard and serve every day.</p><p></p><p>He didn't have experience managing operations at such a scale.</p><p>... and everything he tried failed.</p><p></p><p>He told me..</p><p></p><p>\"Katie, I was watching a movie with my partner and I got a notification on my phone that I needed to onboard a client\u2026At that moment, I hated everything about my business. There has to be a better way to run my business.\"</p><p></p><p>You see, John gave it everything he had.",
         "I was 28 years old and weighed 89 kilos.</p><p></p><p>I had no specific weight goal.</p><p></p><p>I had no clear and simple method.</p><p></p><p>I had no system that respected my current life.</p><p></p><p>...and I had just missed my second Olympic qualification in the finals.</p><p></p><p>This meant I couldn't reach my physical peak for a possible next attempt.</p><p></p><p>There's a stupid myth out there... that the more you suffer, the better results you get.</p><p></p><p>...Well sometimes that's not the case...</p><p></p><p>And if you want to lose weight sustainably, it's almost never the answer...</p><p></p><p>I know this, because I tried.</p><p></p><p>I gave it everything."),
        # "He gave it his BEST shot."
        ("He gave it his BEST shot.</p><p></p><p>And it didn't work.</p><p></p><p>Because he played by the rules and he did everything right...",
         "I gave my BEST shot.</p><p></p><p>And it didn't work.</p><p></p><p>Because I played by the rules and did everything correctly..."),
        # "He Ended Up Stressed Daily"
        ("<strong>He Ended Up Stressed Daily </strong></h1><h1><strong>And He Hated It\u2026</strong>",
         "<strong>I Ended Up With the Same Disappointing Results as Everyone Else</strong></h1><h1><strong>And I Hated It...</strong>"),
        # "He hated it because..."
        ("<strong>He hated it because the entire business relied on him.</strong></p><p></p><p>He had goals, dreams, and aspirations...He wanted more out of life...</p><p>...and working 24/7 in the business wasn't going to work.</p><p></p><p>So he did what everyone else out there does in this situation.</p><p></p><p>He started looking for a way out.</p><p></p><p>He looked everywhere and a few months later he reached out to me.</p><p></p><p>Within a few weeks of working together, John's systems were fully streamlined and automated.</p><p><br>The biggest bottleneck was his client onboarding process which cost him tens of thousands of dollars in client recurring revenue &amp; countless hours in admin work\u2026This was now fully automated.</p><p></p><p>No more client churn, and no more tedious onboarding tasks.</p><p></p><p>All he had to do was fill out a form that automatically took care of onboarding clients 24/7 and 100% accurately.</p><p></p><p>What we worked on with John completely changed his life and his business.</p><p></p><p>The business is currently making multiple 7 figures because he doesn't spend time on tedious onboarding tasks and his client lifetime value increased steeply.</p><p></p><p>Today, we laugh together thinking about the old times\u2026 when onboarding clients manually defined his lifestyle.</p>",
         "I hated it because it didn't respect my life, my constraints, my desires.</p><p></p><p>I had goals, dreams and aspirations... I wanted more from life...</p><p></p><p>...and traditional weight loss methods weren't going to work.</p><p></p><p>So I did what everyone does in this situation.</p><p></p><p>I started looking for a way out.</p><p></p><p>I searched everywhere and a few months later I found it.</p><p></p><p>I came across an approach where a group of people talked about how they \"optimized their basal metabolism\" to create natural weight loss conditions.</p><p></p><p>It was a cool concept to me, and as I did more research, I found that most of them were like me.</p><p></p><p>They also wanted to lose weight without sacrificing their life.</p><p></p><p>The only difference was that they were using the Neutral Basal System."),
        # "The 1 Click Client Onboarding Install Pack Is One Of The Most..."
        ("<strong>The 1 Click Client Onboarding Install Pack Is</strong></h1><h1><strong>One Of The Most Legitimate And Easy-To-Use If You Want To Onboard Clients Instantly</strong></h1><h1><strong>and Without Doing Admin Work.</strong>",
         "<strong>The Neutral Basal System is One of the Most Legitimate and Easy-to-Use Approaches</strong></h1><h1><strong>If You Want to Lose Weight Sustainably</strong>"),
        # "Just think about it" paragraphs
        ("Send custom contracts to clients? The 1CCO System takes care of this automatically.",
         "Why keep forcing your body with methods it rejects? The Neutral Basal System works WITH your physiology."),
        ("Welcome Clients with a personal touch? The 1CCO System takes care of this automatically.",
         "Why complicate with 47 dietary rules? The Neutral Basal System has a simple and clear protocol."),
        ("Track upcoming and finances? The 1CCO System takes care of this automatically.",
         "Why spend a fortune on supplements and special foods? The Neutral Basal System saves you money."),
        ("Track Clients in a CRM? The 1CCO System takes care of this automatically.",
         "Why sacrifice your social life? The Neutral Basal System adapts to your lifestyle."),
        ("Bridge the communication between the Sales and Fulfillment team? The 1CCO System takes care of this automatically.",
         "Why exhaust yourself with intensive exercise? The Neutral Basal System optimizes your metabolism naturally."),
        ("Focus on closing clients and not admin work? The 1CCO System takes care of this automatically and maximizes your team's capacity.",
         "The Neutral Basal System was the perfect thing for me..."),
        ("The 1CCO System was the perfect thing for all my clients, including John...",
         "And the best part that attracted me to do it this way?"),
        # "best part attracted" heading
        ("<strong>And the best part that attracted me to doing it this way?</strong>",
         "<strong>You Don't Even Need to Disrupt Your Life</strong>"),
        # "You Don't Even Have To Keep Track Of Payment Plans"
        ("<strong>You Don't Even Have To Keep </strong></h1><h1><strong>Track Of Payment Plans</strong>",
         "<strong>Which means you can keep your social habits,</strong></h1><h1><strong>your work rhythm, your food pleasures...</strong>"),
        # "Which means you collect payments..."
        ("Which means you collect payments on time and track the client deals...</p><p></p><p><strong>All you have to do is install the 1CCO System in your existing onboarding process and allow the business machine to do the heavy lifting for you.</strong>",
         "All you have to do is activate the Neutral Basal System according to the precise protocol.</p><p></p><p><strong>And that's it. The system works WITH your body, not against it.</strong>"),
        # "And That Was The Birth Of John's 7-Figure Business Journey"
        ("<strong>And That Was The Birth Of John's </strong></h1><h1><strong>\"7-Figure Business\" Journey</strong>",
         "<strong>And That Was the Birth of My Transformation</strong>"),
        # "After years of working non-stop..."
        ("After years of working non-stop on low-leverage, tedious tasks and <strong>trying to carry the weight of the entire business on his own shoulders</strong>, John followed my direction and drastically added leverage to his business.</p><p></p><p>John knew how to get attention and make sales, but operations were foreign to him.</p><p></p><p>He wasn't consistent because there were too many small tasks and too little time.</p><p></p><p>Here's what John's \"before\" state looked like",
         "After doing some research - I started implementing the Neutral Basal System.</p><p></p><p>I had no idea how my body would react long term.</p><p></p><p>All I knew was that the physiological principles were solid.</p><p></p><p>Here's what my starting point looked like: 89 kilos, frustrated, no clear solution."),
        # "And even though the solution now..."
        ("And even though the solution now with the 1-Click Client Onboarding Install Pack is straightforward...</p><p><br><strong>\u2026I went through a lot of testing and iterations to make it what is it today for John and everyone who implemented it.</strong></p><p></p><p>Looking back, those first 6 months of figuring this out were brutal.</p><p></p><p>Late nights.</p><p></p><p>Hard work.</p><p></p><p>Stress.</p><p></p><p>Everything I did was work, test, reflect and improve.</p><p></p><p>Sometimes I thought - maybe there isn't a better way.</p><p></p><p><strong>That was reality and I was ready to quit on this system.</strong></p><p></p><p><strong>But thankfully, I didn't...</strong>",
         "And even though I had the advantage of having an athletic base,</p><p></p><p>I still had to apply the system rigorously.</p><p></p><p>Looking back, those first months were revealing.</p><p></p><p>Quick results.</p><p></p><p>Simplicity of application.</p><p></p><p>Mental freedom.</p><p></p><p>But most importantly: it was sustainable.</p><p></p><p>This was my life and I was ready to abandon all other systems.</p><p></p><p><strong>But fortunately, I didn't...</strong>"),
        # "That Was Almost 2 Years Ago..."
        ("<strong>That Was Almost 2 Years Ago, </strong></h1><h1><strong>And Fast Forward To Today And It </strong></h1><h1><strong>Almost Seems Like A Bad Dream</strong>",
         "<strong>That Was 8 Months Ago, and Fast Forward to Today</strong></h1><h1><strong>And It Almost Seems Like a Bad Dream</strong>"),
        # "I proved the idea..."
        ('<strong><span style="color: inherit">I proved the idea of "following the traditional business path" to be all wrong\u2026</span></strong></p><p></p><p><span style="color: inherit">Instead of accepting the tedious work and forcing business owners to be organized perfectionists\u2026</span></p><p></p><p><span style="color: inherit">I found the path with the least friction, the maximum leverage, and the surefire way to guarantee amazing client onboarding.</span>',
         '<strong><span style="color: inherit">I proved that the idea of "following the traditional weight loss path" was completely wrong...</span></strong></p><p></p><p><span style="color: inherit">Instead of spending hours at the gym and counting calories,</span></p><p></p><p><span style="color: inherit">I apply the Neutral Basal System according to a simple protocol and live my life normally.</span></p><p></p><p><span style="color: inherit">I went from 89 kilos to 76.3 kilos.</span></p><p></p><p><span style="color: inherit">I have my social life intact.</span>'),
        # "Chatting with friends..."
        ("Chatting with friends and writing this copy you're reading.",
         "Unlike other people in fitness who spend their time calculating their macros and preparing tupperware,"),
        ("Our clients who installed the 1CCO System focus on working ON the business and not IN the business because they understand that their time is worth a lot.</p><p><br>Unlike other coaches and agencies who still do the tedious work and are \"business owned\".</p><p></p><p>You see these coaches and agencies will spend most of their time stressed and busy because they can only rely on themselves.</p><p></p><p>My clients, like John, did this for years, and it not only drove him crazy\u2026</p><p></p><p>It drove him to the point where he wished he didn't have to run this business, and he wished he went back to a normal 9-5 so that he had some sort of freedom.\u00a0</p><p></p><p>Instead of celebrating the new clients, he was miserable and was looking for a way out.",
         "You see, these people end up spending all their free time managing their weight loss.</p><p></p><p>I did that for years, and not only did it drive me crazy...</p><p></p><p>It led me to the point where I was getting the opposite of the result I wanted.</p><p></p><p>Instead of losing weight easily, I was constantly at war with my body."),
        # "Wanna Know What The Main Difference..."
        ("<strong>Wanna Know What The Main Difference Is With The 1 Click Client Onboarding Install Pack And That \"Old Way\" Of Doing Things?</strong>",
         "<strong>Do You Want to Know What the Main Difference Is With the Neutral Basal System Model and This \"Old Way\" of Doing Things?</strong>"),
        # "I rely on a simple Form..."
        ("<strong>I rely on a simple Form, instead of adding complexity with processes and expensive software.</strong>",
         "<strong>I work WITH my basal metabolism instead of fighting it.</strong>"),
        # "Rather than doing all those things..."
        ("Rather than doing all those things I mentioned above in order to have an amazing client onboarding experience, here's what it looks like now...",
         "Rather than doing all those things I mentioned above to lose weight, here's what it looks like now...</p><p></p><p>I activate the Neutral Basal System according to the protocol. The rest of the time, I live normally."),
        # "And The Result Of Using This New Way?"
        # This one is already a heading, keep it
        # "Which Naturally Leads To..."
        ("Taking you from doing manual tasks to automating the most important part of your business\u2026",
         "I get a confidence in myself that I never had regarding controlling my weight."),
        # Long paragraph about profits and scaling
        ("And because it's automated, you get to watch your profits &amp; margins go up, instead of hiring for bandaid solutions.</p><p></p><p>As a result of that, you wake up every morning with a confident smile, instead of opening your Slack just to get sick to your stomach.</p><p></p><p>Because your clients control the direction of your business every single day...</p><p></p><p>How far you can scale, how much trust you have in the market, which products you can launch\u2026</p><p></p><p>the list goes on...</p><p></p><p>...The future of your business literally depends on your clients' success \u2026</p><p></p><p>And that's why...</p><p></p><p>Just the past few months I have received dozens of messages from clients who have successfully doubled their business because they have doubled their capacity and\u00a0 clients stick with them.</p><p></p><p>That fills my heart with love and joy because I know what it's like firsthand to go through hard times and struggle with a mediocre business that owns you.</p><p></p><p>The really cool thing is that\u2026</p><p></p><p><strong>If you install this system step by step, you end up with a highly leveraged business...</strong></p><p></p><p>But it's much more than that...",
         "And the best part is I know I can maintain these results for life.</p><p></p><p>The really cool thing is that...</p><p></p><p><strong>If you follow every step I teach, you end up with the same transformation...</strong></p><p></p><p>But it's much more than that..."),
        # "It's Actually The Only Way..."
        ("<strong>It's Actually The Only Way To Create </strong></h1><h1><strong>A Business Machine That Does </strong></h1><h1><strong>The Heavy Lifting For You</strong>",
         "<strong>It's Actually a New Perspective on How Your Relationship</strong></h1><h1><strong>with Your Body Will Change Forever...</strong>"),
        # "How many client onboarding models..."
        ("How many client onboarding models have you seen come and go through the years?",
         "How many weight loss methods have you seen come and go over the years?"),
        # Bullet points about old methods
        ("\u27a8   Forcing Sales Reps to do admin work",
         "People try hypocaloric diets..."),
        ("\u27a8  Or completely removing the client interactions so they sold a course or info product...",
         "Or intensive cardio programs..."),
        ("\u27a8  Or they hired a lot of Virtual Assistants that did all tasks manually...",
         "Or unstructured extreme fasting..."),
        # "My 1 Click Client Onboarding Install Pack has been working..."
        ("My 1 Click Client Onboarding Install Pack has been working for 50+ online businesses making 7 figures and hundreds more who learned from us.</p><p></p><p>Now, speaking of the install pack...</p><p></p><p>I'm going to share something that's a little bit disturbing with you.</p><p></p><p>Here it goes:</p><p></p><p>I am hurting our profits by showing you this.</p><p></p><p>And the other gurus out there are making loads of money by telling you to spend $10,000+ to get access to their systems (except they don't work).",
         "My results with the Neutral Basal System have lasted for 8 months now.</p><p></p><p>Now, speaking of the model...</p><p></p><p>I'm going to share something a little disturbing with you.</p><p></p><p>Here it is:</p><p></p><p>I'm hurting the fitness industry by showing you this.</p><p></p><p>And other \"experts\" out there make tons of money teaching the opposite of what I teach (except it doesn't work)."),
        # "The #1 Mistake Everyone Else Makes..."
        ("<strong>The #1 Mistake Everyone Else Makes Is Forcing Themselves Or Their Team To Turn Into Admin Robots Instead Of Adding Leverage To Their Business</strong>",
         "<strong>Mistake #1 That Everyone Makes is Believing You Have to Suffer to Lose Weight</strong>"),
        # "There are two types..."
        ("There are the \"Unleveraged\"\u00a0 and there are \"Leveraged\" ones.</p><p></p><p>For the first years, John was Unleveraged.</p><p></p><p>The Unleveraged coaches and agencies are always out there onboarding clients manually, involving themselves in every aspect of the business, and overall spreading themselves thin with low-leverage activities.</p><p><br>Their strategy is to try to control sales and client success.</p><p></p><p>And by focusing on this strategy - they spend a ton of time on...",
         "There are \"Willpower Warriors\" and there are \"Smart Optimizers\".</p><p></p><p>During my early years as an athlete - I was a Willpower Warrior.</p><p></p><p>Willpower Warriors are always there trying to force their body with more effort, more discipline, more sacrifice.</p><p><br>Their strategy is to try to dominate their physiology through mental force.</p><p></p><p>And by focusing on this strategy - they spend crazy time on..."),
        # Bullet list about unleveraged activities
        ("<ul><li><p>Working IN the business and day-to-day tasks.</p></li></ul>",
         "<ul><li><p>Counting every calorie consumed</p></li></ul>"),
        ("<ul><li><p>Being stuck on back-to-back meetings with clients.</p></li></ul>",
         "<ul><li><p>Training even when they're exhausted</p></li></ul>"),
        ("<ul><li><p>Stressing because they aren't \"productive\".</p></li></ul>",
         "<ul><li><p>Depriving themselves of all their food pleasures</p></li></ul>"),
        ("<ul><li><p>Watching others go further ahead in business while they're stagnating</p></li></ul>",
         "<ul><li><p>Feeling guilty at every \"slip-up\"</p></li></ul>"),
        ("<ul><li><p>Trying to delegate client management but having no time because their day is packed with client calls and team management</p></li></ul>",
         ""),
        # "All of this requires time and energy..."
        ("All of this requires time and energy.</h1><p></p><p>The problem isn't the model itself it's the lack of leveraged and streamlined processes that people like John can rely on.</p><p></p><p>And this is the same exact thing that happened to John before we implemented the 1 Click Client Onboarding Install Pack.",
         "All of this takes time and energy.</h1><p></p><p>The problem isn't the model itself, it's that it creates a constant war between you and your body.</p><p></p><p>And that's exactly the same thing that happened to me before I discovered the Neutral Basal System model."),
        # "The solution?" → "Become a Smart Optimizer"
        ("<strong>AN AUTOMATED WAY TO </strong></h1><h1><strong>ONBOARD CLIENTS WITHIN 1 MINUTE</strong>",
         "<strong>Become a Smart Optimizer.</strong>"),
        # "That's right...I said it..."
        ("I said it, we FULLY automate the most important part of your business so that clients get onboarded with 1 click and within a minute....</p><p></p><p>...Because I rather get the business machine to do the heavy lifting instead of business owners whose time is valuable</p><p></p><p>No thanks. Business owners used to do it before and it sucks.</p><p></p><p>So here's the deal...</p><p></p><p>...I give you everything in 1 Click Client Onboarding Install Pack, it's a simple 3-step install pack that shows you everything you need to know.",
         "I said it, we optimize our basal metabolism...</p><p></p><p>...Because I prefer getting lasting results with less effort rather than temporary results with a lot of effort.</p><p></p><p>No thanks. I did that before and it sucks.</p><p></p><p>So here's the deal...</p><p></p><p>...I explain everything in the Neutral Basal System, it's a 40-page book that shows you everything you need to know."),
    ]

    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new, 1)

    return html


def update_what_you_get(html):
    """Update what-you-get section with NBS 3-step system."""
    replacements = [
        # Section heading - "The Only System You'll Ever Need"
        ("<strong>The Only System <u>You'll Ever Need</u></strong></h1><p><strong>To Onboard Your Clients On Autopilot</strong>",
         "<strong>Here's the Exact System Revealed In the Neutral Basal System Book</strong></h1><p><strong>to Lose 2-3 Kilos Per Month</strong>"),
        # Sub-heading about "We put everything..."
        ("We put everything we've learned, everything we use ourselves in this install pack so that you can benefit from all time, effort, and money that went into creating the automated client onboarding system.",
         "All of this is revealed in the 40-page Neutral Basal System book with step-by-step details."),
        # "Here's Everything Else You're Getting..."
        ("<strong>Here's <u>Everything Else You're Getting</u> With Your 1 Click Client Onboarding Install Pack For Only $47.00</strong>",
         "<strong>Here's <u>Everything Else You're Getting</u> With Your Neutral Basal System Book For Only $29</strong>"),
        # "Check Out The Step-By-Step Video Demo"
        ("<strong>Check Out The <u>Step-By-Step Video Demo</u></strong></h1><p><strong>Of How The 1 Click Client Onboarding Works...</strong>",
         "<strong>Step 1</strong> - Understand your basal metabolism and how to optimize it</h1><p><strong>Step 2</strong> - Set up the Neutral Basal System protocol</p><p><strong>Step 3</strong> - Track your progress with the right indicators"),
        # Testimonials heading
        ("<strong>Here's <u>What A Few Member Have To Say</u> About</strong></h1><h1><strong>Using The 1 Click Client Onboarding...</strong>",
         "<strong>Making this a counter-intuitive approach to weight loss</strong></h1><h1><strong>for the person seeking freedom and simplicity.</strong>"),
    ]
    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new, 1)
    return html


def update_also_getting(html):
    """Update also-getting section with NBS 'also discover' items."""
    # The also-getting section heading is within the value-prop body area
    # We need to find and replace content in the remaining sections
    replacements = [
        # The "also getting" content is spread through the value-prop section
        # which we're removing. For NBS, we keep the structure but the content
        # will be in the sales letter flow.
    ]
    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new, 1)
    return html


def update_bonuses(html):
    """Update bonuses section with NBS bonuses."""
    replacements = [
        ('7 BONUSES INCLUDED TODAY', '10 BONUSES INCLUDED TODAY'),
    ]
    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new)
    return html


def update_guarantee(html):
    """Update guarantee section with NBS text."""
    replacements = [
        ('30 Day Money Back Guarantee', '30 Day Money Back Guarantee'),
        ('BACKED BY OUR UNCONDITIONAL', 'BACKED BY OUR UNCONDITIONAL'),
        ('Backed By Our Unconditional', 'Backed By Our Unconditional'),
    ]
    for old, new in replacements:
        if old != new and old in html:
            html = html.replace(old, new)
    return html


def update_sticky_sidebar(html):
    """Update sticky sidebar with NBS pricing."""
    # The sticky sidebar button text is already handled by update_pricing
    # and update_cta_button_text
    return html


def update_footer(html):
    """Update footer with NBS branding."""
    replacements = [
        ('8 Figure Systems', 'Neutral Basal System'),
        ('Katie Bani', 'Kele Diabat\u00e9'),
        ('1 Click Client Onboarding', 'Neutral Basal System'),
        ('1CCO', 'NBS'),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
    return html


def update_email_form(html):
    """Remove the GHL email opt-in iframe (NBS doesn't use GHL)."""
    # Replace iframe with a simple placeholder
    count = 0
    while 'JfoVUQbTOONUDr9Jraq7' in html:
        # Find and remove the iframe
        iframe_pattern = r'<iframe[^>]*JfoVUQbTOONUDr9Jraq7[^>]*>[^<]*</iframe>'
        html, n = re.subn(iframe_pattern, '', html)
        if n == 0:
            # Try self-closing
            iframe_pattern = r'<iframe[^>]*JfoVUQbTOONUDr9Jraq7[^>]*/>'
            html, n = re.subn(iframe_pattern, '', html)
        if n == 0:
            break
        count += n

    print(f"  Removed {count} GHL email opt-in iframes")
    return html


def update_meta_tags(html):
    """Update meta title, description, and keywords for NBS."""
    replacements = [
        # Meta title
        ('content="1 Click Onboarding Install Pack"',
         'content="Neutral Basal System | Lose 2-3kg/Month Sustainably"'),
        ('content="1 Click Onboarding Book"',
         'content="Neutral Basal System | Lose 2-3kg/Month Sustainably"'),
        # Meta description (og and name)
        ('Effortlessly streamline weight loss with our step-by-step process. Our Automated 1 Click Onboarding System come with the Onboarding Form (The exact amount of information you need to fully streamline client delivery), the 7 Figure Analysis, the Feedback Framework, the Client CRM, the Client Analytics, the Client Delivery Materials, the Onboarding Call Mastery.',
         'New book reveals a counter-intuitive approach that helps you lose 2-3kg per month sustainably. Without exercise, without dieting, without counting calories. The Neutral Basal System by Kele Diabat\u00e9.'),
        # Keywords
        ('automated onboarding, weight loss, onboarding automation, onboarding, onboarding form, onboarding template, onboarding sop, onboarding process, onboarding call, onboarding closer, onboarding materials, onboarding framework',
         'weight loss, sustainable weight loss, lose weight without exercise, neutral basal system, basal metabolism, lose 2-3kg per month, no diet weight loss'),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  Meta: replaced '{old[:50]}...'")
    return html


def update_sticky_pricing(html):
    """Fix sticky sidebar pricing that wasn't caught by generic replacements."""
    replacements = [
        # Sticky sidebar hidden price line
        ('<s style="opacity:0.7;">$297</s> &nbsp;$47 Today',
         '<s style="opacity:0.7;">$97</s> &nbsp;$29 Today'),
        # Right column price display
        ('<strong>Only <s>$297</s> $47.00 Today</strong>',
         '<strong>Only <s>$97</s> $29 Today</strong>'),
        # Save text in sticky
        ('(Save $250.00 today)',
         '(Save $68 today)'),
        # Sticky Install Now → Download Now
        ('>Install Now</div>',
         '>Download Now</div>'),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  Sticky: '{old[:50]}...' → '{new[:50]}...'")
    return html


def update_guarantee_text(html):
    """Fix guarantee section text for NBS."""
    replacements = [
        # Price in guarantee text
        ("it's only $47.00", "it's only $29"),
        # "install it" → "implement it"
        ("Download the Book, but more importantly install it.",
         "Download the book, read it, but more importantly apply what you learn in it."),
        # "shoot us an email" already uses the right email
        # Guarantee footer disclaimer pricing
        ("the 1 Click Onboarding product ($47)",
         "the Neutral Basal System book ($29)"),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  Guarantee: '{old[:50]}...' → '{new[:50]}...'")
    return html


def update_what_you_get_price(html):
    """Fix what-you-get section price heading."""
    replacements = [
        ("HERE'S EVERYTHING YOU'RE GETTING INSTANT ACCESS TO TODAY FOR ONLY $47.00",
         "HERE'S EVERYTHING YOU'RE GETTING INSTANT ACCESS TO TODAY FOR ONLY $29"),
    ]
    for old, new in replacements:
        if old in html:
            html = html.replace(old, new)
            print(f"  WYG price: replaced")
    return html


def update_remaining_pricing(html):
    """Catch any remaining $47 or $297 references that slipped through."""
    import re as _re
    replacements = [
        # Sidebar price headings
        ('<h1><strong>$47.00</strong></h1>', '<h1><strong>$29</strong></h1>'),
        # Various "for Just $47.00" patterns
        ('For Just $47.00', 'For Just $29'),
        ('for Just $47.00', 'for Just $29'),
        ('for $47.00', 'for $29'),
        ('for only $47.00', 'for only $29'),
        # "Save $250.00 today" in sidebar
        ('Save $250.00 today', 'Save $68 today'),
        # "Install Pack" that became "NBS Install Pack"
        ('NBS INSTALL PACK FOR ONLY $47.00', 'NEUTRAL BASAL SYSTEM BOOK FOR ONLY $29'),
        ('NBS Install Pack', 'Neutral Basal System Book'),
        ('NBS book', 'Neutral Basal System book'),
        # Even though $47.00 → $29 generic
        ("it's only $47.00", "it's only $29"),
        ('only $47.00', 'only $29'),
        ('$47.00', '$29'),
        # $297 if any remain
        ('$297', '$97'),
        # "and 7 more BONUSES"
        ('and 7 more BONUSES', 'and 10 more BONUSES'),
        # "Install Now" button labels that might remain
        ('>Install NOw</div>', '>Download Now</div>'),
        ('>Install Now</div>', '>Download Now</div>'),
        # "Start automating" → "Start reading"
        ('Start automating in the next 2 minutes', 'Start reading in the next 2 minutes'),
        # "Now Available For Quick Install"
        ('Now Available For Quick Install', 'Now Available For Instant Download'),
        # P.S. text
        ("we'll refund you your $29.", "we'll refund your $29."),
        # "7 Figure" references that should stay as is (they're part of old content we haven't fully swapped yet)
        ('Install the Neutral Basal System Book', 'Download the Neutral Basal System Book'),
        ('Install Neutral Basal System', 'Download Neutral Basal System'),
        ('And Before You Install The Neutral Basal System', 'And Before You Download the Neutral Basal System'),
    ]
    for old, new in replacements:
        if old in html:
            count = html.count(old)
            html = html.replace(old, new)
            if count > 0:
                print(f"  Final pricing: '{old[:50]}' → '{new[:50]}' ({count}x)")
    return html


def update_remaining_1cco_references(html):
    """Catch any remaining 1CCO-specific references."""
    replacements = [
        # Product name references (most specific first)
        ('1 Click Client Onboarding Install Pack', 'Neutral Basal System Book'),
        ('1 Click Client Onboarding', 'Neutral Basal System'),
        ('1-Click Client Onboarding', 'Neutral Basal System'),
        ('1CCO System', 'Neutral Basal System'),
        ('1CCO', 'NBS'),
        ('Install Pack', 'Book'),
        ('install pack', 'book'),
        ('the pack', 'the book'),
        ('The Pack', 'The Book'),
        ('client onboarding', 'weight loss'),
        ('Client Onboarding', 'Weight Loss'),
        ('CLIENT ONBOARDING', 'WEIGHT LOSS'),
        # Katie → Kele references missed by update_sales_letter
        ('Katie &amp; her team', 'Kele'),
        ('Katie', 'Kele'),
        # "John" business narrative → NBS-appropriate narrative
        ("John's systems were fully streamlined", "his metabolism was fully optimized"),
        ("John's", "his"),
        ('John followed my direction', 'he followed my direction'),
        ('John knew how', 'He knew how'),
        ("with John completely changed", "with this system completely changed"),
        ("Today, we laugh together thinking about the old times", "Today, looking back at those early struggles"),
        ('John,', 'a close friend,'),
        (' John ', ' he '),
        # Business-specific terms → weight loss terms
        ('onboarding clients to my service', 'losing weight sustainably'),
        ('onboarding clients', 'losing weight'),
        ('onboard a client', 'deal with my weight'),
        ('onboard and serve', 'transform'),
        ('onboarding a client', 'losing weight'),
        ('Onboarding', 'Weight Loss'),
        ('onboarding', 'weight loss'),
        # COO/consulting → personal story
        ('COO role', 'comfort zone'),
        ('COO', 'manager'),
        ('consulting firm', 'company'),
        # Agency/coaching business terms
        ('coaches and agencies', 'people'),
        ('coaching business', 'health goals'),
        ('agency', 'journey'),
        ('agencies', 'people'),
        # Tech stack
        ('Google Sheets', 'basic calorie counting'),
        ('Zapier', 'generic diet apps'),
        ('tech stack', 'approach'),
        # CRM/SOP business terms
        ('NBS System', 'Neutral Basal System'),
        ('CRM', 'system'),
        ('SOP model', 'approach'),
        ('SOP', 'protocol'),
        # Business operations → weight loss
        ('admin work', 'frustration'),
        ('client churn', 'yo-yo dieting'),
        ('recurring revenue', 'progress'),
        ('tedious tasks', 'painful restrictions'),
        ('tedious onboarding tasks', 'painful restrictions'),
        ('tedious work', 'painful restrictions'),
        ('working ON the business and not IN the business', 'working WITH their body instead of against it'),
        ('closing clients and not admin work', 'living your life without obsessing over food'),
        # 7-figure references
        ("7-Figure Business", "Transformation"),
        ('7 Figures', 'their ideal weight'),
        ('7 Figure', 'Transformation'),
        ('7 figures', 'their goals'),
        ('multiple 7 figures', 'incredible results'),
        ('multiple 6 figures', 'real results'),
        # Client-specific
        ('Feedback Pack', 'Progress Tracker'),
        ('installed the NBS', 'used the NBS'),
        ('installed the Neutral Basal System', 'used the Neutral Basal System'),
        # Business owner references → person struggling with weight
        ('business owner', 'person'),
        ('business owners', 'people'),
        # Remaining "Install pack in module" headings (case-sensitive lowercase p)
        ('Install pack in module', 'Content in chapter'),
        # Meta description "1 Click" references
        ('Automated 1 Click Weight Loss System', 'Neutral Basal System'),
        ('1 Click Weight Loss', 'Neutral Basal System'),
        ('1 Click', 'Neutral Basal'),
        # Business-specific content in sales letter body
        ('sales report form', 'simple protocol'),
        ('client materials, Client system, and finance tracker', 'tracking tools and daily protocol'),
        ('Client system', 'tracking system'),
        ('client materials', 'daily protocol'),
        ('Client Delivery Materials', 'Daily Protocol Guide'),
        ('Weight Loss Call Mastery', 'Metabolism Optimization Guide'),
        ('Feedback Framework', 'Progress Framework'),
        ('Transformation Analysis', 'Body Composition Analysis'),
        ('closing clients', 'achieving results'),
        ('your team', 'your body'),
        # "onboard clients" patterns still present
        ('onboard clients', 'lose weight'),
        ('streamline client delivery', 'streamline your weight loss'),
        ('streamline client success', 'streamline your health journey'),
        ('streamline client', 'streamline weight loss'),
        ('client delivery', 'your health journey'),
        ('client satisfaction', 'your progress'),
        # Footer/branding
        ('7-Figure Systems', 'Neutral Basal System'),
        ('1clickweight loss.com', 'neutralbasalsystem.com'),
        ('1clickweight loss', 'neutralbasalsystem'),
        # Case study names → generic testimonial refs
        ('Bastiaan Slot', 'our readers'),
        ('Bastiaan', 'Reader A'),
        ('Franck Koomen', 'Reader B'),
        ('Franck', 'Reader B'),
        ('Yoon Kim', 'Reader C'),
        ('Yoon', 'Reader C'),
        ('Meghan Wieske', 'Reader D'),
        ('Meghan', 'Reader D'),
        ('Daphne Kroeze', 'Reader E'),
        ('Daphne', 'Reader E'),
        ('Serge Gatari', 'Reader F'),
        ('Serge', 'Reader F'),
        ('Agus Nievas', 'Reader G'),
        ('Agus', 'Reader G'),
        # Tech references in FAQ
        ('Google Form', 'a simple tracking sheet'),
        ('PandaDoc Business Plan', 'basic meal planning'),
        ('PandaDoc', 'a meal planner'),
        # "install it" in context of book
        ('importantly install it', 'importantly apply it'),
        ('install in your business in just 30 minutes', 'implement in just a few hours'),
    ]
    for old, new in replacements:
        if old in html:
            before = html.count(old)
            html = html.replace(old, new)
            print(f"  Remaining refs: '{old}' → '{new}' ({before} occurrences)")
    return html


def main():
    print("=== Creating NBS product page ===\n")

    print("1. Reading template...")
    html = read_file(INPUT_FILE)
    print(f"   Read {len(html):,} chars from index.html\n")

    print("2. Updating title...")
    html = update_title(html)
    print()

    print("3. Removing sections...")
    for section_id in ['section-value-prop', 'section-hormozi-quote', 'section-sneak-peek']:
        html = remove_section(html, section_id)
    print()

    print("4. Updating hero section...")
    html = update_hero_section(html)
    print()

    print("5. Updating sales letter...")
    html = update_sales_letter(html)
    print()

    print("6. Updating what-you-get section...")
    html = update_what_you_get(html)
    print()

    print("7. Updating bonuses...")
    html = update_bonuses(html)
    print()

    print("8. Updating pricing...")
    html = update_pricing(html)
    print()

    print("9. Updating CTA links...")
    html = update_cta_links(html)
    print()

    print("10. Updating CTA button text...")
    html = update_cta_button_text(html)
    print()

    print("11. Updating top bar...")
    html = update_top_bar(html)
    print()

    print("12. Removing email opt-in forms...")
    html = update_email_form(html)
    print()

    print("13. Updating footer...")
    html = update_footer(html)
    print()

    print("14. Updating meta tags...")
    html = update_meta_tags(html)
    print()

    print("15. Updating sticky sidebar pricing...")
    html = update_sticky_pricing(html)
    print()

    print("16. Updating guarantee text...")
    html = update_guarantee_text(html)
    print()

    print("17. Updating what-you-get price...")
    html = update_what_you_get_price(html)
    print()

    print("18. Catching remaining pricing references...")
    html = update_remaining_pricing(html)
    print()

    print("19. Replacing images with placeholders...")
    html = replace_images_with_placeholders(html)
    html = replace_background_images_with_placeholders(html)
    print()

    print("20. Catching remaining 1CCO references...")
    html = update_remaining_1cco_references(html)
    print()

    print("21. Writing output...")
    write_file(OUTPUT_FILE, html)
    print(f"   Wrote {len(html):,} chars to nbs.html\n")

    print("=== Done! ===")
    print(f"   Original: {os.path.getsize(INPUT_FILE):,} bytes")
    print(f"   NBS page: {os.path.getsize(OUTPUT_FILE):,} bytes")


if __name__ == '__main__':
    main()
