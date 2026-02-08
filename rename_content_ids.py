#!/usr/bin/env python3
"""
Rename all content-level GHL elements to semantic names.
Covers: heading, sub-heading, image, video, button, divider elements.

Session #14 renamed structural IDs (section, row, col).
This script renames the remaining content-level random IDs.
"""

import re
import json
import unicodedata
from pathlib import Path

HTML_FILE = Path(__file__).parent / "index.html"
MAP_FILE = Path(__file__).parent / "content_id_map.json"


def strip_html(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', 'and', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def slugify(text: str, max_words: int = 5, max_len: int = 40) -> str:
    """Convert text to a kebab-case slug."""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    words = text.split()[:max_words]
    slug = '-'.join(words)
    return slug[:max_len].rstrip('-')


def extract_element_content(content: str, element_id: str, element_type: str) -> str:
    """Extract readable text content from an element."""
    # Find the element by ID and grab content after it
    pattern = rf'id="{re.escape(element_id)}"[^>]*>(.*?)(?:</div>|</span>)'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        return strip_html(m.group(1))[:200]

    # Fallback: just grab text after the id
    idx = content.find(f'id="{element_id}"')
    if idx >= 0:
        chunk = content[idx:idx + 600]
        return strip_html(chunk)[:200]

    return ""


def find_all_content_ids(content: str) -> dict[str, list[str]]:
    """Find all content-level GHL IDs grouped by type."""
    types = {
        'heading': r'id="(heading-[A-Za-z0-9_-]{6,})"',
        'sub-heading': r'id="(sub-heading-[A-Za-z0-9_-]{6,})"',
        'image': r'id="(image-[A-Za-z0-9_-]{6,})"',
        'video': r'id="(video-[A-Za-z0-9_-]{6,})"',
        'button': r'id="(button-[A-Za-z0-9_-]{6,})"',
        'divider': r'id="(divider-[A-Za-z0-9_-]{6,})"',
    }

    result = {}
    for typ, pattern in types.items():
        ids = sorted(set(re.findall(pattern, content)))
        # Skip _btn suffixed variants (they derive from the base button ID)
        if typ == 'button':
            ids = [i for i in ids if not i.endswith('_btn')]
        if typ == 'divider':
            ids = [i for i in ids if not i.endswith('-divider-inner')]
        result[typ] = ids
    return result


def generate_heading_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for a heading element."""
    text = extract_element_content(content, element_id, 'heading')

    # Map known headings to specific names
    known = {
        'Dear Future 1 Click Client Onboarding': 'dear-future-owner',
        'Before we created the 1 Click': 'before-we-created',
        'Every business scales': 'every-business-scales',
        'So we decided to find': 'decided-find-better-way',
        'After several months': 'after-several-months',
        'Now, you have the opportunity': 'opportunity-to-duplicate',
        'See below to learn how it works': 'see-below-how-it-works',
        'This Is Serge': 'case-serge',
        'Splash CEO': 'case-splash',
        'This is Bastiaan': 'case-bastiaan',
        'Yoon Kim': 'case-yoon',
        'Megan Walsh': 'case-megan',
        'Mehdi': 'case-mehdi',
        'Ben Fewtrell': 'case-ben',
        'Franck Drouhin': 'case-franck',
        'Dominic': 'case-dominic',
        'Here\'s a sneak peek': 'sneak-peek',
        'Check Out The Step-By-Step Video Demo': 'video-demo-heading',
        'Here\'s What A Few Member': 'testimonials-heading',
        'The #1 Mistake Everyone': 'number-one-mistake',
        'And The Result Of Using This New Way': 'result-new-way',
        'And Just A Few Years Ago': 'few-years-ago',
        'But before you do': 'before-you-do-intro',
        'I\'ll talk to you in our private Community': 'talk-in-community',
        'The 1CCO System was the perfect thing': 'perfect-for-clients',
        'In fact: we rarely': 'rarely-build-without-knowing',
        'Right now, as you\'re reading': 'right-now-reading',
        'Track upcoming and finances': 'track-finances',
        'Bridge the communication': 'bridge-communication',
        'You Don\'t Even Have To Keep Track Of Payment': 'no-payment-tracking',
        'And the best part that attracted me': 'best-part-attracted',
        'it took me 4 years': 'took-4-years',
        'Step 1': 'step-1',
        'Step 2': 'step-2',
        'Step 3': 'step-3',
        'Step 4': 'step-4',
        'Step 5': 'step-5',
        'Step 6': 'step-6',
        'Step 7': 'step-7',
        'Step 8': 'step-8',
        'Despite exploring various': 'despite-exploring',
        'Our solution was to overhaul': 'overhaul-dominic',
        'He Ended Up Stressed': 'stressed-daily',
        'All systems accessible': 'systems-accessible',
        '$47.00': 'cta-price',
        '(Save $250.00 today)': 'cta-save',
        'Install Now': 'cta-install',
        'The 1 Click Client Onboarding Install Pack is a counterintuitive': 'counterintuitive-approach',
        'This Install Pack works with all website': 'works-with-all',
        'We achieve this by finding': 'achieve-by-finding',
        'And as a result': 'frees-you-up',
    }

    for prefix, name in known.items():
        if prefix.lower() in text.lower():
            candidate = name
            if candidate in used:
                # Append a counter
                i = 2
                while f'{candidate}-{i}' in used:
                    i += 1
                candidate = f'{candidate}-{i}'
            used.add(candidate)
            return candidate

    # Auto-generate from content
    if text:
        slug = slugify(text)
        if slug and len(slug) > 3:
            candidate = slug
            if candidate in used:
                i = 2
                while f'{candidate}-{i}' in used:
                    i += 1
                candidate = f'{candidate}-{i}'
            used.add(candidate)
            return candidate

    # Fallback: numbered
    candidate = f'text-{idx}'
    used.add(candidate)
    return candidate


def generate_image_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for an image element."""
    # Find the img src
    pattern = rf'id="{re.escape(element_id)}"[^>]*>.*?<img[^>]*src="([^"]*)"'
    m = re.search(pattern, content, re.DOTALL)
    src = m.group(1) if m else ""

    # Also check for alt text
    pattern2 = rf'id="{re.escape(element_id)}"[^>]*>.*?<img[^>]*alt="([^"]*)"'
    m2 = re.search(pattern2, content, re.DOTALL)
    alt = m2.group(1) if m2 else ""

    # Try to get context from nearby headings/text
    img_idx = content.find(f'id="{element_id}"')
    context_name = ""
    if img_idx >= 0:
        before = content[max(0, img_idx - 3000):img_idx]
        # Find the nearest section
        sections = re.findall(r'id="(section-[^"]+)"', before)
        section = sections[-1].replace('section-', '') if sections else ""
        # Find nearest heading text
        headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', before, re.DOTALL)
        heading_text = strip_html(headings[-1])[:60] if headings else ""

        if section:
            context_name = section

    # Use alt text if meaningful
    if alt and len(alt) > 3:
        slug = slugify(alt)
        if slug and len(slug) > 3:
            candidate = slug
            if candidate in used:
                i = 2
                while f'{candidate}-{i}' in used:
                    i += 1
                candidate = f'{candidate}-{i}'
            used.add(candidate)
            return candidate

    # Use section context + position
    if context_name:
        candidate = context_name
        if candidate in used:
            i = 2
            while f'{candidate}-{i}' in used:
                i += 1
            candidate = f'{candidate}-{i}'
        used.add(candidate)
        return candidate

    candidate = f'img-{idx}'
    used.add(candidate)
    return candidate


def generate_video_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for a video element."""
    vid_idx = content.find(f'id="{element_id}"')
    if vid_idx >= 0:
        before = content[max(0, vid_idx - 3000):vid_idx]
        after = content[vid_idx:vid_idx + 500]
        text_before = strip_html(before)[-300:].lower()
        text_after = strip_html(after)[:200].lower()
        combined = text_before + ' ' + text_after

        # Find nearest section for fallback
        sections = re.findall(r'id="(section-[^"]+)"', before)
        section = sections[-1].replace('section-', '') if sections else ""

        # Case study videos
        names_map = [
            ('serge', 'serge'), ('splash', 'splash'), ('bastiaan', 'bastiaan'),
            ('yoon', 'yoon'), ('megan', 'megan'), ('mehdi', 'mehdi'),
            ('ben fewtrell', 'ben'), ('franck', 'franck'), ('dominic', 'dominic'),
        ]
        for keyword, name in names_map:
            if keyword in combined:
                candidate = name
                if candidate in used:
                    i = 2
                    while f'{candidate}-{i}' in used:
                        i += 1
                    candidate = f'{candidate}-{i}'
                used.add(candidate)
                return candidate

        # Contextual videos
        if 'sneak peek' in combined:
            name = 'sneak-peek'
        elif 'step-by-step' in combined or 'demo' in combined:
            name = 'demo'
        elif 'hero' in section or 'shortcut' in combined or 'automating' in combined:
            name = 'hero'
        elif section:
            name = section
        else:
            name = f'vid-{idx}'

        if name in used:
            i = 2
            while f'{name}-{i}' in used:
                i += 1
            name = f'{name}-{i}'
        used.add(name)
        return name

    candidate = f'vid-{idx}'
    used.add(candidate)
    return candidate


def generate_subheading_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for a sub-heading element."""
    text = extract_element_content(content, element_id, 'sub-heading')

    if text:
        slug = slugify(text)
        if slug and len(slug) > 3:
            candidate = slug
            if candidate in used:
                i = 2
                while f'{candidate}-{i}' in used:
                    i += 1
                candidate = f'{candidate}-{i}'
            used.add(candidate)
            return candidate

    candidate = f'subhead-{idx}'
    used.add(candidate)
    return candidate


def generate_button_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for a button element."""
    btn_idx = content.find(f'id="{element_id}"')
    if btn_idx >= 0:
        before = content[max(0, btn_idx - 3000):btn_idx]
        after = content[btn_idx:btn_idx + 500]

        # Find nearest section
        sections = re.findall(r'id="(section-[^"]+)"', before)
        section = sections[-1].replace('section-', '') if sections else ""

        # Get button text
        text = strip_html(after)[:100].lower()

        if 'install now' in text and section:
            candidate = f'cta-{section}'
        elif 'install now' in text:
            candidate = f'cta-install-{idx}'
        elif section:
            candidate = f'cta-{section}'
        else:
            candidate = f'cta-{idx}'

        if candidate in used:
            i = 2
            while f'{candidate}-{i}' in used:
                i += 1
            candidate = f'{candidate}-{i}'
        used.add(candidate)
        return candidate

    candidate = f'cta-{idx}'
    used.add(candidate)
    return candidate


def generate_divider_name(content: str, element_id: str, idx: int, used: set) -> str:
    """Generate semantic name for a divider element."""
    div_idx = content.find(f'id="{element_id}"')
    if div_idx >= 0:
        before = content[max(0, div_idx - 3000):div_idx]
        sections = re.findall(r'id="(section-[^"]+)"', before)
        if sections:
            section = sections[-1].replace('section-', '')
            candidate = section
            if candidate in used:
                i = 2
                while f'{candidate}-{i}' in used:
                    i += 1
                candidate = f'{candidate}-{i}'
            used.add(candidate)
            return candidate

    candidate = f'sep-{idx}'
    used.add(candidate)
    return candidate


def do_replacement(content: str, old_base: str, new_base: str, element_type: str) -> tuple[str, int]:
    """Replace all occurrences of an ID and its derived class names."""
    count = 0

    # The GHL pattern: id="heading-XXX" generates:
    #   - id="heading-XXX" (HTML attribute)
    #   - class="heading-XXX ..." and class="... cheading-XXX ..."
    #   - .heading-XXX and .cheading-XXX (CSS selectors)
    # For buttons: also button-XXX_btn

    old_id = old_base  # e.g., "heading-0A77P26Q7U"
    type_prefix = element_type  # e.g., "heading"
    old_suffix = old_base[len(type_prefix) + 1:]  # e.g., "0A77P26Q7U"
    new_id = f'{type_prefix}-{new_base}'  # e.g., "heading-before-we-created"

    # Replace the base ID
    c = content.count(old_id)
    if c > 0:
        content = content.replace(old_id, new_id)
        count += c

    # Replace the c-prefixed class (cheading-XXX, cimage-XXX, etc.)
    # Map type to c-prefix
    c_prefix_map = {
        'heading': 'cheading',
        'sub-heading': 'csub-heading',
        'image': 'cimage',
        'video': 'cvideo',
        'button': 'cbutton',
        'divider': 'cdivider',
    }
    c_prefix = c_prefix_map.get(type_prefix, f'c{type_prefix}')
    old_c = f'{c_prefix}-{old_suffix}'
    new_c = f'{c_prefix}-{new_base}'
    c2 = content.count(old_c)
    if c2 > 0:
        content = content.replace(old_c, new_c)
        count += c2

    return content, count


def main():
    content = HTML_FILE.read_text()
    original_len = len(content)

    all_ids = find_all_content_ids(content)
    id_map = {}
    total_replacements = 0

    # Process each type
    generators = {
        'heading': generate_heading_name,
        'sub-heading': generate_subheading_name,
        'image': generate_image_name,
        'video': generate_video_name,
        'button': generate_button_name,
        'divider': generate_divider_name,
    }

    for element_type, ids in all_ids.items():
        used_names: set[str] = set()
        gen_func = generators[element_type]
        type_count = 0

        for idx, old_id in enumerate(ids, 1):
            new_name = gen_func(content, old_id, idx, used_names)
            new_full_id = f'{element_type}-{new_name}'

            # Skip if new name would be the same
            if old_id == new_full_id:
                continue

            content, replacements = do_replacement(content, old_id, new_name, element_type)
            if replacements > 0:
                id_map[old_id] = new_full_id
                type_count += replacements
                total_replacements += replacements

        print(f'{element_type}: renamed {len([k for k in id_map if k.startswith(element_type)])} elements ({type_count} replacements)')

    # Write output
    HTML_FILE.write_text(content)
    MAP_FILE.write_text(json.dumps(id_map, indent=2, ensure_ascii=False))

    print(f'\nTotal: {len(id_map)} elements renamed, {total_replacements} replacements')
    print(f'File size: {original_len:,} → {len(content):,} bytes')
    print(f'Map saved to {MAP_FILE}')


if __name__ == '__main__':
    main()
