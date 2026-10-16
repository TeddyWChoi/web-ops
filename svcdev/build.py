# 서비스개발실 웹 업무 페이지 생성. 사용: cd svcdev && python3 build.py [스포2 원본 html] [출력 html]
# 기본값: ../sf2/sf2-web-guide.html → web-ops.html
import re, sys, html, os
from datetime import timedelta
from data import *

HERE = os.path.dirname(os.path.abspath(__file__))
REF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'sf2', 'sf2-web-guide.html')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'web-ops.html')
ref = open(REF, encoding='utf-8').read()
esc = html.escape
md = lambda d: f'{d.month}/{d.day}'

# ---------- 스포2 원본에서 조각 가져오기 ----------
def sec(id_):
    m = re.search(rf'<section id="{id_}">(.*?)\n    </section>', ref, re.S) or re.search(rf'<section id="{id_}">(.*?)\n      </section>', ref, re.S)
    inner = m.group(1)
    return re.sub(r'\s*<h2>.*?</h2>', '', inner, count=1)

def between(a, b, include_b=False):
    i = ref.index(a); j = ref.index(b, i)
    return ref[i:j + (len(b) if include_b else 0)]

def renum(s):
    return re.sub(r'논의 안건 (\d)', r'논의 안건 스포2-\1', s)

sf2_team_src = sec('team')
def card(name):
    return re.search(rf'<div class="person"><span class="role">[^<]*</span><span class="name">{name}</span>.*?</div>', sf2_team_src, re.S).group(0)
NEW = lambda role, name: f'<div class="person"><span class="role">{role}</span><span class="name">{name}</span><p><span class="chip">확인 필요</span> 스포2 담당 업무</p></div>'
sf2_team = (
    '<h4 class="grp">그래픽디자인팀</h4><div class="people">' + card('테디 팀장') + NEW('UIUX 디자인', '레이첼') + NEW('미디어컨텐츠 디자인', '정은이') + '</div>'
    '<h4 class="grp">플랫폼개발팀</h4><div class="people">' + card('김영환 팀장') + card('오중수') + '</div>'
    '<h4 class="grp">관련 부서</h4><div class="people">' + card('에릭 실장') + card('션 팀장') + '</div>'
    '<ul class="plain note"><li>사업 측 결정권자 · PM은 위 기본 정보와 업무별 담당 표 참고</li></ul>')
sf2_raci = sec('raci')
sf2_meeting = sec('meeting')
sf2_todo = renum(sec('todo')).replace(
    '다른 게임과 개발 일정이 겹칠 때 우선순위를 최종 결정하는 사람',
    '다른 게임과 개발 일정이 겹칠 때 우선순위를 최종 결정하는 사람 (공통-1)').replace(
    '<li><span class="chip">확인 필요</span> 다른 게임과 개발 일정이 겹칠 때 우선순위를 최종 결정하는 사람 (공통-1)</li>', '').replace(
    '휴대폰 번호 등 개인정보를 수집하는 페이지의 사내 검토 담당 (개인정보·법무)',
    '휴대폰 번호 등 개인정보를 수집하는 페이지의 사내 검토 담당 (공통-4)')
sf2_status = between('<div class="teams">', '<h3>세부 일정</h3>')
sf2_sched = '<div class="table-box">\n          ' + between('<table class="sched">', '</table>', True) + '\n        </div>'
sf2_note = renum(between('<ul class="plain note">', '</ul>', True))
sf2_open_rows = re.findall(r'<tr>(<td class="who">.*?)</tr>', sec('open-items'), re.S)
_drop = ('정기 회의 소집', '회의 내용 정리·공유', '가이드·일정 양식 공유', '컨플루언스에 정리', '완료</span>')
sf2_action_rows = lambda: None
sf2_action_rows = re.findall(r'<tr>(<td class="who">.*?)</tr>', sec('actions'), re.S)
sf2_action_rows = [r for r in sf2_action_rows if not any(k in r for k in _drop)]
sf2_minutes = sec('minutes').replace('<details class="mtg" open>', '<details class="mtg">')
sf2_ag_intro = re.search(r'(<ul class="plain">.*?</ul>)', sec('agenda'), re.S).group(1)
sf2_agendas = re.search(r'<div class="agendas">(.*)</div>\s*$', sec('agenda'), re.S).group(1)
sf2_agendas = renum(re.sub(r'<span class="ag-no">(\d)</span>', r'<span class="ag-no">스포2-\1</span>', sf2_agendas))
sf2_minutes = renum(sf2_minutes)

css_ref = '\n'.join(re.findall(r'<style>(.*?)</style>', ref, re.S))

# ---------- 간트 ----------
def text_w(t):
    return sum(12 if ord(c) > 0x2000 else 7 for c in t) + 8

def stagger(items, W):
    """items: [(x, label, cls)] -> (spans html, lane height). 최대 3줄에 나눠 겹침 방지, 오른쪽 끝은 왼쪽으로 붙임."""
    TOPS = (4, 24, 44)
    out = ''; last = [-999] * 3; used = 1
    for x, label, cls in sorted(items):
        w = text_w(label)
        left = x + 10
        if left + w > W: left = x - 10 - w
        lane = next((i for i in range(3) if min(left, x - 8) > last[i] + 4), None)
        if lane is None: lane = min(range(3), key=lambda i: last[i])
        top = TOPS[lane]; used = max(used, lane + 1)
        last[lane] = max(left + w, x + 8)
        out += f'<span class="g-ms{cls}" style="left:{x}px;top:{top + 2}px" title="{esc(label)}"></span>'
        out += f'<span class="g-mslabel{cls}" style="left:{left}px;top:{top}px">{esc(label)}</span>'
    return out, 6 + 20 * max(used, 2)

class Gantt:
    def __init__(s, start, end, px):
        s.start, s.end, s.px = start, end, px
        s.W = ((end - start).days + 1) * px
    def x(s, d): return (d - s.start).days * s.px
    def today_x(s): return s.x(BASE) + s.px // 2
    def track(s, inner, cls='', h=None):
        if isinstance(inner, tuple): inner, h = inner
        hs = f';height:{h}px' if h else ''
        return f'<td class="g-track"><div class="g-lane{cls}" style="width:{s.W}px{hs}">{inner}<span class="g-today" style="left:{s.today_x()}px"></span></div></td>'
    def head(s, label='업무'):
        months, d = '', s.start.replace(day=1)
        while d <= s.end:
            if d >= s.start: months += f'<span class="g-m" style="left:{s.x(d)}px">{d.month}월</span>'
            d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        first_mon = s.start + timedelta(days=(7 - s.start.weekday()) % 7)
        weeks, d = '', first_mon
        while d <= s.end:
            weeks += f'<span class="g-w" style="left:{s.x(d)}px">{md(d)}</span>'; d += timedelta(days=7 if s.px * 7 >= 40 else 14)
        s.grid_off = s.x(first_mon)
        return (f'<tr><th class="g-name">{label}</th><th class="g-note">일정</th><th class="g-head"><div class="g-lane g-hlane" style="width:{s.W}px">'
                f'{months}{weeks}<span class="g-todaytag" style="left:{s.today_x()}px">오늘 {md(BASE)}</span></div></th></tr>')
    def bar(s, a, b, st, est):
        a = max(a, s.start); b = min(b, s.end)
        return f'<span class="g-bar {st}{" est" if est else ""}" style="left:{s.x(a)}px;width:{(b - a).days * s.px + s.px}px"></span>'
    def table(s, head, rows, legend):
        return (f'<div class="g-legend">{legend}</div>\n<div class="g-box"><table class="gantt" data-start="{s.start.isoformat()}" data-end="{s.end.isoformat()}" data-px="{s.px}" '
                f'style="--grid-off:{s.grid_off}px;--wk:{s.px * 7}px"><thead>{head}</thead><tbody>\n' + '\n'.join(rows) + '\n</tbody></table></div>')

LEG = ('<span><i class="g-key done"></i>완료</span><span><i class="g-key now"></i>진행 중</span><span><i class="g-key plan"></i>예정</span>'
       '<span><i class="g-key warn"></i>위험</span><span><i class="g-key plan est"></i>예상 일정</span><span><i class="g-key-ms"></i>마일스톤</span>')

