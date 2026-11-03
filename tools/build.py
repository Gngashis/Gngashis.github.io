#!/usr/bin/env python3
"""Static site generator for the new MyTravelExpert luxury brochure site.

Reads data/packages.json (verbatim content extracted and cross-verified from
mytravelexpert.co.in) and writes index.html, packages.html, 16 package detail
pages, about.html and contact.html.

Content rules:
- Package names, destinations, durations, itineraries, descriptions,
  inclusions, exclusions and prices are reproduced verbatim. Nothing is
  invented. Sections absent on the source site are rendered with an honest
  "available on request" note.
- Visual design (layout, palette, typography) is entirely original.
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "packages.json").read_text())
IMG = "img/packages"

CONTACT_PHONE = "+91 80012 47778"
CONTACT_PHONE_HREF = "tel:+918001247778"
CONTACT_EMAIL = "infomytravelexpert4306@gmail.com"
WA = "https://wa.me/918001247778?text=Hello%21+I+want+to+explore+bespoke+travel+packages."

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\u2B00-\u2BFF\uFE0F]+")

def esc(s): return html.escape(str(s), quote=True)

def tidy(s):
    """Strip decorative emoji and trailing punctuation artifacts for display."""
    if not s: return ""
    return EMOJI_RE.sub("", s).replace(" .", ".").strip(" .·•")

def region_of(p):
    """Derive a display region from the package name only (no invented facts)."""
    n = p["name"].upper()
    if "BHUTAN" in n: return "Bhutan"
    if "DOOARS" in n: return "Dooars"
    if "DARJEELING" in n and ("SIKKIM" in n or "ZULUK" in n or "NAMCHI" in n): return "Sikkim & Darjeeling"
    if "SIKKIM" in n: return "Sikkim"
    return "Darjeeling & Kalimpong"

def nights_label(p):
    m = re.search(r"(\d+)\s*(?:Days?)", p.get("duration") or "")
    d = m.group(1) if m else str(len(p["itinerary"]) or "")
    return f"{d} Days"

def price_num(s):
    m = re.search(r"([\d,]+)", s or "")
    return int(m.group(1).replace(",", "")) if m else 0

def img(p, suffix, i=None):
    name = f"{p['slug']}-{suffix}"
    for ext in (".webp", ".jpg", ".jpeg", ".png"):
        if (ROOT / IMG / (name + ext)).exists():
            return f"{IMG}/{name}{ext}"
    return None

# ---------------------------------------------------------------- components

def head(title, desc, extra=""):
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">{extra}"""

def header(active="", base=""):
    def a(href, label, key):
        cls = ' class="active"' if key == active else ""
        return f'<a href="{href}"{cls}>{label}</a>'
    return f"""
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <nav class="nav" aria-label="Primary">
    <a class="brand" href="index.html">My<span>Travel</span>Expert</a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="navmenu" aria-label="Open menu">
      <span></span><span></span>
    </button>
    <div class="nav-menu" id="navmenu">
      {a(f'{base}/index.html' if base else 'index.html', 'Home', 'home')}
      {a(f'{base}/packages.html' if base else 'packages.html', 'Journeys', 'packages')}
      {a(f'{base}/about.html' if base else 'about.html', 'The House', 'about')}
      {a(f'{base}/contact.html' if base else 'contact.html', 'Contact', 'contact')}
      <a class="nav-cta" href="{WA}" target="_blank" rel="noopener">Enquire</a>
    </div>
  </nav>
</header>"""

def footer(base=""):
    return f"""
<footer class="site-footer">
  <div class="foot-inner">
    <div>
      <p class="foot-brand">My<span>Travel</span>Expert</p>
      <p class="foot-note">Curated journeys across the Himalayas, Sikkim, Darjeeling, Dooars and Bhutan.</p>
    </div>
    <div class="foot-col">
      <p class="foot-h">Explore</p>
      <a href="{base}/packages.html" if base else "packages.html">All journeys</a>
      <a href="{base + '/index.html#collections' if base else 'index.html#collections'}">Collections</a>
      <a href="{base + '/about.html' if base else 'about.html'}">The House</a>
    </div>
    <div class="foot-col">
      <p class="foot-h">Speak with us</p>
      <a href="{CONTACT_PHONE_HREF}">{CONTACT_PHONE}</a>
      <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      <a href="{WA}" target="_blank" rel="noopener">WhatsApp concierge</a>
    </div>
  </div>
  <p class="foot-legal">© 2026 MyTravelExpert. All journeys are subject to availability; a travel expert confirms every detail personally.</p>
</footer>"""

