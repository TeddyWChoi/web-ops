import re, os
from datetime import date, timedelta
p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'sf2-web-guide.html')
s=open(p,encoding='utf-8').read()
D=lambda m,d: date(2026,m,d)
START=D(10,1); END=D(12,12); PX=8
days=(END-START).days+1; W=days*PX
x=lambda d:(d-START).days*PX
# (team, owner, rows) ; row=(name, start, end, state, est, note)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared'))
from sf2_schedule import SF2_TEAMS, SF2_MILES, SF2_BASE
TODAY=SF2_BASE
# shared/sf2_schedule.py 가 원본. 여기서는 (업무명, 시작, 끝, 상태, 추정, 문구)만 사용
teams=[(t,o,[r[:6] for r in rows]) for t,o,rows in SF2_TEAMS]
miles=SF2_MILES
first_mon=START+timedelta(days=(7-START.weekday())%7)
grid_off=x(first_mon)
def track(inner):
    return f'<td class="g-track"><div class="g-lane" style="width:{W}px">{inner}<span class="g-today" style="left:{x(TODAY)+PX//2}px"></span></div></td>'
# header
months=''.join(f'<span class="g-m" style="left:{x(d)}px">{d.month}월</span>' for d in [D(10,1),D(11,1),D(12,1)])
weeks=''
d=first_mon
while d<=END:
    weeks+=f'<span class="g-w" style="left:{x(d)}px">{d.month}/{d.day}</span>'
    d+=timedelta(days=7)
head=f'<tr><th class="g-name">업무</th><th class="g-note">일정</th><th class="g-head"><div class="g-lane g-hlane" style="width:{W}px">{months}{weeks}<span class="g-todaytag" style="left:{x(TODAY)+PX//2}px">오늘 10/12</span></div></th></tr>'
rows=[]
ms_inner=''.join(f'<span class="g-ms" style="left:{x(d)+PX//2}px" title="{d.month}/{d.day} {n}"></span><span class="g-mslabel" style="left:{x(d)+PX//2+10}px">{d.month}/{d.day} {n}</span>' for d,n in miles)
rows.append(f'<tr class="g-group"><td class="g-name" colspan="2"><b>마일스톤</b></td>{track(ms_inner)}</tr>')
for team,owner,items in teams:
    rows.append(f'<tr class="g-group"><td class="g-name" colspan="2"><b>{team}</b><span>{owner}</span></td>{track("")}</tr>')
    for name,a,b,st,est,note in items:
        if a:
            bar=f'<span class="g-bar {st}{" est" if est else ""}" style="left:{x(a)}px;width:{(b-a).days*PX+PX}px"></span>'
        else:
            bar=''
        rows.append(f'<tr><td class="g-name g-task">{name}</td><td class="g-note"><span class="g-st {st}">{note}</span></td>{track(bar)}</tr>')
