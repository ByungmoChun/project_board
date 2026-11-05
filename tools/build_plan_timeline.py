#!/usr/bin/env python3
"""보드 3장 — 다음 일정안(가안) 생성기. 아래 PLAN·DECISIONS·NOTES만 고치고 실행한다.
대표 판단으로 확정된 항목은 여기서 지우고 해당 R&R 문서 마일스톤 표로 옮긴다(→ 2장 타임라인에 나타남).
사용: python3 tools/build_plan_timeline.py deploy YYYY-MM-DD"""
import sys, re, html, datetime as dt
from pathlib import Path
D = Path(sys.argv[1]); TODAY = dt.date.fromisoformat(sys.argv[2])
BASIS = '11/5 대표 보고 기준 (메이커 개발 일정안 · 디자인 제작 일정안)'
def d(s):
    m, dd = map(int, s.split('/')); return dt.date(2026 if m >= 7 else 2027, m, dd)
# (그룹, 행 이름, [(시작, 끝, 라벨, 색)], 메모)  — 끝==시작이면 ◆
PLAN = [
 ('개발', '플레이북 V2 후속', [('11/9','11/27','안정화·버그','#b9b2ef')], 'V2 마감 ✅ 11/06 → 2장 확정'),
 ('개발', '메이커 V3', [('11/9','3/12','스파인 편집 내재화·IK 메시·어시스턴트·MCP·자체 본 애니·로직블록·로컬라이즈 AI·이미지 생성 → 3월 중순','#5b4fc4')], '수화 전담 · 국주 보조'),
 ('개발', 'FMV 러브룰렛', [('11/9','11/13','영상 AI 분석·리스트업','#c97a10'), ('11/16','12/4','알파 2~3주','#f0a030'), ('12/7','1/15','베타 6주','#f5c97a'), ('1/18','1/18','서비스 오픈 미정','#f5c97a')], '국주 · 11/4 소스 수령 · 리스트업 후 세부 일정'),
 ('개발', '결 · 감정 TTS', [('11/2','2/19','감정 TTS ~2/19 (렌탈 GPU) · 영상 클립 API','#d4507a')], '순형 · 외부 API 우선 → 렌탈 GPU'),
 ('개발', 'AI 장비 (맥 스튜디오)', [('11/10','1/8','11/10~1/10 대여(2달) → 렌탈 GPU','#9b3030'), ('1/11','3/12','반환 후 학습·추론 내재화','#1f9e72')], ''),
 ('디자인', '뮤직비디오 (나홍이)', [('11/5','11/23','본편 13일','#f0a030'), ('11/24','11/27','폴리싱·쇼츠 ~11/27','#d4507a')], '성현 전담'),
 ('디자인', '레드', [('11/10','11/10','11/10 녹음','#888'), ('11/12','11/16','적용·납품','#888')], ''),
 ('디자인', '어린왕자 ① 선행', [('11/30','12/11','그림체 → 연출 기획','#d95c32'), ('12/1','12/14','리소스 → 분절 외주','#d95c32')], '뮤비 종료 후 착수'),
 ('디자인', '어린왕자 ② 애니', [('12/15','4/16','12/15 킥오프 → 4월 초~중순 (분절·보이스·사운드 외주) · 메이커 기술 지원','#d95c32')], '리소스 완료 후 16~18주'),
 ('디자인', '빨간 망토 — 선행', [('11/2','11/6','기획 1차 ~11/6','#a6dcc6'), ('11/30','12/11','모델·리소스','#2a9a6c'), ('12/7','12/14','분절 외주','#2a9a6c')], ''),
 ('디자인', '빨간 망토 — 병렬(+2명)일 경우', [('12/22','3/12','12/22 킥오프 → 애니·로비 → 3월 중순','#1f9e72')], '두 작품 4월 중순 완료'),
 ('디자인', '빨간 망토 — 순차일 경우', [('4/20','4/30','4/20 ~ 7월 중순 →','#a6dcc6')], '어린왕자 뒤 12주 · 7월 중순 완료'),
]
MARKS = [('11/6','V2 완료','#7b6fdc'), ('11/27','뮤비 마감','#d4507a'), ('12/15','어린왕자 킥오프','#d95c32')]
SHADE = ('11/30','12/18','12월: 어린왕자·빨간 망토 선행 동시 → 디자인팀 병목(+2명 필요)')
DECISIONS = [
 ('어린왕자 분절 외주 승인', '어린왕자 · 빨간 망토', '외주 전제로 16~18주 산출 — 내부 분절이면 일정 불성립. 외주 비용(분절+4개 국어 보이스+사운드) 최소 약 6,000만 원은 본계약 협상 기초 자료'),
 ('어린왕자·빨간 망토 병렬 여부', '어린왕자 · 빨간 망토 · 디자인팀', '순차 28~30주(빨간 망토 7월경) / 병렬 16~18주(두 작품 4월 중순, 스파인 애니메이터 +2명 12월 초 합류)'),
 ('뮤직비디오 우선순위 유지', '어린왕자 · 빨간 망토', '어린왕자·빨간 망토 실작업이 11/28 이후로 밀린 원인'),
 ('어린왕자 보이스 방식 3안', '어린왕자', '① 풀 AI ② 나레이션 AI + 인물 성우 ③ 전부 성우(4개 국어) — 본계약 · K-POP 스타 조건과 연계'),
 ('V2 이후 단계 승인 · 명칭', 'PlayToon Maker', 'V3 / V2.5 / AI 확장 — 수화 전담 투입, 사업 요청 스펙 반영'),
 ('MCP 개발 · 외부 공개 범위', 'PlayToon Maker', '내부용만 / 외부 공개(AI 비용 전가 · BM 설계 필요)'),
 ('맥 스튜디오 대여 · AI 렌탈 예산 · 새 장비', '결 · TTS · 메이커 V3', '대여 최대 2달(1월 중순 반환) · 렌탈 GPU 월 상한 · 학습용 4090/5090급 윈도우 머신 요청'),
]
NOTES = [
 '<b>플레이북 V2</b> — 11/6 마감 확정(→ Maker 문서 2.0, 2장). 이후 안정화·버그 대응만 가안으로 남김.',
 '<b>어린왕자</b> — 리소스(모델·배경) 완료 후 16~18주, 분절·보이스·사운드 외주 전제. 분량 약 2시간(신데렐라의 9배). 본계약 전제 조건(POMASE 승인 절차 · K-POP 스타 참여)이 기산점을 밀 수 있음.',
 '<b>빨간 망토</b> — 리소스 완료 후 12주, 로비 전면 개편(테마 로비 · 수집 · 꾸미기) 포함. 로비 상훈 · 서버 순형.',
 '<b>FMV 러브룰렛</b> — 영상 소스 11/04 수령(약 27TB) → 백업 복사 ~3일 → 11/9 주 AI 분석·리스트업(국주) → 알파 2~3주(챕터 1, 재미·자극·결제 검증) → 베타 6주 → 서비스. 알파·베타는 리스트업으로 분량을 본 뒤 세부 확정.',
 '<b>메이커 V3</b> — 기본 버전 3월 중순(가안). 스파인 편집·물리(V2 범위 밖 배포분) 디벨롭과 사업 요청 스펙(AI 어시스턴트) 중심.',
 '<b>결 · 감정 TTS</b> — 맥 스튜디오 대여로 외부 API 선행 → 렌탈 GPU 전환. 팁스 평가 대상(영상 클립 + Emotional TTS).',
]
# ---- 렌더 ----
W0 = d('11/2'); WEND = d('4/30'); weeks = ((WEND - W0).days // 7) + 1; DW = 6
def x(day): days = (day - W0).days; wk, wd = divmod(days, 7); return (wk*5 + min(wd, 4)) * DW
track = weeks*5*DW
hd = ''
for i in range(weeks):
    w = W0 + dt.timedelta(weeks=i)
    if i == 0 or w.month != (w - dt.timedelta(weeks=1)).month:
        hd += f'<div class="plwk" style="left:{i*5*DW}px"><b>{w.month}월</b></div>'
grid = ''.join(f'<div class="plgl" style="left:{i*5*DW}px"></div>' for i in range(weeks+1))
sx0, sx1 = x(d(SHADE[0])), x(d(SHADE[1])) + DW
shade = f'<div class="plshade" style="left:{sx0}px;width:{sx1-sx0}px"></div>'
rows = ''; grp = None
for g, name, segs, memo in PLAN:
    if g != grp:
        rows += f'<div class="plrow plgrp"><div class="pllab">{g}팀</div><div class="pltr" style="width:{track}px"></div></div>'; grp = g
    bars = ''
    for si, (a, b, lab, col) in enumerate(segs):
        top = 6 + si*17
        A, B = d(a), d(b)
        if A == B:
            bars += f'<div class="pldia" style="top:{top+1}px;left:{x(A)+DW/2-5}px;border-color:{col}" title="{html.escape(lab)}"></div><div class="plbl" style="top:{top-1}px;left:{x(A)+DW+6}px">{html.escape(lab)}</div>'
        else:
            x0, x1 = x(A), x(B) + DW
            bars += f'<div class="plbar" style="top:{top}px;left:{x0}px;width:{max(x1-x0,DW*2)}px;border-color:{col};background:{col}22" title="{html.escape(lab)} ({A.month}/{A.day}~{B.month}/{B.day})"></div><div class="plbl" style="top:{top-1}px;left:{x1+4}px">{html.escape(lab)}</div>'
    rh = 12 + len(segs)*17
    rows += (f'<div class="plrow" style="min-height:{rh}px"><div class="pllab"><b>{html.escape(name)}</b>' + (f'<em>{html.escape(memo)}</em>' if memo else '') +
             f'</div><div class="pltr" style="width:{track+260}px">{grid}{shade}{bars}</div></div>')
marks = ''.join(f'<div class="plmark" style="left:calc(var(--pllab) + {x(d(m))+DW/2}px);border-color:{c}"><span style="background:{c};bottom:{-18-(i%2)*16}px">{l} {d(m).month}/{d(m).day}</span></div>' for i, (m, l, c) in enumerate(MARKS))
today = f'<div class="plmark" style="left:calc(var(--pllab) + {x(TODAY)+DW/2}px);border-color:var(--accent);border-left-style:solid"><span style="background:var(--accent);top:-44px">오늘 {TODAY.month}/{TODAY.day}</span></div>' if W0 <= TODAY <= WEND else ''
dec = ''.join(f'<tr><td>{i}</td><td><b>{html.escape(a)}</b></td><td>{html.escape(b)}</td><td>{html.escape(c)}</td><td class="date">대기</td></tr>' for i, (a, b, c) in enumerate(DECISIONS, 1))
notes = ''.join(f'<li>{n}</li>' for n in NOTES)
SEC = f'''<!-- PLAN:START — tools/build_plan_timeline.py가 생성. 직접 수정 금지 -->
<style>
.plwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);margin-top:6px;}}
.pl{{position:relative;min-width:max-content;--pllab:200px;padding-top:20px;padding-bottom:38px;}}
.plrow{{display:flex;border-bottom:1px solid var(--line);min-height:30px;}} .plrow:last-child{{border-bottom:0;}}
.plrow.plgrp{{background:var(--soft);min-height:24px;}} .plrow.plgrp .pllab{{background:var(--soft);font-weight:800;font-size:11.5px;}}
.pllab{{position:sticky;left:0;z-index:4;flex:0 0 var(--pllab);background:var(--card);border-right:1px solid var(--line);padding:5px 10px;font-size:12px;line-height:1.35;display:flex;flex-wrap:wrap;align-items:center;gap:0 5px;}}
.pllab em{{font-style:normal;color:var(--ink3);font-size:10.5px;width:100%;}}
.pltr{{position:relative;flex:0 0 auto;}} .plhead .pltr{{height:26px;}}
.plwk{{position:absolute;top:0;height:26px;font-size:11px;padding:5px 0 0 4px;border-left:1px solid var(--line);white-space:nowrap;}}
.plgl{{position:absolute;top:0;bottom:0;border-left:1px solid #f3efe8;}}
.plshade{{position:absolute;top:0;bottom:0;background:rgba(217,92,50,.07);}}
.plbar{{position:absolute;height:12px;border:1.5px dashed;border-radius:3px;}}
.pldia{{position:absolute;width:10px;height:10px;border:1.5px dashed;transform:rotate(45deg);background:#fff;}}
.plbl{{position:absolute;font-size:10.5px;color:var(--ink2);white-space:nowrap;}}
.plmark{{position:absolute;top:46px;bottom:38px;border-left:1.5px dashed;z-index:3;pointer-events:none;}}
.plmark span{{position:absolute;left:-2px;color:#fff;font-size:9.5px;font-weight:800;padding:0 4px;border-radius:3px;white-space:nowrap;}}
.plshade-note{{font-size:11.5px;color:#b5482a;font-weight:700;margin:8px 0 0;}}
@media (max-width:700px){{.pl{{--pllab:150px;}}}}
</style>
<h2><span class="n">3.</span> 다음 일정안 <span style="font-weight:400;font-size:12.5px;color:var(--ink3);">— 가안 · 대표 판단 대기</span></h2>
<p class="cap">{BASIS}. <b>확정 일정이 아니다</b> — 막대는 점선. 대표 판단으로 확정된 항목은 이 장에서 빼고 해당 R&amp;R 문서 마일스톤으로 옮긴다(그러면 2장 타임라인에 실선으로 나타난다). 판단이 모두 끝나면 이 장은 비운다.</p>
<h3 style="font-size:14px;font-weight:700;margin:14px 0 6px;">① 대표 판단 대기 ({len(DECISIONS)}건)</h3>
<table style="table-layout:fixed">
  <tr><th style="width:4%">#</th><th style="width:22%">판단 사항</th><th style="width:16%">영향</th><th>선택지 · 조건</th><th style="width:7%">결정</th></tr>
  {dec}
</table>
<h3 style="font-size:14px;font-weight:700;margin:18px 0 6px;">② 일정안 타임라인 (11월 ~ 4월)</h3>
<p class="plshade-note">▼ {SHADE[2]}</p>
<div class="plwrap"><div class="pl">
<div class="plrow plhead"><div class="pllab" style="font-size:11px;color:var(--ink3)">작품 · 과제</div><div class="pltr" style="width:{track+260}px">{hd}</div></div>
{rows}{marks}{today}
</div></div>
<h3 style="font-size:14px;font-weight:700;margin:18px 0 6px;">③ 설명</h3>
<ul>{notes}</ul>
<p class="cap">보고서 원본 2건(11/5 대표 보고)은 외주 비용·인력·장비 사항을 담고 있어 보드에 올리지 않고 사내 보관한다.</p>
<!-- PLAN:END -->'''
F = D/'index.html'; s = F.read_text(encoding='utf-8')
if '<!-- PLAN:START' in s:
    s = re.sub(r'<!-- PLAN:START.*?<!-- PLAN:END -->', lambda _: SEC, s, flags=re.S)
else:
    k = s.find('<!-- TIMELINE:END -->') + len('<!-- TIMELINE:END -->')
    s = s[:k] + '\n\n' + SEC + s[k:]
F.write_text(s, encoding='utf-8'); print('plan rows', len(PLAN), 'decisions', len(DECISIONS))
