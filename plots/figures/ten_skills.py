"""Ten-skill (the ten-skill run accepted-chain) figures. Reads only plots/data/* (allowlisted, public-safe)."""
import json,os,sys,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'lib'))
from housesvg import *
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D=os.path.join(W,'plots','data'); OUT=os.path.join(W,'plots','output','ten_skills')
T=json.load(open(os.path.join(D,'derived','tables.json'))); SK=T['skills']; LAB=T['labels']
SC=dict(zip(SK,SKILL_COLORS))
def _series(name): return json.load(open(os.path.join(D,'series',name)))['rows']
_cache={}
def series(name):
    if name not in _cache: _cache[name]=_series(name)
    return _cache[name]
BOUND=[0]+[d['cumulative_updates'] for d in T['dose']]  # 0,9850,...,63282

def f1_stream():
    tr=series('training_loss.json'); f=Figure('ts_f1_stream',height=560,title='Ten skills, one stream: training loss per update')
    f.legend([('training loss, smoothed (moving average, span 31)',TEAL,'line'),('raw per-update loss, min to max',PALE_TEAL,'box')])
    box=f.panel(36,86,808,420,'One example per update, 63,282 updates in the order they were applied',"loss on the example being trained, nats (log scale)")
    ax=f.axes(box,(0,63282),(1e-4,10),ylog=True)
    ax.grid(yticks=[1e-4,1e-3,1e-2,1e-1,1,10],ylabel_fmt=lambda t:('%g'%t),xticks=[0,10000,20000,30000,40000,50000,60000],xlabel_fmt=lambda t:f"{int(t):,}",xlabel='update')
    for i,s in enumerate(SK):
        if i%2==1: ax.band(BOUND[i],BOUND[i+1],color='#EFEFEA',opacity=0.9)
    raw=[(r['global_update'],max(r['training_loss'],1e-4)) for r in tr if r['training_loss'] is not None]; lo,hi=envelope(raw,780); ax.area(lo,hi,TEAL,0.20)
    vals=ema([r['training_loss'] for r in tr],31); pts=[(r['global_update'],max(v,1e-4)) for r,v in zip(tr,vals) if v is not None]; ax.line(downsample(pts,2400),TEAL,1.4)
    f.units='nats per supervised token'; f.smoothing='exponential moving average, span 31 updates (line); none (band)'; f.transforms=['values below 1e-4 drawn at 1e-4','band: per-slice minimum and maximum of the raw loss over 780 slices (extrema preserved)','line: smoothed series sampled at 2,400 evenly spaced updates']
    f.plotted={'n_raw_points':len(raw),'raw_min':min(v for _,v in raw),'raw_max':max(v for _,v in raw)}
    for i,s in enumerate(SK):
        mid=(BOUND[i]+BOUND[i+1])/2; f.text(ax.px(mid),ax.y+14+(13 if i%2 else 0),LAB[s],size=11,color=DEEP,anchor='middle',weight='600')
    f.footnote('Ten skills taught one after another; shaded columns alternate per skill. Losses below 1e-4 are drawn at 1e-4. The pale band spans the lowest and highest raw loss in each of 780 slices of the stream, so every spike is inside it; the line is the smoothed loss. Source: plots/data/series/training_loss.json.')
    f.caption='Training loss over the whole stream: each skill starts high, drops within its own segment, and hands over to the next. Nothing in the stream tells the learner where one skill ends and the next begins.'
    f.alt='Line chart of training loss on a log scale over 63,282 single-example updates, with ten labelled segments in the taught order (SCAN, Meridian, Adyghe G2P, Oriel, COGS, Sable, PCFG, Tessel, Juniper, Bracken). The loss rises at the start of each new skill and falls within it.'
    f.source('plots/data/series/training_loss.json',os.path.join(D,'series','training_loss.json')); return f

