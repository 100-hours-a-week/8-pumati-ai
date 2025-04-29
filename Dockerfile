# Python 3.10 기반 이미지 선택
FROM python:3.10

# 시스템 업데이트 + git 설치
RUN apt-get update && apt-get install -y git

# 작업 폴더 설정
WORKDIR /app

# requirements.txt 복사 후 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# FastAPI 서버 실행 예시 (필요 시 수정)
CMD ["uvicorn", "app.fast_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
