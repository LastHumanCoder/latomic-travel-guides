#!/usr/bin/env python3
"""Build the Latomic travel-agency AI-search guides into self-contained pages in dist/.

Each src/<slug>.html is a frontmatter comment + the page's <main> body. Author icons as
`<i data-i="name"></i>` (shared/icons/lucide/) or `<i data-logo="name"></i>` (shared/icons/);
they are inlined at build time. The shared stylesheet (shared/base.css), nav and footer are
injected, so every dist page is standalone (only Google Fonts is external) and drops onto
GitHub Pages or opens straight from disk.

  python3 build.py            # build all
  python3 build.py <slug>     # build one
"""
import re, sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SRC, DIST, ICONS = ROOT/"src", ROOT/"dist", ROOT/"shared"/"icons"
CSS = (ROOT/"shared"/"base.css").read_text()
WA = "https://wa.me/"  # placeholder; set the real number before launch

NAV = '''<header class="nav"><div class="nav-in">
<a href="index.html" class="brand" aria-label="Latomic home">lat<svg class="o" viewBox="0 0 24 24" aria-hidden="true"><circle class="ring" cx="12" cy="12" r="9.4"/><g class="e"><circle cx="12" cy="1.6" r="3.2" fill="#FF5A3C"/></g></svg>mic</a>
<nav class="nav-links" aria-label="Main"><a href="index.html">Guides</a><a href="#plan">Check your agency</a><a href="#faq">FAQ</a></nav>
<a href="#plan" class="btn">Get a free growth plan</a></div></header>'''

FOOTER = '''<footer><div class="wrap foot">
<div class="brand" style="font-size:20px">lat<svg class="o" viewBox="0 0 24 24" aria-hidden="true" style="width:.72em;height:.72em;margin:.1em .02em 0"><circle class="ring" cx="12" cy="12" r="9.4"/><g class="e"><circle cx="12" cy="1.6" r="3.2" fill="#FF5A3C"/></g></svg>mic · the growth team for travel agencies</div>
<nav><a href="index.html">Guides</a><a href="#plan">Get started</a><a href="''' + WA + '''">WhatsApp</a></nav></div>
<div class="wrap"><p class="disc">Latomic helps travel agencies and tour operators get found by customers across Google, ChatGPT and other AI assistants. Guides are informational and reflect platform behaviour that changes often; verify against the linked sources. Not affiliated with OpenAI.</p></div></footer>'''

LEAD = '''<section class="leadsec" id="plan"><div class="kicker">Free growth plan</div>
<h2>See how ChatGPT describes your agency today</h2>
<p>Drop your website, Instagram or Google profile and we will send back what the assistants say about you now, and the three things that would move you up.</p>
<form class="lead-box" onsubmit="return false"><label><small>Your website, Instagram or Google profile</small><input name="website" type="text" inputmode="url" placeholder="youragency.com" aria-label="Your website, Instagram or Google profile"></label>
<button type="submit" class="btn coral">Get my free growth plan <i data-i="arrow-right"></i></button></form>
<div class="lead-micro"><span><i data-i="check"></i>Free plan in 24 hours</span><span><i data-i="check"></i>Everything included</span><span><i data-i="check"></i>No contract</span></div></section>'''

def svg(path, cls):
    s = path.read_text()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<title>.*?</title>", "", s)
    s = re.sub(r'\s(class|width|height|role)="[^"]*"', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace("<svg", f'<svg class="{cls}" aria-hidden="true" focusable="false"', 1)

def icons(html):
    html = re.sub(r'<i data-i="([\w-]+)"></i>', lambda m: svg(ICONS/"lucide"/f"{m.group(1)}.svg", "ic"), html)
    html = re.sub(r'<i data-logo="([\w-]+)"></i>', lambda m: svg(ICONS/f"{m.group(1)}.svg", "logo"), html)
    return html

def frontmatter(raw):
    m = re.search(r"<!--\s*(.*?)\s*-->", raw, re.S)
    fm = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line:
            k, v = line.split(":", 1); fm[k.strip()] = v.strip()
    body = raw[m.end():] if m else raw
    return fm, body

def page(slug, fm, body):
    title = fm.get("title", slug)
    desc = fm.get("desc", "")
    html = f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} · Latomic</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#FBFAF7">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{NAV}
{body.strip()}
{LEAD}
{FOOTER}
</body></html>'''
    return icons(html)

INDEX_CARDS = []  # filled during build for the hub

def build_one(p):
    fm, body = frontmatter(p.read_text())
    out = page(p.stem, fm, body)
    (DIST/f"{p.stem}.html").write_text(out)
    INDEX_CARDS.append((p.stem, fm))
    return fm

def build_index():
    cards = ""
    order = ["chatgpt-business-profile-for-travel-agencies","get-your-travel-agency-recommended-by-chatgpt",
             "why-isnt-my-travel-agency-showing-up-in-chatgpt","how-to-claim-your-travel-agency-in-chatgpt",
             "make-your-travel-website-visible-to-ai","chatgpt-business-listing-requirements-travel-agencies",
             "chatgpt-business-hub-for-travel-agencies","chatgpt-business-agent-for-travel-agencies",
             "chatgpt-vs-google-business-profile-travel-agencies"]
    by = {s: fm for s, fm in INDEX_CARDS}
    for s in order:
        if s not in by: continue
        fm = by[s]
        cards += (f'<a href="{s}.html"><span class="k">{fm.get("kind","Guide")}</span>'
                  f'<b>{fm.get("card", fm.get("title",""))}</b>'
                  f'<span>Read <i data-i="arrow-right"></i></span></a>')
    html = f'''<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI search guides for travel agencies · Latomic</title>
<meta name="description" content="How travel agencies and tour operators get found in ChatGPT, Google and other AI assistants. Plain guides from Latomic, the growth team for travel agencies.">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#FBFAF7">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{NAV}
<main class="wrap art">
<div class="art-head"><span class="eyebrow"><span class="pulse"></span>AI search · for travel agencies</span>
<h1>Get your travel agency found in ChatGPT &amp; AI search</h1>
<p class="lede">Travelers now ask AI assistants who to book with. These are plain, no-jargon guides for travel agencies and tour operators on getting named, claimed and recommended, from Latomic, the growth team for travel agencies.</p></div>
<div class="rel" style="margin-top:26px">{cards}</div>
</main>
{LEAD}
{FOOTER}
</body></html>'''
    (DIST/"index.html").write_text(icons(html))

def main(only):
    DIST.mkdir(exist_ok=True)
    srcs = sorted(SRC.glob("*.html"))
    for p in srcs:
        if only and p.stem not in only: continue
        fm = build_one(p)
        print(f"  built dist/{p.stem}.html  ({fm.get('title','?')[:50]})")
    # index needs all cards; build from every src regardless of filter
    if not only:
        build_index(); print("  built dist/index.html")

if __name__ == "__main__":
    main(set(sys.argv[1:]))