gantt=f'''        <div class="g-legend">
          <span><i class="g-key done"></i>완료</span><span><i class="g-key now"></i>진행 중</span><span><i class="g-key plan"></i>예정</span><span><i class="g-key warn"></i>위험</span><span><i class="g-key plan est"></i>예상 일정</span><span><i class="g-key-ms"></i>마일스톤</span>
        </div>
        <div class="g-box">
          <table class="gantt" style="--grid-off:{grid_off}px;--wk:{PX*7}px">
            <thead>{head}</thead>
            <tbody>
{chr(10).join("              "+r for r in rows)}
            </tbody>
          </table>
        </div>
'''
css='''.g-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12.5px; color: var(--muted); }
.g-legend span { display: inline-flex; align-items: center; gap: 6px; }
.g-key { display: inline-block; width: 22px; height: 10px; border-radius: 3px; }
.g-key-ms { display: inline-block; width: 10px; height: 10px; transform: rotate(45deg); background: var(--fg); }
.g-box { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); }
table.gantt { border-collapse: separate; border-spacing: 0; min-width: 0; width: auto; font-size: 13px; }
table.gantt th, table.gantt td { padding: 0; border-bottom: 1px solid var(--line); vertical-align: middle; }
table.gantt th { background: var(--bg); }
.g-name { position: sticky; left: 0; z-index: 3; background: var(--surface); min-width: 210px; max-width: 210px; padding: 8px 12px !important; border-right: 1px solid var(--line); }
th.g-name { background: var(--bg); z-index: 4; }
.g-note { min-width: 128px; max-width: 128px; padding: 6px 10px !important; border-right: 1px solid var(--line); white-space: normal; }
.g-task { padding-left: 24px !important; white-space: normal; line-height: 1.4; }
tr.g-group td { background: var(--bg); }
tr.g-group .g-name { background: var(--bg); }
tr.g-group .g-name b { font-size: 13.5px; }
tr.g-group .g-name span { display: block; font-size: 12px; color: var(--muted); font-weight: 400; }
.g-lane { position: relative; height: 34px; background-image: repeating-linear-gradient(to right, var(--line) 0 1px, transparent 1px var(--wk)); background-position: var(--grid-off) 0; }
tr.g-group .g-lane { height: 30px; }
.g-hlane { height: 46px; background: none; }
.g-m { position: absolute; top: 5px; font-family: var(--font-mono); font-size: 11.5px; font-weight: 500; color: var(--fg); padding-left: 4px; border-left: 1px solid var(--muted); }
.g-w { position: absolute; top: 25px; font-size: 11px; color: var(--muted); padding-left: 3px; font-variant-numeric: tabular-nums; }
.g-todaytag { position: absolute; top: 2px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: var(--surface); background: var(--accent); border-radius: 4px; padding: 0 5px; white-space: nowrap; z-index: 2; }
.g-today { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--accent); opacity: .55; z-index: 1; }
.g-bar { position: absolute; top: 9px; height: 16px; border-radius: 4px; z-index: 2; }
.g-bar.done, .g-key.done { background: var(--ok); }
.g-bar.now, .g-key.now { background: var(--accent); }
.g-bar.plan, .g-key.plan { background: var(--accent-soft); border: 1.5px solid var(--accent); }
.g-bar.warn, .g-key.warn { background: var(--flag-soft); border: 1.5px solid var(--flag); }
.g-bar.est, .g-key.est { border-style: dashed; }
.g-bar.now.est { background: var(--accent); border: 1.5px dashed var(--surface); }
.g-ms { position: absolute; top: 9px; width: 12px; height: 12px; margin-left: -6px; transform: rotate(45deg); background: var(--fg); z-index: 2; }
.g-mslabel { position: absolute; top: 7px; font-size: 12px; font-weight: 600; white-space: nowrap; z-index: 2; background: var(--bg); padding: 0 3px; }
.g-st { font-size: 12px; font-weight: 600; }
.g-st.done { color: var(--ok); } .g-st.now { color: var(--accent); } .g-st.plan { color: var(--muted); } .g-st.warn { color: var(--flag); } .g-st.tbd { color: var(--muted); font-weight: 400; }
'''
# replace old ms-box
a=s.index('        <div class="g-legend">'); b=s.index('        <h3>팀별 현황')
s=s[:a]+gantt+s[b:]
open(p,'w',encoding='utf-8').write(s)
print('ok', W, grid_off, x(TODAY))

s=open(p,encoding='utf-8').read()
import re as _re
s=_re.sub(r'<span class="g-mslabel" style="left:(\d+)px">12/8 웹사이트 오픈</span>', lambda m: f'<span class="g-mslabel" style="left:{int(m.group(1))-20}px;transform:translateX(-100%)">12/8 웹사이트 오픈</span>', s)
s=s.replace('.teams { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));','.teams { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));')
s=s.replace('.g-name { position: sticky; left: 0; z-index: 3; background: var(--surface); min-width: 210px; max-width: 210px;','.g-name { position: sticky; left: 0; z-index: 3; background: var(--surface); min-width: 190px; max-width: 190px;')
s=s.replace('.g-note { min-width: 128px; max-width: 128px;','.g-note { min-width: 118px; max-width: 118px;')
s=s.replace('.g-w { position: absolute; top: 25px; font-size: 11px;','.g-w { position: absolute; top: 25px; font-size: 10.5px;')
open(p,'w',encoding='utf-8').write(s)
