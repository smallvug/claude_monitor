# Claude Monitor

Windows 시스템 트레이에 **Claude Code 플랜 사용량**을 실시간으로 표시하는 경량 모니터링 도구.

![Python](https://img.shields.io/badge/Python-3.14-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![Version](https://img.shields.io/badge/version-0.1.0-green)

---

## 스크린샷

트레이 아이콘 예시:

| 상태 | 배경색 | 숫자 |
|------|--------|------|
| 여유 (< 50%) | 🟢 초록 | 세션 사용률 |
| 주의 (50~79%) | 🟠 주황 | 세션 사용률 |
| 위험 (≥ 80%) | 🔴 빨강 | 세션 사용률 + 빨간 테두리 |

- **숫자**: 5시간 세션 사용률 (%)
- **배경색**: 7일 주간 사용률 상태
- **마우스 오버**: 세션/주간/Sonnet 상세 수치 + 리셋 시각

---

## 요구사항

- Windows 10/11
- Python 3.x
- Claude Code CLI 설치 및 로그인 상태 (`~/.claude/.credentials.json` 존재)

### 패키지 설치

```bash
pip install requests pystray Pillow pywin32
```

---

## 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/smallvug/claude_monitor.git
cd claude_monitor
```

### 2. 패키지 설치

```bash
pip install requests pystray Pillow pywin32
```

### 3. 실행

```bash
# 콘솔 창 없이 실행 (권장)
pythonw monitor.pyw

# 또는 탐색기에서 monitor.pyw 더블클릭
```

### 4. 시작 프로그램 등록

트레이 아이콘 **우클릭 → "시작 프로그램 등록"** 체크
(레지스트리 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 자동 등록/해제)

---

## 사용법

| 동작 | 설명 |
|------|------|
| 트레이 아이콘 확인 | 현재 세션(5h) 사용률 숫자 + 주간(7d) 상태 배경색 |
| 마우스 오버 | 상세 수치 툴팁 (세션/주간/Sonnet + 리셋 시각) |
| 우클릭 → 지금 갱신 | 즉시 API 호출하여 수치 업데이트 |
| 우클릭 → 시작 프로그램 등록 | 부팅 시 자동 실행 토글 |
| 우클릭 → 종료 | 앱 종료 |

---

## 동작 원리

### 인증

Claude Code CLI가 로그인 시 저장하는 OAuth 토큰을 재사용합니다.

```
~/.claude/.credentials.json
  └── claudeAiOauth.accessToken  ← Bearer 토큰
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
  "five_hour": {
    "utilization": 14.0,
    "resets_at": "2026-03-04T07:00:00Z"
  },
  "seven_day": {
    "utilization": 23.0,
    "resets_at": "2026-03-06T09:00:00Z"
  },
  "seven_day_sonnet": {
    "utilization": 2.0,
    "resets_at": "2026-03-11T02:00:00Z"
  },
  "extra_usage": {
    "is_enabled": false
  }
}
```

> **참고**: `claude.ai` 도메인은 Cloudflare JS 챌린지로 외부 HTTP 클라이언트가 차단됩니다.
> 엔드포인트는 `api.anthropic.com`을 사용합니다.
> 엔드포인트 및 인증 방식은 Claude Code VSCode 확장(`extension.js`)의 소스코드를 역추적하여 확인했습니다.

### 갱신 주기

기본 **1분**. `monitor.pyw` 상단의 `REFRESH_INTERVAL` 값으로 조정:

```python
REFRESH_INTERVAL = 60   # 초 단위
```

---

## 설정

[monitor.pyw](monitor.pyw) 상단의 상수를 수정합니다.

```python
CREDS_PATH       = ...   # credentials.json 경로 (기본: ~/.claude/)
REFRESH_INTERVAL = 60    # 갱신 주기 (초)
```

---

## 아이콘 크기 한계

Windows 시스템 트레이 아이콘은 기본 DPI(100%)에서 **16×16px**으로 고정됩니다.
DPI 스케일링을 높이면 아이콘이 커집니다:

| Windows 배율 | 아이콘 크기 |
|-------------|------------|
| 100% | 16×16 |
| 125% | 20×20 |
| 150% | 24×24 |
| 200% | 32×32 |

앱은 `SM_CXSMICON` API로 실제 크기를 자동 감지하여 2x 오버샘플 후 LANCZOS 다운샘플링합니다.

---

## 로드맵

- [ ] 토큰 만료 시 `refreshToken`으로 자동 갱신
- [ ] 사용률 80% / 95% 도달 시 Windows 토스트 알림
- [ ] 아이콘 더블클릭 시 상세 팝업 창
- [ ] 사용 이력 그래프 (로컬 SQLite)

---

## 라이선스

MIT
