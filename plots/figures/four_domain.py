"""Four-domain (Plasticity Without Forgetting) figures rebuilt in the house style from the measured receipts.
Public naming rule: conditions named by capacity only (1x / 2x) and LoRA r256."""
import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'lib'))
from housesvg import *
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D=os.path.join(W,'plots','data','four_domain')
ORDER=["a_book_class","d_yoruba","c_language","d_news"]; DL={"a_book_class":"US government documents (EN)","d_yoruba":"Yoruba","c_language":"Amharic","d_news":"multilingual news"}
ARMS=[('learner_1x','Learner 1.0 (1x)',TEAL),('learner_2x','Learner 1.0 (2x)',DEEP),('lora_r256','LoRA r256',AMBER)]
def load(arm):
    d=json.load(open(os.path.join(D,arm,'A_equivalence.json'))); m=d.get('measured',d)
    tr=[json.loads(l) for l in open(os.path.join(D,arm,'train_curve.jsonl')) if l.strip()] if os.path.exists(os.path.join(D,arm,'train_curve.jsonl')) else []
    va=[json.loads(l) for l in open(os.path.join(D,arm,'val_curve.jsonl')) if l.strip()]
    if arm=='lora_r256':
        pack={'base':m['base_loss_nats'],'own':m['own_loss_nats'],'bwt':m['bwt_per_domain'],'acq':m['acquisition_nats'],'ctrl':{'base':m.get('collateral_base'),'final':(m.get('collateral_base') or 0)+(m.get('collateral_nats') or 0)},'n_tr':d['build']['n_trainable']}
    else:
        pack={'base':d['base_loss_nats'],'own':m['own_loss_at_last_train'],'bwt':m['per_source_bwt'],'acq':m['acquisition_nats'],'ctrl':m['control_domain'],'n_tr':d['n_trainable_params']}
    pack['tr']=tr; pack['va']=va; return pack
def fd_f1_stream():
    f=Figure('fd_f1_stream',height=600,title='Four domains in sequence: training loss for three conditions')
    f.legend([(l,c,'line') for _,l,c in ARMS])
    box=f.panel(36,86,808,460,'Same corpus, same order, one pass','training loss, nats; lines smoothed (moving average, span 31), pale band = raw range of the 1x condition')
    packs={a:load(a) for a,_,_ in ARMS}
    def p2(tr):
        rows=[r for r in tr if r.get('phase') in ORDER]
        if not rows: return []
        g0=min(r['gstep'] for r in rows); return [(r['gstep']-g0,r['phase'],r['loss']) for r in rows]
    series={a:p2(packs[a]['tr']) for a,_,_ in ARMS}
    xmax=max((s[-1][0] for s in series.values() if s),default=1); allv=[v for s in series.values() for _,_,v in s]
    ax=f.axes(box,(0,xmax),(min(allv)*0.9 if allv else 1,max(allv)*1.05 if allv else 3)); ax.grid(xlabel='training step (single pass over the four domains)',ylabel='training loss (nats)',xlabel_fmt=lambda t:f"{int(t):,}")
    # domain bands from the 1x arm
    s1=series['learner_1x']
    if s1:
        cur=None; start=0
        for x,ph,_ in s1:
            if ph!=cur:
                if cur is not None: f.text(ax.px((start+x)/2),ax.y+14,DL[cur],size=11.5,color=DEEP,anchor='middle',weight='600'); ax.vline(x)
                cur=ph; start=x
        f.text(ax.px((start+s1[-1][0])/2),ax.y+14,DL[cur],size=11.5,color=DEEP,anchor='middle',weight='600')
    for a,l,c in ARMS:
        s=series[a]
        if not s: continue
        if a=='learner_1x':
            lo_,hi_=envelope([(x,v) for x,_,v in s],600); ax.area(lo_,hi_,c,0.13)
        ax.line([(x,v) for (x,_,_),v in zip(s,ema([v for _,_,v in s],31))],c,1.6)
    f.units='nats per token'; f.smoothing='exponential moving average, span 31 steps (lines); none (pale band: raw minimum to maximum for the 1x condition)'; f.transforms=['x axis is the step within the four-domain stream, starting at 1']
    f.plotted={a:{'points':len(series[a]),'first':series[a][0][2],'last':series[a][-1][2]} for a,_,_ in ARMS if series[a]}
    f.footnote('All 1,200 steps are drawn for every condition; nothing is subsampled. The unsmoothed per-step loss of all three conditions is in the companion figure fd_f1b_stream_raw. Source: train_curve.jsonl per condition. Conditions are named by trainable capacity only.')
    f.caption='Three conditions trained on the same four-domain stream. All three learn each domain in turn; the difference between them shows up afterwards, in what they keep.'
    f.alt='Line chart of training loss over one pass through four domains (US government documents, Yoruba, Amharic, news) for three conditions: Learner 1.0 (1x), Learner 1.0 (2x), LoRA r256.'
    for a,_,_ in ARMS: f.source(f'plots/data/four_domain/{a}/train_curve.jsonl')
    return f
