"""House-style SVG figures (Plasticity Without Forgetting family; tml-article-craft §3b).
Pure standard library. Deterministic output. 880-wide canvas; Inter; palette below.
Every figure writes <name>.svg plus <name>.json (caption, alt, data provenance)."""
import json, math, hashlib, os

INK="#14171A"; MUTED="#616660"; RULE="#DADCD4"; PAPER="#FFFFFF"
TEAL="#2F6E62"; DEEP="#173B34"; AMBER="#B4762A"; VOID="#8A8F88"; PALE_TEAL="#DCEBE6"; PALE_AMBER="#F3E4CE"
SKILL_COLORS=["#2F6E62","#173B34","#B4762A","#5C8A7E","#8A5A22","#3F7F72","#D19A55","#264F47","#7A9E95","#A67C3D"]
FONT="Inter,system-ui,sans-serif"

ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def fmt(v,d=2):
    if v is None: return ""
    if abs(v)>=1000: return f"{v:,.0f}"
    return f"{v:.{d}f}".rstrip("0").rstrip(".") if d>0 else f"{v:.0f}"

def nice_ticks(lo,hi,n=5):
    if hi<=lo: hi=lo+1
    span=hi-lo; raw=span/max(n-1,1); mag=10**math.floor(math.log10(raw)); 
    for m in (1,2,2.5,5,10):
        step=m*mag
        if span/step<=n+1: break
    start=math.floor(lo/step)*step; ticks=[]; t=start
    while t<=hi+1e-9:
        if t>=lo-1e-9: ticks.append(round(t,10))
        t+=step
    return ticks