def _f2(name,shared):
    tr=series('training_loss.json'); va=series('held_out_loss.json')
    f=Figure(name,height=1540,title=('Each skill during its own teach: training loss and held-out loss' if shared else 'Each skill during its own teach, zoomed: every panel has its own loss scale'))
    f.legend([('training loss, smoothed (moving average, span 31)',TEAL,'line'),('raw training loss, min to max',PALE_TEAL,'box')],y=50); f.legend([('held-out loss on 8 monitored panel rows, every 25 updates',AMBER,'line')],y=70)
    col_w=392; row_h=262; plotted={}
    for i,s in enumerate(SK):
        r=i//2; c=i%2; x=36+c*(col_w+24); y=90+r*(row_h+12)
        seg=[q for q in tr if q['skill']==s]; vs=[q for q in va if q['teach_index']==i+1 and q['monitored_skill']==s and q['panel_rows']==8]
        n=len(seg); box=f.panel(x,y,col_w,row_h,f"{i+1}. {LAB[s]}",f"{n:,} updates · held-out loss at the end {sig(vs[-1]['held_out_loss'],2) if vs else 'n/a'} nats",pad=(20,30,44,40))
        if shared: ymin=1e-5
        else:
            lo=min(min(q['training_loss'] for q in seg if q['training_loss'] is not None),min(q['held_out_loss'] for q in vs) if vs else 1); ymin=10**math.floor(math.log10(max(lo,1e-5)))
        ax=f.axes(box,(0,n),(ymin,10),ylog=True); ax.grid(yticks=[t for t in [1e-5,1e-4,1e-3,1e-2,1e-1,1,10] if t>=ymin],ylabel_fmt=lambda t:('%g'%t),xticks=nice_ticks(0,n,4),xlabel_fmt=lambda t:f"{int(t):,}",xlabel='update within the skill')
        base=seg[0]['global_update']-1
        raw=[(q['global_update']-base,max(q['training_loss'],ymin)) for q in seg if q['training_loss'] is not None]; lo_,hi_=envelope(raw,340); ax.area(lo_,hi_,TEAL,0.20)
        sm=[(q['global_update']-base,max(v,ymin)) for q,v in zip(seg,ema([q['training_loss'] for q in seg],31)) if v is not None]; ax.line(downsample(sm,700),TEAL,1.4)
        hp=[(q['global_update']-base,max(q['held_out_loss'],ymin)) for q in vs]
        if len(hp)>=3: ax.line(hp,AMBER,1.8)
        elif len(hp)==2:                                    # gate measurement at both ends of the teach
            ax.line(hp,AMBER,1.6,dash='5 4')
            for x_,v_ in hp: ax.dot(x_,v_,AMBER,4.2)
            f.text(ax.x+ax.w-4,ax.y+12,('measured at the start and the end of this teach' if hp[0][0]<=1 else 'measured where the teach resumed and at its end'),size=10.5,color=AMBER,anchor='end')
        else:
            for x_,v_ in hp: ax.dot(x_,v_,AMBER,4)
            f.text(ax.x+ax.w-4,ax.y+12,'held-out loss measured at the endpoint only',size=10.5,color=AMBER,anchor='end')
        plotted[s]={'updates':n,'monitor_points':len(vs),'last_monitored_held_out_loss':(vs[-1]['held_out_loss'] if vs else None)}
    f.footnote(('All ten panels share one loss axis (1e-5 to 10 nats, log scale). ' if shared else 'Zoomed view: the loss axis differs between panels, so compare shapes within a panel, not levels across panels. ')+'The held-out curve is the mean per-token loss on eight fixed panel rows that are never trained on, measured every 25 updates; it is a monitor, not the 225-row evaluation. During the PCFG and Tessel teaches the every-25-update monitor watched the previously taught skills and the English control rather than the skill being taught; that skill was measured on the same eight rows at the gate instead, once before its first update and once after its last, and those two points are drawn with a dashed segment between them. The PCFG point sits 792 updates in because that teach was resumed there; the Tessel point sits at the start of its teach. Source: plots/data/series/{training_loss,held_out_loss}.json.',y=1478)
    f.caption=("Per-skill training and held-out loss during each skill's own segment, on one shared scale. Held-out loss falls with training on all ten and settles at very different levels: near zero for SCAN and COGS, far higher for Oriel and Juniper." if shared else "The same ten panels with a separate loss scale per panel, to show the shape of each curve. Levels are not comparable across panels in this view; use the shared-scale figure for that.")
    f.alt='Ten small panels, one per skill in taught order, each with a pale band of raw training loss, a teal smoothed training-loss line and an amber held-out-loss line on a log scale against updates within the skill.'
    f.units='nats per supervised token'; f.smoothing='exponential moving average, span 31 updates (teal line); none (band, amber line)'; f.transforms=['values below the axis minimum drawn at the axis minimum','band: per-slice minimum and maximum of the raw loss (extrema preserved)','line: smoothed series sampled at up to 700 evenly spaced updates']; f.plotted=plotted
    f.source('plots/data/series/training_loss.json'); f.source('plots/data/series/held_out_loss.json'); return f
