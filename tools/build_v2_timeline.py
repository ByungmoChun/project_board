#!/usr/bin/env python3
"""PlayToon Maker 문서 2.2 V2 타임라인 생성기 — 2.1 표(기간·상태)를 읽어 V2TL 마커 사이를 다시 쓴다.
사용: python3 tools/build_v2_timeline.py deploy YYYY-MM-DD"""
import re, sys, html, datetime as dt
from pathlib import Path
D = Path(sys.argv[1]); TODAY = dt.date.fromisoformat(sys.argv[2])
F = D/'playtoon_maker_rnr_milestones.html'
s = F.read_text(encoding='utf-8')
W1 = dt.date(2026, 9, 28); WEEKS = 6; DW = 15   # 1일당 px (평일 5일 × 6주)
def tx(x): return html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
def pd(x):
    m = re.search(r'(\d{1,2})/(\d{1,2})', x); return dt.date(2026, int(m[1]), int(m[2])) if m else None
a = s.find('<!-- V21:START -->'); b = s.find('<!-- V21:END -->')
rows = []
for m in re.finditer(r'<tr><td[^>]*>([FS]\d(?:-\d)?)</td>(.*?)</tr>', s[a:b], re.S):
    tds = re.findall(r'<td[^>]*>(.*?)</td>', m[2], re.S)
    if '-' in m[1]: continue
    name, who, per, st = tx(tds[0]), tx(tds[1]), tds[3], tx(tds[4])
    ds = re.findall(r'(\d{1,2}/\d{1,2})', per)
    end = pd(ds[-1]) if ds else None
    start = pd(ds[0]) if len(ds) == 2 else None
    rows.append((m[1], name, who, start, end, st))
if not rows:
    sys.exit('오류: 2.1 표에서 행을 하나도 읽지 못함 — 표 형식 확인 필요(타임라인 갱신 중단)')
def x(d):  # 평일 기준 위치
    days = (d - W1).days; wk, wd = divmod(days, 7); return (wk*5 + min(wd, 4)) * DW
track = WEEKS*5*DW
head = ''.join(f'<div class="v2wk" style="left:{i*5*DW}px;width:{5*DW}px"><b>{i+1}주</b><i>{(W1+dt.timedelta(weeks=i)).month}/{(W1+dt.timedelta(weeks=i)).day}~</i></div>' for i in range(WEEKS))
grid = ''.join(f'<div class="v2gl" style="left:{i*5*DW}px"></div>' for i in range(WEEKS+1))
body = ''
for rid, name, who, st_d, en_d, st in rows:
    if not en_d: bar = '<div class="v2na">일정 미정</div>'
    else:
        if '완료' in st: c = 'done'
        elif '보류' in st: c = 'hold'
        elif '지연' in st or (en_d < TODAY): c = 'late'
        elif '진행' in st: c = 'now'
        else: c = 'next'
        if st_d:
            x0, x1 = x(st_d), x(en_d) + DW
            bar = f'<div class="v2bar {c}" style="left:{x0}px;width:{max(x1-x0,DW)}px" title="{html.escape(f"{rid} {name} · {st_d.month}/{st_d.day}~{en_d.month}/{en_d.day} · {st}")}"></div>'
            lab = f'{st_d.month}/{st_d.day}–{en_d.month}/{en_d.day}'
        else:
            x1 = x(en_d) + DW
            bar = f'<div class="v2dia {c}" style="left:{x(en_d)+DW/2-6}px"></div>'; lab = f'~{en_d.month}/{en_d.day}'
        bar += f'<div class="v2bl" style="left:{x1+5 if st_d else x(en_d)+DW+3}px">{lab} · {html.escape(st)}</div>'
    body += (f'<div class="v2row"><div class="v2lab"><b>{rid}</b> {html.escape(name)}<em>{html.escape(who)}</em></div>'
             f'<div class="v2tr" style="width:{track}px">{grid}{bar}</div></div>')
