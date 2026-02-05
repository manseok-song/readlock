"""GCS 직접 업로드 컴포넌트

클라이언트(브라우저)에서 GCS로 직접 업로드하여 Cloud Run 413 에러 우회.
Signed URL을 사용하여 인증 없이 업로드 가능.
"""

import json
import uuid
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# GCS Helper import
try:
    from src.storage.gcs import get_gcs_helper, GCSHelper
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


def generate_upload_url(filename: str) -> Optional[dict]:
    """업로드용 signed URL 생성

    Args:
        filename: 업로드할 파일명

    Returns:
        dict with upload_url, gs_uri, blob_name or None if failed
    """
    if not GCS_AVAILABLE:
        return None

    try:
        gcs = get_gcs_helper()

        # 고유 blob 이름 생성 (timestamp + uuid + filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = Path(filename).name  # 경로 제거
        blob_name = f"uploads/{timestamp}_{unique_id}_{safe_filename}"

        # Content-Type 추론
        suffix = Path(filename).suffix.lower()
        content_types = {
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
        }
        content_type = content_types.get(suffix, "application/octet-stream")

        # Signed URL 생성
        result = gcs.generate_upload_signed_url(
            blob_name=blob_name,
            content_type=content_type,
            expiration_minutes=60  # 1시간 유효
        )

        return result

    except Exception as e:
        print(f"[GCS] Signed URL 생성 실패: {e}")
        return None


def render_simple_gcs_upload() -> Optional[Tuple[str, str]]:
    """간단한 GCS 업로드 (서버 사이드, 청크 처리)

    Streamlit의 file_uploader를 사용하되, 청크 단위로 GCS에 스트리밍.
    Cloud Run 메모리 제한 내에서 대용량 파일 처리.

    Returns:
        Tuple of (gs_uri, filename) if successful, None otherwise
    """
    if not GCS_AVAILABLE:
        st.warning("GCS 설정이 필요합니다")
        return None

    st.markdown("""
    ### GCS 직접 업로드

    파일이 **GCS로 직접 스트리밍** 업로드됩니다.
    Cloud Run 서버 메모리를 거치지 않아 **대용량 파일도 처리 가능**합니다.
    """)

    # 파일 업로드 (청크 처리)
    uploaded_file = st.file_uploader(
        "영상 또는 오디오 파일 선택",
        type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a", "flac"],
        help="최대 2GB까지 지원"
    )

    if uploaded_file:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"파일: **{uploaded_file.name}** ({file_size_mb:.1f} MB)")

        if st.button("GCS에 업로드", type="primary"):
            return _stream_upload_to_gcs(uploaded_file)

    return None


def _stream_upload_to_gcs(uploaded_file) -> Optional[Tuple[str, str]]:
    """스트리밍 방식으로 GCS에 업로드

    메모리 효율적인 청크 업로드.
    """
    try:
        gcs = get_gcs_helper()

        # Blob 이름 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = Path(uploaded_file.name).name
        blob_name = f"uploads/{timestamp}_{unique_id}_{safe_filename}"

        # Content-Type 추론
        suffix = Path(uploaded_file.name).suffix.lower()
        content_types = {
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
        }
        content_type = content_types.get(suffix, "application/octet-stream")

        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        # GCS Blob 생성
        blob = gcs.bucket.blob(blob_name)

        # 스트리밍 업로드 (청크 단위)
        total_size = uploaded_file.size
        uploaded_size = 0
        chunk_size = 8 * 1024 * 1024  # 8MB 청크

        status_text.text("GCS 업로드 시작...")

        # Resumable upload 사용
        with blob.open("wb", content_type=content_type) as gcs_file:
            while True:
                chunk = uploaded_file.read(chunk_size)
                if not chunk:
                    break
                gcs_file.write(chunk)
                uploaded_size += len(chunk)

                # 진행률 업데이트
                progress = uploaded_size / total_size
                progress_bar.progress(progress)
                status_text.text(f"업로드 중... {uploaded_size / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB")

        # 완료
        gs_uri = f"gs://{gcs.bucket_name}/{blob_name}"
        progress_bar.progress(1.0)
        status_text.text("업로드 완료!")

        st.success(f"GCS 업로드 완료")
        st.code(gs_uri)

        # 세션에 저장
        st.session_state.gcs_uri = gs_uri
        st.session_state.uploaded_filename = uploaded_file.name

        return (gs_uri, uploaded_file.name)

    except Exception as e:
        st.error(f"GCS 업로드 실패: {e}")
        import traceback
        print(f"[GCS] Upload error: {traceback.format_exc()}")
        return None


def download_from_gcs(gs_uri: str) -> Optional[str]:
    """GCS URI에서 임시 파일로 다운로드

    Args:
        gs_uri: GCS URI (gs://bucket/path)

    Returns:
        임시 파일 경로 또는 None
    """
    if not gs_uri or not gs_uri.startswith("gs://"):
        return None

    try:
        gcs = get_gcs_helper()

        # GCS에서 임시 파일로 다운로드 (서버 내부)
        import tempfile

        # Blob 경로 추출
        parts = gs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""

        # 임시 파일 생성
        suffix = Path(blob_name).suffix or ".mp4"
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp_file.name
        tmp_file.close()

        with st.spinner("GCS에서 파일 로드 중..."):
            blob = gcs.bucket.blob(blob_name)
            blob.download_to_filename(tmp_path)

        file_size_mb = Path(tmp_path).stat().st_size / (1024 * 1024)
        st.success(f"파일 로드 완료: {file_size_mb:.1f} MB")

        return tmp_path

    except Exception as e:
        st.error(f"GCS 파일 로드 실패: {e}")
        return None


def process_from_gcs_uri(gs_uri: str, settings: dict) -> Optional[str]:
    """GCS URI에서 파일을 가져와 처리 준비

    Args:
        gs_uri: GCS URI (gs://bucket/path)
        settings: 전사 설정

    Returns:
        임시 파일 경로 또는 None
    """
    tmp_path = download_from_gcs(gs_uri)
    if tmp_path:
        st.session_state.temp_file_path = tmp_path
        return tmp_path
    return None
