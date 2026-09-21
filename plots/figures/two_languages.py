"""Two invented languages (the Learner 1.0 one-pass recording + the original sequential LoRA comparator on byte-identical corpora)."""
import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'lib'))
from housesvg import *
W=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D=os.path.join(W,'plots','data'); TL=json.load(open(os.path.join(D,'two_languages.json')))
def tl_f1_curves():
    f=Figure('tl_f1_curves',height=560,title='Two invented languages, taught one after the other in one pass')
    f.legend([('training loss, each update',PALE_TEAL,'line'),('15-update average',TEAL,'line'),('held-out loss on 2 withheld windows',AMBER,'box')])
    O=TL['learner_onepass']; nv=O['updates']['velenic']; nm=O['updates']['morvath']; total=nv+nm; plotted={}
    series={'velenic':[(k+1,y) for k,y in enumerate(O['train_loss']['velenic'])],'morvath':[(nv+k+1,y) for k,y in enumerate(O['train_loss']['morvath'])]}
    ylim=(0,max(y for s in series.values() for _,y in s)*1.05)
    def avg(pts,w=15): return [(pts[k][0],sum(y for _,y in pts[max(0,k-w+1):k+1])/len(pts[max(0,k-w+1):k+1])) for k in range(len(pts))]
    for k,lang in enumerate(('velenic','morvath')):
        n=O['updates'][lang]; H=O['held_out'][lang]
        box=f.panel(36+k*416,86,392,400,f"{k+1}. {lang.capitalize()}",f"{n} training windows of 256 tokens ({n*256:,} tokens), each presented once")
        ax=f.axes(box,(0,total),ylim); ax.grid(xlabel='update',ylabel='loss (nats)',xlabel_fmt=lambda t:f"{int(t)}",xticks=[0,nv,total])
        ax.vline(nv,label=None)
        ax.line(series[lang],PALE_TEAL,1.1); ax.line(avg(series[lang]),TEAL,2)
        pts=[(0,H['before']),(nv,H['after_language_1']),(total,H['after_language_2'])]
        for q,(x,y) in enumerate(pts):
            ax.dot(x,y,AMBER,4.5); ax.label(x,y,f"{y:.4f}",color=AMBER,size=11.5,dx=(8 if q<2 else -8),dy=(22 if (q==2 and lang=='morvath') else (-8 if q!=1 or lang=='morvath' else 16)),anchor=('start' if q<2 else 'end'),weight='600')
        plotted[lang]={'updates':n,'held_out':H,'train_loss_points':len(series[lang]),'first_train_loss':series[lang][0][1],'last_train_loss':series[lang][-1][1]}
    f.footnote("Held-out loss is read at three fixed points (before any teaching, after Velenic, after Morvath) on two 256-token windows withheld from each corpus; it is not a continuous validation curve. The vertical rule marks the end of the Velenic teach, update 274. Source: plots/data/two_languages.json (learner_onepass block).")
    V=O['held_out']['velenic']; M=O['held_out']['morvath']
    f.caption=f"Learner 1.0, one-pass recording. Velenic's held-out loss falls from {V['before']:.4f} to {V['after_language_1']:.4f} nats during its own teach and reads {V['after_language_2']:.4f} after Morvath is taught. Morvath's falls from {M['after_language_1']:.4f} to {M['after_language_2']:.4f} during its teach."
    f.alt='Two panels on a shared loss axis and a shared update axis from 0 to 627. Each shows a pale raw training-loss trace with a darker 15-update average during that language\'s own teach, and three amber held-out points.'
    f.units='nats per token'; f.smoothing='trailing 15-update mean, drawn over the raw trace'; f.plotted=plotted
    f.source('plots/data/two_languages.json'); return f
