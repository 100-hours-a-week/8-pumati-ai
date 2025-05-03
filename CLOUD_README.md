# 도커 이미지 빌드 및 배포 가이드

## cicd를 위해 레포에 추가해야 할 secrets
- GCP_SA_KEY : 구글 클라우드 서비스 계정 키

기본적으로 IAM -> 서비스 계정 들어가면 컴퓨트 엔진 서비스 계정이 있는데, 이 계정을 사용하면 된다. 이걸 레포 시크릿에 추가

GCP_SA_KEY 생성 및 확인하기
서비스 계정 키 생성 과정:
GCP 콘솔 접속: https://console.cloud.google.com/
왼쪽 메뉴에서 "IAM 및 관리" → "서비스 계정" 선택
기존 서비스 계정 사용 또는 "서비스 계정 만들기" 버튼 클릭
새 서비스 계정 생성 시 이름 입력 (예: "github-actions")
역할 부여: "Storage 관리자", "Container Registry 서비스 에이전트"
서비스 계정 목록에서 해당 계정 선택 → "키" 탭 → "키 추가" → "새 키 만들기"
"JSON" 키 유형 선택 → "만들기"
JSON 파일이 자동으로 다운로드됨
GitHub 시크릿에 추가:
JSON 파일 내용 전체를 복사 (파일 열어서 내용 전체 선택)
GitHub 저장소 → "Settings" 탭
왼쪽 메뉴 "Security" 섹션에서 "Secrets and variables" → "Actions" 선택
"New repository secret" 버튼 클릭
Name: GCP_SA_KEY
Value: JSON 파일 내용 전체 붙여넣기
"Add secret" 버튼 클릭

## 테스트 시 맥북에서 빌드하면 arm/amd 문제 발생하므로, 소스코드를 직접 올려서 빌드하는 법

# 소스 코드를 압축
# tar 명령어로 현재 디렉토리 모든 파일 압축
tar -czvf source.tar.gz .

# 또는 특정 파일/디렉토리 제외하고 압축
tar -czvf source.tar.gz --exclude='node_modules' --exclude='.git' --exclude='source.tar.gz' .

# GCS에 업로드
gsutil cp source.tar.gz gs://ktb8team-static-storage/test/source.tar.gz

# GCP 인스턴스에 SSH 접속 후 실행할 명령어:
gsutil cp gs://ktb8team-static-storage/test/source.tar.gz .
mkdir project && cd project
tar -xzf ../source.tar.gz
docker build -t test-ai .
docker tag test-ai gcr.io/ktb8team/test-ai:latest
docker push gcr.io/ktb8team/test-ai:latest

# 향후 L4 인스턴스에서 실행할 명령어
docker pull gcr.io/ktb8team/test-ai:latest
docker run --gpus all -p 8000:8000 gcr.io/ktb8team/test-ai:latest