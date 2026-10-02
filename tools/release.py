#!/usr/bin/env python3
"""보드 배포 관문.
  python3 tools/release.py check                       deploy/가 배포 가능한 상태인지 검사 (실패 시 종료코드 1)
  python3 tools/release.py promote <초안파일> [표시명 분류]  drafts/의 문서를 deploy/로 승격
배포는 check 통과 후에만 한다. drafts/와 tools/는 배포하지 않는다.
"""
import re, sys, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DEPLOY, DRAFTS = ROOT/'deploy', ROOT/'drafts'

def check():
    errs = []
    for f in sorted(DEPLOY.rglob('*.html')):
        s = f.read_text(encoding='utf-8')
        rel = f.relative_to(DEPLOY)
        if 'name="draft"' in s or 'DRAFT:START' in s:
            errs.append(f'{rel}: 초안 표식이 남아 있음 — 승격 절차를 거치지 않은 문서')
        for m in re.finditer(r'(?:href|src)="([^"#?]+)', s):
            u = m[1]
            if re.match(r'(https?:|mailto:|data:|javascript:)', u): continue
            if 'drafts/' in u or u.startswith('../'):
                errs.append(f'{rel}: 배포 폴더 밖을 가리키는 링크 {u}'); continue
            tgt = (f.parent/u)
            if u in ('./', '.'): tgt = DEPLOY/'index.html'
            if not tgt.exists() and not Path(str(tgt)+'.html').exists():
                errs.append(f'{rel}: 깨진 링크 {u}')
    if errs:
        print('배포 불가 —', len(errs), '건'); [print(' ✗', e) for e in errs]; sys.exit(1)
    pending = sorted(p.name for p in DRAFTS.glob('*.html')) if DRAFTS.exists() else []
    print('배포 가능 ✓  (deploy/ 검사 통과)')
    if pending: print('  참고 — 미승격 초안(배포 제외):', ', '.join(pending))

def promote(name, title=None, cat=None):
    src = DRAFTS/name; dst = DEPLOY/name
    s = src.read_text(encoding='utf-8')
    s = re.sub(r'<!-- DRAFT:START -->.*?<!-- DRAFT:END -->\n?', '', s, flags=re.S)
    s = s.replace('<meta name="draft" content="true">\n', '').replace('<title>[초안] ', '<title>')
    s = re.sub(r' · 초안 v0\.\d+', ' · v1.0', s).replace(re.search(r'초안 v0\.\d+ — 검토 후 승격\. ', s).group(0) if re.search(r'초안 v0\.\d+ — 검토 후 승격\. ', s) else '§', '')
    dst.write_text(s, encoding='utf-8'); src.unlink()
    if title and cat:
        bt = ROOT/'tools'/'build_timeline.py'; t = bt.read_text(encoding='utf-8')
        if name not in t:
            t = re.sub(r"(PROJECTS = \[.*?\n)(\])", lambda m: m[1] + f"    ('{name}', '{title}', '{cat}'),\n" + m[2], t, count=1, flags=re.S)
            bt.write_text(t, encoding='utf-8')
    print(f'승격 완료: {name} → deploy/  (남은 일: 보드 행 상세 칸 링크 · README 갱신 · build_timeline 실행 · check)')

if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['check']: check()
    elif a[:1] == ['promote'] and len(a) >= 2: promote(a[1], *(a[2:4] if len(a) >= 4 else (None, None)))
    else: print(__doc__)
