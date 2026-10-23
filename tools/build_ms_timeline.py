#!/usr/bin/env python3
"""R&R 문서 마일스톤 타임라인 생성기 — 각 문서 마일스톤 표(# / 마일스톤 / 시작일 / 목표일 / 담당)를 읽어
MSTL 마커 사이를 다시 쓴다. 마커가 없으면 마일스톤 표 바로 아래에 만든다.
사용: python3 tools/build_ms_timeline.py deploy YYYY-MM-DD"""
import re, sys, html, datetime as dt
from pathlib import Path
D = Path(sys.argv[1]); TODAY = dt.date.fromisoformat(sys.argv[2])
DOCS = ['cinderella_rnr_milestones.html', 'naver_red_rnr_milestones.html', 'gyeol_rnr_milestones.html']
def tx(x): return html.unescape(re.sub(r'<[^>]+>', ' ', x)).strip()
def pd(x):
    t = tx(x)
    if '■' in t: return None
    m = re.search(r'(\d{1,2})/(\d{1,2})', t)
    if not m: return None
    mo = int(m[1]); return dt.date(2026 if mo >= 7 else 2027, mo, int(m[2]))
def monday(d): return d - dt.timedelta(days=d.weekday())
CSS = '''<style>
.mtwrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);margin-top:6px;}
.mt{position:relative;min-width:max-content;--mtlab:200px;}
.mtrow{display:flex;border-bottom:1px solid var(--line);min-height:30px;} .mtrow:last-child{border-bottom:0;}
.mtlab{position:sticky;left:0;z-index:2;flex:0 0 var(--mtlab);background:var(--card);border-right:1px solid var(--line);padding:5px 10px;font-size:12px;line-height:1.35;display:flex;flex-wrap:wrap;gap:0 5px;align-items:center;}
.mtlab em{font-style:normal;color:var(--ink3);font-size:10.5px;width:100%;}
.mttr{position:relative;flex:0 0 auto;} .mthead .mttr{height:34px;}
.mtwk{position:absolute;top:0;height:34px;text-align:center;font-size:10.5px;line-height:1.3;padding-top:3px;border-left:1px solid var(--line);overflow:hidden;}
.mtwk b{display:block;} .mtwk i{display:block;font-style:normal;color:var(--ink3);font-size:9.5px;}
.mtgl{position:absolute;top:0;bottom:0;border-left:1px solid #f0ece4;}
.mtbar{position:absolute;top:8px;height:14px;border-radius:3px;}
.mtdia{position:absolute;top:9px;width:12px;height:12px;transform:rotate(45deg);}
.mtbar.now,.mtdia.now{background:#2F6FE8;} .mtbar.next,.mtdia.next{background:#dbe6fb;border:1px solid #2F6FE8;}
.mtbar.done,.mtdia.done{background:#3d8c4a;opacity:.6;} .mtbar.late,.mtdia.late{background:#fff;border:2px solid #c0392b;}
.mtbl{position:absolute;top:7px;font-size:10.5px;color:var(--ink3);white-space:nowrap;}
.mtna{position:absolute;left:8px;top:7px;font-size:10.5px;color:var(--ink3);}
.mttoday{position:absolute;top:34px;bottom:0;border-left:2px solid var(--accent);z-index:3;pointer-events:none;}
.mttoday span{position:absolute;top:-17px;left:3px;background:var(--accent);color:#fff;font-size:9.5px;font-weight:800;padding:0 4px;border-radius:3px;white-space:nowrap;}
@media (max-width:700px){.mt{--mtlab:150px;}}
</style>'''
for name in DOCS:
    F = D/name; s = F.read_text(encoding='utf-8')
    a = s.find('<tr><td>M1</td>'); tb_end = s.find('</table>', a) + len('</table>')
    rows = []
    for m in re.finditer(r'<tr><td>(M\d+)</td>(.*?)</tr>', s[s.rfind('<table', 0, a):tb_end], re.S):
        tds = re.findall(r'<td[^>]*>(.*?)</td>', m[2], re.S)
        done = '✅' in tds[0]
        nm = re.sub(r'✅\s*(완료)?', '', tx(re.split(r'<br', tds[0])[0])).strip()
        rows.append((m[1], nm, pd(tds[1]), pd(tds[2]), tx(tds[3]).split('/')[0].strip(), done))
    if not rows: sys.exit(f'오류: {name} 마일스톤 표에서 행을 못 읽음 — 갱신 중단')
    ds = [d for r in rows for d in (r[2], r[3]) if d]
    W0 = monday(min(ds)); W1 = monday(max(ds)); weeks = (W1 - W0).days//7 + 1
    DW = max(4, min(15, 560 // (weeks*5)))   # 평일 1일 px
    def x(d):
        days = (d - W0).days; wk, wd = divmod(days, 7); return (wk*5 + min(wd, 4)) * DW
    track = weeks*5*DW
    narrow = 5*DW < 44
    hs = []
    for i in range(weeks):
        wd = W0 + dt.timedelta(weeks=i)
        if narrow:
            if i == 0 or wd.month != (wd - dt.timedelta(weeks=1)).month:
                hs.append(f'<div class="mtwk" style="left:{i*5*DW}px;width:{5*DW*4}px;text-align:left;padding-left:4px"><b>{wd.month}월</b></div>')
        else:
            hs.append(f'<div class="mtwk" style="left:{i*5*DW}px;width:{5*DW}px"><b>{wd.month}/{wd.day}</b></div>')
    head = ''.join(hs)
    grid = ''.join(f'<div class="mtgl" style="left:{i*5*DW}px"></div>' for i in range(weeks+1))
    body = ''
    for rid, nm, st, en, who, done in rows:
        if not en:
            bar = '<div class="mtna">일정 미정 (■)</div>'
        else:
            c = 'done' if done else ('late' if en < TODAY else ('now' if st and st <= TODAY else 'next'))
            word = {'done': '완료', 'late': '목표일 경과', 'now': '진행', 'next': '예정'}[c]
            if st and st < en:
                x0, x1 = x(st), x(en) + DW
                bar = f'<div class="mtbar {c}" style="left:{x0}px;width:{max(x1-x0,DW)}px"></div>'
                lab = f'{st.month}/{st.day}–{en.month}/{en.day}'
            else:
                x1 = x(en) + DW
                bar = f'<div class="mtdia {c}" style="left:{x(en)+DW/2-6}px"></div>'; lab = f'{en.month}/{en.day}'
            bar += f'<div class="mtbl" style="left:{x1+5}px">{lab} · {word}</div>'
        body += (f'<div class="mtrow"><div class="mtlab"><b>{rid}</b> {html.escape(nm)}<em>{html.escape(who)}</em></div>'
                 f'<div class="mttr" style="width:{track+150}px">{grid}{bar}</div></div>')
    today = (f'<div class="mttoday" style="left:calc(var(--mtlab) + {x(TODAY)+DW/2}px)"><span>오늘 {TODAY.month}/{TODAY.day}</span></div>'
             if W0 <= TODAY <= W1 + dt.timedelta(days=6) else '')
    SEC = (f'<!-- MSTL:START — tools/build_ms_timeline.py가 위 마일스톤 표에서 생성. 직접 수정 금지 -->\n{CSS}\n'
           f'<h3 style="font-size:15px;font-weight:700;margin:22px 0 6px;">마일스톤 타임라인</h3>\n'
           f'<p class="cap">위 마일스톤 표의 시작일·목표일을 막대로 그린 것(평일 기준, 열 = 주 시작 월요일). '
           f'<b>진행</b> 파랑 · <b>예정</b> 연파랑 · <b>완료</b> 초록 · <b>목표일 경과</b> 빨간 테두리 · ◆ = 시작일 없는 단발 항목. 표를 고치면 다시 생성한다.</p>\n'
           f'<div class="mtwrap"><div class="mt">\n<div class="mtrow mthead"><div class="mtlab" style="font-size:11px;color:var(--ink3)">마일스톤 / 담당</div>'
           f'<div class="mttr" style="width:{track+150}px">{head}</div></div>\n{body}{today}\n</div></div>\n<!-- MSTL:END -->')
    if '<!-- MSTL:START' in s:
        s = re.sub(r'<!-- MSTL:START.*?<!-- MSTL:END -->', lambda _: SEC, s, flags=re.S)
    else:
        s = s[:tb_end] + '\n\n' + SEC + s[tb_end:]
    F.write_text(s, encoding='utf-8'); print(name, 'rows', len(rows), 'weeks', weeks, 'DW', DW)
