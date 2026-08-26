from pathlib import Path
import json, html, datetime, shutil

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
DATA_FILE=ROOT/'source'/'site-data.json'
MANIFEST=ROOT/'source'/'generated-pages.json'

def e(v): return html.escape(str(v or ''), quote=True)
def load(): return json.loads(DATA_FILE.read_text(encoding='utf-8'))
def root_url(d): return str(d.get('seo',{}).get('siteUrl','')).strip().rstrip('/')
def absurl(d,path=''):
    u=root_url(d)
    if not u: return ''
    p=str(path or '').lstrip('/')
    return u + ('/'+p if p else '/')
def canonical(url): return f'<link rel="canonical" href="{e(url)}">' if url else ''
def verify(d):
    v=str(d.get('seo',{}).get('googleSiteVerification','')).strip()
    return f'<meta name="google-site-verification" content="{e(v)}">' if v else ''
def share_image(d):
    p=d.get('seo',{}).get('defaultShareImage','')
    return absurl(d,p) if p else ''
def og(d,title,desc,url):
    img=share_image(d); loc=d.get('seo',{}).get('locale','en_AU')
    parts=[
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">'
    ]
    if url: parts.append(f'<meta property="og:url" content="{e(url)}">')
    if img: parts.append(f'<meta property="og:image" content="{e(img)}">')
    if loc: parts.append(f'<meta property="og:locale" content="{e(loc)}">')
    parts += [
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">'
    ]
    if img: parts.append(f'<meta name="twitter:image" content="{e(img)}">')
    return ''.join(parts)

def home_schema(d):
    seo=d['seo']; obj={'@context':'https://schema.org','@type':'WebSite','name':seo.get('siteName') or 'Might Help'}
    if seo.get('alternateName'): obj['alternateName']=seo['alternateName']
    if root_url(d): obj['url']=absurl(d)
    return json.dumps(obj,ensure_ascii=False)

def resource_schema(d,r):
    obj={
      '@context':'https://schema.org','@type':'SoftwareApplication','name':r['title'],
      'description':r.get('metaDescription') or r.get('description',''),
      'applicationCategory':'EducationalApplication' if 'Learning' in r.get('tags',[]) else 'UtilityApplication',
      'operatingSystem':'Web browser','isAccessibleForFree':True
    }
    if root_url(d): obj['url']=absurl(d,r['slug']+'/')
    return json.dumps(obj,ensure_ascii=False)

