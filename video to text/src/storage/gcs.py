"""Google Cloud Storage 헬퍼 모듈"""

import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import google.auth
from google.auth import compute_engine
from google.auth.transport import requests
from google.cloud import storage
from google.cloud.exceptions import NotFound


# 버킷 이름 설정
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "video-to-text-uploads-causal-binder")


class GCSHelper:
    """Google Cloud Storage 헬퍼 클래스"""

    def __init__(self, bucket_name: str = GCS_BUCKET_NAME):
        self.bucket_name = bucket_name
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[storage.Bucket] = None
        self._service_account_email: Optional[str] = None

    @property
    def client(self) -> storage.Client:
        """GCS 클라이언트 (lazy initialization)"""
        if self._client is None:
            self._client = storage.Client()
        return self._client

    @property
    def bucket(self) -> storage.Bucket:
        """GCS 버킷 (lazy initialization)"""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    @property
    def service_account_email(self) -> Optional[str]:
        """Cloud Run 서비스 계정 이메일 가져오기"""
        if self._service_account_email is None:
            try:
                # Google Cloud 환경에서 서비스 계정 이메일 가져오기
                credentials, project = google.auth.default()
                if hasattr(credentials, 'service_account_email'):
                    self._service_account_email = credentials.service_account_email
                else:
                    # Compute Engine 환경에서 메타데이터 서버 사용
                    auth_req = requests.Request()
                    credentials.refresh(auth_req)
                    if hasattr(credentials, 'service_account_email'):
                        self._service_account_email = credentials.service_account_email
            except Exception as e:
                print(f"[GCS] 서비스 계정 이메일 가져오기 실패: {e}")
        return self._service_account_email

    def upload_file(
        self,
        file_path: str | Path,
        destination_blob_name: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        파일을 GCS에 업로드

        Args:
            file_path: 업로드할 로컬 파일 경로
            destination_blob_name: GCS 내 저장될 이름 (None이면 자동 생성)
            content_type: 파일 MIME 타입 (None이면 자동 감지)

        Returns:
            Tuple[gs_uri, public_url]: GCS URI와 공개 URL
        """
        file_path = Path(file_path)

        if destination_blob_name is None:
            # 고유한 파일명 생성: timestamp_uuid_filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            destination_blob_name = f"{timestamp}_{unique_id}_{file_path.name}"

        blob = self.bucket.blob(destination_blob_name)

        # MIME 타입 자동 감지
        if content_type is None:
            extension = file_path.suffix.lower()
            content_types = {
                ".mp4": "video/mp4",
                ".mkv": "video/x-matroska",
                ".avi": "video/x-msvideo",
                ".mov": "video/quicktime",
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".flac": "audio/flac",
                ".ogg": "audio/ogg",
            }
            content_type = content_types.get(extension, "application/octet-stream")

        blob.upload_from_filename(str(file_path), content_type=content_type)

        gs_uri = f"gs://{self.bucket_name}/{destination_blob_name}"
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"

        return gs_uri, public_url

    def upload_from_string(
        self,
        data: bytes,
        destination_blob_name: str,
        content_type: str = "application/octet-stream"
    ) -> Tuple[str, str]:
        """
        바이트 데이터를 GCS에 업로드

        Args:
            data: 업로드할 바이트 데이터
            destination_blob_name: GCS 내 저장될 이름
            content_type: 파일 MIME 타입

        Returns:
            Tuple[gs_uri, public_url]: GCS URI와 공개 URL
        """
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(data, content_type=content_type)

        gs_uri = f"gs://{self.bucket_name}/{destination_blob_name}"
        public_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"

        return gs_uri, public_url

    def generate_signed_url(
        self,
        blob_name: str,
        expiration_hours: int = 24
    ) -> str:
        """
        서명된 다운로드 URL 생성 (시간 제한 접근)

        Cloud Run에서는 IAM 기반 서명을 사용합니다.

        Args:
            blob_name: 블롭 이름
            expiration_hours: URL 만료 시간 (시간 단위)

        Returns:
            서명된 URL
        """
        blob = self.bucket.blob(blob_name)

        # Cloud Run/Compute Engine 환경에서 IAM 서명 사용
        sa_email = self.service_account_email

        if sa_email:
            # IAM 기반 서명 (Cloud Run용)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET",
                service_account_email=sa_email,
                access_token=self._get_access_token(),
            )
        else:
            # 로컬 환경 (서비스 계정 키 사용)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
        return url

    def generate_upload_signed_url(
        self,
        blob_name: str,
        content_type: str = "application/octet-stream",
        expiration_minutes: int = 60
    ) -> dict:
        """
        서명된 업로드 URL 생성 (클라이언트 직접 업로드용)

        Cloud Run에서는 IAM 기반 서명을 사용합니다.

        Args:
            blob_name: 저장될 블롭 이름
            content_type: 파일 MIME 타입
            expiration_minutes: URL 만료 시간 (분 단위)

        Returns:
            dict: {upload_url, gs_uri, blob_name}
        """
        blob = self.bucket.blob(blob_name)

        # Cloud Run/Compute Engine 환경에서 IAM 서명 사용
        sa_email = self.service_account_email

        if sa_email:
            # IAM 기반 서명 (Cloud Run용)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="PUT",
                content_type=content_type,
                service_account_email=sa_email,
                access_token=self._get_access_token(),
            )
        else:
            # 로컬 환경 (서비스 계정 키 사용)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="PUT",
                content_type=content_type,
            )

        return {
            "upload_url": url,
            "gs_uri": f"gs://{self.bucket_name}/{blob_name}",
            "blob_name": blob_name,
            "content_type": content_type,
        }

    def _get_access_token(self) -> Optional[str]:
        """현재 자격증명의 액세스 토큰 가져오기"""
        try:
            credentials, _ = google.auth.default()
            auth_req = requests.Request()
            credentials.refresh(auth_req)
            return credentials.token
        except Exception as e:
            print(f"[GCS] 액세스 토큰 가져오기 실패: {e}")
            return None

    def download_file(
        self,
        blob_name: str,
        destination_path: str | Path
    ) -> Path:
        """
        GCS에서 파일 다운로드

        Args:
            blob_name: 블롭 이름
            destination_path: 다운로드할 로컬 경로

        Returns:
            다운로드된 파일 경로
        """
        destination_path = Path(destination_path)
        blob = self.bucket.blob(blob_name)
        blob.download_to_filename(str(destination_path))
        return destination_path

    def delete_file(self, blob_name: str) -> bool:
        """
        GCS에서 파일 삭제

        Args:
            blob_name: 블롭 이름

        Returns:
            삭제 성공 여부
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except NotFound:
            return False

    def file_exists(self, blob_name: str) -> bool:
        """
        파일 존재 여부 확인

        Args:
            blob_name: 블롭 이름

        Returns:
            존재 여부
        """
        blob = self.bucket.blob(blob_name)
        return blob.exists()

    def get_blob_name_from_url(self, url: str) -> Optional[str]:
        """
        URL에서 블롭 이름 추출

        Args:
            url: GCS URL (gs:// 또는 https://storage.googleapis.com/...)

        Returns:
            블롭 이름 또는 None
        """
        if url.startswith(f"gs://{self.bucket_name}/"):
            return url[len(f"gs://{self.bucket_name}/"):]
        elif url.startswith(f"https://storage.googleapis.com/{self.bucket_name}/"):
            return url[len(f"https://storage.googleapis.com/{self.bucket_name}/"):]
        return None

    def list_files(self, prefix: str = "") -> list[dict]:
        """
        버킷의 파일 목록 조회

        Args:
            prefix: 필터링할 접두사

        Returns:
            파일 정보 목록
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [
            {
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created,
                "updated": blob.updated,
                "content_type": blob.content_type
            }
            for blob in blobs
        ]


# 싱글톤 인스턴스
_gcs_helper: Optional[GCSHelper] = None


def get_gcs_helper() -> GCSHelper:
    """GCS 헬퍼 싱글톤 인스턴스 반환"""
    global _gcs_helper
    if _gcs_helper is None:
        _gcs_helper = GCSHelper()
    return _gcs_helper
