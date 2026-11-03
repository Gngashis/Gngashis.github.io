#!/usr/bin/env python3
import re, json, html
from pathlib import Path
ROOT = Path('/Volumes/AI_WORKSPACE/Projects/my travelexpert/website')
DATA = json.loads((ROOT / 'data' / 'packages.json').read_text())
OUT = ROOT / 'out'
OUT.mkdir(exist_ok=True)

def clean(s):
    if s is None: return None
    s = html.unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

reports = []
for pkg in DATA:
    slug = pkg['slug']
    fpath = ROOT / 'packages' / f'{slug}.html'
    if not fpath.exists():
        reports.append({'slug':slug,'error':'missing file'})
        continue
    txt = fpath.read_text(encoding='utf8', errors='replace')
    # H1
    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', txt, re.S|re.I)
    h1 = clean(h1_m.group(1)) if h1_m else None
    # destination
    dest_m = re.search(r'<p[^>]*class="dhero-loc"[^>]*>(.*?)</p>', txt, re.S|re.I)
    if not dest_m:
        dest_m = re.search(r'<div[^>]*class="hero-copy"[^>]*>.*?<p[^>]*>(.*?)</p>', txt, re.S|re.I)
    dest = clean(dest_m.group(1)) if dest_m else None
    # factbar
    factbar_m = re.search(r'<ul[^>]*class="factbar"[^>]*>(.*?)</ul>', txt, re.S|re.I)
    facts = {}
    if factbar_m:
        fb = factbar_m.group(1)
        for li in re.finditer(r'<li[^>]*>(.*?)</li>', fb, re.S|re.I):
            li_html = li.group(1)
            k_m = re.search(r'<span[^>]*>(.*?)</span>', li_html, re.S|re.I)
            v_m = re.search(r'<strong[^>]*>(.*?)</strong>', li_html, re.S|re.I)
            k = clean(k_m.group(1)) if k_m else None
            v = clean(v_m.group(1)) if v_m else None
            if k:
                facts[k.upper()] = v
    # prices: orig from <del> in page, disc from factbar 'FROM' strong
    orig_m = re.search(r'<del>\s*(₹[\d,]+)\s*</del>', txt)
    orig = clean(orig_m.group(1)) if orig_m else None
    disc = None
    if 'FROM' in facts and facts['FROM']:
        disc = facts['FROM']
    else:
        # fallback: look for strong.gold
        g_m = re.search(r'<strong[^>]*class="[^"]*gold[^"]*"[^>]*>(.*?)</strong>', txt, re.S|re.I)
        disc = clean(g_m.group(1)) if g_m else None
    # itinerary count
    it_count = len(re.findall(r'<li[^>]*class="day"', txt))
    if it_count==0:
        # some pages may use <li class="day"> vs other
        it_count = len(re.findall(r'<ol[^>]*class="timeline"[^>]*>.*?<li', txt, re.S|re.I))
    # inclusions/exclusions
    incls = []
    excl = []
    incl_m = re.search(r'<div[^>]*class="ie-card incl"[^>]*>(.*?)</div>', txt, re.S|re.I)
    excl_m = re.search(r'<div[^>]*class="ie-card excl"[^>]*>(.*?)</div>', txt, re.S|re.I)
    if incl_m:
        incls = [clean(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', incl_m.group(1), re.S|re.I)]
    else:
        # check for note fallback
        note_m = re.search(r'<p[^>]*class="note"[^>]*>(.*?)</p>', txt, re.S|re.I)
        if note_m:
            # no explicit inclusions
            incls = []
    if excl_m:
        excl = [clean(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', excl_m.group(1), re.S|re.I)]
    # gallery count
    gal_m = re.search(r'<div[^>]*class="gal-grid"[^>]*>(.*?)</div>', txt, re.S|re.I)
    gal_count = 0
    if gal_m:
        gal_count = len(re.findall(r'<img[^>]*src="', gal_m.group(1)))
    # compare to source
    diffs = {}
    diffs['name'] = (h1==clean(pkg.get('name')))
    diffs['destination'] = (clean(pkg.get('destination'))==clean(dest))
    diffs['duration'] = (clean(pkg.get('duration'))==clean(facts.get('DURATION')))
    diffs['orig_price'] = (clean(pkg.get('original_price'))==clean(orig))
    diffs['disc_price'] = (clean(pkg.get('discounted_price'))==clean(disc))
    diffs['itinerary_count'] = (len(pkg.get('itinerary',[]))==it_count)
    diffs['inclusions_count'] = (len(pkg.get('inclusions',[]))==len(incls))
    diffs['exclusions_count'] = (len(pkg.get('exclusions',[]))==len(excl))
    diffs['gallery_count'] = (len(pkg.get('gallery',[]))==gal_count)

    reports.append({
        'slug':slug,
        'h1':h1,
        'destination':dest,
        'facts':facts,
        'orig':orig,'disc':disc,'it_count':it_count,'inclusions':incls,'exclusions':excl,'gal_count':gal_count,
        'src':{'name':pkg.get('name'),'destination':pkg.get('destination'),'duration':pkg.get('duration'),'original_price':pkg.get('original_price'),'discounted_price':pkg.get('discounted_price'),'itinerary_days':len(pkg.get('itinerary',[])),'inclusions_count':len(pkg.get('inclusions',[])),'exclusions_count':len(pkg.get('exclusions',[])),'gallery_count':len(pkg.get('gallery',[]))},
        'diffs':diffs
    })

# summary
summary = {'total':len(reports),'mismatches':sum(1 for r in reports if not all(r['diffs'].values()))}
(Output := OUT / 'verification.json').write_text(json.dumps({'reports':reports,'summary':summary}, indent=2, ensure_ascii=False))
md = [f"# Package verification report\n\nTotal packages: {summary['total']}\nMismatched pages: {summary['mismatches']}\n\n"]
for r in reports:
    lines = [f"## {r['slug']}", f"Name: {r['h1']} (src: {r['src']['name']})", f"Destination: {r['destination']} (src: {r['src']['destination']})",
             f"Duration (page): {r['facts'].get('DURATION')} | src: {r['src']['duration']}", f"Price page: orig={r['orig']}, disc={r['disc']} | src: orig={r['src']['original_price']}, disc={r['src']['discounted_price']}",
             f"Itinerary days: page={r['it_count']} | src={r['src']['itinerary_days']}", f"Inclusions: page={len(r['inclusions'])} | src={r['src']['inclusions_count']}", f"Exclusions: page={len(r['exclusions'])} | src={r['src']['exclusions_count']}", f"Gallery images: page={r['gal_count']} | src={r['src']['gallery_count']}", f"Match summary: {r['diffs']}", '---']
    md.extend(line + '\n' for line in lines)
( Path('/Volumes/AI_WORKSPACE/Projects/my travelexpert/RESEARCH') / 'PACKAGE_VERIFICATION.md').write_text('\n'.join(md))
print('WROTE', Output)
