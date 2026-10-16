import re
from datetime import date, timedelta
p='sf2-web-guide.html'
s=open(p,encoding='utf-8').read()
D=lambda m,d: date(2026,m,d)
START=D(10,1); END=D(12,12); PX=8
days=(END-START).days+1; W=days*PX
x=lambda d:(d-START).days*PX
TODAY=D(10,16)
# (team, owner, rows) ; row=(name, start, end, state, est, note)
teams=[
 ('웹기획 · 디자인','테디 팀장',[
   ('홈페이지 디자인 · 검수',D(10,2),D(10,8),'done',False,'완료'),
   ('사전예약 웹기획 재검토',D(10,8),D(10,13),'done',False,'완료'),
   ('사전예약 디자인',D(10,9),D(10,15),'done',False,'10/15 개발팀 전달 완료'),
   ('개발 중 디자인 대응 · QA 화면 확인',D(10,16),D(12,7),'now',True,'수정 마감까지'),
 ]),
 ('웹 개발','김영환 팀장 · 오중수',[
   ('개발 총괄 · DB 설계 · 김영환 팀장',D(10,12),D(12,7),'now',True,'전체 개발 진행 총괄'),
   ('심사용 홈페이지 · 오중수',D(10,12),D(11,13),'now',True,'PG·연령제한 심사용, 구조·구성 확인 수준'),
   ('실서비스 기능 · QA · 오중수',D(11,13),D(12,10),'warn',True,'12/10 목표 (오픈 12/8보다 늦음)'),
   ('사전예약 개발 · 오중수',D(10,15),D(11,13),'now',True,'홈페이지와 동시 진행'),
   ('19세 미만 접근 제한 · 인증 구조 재검토',None,None,'tbd',False,'IT DEV·플랫폼·사업, 다음 회의 공유'),
   ('한국 플랫폼 연동 · SF2 연결 · 오중수',None,None,'tbd',False,'기한 미정'),
 ]),
 ('사업','김충곤 팀장 · 고민제 PM',[
   ('사전예약 보상 아이템명·이미지 전달',D(10,13),D(10,15),'done',False,'완료'),
   ('PG 2차 미팅',D(10,23),D(10,23),'plan',True,'10/23 전후, 김충곤·김영환 팀장'),
   ('19세 등급 신청 · 결과 대기',D(10,28),D(11,20),'warn',True,'10/28 신청, 11/18~20 결과 예상'),
   ('카드사 심사',D(11,13),D(12,4),'warn',True,'2주~최대 3주, 이후 약 1주 테스트'),
   ('사전예약 운영',D(11,17),D(12,7),'plan',False,'11/17 시작'),
 ]),
 ('인프라','에릭 실장 · 션 팀장',[
   ('라이브 서버 세팅 · 전달',D(10,19),D(11,6),'now',True,'빠르면 10월 말, 늦어도 11/6'),
 ]),
 ('수정 마감 · QA (제안)','김충곤 팀장 확정 필요',[
   ('사전예약 수정 마감',D(11,6),D(11,6),'plan',True,'11/6 이후 수정 받지 않음'),
   ('사전예약 QA · 콘텐츠 반영',D(11,9),D(11,13),'plan',True,'사전예약 시작 전 1주'),
   ('심사용 홈페이지 QA · 수정',D(11,10),D(11,12),'plan',True,'11/9 개발 완료 전제'),
   ('홈페이지 1차 QA',D(11,16),D(11,27),'plan',True,'완성된 화면부터 점검, 지승철 참여'),
   ('홈페이지 수정 · 콘텐츠 입력 마감',D(11,27),D(11,27),'plan',True,'11/27 이후 수정 받지 않음'),
   ('홈페이지 2차 QA',D(11,30),D(12,4),'plan',True,'수정 반영 확인'),
   ('최종 확인',D(12,7),D(12,7),'plan',True,'오픈 전날'),
 ]),
]
miles=[(D(10,2),'킥오프'),(D(11,13),'심사용 홈페이지'),(D(11,17),'사전예약 시작'),(D(12,8),'웹사이트 오픈')]
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
