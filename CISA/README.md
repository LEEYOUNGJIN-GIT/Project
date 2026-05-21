# CISA 자동 문제 생성 (Gemini + GitHub Actions)

## 폴더 구조

```
CISA/
  config/domains.yaml      ← 로직 트리 설정 (MODE → 파일·문항수·연계 pair)
  prompts/generation_brief.md
  scripts/generate_questions.py   ← 단일 진입점
  workflows/*.yml          ← 소스 복사본 (GitHub 실행 경로는 아래 참고)
  output/                  ← 생성 결과 (gitignore)

.github/workflows/CISA/   ← GitHub Actions가 실제 실행하는 YAML (6개)
C1/                        ← 교재·MASTER_SYSTEM·D1~D5
```

> GitHub는 **`.github/workflows/`** 아래 YAML만 자동 실행합니다.  
> `CISA/workflows/`는 동일 파일의 **보관·편집용** 복사본입니다.

## 로직 트리

```
workflow_dispatch (D1~D5 / CROSS 중 하나 클릭)
        │
        ▼
  env: CISA_MODE=D4  (YAML에 고정 — 스크립트 분기만)
        │
        ▼
generate_questions.py
        │
        ├─ load domains.yaml
        ├─ resolve_plan(CISA_MODE)
        │     ├─ type=single → D1~D5 해당 md 1개 + MASTER 발췌
        │     └─ type=cross  → 연계 pair별 D파일 2개씩 + MASTER §4 교차표
        ├─ build_system_instruction()
        ├─ Gemini API
        └─ CISA/output/{MODE}_phase{n}_{count}q_{timestamp}.md
```

### MODE 분기 (`config/domains.yaml`)

| CISA_MODE | type   | 컨텍스트 파일                         | 기본 문항 |
|-----------|--------|--------------------------------------|----------|
| D1        | single | D1_IS감사프로세스.md                  | 2        |
| D2        | single | D2_거버넌스IT관리.md                  | 2        |
| D3        | single | D3_시스템도입개발구현.md              | 1        |
| D4        | single | D4_운영비즈니스복원성.md              | 3        |
| D5        | single | D5_정보자산보호.md                    | 3        |
| CROSS     | cross  | D1~D5 중 pair에 해당하는 파일 (최대 5개) | 2        |

### CROSS pair (MASTER §4)

- D1↔D2, D2↔D5 (고빈도)
- D3↔D4, D4↔D5 (중빈도)
- D1↔D5 (저빈도)

## Actions 사용법

1. Repo **Settings → Secrets → `GEMINI_API_KEY`**
2. **Actions** 탭 → `CISA Generate — D4` 등 선택 → **Run workflow**
3. `phase`: 1=문제만, 2=정답+해설
4. 완료 후 **Artifacts**에서 `CISA/output` 다운로드

## 로컬 테스트

```powershell
$env:GEMINI_API_KEY = "your-key"
$env:CISA_MODE = "D1"
$env:CISA_PHASE = "1"
python CISA/scripts/generate_questions.py
```