def tl_f2_lora():
    f=Figure('tl_f2_lora_sequential',height=520,title='The same two corpora through a single LoRA adapter, in sequence')
    f.legend([('language 1',TEAL,'line'),('language 2',DEEP,'line'),('English control',VOID,'dash')])
    S=TL['lora']['stages']; st=['stage_base','stage_after_velenic','stage_after_morvath']; lab=['base','after language 1','after language 2']
    box=f.panel(36,86,808,380,'Cross-entropy on each language after each stage','one adapter carried through both teaches; nats, lower is better')
    ys=[v for s in st for v in S[s].values()]; ax=f.axes(box,(-0.3,2.3),(1,9)); ax.grid(yticks=[1,3,5,7,9],ylabel_fmt=lambda t:f"{int(t)}",xticks=[0,1,2],xlabel_fmt=lambda t:lab[int(round(t))],ylabel='cross-entropy (nats)')
    for key,col,name,dash in [('ce_velenic',TEAL,'language 1',None),('ce_morvath',DEEP,'language 2',None),('ce_english',VOID,'English control','4 4')]:
        pts=[(i,S[s][key]) for i,s in enumerate(st)]; ax.line(pts,col,2,dash=dash)
        for x,v in pts: ax.dot(x,v,col,3.5); ax.label(x,v,f"{v:.2f}",color=col,size=11,dx=(8 if x<2 else -8),dy=(-6 if key!='ce_morvath' else 14),anchor=('start' if x<2 else 'end'))
    f.footnote(f"Rank {TL['lora']['cfg']['rank']} on the feed-forward projections, {TL['lora']['n_trainable']/1e9:.2f} billion trainable parameters, learning rate {TL['lora']['cfg']['lr']}. Source: plots/data/two_languages.json (lora block).")
    f.units='nats per token'; f.plotted=S
    f.caption='A single adapter learns language 1 (4.35 to 2.22 nats), then learning language 2 pushes language 1 to 6.00 nats, worse than before it was ever taught. English is untouched: the damage is between the two taught skills.'
    f.alt='Line chart with three points per line (base, after language 1, after language 2): language 1 falls then rises above its starting value; language 2 rises then falls; the English control stays flat near 3.'
    f.source('plots/data/two_languages.json'); return f
def tl_f3_matrix():
    f=Figure('tl_f3_generation_matrix',height=470,title='Generation identity after each stage: Learner 1.0 versus LoRA')
    M0=TL['learner_onepass']['generation_matrix']; M={'before':M0['before'],'after_l1':M0['after_language_1'],'after_l2':M0['after_language_2']}; S=TL['lora']['stages']
    f.legend([('cross-language contamination (share of generated text in the other language)',AMBER,'box')])
    box=f.panel(36,86,808,330,'Learner 1.0 (greedy) contamination is 0.00 in every cell','LoRA, original comparator recording: 1.00 after language 1 on language-2 prompts, 0.96 after language 2 on language-1 prompts',pad=(20,30,0,0))
    cols=['before','after_l1','after_l2']; rows=[('velenic','language 1 prompts'),('morvath','language 2 prompts')]
    x0=36+230; y0=box[1]+6; cw=150; ch=54
    for j,c in enumerate(cols): f.text(x0+j*cw+cw/2,y0-8,c.replace('_',' ').replace('l1','language 1').replace('l2','language 2'),size=12,color=MUTED,anchor='middle')
    lora={('velenic','after_l1'):0.0,('morvath','after_l1'):1.0,('velenic','after_l2'):0.96,('morvath','after_l2'):0.0,('velenic','before'):0.0,('morvath','before'):0.0}
    for i,(lang,rl) in enumerate(rows):
        yy=y0+i*ch*2; f.text(x0-10,yy+ch/2+4,rl+', Learner 1.0',size=12,anchor='end'); f.text(x0-10,yy+ch+ch/2+4,rl+', LoRA',size=12,anchor='end')
        for j,c in enumerate(cols):
            v=M[c][lang]['contamination'] if lang in M[c] else None; lv=lora[(lang,c)]
            for r2,val in enumerate([v,lv]):
                yv=yy+r2*ch; xx=x0+j*cw
                if val is None: f.add(f'<rect x="{xx+2}" y="{yv+2}" width="{cw-4}" height="{ch-4}" rx="3" fill="#F4F4F1"/>'); continue
                col=f'rgb({int(255-(255-0xB4)*val)},{int(255-(255-0x76)*val)},{int(255-(255-0x2A)*val)})'
                f.add(f'<rect x="{xx+2}" y="{yv+2}" width="{cw-4}" height="{ch-4}" rx="3" fill="{col}"/>'); f.text(xx+cw/2,yv+ch/2+5,f"{val:.2f}",size=13,anchor='middle',weight='600',color=(PAPER if val>0.5 else INK))
    f.footnote('Means over 8 prompts per cell, greedy decoding. Learner 1.0: one-pass recording (answers/session.json), English controls 4/4 at every stage. LoRA: original comparator recording. Source: plots/data/two_languages.json.')
    f.plotted={'product':M,'lora':{f'{a}|{b}':v for (a,b),v in lora.items()}}
    f.caption='Where the LoRA adapter answers language-1 prompts in language 2 after the second teach (0.96), Learner 1.0 keeps the two apart (0.00 in every cell).'
    f.alt='A grid of contamination values for Learner 1.0 and LoRA rows across three stages; Learner 1.0 cells all 0.00; LoRA cells 1.00 and 0.96 in the two cross-language positions.'
    f.source('plots/data/two_languages.json'); return f
FIGS={'tl_f1_curves':tl_f1_curves,'tl_f2_lora_sequential':tl_f2_lora,'tl_f3_generation_matrix':tl_f3_matrix}