def card(p, detail_href, base=""):
    hero = img(p, "hero") or (p.get("gallery") or [None])[0] or (img(p, "g1"))
    if hero and base: hero = base + "/" + hero
    alt = f"{p['name']} — {p.get('destination') or 'journey'}"
    disc = price_num(p.get("discounted_price")); orig = price_num(p.get("original_price"))
    off = round((1 - disc / orig) * 100) if orig and disc else 0
    return f"""
<article class="journey-card reveal" data-region="{esc(region_of(p))}">
  <a class="card-media" href="{base + '../packages/' + p['slug'] + '.html' if base else detail_href}" tabindex="-1" aria-hidden="true">
    <img src="{hero}" alt="{esc(alt)}" loading="lazy">
    <span class="card-region">{esc(region_of(p))}</span>
    {f'<span class="card-off">−{off}%</span>' if off else ''}
  </a>
  <div class="card-body">
    <p class="card-eyebrow">{esc(tidy(p.get('destination')) or region_of(p))}</p>
    <h3 class="card-title"><a href="{base + '../packages/' + p['slug'] + '.html' if base else detail_href}">{esc(p['name'])}</a></h3>
    <p class="card-meta">{esc(nights_label(p))} · {esc(tidy(p.get('difficulty')).replace(' Level',''))}</p>
    <div class="card-price">
      <p class="price-from">from <strong>₹{disc:,}</strong> <span>/ person</span></p>
      {f'<del>₹{orig:,}</del>' if orig and orig > disc else ''}
    </div>
    <a class="btn-line" href="{base + '../packages/' + p['slug'] + '.html' if base else detail_href}">View the journey</a>
  </div>
</article>"""

def detail_href(p):
    return f"packages/{p['slug']}.html" if Path(ROOT / "packages" / f"{p['slug']}.html").exists() else "packages.html"

CSS_HREF = "assets/css/style.css"

