#!/usr/bin/env python3
"""프로젝트 보드 3장(마일스톤 타임라인) 생성기.
각 R&R 문서의 마일스톤 표를 읽어 index.html의 TIMELINE 마커 사이를 다시 쓴다.
사용: python3 tools/build_timeline.py [deploy 폴더] [기준일 YYYY-MM-DD]
보드 3장은 손으로 고치지 않는다 — R&R 문서를 고친 뒤 이 스크립트를 다시 돌린다.
"""
import re, sys, html, datetime as dt
from pathlib import Path

DEPLOY = Path(sys.argv[1] if len(sys.argv) > 1 else 'deploy')
TODAY = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date.today()
WEEK1 = dt.date(2026, 9, 28)          # 1주차 = 9/28(월)
PAST_WEEKS = 2                        # 1주차 앞에 보여줄 '이전' 주 수
W = 46                                # 주당 px

PROJECTS = [  # (문서, 표시명, 분류)
    ('cinderella_rnr_milestones.html',   '신데렐라 앱',            'A'),
    ('naver_red_rnr_milestones.html',    '네이버 레드 샘플 PoC',    'B'),
    ('love_roulette_rnr_milestones.html','러브룰렛 「모니터룸」',   'B'),
    ('playtoon_maker_rnr_milestones.html','PlayToon Maker',       'C'),
    ('gyeol_rnr_milestones.html',        '결 (GYEOL)',             'C'),
]
# 같은 작업이 두 문서에 걸쳐 있는 경우 — 부하 계산에서 한 번만 센다
LOAD_SKIP = {('playtoon_maker_rnr_milestones.html', 'M1')}  # = 네이버 레드 M2 Maker 지원
PEOPLE = ['전병모','이상훈','안국주','홍수화','이순형','박인성','이규선','유성현']

def text(x): return html.unescape(re.sub(r'<[^>]+>', '', x)).strip()

def pdate(cell):
    c = text(cell)
    if '■' in c: return None
    m = re.search(r'(\d{1,2})/(\d{1,2})', c)
    if not m: return None
    mo, d = int(m[1]), int(m[2])
    return dt.date(2026 if mo >= 7 else 2027, mo, d)

def parse(doc):
    s = (DEPLOY/doc).read_text(encoding='utf-8')
    out = []
    for m in re.finditer(r'<tr><td>(M\d+)</td>(.*?)</tr>', s, re.S):
        tds = re.findall(r'<td[^>]*>(.*?)</td>', m[2], re.S)
        name_html = tds[0]
        done = '✅' in name_html
        name = text(re.split(r'<br', name_html)[0])
        name = re.sub(r'✅\s*(완료)?', '', name).split(' — ')[0].strip()
        owner = text(tds[3]).split('/')[0]
        who = [p for p in PEOPLE if p in owner]
        out.append(dict(id=m[1], name=name, start=pdate(tds[1]), end=pdate(tds[2]), single=text(tds[1]) == '—',
                        done=done, owner=text(tds[3]), who=who))
    return out

def x(d):  # 날짜 → px
    origin = WEEK1 - dt.timedelta(weeks=PAST_WEEKS)
    return (d - origin).days * W / 7

def fmt(d): return f'{d.month}/{d.day}'

