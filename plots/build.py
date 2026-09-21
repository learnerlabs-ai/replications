#!/usr/bin/env python3
"""Build every registered figure (or named ones), run the checks, optionally rasterize.
Usage: python3 plots/build.py                 # all figures, SVG + sidecars + checks + contact sheet
       python3 plots/build.py ts_f4_matrix    # one figure
       python3 plots/build.py --png           # also write <name>.png (2x, 1760 px wide) with headless Chrome/Chromium
Outputs: plots/output/<group>/<name>.svg + .json (+ .png); plots/checks/report.json; plots/output/contact_sheet.html
Static groups (module null) are figures authored elsewhere and registered unchanged; they are checked and rasterized, not drawn."""
import re, json,os,sys,importlib,hashlib,xml.dom.minidom,subprocess,shutil
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'figures')); sys.path.insert(0,os.path.join(HERE,'lib')); sys.path.insert(0,os.path.join(HERE,'checks'))
REG=json.load(open(os.path.join(HERE,'config','registry.json')))
args=sys.argv[1:]; PNG='--png' in args; want=[a for a in args if a not in ('all','--png')]; report=[]
# The section titles below are the site's own, so the explorer's sections and numbering match the articles.
SECTIONS={'ten_skills':('Demonstration 1 &middot; Ten skills, one after another','the ten-skill report'),
          'four_domain':('Demonstration 2 &middot; Four domains, against LoRA','Plasticity Without Forgetting'),
          'two_languages':('Demonstration 3 &middot; Two invented languages','the two-languages report'),
          'facts':('Fact demonstrations','the facts page')}
_CSS="""body{font:15px/1.6 Inter,system-ui,sans-serif;max-width:1180px;margin:0 auto;padding:30px 12px 80px;color:#14171A;background:#fff}
h1{font-size:30px;margin:0 0 6px}p.lede{color:#5A5F5A;margin:0 0 26px;max-width:62ch}
.wrap{display:grid;grid-template-columns:230px minmax(0,1fr);gap:34px;align-items:start}
aside{position:sticky;top:24px;font-size:13.5px}
aside p.sh{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:#616660;margin:0 0 8px}
aside ol{list-style:none;margin:0 0 18px;padding:0}
aside li{margin:0 0 6px;position:relative}
aside a{color:#5A5F5A;text-decoration:none;display:block;line-height:1.35}
aside a.on{color:#14171A;font-weight:600}
aside li.on::before{content:"";position:absolute;left:-12px;top:.55em;width:5px;height:5px;border-radius:50%;background:#2F6E62}
h2{font-size:20px;margin:34px 0 4px;scroll-margin-top:24px;border-bottom:1px solid #DADCD4;padding-bottom:6px}
h2:first-of-type{margin-top:0}
h2 small{font-weight:400;color:#616660;font-size:13.5px;display:block;border:0;padding:0;margin-top:3px}
figure{margin:22px 0;border:1px solid #DADCD4;border-radius:6px;padding:12px;scroll-margin-top:24px}
figcaption{color:#616660;margin-top:8px;font-size:13.5px}
figcaption .figlab{color:inherit;text-decoration:none;border-bottom:1px dotted #8A8F88}
svg{max-width:100%;height:auto}
@media(max-width:860px){.wrap{grid-template-columns:1fr}aside{position:static}}"""
_SPY="""<script>
(function(){var ls=[].slice.call(document.querySelectorAll('aside a[href^="#"]'));
if(!ls.length)return;var ts=ls.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
function mark(){var y=window.scrollY+120,i=0;for(var j=0;j<ts.length;j++){if(ts[j]&&ts[j].offsetTop<=y)i=j;}
ls.forEach(function(a,k){var on=k===i;a.classList.toggle('on',on);if(a.parentNode)a.parentNode.classList.toggle('on',on);
if(on)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});}
var t=false;addEventListener('scroll',function(){if(t)return;t=true;requestAnimationFrame(function(){t=false;mark();});},{passive:true});
addEventListener('resize',mark);mark();})();
</script>"""
html=['<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      '<meta name="robots" content="noindex"><title>Every figure, by demonstration</title><style>'+_CSS+'</style>'
      '<h1>Every figure, by demonstration</h1>'
      '<p class="lede">Every figure this programme publishes, grouped by the demonstration it belongs to and '
      'numbered as that demonstration numbers it. Each one is drawn from the released data by the replication '
      'repository\'s own plot code.</p>']
rail=[]; body=[]
def chrome():
    for c in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','google-chrome','chromium','chromium-browser']:
        if os.path.exists(c) or shutil.which(c): return c
def rasterize(svg_path,w,h):
    c=chrome()
    if not c: return None
    out=svg_path[:-4]+'.png'; page=svg_path[:-4]+'.__png.html'
    open(page,'w').write(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}svg{{display:block;width:{w}px;height:{h}px}}</style>'+open(svg_path).read())
    subprocess.run([c,'--headless=new','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=2',f'--window-size={w},{h}',f'--screenshot={out}','file://'+page],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120)
    os.remove(page); return out if os.path.exists(out) else None