def homepage(d):
    s,seo,don=d['site'],d['seo'],d['donation']
    visible=[r for r in d['resources'] if r.get('visible',True)]
    featured=next((r for r in visible if r.get('featured')), visible[0] if visible else None)
    tags=[]
    for r in visible:
        for t in r.get('tags',[]):
            if t not in tags: tags.append(t)
    filters=''.join(f'<button class="filter{" active" if i==0 else ""}" type="button" data-filter="{e(t.lower())}">{e(t)}</button>' for i,t in enumerate(['All']+tags))
    cards=[]
    for r in visible:
        target=(r['slug']+'/') if r.get('seoPageEnabled') else (r.get('appUrl') or '#')
        status=r.get('statusText') or ('View' if r.get('status')=='available' else 'Coming soon')
        action=f'<a class="open" href="{e(target)}">{e(status)} →</a>' if r.get('status')=='available' or r.get('seoPageEnabled') else f'<span class="open">{e(status)}</span>'
        search=' '.join([r.get('title',''),r.get('subtitle',''),r.get('description',''),r.get('cardDescription',''),r.get('search',''),' '.join(r.get('tags',[]))]).lower()
        cards.append(f'<article class="card{" coming" if r.get("status")=="coming" else ""}" data-tags="{e("|".join(x.lower() for x in r.get("tags",[])))}" data-search="{e(search)}"><div class="icon">{e(r.get("icon","+"))}</div><h3>{e(r["title"])}</h3><p>{e(r.get("cardDescription") or r.get("description"))}</p><div class="cardbottom"><span class="tag">{e(r.get("category","Resource"))}</span>{action}</div></article>')
    feature=''
    if featured:
        target=(featured['slug']+'/') if featured.get('seoPageEnabled') else (featured.get('appUrl') or '#')
        bullets=''.join(f'<div class="bullet"><span class="tick">✓</span><span>{e(x)}</span></div>' for x in featured.get('featuredBullets',[]))
        feature=f'''<section><div class="container"><article class="featured"><div class="featurecopy"><div class="kicker">Featured resource</div><h2>{e(featured['title'])}</h2><p><strong>{e(featured.get('subtitle',''))}</strong></p><p>{e(featured.get('description',''))}</p><div class="bullets">{bullets}</div><a class="btn primary" href="{e(target)}">View {e(featured['title'])} →</a></div><div class="visual" aria-label="{e(featured['title'])} preview"><div class="mock"><div class="mocktop"></div><div class="mockgrid"><div class="side"><div class="bar blue"></div><div class="bar"></div><div class="bar"></div><div class="bar blue"></div></div><div class="sheet"><div class="row"><div class="letters">a a a a</div></div><div class="row"><div class="letters">m m m</div></div><div class="row"><div class="letters">trace</div></div><div class="row"></div></div></div></div></div></article></div></section>'''
    about=''.join(f'<p>{"<strong>"+e(p)+"</strong>" if i in (2,len(s["aboutParagraphs"])-1) else e(p)}</p>' for i,p in enumerate(s['aboutParagraphs']))
    principles=''.join(f'<div class="principle"><strong>{e(x["title"])}</strong><span>{e(x["text"])}</span></div>' for x in s['principles'])
    donation='' if not don.get('enabled',True) else f'''<section><div class="container"><div class="donate" id="donate"><div><div class="kicker">Support Might Help</div><h2>{e(don['title'])}</h2><p>{e(don['text'])}</p></div><div class="donatebox"><div class="heart">♡</div><a class="btn primary" href="{e(don.get('url') or '#')}">{e(don.get('buttonText','Donate'))}</a><small>{e(don.get('note',''))}</small></div></div></div></section>'''
    contact=f'<a href="{e(d["links"]["contact"])}">Contact</a>' if d.get('links',{}).get('contact') else ''
    donate_nav='<a class="donate-nav" href="#donate">Donate</a>' if don.get('enabled',True) else ''
    url=absurl(d)
    head=f'''<title>{e(seo['homeTitle'])}</title><meta name="description" content="{e(seo['homeDescription'])}">{canonical(url)}{verify(d)}{og(d,seo['homeTitle'],seo['homeDescription'],url)}<link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/css/site.css"><script type="application/ld+json">{home_schema(d)}</script>'''
    return f'''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f6f8fb">{head}</head><body><a class="skip" href="#main">Skip to main content</a><header><div class="container"><nav class="nav" aria-label="Main navigation"><a class="brand" href="./"><span class="mark">M</span><span>{e(s['brand'])}</span></a><div class="navlinks"><a href="#resources">Resources</a><a href="#about">Why Might Help?</a>{donate_nav}<a class="navbtn" href="#resources">Browse resources</a></div></nav></div></header><main id="main"><section class="hero"><div class="container"><div class="eyebrow"><span class="dot"></span><span>{e(s['eyebrow'])}</span></div><h1>{e(s['heroTitle'])}</h1><p class="lead">{e(s['heroLead'])}</p><div class="actions"><a class="btn primary" href="#resources">Browse resources →</a><a class="btn" href="#about">Why Might Help?</a></div><div class="note">{e(s['heroNote'])}</div></div></section>{feature}<section id="resources"><div class="container"><div class="heading"><div class="kicker">Explore</div><h2>{e(s['resourcesHeading'])}</h2><p>{e(s['resourcesIntro'])}</p></div><div class="tools"><input class="search" id="resourceSearch" type="search" placeholder="Search resources…" aria-label="Search resources"><div class="filters" id="filters">{filters}</div></div><div class="grid" id="resourceGrid">{"".join(cards)}</div><div class="empty" id="emptyState">Nothing matches that search yet.</div></div></section><section id="about"><div class="container"><div class="why"><div><div class="kicker">Why Might Help?</div><h2>{e(s['aboutHeading'])}</h2></div><div class="aboutcopy">{about}</div></div><div class="principles">{principles}</div></div></section>{donation}<section><div class="container"><div class="cta"><h2>{e(s['finalHeading'])}</h2><p>{e(s['finalText'])}</p><a class="btn" href="#resources">Browse resources →</a></div></div></section></main><footer><div class="container"><div class="footer"><div><strong>{e(s['brand'])}</strong><div>{e(s['tagline'])}</div></div><div class="footerlinks"><a href="#about">About</a><a href="privacy.html">Privacy</a><a href="terms.html">Terms</a>{contact}</div><div>{e(s['copyright'])}</div></div></div></footer><script src="assets/js/site.js" defer></script></body></html>'''

