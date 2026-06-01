# GitHub [LEEYOUNGJIN-GIT/Project](https://github.com/LEEYOUNGJIN-GIT/Project) 배포

## 이 저장소에 추가되는 것 (기존 루트 교재는 그대로)

```
.github/workflows/CISA/   ← 6개 워크플로 (실행)
CISA/                    ← 스크립트·설정·output
.gitignore               ← CISA/output 제외
```

교재 경로: **repo 루트** (`MASTER_SYSTEM.md`, `KOREAN.md`, `D1_IS감사프로세스.md` ~ `D5_정보자산보호.md`).  
`domains.yaml`의 `materials_dir: .` — `C1/` 하위 폴더는 사용하지 않음.

## 1. Secret 등록

**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|--------|
| `GEMINI_API_KEY` | Google AI Studio API 키 |

## 2. 푸시 (로컬 eng 커밋 없이 Project만)

```powershell
cd $env:TEMP
git clone https://github.com/LEEYOUNGJIN-GIT/Project.git
cd Project

# eng 폴더에서 복사 (경로 본인 환경에 맞게)
Copy-Item -Recurse "C:\Users\AP493158\Desktop\eng\CISA" .
Copy-Item -Recurse "C:\Users\AP493158\Desktop\eng\.github" .
Copy-Item "C:\Users\AP493158\Desktop\eng\.gitignore" . -ErrorAction SilentlyContinue

git add CISA .github .gitignore
git status
git commit -m "Add CISA Gemini question generation workflows"
git push origin main
```

## 3. Actions 실행

1. **Actions** 탭 → `CISA Generate — D1` (또는 D2~D5, 도메인 연계)
2. **Run workflow** → `phase` 1 (문제) / 2 (해설)
3. 완료 후 **Artifacts** → `cisa-D1-phase1` 등 다운로드

## 4. (선택) 생성 결과를 repo에 커밋

기본은 Artifact만 저장. repo에 남기려면 워크플로에 `git-auto-commit` 단계 추가.