def project_gantt(rng, teams, miles):
    g = Gantt(*rng); head = g.head()
    rows = [f'<tr class="g-group g-msrow"><td class="g-name" colspan="2"><b>마일스톤</b></td>{g.track(stagger([(g.x(d) + g.px // 2, f"{md(d)} {n}", "") for d, n in miles], g.W))}</tr>']
    for team, owner, items in teams:
        rows.append(f'<tr class="g-group"><td class="g-name" colspan="2"><b>{esc(team)}</b><span>{esc(owner)}</span></td>{g.track("")}</tr>')
        for name, a, b, st, est, note, *_ in items:
            rows.append(f'<tr><td class="g-name g-task">{esc(name)}</td><td class="g-note"><span class="g-st {st}">{esc(note)}</span></td>{g.track(g.bar(a, b, st, est) if a else "")}</tr>')
    return g.table(head, rows, LEG)

def overview_gantt():
    g = Gantt(*OV_RANGE); head = g.head('프로젝트')
    rows = []
    for p in PROJECTS:
        if p['miles']:
            ds = [d for d, _ in p['miles']]
            span = f'<span class="g-span" style="left:{g.x(min(ds)) + g.px // 2}px;width:{g.x(max(ds)) - g.x(min(ds))}px"></span>'
            ms = stagger([(g.x(d) + g.px // 2, f'{md(d)} {n}', ' est' if d in p['est_miles'] else '') for d, n in p['miles']], g.W)
            note = f'<span class="g-st {"warn" if p["status"] in ("warn", "risk") else "now"}">{esc(p["status_txt"])}</span>'
            inner = (span + ms[0], ms[1])
        else:
            note = '<span class="g-st tbd">일정 미입력</span>'; inner = ''
        rows.append(f'<tr class="g-msrow"><td class="g-name"><a href="#p-{p["id"]}">{esc(p["name"])}</a></td><td class="g-note">{note}</td>{g.track(inner)}</tr>')
    leg = '<span><i class="g-key-ms"></i>확정 마일스톤</span><span><i class="g-key-ms est"></i>시작일 미정 · 제안</span><span><i class="g-key span"></i>진행 기간</span>'
    return g.table(head, rows, leg)

# ---------- 인력별 작업 ----------
def all_tasks():
    out = []
    for pid, short, teams in (('sf2', '스포2', SF2_TEAMS), ('latale', '라테일', LATALE_TEAMS), ('uwo', 'UWO', UWO_TEAMS)):
      for team, owner, items in teams:
        for name, a, b, st, est, note, owners, load in items:
            for o in owners:
                out.append(dict(person=o, proj=pid, short=short, name=re.sub(r' · (오중수|김영환 팀장|테디 팀장)$', '', name),
                                a=a, b=b, st=st, est=est, note=note, load=load))
    for person, pid, short, name, a, b, st, est, note, load in EXTRA_TASKS:
        out.append(dict(person=person, proj=pid, short=short, name=name, a=a, b=b, st=st, est=est, note=note, load=load))
    return out

TASKS = all_tasks()
DECIDER = {p['id']: p['decider'] for p in PROJECTS}

def overlaps(tasks, min_days=3):
    res = []
    ts = [t for t in tasks if t['a'] and t['load'] and t['st'] != 'done']
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a = max(ts[i]['a'], ts[j]['a']); b = min(ts[i]['b'], ts[j]['b'])
            if (b - a).days + 1 >= min_days:
                res.append((ts[i], ts[j], a, b))
    return res

def people_gantt():
    g = Gantt(*PEOPLE_RANGE); head = g.head('사람 · 작업')
    rows = []
    for team, members in PEOPLE:
        rows.append(f'<tr class="g-team"><td class="g-name" colspan="3"><b>{team}</b></td></tr>')
        for name, role in members:
            ts = [t for t in TASKS if t['person'] == name]
            clash = ''.join(f'<span class="{"g-par" if t1["proj"] == t2["proj"] else "g-clash"}" style="left:{g.x(a)}px;width:{(b - a).days * g.px + g.px}px" '
                            f'title="{md(a)}~{md(b)} {"같은 프로젝트 병행" if t1["proj"] == t2["proj"] else "프로젝트 간 겹침"}"></span>'
                            for t1, t2, a, b in overlaps(ts))
            cnt = len([t for t in ts if t['st'] != 'done'])
            rows.append(f'<tr class="g-group"><td class="g-name" colspan="2"><b>{esc(name)}</b><span>{esc(role)} · 진행·예정 {cnt}건</span></td>{g.track(clash)}</tr>')
            for t in ts:
                rows.append(f'<tr><td class="g-name g-task"><span class="ptag">{t["short"]}</span> {esc(t["name"])}</td>'
                            f'<td class="g-note"><span class="g-st {t["st"]}">{esc(t["note"])}</span></td>{g.track(g.bar(t["a"], t["b"], t["st"], t["est"]) if t["a"] else "")}</tr>')
            if not ts:
                rows.append(f'<tr><td class="g-name g-task">—</td><td class="g-note"><span class="g-st tbd">배정 없음</span></td>{g.track("")}</tr>')
    leg = LEG.replace('<span><i class="g-key-ms"></i>마일스톤</span>', '') + '<span><i class="g-key par"></i>같은 프로젝트 병행</span><span><i class="g-key clash"></i>프로젝트 간 겹침</span>'
    return g.table(head, rows, leg)

def conflict_rows():
    cross, same = [], []
    for team, members in PEOPLE:
        for name, _ in members:
            for t1, t2, a, b in overlaps([t for t in TASKS if t['person'] == name]):
                works = f'[{t1["short"]}] {esc(t1["name"])}<br>[{t2["short"]}] {esc(t2["name"])}'
                if t1['proj'] == t2['proj']:
                    dec = DECIDER[t1['proj']]
                    who = f'{dec}' if dec else '결정권자 <span class="chip">확인 필요</span>'
                    same.append(f'<tr><td class="who">{esc(name)}</td><td>{works}</td><td class="d">{md(a)}~{md(b)}</td><td>{who}</td></tr>')
                else:
                    cross.append(f'<tr><td class="who">{esc(name)}</td><td>{works}</td><td class="d">{md(a)}~{md(b)}</td><td><span class="chip">확인 필요</span> 서비스개발실장 공석</td></tr>')
    return cross, same

# ---------- 공통 조각 ----------
def st_badge(cls, txt): return f'<span class="st {cls}">{esc(txt)}</span>'
def val(v): return esc(v) if v else '<span class="chip">확인 필요</span>'

def project_table():
    rows = []
    for p in PROJECTS:
        rows.append(f'<tr><td class="who"><a href="#p-{p["id"]}">{esc(p["name"])}</a></td><td>{val(p["decider"])}</td><td>{val(p["pm"])}</td>'
                    f'<td>{val(p["planner"])}</td><td>{val(p["design"])}</td><td>{val(p["dev"])}</td><td>{val(p["stage"])}</td><td>{val(p["next"])}</td>'
                    f'<td>{st_badge(p["status"], p["status_txt"])}</td></tr>')
    return ('<div class="table-box"><table class="ptable"><thead><tr><th>프로젝트</th><th>결정권자</th><th>PM</th><th>웹기획</th><th>디자인</th><th>웹 개발</th>'
            '<th>현재 단계</th><th>다음 마일스톤</th><th>상태</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')

def issues_table():
    pshort = {p['id']: p['short'] for p in PROJECTS}
    rows = ''
    for svc, items in SERVICES:
        if not items:
            rows += f'<tr><td class="who">{esc(svc)}</td><td class="ctx">이번 주 웹 이슈 없음</td><td></td><td></td></tr>'
            continue
        for i, (t, per, sc, stx, pid) in enumerate(items):
            link = f' <a class="ptag" href="#p-{pid}">{esc(pshort[pid])}</a>' if pid else ''
            rows += (f'<tr{" class=svc-first" if i == 0 else ""}><td class="who">{esc(svc) if i == 0 else ""}</td><td>{esc(t)}{link}</td>'
                     f'<td class="d">{esc(per)}</td><td>{st_badge(sc, stx)}</td></tr>')
    return ('<div class="table-box"><table class="issues"><thead><tr><th>서비스</th><th>웹 이슈</th><th>기간</th><th>상태</th></tr></thead><tbody>'
            + rows + '</tbody></table></div>')

def _ukey(r):
    m = re.match(r'(\d+)/(\d+)', r[0])
    return (int(m.group(1)), int(m.group(2))) if m else (99, 0)

def _uend(r):
    ds = re.findall(r'(\d+)/(\d+)', r[0])
    if not ds:
        m = re.match(r'(\d+)/\d+~(\d+)$', r[0])
    m2 = re.match(r'(\d+)/(\d+)~(\d+)$', r[0])
    if m2: return (int(m2.group(1)), int(m2.group(3)))
    return (int(ds[-1][0]), int(ds[-1][1])) if ds else None

def upcoming_table():
    base = (BASE.month, BASE.day)
    rowf = lambda d, p, c, w, sc, s: f'<tr><td class="d">{d}</td><td><span class="ptag">{p}</span></td><td>{esc(c)}</td><td>{esc(w)}</td><td>{st_badge(sc, s)}</td></tr>'
    items = sorted(UPCOMING, key=_ukey)
    up = [r for r in items if _uend(r) is None or _uend(r) >= base]
    past = [r for r in items if _uend(r) is not None and _uend(r) < base]
    html_ = ('<div class="table-box"><table><thead><tr><th>날짜</th><th>프로젝트</th><th>내용</th><th>담당</th><th>상태</th></tr></thead><tbody>'
            + ''.join(rowf(*r) for r in up) + '</tbody></table></div>')
    if past:
        html_ += ('<h3>기한 지난 항목 <span class="asof">완료 여부 확인 필요</span></h3><div class="table-box"><table><thead><tr><th>날짜</th><th>프로젝트</th><th>내용</th><th>담당</th><th>상태</th></tr></thead><tbody>'
                  + ''.join(rowf(d, p, c, w, 'warn', '확인 필요') for d, p, c, w, sc, s in past) + '</tbody></table></div>')
    return html_

def checklist(pid):
    p = next(x for x in PROJECTS if x['id'] == pid)
    desc = f'<p>{esc(p["desc"])}</p>' if p.get('desc') else ''
    return f'''<section id="p-{pid}" class="proj" hidden>
        <h2>{esc(p["name"])} {st_badge(p["status"], p["status_txt"])}</h2>
        {desc}
        <dl class="pkv"><dt>결정권자</dt><dd>{val(p["decider"])}</dd><dt>PM</dt><dd>{val(p["pm"])}</dd><dt>웹기획</dt><dd>{val(p["planner"])}</dd><dt>디자인</dt><dd>{val(p["design"])}</dd><dt>웹 개발</dt><dd>{val(p["dev"])}</dd><dt>현재 단계</dt><dd>{val(p["stage"])}</dd><dt>오픈 목표</dt><dd>{val(p["open"])}</dd></dl>
        {'<ul class="plain note"><li>일정 미입력. 담당과 일정이 정해지면 상세 간트 추가</li></ul>' if not p['miles'] else ''}
      </section>'''

def latale_section():
    p = next(x for x in PROJECTS if x['id'] == 'latale')
    ms = ''.join(f'<tr{" class=\"gate\"" if g else ""}><td class="d">{d} ({w})</td><td>{esc(t)}</td><td>{esc(o)}</td><td>{('<span class="st warn">' + g + '</span>') if g else ''}</td></tr>'
                 for d, w, t, o, g in LATALE_MASTER)
    return f'''<section id="p-latale" class="proj" hidden>
        <h2>{esc(p["name"])} {st_badge(p["status"], p["status_txt"])}</h2>
        <dl class="pkv"><dt>결정권자</dt><dd>{val(p["decider"])}</dd><dt>PM</dt><dd>{val(p["pm"])}</dd><dt>웹기획</dt><dd>{val(p["planner"])}</dd><dt>디자인</dt><dd>{val(p["design"])}</dd><dt>웹 개발</dt><dd>{val(p["dev"])}</dd><dt>오픈 목표</dt><dd>12/17 (목) 북미 LIVE</dd><dt>기준 시간</dt><dd>PDT 밴쿠버 시간. 마감은 각 주 금요일</dd><dt>외부</dt><dd>액토즈 (WEB URL 전달, 설치패키지 연동), Steam</dd></dl>
        <div class="proj-sec"><h3>마스터 마일스톤</h3>
        <div class="table-box"><table><thead><tr><th>마감</th><th>마일스톤</th><th>주관</th><th>게이트</th></tr></thead><tbody>{ms}</tbody></table></div></div>
        <div class="proj-sec"><h3>상세 일정</h3>
        {project_gantt(LATALE_RANGE, LATALE_TEAMS, LATALE_MILES)}
        <ul class="plain note"><li>8~9월 마감 항목은 일정표 기준으로 완료 표시. 실제 완료 여부 확인 필요</li><li>★ 표시는 주 선행 작업. 늦어지면 다음 게이트가 밀림</li></ul></div>
        <div class="risk"><strong>다음 게이트: 11/6 스테이징 통합테스트 + 런처 WEB URL 액토즈 전달</strong>
        <p>10/16 프론트엔드 완료와 10/23 파파야 API 연동 · 웹 호스팅 인프라 구축이 선행입니다. URL 전달이 늦어지면 11/9부터 시작하는 설치패키지 연동테스트와 통합 QA가 함께 밀리고, 12/11 게이트②와 12/17 LIVE에 영향이 갑니다.</p></div>
        <div class="proj-sec"><h3>확인 필요 항목</h3><ul class="plain todo">
          <li><span class="chip">확인 필요</span> 플랫폼 업무 담당이 성경진 단독인지. 인력별 현황은 성경진 기준으로 표시</li>
          <li><span class="chip">확인 필요</span> SRE · QA 담당</li>
          <li><span class="chip">확인 필요</span> 8~9월 마감 항목 (액토즈 회신, 킥오프, UI 확정 · 핸드오프) 실제 완료 여부</li>
          <li><span class="chip">확인 필요</span> 정기 회의 일시와 회의 내용 정리 담당</li>
        </ul></div>
      </section>'''

def uwo_section():
    p = next(x for x in PROJECTS if x['id'] == 'uwo')
    rows = ''.join(f'<tr><td class="d">{n}</td><td class="who">{esc(t)}</td><td>{esc(req)}</td><td>{esc(res)}</td><td>{st_badge(sc, stx)}</td></tr>'
                   for n, t, req, res, sc, stx in UWO_ITEMS)
    todo = ''.join(f'<li><span class="chip">확인 필요</span> {esc(t)}</li>' for t in UWO_TODO)
    return f'''<section id="p-uwo" class="proj" hidden>
        <h2>{esc(p["name"])} {st_badge(p["status"], p["status_txt"])}</h2>
        <p>{esc(p["desc"])}</p>
        <dl class="pkv"><dt>결정권자</dt><dd>{val(p["decider"])}</dd><dt>PM</dt><dd>{val(p["pm"])}</dd><dt>웹 개발</dt><dd>김영환 팀장 (구조가 복잡해 직접 작업)</dd><dt>웹기획</dt><dd>{val(p["planner"])}</dd><dt>디자인</dt><dd>테디 팀장. 미스테리 코브는 일반 코브와 구분 (최소 배경색, 가능하면 디자인 개선). 착수 시 요청</dd><dt>일정</dt><dd>11/25 게임 크로스월드 개방 (사업 확정) · 웹 12/8 착수 → 1월 중순 완료 예상</dd></dl>
        <div class="proj-sec"><h3>요청 항목 · 10/13 회의 결과</h3>
        <div class="table-box"><table class="uwo"><thead><tr><th>번호</th><th>항목</th><th>요청</th><th>회의 결과</th><th>회신</th></tr></thead><tbody>{rows}</tbody></table></div>
        <ul class="plain note"><li>작업 순서: 랜딩 제거 · 사이트 정리 → 팝업샵 · 컴퍼스 서버 선택 → 정리된 상태를 보고 코브 수정 → 미스테리 코브</li></ul></div>
        <div class="proj-sec"><h3>상세 일정</h3>
        {project_gantt(UWO_RANGE, UWO_TEAMS, p["miles"])}
        </div>
        <div class="risk"><strong>가장 큰 일정 위험: 웹 착수가 스포2 12/8 오픈에 묶여 있음</strong>
        <p>UWO 웹 작업은 김영환 팀장이 스포2 빌링 · 세팅 · API 정리를 마친 뒤 착수합니다. 스포2가 밀리면 같이 밀립니다. 1월 중순 완료는 중간에 다른 작업이 끼지 않는다는 전제이고, 코브는 소스 확인 전이라 기간이 늘 수 있습니다. 일정 협의 중인 파파야플레이 일본 구축과 같은 시기에 걸릴 수 있습니다.</p></div>
        <div class="proj-sec"><h3>확인 필요 항목</h3><ul class="plain todo">{todo}</ul></div>
      </section>'''

def agenda(no, title, cur, prob, prop, res_cls, res):
    return f'''<div class="agenda" data-p="common"><div class="ag-head"><span class="ag-no">{no}</span><h3>{title}</h3></div>
            <dl class="ag-kv"><dt>현재</dt><dd>{cur}</dd><dt>문제</dt><dd>{prob}</dd><dt>제안</dt><dd>{prop}</dd>
            <dt class="ag-dec">결정</dt><dd class="ag-res {res_cls}">{res}</dd></dl></div>'''

COMMON_AGENDAS = ''.join([
    agenda('공통-1', '프로젝트 간 일정 · 인력 겹침 시 우선순위',
           '프로젝트마다 결정권자가 자기 프로젝트 일정만 확정. 다른 게임 일정과 겹치면 에릭 실장에게 공유하는 것까지만 정해져 있고, 우선순위를 정하는 사람은 없음',
           '같은 사람에게 여러 작업이 같은 기간에 잡혀도 어느 쪽을 먼저 할지 정할 사람이 없음. 결정권자가 다른 두 프로젝트가 겹치면 실무자끼리 순서를 정하게 됨',
           '같은 프로젝트 안의 겹침은 그 프로젝트 결정권자가 정함. 프로젝트 간 겹침은 김영환 팀장이 영향을 정리해 두 결정권자에게 올리고, 합의가 안 되면 올릴 사람을 지정',
           'open', '논의 필요. 프로젝트 간 겹침을 최종 정리할 사람'),
    agenda('공통-2', '웹 작업 요청 창구',
           '스포2는 고민제 PM으로 일원화 (10/13). 다른 프로젝트는 요청 경로가 정해져 있지 않고, 기획 요청이 디자인팀에 직접 들어오기도 함',
           '요청이 정리되지 않은 채 실무자에게 내려오면 작업 중간에 방향이 바뀜 (스포2 사전예약 사례)',
           '프로젝트마다 PM 1명을 창구로 지정하고 요청은 지라에 등록. 새 프로젝트는 등록 체크리스트를 채운 뒤 착수',
           'part', '일부 결정. 스포2만 확정, 나머지 프로젝트 PM 확인 필요'),
    agenda('공통-3', '공통 채널 구성',
           '요청은 지라, 팀 간 소통은 팀즈. 일정 변경 · 긴급 이슈를 전원이 함께 보는 채널은 없음 (스포2 공통 채널 신설 논의 중)',
           '일정 변경과 결정 사항이 팀별로 따로 전달되어 관련 팀이 늦게 알게 됨',
           '프로젝트별 공통 채널로 둘지, 서비스개발실 웹 통합 채널 하나로 둘지 결정',
           'open', '논의 필요'),
    agenda('공통-4', '개인정보 수집 페이지 사내 검토',
           '휴대폰 번호 등 개인정보를 수집하는 페이지의 사내 검토 담당(개인정보 · 법무)이 정해져 있지 않음',
           '약관 · 동의 · 보관 기간 검토가 빠지면 오픈 직전에 막힘. 스포2 사전예약이 해당',
           '검토 담당과 요청 경로를 정하고, 웹기획 단계에서 개인정보 수집 여부를 필수 항목으로 확인',
           'open', '논의 필요'),
    agenda('공통-5', '일정표 갱신 담당과 양식',
           '스포2는 고민제 PM이 WBS · 일정표를 관리하고 주간 보고 (10/13). 이 페이지 양식을 참고해 표준 양식을 정하기로 함',
           '페이지 작성자 한 명이 모든 프로젝트 일정을 갱신하면 진행 관리가 다시 한 사람에게 몰림',
           '각 프로젝트 PM이 회의 후 일정 · 결정을 공유하고, 테디 팀장은 양식과 역할 · 절차 반영을 맡음. 각 팀 팀장이 크로스 체크',
           'part', '일부 결정. 스포2 적용, 다른 프로젝트 확인 필요'),
    agenda('공통-6', '정기 회의 범위',
           '정기 회의는 스포2 금요일 회의 하나',
           '다른 프로젝트는 진행 상황을 확인하는 자리가 없음',
           '프로젝트별 회의를 따로 둘지, 금요일 회의 뒤에 전 프로젝트 현황 확인을 붙일지 결정',
           'open', '논의 필요'),
])

# ---------- 공통 가이드 ----------
def team_html():
    out = ''
    for team, members in PEOPLE:
        cards = ''
        for name, role in members:
            pids = []
            for t in TASKS:
                if t['person'] == name and t['proj'] not in pids: pids.append(t['proj'])
            for pr in PROJECTS:
                if pr['id'] not in pids and any(name in (pr.get(k) or '') for k in ('planner', 'design', 'dev', 'pm')): pids.append(pr['id'])
            shorts = [pr['short'] for pr in PROJECTS if pr['id'] in pids]
            pj = ' '.join(f'<span class="ptag">{esc(x)}</span>' for x in shorts) if shorts else '<span class="chip">확인 필요</span>'
            cards += f'<div class="person"><span class="role">{esc(role)}</span><span class="name">{esc(name)}</span><p>참여 프로젝트 {pj}</p></div>'
        out += f'<h4 class="grp">{esc(team)}</h4><div class="people">{cards}</div>'
    return out

GUIDE = '''
    <section id="g-about">
      <h2><span class="no">00</span>이 문서에 대해</h2>
      <div class="principle">
        <p><strong>결정은 각 프로젝트 결정권자가, 진행은 PM이 합니다.</strong></p>
        <p>웹 요청, 문의, 검수 의견은 프로젝트 PM을 통해 주고받습니다. PM 선에서 해결되지 않는 건은 결정권자에게 올립니다. 일정, 범위, 오픈 여부는 결정권자의 확정으로 바뀌며, 실무자 사이의 합의만으로는 바뀌지 않습니다.</p>
      </div>
      <ul class="plain">
        <li><b>적용 범위</b> 서비스개발실(디자인팀, 플랫폼개발팀)이 맡는 모든 웹 작업. 게임별 공식 홈페이지, 사전예약 · 이벤트 · 프로모션 페이지, 플랫폼(파파야플레이 등) 작업</li>
        <li><b>제외</b> 게임 클라이언트, 인게임, 서버 인프라 일정. 웹과 맞물리는 지점만 적음</li>
        <li><b>소통 도구</b> 웹 작업 · 수정 요청은 지라, 팀 간 소통은 팀즈, 일정 변경 · 긴급 이슈는 프로젝트 공통 채널 (공통-3)</li>
        <li><b>적용 기간</b> 웹 전담 기획자가 없는 동안 상시 기준. 기획자 합류 시 인계 자료로 사용</li>
      </ul>
    </section>

    <section id="g-team">
      <h2><span class="no">01</span>팀 구성</h2>
      {TEAM_HTML}
    </section>

    <section id="g-roles">
      <h2><span class="no">02</span>역할</h2>
      <div class="table-box">
        <table>
          <thead><tr><th>역할</th><th>담당</th><th>하는 일</th><th>하지 않는 일</th></tr></thead>
          <tbody>
            <tr><td class="who">결정권자</td><td>프로젝트별 (전체 현황 표)</td><td>요구사항, 웹기획안, 일정, 디자인, 오픈 확정. 대표 보고</td><td>개발 공수 산정</td></tr>
            <tr><td class="who">PM</td><td>프로젝트별</td><td>요청 정리 · 전달, 회의 소집 · 진행, 회의 내용 정리 · 공유, WBS · 일정표 · 주간 보고, 검수 의견 취합, 오픈 공지</td><td>결정권자 확정 없이 일정 · 범위 변경에 동의</td></tr>
            <tr><td class="who">웹기획</td><td>테디 팀장 (공석 기간 지원)</td><td>페이지 목록, 화면별 상태, 사용 흐름, 예외 상황 설계</td><td>일정 · 범위 결정</td></tr>
            <tr><td class="who">디자인</td><td>디자인팀</td><td>시안, 확정 디자인, 개발 전달용 파일. 디자인 일정 산정</td><td>수정 요청을 개발팀에 대신 전달</td></tr>
            <tr><td class="who">웹 개발</td><td>플랫폼개발팀 (김영환 팀장 총괄)</td><td>공수 · 일정 산정, 개발, 지연 시 사유와 새 일정 보고. 개발 일정의 1차 책임</td><td>실무자와만 합의하고 일정 변경</td></tr>
            <tr><td class="who">기술 에스컬레이션</td><td>에릭 실장 (SRE 인프라실)</td><td>여러 프로젝트의 개발 리소스가 겹칠 때, 인프라 · 서버 영향이 있을 때 확인. 공통 채널로 비동기 보고</td><td>일상적인 웹 일정 확인</td></tr>
            <tr><td class="who">인프라</td><td>션 팀장</td><td>웹 서버, 도메인, 배포 환경</td><td>—</td></tr>
            <tr><td class="who">크로스 체크</td><td>각 팀 팀장</td><td>진행 상황 공유, 산출물이 갱신됐는지 서로 확인 (PMO 역할 분담)</td><td>—</td></tr>
            <tr><td class="who">가이드 관리</td><td>테디 팀장</td><td>이 페이지와 양식 관리, 바뀐 역할 · 절차 반영, 요청이 맞는 결정권자에게 가도록 안내</td><td>일정 · 범위 결정, 개발팀 대신 보고, 모든 프로젝트 일정 직접 갱신</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section id="g-flow">
      <h2><span class="no">03</span>업무 흐름</h2>
      <div class="steps">
        <div class="step"><div class="n">1</div><div class="body"><h3>요청 접수</h3><dl class="kv"><dt>주관</dt><dd>PM (사업팀 의견을 정리해 요청)</dd><dt>산출물</dt><dd>작업 종류, 기존과 달라지는 점, 목적, 희망 오픈일, 참고 자료</dd><dt>분기</dt><dd>기존 구조 수정이면 메뉴구조도나 수정 목록으로 바로 디자인. 신규 기능이 들어가면 웹기획부터</dd><dt>넘어가는 조건</dt><dd>요청이 지라에 등록됨. 새 프로젝트는 등록 체크리스트의 사람과 창구 항목이 채워짐</dd></dl></div></div>
        <div class="step"><div class="n">2</div><div class="body"><h3>요구사항과 웹기획</h3><dl class="kv"><dt>주관</dt><dd>PM (요구사항), 웹기획 담당 (웹기획안)</dd><dt>산출물</dt><dd>웹기획안: 전체 페이지 목록, 화면별 상태(진행 전 · 중 · 완료 · 종료 후), 사용 흐름, 예외 상황, 개인정보 수집 여부, PC/모바일 차이</dd><dt>지원</dt><dd>김영환 팀장이 구현 가능성 의견</dd><dt>넘어가는 조건</dt><dd>PM 확인 후 결정권자가 웹기획안 확정</dd></dl></div></div>
        <div class="step"><div class="n">3</div><div class="body"><h3>일정 산정과 확정</h3><dl class="kv"><dt>주관</dt><dd>김영환 팀장 (개발), 디자인팀 (디자인)</dd><dt>산출물</dt><dd>화면별 완성일, 디자인 완료일, 개발 완료일, 수정 마감일, 1차 · 2차 QA, 최종 확인일, 오픈일. 약관 · 개인정보 · 콘텐츠처럼 개발이 아닌 일도 포함</dd><dt>넘어가는 조건</dt><dd>결정권자 확정. 전체 현황의 인력별 작업에서 겹침 확인. 다른 프로젝트와 겹치면 공통-1 경로, 인프라 영향이 있으면 션 팀장에게 공유</dd></dl></div></div>
        <div class="step"><div class="n">4</div><div class="body"><h3>디자인</h3><dl class="kv"><dt>주관</dt><dd>디자인팀</dd><dt>산출물</dt><dd>시안, 확정 디자인, 개발 전달용 파일</dd><dt>넘어가는 조건</dt><dd>PM 확인 후 결정권자 디자인 확정</dd></dl></div></div>
        <div class="step"><div class="n">5</div><div class="body"><h3>웹 개발</h3><dl class="kv"><dt>주관</dt><dd>플랫폼개발팀</dd><dt>산출물</dt><dd>검수 가능한 테스트 페이지</dd><dt>넘어가는 조건</dt><dd>테스트 환경 반영 완료를 공통 채널에 공유</dd></dl></div></div>
        <div class="step"><div class="n">6</div><div class="body"><h3>검수</h3><dl class="kv"><dt>주관</dt><dd>사업팀 내부 검토 → PM이 의견을 수정 목록 하나로 정리해 전달</dd><dt>지원</dt><dd>디자인팀 (화면), 플랫폼개발팀 (기능)은 사업팀 검토 전에 자체 확인</dd><dt>넘어가는 조건</dt><dd>결정권자 검수 완료와 오픈 확정</dd></dl></div></div>
        <div class="step"><div class="n">7</div><div class="body"><h3>오픈과 운영</h3><dl class="kv"><dt>주관</dt><dd>플랫폼개발팀 (반영), PM (공지)</dd><dt>산출물</dt><dd>오픈 공지. 운영 중 수정은 상황별 대응 절차를 따름. 프로젝트 종료 후 절차를 컨플루언스에 정리</dd></dl></div></div>
      </div>
    </section>

    <section id="g-cases">
      <h2><span class="no">04</span>상황별 대응</h2>
      <div class="cases">
        <div class="case">
          <h3>일정이 밀릴 것 같을 때</h3>
          <ol>
            <li>지연이 생긴 팀의 팀장이 지연 대상, 사유, 새 일정, 결정이 필요한 사항을 정리합니다.</li>
            <li>공통 채널에 올리고 PM과 결정권자를 태그합니다.</li>
            <li>결정권자가 확정하면 일정이 바뀐 것으로 봅니다. 확정 전까지는 기존 일정이 유효합니다.</li>
            <li>다른 프로젝트 일정에 영향이 있으면 공통-1 경로로, 인프라에 영향이 있으면 션 팀장에게도 공유합니다.</li>
            <li>PM이 변경 내용을 일정표와 다음 정기 회의 내용에 반영합니다.</li>
          </ol>
          <p class="dont">실무자끼리만 합의한 일정 변경은 효력이 없습니다.</p>
        </div>
        <div class="case">
          <h3>수정 요청이 생길 때</h3>
          <ol>
            <li>사업팀 안에서 정리한 뒤 PM이 한 번에 전달합니다. 실무자에게 개별로 들어온 요청은 PM을 거치도록 안내합니다.</li>
            <li>웹기획 단계라면 웹기획 담당이 기획안을 고칩니다.</li>
            <li>디자인 확정 전이라면 디자인팀이 반영합니다.</li>
            <li>디자인 확정 후나 개발 중이라면 김영환 팀장이 일정 영향을 판단합니다. 일정이 바뀌면 위의 지연 절차를 따릅니다.</li>
          </ol>
          <p class="dont">수정 마감일 이후, 확정 이후의 범위 추가는 결정권자 확정 없이 받지 않습니다.</p>
        </div>
        <div class="case">
          <h3>오픈 직전이나 직후 긴급 이슈가 생길 때</h3>
          <ol>
            <li>발견한 사람이 공통 채널에 즉시 올리고 김영환 팀장과 개발 담당을 태그합니다.</li>
            <li>김영환 팀장이 원인과 예상 조치 시간을 회신합니다.</li>
            <li>오픈 연기나 페이지 내림이 필요하면 결정권자가 결정하고, PM이 공지합니다.</li>
          </ol>
        </div>
        <div class="case">
          <h3>여러 프로젝트 작업이 한 사람에게 겹칠 때</h3>
          <ol>
            <li>전체 현황의 인력별 작업 현황에서 겹침 구간을 확인합니다.</li>
            <li>같은 프로젝트 안이면 그 프로젝트 PM이 결정권자에게 우선순위 확정을 요청합니다.</li>
            <li>프로젝트 간이면 김영환 팀장(개발) 또는 디자인팀 팀장(디자인)이 영향을 정리해 두 프로젝트 PM에게 공유하고, 공통-1 경로로 올립니다.</li>
          </ol>
        </div>
        <div class="case">
          <h3>누가 맡을지 애매할 때</h3>
          <ol>
            <li>프로젝트별 탭의 업무별 담당 표를 먼저 확인합니다.</li>
            <li>그래도 불분명하면 테디 팀장에게 문의합니다. 담당자를 안내하고, 필요하면 정기 회의 안건으로 올립니다.</li>
            <li>사업팀 쪽 문의는 PM에게 하고, 해결되지 않으면 결정권자에게 올립니다.</li>
          </ol>
        </div>
      </div>
    </section>

    <section id="g-meeting">
      <h2><span class="no">05</span>정기 회의 운영</h2>
      <ul class="plain">
        <li><b>소집 · 진행</b> 프로젝트 PM. 아젠다를 회의 전에 공유</li>
        <li><b>주간 보고</b> PM이 일정 대비 진행 상황과 이슈를 정리하고, 각 팀 팀장이 확인</li>
        <li><b>회의 내용 정리</b> PM이 정리 · 공유하고 일정표에 반영. 테디 팀장은 바뀐 역할 · 절차를 이 페이지에 반영</li>
        <li><b>결정</b> 결정권자 (부재 시 지정된 대리)</li>
        <li><b>공유</b> 회의 내용은 에릭 실장에게도 공유</li>
      </ul>
      <h3>고정 안건</h3>
      <div class="table-box">
        <table>
          <thead><tr><th>안건</th><th>발표</th><th>남길 것</th></tr></thead>
          <tbody>
            <tr><td>팀별 진행 상황과 일정 변경 여부</td><td>각 팀 팀장</td><td>진행 상태, 변경 시 사유 · 새 일정 · 확정 여부</td></tr>
            <tr><td>주간 보고</td><td>PM</td><td>지연 항목과 대응</td></tr>
            <tr><td>이번 주 수정 요청 · 검수 현황</td><td>PM</td><td>요청 목록, 남은 이슈 수와 담당</td></tr>
            <tr><td>다른 프로젝트와 겹침</td><td>PM</td><td>겹치는 사람 · 기간, 우선순위 결정자</td></tr>
            <tr><td>결정 사항</td><td>결정권자 (기록 PM)</td><td>무엇을, 누가 결정했는지</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section id="g-register">
      <h2><span class="no">06</span>새 프로젝트 등록</h2>
      <div class="table-box">
        <table>
          <thead><tr><th>구분</th><th>확인 항목</th></tr></thead>
          <tbody>
            <tr><td class="who">사람과 창구</td><td>결정권자 · PM · PM 선에서 안 풀릴 때 올리는 사람 · 결정권자 부재 시 대리 · 웹기획 / 디자인 / 웹 개발 / 검수 담당 · 인프라 · 클라이언트 등 맞물리는 팀 담당</td></tr>
            <tr><td class="who">작업 범위</td><td>기존 구조 수정인지 신규 기능인지 · 개인정보 수집 (약관 · 동의 · 보관 기간 · 검토 담당) · 결제 (PG · 카드사 심사 일정, 심사 필수 화면) · 연령 제한, 확률 공개 등 법적 · 권고 사항 · 오픈 전 콘텐츠와 담당</td></tr>
            <tr><td class="who">일정</td><td>오픈일과 근거 · 오픈을 좌우하는 외부 일정 · 화면별 완성일 ("○일까지 확인 가능한 사이트"가 아니라 화면 단위) · 수정 마감일, 1차 · 2차 QA, 최종 확인일 · 같은 기간 같은 사람에게 겹치는 프로젝트</td></tr>
            <tr><td class="who">운영</td><td>정기 회의 일시, 소집 · 진행, 참석자 · 회의 내용 정리 · 공유 담당 · 요청 / 팀 간 / 전원 공유 채널 · 페이지 공유 범위</td></tr>
          </tbody>
        </table>
      </div>
    </section>
'''

GUIDE = GUIDE.replace('{TEAM_HTML}', team_html())
# ---------- 조립 ----------
sf2 = next(p for p in PROJECTS if p['id'] == 'sf2')
open_rows = ''.join(f'<tr data-p="sf2"><td><span class="ptag">스포2</span></td>{r}</tr>' for r in sf2_open_rows)
def _row(pid, tag, *cells):
    return f'<tr data-p="{pid}"><td><span class="ptag">{tag}</span></td>' + ''.join(f'<td{" class=who" if i == 0 else ""}>{c}</td>' for i, c in enumerate(cells)) + '</tr>'
open_rows += _row('uwo', 'UWO', '코브 수정 방식과 기간', '김영환 팀장 (소스 확인 후)', '코브 개편 · 미스테리 코브 일정')
open_rows += _row('uwo', 'UWO', 'Treasure Cove 2개(Maris / Ventus) 유지 여부, 플로팅 배너 제거 여부', '이진우 실장', '사이트 정리 범위, 코브 디자인')
open_rows += _row('jp', '일본', '파파야플레이 일본 오픈 일정', '대표님', '일본 구축 일정, 12월 이후 개발 인력 배분')
action_rows = _row('uwo', 'UWO', '김영환 팀장', '코브 소스 검토 후 수정 방식 · 기간 회신', '<span class="d">—</span>') \
 + _row('uwo', 'UWO', '이진우 실장', '사토시 협의 결과 공유, 10/15(목) 회의 진행 여부 알림', '<b>10/14</b>') \
 + _row('uwo', 'UWO', '이진우 실장', '확정된 웹 일정에 맞춰 재기획 후 공유', '—') \
 + _row('uwo', 'UWO', '그래픽디자인팀', '미스테리 코브 디자인 방향 검토 (일반 코브와 차이, 저가 느낌이되 너무 싸 보이지 않게)', '디자인 요청 시') \
 + ''.join(f'<tr data-p="sf2"><td><span class="ptag">스포2</span></td>{r}</tr>' for r in sf2_action_rows)
conf, par = conflict_rows()
psel = ''.join(f'<a href="#p-{p["id"]}" data-pid="{p["id"]}">{esc(p["short"])}</a>' for p in PROJECTS)
fsel = '<button type="button" data-f="all" aria-pressed="true">전체</button>' + ''.join(
    f'<button type="button" data-f="{p["id"]}" aria-pressed="false">{esc(p["short"])}</button>' for p in PROJECTS)
afsel = '<button type="button" data-f="all" aria-pressed="true">전체</button><button type="button" data-f="common" aria-pressed="false">공통</button>' + ''.join(
    f'<button type="button" data-f="{p["id"]}" aria-pressed="false">{esc(p["short"])}</button>' for p in PROJECTS)
JP_LOG = '<div class="case" data-p="jp"><h3>파파야플레이 일본 구축</h3><h3>회의 밖 결정 · 논의</h3><ul class="plain"><li><b>10/13</b> hange.jp 이전은 진행하지 않음. 파파야플레이 일본을 자체 구축하기로 함</li><li><b>10/13</b> (UWO 회의 중 논의) 오픈 일정은 협의 중. 빌링 연동은 최대 8주 (이전 5주 소요). 한국 플랫폼을 정리한 뒤 통째로 복제하고 결제만 일본에 맞추는 안은 김영환 팀장이 소스 확인 후 판단</li></ul></div>'
UWO_LOG = '''<details class="mtg" data-p="uwo"><summary><span class="mdate">10/13</span><span class="mtitle">UWO 크로스월드 웹 작업 회의</span></summary><div class="mbody">
<p class="ctx">UWO 사업 측 요청 6건(크로스월드 11/25)의 가능 여부와 일정 협의. 참석: 이진우 실장, 김영환 팀장, 테디 팀장</p>
<h3>결정</h3><ul class="plain">
<li><b>11/25</b> 게임 내 크로스월드는 사업 확정일. 웹 작업이 안 되더라도 그대로 개방</li>
<li><b>웹 일정</b> 모든 웹 작업은 12/8 스포2 오픈 이후 일괄 착수. 약 1개월, 1월 중순 완료 예상 (중간에 다른 작업이 끼지 않는 전제). 코브는 소스 확인 후 확정</li>
<li><b>순서</b> 랜딩(서버 선택) 제거 · 사이트 정리 → 팝업샵 · 컴퍼스 서버 선택 옵션 → 코브 수정 → 미스테리 코브</li>
<li><b>Lucky Wheel</b> 운영 중단. 메뉴 제거, URL 직접 접근 차단, 소스는 보존</li>
<li><b>지급 방식</b> 서버 무관 은행 수령은 SRE 불가. Send to Bank 시 Maris / Ventus 선택 팝업으로 진행 (팝업샵 · 컴퍼스 동일)</li>
<li><b>웹 로그인 이벤트</b> 2024년 이벤트와 동일하게, 이전 소스 재사용</li>
</ul>
<h3>주요 논의</h3><ul class="plain">
<li><b>미스테리 코브</b> 기존 TC보다 약 20% 저렴. 열쇠 가격 정책 · 아이템 테이블 · 어드민을 별도로 만들어야 하고 공통 플랫폼이라 키만 바꾸면 다른 게임에 영향. 개발 1~2개월, 11/25 불가</li>
<li><b>Treasure Cove</b> 크로스월드는 서버 통합이 아니어서 당분간 Maris / Ventus 코브 2개 유지 가능성. 통합 여부는 소스 확인 후</li>
<li><b>디자인</b> 미스테리 코브와 일반 코브는 최소 배경색으로 구분, 가능하면 디자인 개선. 미스테리 코브는 저가 느낌이되 너무 싸 보이지 않게. 디자인 요청은 착수 시</li>
<li><b>플로팅 배너</b> Maris ↔ Ventus 이동용이라 불필요해질 수 있음. 제거 여부 미정</li>
<li><b>배경</b> Ventus 런칭 때 적절한 시기에 크로스월드를 개방한다고 공지함</li>
<li><b>개발팀 일정</b> 스포2 빌링 · 세팅 · API 정리, 클로저스 Steam 오픈(11월 중순) 대응과 겹침</li>
</ul></div></details>'''
no_records = UWO_LOG + JP_LOG

EXTRA_CSS = '''
[hidden] { display: none !important; }
.wrap.single { max-width: 1120px; }
.panel > section, .proj { display: grid; gap: 18px; }
.psel, .fsel { display: flex; flex-wrap: wrap; gap: 6px; }
.psel a, .fsel button { font: inherit; font-size: 13.5px; font-weight: 600; text-decoration: none; color: var(--muted); background: var(--surface); border: 1px solid var(--line); border-radius: 999px; padding: 4px 14px; cursor: pointer; }
.psel a[aria-current="true"], .fsel button[aria-pressed="true"] { color: var(--surface); background: var(--accent); border-color: var(--accent); }
.psel a:focus-visible, .fsel button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.st.risk { background: var(--flag); color: var(--surface); }
.st.ok { background: var(--ok-soft); color: var(--ok); }
.st.now { background: var(--accent); color: var(--surface); }
.ptag { display: inline-block; font-size: 11.5px; font-weight: 600; color: var(--accent); background: var(--accent-soft); border-radius: 4px; padding: 0 6px; white-space: nowrap; vertical-align: 1px; }
table.ptable { min-width: 1060px; }
table.ptable td:nth-child(2), table.ptable td:nth-child(3), table.ptable td:nth-child(4), table.ptable td:nth-child(5) { white-space: nowrap; }
table.ptable td a, .g-name a { color: var(--fg); text-decoration: none; border-bottom: 1px solid var(--line); }
table.ptable td a:hover, .g-name a:hover { color: var(--accent); border-bottom-color: var(--accent); }
.pkv { margin: 0; display: grid; grid-template-columns: 104px minmax(0, 1fr); gap: 4px 12px; font-size: 14px; }
.pkv dt { color: var(--muted); font-size: 13px; padding-top: 1px; }
.pkv dd { margin: 0; }
.proj-sec { display: grid; gap: 18px; }
.proj h2 .st { font-size: 12px; }
tr.g-team td { background: var(--surface); }
tr.g-team .g-name { font-family: var(--font-mono); font-size: 11.5px; letter-spacing: .06em; color: var(--muted); max-width: none; border-right: 0; }
tr.g-team .g-name b { font-weight: 500; }
tr.g-msrow .g-lane { height: 46px; }
.g-span { position: absolute; top: 13px; height: 4px; border-radius: 2px; background: var(--accent-soft); border: 1px solid var(--accent); z-index: 1; }
.g-key.span { height: 4px; background: var(--accent-soft); border: 1px solid var(--accent); }
.g-ms.est, .g-key-ms.est { background: var(--surface); border: 2px solid var(--fg); }
.g-key-ms.est { width: 10px; height: 10px; }
.g-clash { position: absolute; top: 5px; bottom: 5px; border: 1.5px solid var(--flag); border-radius: 4px; background: repeating-linear-gradient(45deg, var(--flag-soft) 0 4px, transparent 4px 8px); z-index: 1; }
.g-par { position: absolute; top: 5px; bottom: 5px; border: 1.5px dashed var(--accent); border-radius: 4px; background: var(--accent-soft); opacity: .7; z-index: 1; }
.g-key.par { border: 1.5px dashed var(--accent); background: var(--accent-soft); }
.g-key.clash { border: 1.5px solid var(--flag); background: repeating-linear-gradient(45deg, var(--flag-soft) 0 3px, transparent 3px 6px); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; display: grid; gap: 2px; }
.stat b { font-size: 24px; font-variant-numeric: tabular-nums; line-height: 1.2; }
.stat span { font-size: 13px; color: var(--muted); }
.stat.flag b { color: var(--flag); }
table.chk td:first-child { width: 120px; }
table.uwo { min-width: 900px; }
table.uwo td:nth-child(2), table.uwo td:nth-child(5) { white-space: nowrap; }
table.uwo td:nth-child(3) { min-width: 240px; }
table.uwo td:nth-child(4) { min-width: 320px; }
h4.grp { margin: 4px 0 -6px; font-family: var(--font-mono); font-size: 11.5px; font-weight: 500; letter-spacing: .06em; color: var(--muted); }
table.issues { min-width: 760px; }
table.issues td.d { font-weight: 500; white-space: normal; min-width: 160px; }
table.issues tr.svc-first td { border-top: 1px solid var(--line); }
tr.gate td { background: var(--flag-soft); }
.sub-h { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
'''

n_open = sum(1 for p in PROJECTS for k in ('decider', 'pm', 'planner', 'design', 'dev', 'stage', 'next') if not p[k])
stats = f'''<div class="stats">
          <div class="stat"><b>{len(PROJECTS)}</b><span>등록 프로젝트</span></div>
          <div class="stat"><b>{sum(1 for p in PROJECTS if p['miles'])}</b><span>일정 입력된 프로젝트</span></div>
          <div class="stat flag"><b>{len(conf)}</b><span>프로젝트 간 인력 겹침</span></div>
          <div class="stat flag"><b>{n_open}</b><span>프로젝트 표 확인 필요 칸</span></div>
        </div>'''

page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>서비스개발실 웹 업무</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>{css_ref}
{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap single">
  <main>
    <header class="doc">
      <div class="meta"><span>{VERSION}</span><span>{BASE.year}.{BASE.month:02d}.{BASE.day:02d}</span><span>관리 테디 (서비스개발실)</span></div>
      <h1>서비스개발실 웹 업무</h1>
    </header>
    <div class="tabs" role="tablist"><a href="#overview" data-tab="overview">전체 현황</a><a href="#projects" data-tab="projects">프로젝트별</a><a href="#minutes" data-tab="minutes">회의록 · 미결</a><a href="#team" data-tab="team">팀 구성</a></div>

    <div id="overview" class="panel">
      <section>
        <div class="sub-h"><h2>진행 중인 프로젝트</h2><span class="asof">{md(BASE)} 기준</span></div>
        {stats}
        {project_table()}
      </section>
      <section>
        <h2>2주 안 일정</h2>
        {upcoming_table()}
      </section>
      <section>
        <div class="sub-h"><h2>운영 서비스 웹 이슈</h2><span class="asof">{ISSUES_ASOF} 기준 · 플랫폼개발팀 주요 이슈</span></div>
        {issues_table()}
        <ul class="plain note">
          <li>웹 작업이 아닌 항목은 제외: {' · '.join(ISSUES_EXCLUDED)}</li>
          <li>기간이 없는 진행 중 항목은 완료 목표일 확인 필요</li>
        </ul>
      </section>
      <section>
        <h2>전체 일정</h2>
        {overview_gantt()}
      </section>
      <section>
        <h2>인력별 작업 현황</h2>
        {people_gantt()}
        <ul class="plain note">
          <li>서비스개발실 인원만 표시. 사업팀 · 인프라 작업은 프로젝트별 간트에 있음</li>
          <li>같은 사람에게 3일 이상 같은 기간 진행 · 예정 작업이 2개 이상이면 표시. 프로젝트가 다르면 겹침(주황), 같은 프로젝트면 병행(파랑). 총괄 · 회의 작업은 제외</li>
        </ul>
      </section>
      <section>
        <h2>인력 충돌</h2>
        <div class="table-box">
          <table>
            <thead><tr><th>사람</th><th>겹치는 작업</th><th>기간</th><th>우선순위 결정</th></tr></thead>
            <tbody>{''.join(conf) or '<tr><td colspan="4" class="ctx">현재 프로젝트 간 겹침 없음. 아래 담당이 정해지면 다시 판단</td></tr>'}</tbody>
          </table>
        </div>
        <ul class="plain todo">
          <li><span class="chip">확인 필요</span> UWO 웹 작업(김영환 팀장, 12/8~1월 중순 예상)은 파파야플레이 일본 구축과 같은 시기. 일본 일정이 정해지면 겹침 판단</li>
          <li><span class="chip">확인 필요</span> 프로젝트 간 일정 · 인력 우선순위를 정할 사람 (서비스개발실장 공석)</li>
          <li><span class="chip">확인 필요</span> 한국 어드민 · 글로벌 · 일본 프로젝트 일정. 입력되어야 프로젝트 간 겹침을 판단할 수 있음</li>
          <li><span class="chip">확인 필요</span> 레이첼 · 정은이 담당 작업, 그 밖의 구성원 명단</li>
          <li><span class="chip">확인 필요</span> 라이브 게임 운영 업무를 인력별 현황에 상시 작업으로 표시할지</li>
        </ul>
        <h3>같은 프로젝트 안 병행</h3>
        <div class="table-box">
          <table>
            <thead><tr><th>사람</th><th>병행 작업</th><th>기간</th><th>순서 확인</th></tr></thead>
            <tbody>{''.join(par) or '<tr><td colspan="4" class="ctx">없음</td></tr>'}</tbody>
          </table>
        </div>
        <ul class="plain note">
          <li>프로젝트 일정표에서 계획한 병행이라 충돌로 보지 않음. 한 사람이 혼자 맡는 경우에만 부담 확인용으로 표시</li>
        </ul>
      </section>
    </div>

    <div id="projects" class="panel" hidden>
      <nav class="psel" aria-label="프로젝트 선택">{psel}</nav>

      <section id="p-sf2" class="proj" hidden>
        <h2>{esc(sf2["name"])} {st_badge(sf2["status"], sf2["status_txt"])}</h2>
        <dl class="pkv"><dt>결정권자</dt><dd>김충곤 팀장 (부재 시 고민제 PM)</dd><dt>PM</dt><dd>고민제 PM</dd><dt>웹기획</dt><dd>테디 팀장</dd><dt>디자인</dt><dd>테디 팀장</dd><dt>웹 개발</dt><dd>오중수 (총괄 김영환 팀장)</dd><dt>오픈 목표</dt><dd>12/8 웹사이트 오픈</dd><dt>정기 회의</dt><dd>매주 금요일 9:30~10:00</dd><dt>적용 범위</dt><dd>공식 웹사이트, 사전예약 페이지, 이벤트 · 프로모션 페이지</dd><dt>운영 가이드</dt><dd><a href="https://claude.ai/code/artifact/db142ad6-834e-4dc6-8554-5881f11c3448" target="_blank" rel="noopener">스포2 웹 업무 가이드</a> (업무별 담당, 금요일 회의, 논의 안건)</dd></dl>

        <div class="proj-sec" id="sf2-todo"><h3>확인 필요 항목</h3>{sf2_todo}</div>
        <div class="proj-sec" id="sf2-schedule"><h3>상세 일정</h3>
        {project_gantt(SF2_RANGE, SF2_TEAMS, SF2_MILES)}
        </div>
        <div class="proj-sec">{sf2_status.replace('<h3>팀별 현황', '<h3>팀별 현황') if '<h3>팀별 현황' in sf2_status else '<h3>팀별 현황 <span class="asof">10/12 기준</span></h3>' + sf2_status}</div>
        <div class="proj-sec"><h3>세부 일정</h3>{sf2_sched}{sf2_note}</div>
      </section>

{latale_section()}
{uwo_section()}
{''.join(checklist(p['id']) for p in PROJECTS if p['id'] not in ('sf2', 'latale', 'uwo'))}
    </div>

    <div id="minutes" class="panel" hidden>
      <div class="fsel" data-scope="minutes">{fsel}</div>
      <section>
        <h2>미결 사항</h2>
        <div class="table-box">
          <table>
            <thead><tr><th>프로젝트</th><th>안건</th><th>결정할 사람</th><th>막혀 있는 일</th></tr></thead>
            <tbody>{open_rows}</tbody>
          </table>
        </div>
      </section>
      <section>
        <h2>액션 아이템</h2>
        <div class="table-box">
          <table>
            <thead><tr><th>프로젝트</th><th>담당</th><th>내용</th><th>기한</th></tr></thead>
            <tbody>{action_rows}</tbody>
          </table>
        </div>
      </section>
      <section>
        <h2>결정 기록 · 회의록</h2>
        <div class="proj-sec" data-p="sf2"><h3>{esc(sf2["name"])}</h3>{sf2_minutes}</div>
        {no_records}
      </section>
    </div>

    <div id="team" class="panel" hidden>
      <section>
        <h2>팀 구성</h2>
        {team_html()}
      </section>
    </div>

    <footer>{VERSION} · {BASE.year}.{BASE.month:02d}.{BASE.day:02d}</footer>
  </main>
</div>

<script>
(function () {{
  var wrap = document.querySelector('.wrap');
  var panels = Array.prototype.slice.call(document.querySelectorAll('.panel'));
  var projs = Array.prototype.slice.call(document.querySelectorAll('.proj'));
  function showProj(id) {{
    projs.forEach(function (p) {{ p.hidden = p.id !== id; }});
    document.querySelectorAll('.psel a').forEach(function (a) {{
      if (('p-' + a.getAttribute('data-pid')) === id) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    }});
  }}
  function route() {{
    var h = decodeURIComponent((location.hash || '').slice(1));
    var el = h ? document.getElementById(h) : null;
    var panel = el ? (el.classList.contains('panel') ? el : el.closest('.panel')) : null;
    if (!panel) {{ panel = document.getElementById('overview'); el = panel; }}
    panels.forEach(function (p) {{ p.hidden = p !== panel; }});
    document.querySelectorAll('.tabs a').forEach(function (a) {{
      if (a.getAttribute('data-tab') === panel.id) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    }});
    if (panel.id === 'projects') {{
      var proj = el.classList.contains('proj') ? el : el.closest('.proj');
      showProj(proj ? proj.id : projs[0].id);
    }}
    if (el === panel || (el && el.classList.contains('proj'))) window.scrollTo(0, 0);
    else if (el) el.scrollIntoView();
  }}
  window.addEventListener('hashchange', route);
  route();

  document.querySelectorAll('.fsel').forEach(function (bar) {{
    var scope = document.getElementById(bar.getAttribute('data-scope'));
    bar.addEventListener('click', function (e) {{
      var b = e.target.closest('button'); if (!b) return;
      var f = b.getAttribute('data-f');
      bar.querySelectorAll('button').forEach(function (x) {{ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }});
      scope.querySelectorAll('[data-p]').forEach(function (n) {{
        n.hidden = !(f === 'all' || n.getAttribute('data-p') === f);
      }});
    }});
  }});
}})();
</script>
<script>
(function () {{
  var now = new Date(), today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  document.querySelectorAll('table.gantt[data-start]').forEach(function (t) {{
    var s = t.getAttribute('data-start').split('-'), e = t.getAttribute('data-end').split('-');
    var START = new Date(+s[0], s[1] - 1, +s[2]), END = new Date(+e[0], e[1] - 1, +e[2]);
    var PX = +t.getAttribute('data-px');
    var days = Math.round((today - START) / 86400000);
    var inRange = today >= START && today <= END;
    var left = (days * PX + PX / 2) + 'px';
    t.querySelectorAll('.g-today, .g-todaytag').forEach(function (el) {{ el.hidden = !inRange; el.style.left = left; }});
    var tag = t.querySelector('.g-todaytag');
    if (tag) tag.textContent = '오늘 ' + (today.getMonth() + 1) + '/' + today.getDate();
  }});
}})();
</script>
</body>
</html>
'''
page = re.sub(r'(?<!그래픽)디자인팀', '그래픽디자인팀', page)
page = re.sub(r'\s*\(논의 안건 스포2-\d\)', '', page)
page = re.sub(r'\s*\(공통-\d\)', '', page)
page = re.sub(r'<li><span class="chip ok">검토 요청</span>.*?</li>', '', page)
page = page.replace('<li>"제안" 표시 일정은 아직 확정 전입니다.</li>', '<li>"제안" 표시 일정은 아직 확정 전입니다. 확정되면 표시를 뺍니다.</li>')
open(OUT, 'w', encoding='utf-8').write(page)
print('ok', len(page), 'cross', len(conf), 'same', len(par))
