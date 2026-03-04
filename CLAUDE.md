# Claude Monitor

## 프로젝트 개요

Windows 시스템 트레이에 Claude Code 플랜 사용량을 실시간으로 표시하는 모니터링 도구.

> **CLAUDE.md 업데이트 규칙**: 이 파일은 사용자가 명시적으로 요청할 때만 업데이트한다. 작업 완료 후 자동으로 업데이트하지 않는다. 단, git 푸시 전에는 반드시 CLAUDE.md를 최신 상태로 업데이트한다.

- **환경**: Python 3.14, Windows 10
- **주요 라이브러리**: requests, pystray, Pillow, pywin32
- **Python 경로**: `C:\Users\smallvug\AppData\Local\Programs\Python\Python314\`
- **실행**: `pythonw.exe monitor.pyw` (콘솔 창 없음)

## 핵심 구조

### API
- **엔드포인트**: `https://api.anthropic.com/api/oauth/usage`
- **인증**: `Authorization: Bearer <token>` + `anthropic-beta: oauth-2025-04-20`
- **토큰 위치**: `~/.claude/.credentials.json` → `claudeAiOauth.accessToken`
- **주의**: `claude.ai` 도메인은 Cloudflare JS 챌린지로 차단됨 → `api.anthropic.com` 사용

### 사용량 데이터 구조
```json
{
  "five_hour":  {"utilization": 14.0, "resets_at": "..."},
  "seven_day":  {"utilization": 23.0, "resets_at": "..."},
  "seven_day_sonnet": {"utilization": 2.0, "resets_at": "..."},
  "extra_usage": {"is_enabled": false, ...}
}
```

### 아이콘 설계
- Windows 트레이 아이콘 크기: `SM_CXSMICON` (일반적으로 16px at 96 DPI)
- `ICON_SIZE = 실제크기 × 2` 로 2x 오버샘플 후 LANCZOS 다운샘플
- 배경색 = 주간(7d) 상태 (초록/주황/빨강), 숫자 = 세션(5h) 사용률

## 진행 상황

### 1. 초기 구현 (v0.1.0)
- `api.anthropic.com/api/oauth/usage` 엔드포인트 탐색 및 인증 방식 확인
  - Claude Code VSCode 확장(`extension.js`) 소스에서 엔드포인트 및 `anthropic-beta` 헤더 역추적
- 5분 주기 사용량 자동 갱신
- 트레이 우클릭 메뉴: 지금 갱신 / 시작 프로그램 등록 / 종료
- 시작 프로그램 등록: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 레지스트리
- 아이콘: 세션(5h) 숫자 전체 크기 + 배경색 = 주간(7d) 신호등
- 툴팁: 세션/주간/Sonnet 사용률 + 리셋 시각 + 마지막 갱신 시각

### 2. 갱신 주기 조정 (v0.1.1)
- `REFRESH_INTERVAL` 5분 → 1분으로 단축

## 다음 단계

1. **토큰 자동 갱신**: `refreshToken`으로 만료된 `accessToken` 갱신 로직 완성
2. **알림**: 사용률 임계값(80%, 95%) 도달 시 Windows 토스트 알림
3. **더블클릭**: 아이콘 더블클릭 시 상세 팝업 창
