# Apache 로그 모니터링 시스템

실시간으로 Apache 로그를 모니터링하여 의심스러운 활동을 탐지하고 syslog로 알림을 보내는 Python 스크립트입니다.

## 📋 개요

이 프로그램은 Apache 웹 서버의 로그 파일을 실시간으로 모니터링하여 특정 메시지가 포함된 로그 항목을 추적합니다. 동일한 IP 주소에서 설정된 임계값을 초과하는 접속이 발생하면 자동으로 syslog에 경고 메시지를 전송합니다.

## 🚀 주요 기능

- **실시간 로그 모니터링**: Apache 로그 파일을 실시간으로 감시
- **IP 기반 접속 추적**: 각 IP 주소별로 접속 빈도를 추적
- **임계값 기반 알림**: 설정된 시간 내에 임계값을 초과하는 접속 시 자동 알림
- **Syslog 통합**: 시스템 로그와 통합된 알림 시스템
- **자동 정리**: 오래된 기록을 자동으로 정리하여 메모리 효율성 확보
- **날짜별 로그 파일 지원**: 날짜가 바뀌면 새로운 로그 파일로 자동 전환

## 📦 요구사항

- Python 3.x
- Unix/Linux 시스템 (syslog 지원)
- Apache 웹 서버 로그 파일에 대한 읽기 권한

## ⚙️ 설정

스크립트 상단의 설정 섹션에서 다음 매개변수들을 조정할 수 있습니다:

```python
LOG_DIR = "/logs/apache"                    # 로그 디렉토리
LOG_PREFIX = "ssl_www_log-"                 # 로그 파일 접두사
TARGET_MESSAGE = "today_download"           # 감시할 메시지
CHECK_INTERVAL = 1                          # 파일 체크 간격 (초)
TIME_WINDOW = 600                           # 감시 시간 윈도우 (초, 10분)
THRESHOLD_COUNT = 10                        # 임계값 (10회)
CLEANUP_INTERVAL = 300                      # 정리 작업 간격 (초, 5분)
SYSLOG_FACILITY = 'user.error'             # syslog 레벨
SYSLOG_TAG = 'WebAppMonitor'               # syslog 태그
```

### 설정 매개변수 설명

| 매개변수 | 설명 | 기본값 |
|---------|------|--------|
| `LOG_DIR` | 모니터링할 로그 파일이 있는 디렉토리 | `/logs/apache` |
| `LOG_PREFIX` | 로그 파일명 접두사 | `ssl_www_log-` |
| `TARGET_MESSAGE` | 감시할 특정 메시지 | `today_download` |
| `CHECK_INTERVAL` | 로그 파일 체크 간격 (초) | `1` |
| `TIME_WINDOW` | 접속 빈도 계산 시간 윈도우 (초) | `600` (10분) |
| `THRESHOLD_COUNT` | 알림 발생 임계값 | `10` |
| `CLEANUP_INTERVAL` | 메모리 정리 간격 (초) | `300` (5분) |
| `SYSLOG_FACILITY` | Syslog 우선순위 레벨 | `user.error` |
| `SYSLOG_TAG` | Syslog 태그 | `WebAppMonitor` |

## 🔧 설치 및 사용법

### 1. 스크립트 다운로드

```bash
wget https://raw.githubusercontent.com/yourusername/log-monitor/main/log_monitor.py
chmod +x log_monitor.py
```

### 2. 설정 수정

스크립트 내의 설정 섹션을 환경에 맞게 수정합니다:

```python
# 예시: 다른 로그 디렉토리 사용
LOG_DIR = "/var/log/apache2"
LOG_PREFIX = "access_log-"
TARGET_MESSAGE = "suspicious_activity"
```

### 3. 실행

#### 포그라운드 실행
```bash
python3 log_monitor.py
```

#### 백그라운드 실행
```bash
nohup python3 log_monitor.py > /dev/null 2>&1 &
```

#### 시스템 서비스로 실행
systemd 서비스 파일 생성 (`/etc/systemd/system/log-monitor.service`):

```ini
[Unit]
Description=Apache Log Monitor
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /path/to/log_monitor.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

서비스 활성화:
```bash
sudo systemctl daemon-reload
sudo systemctl enable log-monitor.service
sudo systemctl start log-monitor.service
```

## 📊 동작 방식

1. **로그 파일 감시**: 지정된 디렉토리에서 오늘 날짜의 로그 파일을 찾아 모니터링을 시작합니다.

2. **실시간 파싱**: 새로운 로그 라인이 생성될 때마다 즉시 읽어들여 처리합니다.

3. **메시지 필터링**: 로그 라인에서 `TARGET_MESSAGE`가 포함된 항목만 추출합니다.

4. **IP 주소 추출**: 정규표현식을 사용하여 로그 라인에서 IP 주소를 추출합니다.

5. **접속 빈도 추적**: 각 IP 주소별로 접속 시간을 기록하고 시간 윈도우 내의 접속 횟수를 계산합니다.

6. **임계값 검사**: 설정된 시간 윈도우 내에서 임계값을 초과하는 접속이 발생하면 알림을 생성합니다.

7. **알림 전송**: syslog를 통해 시스템 로그에 경고 메시지를 기록합니다.

8. **자동 정리**: 정기적으로 오래된 기록을 삭제하여 메모리 사용량을 관리합니다.

## 📈 로그 형식

이 스크립트는 Apache의 일반적인 로그 형식을 지원합니다:

```
IP주소 - - [타임스탬프] "요청" 상태코드 크기 "리퍼러" "사용자에이전트"
```

예시:
```
192.168.1.100 - - [09/Jul/2025:14:30:25 +0900] "GET /today_download HTTP/1.1" 200 1024 "-" "Mozilla/5.0"
```

## 🔍 알림 예시

임계값을 초과하는 접속이 감지되면 다음과 같은 메시지가 syslog에 기록됩니다:

```
[ERROR] SUSPICIOUS ACTIVITY: IP 192.168.1.100 accessed today_download 15 times in 10 minutes
```

## 🛠️ 문제 해결

### 로그 파일을 찾을 수 없는 경우
```
Waiting for log file: /logs/apache/ssl_www_log-2025-07-09
```
- 로그 디렉토리 경로와 파일명 접두사가 올바른지 확인하세요.
- 파일에 대한 읽기 권한이 있는지 확인하세요.

### syslog 전송 실패
```
Error calling 'logger': [Errno 2] No such file or directory: 'logger'
```
- `logger` 명령이 시스템에 설치되어 있는지 확인하세요.
- 대부분의 Unix/Linux 시스템에서 기본적으로 제공됩니다.

### 메모리 사용량 증가
- `CLEANUP_INTERVAL` 값을 줄여서 더 자주 정리하도록 설정하세요.
- `TIME_WINDOW` 값을 줄여서 더 짧은 시간 윈도우를 사용하세요.

## 🤝 기여하기

1. 이 저장소를 포크하세요
2. 기능 브랜치를 생성하세요 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성하세요

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📧 문의

프로젝트에 대한 질문이나 제안사항이 있으시면 이슈를 생성하거나 이메일로 연락해주세요.

---

**주의**: 이 도구는 보안 모니터링 목적으로 개발되었습니다. 적절한 권한과 법적 고려사항을 확인한 후 사용하세요.