def fd_f2_bwt():
    f=Figure('fd_f2_bwt',height=520,title='What each condition forgot, and what it learned')
    f.legend([(l,c,'box') for _,l,c in ARMS])
    packs={a:load(a) for a,_,_ in ARMS}
    b1=f.panel(36,86,470,380,'What it forgot','change in loss on the three earlier domains after the fourth was trained','nats; positive is worse')
    ax=f.axes(b1,(-0.6,2.6),(-0.02,0.08)); ax.grid(yticks=[-0.02,0,0.02,0.04,0.06,0.08],ylabel_fmt=lambda t:f"{t:+.2f}" if t else "0",xticks=[])
    ax.hline(0,color=VOID,dash=None,width=1.2)
    for i,dm in enumerate(ORDER[:3]):
        f.text(ax.px(i),ax.y+ax.h+18,DL[dm],size=11.5,color=MUTED,anchor='middle')
        for k,(a,l,c) in enumerate(ARMS):
            v=packs[a]['bwt'][dm]; ax.bar(i+(k-1)*0.24,v,26,c,label=(f"{v:+.3f}" if abs(v)>=0.005 else None))
    b2=f.panel(530,86,314,380,'What it learned','loss reduction on the trained domain, mean of four','nats')
    ax2=f.axes(b2,(-0.6,2.6),(0,0.2)); ax2.grid(yticks=[0,0.05,0.1,0.15,0.2],ylabel_fmt=lambda t:f"{t:.2f}",xticks=[])
    for k,(a,l,c) in enumerate(ARMS):
        m=sum(packs[a]['acq'].values())/4; ax2.bar(k,m,54,c,label=f"{m:.3f}"); f.text(ax2.px(k),ax2.y+ax2.h+18,l,size=11.5,color=MUTED,anchor='middle')
    f.footnote(f"Trainable parameters: Learner 1.0 (1x) {packs['learner_1x']['n_tr']/1e9:.2f} billion · Learner 1.0 (2x) {packs['learner_2x']['n_tr']/1e9:.2f} billion · LoRA r256 {packs['lora_r256']['n_tr']/1e9:.2f} billion. Source: A_equivalence.json per arm (measured block).")
    f.units='nats per token'; f.plotted={a:{'bwt':packs[a]['bwt'],'mean_acquisition':sum(packs[a]['acq'].values())/4} for a,_,_ in ARMS}
    f.caption='Both Learner 1.0 conditions keep the earlier domains within a few thousandths of a nat while LoRA r256 gives back 0.07, 0.06 and 0.03 nats; all three learned each domain by about the same amount.'
    f.alt='Left: grouped bars per earlier domain showing forgetting in nats; Learner 1.0 bars are flat at zero, LoRA bars rise to 0.07. Right: three bars of mean acquisition, all near 0.15 nats.'
    for a,_,_ in ARMS: f.source(f'plots/data/four_domain/{a}/A_equivalence.json')
    return f