def f2_per_skill(): return _f2('ts_f2_per_skill',True)
def f2_zoom(): return _f2('ts_f2z_per_skill_zoom',False)

def f3_retention():
    va=series('held_out_loss.json'); f=Figure('ts_f3_retention',height=640,title='What happens to a skill after its teach ends')
    f.legend([(LAB[s],SC[s],'line') for s in SK[:5]],y=57); f.legend([(LAB[s],SC[s],'line') for s in SK[5:]],y=78)
    box=f.panel(36,108,808,440,'Held-out loss of every earlier skill while later skills are trained',"lines: 8 monitored rows every 25 updates · dots: separate 24-row sweeps at teach endpoints; nats, log scale")
    box=(box[0],box[1],box[2]-150,box[3])
    ax=f.axes(box,(0,63282),(1e-5,10),ylog=True); ax.grid(yticks=[1e-5,1e-4,1e-3,1e-2,1e-1,1,10],ylabel_fmt=lambda t:('%g'%t),xticks=[0,10000,20000,30000,40000,50000,60000],xlabel_fmt=lambda t:f"{int(t):,}",xlabel='update (whole stream)')
    for i,b in enumerate(BOUND[1:-1]): ax.vline(b,label=None)
    ends=[]
    for i,s in enumerate(SK):
        pts=[(q['global_update'],max(q['held_out_loss'],1e-5)) for q in va if q['monitored_skill']==s and q['panel_rows']==8]
        segs=[[]]
        for q in pts:
            if segs[-1] and q[0]-segs[-1][-1][0]>200: segs.append([])
            segs[-1].append(q)
        for sg in segs:
            if len(sg)>=3: ax.line(sg,SC[s],1.4)
            else:
                for x_,v_ in sg: ax.dot(x_,v_,SC[s],2.6)
        for q in va:
            if q['monitored_skill']==s and q['panel_rows']==24 and q['kind']=='endpoint': ax.dot(q['global_update'],max(q['held_out_loss'],1e-5),SC[s],2.6)
        if pts: ends.append((s,ax.py(pts[-1][1]),pts[-1][1]))
    ctl=[(q['global_update'],q['held_out_loss']) for q in va if q['monitored_skill']=='__english_control_24__']
    if ctl:
        segs=[[]]
        for q in ctl:
            if segs[-1] and q[0]-segs[-1][-1][0]>200: segs.append([])
            segs[-1].append(q)
        for sg in segs:
            if len(sg)>=3: ax.line(sg,VOID,1.2,dash='3 3')
            else:
                for x_,v_ in sg: ax.dot(x_,v_,VOID,2.4)
        ends.append(('__ctl__',ax.py(ctl[-1][1]),ctl[-1][1]))
    ys=spread([(k,y) for k,y,_ in ends],13,ax.y+8,ax.y+ax.h-4); xr=ax.x+ax.w+6
    for k,y,v in ends:
        yy=ys[k]; col=(MUTED if k=='__ctl__' else SC[k]); name=('English control (24 rows)' if k=='__ctl__' else LAB[k])
        f.add(f'<line x1="{ax.x+ax.w:.1f}" y1="{y:.1f}" x2="{xr-2:.1f}" y2="{yy:.1f}" stroke="{col}" stroke-width="0.8" opacity="0.7"/>')
        f.text(xr,yy+4,f"{name} {sig(v,2)}",size=10.5,color=col,anchor='start')
    f.footnote('In the first five teaches an earlier skill was measured only at teach endpoints; in the sixth teach two earlier skills were monitored continuously, and from the seventh every earlier skill was. The 8-row monitor and the 24-row endpoint sweeps are different samples of the panel and are drawn as separate marks. A line is drawn only across consecutive measurements; where a skill was not monitored there is a gap, and isolated endpoint measurements are dots. Dashed verticals mark teach boundaries. Source: plots/data/series/held_out_loss.json.')
    f.caption='Retention as a loss curve: after a skill\'s own segment ends, its held-out loss is nearly flat across the remaining tens of thousands of updates on other skills. The English control panel (never trained) stays where it started.'
    f.alt='Line chart on a log scale with one curve per skill showing held-out loss across the entire 63,282-update stream; each curve is close to flat after the skill\'s own segment; an English control line is flat near 3 nats.'
    f.source('plots/data/series/held_out_loss.json'); return f