def resource_page(d,r):
    seo=d['seo']; url=absurl(d,r['slug']+'/'); title=r.get('seoTitle') or f'{r["title"]} | Might Help'; desc=r.get('metaDescription') or r.get('description','')
    tags=''.join(f'<span>{e(t)}</span>' for t in r.get('tags',[])); paras=''.join(f'<p>{e(p)}</p>' for p in r.get('pageContent',[]) if str(p).strip())
    button=f'<a class="btn primary" href="../{e(r["appUrl"])}">Open {e(r["title"])} →</a>' if r.get('appUrl') else '<span class="btn">Coming soon</span>'
    return f'''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f6f8fb"><title>{e(title)}</title><meta name="description" content="{e(desc)}">{canonical(url)}{og(d,title,desc,url)}<link rel="icon" href="../assets/images/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../assets/css/site.css"><script type="application/ld+json">{resource_schema(d,r)}</script></head><body><header><div class="container"><nav class="nav"><a class="brand" href="../"><span class="mark">M</span><span>{e(d['site']['brand'])}</span></a><div class="navlinks"><a href="../#resources">Resources</a><a href="../#about">Why Might Help?</a><a class="navbtn" href="../">Home</a></div></nav></div></header><main class="resource-page"><div class="container"><div class="breadcrumbs"><a href="../">Might Help</a> / {e(r['title'])}</div><div class="resource-hero"><div><div class="kicker">{e(r.get('category','Resource'))}</div><h1>{e(r.get('pageHeading') or r['title'])}</h1><p class="summary">{e(r.get('pageIntro') or r.get('subtitle',''))}</p><div class="resource-tags">{tags}</div><div class="actions" style="justify-content:flex-start">{button}</div></div><aside class="resource-panel"><strong>{e(r.get('subtitle',''))}</strong><p>{e(r.get('description',''))}</p></aside></div><article class="resource-content"><h2>About {e(r['title'])}</h2>{paras}</article></div></main><footer><div class="container"><div class="footer"><div><strong>{e(d['site']['brand'])}</strong><div>{e(d['site']['tagline'])}</div></div><div class="footerlinks"><a href="../privacy.html">Privacy</a><a href="../terms.html">Terms</a></div><div>{e(d['site']['copyright'])}</div></div></div></footer></body></html>'''

