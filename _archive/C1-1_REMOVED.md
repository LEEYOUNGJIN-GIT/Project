# C1 - 1 아카이브 안내 (2026-06-01)

`eng/C1 - 1/` 디렉터리는 **`eng/C1/` 7파일 정본**의 구버전 사본이었습니다.

- `SYSTEM.md` 단일 참조·v7.4 이전 헤더 등 **정본과 불일치**
- 유지 시 MASTER·KOREAN·파이프라인 참조 혼선 유발

**정본 경로:** GitHub [Project](https://github.com/LEEYOUNGJIN-GIT/Project) **repo 루트** (`MASTER_SYSTEM.md`, `D1~D5`, `KOREAN.md`). 로컬 개발 복사본은 `eng/C1/` 가능.

| 파일 | 역할 |
|------|------|
| MASTER_SYSTEM.md | 문항 생성·해설 규칙 |
| KOREAN.md | 풀이 |
| D1~D5_*.md | ECO 이론 |

GitHub [Project](https://github.com/LEEYOUNGJIN-GIT/Project) 배포 시에도 동일 파일명을 루트 또는 `C1/`에 두고, `CISA` 스크립트 `resolve_materials_dir()` fallback을 사용합니다.