def f4_matrix():
    M=T['matrix']; f=Figure('ts_f4_matrix',height=640,title='Accuracy on the fixed 225-row panels at every accepted checkpoint')
    box=f.panel(36,60,808,540,'Rows: checkpoint after each teach. Columns: skill. Cell: correct of 225 (exact match)','blank = not yet taught at that checkpoint',pad=(20,30,0,0))
    x0=36+150; y0=box[1]+10; cw=64; ch=40
    for j,s in enumerate(SK): f.text(x0+j*cw+cw/2,y0-8,LAB[s],size=11.5,color=MUTED,anchor='middle')
    for i,row in enumerate(M[1:]):
        yy=y0+i*ch; f.text(x0-10,yy+ch/2+4,f"after {i+1}: {LAB[row['taught']]}",size=12,color=INK,anchor='end')
        for j,s in enumerate(SK):
            v=row[s]; xx=x0+j*cw
            if v is None: f.add(f'<rect x="{xx+2}" y="{yy+2}" width="{cw-4}" height="{ch-4}" rx="3" fill="#F4F4F1"/>'); continue
            frac=v/225; col=f'rgb({int(255-(255-0x2F)*frac)},{int(255-(255-0x6E)*frac)},{int(255-(255-0x62)*frac)})'
            f.add(f'<rect x="{xx+2}" y="{yy+2}" width="{cw-4}" height="{ch-4}" rx="3" fill="{col}"/>')
            f.text(xx+cw/2,yy+ch/2+4,str(v),size=12.5,color=(PAPER if frac>0.55 else INK),anchor='middle',weight='600')
    f.footnote('Each cell is the number of exactly-correct answers on that skill\'s fixed 225-row held-out panel at that checkpoint. Source: plots/data/derived/tables.json (matrix), from the panel analysis receipt.')
    f.plotted={'matrix':[[r.get(k) for k in SK] for r in M]}
    f.caption='The checkpoint-by-skill matrix: each skill is scored from its own teach onward, so cells above the diagonal are blank. Read down a column to see a skill\'s score while later skills are taught: SCAN 222 at every one of ten checkpoints; Meridian moves within 81 to 84; Oriel is the only column that moves by more than two rows.'
    f.alt='A ten-by-ten grid of numbers (correct of 225), rows are checkpoints after each teach, columns are skills; cells above the diagonal are blank; values are stable down each column except Oriel.'
    f.source('plots/data/derived/tables.json'); return f

