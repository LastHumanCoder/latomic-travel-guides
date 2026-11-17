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
import re, sys, json, pathlib, shutil

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

XSVG = '<svg class="logo" viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
LISVG = '<svg class="logo" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'
FBSVG = '<svg class="logo" viewBox="0 0 24 24" aria-hidden="true"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>'

RAIL = f'''<aside class="share-rail" aria-label="Share this guide">
<span class="sr-label">Share</span>
<a class="sr-btn x" data-share="x" href="#" aria-label="Share on X">{XSVG}</a>
<a class="sr-btn li" data-share="li" href="#" aria-label="Share on LinkedIn">{LISVG}</a>
<a class="sr-btn fb" data-share="fb" href="#" aria-label="Share on Facebook">{FBSVG}</a>
<a class="sr-btn wa" data-share="wa" href="#" aria-label="Share on WhatsApp"><i data-logo="whatsapp"></i></a>
<button class="sr-btn copy" data-share="copy" type="button" aria-label="Copy link"><i data-i="link"></i></button>
</aside>'''

SHARE_JS = '''<script>(function(){var u=encodeURIComponent(location.href),t=encodeURIComponent(document.title);
var m={x:'https://twitter.com/intent/tweet?url='+u+'&text='+t,li:'https://www.linkedin.com/sharing/share-offsite/?url='+u,
fb:'https://www.facebook.com/sharer/sharer.php?u='+u,wa:'https://wa.me/?text='+t+'%20'+u};
document.querySelectorAll('.sr-btn[data-share]').forEach(function(b){var k=b.getAttribute('data-share');
if(m[k]){b.href=m[k];b.target='_blank';b.rel='noopener';}
if(k==='copy'){b.addEventListener('click',function(){navigator.clipboard&&navigator.clipboard.writeText(location.href);b.classList.add('done');setTimeout(function(){b.classList.remove('done')},1200);});}});})();</script>'''

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
    # hero cover image under the title, if one exists for this slug
    if (ROOT/"covers"/f"{slug}.webp").exists():
        fig = f'<figure class="cover"><img src="covers/{slug}.webp" alt="" loading="eager" width="1200" height="658"></figure>'
        body = re.sub(r'(class="lede"[^>]*>.*?</p>\s*</div>)', lambda m: m.group(1)+"\n"+fig, body, count=1, flags=re.S)
    # make the Key insights box collapsible (title visible, bullets behind an Expand toggle)
    body = re.sub(
        r'<div class="insights">\s*<div class="kicker">(.*?)</div>\s*(<ul>.*?</ul>)\s*</div>',
        lambda m: ('<div class="insights"><div class="ins-h">'+m.group(1)+'</div>'
                   '<details class="ins-d"><summary><span class="s-c">Expand key insights</span>'
                   '<span class="s-o">Hide key insights</span></summary>'+m.group(2)+'</details></div>'),
        body, count=1, flags=re.S)
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
{RAIL}
{body.strip()}
{LEAD}
{FOOTER}
{SHARE_JS}
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
             "chatgpt-vs-google-business-profile-travel-agencies",
             "does-chatgpt-recommend-hotels-and-travel-businesses","will-ai-replace-travel-agents",
             "how-to-get-travel-agency-leads-from-chatgpt-and-ai-search"]
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
    if (ROOT/"covers").exists():
        shutil.copytree(ROOT/"covers", DIST/"covers", dirs_exist_ok=True)
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
