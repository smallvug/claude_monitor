# Claude Monitor

Windows 시스템 트레이에 **Claude Code 플랜 사용량**을 실시간으로 표시하는 경량 모니터링 도구.

![Python](https://img.shields.io/badge/Python-3.14-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![Version](https://img.shields.io/badge/version-0.1.8-green)

---

## 트레이 아이콘

| 상태 | 배경색 | 숫자 |
|------|--------|------|
| 여유 (< 50%) | 🟢 초록 | 세션 사용률 |
| 주의 (50~79%) | 🟠 주황 | 세션 사용률 |
| 위험 (≥ 80%) | 🔴 빨강 | 세션 사용률 + 빨간 테두리 |
| 극위험 (≥ 95%) | 🔴 깜빡임 | 0.5초 간격 점멸 |

- **숫자**: 5시간 세션 사용률 (%)
- **배경색**: 7일 주간 사용률 상태
- **마우스 오버**: 세션/주간/Sonnet 상세 수치 + 리셋 시각

---

## 요구사항

- Windows 10/11
- Python 3.x
- Claude Code CLI 설치 및 로그인 상태 (`~/.claude/.credentials.json` 존재)

```bash
pip install requests pystray Pillow pywin32
```

---

## 설치 및 실행

```bash
git clone https://github.com/smallvug/claude_monitor.git
cd claude_monitor
```

탐색기에서 **`run.bat`** 더블클릭 — venv 생성 및 패키지 설치를 자동으로 처리합니다.

> **다중 PC / Dropbox 환경**: `.venv`는 PC마다 경로가 달라 공유되지 않습니다. 각 PC에서 `run.bat`을 한 번씩 실행하면 자동으로 설정됩니다.

---

## 사용법

| 동작 | 설명 |
|------|------|
| 트레이 아이콘 확인 | 세션(5h) % 숫자 + 주간(7d) 배경색 |
| 마우스 오버 | 세션/주간/Sonnet 수치 + 리셋 시각 툴팁 |
| **더블클릭** | 상세 팝업 창 (프로그레스 바 + 리셋 타이머) |
| 우클릭 → 상세 보기 | 상세 팝업 창 열기 |
| 우클릭 → 지금 갱신 | 즉시 API 호출하여 수치 업데이트 |
| 우클릭 → 갱신 주기 | 1분 / 5분 / 10분 선택 |
| 우클릭 → 시작 프로그램 등록 | 부팅 시 자동 실행 토글 |
| 우클릭 → 종료 | 앱 종료 |

### Windows 알림

| 임계값 | 알림 |
|--------|------|
| 80% 도달 | 주의 풍선 알림 |
| 95% 도달 | 위험 풍선 알림 + 아이콘 깜빡임 |

임계값을 넘을 때 **한 번만** 알림. 수치가 낮아졌다가 다시 올라오면 재알림.

---

## 동작 원리

### 인증

Claude Code CLI가 로그인 시 저장하는 OAuth 토큰을 재사용합니다.

```
~/.claude/.credentials.json
  └── claudeAiOauth.accessToken  ← Bearer 토큰 (만료 시 refreshToken으로 자동 갱신)
```

### API

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer <token>
anthropic-beta: oauth-2025-04-20
```

### 응답 구조

```json
{
  "five_hour":       {"utilization": 14.0, "resets_at": "2026-03-04T07:00:00Z"},
  "seven_day":       {"utilization": 23.0, "resets_at": "2026-03-06T09:00:00Z"},
  "seven_day_sonnet":{"utilization":  2.0, "resets_at": "2026-03-11T02:00:00Z"},
  "extra_usage":     {"is_enabled": false}
}
```

> `claude.ai` 도메인은 Cloudflare JS 챌린지로 차단 → `api.anthropic.com` 사용.
> 엔드포인트/인증 방식은 Claude Code VSCode 확장(`extension.js`) 역추적으로 확인.

### 갱신 주기

기본 **5분**. 우클릭 → 갱신 주기에서 1분/5분/10분 선택 가능.

---

## 아이콘 크기

Windows 시스템 트레이 아이콘은 DPI에 따라 크기가 달라집니다:

| Windows 배율 | 아이콘 크기 |
|-------------|------------|
| 100% | 16×16 |
| 125% | 20×20 |
| 150% | 24×24 |
| 200% | 32×32 |

`SM_CXSMICON` API로 실제 크기를 자동 감지하여 2x 오버샘플 후 LANCZOS 다운샘플링합니다.

---

## 로드맵

- [x] 토큰 만료 시 `refreshToken`으로 자동 갱신
- [x] 사용률 80%/95% 도달 시 Windows 풍선 알림
- [x] 아이콘 더블클릭 시 상세 팝업 창
- [x] 갱신 주기 메뉴 (30초/1분/5분)
- [x] 95% 이상 시 아이콘 깜빡임
- [x] 429 Too Many Requests 처리 (Retry-After 대기, 최소 60초)
- [x] 중복 실행 방지 (Windows 명명된 뮤텍스)
- [x] 기본 갱신 주기 5분으로 조정 (다중 PC 환경 대응)
- [x] run.bat 런처: venv 자동 생성/복구 (Dropbox 다중 PC 대응)
- [ ] 팝업 자동 갱신 (열어 둔 상태에서 수치 업데이트)
- [ ] 오류 상태 아이콘 (API 실패 시 회색 `?`)
- [ ] 사용 이력 그래프 (로컬 SQLite)

---

## 라이선스

MIT