def shell(title, desc, body, active="", extra_head="", base=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(title, desc, extra_head)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{base + '/assets/css/style.css' if base else CSS_HREF}">
</head>
<body>
{header(active, base)}
<main id="main">
{body}
</main>
{footer(base)}
<script src="{base + '/assets/js/main.js' if base else 'assets/js/main.js'}" defer></script>
</body>
</html>"""

# ------------------------------------------------------------------- pages

def page_home():
    featured = [p for p in DATA if p["slug"] in (
        "bhutan-phuentsholing-thimphu-paro-5n-6d", "gangtok-lachung-lachen",
        "darjeeling-4n-5d", "paro-tigers-nest-trekking-tour", "zuluk-namchi-darjeeling",
        "lachung-yumthang-valley-tour")]
    hero_p = next(p for p in DATA if p["slug"] == "gangtok-lachung-lachen")
    cards = "\n".join(card(p, detail_href(p)) for p in DATA)
    feat_cards = "\n".join(card(p, detail_href(p)) for p in featured)
    body = f"""
<section class="hero">
  <img class="hero-img" src="{img(hero_p,'hero')}" alt="The Himalayas at first light">
  <div class="hero-veil"></div>
  <div class="hero-copy reveal">
    <p class="eyebrow">Est. for the discerning traveller</p>
    <h1>Journeys composed<br><em>like literature.</em></h1>
    <p class="hero-sub">Bespoke Himalayan travel — Sikkim, Darjeeling, Kalimpong, the Dooars and the Kingdom of Bhutan — curated by people who walk these roads themselves.</p>
    <div class="hero-actions">
      <a class="btn-solid" href="packages.html">Explore journeys</a>
      <a class="btn-ghost" href="contact.html">Speak to an expert</a>
    </div>
  </div>
</section>

<section class="strip">
  <div><strong>16</strong><span>Signature journeys</span></div>
  <div><strong>5</strong><span>Regions</span></div>
  <div><strong>24×7</strong><span>Concierge support</span></div>
  <div><strong>1:1</strong><span>Expert planning</span></div>
</section>

<section class="section" id="collections">
  <div class="wrap">
    <p class="eyebrow">The collection</p>
    <h2 class="h2">Every journey, <em>considered.</em></h2>
    <p class="lede">From sunrise over Tiger Hill to the cliff-hung monasteries of Paro — each itinerary below is a real, priced journey, confirmed personally by our travel experts.</p>
    <div class="grid">{feat_cards}</div>
    <p class="center-cta"><a class="btn-solid" href="packages.html">View all 16 journeys</a></p>
  </div>
</section>

<section class="section alt">
  <div class="wrap cols">
    <div>
      <p class="eyebrow">The house</p>
      <h2 class="h2">Quiet expertise,<br><em>openly priced.</em></h2>
      <p class="lede">No call-centres, no queues. One expert, one conversation, and a journey shaped around the way you travel.</p>
      <a class="btn-line" href="about.html">Our approach</a>
    </div>
    <ul class="principles">
      <li><h3>Curated, not aggregated</h3><p>A tight collection of journeys we know intimately — never an endless catalogue.</p></li>
      <li><h3>Honest pricing</h3><p>Every price shown is the real per-person fare. Inclusions and exclusions stated plainly.</p></li>
      <li><h3>A human confirms everything</h3><p>Availability, permits and pacing are verified with you, personally, before anything is booked.</p></li>
    </ul>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <p class="eyebrow">Full collection</p>
    <h2 class="h2">All journeys</h2>
    <div class="grid">{cards}</div>
  </div>
</section>"""
    return shell("MyTravelExpert — Bespoke Himalayan Journeys",
                 "Curated luxury journeys across Sikkim, Darjeeling, Kalimpong, Dooars and Bhutan. Honest pricing, expert planning, 24×7 concierge.",
                 body, active="home")

def page_packages():
    cards = "\n".join(card(p, detail_href(p)) for p in DATA)
    body = f"""
<section class="page-hero slim">
  <div class="wrap">
    <p class="eyebrow">The collection</p>
    <h1 class="h1">Sixteen journeys,<br><em>one standard.</em></h1>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="filters" role="group" aria-label="Filter journeys">
      <button class="chip is-on" data-region="all">All regions</button>
      <button class="chip" data-region="Sikkim">Sikkim</button>
      <button class="chip" data-region="Darjeeling & Kalimpong">Darjeeling &amp; Kalimpong</button>
      <button class="chip" data-region="Sikkim & Darjeeling">Sikkim &amp; Darjeeling</button>
      <button class="chip" data-region="Bhutan">Bhutan</button>
      <button class="chip" data-region="Dooars">Dooars</button>
    </div>
    <div class="grid" id="all-grid">{cards}</div>
    <p class="empty-note" hidden>No journeys in this region yet — <a href="{WA}" target="_blank" rel="noopener">ask us to compose one</a>.</p>
  </div>
</section>"""
    return shell("All Journeys — MyTravelExpert",
                 "All 16 curated tour packages with real prices, full itineraries, inclusions and exclusions.",
                 body, active="packages")

def page_detail(p):
    base = ".."
    hero = img(p, "hero")
    gal = [g for g in (img(p, f"g{i+1}") for i in range(8)) if g]
    if base: gal = ['../' + g for g in gal]
    disc = price_num(p.get("discounted_price")); orig = price_num(p.get("original_price"))
    off = round((1 - disc / orig) * 100) if orig and disc else 0

    highlights = ""
    hl = [tidy(h) for h in p.get("highlights", []) if tidy(h)]
    if hl:
        highlights = f"""<section class="section tight"><div class="wrap">
        <p class="eyebrow">Journey highlights</p>
        <ul class="hl-grid">{''.join(f'<li>{esc(h)}</li>' for h in hl)}</ul></div></section>"""

    days = ""
    for d in p.get("itinerary", []):
        chips = tidy(d.get("highlights_chips") or "")
        chip_html = ""
        if chips:
            chip_html = '<p class="day-chips">' + "".join(
                f'<span>{esc(c.strip())}</span>' for c in chips.split("•") if c.strip()) + "</p>"
        tags = []
        if d.get("meals"): tags.append(f'<span class="tag">{esc(d["meals"])}</span>')
        if d.get("stay"): tags.append(f'<span class="tag">{esc(d["stay"])}</span>')
        days += f"""
<li class="day reveal">
  <div class="day-marker"><span>{esc(d.get('day') or '')}</span></div>
  <div class="day-card">
    <h3>{esc(d.get('title') or '')}</h3>
    {f'<p>{esc(d["description"])}</p>' if d.get('description') else '<p class="muted">Day details available from your travel expert on request.</p>'}
    {chip_html}
    {'<div class="day-tags">' + ''.join(tags) + '</div>' if tags else ''}
  </div>
</li>"""
    if days:
        days = f"""<section class="section tight"><div class="wrap">
        <p class="eyebrow">Day by day</p>
        <h2 class="h2">The itinerary</h2>
        <ol class="timeline">{days}</ol></div></section>"""

    inc = p.get("inclusions") or []
    exc = p.get("exclusions") or []
    if inc or exc:
        ie = f"""<section class="section tight"><div class="wrap cols-ie">
        <div class="ie-card incl"><h3>Included</h3><ul>{''.join(f'<li>{esc(i)}</li>' for i in inc)}</ul></div>
        <div class="ie-card excl"><h3>Not included</h3><ul>{''.join(f'<li>{esc(i)}</li>' for i in exc)}</ul></div>
        </div></section>"""
    else:
        ie = f"""<section class="section tight"><div class="wrap">
        <p class="note">Full inclusions and exclusions for this journey are confirmed personally by your travel expert — <a href="{WA}" target="_blank" rel="noopener">ask us</a>.</p></div></section>"""

    gallery = ""
    if gal:
        gallery = f"""<section class="section tight"><div class="wrap">
        <p class="eyebrow">Gallery</p><h2 class="h2">Scenes from the route</h2>
        <div class="gal-grid">{''.join(f'<img src="{g}" alt="{esc(p["name"])} — journey photograph" loading="lazy">' for g in gal)}</div></div></section>"""

    wa_msg = f"Hello! I'm interested in the {p['name']} journey ({p.get('duration','')}, ₹{disc:,}/person)."
    wa_link = "https://wa.me/918001247778?text=" + wa_msg.replace(" ", "+").replace("!", "%21")

    body = f"""
<section class="dhero">
  <img class="hero-img" src="{'../' + hero if base else hero}" alt="{esc(p['name'])}">
  <div class="hero-veil"></div>
  <div class="wrap hero-copy">
    <p class="eyebrow">{esc(region_of(p))}{f' · −{off}% ' if off else ''}</p>
    <h1 class="h1">{esc(p['name'])}</h1>
    {f'<p class="dhero-loc">{esc(p["destination"])}</p>' if p.get('destination') else ''}
    <ul class="factbar">
      {f'<li><span>Duration</span><strong>{esc(p["duration"])}</strong></li>' if p.get('duration') else ''}
      {f'<li><span>Party</span><strong>{esc(p["group_size"])}</strong></li>' if p.get('group_size') else ''}
      {f'<li><span>Pace</span><strong>{esc(tidy(p["difficulty"]).replace(" Level",""))}</strong></li>' if p.get('difficulty') else ''}
      <li><span>From</span><strong class="gold">₹{disc:,}</strong>
        {f'<del>₹{orig:,}</del>' if orig and orig > disc else ''}<em> / person</em></li>
    </ul>
    <div class="hero-actions">
      <a class="btn-solid" href="{wa_link}" target="_blank" rel="noopener">Enquire — ₹{disc:,} / person</a>
      <a class="btn-ghost" href="{CONTACT_PHONE_HREF}">Call {CONTACT_PHONE}</a>
    </div>
  </div>
</section>

{f'<section class="section tight"><div class="wrap"><p class="eyebrow">Overview</p><p class="ov">{esc(p["overview"])}</p></div></section>' if p.get('overview') else ''}
{highlights}
{days}
{ie}
{gallery}

<section class="section tight"><div class="wrap cta-band reveal">
  <div><p class="eyebrow">Reserve this journey</p>
  <h2 class="h2">Speak with the expert<br>who knows this route.</h2></div>
  <div class="cta-actions">
    <a class="btn-solid" href="{wa_link}" target="_blank" rel="noopener">WhatsApp us</a>
    <a class="btn-ghost" href="mailto:{CONTACT_EMAIL}?subject={esc('Enquiry: ' + p['name'])}">Email us</a>
  </div>
</div></section>"""
    desc = f"{p['name']} — {p.get('destination') or 'curated journey'} — {p.get('duration','')} from ₹{disc:,} per person."
    return shell(f"{p['name']} — MyTravelExpert", desc, body, base=base)

def page_about():
    body = f"""
<section class="page-hero slim"><div class="wrap">
  <p class="eyebrow">The house</p>
  <h1 class="h1">Travel, arranged<br><em>the slow, exacting way.</em></h1>
</div></section>
<section class="section"><div class="wrap narrow">
  <p class="ov">MyTravelExpert is a small travel house devoted to the Eastern Himalaya — the tea hills of Darjeeling, the monasteries of Sikkim, the river plains of the Dooars and the fortress valleys of Bhutan. We keep a deliberately short collection: sixteen journeys we have walked, priced honestly, and refined season after season.</p>
  <p class="ov">When you write to us, a travel expert — not a bot, not a call centre — reads your note, calls you back, and shapes the journey around you. Permits, pacing, rooms and viewpoints are all confirmed before you commit to anything.</p>
  <div class="cta-band"><div>
    <h2 class="h2">Begin a conversation</h2>
    <p class="lede">Tell us when, who, and how far you like to walk. We'll do the rest.</p>
  </div>
  <div class="cta-actions">
    <a class="btn-solid" href="{WA}" target="_blank" rel="noopener">WhatsApp</a>
    <a class="btn-ghost" href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
  </div></div>
</div></section>"""
    return shell("The House — MyTravelExpert", "About MyTravelExpert — curated Himalayan journeys, arranged personally.",
                 body, active="about")

def page_contact():
    body = f"""
<section class="page-hero slim"><div class="wrap">
  <p class="eyebrow">Contact</p>
  <h1 class="h1">Your journey begins<br><em>with a conversation.</em></h1>
</div></section>
<section class="section"><div class="wrap contact-grid">
  <a class="contact-card reveal" href="{WA}" target="_blank" rel="noopener">
    <p class="eyebrow">Fastest</p><h2>WhatsApp</h2>
    <p class="lede">Message our concierge any time — we reply within the hour, 24×7.</p>
    <span class="btn-line">Open WhatsApp</span></a>
  <a class="contact-card reveal" href="{CONTACT_PHONE_HREF}">
    <p class="eyebrow">Direct</p><h2>Call {CONTACT_PHONE}</h2>
    <p class="lede">Speak with a travel expert about routes, dates and pacing.</p>
    <span class="btn-line">Dial now</span></a>
  <a class="contact-card reveal" href="mailto:{CONTACT_EMAIL}">
    <p class="eyebrow">Considered</p><h2>{CONTACT_EMAIL}</h2>
    <p class="lede">For detailed itineraries and group planning, write to us.</p>
    <span class="btn-line">Compose email</span></a>
</div></section>"""
    return shell("Contact — MyTravelExpert", "Contact MyTravelExpert — WhatsApp, phone or email a Himalayan travel expert.",
                 body, active="contact")

# ------------------------------------------------------------------ build

def main():
    (ROOT / "packages").mkdir(exist_ok=True)
    (ROOT / "index.html").write_text(page_home())
    (ROOT / "packages.html").write_text(page_packages())
    (ROOT / "about.html").write_text(page_about())
    (ROOT / "contact.html").write_text(page_contact())
    for p in DATA:
        (ROOT / "packages" / f"{p['slug']}.html").write_text(page_detail(p))
    print("Built index.html, packages.html, about.html, contact.html +",
          len(DATA), "detail pages")

if __name__ == "__main__":
    main()
