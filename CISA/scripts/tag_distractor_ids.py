#!/usr/bin/env python3
"""Add '| 권장 **D-N**' to ⚠️ trap lines missing it (additive only)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
C1 = ROOT / "C1"
FILES = [
    "D1_IS감사프로세스.md",
    "D2_거버넌스IT관리.md",
    "D3_시스템도입개발구현.md",
    "D4_운영비즈니스복원성.md",
    "D5_정보자산보호.md",
]

RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Compliance|준수.*=.*통제|인증.*=.*영구|SOC.*=.*감사 완료|SLA 존재|BCP 수립 = BCM|MDM 도입 =|SIEM 도입 =|CASB 도입 =|IaC 도입 =|DevSecOps = 보안팀 불필요|오픈소스 = 무료", re.I), "D-9"),
    (re.compile(r"독립|CAE|CIO|감사위원회|역할|SoD|직무|피감|워킹페이퍼|IT팀이 UAT|포렌식.*IT 보안팀|CSIRT = IT|DBA가 자체|프로그래머가 운영|경영진.*보고|외부 압력|RACI|Accountable", re.I), "D-2"),
    (re.compile(r"시점|FIRST|NEXT|연속감사|연속모니터|사고.*중|근본원인|이관 후|UAT 통과 = Go|DRP 테스트 통과|체크리스트.*DRP|관찰 =|준비.*전", re.I), "D-1"),
    (re.compile(r"범위|중요성.*생략|감사 생략|통제위험.*생략|판단 샘플링|모집단|과잉|환경 차이|파일럿 성공", re.I), "D-3"),
    (re.compile(r"PRIMARY|부수|BCP의 PRIMARY|DRP = BCP|UAT 통과|해시 합계 = 암호", re.I), "D-4B"),
    (re.compile(r"통제 유형|예방.*탐지|심층 방어|물리.*논리|탐지 통제일", re.I), "D-4A"),
    (re.compile(r"기술|구현|패치|암호화 =|VPN|ZTA 도입 자체|최신 기술|ROI만|기술 지표|GAS|데이터 분석 결과만", re.I), "D-5"),
    (re.compile(r"이상|완벽|최선|금지가 최선|전면 중단.*BEST|직접전환.*BEST|Rehost = 클라우드 최적화", re.I), "D-7"),
    (re.compile(r"실무|비ISACA|RPA = AI|Kerberos|TCP/IP|ARP|Bell-LaPadula", re.I), "D-8"),
    (re.compile(r"혼동|= .*=|vs |구분|차이|EDM|IR/CR|BCP|DRP|연속감사 vs|준수성 vs|속성 vs|변량|DevOps vs|ITIL|COBIT|CMMI|Risk Appetite|해시 합계|컨트롤 합계|RAID|증분|차등|Transport|Tunnel|FAR|FRR|CER|RTO|MTPD|WRT|핫 사이트|콜드|미러", re.I), "D-11"),
]


def pick_d_n(line: str) -> str:
    for pat, d in RULES:
        if pat.search(line):
            return d
    return "D-11"


def tag_line(line: str) -> str:
    if "⚠️" not in line or "권장" in line:
        return line
    if "**오답**" not in line and "→ **오답**" not in line and "CONCERN" not in line:
        return line
    d = pick_d_n(line)
    suffix = f" | 권장 **{d}**"
    line = line.rstrip("\n")
    if line.endswith(")"):
        return line + suffix + "\n"
    return line + suffix + "\n"


def process(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    n = 0
    for line in lines:
        new = tag_line(line)
        if new != line:
            n += 1
        out.append(new)
    if n:
        path.write_text("".join(out), encoding="utf-8")
    return n


def main() -> None:
    total = 0
    for name in FILES:
        p = C1 / name
        c = process(p)
        print(f"{name}: +{c} tags")
        total += c
    print(f"total: {total}")


if __name__ == "__main__":
    main()
