#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import re
from datetime import datetime
from collections import defaultdict

# --- 설정 ---
LOG_DIR = "/logs/apache"                    # 1. 로그 디렉토리
LOG_PREFIX = "ssl_www_log-"                 # 2. 로그 파일 접두사
TARGET_MESSAGE = "today_download"           # 3. 감시할 메시지
CHECK_INTERVAL = 1                          # 4. 파일 체크 간격 (초)
TIME_WINDOW = 600                           # 5. 감시 시간 윈도우 (초, 10분)
THRESHOLD_COUNT = 10                        # 6. 임계값 (10회)
CLEANUP_INTERVAL = 300                      # 7. 정리 작업 간격 (초, 5분)
SYSLOG_FACILITY = 'user.error'             # 8. syslog 레벨
SYSLOG_TAG = 'WebAppMonitor'               # 9. syslog 태그
IP_REGEX = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # 10. IP 주소 추출 정규식

def extract_ip_from_log(log_line):
    """로그 라인에서 IP 주소를 추출합니다."""
    # Apache 일반적인 로그 형식: IP - - [timestamp] ...
    match = re.match(IP_REGEX, log_line)
    return match.group(1) if match else None

def cleanup_old_records(ip_access_times, current_time):
    """10분 이전의 기록들을 정리합니다."""
    cutoff_time = current_time - TIME_WINDOW
    for ip in list(ip_access_times.keys()):
        ip_access_times[ip] = [t for t in ip_access_times[ip] if t > cutoff_time]
        if not ip_access_times[ip]:
            del ip_access_times[ip]

def get_today_log_file():
    """오늘 날짜의 로그 파일 경로를 반환합니다."""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"{LOG_PREFIX}{today}")

def log_to_syslog(message):
    """지정된 메시지를 syslog에 ERROR 레벨로 기록합니다."""
    print(f"ALERT: {message}", file=sys.stderr)
    try:
        subprocess.run(['logger', '-p', SYSLOG_FACILITY, '-t', SYSLOG_TAG, message], check=True)
    except Exception as e:
        print(f"Error calling 'logger': {e}", file=sys.stderr)

def monitor_log_file():
    """로그 파일을 실시간으로 모니터링합니다."""
    current_log_file = None
    file_handle = None
    ip_access_times = defaultdict(list)  # IP별 접속 시간 기록
    alerted_ips = {}  # IP별 마지막 알림 시간 기록
    last_cleanup_time = 0  # 마지막 정리 시간
    
    try:
        while True:
            today_log_file = get_today_log_file()
            
            # 날짜가 바뀌어 새 로그 파일이 생성된 경우
            if current_log_file != today_log_file:
                if file_handle:
                    file_handle.close()
                
                current_log_file = today_log_file
                # 날짜가 바뀌면 기록 초기화
                ip_access_times.clear()
                alerted_ips.clear()
                
                # 새 로그 파일이 존재할 때까지 대기
                while not os.path.exists(current_log_file):
                    print(f"Waiting for log file: {current_log_file}", file=sys.stderr)
                    time.sleep(CHECK_INTERVAL)
                
                try:
                    file_handle = open(current_log_file, 'r')
                    file_handle.seek(0, 2)  # 파일 끝으로 이동
                    print(f"Monitoring started: {current_log_file}", file=sys.stderr)
                except IOError as e:
                    print(f"Error opening log file {current_log_file}: {e}", file=sys.stderr)
                    time.sleep(CHECK_INTERVAL)
                    continue
            
            # 새로운 로그 라인 읽기
            if file_handle:
                line = file_handle.readline()
                if line:
                    line = line.strip()
                    if TARGET_MESSAGE in line:
                        current_time = time.time()
                        
                        # IP 주소 추출
                        ip_address = extract_ip_from_log(line)
                        if ip_address:
                            # 현재 시간을 기록
                            ip_access_times[ip_address].append(current_time)
                            
                            # 정리 작업 (설정된 간격마다)
                            if current_time - last_cleanup_time >= CLEANUP_INTERVAL:
                                cleanup_old_records(ip_access_times, current_time)
                                # 10분 이전에 알림을 보낸 IP들만 정리
                                cutoff_time = current_time - TIME_WINDOW
                                alerted_ips = {ip: alert_time for ip, alert_time in alerted_ips.items() 
                                             if alert_time > cutoff_time}
                                last_cleanup_time = current_time
                            
                            # 시간 윈도우 내 접속 횟수 확인
                            recent_accesses = [t for t in ip_access_times[ip_address] 
                                             if t > current_time - TIME_WINDOW]
                            
                            # 임계값 초과하고 마지막 알림으로부터 시간 윈도우가 지난 경우
                            last_alert_time = alerted_ips.get(ip_address, 0)
                            if len(recent_accesses) >= THRESHOLD_COUNT and (current_time - last_alert_time) >= TIME_WINDOW:
                                log_message = f"[ERROR] SUSPICIOUS ACTIVITY: IP {ip_address} accessed {TARGET_MESSAGE} {len(recent_accesses)} times in {TIME_WINDOW//60} minutes"
                                log_to_syslog(log_message)
                                alerted_ips[ip_address] = current_time
                else:
                    # 새 라인이 없으면 잠시 대기
                    time.sleep(CHECK_INTERVAL)
            else:
                time.sleep(CHECK_INTERVAL)
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped.", file=sys.stderr)
        if file_handle:
            file_handle.close()
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if file_handle:
            file_handle.close()
        sys.exit(1)

if __name__ == "__main__":
    monitor_log_file()