def fd_f3_control():
    f=Figure('fd_f3_control',height=570,title='The never-trained control bank')
    f.legend([(l,c,'line') for _,l,c in ARMS[:2]])
    packs={a:load(a) for a,_,_ in ARMS[:2]}
    box=f.panel(36,86,808,360,'Held-out control loss after each domain','8 control windows per measurement, mostly Amharic text; no control window is ever trained; nats')
    ys=[]
    for a in packs: 
        c=packs[a]['ctrl']; ys+=[c['base']]+[t['control_loss'] for t in c.get('trace',[])]
    ax=f.axes(box,(-0.3,4.3),(min(ys)-0.02,max(ys)+0.02)); ax.grid(yticks=nice_ticks(min(ys)-0.02,max(ys)+0.02,5),ylabel_fmt=lambda t:f"{t:.2f}",xticks=[0,1,2,3,4],xlabel_fmt=lambda t:(['base reference']+[DL[d] for d in ORDER])[int(round(t))],xlabel='after training')
    for a,l,c in ARMS[:2]:
        ct=packs[a]['ctrl']; pts=[(i+1,t['control_loss']) for i,t in enumerate(ct.get('trace',[]))]; ax.line(pts,c,2); ax.hline(ct['base'],color=c,dash='4 4',width=1.1)
        for x,v in [(0,ct['base'])]+pts: ax.dot(x,v,c,3.5)
    f.footnote('Both Learner 1.0 conditions were scored on 8 windows of the 64-window control bank after each domain. The LoRA condition was scored once before and once after the stream on all 64 windows (1.377 to 1.293 nats), a different sample, so it is not drawn on this axis. Of the 64 control windows 59 are Amharic text; none is a window of the Amharic domain. The dashed levels are each condition\'s recorded base reference; the first measurement inside the stream is the one after the first domain. Source: A_equivalence.json control_domain.')
    f.units='nats per token'; f.plotted={a:[packs[a]['ctrl']['base']]+[t['control_loss'] for t in packs[a]['ctrl'].get('trace',[])] for a in packs}
    f.caption='On 8 never-trained control windows the two Learner 1.0 conditions move by about 0.01 nats across the stream and sit about 0.12 nats below their recorded base reference. The figure does not isolate how much of that difference arose inside the displayed stream.'
    f.alt='Two nearly flat lines near 1.28 nats across four points, one after each domain, with two dashed reference levels near 1.39 nats above them.'
    for a,_,_ in ARMS[:2]: f.source(f'plots/data/four_domain/{a}/A_equivalence.json')
    return f
def fd_f4_validation():
    f=Figure('fd_f4_validation',height=810,title='Held-out loss inside each domain, all three conditions')
    f.legend([(l,c,'line') for _,l,c in ARMS]+[('base reference',VOID,'dash')])
    packs={a:load(a) for a,_,_ in ARMS}; plotted={}
    for k,dm in enumerate(ORDER):
        r=k//2; c=k%2; box=f.panel(36+c*416,90+r*320,392,300,f"{k+1}. {DL[dm]}",'8 held-out windows, every 25 steps while the domain is trained; nats')
        cur={a:sorted({(q['gstep'],q['val_loss']) for q in packs[a]['va'] if q['domain']==dm}) for a,_,_ in ARMS}
        g0=min(g for a in cur for g,_ in cur[a])-25; base=packs['learner_1x']['base'][dm]
        ys=[v for a in cur for _,v in cur[a]]+[base]; ax=f.axes(box,(0,300),(min(ys)-0.01,max(ys)+0.01))
        ax.grid(yticks=nice_ticks(min(ys)-0.01,max(ys)+0.01,5),ylabel_fmt=lambda t:f"{t:.2f}",xticks=[0,100,200,300],xlabel_fmt=lambda t:f"{int(t)}",xlabel='step within the domain')
        ax.hline(base,color=VOID,dash='4 4')
        # Where the starting loss value comes from. The base
        # reference now carries its number in every panel, and in the FIRST domain -- the only one
        # where the model at step 0 provably is the untrained base -- each condition's curve is
        # carried back to its own base with a dotted segment. In the later domains the model has
        # already trained on earlier ones and its loss there at step 0 was not measured, so nothing
        # is drawn into that gap.
        ax.label(300, base, f"base {base:.2f}", color=VOID, size=11, anchor='end', dy=-6)
        for a,l,col in ARMS:
            pts=[(g-g0,v) for g,v in cur[a]]
            if k == 0:
                b_a = packs[a]['base'][dm]
                ax.line([(0,b_a), pts[0]], col, 1.4, dash='3 3', opacity=.75)
                ax.dot(0, b_a, PAPER, 3.4); ax.dot(0, b_a, col, 2.0)
                plotted[f'{a}:{dm}:start'] = [0, round(b_a, 6)]
            ax.line(pts,col,2)
            for x,v in pts: ax.dot(x,v,col,2.4)
            plotted[f'{a}:{dm}']={'first':pts[0],'last':pts[-1],'n':len(pts)}
    f.footnote('Every recorded validation point is drawn (12 per condition per domain; the first is at step 25; in the first panel each condition is also carried back to its own recorded base at step 0, where the model is the untrained base -- in the later panels the model has already trained on earlier domains and its loss at step 0 was not measured, so no segment is drawn there). The three conditions share one axis inside each panel; the loss range differs between panels because the domains differ. The dashed line is the recorded base reference on the same 8 windows. Source: val_curve.jsonl per condition.')
    f.caption='Held-out loss while each domain is trained, against the recorded base reference (dashed, value shown). The Learner 1.0 conditions are close to their final level by the first measurement at step 25; the LoRA condition gets there over the 300 steps. All three end each domain at a similar level.'
    f.alt='Four panels, one per domain, each with three lines of held-out loss against step within the domain and a dashed base-reference line above them; the two Learner 1.0 lines are nearly flat from step 25, the LoRA line falls steadily.'
    f.units='nats per token'; f.smoothing='none'; f.plotted=plotted
    for a,_,_ in ARMS: f.source(f'plots/data/four_domain/{a}/val_curve.jsonl')
    return f
