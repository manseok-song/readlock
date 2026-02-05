# Video-to-Text 자막 자동화 시스템
# Google Cloud Run 배포용 Dockerfile (fast 모드)

FROM python:3.11-slim

# FFmpeg 및 Node.js 설치 (yt-dlp 필요)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사 및 패키지 설치
COPY src/ ./src/
COPY pyproject.toml .

# 패키지 설치 (모듈 인식을 위해)
RUN pip install --no-cache-dir -e .

# Streamlit 추가 설치 (dashboard용) + gdown (Google Drive 다운로드)
RUN pip install --no-cache-dir streamlit plotly yt-dlp gdown google-cloud-storage

# Python 출력 버퍼링 비활성화 (로그 실시간 출력)
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080

# Streamlit 대시보드 실행 (업로드 크기 제한 증가: 2GB)
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true", "--server.maxUploadSize=2000", "--server.maxMessageSize=2000"]