tx_ = x(TODAY) if W1 <= TODAY <= W1+dt.timedelta(weeks=WEEKS) else None
today = f'<div class="v2today" style="left:calc(var(--v2lab) + {tx_+DW/2}px)"><span>오늘 {TODAY.month}/{TODAY.day}</span></div>' if tx_ is not None else ''
SEC = f'''<!-- V2TL:START — tools/build_v2_timeline.py가 2.1 표에서 생성. 직접 수정 금지 -->
<style>
.v2wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);margin-top:6px;}}
.v2{{position:relative;min-width:max-content;--v2lab:200px;}}
.v2row{{display:flex;border-bottom:1px solid var(--line);min-height:30px;}} .v2row:last-child{{border-bottom:0;}}
.v2lab{{position:sticky;left:0;z-index:2;flex:0 0 var(--v2lab);background:var(--card);border-right:1px solid var(--line);padding:5px 10px;font-size:12px;line-height:1.35;display:flex;flex-wrap:wrap;gap:0 5px;align-items:center;}}
.v2lab em{{font-style:normal;color:var(--ink3);font-size:10.5px;width:100%;}}
.v2tr{{position:relative;flex:0 0 auto;}} .v2head .v2tr{{height:34px;}}
.v2wk{{position:absolute;top:0;height:34px;text-align:center;font-size:11px;line-height:1.3;padding-top:3px;border-left:1px solid var(--line);}}
.v2wk b{{display:block;}} .v2wk i{{display:block;font-style:normal;color:var(--ink3);font-size:9.5px;}}
.v2gl{{position:absolute;top:0;bottom:0;border-left:1px solid #f0ece4;}}
.v2bar{{position:absolute;top:8px;height:14px;border-radius:3px;}}
.v2dia{{position:absolute;top:9px;width:12px;height:12px;transform:rotate(45deg);}}
.v2bar.now,.v2dia.now{{background:#2F6FE8;}} .v2bar.next,.v2dia.next{{background:#dbe6fb;border:1px solid #2F6FE8;}}
.v2bar.done,.v2dia.done{{background:#3d8c4a;opacity:.6;}} .v2bar.late,.v2dia.late{{background:#fff;border:2px solid #c0392b;}}
.v2bar.hold,.v2dia.hold{{background:repeating-linear-gradient(45deg,#f3e3b0 0 5px,#fff 5px 10px);border:1px solid #c99a1d;}}
.v2bl{{position:absolute;top:7px;font-size:10.5px;color:var(--ink3);white-space:nowrap;}}
.v2na{{position:absolute;left:8px;top:7px;font-size:10.5px;color:var(--ink3);}}
.v2today{{position:absolute;top:34px;bottom:0;border-left:2px solid var(--accent);z-index:3;pointer-events:none;}}
.v2today span{{position:absolute;top:-17px;left:3px;background:var(--accent);color:#fff;font-size:9.5px;font-weight:800;padding:0 4px;border-radius:3px;white-space:nowrap;}}
@media (max-width:700px){{.v2{{--v2lab:150px;}}}}
</style>
<p class="cap">2.1 표의 기간·상태를 그대로 막대로 그린 것(평일 기준, 1주차 = 9/28). <b>진행</b> 파랑 · <b>예정</b> 연파랑 · <b>완료</b> 초록 · <b>지연·목표일 경과</b> 빨간 테두리 · <b>보류</b> 빗금. 세부 태스크 일정은 Jira(2.3)에서 본다.</p>
<div class="v2wrap"><div class="v2">
<div class="v2row v2head"><div class="v2lab" style="font-size:11px;color:var(--ink3)">기능 · 지원 / 담당</div><div class="v2tr" style="width:{track}px">{head}</div></div>
{body}{today}
</div></div>
<!-- V2TL:END -->'''
s = re.sub(r'<!-- V2TL:START.*?<!-- V2TL:END -->', lambda _: SEC, s, flags=re.S)
F.write_text(s, encoding='utf-8'); print('v2 timeline rows', len(rows))
