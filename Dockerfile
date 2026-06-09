# server image: Python 이미지를 사용
FROM python:3.13

# 컨테이너 안에서 사용할 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일을 먼저 복사해서 설치 단계 캐시
COPY backend/requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 앱 코드를 이미지 안으로 복사
COPY backend/app ./app

# 컨테이너 내부에서 앱이 8000번 포트 사용
EXPOSE 8000

# Uvicorn으로 FastAPI 앱을 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
