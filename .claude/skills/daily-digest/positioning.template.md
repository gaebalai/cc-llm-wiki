# positioning.md 템플릿

`vault/positioning.md` 로 복사한 뒤 본인 환경에 맞게 채우세요.
**사용자가 직접 작성** — LLM 이 자동 수정하지 않습니다 (CLAUDE.md §3-⑤ 의 self 정신과 같음).

```bash
cp .claude/skills/daily-digest/positioning.template.md vault/positioning.md
$EDITOR vault/positioning.md
```

---

```markdown
---
type: positioning
locale: ko
updated_at: 2026-05-18T00:00:00+09:00
---

# positioning — daily-digest 의 의도 헌법

## interests (관심사)

키워드·토픽 5~15 개. daily-digest 가 매일 검색 쿼리로 변환.

- LLM agent infrastructure
- knowledge graph / GraphRAG
- Obsidian + Claude Code workflow
- Anthropic Context Engineering
- personal knowledge management 운영 사례
- (필요한 만큼 추가)

## avoid (피할 토픽)

명시적 부정형 키워드. WebSearch 에 `-keyword` 로 적용.

- 가격 비교·세일 정보
- 정치·연예
- (필요한 만큼 추가)

## trusted_sources (신뢰 도메인)

가중치 ↑ 받는 출처 도메인.

- anthropic.com
- docs.anthropic.com
- arxiv.org
- github.com/karpathy
- github.com/microsoft/graphrag
- 본인 신뢰하는 한국 블로거·뉴스레터

## avoid_sources (피할 도메인)

content farm·광고 사이트 등.

- example-spam.com

## tone (digest 본문 톤)

- 한국어 (영어 출처도 한국어로 요약)
- 1 출처당 2~3 문장
- "왜 흥미로운가" 한 줄 포함

## frequency_hint

- 매일 5 건 (기본)
- 주말은 3 건으로 줄임 (옵션)
- 같은 토픽 3 일 연속이면 다른 토픽 강제 전환

## 회고 슬롯

운영하면서 positioning 자체가 어떻게 진화하는지 timestamp 와 함께 append.

- 2026-XX-XX — interests 에서 'GraphRAG' 빼고 'agent memory' 추가 (이미 충분히 ingest)
```

---

## 운영 메모

- positioning.md 는 `self/` 가 아니지만 외부 발신 금지 폴더 정신은 유지 — LLM 이 인용해 외부 출력에 노출하지 않음
- 주 1 회 weekly-review 슬롯에 positioning 한 줄 검토 권장
- daily-digest 가 매번 본 파일을 통째 읽으니 너무 길어지지 않도록 (≤ 50 줄 권장)
