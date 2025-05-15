# 서비스 계정 생성 방법(아티팩트 레지스트리 푸시용)
## 반드시 해당 아티팩트 레지스트리
gcloud auth login

# 프로젝트 설정. 까먹지마라. 마지막은 프로젝트 아이디임!!!
gcloud config set project ktb8team-458916

### 서비스 계정 생성
# 서비스 계정 이름은 'github-actions-pusher'를 사용합니다.
# 서비스 계정 이메일은 'github-actions-pusher@ktb8team.iam.gserviceaccount.com' 형식이 됩니다.
gcloud iam service-accounts create github-actions-pusher \
    --description="Service account for GitHub Actions to push images to Artifact Registry in ktb8team project" \
    --display-name="GitHub Actions Artifact Pusher for ktb8team" \
    --project=ktb8team-458916

### 권한 부여
# 위에서 생성한 서비스 계정(github-actions-pusher@ktb8team.iam.gserviceaccount.com)에
# 'ktb8team' 프로젝트의 Artifact Registry에 대한 쓰기 권한을 부여합니다.
gcloud projects add-iam-policy-binding ktb8team-458916 \
    --member="serviceAccount:github-actions-pusher@ktb8team-458916.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"
// ... 기존 코드 ...

# 커밋 메시지에 [cpu]가 포함된 경우에만 실행
 - cpu 에서 작동하는 기능은 커밋 시 메세지 안의 어디든 [cpu] 키워드가 포함되어야 함