def simple_page(d,kind):
    url=absurl(d,kind+'.html'); title=('Privacy' if kind=='privacy' else 'Terms of Use')+' | Might Help'; desc='Privacy information for Might Help.' if kind=='privacy' else 'Terms of use for Might Help programs, tools and resources.'
    if kind=='privacy':
        body='''<h1>Privacy</h1><p>Might Help is designed to keep things simple. The public website does not require an account and does not intentionally collect personal information through the resources shown here unless a particular resource clearly says otherwise.</p><h2>Local use</h2><p>Where a tool runs entirely in your browser, information you enter stays in your browser unless that tool clearly provides an option to export or send it elsewhere.</p><h2>External services</h2><p>Some links may take you to third-party services, such as a donation provider. Those services operate under their own privacy policies.</p><h2>Hosting</h2><p>The website host may keep normal technical logs as part of operating the service. Might Help does not use those logs to build advertising profiles.</p>'''
    else:
        body='''<h1>Terms of Use</h1><p>Might Help makes practical programs, tools and resources available because they might be useful to someone else.</p><h2>Free to use</h2><p>Unless a resource states otherwise, resources made available through Might Help are free to use through the website for their intended purpose. Free access does not transfer ownership of software, designs, source material, branding or other intellectual property.</p><h2>Resource-specific terms</h2><p>Some resources may include separate licence conditions or third-party material. Where that happens, the specific resource information applies.</p><h2>No guarantee</h2><p>Resources are practical aids and may not suit every situation. Users remain responsible for checking professional, legal, safety or technical requirements that apply.</p><h2>Donations</h2><p>Donations are optional and help support hosting, maintenance and continued development. A donation does not purchase ownership or additional licensing rights unless explicitly stated otherwise.</p>'''
    return f'''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(desc)}">{canonical(url)}<link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/css/site.css"><style>.simple{{max-width:820px;margin:65px auto;padding:0 20px 70px}}.simple h1{{font-size:clamp(2.5rem,7vw,4.5rem);text-align:left}}.simple h2{{margin-top:30px}}.simple p{{color:#475467}}.back{{color:#3157d5;font-weight:850}}</style></head><body><main class="simple"><a class="back" href="./">← Back to Might Help</a>{body}</main></body></html>'''

def sitemap(d):
    u=root_url(d)
    if not u: return '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Set the final HTTPS site URL in the offline editor, then build again. -->\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n'
    today=datetime.date.today().isoformat(); rows=[('',today),('privacy.html',today),('terms.html',today)]
    rows += [(r['slug']+'/',r.get('updated') or today) for r in d['resources'] if r.get('visible',True) and r.get('seoPageEnabled')]
    inner=''.join(f'  <url><loc>{e(absurl(d,p))}</loc><lastmod>{e(dt)}</lastmod></url>\n' for p,dt in rows)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+inner+'</urlset>\n'

def robots(d):
    s='User-agent: *\nAllow: /\n'
    if root_url(d): s+='\nSitemap: '+root_url(d)+'/sitemap.xml\n'
    return s

def build(d=None):
    d=d or load(); DOCS.mkdir(parents=True,exist_ok=True)
    old=[]
    if MANIFEST.exists():
        try: old=json.loads(MANIFEST.read_text(encoding='utf-8'))
        except: pass
    current=[r['slug'] for r in d['resources'] if r.get('visible',True) and r.get('seoPageEnabled')]
    for slug in old:
        if slug not in current:
            p=DOCS/slug
            if p.exists() and p.is_dir(): shutil.rmtree(p)
    (DOCS/'index.html').write_text(homepage(d),encoding='utf-8')
    (DOCS/'privacy.html').write_text(simple_page(d,'privacy'),encoding='utf-8')
    (DOCS/'terms.html').write_text(simple_page(d,'terms'),encoding='utf-8')
    (DOCS/'sitemap.xml').write_text(sitemap(d),encoding='utf-8')
    (DOCS/'robots.txt').write_text(robots(d),encoding='utf-8')
    (DOCS/'.nojekyll').write_text('',encoding='utf-8')
    for r in d['resources']:
        if r.get('visible',True) and r.get('seoPageEnabled'):
            p=DOCS/r['slug']; p.mkdir(parents=True,exist_ok=True); (p/'index.html').write_text(resource_page(d,r),encoding='utf-8')
    MANIFEST.write_text(json.dumps(current,indent=2)+'\n',encoding='utf-8')
    cname=str(d.get('seo',{}).get('customDomain','')).strip(); cp=DOCS/'CNAME'
    if cname: cp.write_text(cname+'\n',encoding='utf-8')
    elif cp.exists(): cp.unlink()
    return {'resource_pages':len(current),'site_url':root_url(d),'custom_domain':cname}

if __name__=='__main__':
    result=build(); print(json.dumps(result,indent=2))
