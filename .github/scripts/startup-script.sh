#!/bin/bash

LOGFILE="/var/log/startup-script.log"
log_message() {
  local message="$1"
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] $message" | tee -a $LOGFILE
  logger -t startup-script "$message"
}

log_message "✅ [시작] 스타트업 스크립트 실행 - 호스트명: $(hostname)"

# 보안 값 로드 - 테라폼에서 직접 전달받은 변수 사용
# TUNNEL_UUID와 WEBHOOK_URL은 providers.tf에서 전달

##########################
# 1. NVIDIA 드라이버 설치
##########################
log_message "▶ NVIDIA 드라이버 및 CUDA는 이미 딥러닝 VM 이미지에 설치되어 있음"
# 설치 확인
nvidia-smi
log_message "✅ NVIDIA 드라이버 확인 완료"

#####################################
# 2. 종료 감지 → Discord 알림 전송
#####################################
log_message "▶ 프리엠션 감지 스크립트 설정 중..."
cat <<EOF > /opt/detect-preemption.sh
#!/bin/bash
while true; do
  PREEMPTED=\$(curl -s -f -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/preempted 2>/dev/null)
  if [[ "\$PREEMPTED" == "TRUE" ]]; then
    curl -H "Content-Type: application/json" \
         -X POST \
         -d '{"content": "🚨 GCP 스팟 인스턴스가 중단(preempt)됩니다. 약 30초 내 종료 예정입니다."}' \
         "${secrets.DISCORD_WEBHOOK_URL_JACKY}"
    break
  fi
  sleep 5
done
EOF
chmod +x /opt/detect-preemption.sh
nohup /opt/detect-preemption.sh > /var/log/preempt.log 2>&1 &
log_message "✅ 프리엠션 감지 스크립트 백그라운드 실행 완료"

################################
# 3. cloudflared 설치 및 설정
################################
log_message "▶ cloudflared 설치 시작"
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

log_message "▶ cloudflared 디렉토리 생성 중"
mkdir -p /etc/cloudflared /root/.cloudflared /var/log/cloudflared

log_message "▶ cloudflared 인증 파일 GCS에서 다운로드 중"
gsutil cp gs://ktb8team-static-storage/cloudflare/${secrets.TUNNEL_UUID}.json /etc/cloudflared/llm-tunnel.json
gsutil cp gs://ktb8team-static-storage/cloudflare/cert.pem /root/.cloudflared/cert.pem

log_message "▶ config.yml 설정 파일 생성"
cat <<EOF > /etc/cloudflared/config.yml
tunnel: ${secrets.TUNNEL_UUID}
credentials-file: /etc/cloudflared/llm-tunnel.json

ingress:
  - hostname: ai.mydairy.my
    service: http://localhost:8000
  - service: http_status:404
EOF

log_message "▶ cloudflared systemd 서비스 파일 생성"
cat <<EOF > /etc/systemd/system/cloudflared.service
[Unit]
Description=Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable cloudflared
systemctl start cloudflared
log_message "✅ cloudflared 터널 서비스 시작 완료"

##################################
# 4. Docker 설정 (이미 설치됨)
##################################
log_message "▶ Docker 및 NVIDIA Container Toolkit은 이미 설치되어 있음"
# 설정 확인
docker info | grep -i nvidia
log_message "✅ Docker NVIDIA 설정 확인 완료"

#############################
# 5. Docker 이미지 실행
#############################
log_message "▶ 애플리케이션 디렉토리 생성 중"
mkdir -p /opt/ai-app
cd /opt/ai-app

log_message "▶ GCS에서 이미지 tar 파일 다운로드 중"
gsutil cp gs://ktb8team-static-storage/ai/ai-test.tar /opt/ai-app/
log_message "✅ 다운로드 완료: ai-test.tar"

log_message "▶ Docker 이미지 로드 시도"
docker load < ai-test.tar
IMAGE_NAME=$(docker images --format "{{.Repository}}:{{.Tag}}" | head -n 1)

if [ -n "$IMAGE_NAME" ]; then
  log_message "✅ 이미지 로드 성공: $IMAGE_NAME"
  log_message "▶ 컨테이너 실행 (GPU 할당 포함)"
  docker run -d --gpus all -p 8000:8000 $IMAGE_NAME
  if [ $? -eq 0 ]; then
    log_message "✅ 컨테이너 실행 성공"
  else
    log_message "❌ 컨테이너 실행 실패 - 다른 포트로 재시도"
    docker run -d --gpus all -P $IMAGE_NAME
  fi
else
  log_message "❌ 이미지 로드 실패"
  # Discord로 알림 전송
  curl -H "Content-Type: application/json" \
       -X POST \
       -d '{"content": "🚨 이미지 로드 실패: Docker 이미지를 GCS에서 로드하지 못했습니다. 서버 $(hostname)를 확인해주세요."}' \
       "${secrets.DISCORD_WEBHOOK_URL_JACKY}"
fi

###################################
# 6. 완료 알림 메타데이터 표시
###################################
log_message "✅ [완료] 스타트업 스크립트 실행 종료 - $(hostname)"
curl -X PUT "http://metadata.google.internal/computeMetadata/v1/instance/guest-attributes/startup-script/status" \
  -H "Metadata-Flavor: Google" \
  -d "DONE"