for grp in REG['groups']:
    outdir=os.path.join(HERE,'output',grp['name']); mod=importlib.import_module(grp['module']) if grp.get('module') else None
    _title,_where=SECTIONS.get(grp['name'],(grp['name'],''))
    _sid='sec-'+grp['name']; _fign=[0]
    rail.append('<li><a href="#%s">%s</a></li>' % (_sid,_title.replace('&middot;','·')))
    body.append('<h2 id="%s">%s<small>as published in %s</small></h2>' % (_sid,_title,_where))
    for name in grp['figures']:
        if want and name not in want: continue
        if mod: fig=mod.FIGS[name](); p=fig.save(outdir)
        else: p=os.path.join(outdir,name+'.svg')
        svg=open(p).read(); ok=True; err=''
        # The static figures carry the repository link inside their own rendered text, so a
        # find-and-replace over prose never reaches them. The link is kept in step here, written
        # back, and the sidecar hash refreshed -- otherwise the edit is a hand change that the next
        # regeneration silently loses.
        # [2026-09-19] This used to choose its direction from an environment variable, defaulting to
        # a name that is not this repository's. A reader running the documented build with the
        # variable unset -- which is every reader -- rewrote three published figures to a link that
        # answers 404 for them, and the sidecar refresh below then re-certified the broken file, so
        # the check reported clean. The direction is now fixed: figures cite the repository they are
        # published in.
        if not mod:
            fixed = re.sub(r'github\.com/learnerlabs-ai/[A-Za-z0-9._-]+(?=[< ])',
                           'github.com/learnerlabs-ai/replications', svg)
            if fixed != svg:
                open(p,'w').write(fixed); svg = fixed
                _m = json.load(open(p[:-4]+'.json'))
                _m['svg_sha256'] = hashlib.sha256(svg.encode()).hexdigest()
                json.dump(_m, open(p[:-4]+'.json','w'), indent=1)
                print('static figure: repository link brought in step,', os.path.basename(p))
        try: xml.dom.minidom.parseString(svg)
        except Exception as e: ok=False; err+=f' xml: {e}'
        meta=json.load(open(p[:-4]+'.json'))
        if hashlib.sha256(svg.encode()).hexdigest()!=meta['svg_sha256']: ok=False; err+=' svg hash differs from sidecar'
        for s in (meta['sources'] if mod else []):  # static figures cite the page they were drawn in, which is not part of this tree
            real=os.path.join(HERE,'..',s['path'])
            if not os.path.exists(real): ok=False; err+=f" missing source {s['path']}"
            elif 'sha256' in s and hashlib.sha256(open(real,'rb').read()).hexdigest()!=s['sha256']: ok=False; err+=f" source hash mismatch {s['path']}"
        png=None
        if PNG:
            png=rasterize(p,meta.get('width') or 880,meta.get('height') or 520)
            if not png: ok=False; err+=' png not written (no headless Chrome/Chromium found)'
        report.append({'name':name,'group':grp['name'],'ok':ok,'error':err.strip() or None,'svg_sha256':meta['svg_sha256'],'bytes':len(svg),'png':bool(png),'caption':meta['caption'][:120]})
        # A demonstration numbers its own figures; where its page skips a number, the sheet follows the page.
        _fign[0]=grp.get('figure_numbers',{}).get(name,_fign[0]+1)
        body.append(f'<figure id="{name}"><div>{svg}</div><figcaption>'
                    f'<b><a class="figlab" href="#{name}">Figure {_fign[0]}</a>.</b> {meta["caption"]} '
                    f'<span style="opacity:.7">({name}, {meta.get("badge")})</span></figcaption></figure>')
        print(('OK  ' if ok else 'FAIL'),name,len(svg),'bytes',err)
if not want:
    page=('\n'.join(html)+'<div class="wrap"><aside><p class="sh">Contents</p><ol>'+''.join(rail)+'</ol></aside>'
          '<main>'+'\n'.join(body)+'</main></div>'+_SPY)
    open(os.path.join(HERE,'output','contact_sheet.html'),'w').write(page)
numeric=None
try:
    import numeric_checks; numeric=numeric_checks.run(HERE)
    for r in numeric: print(('OK  ' if r['ok'] else 'FAIL'),'numeric',r['figure'],r['detail'])
except ImportError: pass
allok=all(r['ok'] for r in report) and (numeric is None or all(r['ok'] for r in numeric))
os.makedirs(os.path.join(HERE,'checks'),exist_ok=True)
json.dump({'python':sys.version.split()[0],'rasterizer':('headless Chrome, device scale factor 2 (PNG is 2x the SVG viewBox)' if PNG else None),'figures':report,'numeric':numeric,'all_ok':allok},open(os.path.join(HERE,'checks','report.json'),'w'),indent=1)
print('all_ok',allok,'n',len(report)); sys.exit(0 if allok else 1)
