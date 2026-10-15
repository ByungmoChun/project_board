#!/usr/bin/env python3
"""주간 스냅샷: deploy/의 보드·상세 문서를 deploy/snapshots/<날짜>/에 고정본으로 복사한다.
사용: python3 tools/snapshot.py deploy YYYY-MM-DD"""
import re, sys, shutil
from pathlib import Path
D = Path(sys.argv[1]); date = sys.argv[2]
out = D/'snapshots'/date; out.mkdir(parents=True, exist_ok=True)
banner = (f'<div style="background:#eef3fd;border:1.5px solid #9db6ea;color:#1f3f7a;border-radius:8px;padding:8px 14px;'
          f'margin:0 0 14px;font-size:12.5px;">📸 <b>주간 스냅샷 {date}</b> — 이 날짜 기준의 고정본입니다. 이후 변경은 반영되지 않습니다. '
          f'<a href="../../" style="color:#1f3f7a;font-weight:700;">현재 보드로 →</a> · <a href="../" style="color:#1f3f7a;">스냅샷 목록</a></div>')
for f in sorted(D.glob('*.html')):
    s = f.read_text(encoding='utf-8')
    s = re.sub(r'(href|src)="files/', r'\1="../../files/', s)
    s = s.replace('href="snapshots/"', 'href="../"')
    s = s.replace('<div class="wrap">', '<div class="wrap">\n' + banner, 1)
    s = re.sub(r'<title>', f'<title>[스냅샷 {date}] ', s, count=1)
    (out/f.name).write_text(s, encoding='utf-8')
# 목록 페이지
dates = sorted([p.name for p in (D/'snapshots').iterdir() if p.is_dir()], reverse=True)
items = ''.join(f'<li><a href="{d}/">{d}</a></li>' for d in dates)
(D/'snapshots'/'index.html').write_text(f'''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>주간 스냅샷 목록</title>
<style>body{{font-family:Pretendard,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;background:#faf8f4;color:#222;max-width:720px;margin:40px auto;padding:0 20px}}h1{{font-size:20px}}li{{margin:8px 0;font-size:15px}}a{{color:#c8452a;font-weight:700;text-decoration:none}}p{{color:#777;font-size:13px}}</style></head>
<body><h1>개발본부 프로젝트 보드 — 주간 스냅샷</h1><p>매주 목요일 보드 갱신 후 그 주 상태를 날짜별 고정본으로 보관합니다. <a href="../">← 현재 보드</a></p><ul>{items}</ul></body></html>''', encoding='utf-8')
print('snapshot', out, len(list(out.glob('*.html'))), 'pages')