def f5_ownfinal():
    O=T['own_end_vs_final']; f=Figure('ts_f5_own_vs_final',height=560,title='Own-end score versus final score, per skill')
    f.legend([('right after its own teach',AMBER,'box'),('after all ten teaches',TEAL,'box')])
    box=f.panel(36,86,808,420,'Correct of 225 on each skill\'s fixed held-out panel','the two marks coincide when nothing changed')
    ax=f.axes(box,(0,225),(-0.5,9.5)); ax.grid(yticks=[],xticks=[0,45,90,135,180,225],xlabel_fmt=lambda t:f"{int(t)}",xlabel='correct of 225')
    for i,o in enumerate(O):
        yv=9-i; x1,x2=o['own_end_correct'],o['final_correct']
        f.add(f'<line x1="{ax.px(x1):.1f}" y1="{ax.py(yv):.1f}" x2="{ax.px(x2):.1f}" y2="{ax.py(yv):.1f}" stroke="{RULE}" stroke-width="3"/>')
        ax.dot(x1,yv,AMBER,6); ax.dot(x2,yv,TEAL,6)
        f.text(ax.x-10,ax.py(yv)+4,o['label'],size=12.5,anchor='end')
        d=o['delta']; txt=f"{x1} → {x2}" + (f"  ({'+' if d>0 else ''}{d})" if d else "  (no change)")
        if max(x1,x2)>190: ax.label(min(x1,x2),yv,txt,color=(AMBER if d<0 else (TEAL if d>0 else MUTED)),size=11.5,anchor='end',dx=-10)
        else: ax.label(max(x1,x2),yv,txt,color=(AMBER if d<0 else (TEAL if d>0 else MUTED)),size=11.5,dx=10)
    f.footnote('Own-end = the checkpoint at the end of that skill\'s segment; final = the checkpoint after the tenth teach. Source: plots/data/derived/tables.json.')
    f.plotted={o['skill']:[o['own_end_correct'],o['final_correct']] for o in T['own_end_vs_final']}
    f.caption='All ten skills hold what they learned: nine end within two rows of their own teach, and for Oriel the four working components survive, with the header and escaping right on every row at the end and the payload and decoded length on 92 to 95 per cent of them. Its exact-match count still moves 12 to 9 of 225 because one wrong checksum costs the whole row. Juniper and Meridian end slightly higher than at their own teach.'
    f.alt='Dumbbell chart with ten rows, one per skill; amber dot at the own-end score and teal dot at the final score, joined by a grey bar; most pairs coincide or differ by one or two; Oriel shows 12 to 9.'
    f.source('plots/data/derived/tables.json'); return f

def f6_dose():
    Dd=T['dose']; f=Figure('ts_f6_dose',height=560,title='How much each skill was trained')
    f.legend([('updates applied (one example each)',TEAL,'box'),('supervised tokens, including the end-of-sequence token',AMBER,'box')])
    b1=f.panel(36,86,392,420,'Updates','examples the learner was trained on'); b2=f.panel(452,86,392,420,'Supervised tokens','tokens the loss was computed on')
    for box,key,col,fm in [(b1,'updates_applied',TEAL,lambda v:f"{v:,}"),(b2,'supervised_tokens_trained',AMBER,lambda v:f"{v/1000:.0f}k")]:
        mx=max(d[key] for d in Dd); ax=f.axes(box,(0,mx*1.25),(-0.5,9.5)); ax.grid(yticks=[],xticks=[],xlabel=None)
        for i,d in enumerate(Dd):
            yv=9-i; yy=ax.py(yv); hh=ax.h/10*0.62
            f.add(f'<rect x="{ax.x:.1f}" y="{yy-hh/2:.1f}" width="{ax.px(d[key])-ax.x:.1f}" height="{hh:.1f}" rx="2" fill="{col}"/>')
            f.text(ax.x-8,yy+4,d['label'],size=12,anchor='end'); f.text(ax.px(d[key])+6,yy+4,fm(d[key]),size=11.5,color=INK)
    tot=T['dose_totals']
    f.footnote(f"Totals: {tot['updates']:,} updates, {tot['supervised_trained']:,} supervised tokens, {tot['presented_trained']:,} presented tokens. Source: plots/data/derived/tables.json (dose).")
    f.plotted={d['skill']:[d['updates_applied'],d['supervised_tokens_trained']] for d in Dd}
    f.caption='Training dose per skill. COGS received a third of all updates and half of all supervised tokens; the other nine received between 2,835 and 9,850 updates each.'
    f.alt='Two horizontal bar charts with ten skills each: updates applied (COGS 21,309 largest, Tessel 2,835 smallest) and supervised tokens (COGS 1.1 million largest).'
    f.source('plots/data/derived/tables.json'); return f