data = [(doc, nm, cat, parse(doc)) for doc, nm, cat in PROJECTS]
dated = [m for *_, ms in data for m in ms if m['end']]
last = max(m['end'] for m in dated)
nweeks = PAST_WEEKS + ((last - WEEK1).days // 7) + 1
origin = WEEK1 - dt.timedelta(weeks=PAST_WEEKS)
track_w = nweeks * W
view_start = origin

def week_head():
    cells = []
    for i in range(nweeks):
        d = origin + dt.timedelta(weeks=i)
        n = i - PAST_WEEKS + 1
        lab = f'{n}주' if n >= 1 else '이전'
        mon = f'<b>{d.month}월</b>' if d.day <= 7 or i == 0 else ''
        cls = 'wk past' if n < 1 else 'wk'
        cells.append(f'<div class="{cls}" style="left:{i*W}px;width:{W}px">{mon}<span>{lab}</span><i>{fmt(d)}</i></div>')
    return ''.join(cells)

def grid_lines():
    return ''.join(f'<div class="gl{" m" if (origin+dt.timedelta(weeks=i)).day<=7 else ""}" style="left:{i*W}px"></div>' for i in range(nweeks))

today_x = x(TODAY)
rows, undated, early = [], [], []
for doc, nm, cat, ms in data:
    rows.append(f'<div class="tl-row grp"><div class="tl-lab"><span class="lb {cat}">{cat}</span><a class="doc" href="{doc}">{nm}</a></div><div class="tl-track" style="width:{track_w}px">{grid_lines()}</div></div>')
    for m in ms:
        if not m['end']:
            undated.append((cat, nm, doc, m)); continue
        if m['end'] < origin:
            early.append((nm, m)); continue
        s = m['start'] or m['end']
        s = max(s, origin)
        x0, x1 = x(s), x(m['end'] + dt.timedelta(days=1))
        if m['done']: st = 'done'
        elif m['end'] < TODAY: st = 'late'
        elif m['start'] and m['start'] <= TODAY: st = 'now'
        else: st = 'next'
        span = f"{fmt(m['start'])}–{fmt(m['end'])}" if m['start'] else f"~{fmt(m['end'])}"
        tip = html.escape(f"{m['id']} {m['name']} · {span} · {m['owner']}")
        if m['start']:
            shape = f'<div class="bar {st} c{cat}" style="left:{x0:.1f}px;width:{max(x1-x0,6):.1f}px" title="{tip}"></div>'
        else:  # 단발 판단·시작 미정 → 목표일 마커
            shape = f'<div class="dia {st} c{cat}" style="left:{x(m["end"])+W/14-6:.1f}px" title="{tip}"></div>'
        note = '' if (m['start'] or m['single']) else ' · 시작 미정'
        label = f'<div class="bl" style="left:{x1+5:.1f}px">{span}{note}</div>'
        chk = ' ✅' if m['done'] else ''
        rows.append(f'<div class="tl-row"><div class="tl-lab ms"><b>{m["id"]}</b> {html.escape(m["name"])}{chk}<em>{html.escape(m["owner"])}</em></div>'
                    f'<div class="tl-track" style="width:{track_w}px">{grid_lines()}{shape}{label}</div></div>')

# 담당자별 동시 진행 부하 (완료 제외, 시작·목표 모두 있는 마일스톤)
load_rows = []
for p in PEOPLE:
    cells = []
    for i in range(nweeks):
        ws = origin + dt.timedelta(weeks=i); we = ws + dt.timedelta(days=4)
        hit = [f'{nm} {m["id"]}' for doc, nm, _, ms in data for m in ms
               if (doc, m['id']) not in LOAD_SKIP and p in m['who'] and not m['done'] and m['start'] and m['end']
               and m['start'] <= we and m['end'] >= ws]
        n = len(hit)
        cells.append(f'<div class="ld l{min(n,4)}" style="left:{i*W}px;width:{W}px" title="{html.escape(" / ".join(hit)) or "없음"}">{n or ""}</div>')
    load_rows.append(f'<div class="tl-row"><div class="tl-lab ms"><b>{p}</b></div><div class="tl-track" style="width:{track_w}px">{"".join(cells)}</div></div>')

und_html = ''
cur = None
items = []
for cat, nm, doc, m in undated:
    items.append(f'<li><span class="lb {cat}">{cat}</span><a class="doc" href="{doc}">{nm}</a> <b>{m["id"]}</b> {html.escape(m["name"])} <em>{html.escape(m["owner"])}</em></li>')
und_html = '<ul class="und">' + ''.join(items) + '</ul>'
early_html = ' · '.join(f'{nm} {m["id"]} {html.escape(m["name"])} ({fmt(m["end"])})' for nm, m in early)

SECTION = f'''<!-- TIMELINE:START — tools/build_timeline.py가 생성. 직접 수정 금지 -->
<style>
  .tl-wrap{{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:8px;}}
  .tl{{position:relative;min-width:max-content;--lab:250px;}}
  .tl-row{{display:flex;border-bottom:1px solid var(--line);min-height:30px;}}
  .tl-row:last-child{{border-bottom:0;}}
  .tl-lab{{position:sticky;left:0;z-index:3;flex:0 0 var(--lab);background:var(--card);border-right:1px solid var(--line);padding:5px 10px;font-size:12px;display:flex;align-items:center;gap:6px;}}
  .tl-lab.ms{{padding-left:22px;color:var(--ink2);flex-wrap:wrap;gap:0 5px;line-height:1.35;}}
  .tl-lab.ms em{{font-style:normal;color:var(--ink3);font-size:10.5px;width:100%;}}
  .tl-row.grp{{background:var(--soft);}} .tl-row.grp .tl-lab{{background:var(--soft);font-weight:800;}}
  .tl-track{{position:relative;flex:0 0 auto;}}
  .tl-head .tl-track{{height:46px;}}
  .wk{{position:absolute;top:0;height:46px;font-size:10.5px;color:var(--ink2);text-align:center;padding-top:3px;line-height:1.25;border-left:1px solid var(--line);}}
  .wk b{{display:block;font-size:10.5px;color:var(--ink);height:13px;}} .wk span{{display:block;font-weight:700;}} .wk i{{display:block;font-style:normal;color:var(--ink3);font-size:9.5px;}}
  .wk:not(:has(b:not(:empty))) {{}}
  .wk.past{{background:#f3f1ec;color:var(--ink3);}}
  .gl{{position:absolute;top:0;bottom:0;border-left:1px solid #f0ece4;}} .gl.m{{border-left-color:var(--line);}}
  .bar{{position:absolute;top:8px;height:14px;border-radius:3px;z-index:1;}}
  .dia{{position:absolute;top:9px;width:12px;height:12px;transform:rotate(45deg);z-index:1;}}
  .cA{{--pc:var(--a);}} .cB{{--pc:var(--b);}} .cC{{--pc:var(--c);}}
  .bar.now,.dia.now{{background:var(--pc);}}
  .bar.next,.dia.next{{background:color-mix(in srgb,var(--pc) 32%,#fff);border:1px solid var(--pc);}}
  .bar.done,.dia.done{{background:var(--e);opacity:.55;}}
  .bar.late,.dia.late{{background:#fff;border:2px solid #c0392b;}}
  .bl{{position:absolute;top:7px;font-size:10.5px;color:var(--ink3);white-space:nowrap;z-index:1;}}
  .today{{position:absolute;top:46px;bottom:0;width:0;border-left:2px solid var(--accent);z-index:2;pointer-events:none;}}
  .today span{{position:absolute;top:2px;left:3px;background:var(--accent);color:#fff;font-size:9.5px;font-weight:800;padding:0 4px;border-radius:3px;white-space:nowrap;}}
  .ld{{position:absolute;top:4px;height:22px;font-size:11px;font-weight:800;text-align:center;line-height:22px;border-left:1px solid var(--card);}}
  .ld.l1{{background:#eef3fd;color:var(--c);}} .ld.l2{{background:#fbe9c8;color:#8a5a00;}} .ld.l3,.ld.l4{{background:#f6c9bd;color:#a12e12;}}
  .tl-key{{display:flex;gap:14px;flex-wrap:wrap;font-size:11.5px;color:var(--ink2);margin:6px 0 0;align-items:center;}}
  .tl-key i{{display:inline-block;width:18px;height:10px;border-radius:2px;vertical-align:-1px;margin-right:4px;}}
  ul.und{{columns:2;column-gap:24px;list-style:none;padding:0;margin:6px 0 0;font-size:12px;}}
  ul.und li{{break-inside:avoid;padding:3px 0;border-bottom:1px dashed var(--line);}}
  ul.und em{{font-style:normal;color:var(--ink3);font-size:11px;}}
  h3.tl-h{{font-size:14px;font-weight:800;margin:20px 0 2px;}}
  @media (max-width:700px){{ul.und{{columns:1;}} .tl{{--lab:170px;}}}}
</style>
<h2><span class="n">3.</span> 마일스톤 타임라인 (주차)</h2>
<p class="cap">5개 R&amp;R 문서의 마일스톤 표에서 자동 생성 — 기준일 {TODAY.month}/{TODAY.day} · 1주차 = 9/28(월). 막대 = 시작일~목표일, ◆ = 시작일 없는 항목(단발 판단·시작 미정). 막대에 마우스를 올리면 담당·기간이 보인다. 이 장은 직접 고치지 않고 R&amp;R 문서를 고친 뒤 다시 생성한다.</p>
<div class="tl-key"><span><i style="background:var(--c)"></i>진행 중</span><span><i style="background:#dbe6fb;border:1px solid var(--c)"></i>예정</span><span><i style="background:var(--e);opacity:.55"></i>완료</span><span><i style="background:#fff;border:2px solid #c0392b"></i>목표일 경과·미완료</span><span><i style="background:var(--accent);width:3px"></i>오늘</span></div>
<div class="tl-wrap"><div class="tl">
  <div class="tl-row tl-head"><div class="tl-lab" style="font-size:11px;color:var(--ink3)">프로젝트 · 마일스톤 / 담당</div><div class="tl-track" style="width:{track_w}px">{week_head()}</div></div>
  {''.join(rows)}
  <div class="today" style="left:calc(var(--lab) + {today_x:.1f}px)"><span>오늘 {TODAY.month}/{TODAY.day}</span></div>
</div></div>
{('<p class="cap">창 이전 완료: ' + early_html + '</p>') if early else ''}

<h3 class="tl-h">3.1 담당자별 동시 진행 마일스톤 수</h3>
<p class="cap">주별로 겹치는 미완료 마일스톤 개수(담당 기준, 시작·목표일 모두 있는 것만). 2 이상은 우선순위 확인 대상(Maker M1 = 레드 M2는 같은 작업이라 한 번만 셈) — 칸에 마우스를 올리면 해당 건이 보인다.</p>
<div class="tl-wrap"><div class="tl">
  <div class="tl-row tl-head"><div class="tl-lab" style="font-size:11px;color:var(--ink3)">담당자</div><div class="tl-track" style="width:{track_w}px">{week_head()}</div></div>
  {''.join(load_rows)}
  <div class="today" style="left:calc(var(--lab) + {today_x:.1f}px)"></div>
</div></div>

<h3 class="tl-h">3.2 날짜 미정 (■) — 금요일 주간회의 기입 대상 {len(undated)}건</h3>
{und_html}
<!-- TIMELINE:END -->'''

idx = DEPLOY/'index.html'
s = idx.read_text(encoding='utf-8')
if '<!-- TIMELINE:START' in s:
    s = re.sub(r'<!-- TIMELINE:START.*?<!-- TIMELINE:END -->', lambda _: SECTION, s, flags=re.S)
else:
    s = s.replace('\n<footer>', '\n' + SECTION + '\n\n<footer>', 1)
idx.write_text(s, encoding='utf-8')
print(f'ok: {len(dated)} dated, {len(undated)} undated, {nweeks} weeks, last {last}')
