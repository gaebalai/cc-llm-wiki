# SCHEMA — 사서 규율

이 파일은 **사람이 직접 정의**한 규율이다. LLM은 **읽기만** 한다(절대 자동 수정 금지).
모든 Skill·Hook는 이 SCHEMA를 기준으로 검증한다.

---

## 1. 페이지 타입 (4종)

| type | 폴더 | 누가 만드는가 | 외부 발행 가능? |
|---|---|---|---|
| `topic` | `02_wiki/topics/` | compile Skill (사람 승인) | 가능 |
| `decision` | `02_wiki/decisions/` | 사람 (append only) | 가능(조건부) |
| `self` | `02_wiki/self/` | 사람 (LLM은 읽기만) | **불가** |
| `digest` | `02_wiki/digests/` | daily-digest routine | 가능 |

---

## 2. Frontmatter 필수 키

```yaml
---
id: <ISO8601-timestamp>-<kebab-slug>   # 불변, 4층 공유 키
type: topic | decision | self | digest # enum 외 값은 lint 실패
status: draft | reviewed | published   # status 게이트
locale: ko | en | ja                   # 기본 ko, publish가 파생 생성
sources: [<vault/01_raw/...>]          # 출처 명시 (없으면 lint 실패)
related: ["[[other-slug]]"]            # wikilink 배열
updated_at: <ISO8601 with TZ>
graph_synced_at: null | <ISO8601>      # graph-sync 성공 시 갱신
---
```

---

## 3. 명명 규칙

- 파일명: `YYYY-MM-DD-<kebab-slug>.md`. slug는 영문 소문자·숫자·하이픈만(반각공백·콜론·슬래시 금지)
- wikilink: `[[<exact-slug-without-extension>]]`. 띄어쓰기·대문자·이모지 금지
- raw 파일도 동일 규칙: `vault/01_raw/<genre>/YYYY-MM-DD-<slug>.md`

---

## 4. 사서로서의 행동 규율 (LLM 준수)

1. **출처 명시**: 모든 topic·digest는 frontmatter `sources`에 raw 경로 1개 이상
2. **링크 강제**: 본문에서 다른 wiki를 언급하면 반드시 `[[...]]`로 연결
3. **원본 재확인**: 기존 페이지 갱신 시 `sources`의 raw를 다시 읽고 모순 검사
4. **자기 검열**: self/ 내용을 어떤 출력(graph·publish·digest·query 응답)에도 포함 금지
5. **반증 우선**: 모순 발견 시 기존 페이지를 덮어쓰지 말고 `CONTRADICTS` 메모 추가 → 사람에게 토론 요청
6. **메타 데이터 보존**: `id`·`updated_at` 갱신은 compile Skill만 수행. 사람 수정 시 `updated_at` 직접 변경

---

## 5. lint 규칙 (P2부터 본격 적용)

- enum 위반(`type`·`status`·`locale`) → 에러
- `sources` 빈 배열 → 에러 (topic/digest)
- wikilink 끊김(존재하지 않는 slug 참조) → 에러
- 고립 페이지(아무도 링크하지 않음) → 경고
- stale 페이지(`updated_at`이 90일 이상 + sources의 raw가 갱신됨) → 경고
- 슬러그에 반각 공백·대문자·이모지 → 에러
- duplicate `id` → 에러 (4층 공유 키 충돌)

---

## 6. SCHEMA 변경 절차

- 본 파일 변경은 **사람만** 수행
- 변경 PR에는 영향받는 Skill 목록을 본문에 명시
- 변경 후 즉시 `/lint` 1회 실행해 기존 페이지 위반 여부 확인