class Axes:
    def __init__(self,fig,x,y,w,h,xlim,ylim,xlog=False,ylog=False):
        self.f=fig; self.x=x; self.y=y; self.w=w; self.h=h; self.xlim=xlim; self.ylim=ylim; self.xlog=xlog; self.ylog=ylog
    def px(self,v):
        lo,hi=self.xlim
        if self.xlog: v,lo,hi=math.log10(max(v,1e-12)),math.log10(lo),math.log10(hi)
        return self.x+ (v-lo)/(hi-lo)*self.w
    def py(self,v):
        lo,hi=self.ylim
        if self.ylog: v,lo,hi=math.log10(max(v,1e-12)),math.log10(lo),math.log10(hi)
        return self.y+self.h-(v-lo)/(hi-lo)*self.h
    def grid(self,yticks=None,xticks=None,ylabel_fmt=None,xlabel_fmt=None,xlabel=None,ylabel=None):
        f=self.f
        if yticks is None: yticks=nice_ticks(*self.ylim)
        for t in yticks:
            yy=self.py(t); f.add(f'<line x1="{self.x:.1f}" y1="{yy:.1f}" x2="{self.x+self.w:.1f}" y2="{yy:.1f}" stroke="{RULE}" stroke-width="1"/>')
            f.text(self.x-8,yy+4,(ylabel_fmt or fmt)(t),size=12,color=MUTED,anchor="end")
        f.add(f'<line x1="{self.x:.1f}" y1="{self.y:.1f}" x2="{self.x:.1f}" y2="{self.y+self.h:.1f}" stroke="{RULE}" stroke-width="1.4" stroke-linecap="round"/>')
        f.add(f'<line x1="{self.x:.1f}" y1="{self.y+self.h:.1f}" x2="{self.x+self.w:.1f}" y2="{self.y+self.h:.1f}" stroke="{RULE}" stroke-width="1.4" stroke-linecap="round"/>')
        if xticks is None: xticks=nice_ticks(*self.xlim)
        for t in xticks:
            xx=self.px(t); f.add(f'<line x1="{xx:.1f}" y1="{self.y+self.h:.1f}" x2="{xx:.1f}" y2="{self.y+self.h+5:.1f}" stroke="{RULE}" stroke-width="1.2"/>')
            f.text(xx,self.y+self.h+18,(xlabel_fmt or fmt)(t),size=12,color=MUTED,anchor="middle")
        if xlabel: f.text(self.x+self.w/2,self.y+self.h+36,xlabel,size=12.5,color=MUTED,anchor="middle")
        if ylabel: f.add(f'<text transform="translate({self.x-44:.1f},{self.y+self.h/2:.1f}) rotate(-90)" text-anchor="middle" font-family="{FONT}" font-size="12.5" fill="{MUTED}">{esc(ylabel)}</text>')
    def line(self,pts,color=TEAL,width=2,dash=None,opacity=1.0):
        if not pts: return
        d=" ".join(f"{self.px(x):.1f},{self.py(y):.1f}" for x,y in pts)
        da=f' stroke-dasharray="{dash}"' if dash else ""
        self.f.add(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{da} opacity="{opacity}"/>')
    def area(self,lo,hi,color=TEAL,opacity=0.22):
        if not lo: return
        d="M"+" L".join(f"{self.px(x):.1f},{self.py(y):.1f}" for x,y in hi)+" L"+" L".join(f"{self.px(x):.1f},{self.py(y):.1f}" for x,y in reversed(lo))+" Z"
        self.f.add(f'<path d="{d}" fill="{color}" opacity="{opacity}" stroke="none"/>')
    def hline(self,yv,color=RULE,width=1.4,dash="4 4",label=None,label_color=MUTED):
        yy=self.py(yv); self.f.add(f'<line x1="{self.x:.1f}" y1="{yy:.1f}" x2="{self.x+self.w:.1f}" y2="{yy:.1f}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
        if label: self.f.text(self.x+self.w-4,yy-5,label,size=12,color=label_color,anchor="end")
    def vline(self,xv,color=RULE,width=1.2,dash="3 4",label=None,label_y=None,label_color=MUTED,anchor="middle"):
        xx=self.px(xv); self.f.add(f'<line x1="{xx:.1f}" y1="{self.y:.1f}" x2="{xx:.1f}" y2="{self.y+self.h:.1f}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
        if label: self.f.text(xx,label_y if label_y is not None else self.y-6,label,size=11.5,color=label_color,anchor=anchor)
    def band(self,x0,x1,color=PALE_TEAL,opacity=0.6):
        self.f.add(f'<rect x="{self.px(x0):.1f}" y="{self.y:.1f}" width="{self.px(x1)-self.px(x0):.1f}" height="{self.h:.1f}" fill="{color}" opacity="{opacity}"/>')
    def dot(self,xv,yv,color=TEAL,r=4,stroke=PAPER):
        self.f.add(f'<circle cx="{self.px(xv):.1f}" cy="{self.py(yv):.1f}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="1.2"/>')
    def bar(self,xv,yv,wpx,color=TEAL,y0=0.0,label=None,label_color=INK,opacity=1.0):
        xx=self.px(xv)-wpx/2; ya=self.py(max(yv,y0)); yb=self.py(min(yv,y0))
        self.f.add(f'<rect x="{xx:.1f}" y="{ya:.1f}" width="{wpx:.1f}" height="{max(yb-ya,0.5):.1f}" rx="2" fill="{color}" opacity="{opacity}"/>')
        if label is not None: self.f.text(xx+wpx/2,ya-5 if yv>=y0 else yb+13,label,size=11.5,color=label_color,anchor="middle",weight="600")
    def label(self,xv,yv,text,color=INK,size=12,anchor="start",dx=6,dy=4,weight="400"):
        self.f.text(self.px(xv)+dx,self.py(yv)+dy,text,size=size,color=color,anchor=anchor,weight=weight)

class Figure:
    def __init__(self,name,width=880,height=520,title=None,badge="measured"):
        self.name=name; self.w=width; self.h=height; self.parts=[]; self.badge=badge; self.title_text=title; self.provenance=[]; self.caption=""; self.alt=""
        if title: self.text(36,34,title,size=22,weight="600")
        if badge:
            bw=84 if badge=="measured" else 90; bx=self.w-36-bw
            col=TEAL if badge=="measured" else AMBER
            self.add(f'<rect x="{bx}" y="18" width="{bw}" height="22" rx="11" fill="{PAPER}" stroke="{col}" stroke-width="1.2"/>')
            self.text(bx+bw/2,33,badge,size=12,color=col,anchor="middle",weight="600")
    def add(self,s): self.parts.append(s)
    def text(self,x,y,s,size=13,color=INK,anchor="start",weight="400",italic=False):
        st=' font-style="italic"' if italic else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{color}"{st}>{esc(s)}</text>')
    def legend(self,items,x=36,y=57):
        cx=x
        for label,color,kind in items:
            if kind=="line": self.add(f'<line x1="{cx}" y1="{y+6}" x2="{cx+18}" y2="{y+6}" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>'); cx+=24
            elif kind=="dash": self.add(f'<line x1="{cx}" y1="{y+6}" x2="{cx+18}" y2="{y+6}" stroke="{color}" stroke-width="2" stroke-dasharray="4 4"/>'); cx+=24
            else: self.add(f'<rect x="{cx}" y="{y}" width="12" height="12" rx="2" fill="{color}"/>'); cx+=18
            self.text(cx,y+11,label,size=15); cx+=len(label)*7.6+22
    def panel(self,x,y,w,h,title=None,subtitle=None,sub2=None,pad=(20,30,44,40)):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{PAPER}" stroke="{RULE}" stroke-width="1.4"/>')
        top=y+pad[1]
        if title: self.text(x+pad[0],y+30,title,size=20,weight="600"); top=y+40
        for st in (subtitle,sub2):
            if not st: continue
            for l in wrap(st,int((w-2*pad[0])/5.9)): self.text(x+pad[0],top+16,l,size=12.5,color=MUTED); top+=16
        return (x+pad[2]+20, top+22, w-pad[2]-40, h-(top-y)-22-pad[3])
    def axes(self,box,xlim,ylim,**kw): return Axes(self,box[0],box[1],box[2],box[3],xlim,ylim,**kw)
    def footnote(self,s,y=None,maxchars=128):
        lines=wrap(s,maxchars); y0=(y if y is not None else self.h-14-(len(lines)-1)*15)
        for i,l in enumerate(lines): self.text(36,y0+i*15,l,size=11.5,color=MUTED)
    def note(self,x,y,s,color=MUTED,size=12,italic=True,anchor="start"): self.text(x,y,s,size=size,color=color,anchor=anchor,italic=italic)
    def source(self,path,sha_of=None,transform=None):
        """Record an input. `path` is relative to the repository/wave root; its sha256 is always computed when the file exists."""
        ent={"path":path}; real=sha_of or os.path.join(ROOT,path)
        if os.path.exists(real): ent["sha256"]=hashlib.sha256(open(real,"rb").read()).hexdigest()
        if transform: ent["transform"]=transform
        self.provenance.append(ent)
    def render(self):
        head=f'<svg viewBox="0 0 {self.w} {self.h}" width="100%" style="height:auto;display:block" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(self.alt)}">\n<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{PAPER}"/>\n'
        return head+"\n".join(self.parts)+"\n</svg>\n"
    def save(self,outdir):
        os.makedirs(outdir,exist_ok=True); svg=self.render(); p=os.path.join(outdir,self.name+".svg"); open(p,"w").write(svg)
        meta={"name":self.name,"title":self.title_text,"badge":self.badge,"caption":self.caption,"alt":self.alt,"width":self.w,"height":self.h,"svg_sha256":hashlib.sha256(svg.encode()).hexdigest(),"sources":self.provenance,"units":getattr(self,"units",None),"smoothing":getattr(self,"smoothing","none"),"transforms":getattr(self,"transforms",[]),"plotted":getattr(self,"plotted",None)}
        json.dump(meta,open(os.path.join(outdir,self.name+".json"),"w"),indent=1); return p

def wrap(s,maxchars):
    words=str(s).split(); lines=[]; cur=""
    for w in words:
        if len(cur)+len(w)+1>maxchars and cur: lines.append(cur); cur=w
        else: cur=(cur+" "+w).strip()
    if cur: lines.append(cur)
    return lines or [""]

def spread(items,minsep=13,lo=None,hi=None):
    """items: list of (key,y). Returns dict key->y with collisions resolved by pushing apart (pixel units)."""
    it=sorted(items,key=lambda t:t[1]); ys=[y for _,y in it]
    for i in range(1,len(ys)):
        if ys[i]-ys[i-1]<minsep: ys[i]=ys[i-1]+minsep
    if hi is not None and ys and ys[-1]>hi:
        shift=ys[-1]-hi; ys=[y-shift for y in ys]
    for i in range(len(ys)-2,-1,-1):
        if ys[i+1]-ys[i]<minsep: ys[i]=ys[i+1]-minsep
    if lo is not None and ys and ys[0]<lo:
        shift=lo-ys[0]; ys=[y+shift for y in ys]
    return {k:y for (k,_),y in zip(it,ys)}

def sig(v,n=2):
    if v is None: return ""
    if v==0: return "0"
    return f"{v:.{n}g}"

def ema(vals,k=31):
    out=[]; a=2/(k+1); s=None
    for v in vals:
        if v is None or (isinstance(v,float) and v!=v): out.append(s); continue
        s=v if s is None else a*v+(1-a)*s; out.append(s)
    return out

def envelope(pts,n=800):
    """Extrema-preserving reduction of a raw series: for each of n equal x-buckets keep the minimum and the maximum point,
    in x order. Every spike survives; nothing is averaged. Returns (lower_pts, upper_pts)."""
    if not pts: return [],[]
    step=max(1,len(pts)/n); lo=[]; hi=[]; i=0.0
    while int(i)<len(pts):
        b=pts[int(i):max(int(i)+1,int(i+step))]; mn=min(b,key=lambda t:t[1]); mx=max(b,key=lambda t:t[1]); xm=b[len(b)//2][0]
        lo.append((xm,mn[1])); hi.append((xm,mx[1])); i+=step
    return lo,hi

def downsample(pts,n=1500):
    if len(pts)<=n: return pts
    step=len(pts)/n; return [pts[int(i*step)] for i in range(n)]+[pts[-1]]