def f7_loss_acc():
    va=series('held_out_loss.json'); O={o['skill']:o for o in T['own_end_vs_final']}
    f=Figure('ts_f7_loss_vs_accuracy',height=540,title='Held-out loss does not predict exact-match accuracy')
    box=f.panel(36,60,808,440,'Each skill at the end of its own teach','x: held-out loss at the endpoint sweep (nats, log scale) · y: correct of 225')
    ax=f.axes(box,(1e-5,1),(0,230),xlog=True); ax.grid(yticks=[0,45,90,135,180,225],ylabel_fmt=lambda t:f"{int(t)}",xticks=[1e-5,1e-4,1e-3,1e-2,1e-1,1],xlabel_fmt=lambda t:('%g'%t),xlabel='held-out loss at own-end (nats)',ylabel='correct of 225')
    pts=[]
    for i,s in enumerate(SK):
        vs=[q for q in va if q['teach_index']==i+1 and q['monitored_skill']==s]
        if not vs: continue
        L=vs[-1]['held_out_loss']; A=O[s]['own_end_correct']; pts.append((s,L,A)); ax.dot(max(L,1e-5),A,SC[s],6); ax.label(max(L,1e-5),A,LAB[s],color=SC[s],size=12,dx=8)
    f.footnote('Loss is the mean per-token loss over the panel rows in the last sweep of the skill\'s own segment; accuracy needs every token right. Source: plots/data/series/held_out_loss.json, plots/data/derived/tables.json.')
    f.caption='A low held-out loss is necessary but not sufficient for exact-match accuracy: Oriel and Meridian sit at loss levels similar to skills that score far higher, because a single wrong token anywhere in a long structured answer costs the whole row.'
    f.alt='Scatter plot of ten skills, held-out loss on a log x-axis against correct-of-225 on the y-axis, with skill names as labels.'
    f.source('plots/data/series/held_out_loss.json'); f.source('plots/data/derived/tables.json'); return f

def f8_sentinel_base():
    S=T['sentinel']; B=T['base_battery']; f=Figure('ts_f8_sentinel_base',height=560,title='General capability across the stream')
    f.legend([('sentinel, raw likelihood choice',TEAL,'line'),('sentinel, length-normalized',DEEP,'dash'),('full battery (16,481 items)',AMBER,'box')])
    b1=f.panel(36,86,500,420,'Endpoint sentinel at all eleven checkpoints','arc 128 · hellaswag 128 · mmlu 114 · winogrande 128; correct of 498')
    ax=f.axes(b1,(-0.3,10.3),(300,420)); ax.grid(yticks=[300,330,360,390,420],ylabel_fmt=lambda t:f"{int(t)}",xticks=list(range(11)),xlabel_fmt=lambda t:f"{int(t)}",xlabel='after teach')
    ax.line([(s['teach_index'],s['total_correct']) for s in S],TEAL,2); ax.line([(s['teach_index'],s['total_correct_normalized']) for s in S],DEEP,2,dash='4 4')
    for s in S: ax.dot(s['teach_index'],s['total_correct'],TEAL,3.5)
    lo=min(s['total_correct'] for s in S); hi=max(s['total_correct'] for s in S); ax.label(10,S[-1]['total_correct'],f"{lo}–{hi} raw",color=TEAL,size=11.5,anchor='end',dx=-6,dy=-8)
    b2=f.panel(560,86,284,420,'Full battery at 0 / 5 / 10','5-shot likelihood; accuracy')
    ax2=f.axes(b2,(-0.5,2.5),(0.65,0.9)); ax2.grid(yticks=[0.65,0.70,0.75,0.80,0.85,0.90],ylabel_fmt=lambda t:f"{t:.2f}",xticks=[0,1,2],xlabel_fmt=lambda t:['0','5','10'][int(round(t))],xlabel='after teach')
    keys=[('step_zero',0),('after_teach_05',1),('after_teach_10',2)]
    for metric,lab,col in [('mmlu_macro_57','MMLU (57-subject macro)',TEAL),('winogrande_acc','WinoGrande',DEEP),('arc_acc','ARC-Challenge',AMBER)]:
        pts=[(x,B[k][metric]) for k,x in keys]; ax2.line(pts,col,2)
        for x,v in pts: ax2.dot(x,v,col,3.5)
        ax2.label(2,pts[-1][1],lab,color=col,size=11,anchor='end',dx=-6,dy=-7)
    f.footnote('Sentinel and battery are likelihood-based choices scored by the reference harness port. Values: plots/data/derived/tables.json (sentinel, base_battery).')
    f.units='correct of 498 (left); accuracy (right)'; f.plotted={'sentinel_raw':[s_['total_correct'] for s_ in S],'sentinel_normalized':[s_['total_correct_normalized'] for s_ in S],'battery':{k:{m:B[k][m] for m in ('mmlu_macro_57','winogrande_acc','arc_acc')} for k,_ in keys}}
    f.caption=f"The base does not move materially on the measured benchmarks: the 498-item sentinel stays between {lo} and {hi} correct across all eleven checkpoints, and the full battery after ten teaches reads MMLU {B['after_teach_10']['mmlu_macro_57']:.4f}, ARC {B['after_teach_10']['arc_acc']:.4f}, WinoGrande {B['after_teach_10']['winogrande_acc']:.4f} against {B['step_zero']['mmlu_macro_57']:.4f}, {B['step_zero']['arc_acc']:.4f}, {B['step_zero']['winogrande_acc']:.4f} at step zero."
    f.alt='Left: two flat lines across eleven checkpoints for the 498-item sentinel. Right: three nearly flat lines (MMLU, WinoGrande, ARC) at checkpoints 0, 5 and 10.'
    f.source('plots/data/derived/tables.json'); return f

