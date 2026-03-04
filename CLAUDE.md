# Claude Monitor

## 프로젝트 개요

Windows 시스템 트레이에 Claude Code 플랜 사용량을 실시간으로 표시하는 모니터링 도구.

> **버전업 규칙**: "버전업" 요청 시 CLAUDE.md와 README.md를 모두 최신 상태로 업데이트한 후 커밋·푸시한다. CLAUDE.md는 사용자가 명시적으로 요청할 때만 업데이트한다 (버전업 제외).

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

### 3. 토큰 자동 갱신 구현 (v0.1.2)
- `REFRESH_URL`: `claude.ai/oauth/token` → `platform.claude.com/v1/oauth/token` (올바른 엔드포인트)
- `CLIENT_ID`, `OAUTH_SCOPE` 상수 추가 (extension.js 역추적)
- `get_token()` 응답 키 매핑 수정: `access_token`/`refresh_token`/`expires_in` → credentials.json 형식

### 토큰 갱신 상세
- **URL**: `https://platform.claude.com/v1/oauth/token`
- **CLIENT_ID**: `9d1c250a-e61b-44d9-88ed-5944d1962f5e`
- **scope**: `user:profile user:inference user:sessions:claude_code user:mcp_servers`
- **payload**: `{grant_type, refresh_token, client_id, scope}`
- **응답**: `{access_token, refresh_token, expires_in, scope}`

### 4. 더블클릭 상세 팝업 (v0.1.3)
- `show_popup()`: tkinter 다크 테마 팝업 (별도 스레드)
- 세션/주간/Sonnet 사용률 프로그레스 바 + 리셋 타이머
- 트레이 더블클릭 또는 우클릭 → "상세 보기"
- `_popup_open[False]` 플래그로 중복 열림 방지

### 5. 갱신 주기 메뉴 (v0.1.4)
- 우클릭 → "갱신 주기" 서브메뉴: 30초 / 1분 / 5분
- `_refresh_interval = [60]` 뮤터블 리스트로 런타임 변경
- 라디오 체크로 현재 선택 표시

### 6. 토스트 알림 + 아이콘 깜빡임 (v0.1.5)
- `show_toast()`: PowerShell 풍선 알림 (추가 패키지 없음)
- `check_alerts()`: 80% → 주의, 95% → 위험 알림 (임계값 재진입 시만, 낮아지면 리셋)
- `blink_loop()`: 95% 이상 시 0.5초 간격 dim/bright 교번
- `make_icon(dim=True)`: 깜빡임용 어두운 버전

## 다음 단계

1. **시작 시 알림 억제**: 앱 시작 직후 이미 80%+여도 알림 안 뜨게
2. **팝업 자동 갱신**: 열어 둔 팝업이 주기적으로 수치 갱신
3. **오류 상태 아이콘**: API 실패 시 회색 `?` 아이콘