def fd_f1b_stream_raw():
    f=Figure('fd_f1b_stream_raw',height=1010,title='The unsmoothed training loss, one panel per condition')
    f.legend([(l,c,'line') for _,l,c in ARMS])
    packs={a:load(a) for a,_,_ in ARMS}; series={}
    for a,_,_ in ARMS:
        rows=[r for r in packs[a]['tr'] if r.get('phase') in ORDER]; g0=min(r['gstep'] for r in rows); series[a]=[(r['gstep']-g0,r['phase'],r['loss']) for r in rows]
    allv=[v for s_ in series.values() for _,_,v in s_]; xmax=max(s_[-1][0] for s_ in series.values()); ylim=(min(allv)*0.9,max(allv)*1.05); plotted={}
    for k,(a,l,c) in enumerate(ARMS):
        box=f.panel(36,86+k*296,808,280,l,'every one of the 1,200 per-step losses, unsmoothed (thin line); moving average, span 31 (heavy line); nats')
        ax=f.axes(box,(0,xmax),ylim); ax.grid(xlabel=('training step (single pass over the four domains)' if k==2 else None),ylabel='training loss (nats)',xlabel_fmt=lambda t:f"{int(t):,}")
        s_=series[a]; cur=None; start=0
        for x,ph,_ in s_:
            if ph!=cur:
                if cur is not None: f.text(ax.px((start+x)/2),ax.y+14,DL[cur],size=11,color=DEEP,anchor='middle',weight='600'); ax.vline(x)
                cur=ph; start=x
        f.text(ax.px((start+s_[-1][0])/2),ax.y+14,DL[cur],size=11,color=DEEP,anchor='middle',weight='600')
        ax.line([(x,v) for x,_,v in s_],c,0.7,opacity=0.45); ax.line([(x,v) for (x,_,_),v in zip(s_,ema([v for _,_,v in s_],31))],c,1.8)
        vs=[v for _,_,v in s_]; plotted[a]={'points':len(s_),'min':min(vs),'max':max(vs),'first':vs[0],'last':vs[-1]}
    f.units='nats per token'; f.smoothing='none (thin line: every per-step loss); exponential moving average, span 31 steps (heavy line)'; f.transforms=['x axis is the step within the four-domain stream, starting at 1','the three panels share one x axis and one y axis']
    f.plotted=plotted
    f.footnote('Each update trains on one 256-token window, so a per-step loss is the loss of a single window and varies with the text. The three panels share identical axes. No point is dropped or subsampled. Source: train_curve.jsonl per condition.')
    f.caption='The raw per-step training loss behind the smoothed stream figure, for all three conditions on identical axes.'
    f.alt='Three stacked line charts, one per condition, each showing a jagged per-step training loss over 1,200 steps with a heavier smoothed line through it, and vertical rules at the three domain changes.'
    for a,_,_ in ARMS: f.source(f'plots/data/four_domain/{a}/train_curve.jsonl')
    return f
FIGS={'fd_f4_validation':fd_f4_validation,'fd_f1_stream':fd_f1_stream,'fd_f1b_stream_raw':fd_f1b_stream_raw,'fd_f2_bwt':fd_f2_bwt,'fd_f3_control':fd_f3_control}