def f9_oriel():
    Oc=json.load(open(os.path.join(D,'derived','oriel_components.json')))
    f=Figure('ts_f9_oriel_components',height=520,title='Oriel from teach 9 to teach 10: which part of the answer changed')
    f.legend([('after teach 9 (15 of 225 correct)',AMBER,'box'),('after teach 10 (9 of 225 correct)',TEAL,'box')])
    comps=[('escaping_valid','escaping'),('header_correct','header'),('transformed_payload_correct','payload'),('decoded_length_correct','length'),('checksum_correct','checksum')]
    tb=Oc['all_rows_component_totals_teach9']; ta=Oc['all_rows_component_totals_teach10']
    box=f.panel(36,86,808,380,'Rows with each component correct, all 225 panel rows','a row counts as correct only when every component is right')
    ax=f.axes(box,(-0.6,4.6),(0,240)); ax.grid(yticks=[0,45,90,135,180,225],ylabel_fmt=lambda t:f"{int(t)}",xticks=[],ylabel='rows of 225')
    for i,(k,lab) in enumerate(comps):
        b=tb.get(k); a=ta.get(k)
        if b is None or a is None: continue
        ax.bar(i-0.19,b,28,AMBER,label=str(b)); ax.bar(i+0.19,a,28,TEAL,label=str(a)); f.text(ax.px(i),ax.y+ax.h+18,lab,size=12.5,color=MUTED,anchor='middle')
    tr=Oc['transitions']
    f.footnote(f"Paired 225 rows at both checkpoints: correct→wrong {tr.get('correct->wrong')}, wrong→correct {tr.get('wrong->correct')}, correct→correct {tr.get('correct->correct')}. Every lost row had header, payload, escaping and length right and the checksum wrong. Source: plots/data/derived/oriel_components.json.")
    f.caption='The Oriel decline is localized: between the two checkpoints the header, transformed payload, escaping and decoded length stay correct on essentially all rows, while the final checksum value is right on 15 rows, then 11. Seven rows lost that one value; one row gained it.'
    f.alt='Grouped bar chart with five component groups (escaping, header, payload, length, checksum), amber bars for teach 9 and teal bars for teach 10; the first four groups are near 225 at both checkpoints; the checksum group is 15 then 11.'
    f.source('plots/data/derived/oriel_components.json'); return f

def f0_key_summary():
    """Key summary: what each skill scores at every checkpoint, with the base line for scale."""
    M=T['matrix']; S=T['sentinel']
    f=Figure('ts_f0_key_summary',height=640,title='Accuracy and retention: every skill at every checkpoint')
    box=f.panel(36,86,612,448,'Every skill on its own 225-row panel',
                'Ten skills taught one after another. A line starts at the checkpoint where its skill was taught and runs to the end of the stream; the base is scored at all eleven checkpoints.')
    ax=f.axes(box,(-0.45,10.45),(0,100))
    ax.grid(yticks=[0,25,50,75,100],ylabel_fmt=lambda t:f"{int(t)}%",xticks=list(range(11)),xlabel_fmt=lambda t:f"{int(t)}",
            xlabel='checkpoint (0 = before any teaching)',ylabel='percent correct')
    base=[(s_['teach_index'],100.0*s_['total_correct']/s_['total_n']) for s_ in S]
    ax.line(base,VOID,2,dash='5 4')
    for x,y in base: ax.dot(x,y,VOID,2.8,stroke=PAPER)
    ax.label(10,base[-1][1],'base',color=VOID,size=11.5,anchor='end',dx=-8,dy=-10,weight='600')
    plotted={}
    for i,sk in enumerate(SK):
        t0=i+1; col=SC[sk]
        pts=[(k,100.0*M[k][sk]/225.0) for k in range(t0,11) if M[k].get(sk) is not None]
        if not pts: continue
        ax.line(pts,col,2.0)
        ax.dot(pts[0][0],pts[0][1],col,4.8,stroke=PAPER)                  # the teach that put it there
        plotted[sk]={'taught_at':t0,'at_step_zero':M[0][sk],'at_own_teach':M[t0][sk],'at_final':M[10][sk]}
    ax.dot(0,0,INK,5.2,stroke=PAPER)                                      # all ten sit here before teaching
    f.text(ax.px(0)+10,ax.py(0)-12,'all ten skills: 0 before teaching',size=11.5,color=MUTED,italic=True)
    lx=672; f.text(lx,118,'taught at checkpoint',size=11.5,color=MUTED)
    for i,sk in enumerate(SK):
        yy=142+i*26; col=SC[sk]
        f.add(f'<line x1="{lx}" y1="{yy-4}" x2="{lx+18}" y2="{yy-4}" stroke="{col}" stroke-width="2.4" stroke-linecap="round"/>')
        f.add(f'<circle cx="{lx+9}" cy="{yy-4}" r="4.4" fill="{col}" stroke="{PAPER}" stroke-width="1.2"/>')
        f.text(lx+26,yy,LAB[sk],size=13,color=INK)
        f.text(844,yy,str(i+1),size=13,color=MUTED,anchor='end')
    yy=142+10*26+10
    f.add(f'<line x1="{lx}" y1="{yy-4}" x2="{lx+18}" y2="{yy-4}" stroke="{VOID}" stroke-width="2" stroke-dasharray="5 4"/>')
    f.text(lx+26,yy,'base, 498 items',size=13,color=MUTED)
    for j,l in enumerate(['A skill is scored only','from its own teach onward,','so nothing is drawn to','the left of its first dot.']):
        f.text(lx,yy+30+j*16,l,size=11.5,color=MUTED)
    zt=sum(M[0][s_] for s_ in SK); ft=sum(M[10][s_] for s_ in SK)
    f.units='percent correct (skills: of 225 panel rows each; base: of 498 sentinel items)'
    f.transforms=['counts divided by their own denominator so the skills and the base share one axis']
    f.plotted={'skills':plotted,'step_zero_total':zt,'final_total':ft,'base_percent':[round(v,2) for _,v in base]}
    f.footnote(f"Before any teaching the base answers {zt} of the 2,250 panel rows, so every point above the axis was acquired during the run. Each skill is then scored on its own 225-row held-out panel at every checkpoint from its teach onward; it is not scored in between. After all ten teaches {ft:,} of 2,250 are correct. The base line is the 498-item sentinel on its own denominator. Source: plots/data/derived/tables.json.")
    f.caption=f"One picture of the run: nothing is answered before teaching, each skill jumps at its own teach, and every skill holds its level while the skills after it are taught. {ft:,} of 2,250 panel rows are correct at the end, from {zt} at the start, and the base line stays flat throughout."
    f.alt='Line chart, checkpoints 0 to 10 on the horizontal axis and percent correct on the vertical. A single dot at the origin marks that all ten skills answer nothing before teaching. Ten coloured lines, one per skill, each beginning with a filled dot at the checkpoint where that skill was taught and running flat to the right. A grey dashed line for the base sentinel runs flat near 70 percent across all eleven checkpoints. A legend on the right names the ten skills and the checkpoint each was taught at.'
    f.source('plots/data/derived/tables.json'); return f


FIGS={'ts_f0_key_summary':f0_key_summary,'ts_f1_stream':f1_stream,'ts_f2_per_skill':f2_per_skill,'ts_f2z_per_skill_zoom':f2_zoom,'ts_f3_retention':f3_retention,'ts_f4_matrix':f4_matrix,'ts_f5_own_vs_final':f5_ownfinal,'ts_f6_dose':f6_dose,'ts_f7_loss_vs_accuracy':f7_loss_acc,'ts_f8_sentinel_base':f8_sentinel_base,'ts_f9_oriel_components':f9_oriel}
