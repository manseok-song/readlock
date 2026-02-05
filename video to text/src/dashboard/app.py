"""Streamlit 웹 대시보드"""

import asyncio
import io
import json
import os
import sys
import tempfile
import threading
import time
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from pathlib import Path
from typing import Optional

# src 디렉토리를 path에 추가 (상대 import 문제 해결)
_src_dir = Path(__file__).parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_src_dir.parent) not in sys.path:
    sys.path.insert(0, str(_src_dir.parent))

import streamlit as st

# Streamlit 페이지 설정 (가장 먼저 호출해야 함)
st.set_page_config(
    page_title="Video to Text - 한국어 전사 시스템",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.audio.analyzer import AudioAnalyzer
from src.pipeline import (
    TranscriptionPipeline, PipelineConfig, PipelineMode, OutputFormat
)
from src.stt.base import TranscriptionResult

# GCS 자동 업로드 지원 (선택적)
try:
    from src.storage.gcs import get_gcs_helper, GCSHelper
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# GCS 직접 업로드 컴포넌트 (서버 스트리밍)
try:
    from src.dashboard.gcs_uploader import (
        render_simple_gcs_upload,
        download_from_gcs,
        process_from_gcs_uri
    )
    GCS_DIRECT_UPLOAD_AVAILABLE = GCS_AVAILABLE
except ImportError:
    GCS_DIRECT_UPLOAD_AVAILABLE = False

# GCS 클라이언트 직접 업로드 (JavaScript, 413 완전 우회)
try:
    from src.dashboard.gcs_direct_upload import (
        render_client_direct_upload,
        get_signed_upload_url
    )
    GCS_CLIENT_UPLOAD_AVAILABLE = GCS_AVAILABLE
except ImportError:
    GCS_CLIENT_UPLOAD_AVAILABLE = False

# 선거 정보 자동 감지
try:
    from src.rag.election_detector import detect_election_info, DetectedElectionInfo
    ELECTION_DETECTOR_AVAILABLE = True
except ImportError:
    ELECTION_DETECTOR_AVAILABLE = False


class LogCapture:
    """실시간 로그 캡처 클래스 (stdout/stderr 가로채기)"""

    def __init__(self):
        self.logs = []
        self.lock = threading.Lock()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def write(self, text):
        """stdout/stderr 출력을 가로채서 저장"""
        if text.strip():  # 빈 줄 제외
            with self.lock:
                # 타임스탬프 추가
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.logs.append(f"[{timestamp}] {text.rstrip()}")
        # 원본에도 출력 (Cloud Run 로그용)
        self._original_stdout.write(text)
        self._original_stdout.flush()

    def flush(self):
        self._original_stdout.flush()

    def get_logs(self):
        """현재까지의 로그 반환"""
        with self.lock:
            return list(self.logs)

    def clear(self):
        """로그 초기화"""
        with self.lock:
            self.logs = []


def init_session_state():
    """세션 상태 초기화"""
    if "transcription_result" not in st.session_state:
        st.session_state.transcription_result = None
    if "audio_metadata" not in st.session_state:
        st.session_state.audio_metadata = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "progress" not in st.session_state:
        st.session_state.progress = 0
    if "progress_text" not in st.session_state:
        st.session_state.progress_text = ""
    if "history" not in st.session_state:
        st.session_state.history = []
    # 실시간 로그 모니터링
    if "live_logs" not in st.session_state:
        st.session_state.live_logs = []
    if "transcription_done" not in st.session_state:
        st.session_state.transcription_done = False
    if "transcription_error" not in st.session_state:
        st.session_state.transcription_error = None
    # 다운로드 캐시 (URL -> 파일경로)
    if "download_cache" not in st.session_state:
        st.session_state.download_cache = {}
    # GCS 업로드 URI
    if "gcs_uri" not in st.session_state:
        st.session_state.gcs_uri = None
    # 선거 정보 (RAG용)
    if "election_info" not in st.session_state:
        st.session_state.election_info = {
            "region": "",
            "election_type": "",
            "candidates": [],
            "policies": [],
        }
    # 품질 점수
    if "quality_score" not in st.session_state:
        st.session_state.quality_score = None
    # 지식 베이스
    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = None


def check_api_keys() -> dict:
    """API 키 상태 확인"""
    return {
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "HF_TOKEN": bool(os.getenv("HF_TOKEN"))
    }


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("⚙️ 설정")

        # API 키 상태
        st.subheader("🔑 API 키 상태")
        api_status = check_api_keys()

        for key, status in api_status.items():
            if status:
                st.success(f"✓ {key}")
            else:
                if key == "GEMINI_API_KEY":
                    st.error(f"✗ {key} (필수)")
                else:
                    st.warning(f"○ {key} (선택)")

        st.divider()

        # 🗳️ AI Election Archiver 설정
        st.subheader("🗳️ AI Election Archiver")
        st.info("🚀 **Gemini 3 Flash** | 영상 자동 감지 | 선거 토론 특화")

        # 고정 설정 (단순화)
        mode = "fast"  # Gemini 3 Flash 단일 파이프라인
        gemini_model = "gemini-3-flash-preview"
        use_video_mode = False  # 자동 감지에 맡김
        remove_fillers = False  # 필러 제거 비활성화
        election_debate_mode = True  # 선거 토론회 모드 기본 활성화

        st.divider()

        # 기본 설정
        st.subheader("⚙️ 기본 설정")

        language = st.selectbox(
            "언어",
            options=["ko", "en"],
            index=0,
            format_func=lambda x: {"ko": "한국어", "en": "English"}[x]
        )

        num_speakers = st.number_input(
            "화자 수 (0=자동)",
            min_value=0,
            max_value=10,
            value=0,
            help="예상되는 화자 수. 0이면 자동 감지"
        )

        output_formats = st.multiselect(
            "출력 포맷",
            options=["srt", "txt", "json"],
            default=["srt", "txt"]
        )

        include_speakers = st.checkbox(
            "화자 레이블 포함",
            value=True
        )

        # 선거 정보는 영상 초반부에서 자동 감지됨
        if ELECTION_DETECTOR_AVAILABLE:
            st.divider()
            st.caption("💡 선거 정보 (후보자, 지역, 정당)는 **영상 초반부에서 자동 감지**됩니다.")

        return {
            "mode": mode,
            "gemini_model": gemini_model,
            "language": language,
            "num_speakers": num_speakers if num_speakers > 0 else None,
            "output_formats": output_formats,
            "include_speakers": include_speakers,
            "proper_nouns": None,  # 자동 감지로 대체
            "use_video_mode": use_video_mode,
            "remove_fillers": remove_fillers,
            "election_debate_mode": election_debate_mode
        }


def render_input_section():
    """입력 섹션 (파일 업로드 → GCS 자동 업로드 → 자동 처리)"""
    st.header("📥 입력")

    # GCS 클라이언트 직접 업로드 탭 추가 (대용량 파일용, 413 우회)
    if GCS_CLIENT_UPLOAD_AVAILABLE or GCS_DIRECT_UPLOAD_AVAILABLE:
        input_tab0, input_tab1, input_tab2, input_tab3, input_tab4 = st.tabs([
            "☁️ GCS 직접 업로드 (권장)",
            "📤 파일 업로드",
            "📁 Google Drive",
            "🔗 직접 URL",
            "🎬 YouTube URL"
        ])
    else:
        input_tab1, input_tab2, input_tab3, input_tab4 = st.tabs([
            "📤 파일 업로드",
            "📁 Google Drive",
            "🔗 직접 URL",
            "🎬 YouTube URL"
        ])
        input_tab0 = None

    # GCS 클라이언트 직접 업로드 탭 (JavaScript, 413 완전 우회)
    if GCS_CLIENT_UPLOAD_AVAILABLE and input_tab0:
        with input_tab0:
            # JavaScript 클라이언트 직접 업로드 컴포넌트 사용
            gs_uri = render_client_direct_upload()
            if gs_uri:
                return ("gcs_uri", gs_uri)

    # 폴백: 서버 스트리밍 (GCS_CLIENT_UPLOAD가 없을 때)
    elif GCS_DIRECT_UPLOAD_AVAILABLE and input_tab0:
        with input_tab0:
            st.markdown("""
            ### ☁️ GCS 직접 업로드 (대용량 파일 권장)

            **Cloud Run 413 에러 우회** - 파일이 GCS로 직접 스트리밍됩니다.
            """)

            uploaded_file = st.file_uploader(
                "영상 또는 오디오 파일 선택",
                type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a", "flac"],
                key="gcs_direct_uploader"
            )

            if uploaded_file:
                file_size_mb = uploaded_file.size / (1024 * 1024)
                st.info(f"파일: **{uploaded_file.name}** ({file_size_mb:.1f} MB)")

                if st.button("GCS에 업로드", type="primary", key="gcs_upload_btn"):
                    result = _stream_upload_and_prepare(uploaded_file)
                    if result:
                        return ("gcs_uri", result)

            if st.session_state.get("gcs_uri"):
                gs_uri = st.session_state.gcs_uri
                st.success(f"GCS 파일 준비됨")
                st.code(gs_uri)
                return ("gcs_uri", gs_uri)

    with input_tab1:
        st.markdown("""
        ### 🚀 파일 업로드 → 자동 처리

        파일을 업로드하면 **자동으로 GCS에 저장**되고 **즉시 전사가 시작**됩니다.

        **지원 포맷:**
        - 🎬 영상: MP4, MKV, AVI, MOV
        - 🎵 오디오: MP3, WAV, M4A, FLAC
        """)

        uploaded_file = st.file_uploader(
            "영상 또는 오디오 파일을 선택하세요",
            type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a", "flac"],
            help="선거 토론회 영상을 업로드하면 자동으로 처리됩니다"
        )

        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.success(f"✅ 파일 선택됨: {uploaded_file.name} ({file_size_mb:.1f} MB)")
            return ("file", uploaded_file)

    with input_tab2:
        st.markdown("""
        ### Google Drive에서 파일 가져오기

        **설정 방법:**
        1. Google Drive에 영상/오디오 파일 업로드
        2. 파일 우클릭 → **"공유"** → **"링크가 있는 모든 사용자"**로 설정
        3. 공유 링크 복사 후 아래에 붙여넣기

        *시스템이 자동으로 다운로드 링크로 변환합니다*
        """)

        gdrive_url = st.text_input(
            "Google Drive 공유 링크",
            placeholder="https://drive.google.com/file/d/FILE_ID/view?usp=sharing",
            help="Google Drive 공유 링크를 붙여넣으세요"
        )

        if gdrive_url:
            # Google Drive 링크 변환
            converted_url = convert_gdrive_url(gdrive_url)
            if converted_url:
                st.success(f"✅ 변환된 다운로드 링크가 준비되었습니다")
                st.code(converted_url, language=None)
                return ("direct_url", converted_url)
            else:
                st.error("❌ 유효하지 않은 Google Drive 링크입니다")

    with input_tab3:
        st.markdown("""
        **직접 URL 다운로드**
        - Dropbox: URL 끝의 `dl=0`을 `dl=1`로 변경
        - OneDrive: 공유 링크에서 직접 다운로드 URL 추출
        - 기타 직접 다운로드 가능한 URL
        """)
        direct_url = st.text_input(
            "파일 직접 다운로드 URL을 입력하세요",
            placeholder="https://example.com/video.mp4",
            help="직접 다운로드 가능한 미디어 파일 URL"
        )
        if direct_url:
            if direct_url.startswith("http://") or direct_url.startswith("https://"):
                st.success("✅ URL 형식 확인됨")
                return ("direct_url", direct_url)
            else:
                st.error("❌ http:// 또는 https://로 시작하는 URL을 입력하세요")

    with input_tab4:
        st.caption("⚠️ Cloud Run 서버에서 YouTube 다운로드가 차단될 수 있습니다.")
        youtube_url = st.text_input(
            "YouTube URL을 입력하세요",
            placeholder="https://www.youtube.com/watch?v=...",
            help="YouTube 동영상 URL (일반 영상, Shorts 지원)"
        )
        if youtube_url:
            if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
                st.success("✅ 유효한 YouTube URL")
                return ("youtube", youtube_url)
            else:
                st.error("❌ 유효하지 않은 YouTube URL")

    return (None, None)


def convert_gdrive_url(url: str) -> Optional[str]:
    """Google Drive 공유 링크를 직접 다운로드 URL로 변환"""
    import re

    # 패턴 1: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    pattern1 = r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)'
    match1 = re.search(pattern1, url)
    if match1:
        file_id = match1.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    # 패턴 2: https://drive.google.com/open?id=FILE_ID
    pattern2 = r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)'
    match2 = re.search(pattern2, url)
    if match2:
        file_id = match2.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    # 패턴 3: 이미 직접 다운로드 URL인 경우
    if "drive.google.com/uc" in url and "export=download" in url:
        return url

    return None


def render_file_upload():
    """파일 업로드 영역 (하위 호환용)"""
    result = render_input_section()
    if result[0] == "file":
        return result[1]
    return None


def upload_to_gcs(file_path: str, filename: str) -> Optional[str]:
    """GCS에 파일 업로드 (자동 백업)"""
    if not GCS_AVAILABLE:
        return None

    try:
        gcs = get_gcs_helper()
        gs_uri, public_url = gcs.upload_file(file_path)
        print(f"[GCS] 자동 업로드 완료: {gs_uri}")
        return gs_uri
    except Exception as e:
        print(f"[GCS] 업로드 실패 (로컬 처리 계속): {e}")
        return None


def _stream_upload_and_prepare(uploaded_file) -> Optional[str]:
    """GCS로 스트리밍 업로드 후 URI 반환

    Cloud Run 메모리 제한 우회를 위한 청크 업로드.

    Returns:
        GCS URI (gs://bucket/path) or None
    """
    if not GCS_AVAILABLE:
        st.error("GCS 설정이 필요합니다")
        return None

    try:
        import uuid
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

        status_text.text("☁️ GCS 직접 업로드 시작...")

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
                status_text.text(f"☁️ 업로드 중... {uploaded_size / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB")

        # 완료
        gs_uri = f"gs://{gcs.bucket_name}/{blob_name}"
        progress_bar.progress(1.0)
        status_text.text("✅ GCS 업로드 완료!")

        st.success(f"☁️ GCS 업로드 완료: {uploaded_file.name}")
        st.code(gs_uri)

        # 세션에 저장
        st.session_state.gcs_uri = gs_uri
        st.session_state.uploaded_filename = uploaded_file.name

        return gs_uri

    except Exception as e:
        st.error(f"❌ GCS 업로드 실패: {e}")
        import traceback
        print(f"[GCS] Upload error: {traceback.format_exc()}")
        return None


def download_gcs_to_temp(gs_uri: str) -> Optional[str]:
    """GCS URI에서 임시 파일로 다운로드 (서버 내부)

    Args:
        gs_uri: GCS URI (gs://bucket/path)

    Returns:
        임시 파일 경로 또는 None
    """
    if not gs_uri or not gs_uri.startswith("gs://"):
        return None

    try:
        gcs = get_gcs_helper()

        # Blob 경로 추출
        parts = gs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""

        # 임시 파일 생성
        suffix = Path(blob_name).suffix or ".mp4"
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp_file.name
        tmp_file.close()

        with st.spinner("☁️ GCS에서 파일 로드 중..."):
            blob = gcs.bucket.blob(blob_name)
            blob.download_to_filename(tmp_path)

        file_size_mb = Path(tmp_path).stat().st_size / (1024 * 1024)
        st.success(f"✅ 파일 로드 완료: {file_size_mb:.1f} MB")

        return tmp_path

    except Exception as e:
        st.error(f"❌ GCS 파일 로드 실패: {e}")
        return None


def render_file_info(uploaded_file):
    """파일 정보 표시 및 GCS 자동 업로드"""
    import traceback

    if uploaded_file is None:
        return None

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # GCS 자동 업로드 (백그라운드)
    gcs_uri = None
    if GCS_AVAILABLE:
        with st.spinner("☁️ GCS에 파일 백업 중..."):
            gcs_uri = upload_to_gcs(tmp_path, uploaded_file.name)
            if gcs_uri:
                st.success(f"☁️ GCS 백업 완료")
                st.caption(f"`{gcs_uri}`")

    # 파일 분석
    try:
        analyzer = AudioAnalyzer()
        metadata = analyzer.analyze(tmp_path)
        quality = analyzer.get_audio_quality_score(metadata)
        estimate = analyzer.estimate_processing_time(metadata)

        st.session_state.audio_metadata = metadata
        st.session_state.gcs_uri = gcs_uri  # GCS URI 저장

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📏 길이", metadata.duration_formatted)
        with col2:
            st.metric("🎵 샘플레이트", f"{metadata.sample_rate:,} Hz")
        with col3:
            st.metric("📊 채널", f"{metadata.channels}ch ({estimate['channel_type']})")

        # 품질 점수
        col4, col5, col6 = st.columns(3)

        with col4:
            quality_color = "🟢" if quality["score"] >= 80 else "🟡" if quality["score"] >= 50 else "🔴"
            st.metric("품질 점수", f"{quality_color} {quality['score']}/100")
        with col5:
            st.metric("📁 파일 크기", f"{metadata.file_size / (1024*1024):.1f} MB")

        if quality["issues"]:
            with st.expander("⚠️ 품질 주의사항"):
                for issue in quality["issues"]:
                    st.warning(issue)

        return tmp_path

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 파일 분석 실패: {error_msg}")
        print(traceback.format_exc())

        # 분석 실패해도 파일 경로는 반환 (전사 시도 가능)
        st.warning(f"⚠️ 파일 분석 실패: {error_msg}")
        st.info("파일 분석은 실패했지만 전사를 시도할 수 있습니다.")

        # 기본 파일 크기만 표시
        file_size = Path(tmp_path).stat().st_size
        st.metric("📁 파일 크기", f"{file_size / (1024*1024):.1f} MB")

        return tmp_path


async def run_transcription(file_path: str, settings: dict) -> Optional[tuple]:
    """전사 실행"""
    try:
        # 선거 정보 자동 감지 (전사 전에 수행)
        detected_info = None
        if ELECTION_DETECTOR_AVAILABLE and settings.get("election_debate_mode", False):
            try:
                print("[Pipeline] 선거 정보 자동 감지 시작...")
                print("[Pipeline] 영상 초반부 분석 중 (1분~4분 구간)...")
                detected_info = await detect_election_info(file_path, auto_retry=True)

                if detected_info and detected_info.confidence >= 0.5:
                    print(f"[Pipeline] 선거 정보 감지 완료 (신뢰도: {detected_info.confidence:.2f})")
                    print(f"[Pipeline] - 선거 유형: {detected_info.election_type}")
                    print(f"[Pipeline] - 지역: {detected_info.region} {detected_info.position}")
                    print(f"[Pipeline] - 후보자: {', '.join(detected_info.candidates)}")
                    print(f"[Pipeline] - 정당: {', '.join(detected_info.parties)}")

                    # 감지된 정보를 proper_nouns에 추가
                    existing_nouns = settings.get("proper_nouns", []) or []
                    auto_nouns = (
                        detected_info.candidates +
                        detected_info.parties +
                        [detected_info.region, detected_info.position]
                    )
                    # 빈 문자열 제거
                    auto_nouns = [n for n in auto_nouns if n]
                    settings["proper_nouns"] = list(set(existing_nouns + auto_nouns))
                    print(f"[Pipeline] 자동 추가된 고유명사: {auto_nouns}")

                else:
                    print(f"[Pipeline] 선거 정보 감지 실패 또는 낮은 신뢰도")

            except Exception as e:
                print(f"[Pipeline] 선거 정보 감지 오류 (무시하고 계속): {e}")

        # 모드 파싱
        mode = PipelineMode(settings["mode"])

        # 출력 포맷 파싱
        formats = [OutputFormat(f) for f in settings["output_formats"]]

        # 파이프라인 설정
        config = PipelineConfig(
            mode=mode,
            gemini_model=settings.get("gemini_model", "gemini-2.5-pro"),
            language=settings["language"],
            num_speakers=settings["num_speakers"],
            proper_nouns=settings.get("proper_nouns"),  # 고유명사 힌트 전달
            use_video_mode=settings.get("use_video_mode", False),  # 영상 모드 (화면 참고)
            remove_fillers=settings.get("remove_fillers", False),  # 필러 제거 옵션
            election_debate_mode=settings.get("election_debate_mode", False),  # 선거 토론회 모드
            output_formats=formats,
            include_speaker_labels=settings["include_speakers"]
        )

        # 진행 콜백
        def progress_callback(stage: str, progress: float):
            st.session_state.progress = int(progress * 100)
            st.session_state.progress_text = stage

        pipeline = TranscriptionPipeline(config, progress_callback=progress_callback)

        # 임시 출력 디렉토리
        with tempfile.TemporaryDirectory() as output_dir:
            result = await pipeline.run(file_path, output_dir)

            if result.success:
                # 출력 파일 읽기
                output_contents = {}
                for fmt, path in result.output_files.items():
                    if path.exists():
                        with open(path, "r", encoding="utf-8") as f:
                            output_contents[fmt] = f.read()

                return result.transcription, output_contents, result.processing_info

            else:
                st.error(f"전사 실패: {result.error}")
                return None

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None


def _run_transcription_thread(file_path: str, settings: dict, log_capture: LogCapture, result_holder: dict):
    """백그라운드 스레드에서 전사 실행 (로그 캡처)

    Args:
        result_holder: 스레드 간 결과 전달용 딕셔너리 (스레드 안전)
    """
    # stdout/stderr 가로채기
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = log_capture
    sys.stderr = log_capture

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(run_transcription(file_path, settings))
            if result:
                transcription, output_contents, processing_info = result
                # 결과를 result_holder에 저장 (스레드 안전)
                result_holder["transcription_result"] = {
                    "transcription": transcription,
                    "outputs": output_contents,
                    "processing_info": processing_info,
                    "timestamp": datetime.now().isoformat(),
                    "settings": settings
                }
                result_holder["history_item"] = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "duration": st.session_state.audio_metadata.duration_formatted if st.session_state.audio_metadata else "N/A",
                    "mode": settings["mode"],
                    "speakers": transcription.num_speakers
                }
                result_holder["success"] = True
                print("[Thread] ✅ 전사 완료 - 결과 저장됨")
            else:
                result_holder["error"] = "전사 결과가 None입니다. (파이프라인 내부 오류)"
                result_holder["success"] = False
                print("[Thread] ❌ 전사 실패 - 결과 None")
        finally:
            loop.close()

    except Exception as e:
        import traceback
        error_msg = f"{e}\n{traceback.format_exc()}"
        result_holder["error"] = error_msg
        result_holder["success"] = False
        print(f"[Thread] ❌ 예외 발생: {e}")

    finally:
        # stdout/stderr 복원
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        result_holder["done"] = True


def render_transcription_button(file_path: str, settings: dict):
    """전사 시작 버튼 (실시간 로그 모니터링)"""
    if st.button("🚀 전사 시작", type="primary", use_container_width=True):
        # 상태 초기화
        st.session_state.processing = True
        st.session_state.transcription_done = False
        st.session_state.transcription_error = None
        st.session_state.live_logs = []

        # 로그 캡처 객체 생성
        log_capture = LogCapture()

        # 스레드 간 결과 전달용 딕셔너리 (스레드 안전)
        result_holder = {"done": False, "success": False, "error": None}

        # 백그라운드 스레드로 전사 실행
        thread = threading.Thread(
            target=_run_transcription_thread,
            args=(file_path, settings, log_capture, result_holder),
            daemon=True
        )
        thread.start()

        # 실시간 로그 표시 UI
        st.write("### 📡 실시간 처리 로그")
        st.info("💡 청크별 진행 상황이 아래에 실시간으로 표시됩니다.")

        log_placeholder = st.empty()
        status_placeholder = st.empty()

        # 스레드가 실행 중인 동안 로그 폴링
        while thread.is_alive() or not result_holder.get("done", False):
            current_logs = log_capture.get_logs()

            # 로그 표시 (최근 30줄만)
            if current_logs:
                display_logs = current_logs[-30:]  # 최근 30줄
                log_text = "\n".join(display_logs)
                log_placeholder.code(log_text, language="text")

            # 진행 상태 표시
            status_placeholder.write(f"⏳ 처리 중... (로그 {len(current_logs)}줄)")

            time.sleep(0.5)  # 0.5초마다 갱신

            # 스레드 종료 확인
            if result_holder.get("done", False):
                break

        # 최종 로그 표시
        final_logs = log_capture.get_logs()
        if final_logs:
            log_placeholder.code("\n".join(final_logs[-50:]), language="text")

        # result_holder에서 결과 가져와서 session_state에 저장
        if result_holder.get("success", False):
            st.session_state.transcription_result = result_holder.get("transcription_result")
            if result_holder.get("history_item"):
                st.session_state.history.append(result_holder["history_item"])
            st.session_state.transcription_done = True
            st.session_state.transcription_error = None
        elif result_holder.get("error"):
            st.session_state.transcription_error = result_holder["error"]
            st.session_state.transcription_done = False

        st.session_state.processing = False

        # 결과 처리
        if st.session_state.transcription_done:
            status_placeholder.success("✅ 전사 완료!")
            st.balloons()
            st.rerun()

        elif st.session_state.transcription_error:
            status_placeholder.error(f"❌ 오류 발생: {st.session_state.transcription_error}")

        else:
            status_placeholder.warning("⚠️ 처리가 예상치 못하게 종료되었습니다.")


def render_results():
    """결과 표시"""
    result = st.session_state.transcription_result
    if result is None:
        return

    transcription: TranscriptionResult = result["transcription"]
    outputs = result["outputs"]
    processing_info = result["processing_info"]

    st.header("📊 전사 결과")

    # 요약 통계
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🎤 감지된 화자", f"{transcription.num_speakers}명")
    with col2:
        st.metric("📝 세그먼트 수", len(transcription.segments))
    with col3:
        total_words = sum(len(seg.text.split()) for seg in transcription.segments)
        st.metric("📖 총 단어 수", f"{total_words:,}")
    with col4:
        st.metric("⚙️ 엔진", transcription.engine)

    # 처리 단계
    if processing_info:
        steps = processing_info.get("steps_completed", [])
        st.info(f"**처리 단계:** {' → '.join(steps)}")

    st.divider()

    # 탭으로 결과 표시
    tabs = st.tabs(["📄 전체 텍스트", "🎯 세그먼트 뷰", "👥 화자별 분석", "📊 품질 리포트", "📥 다운로드"])

    # 전체 텍스트 탭
    with tabs[0]:
        st.text_area(
            "전사 결과",
            value=transcription.full_text,
            height=400,
            label_visibility="collapsed"
        )

    # 세그먼트 뷰 탭
    with tabs[1]:
        render_segment_view(transcription)

    # 화자별 분석 탭
    with tabs[2]:
        render_speaker_analysis(transcription)

    # 품질 리포트 탭
    with tabs[3]:
        render_quality_report(transcription)

    # 다운로드 탭
    with tabs[4]:
        render_download_section(outputs)


def render_quality_report(transcription: TranscriptionResult):
    """품질 리포트 표시"""
    st.subheader("📊 품질 분석 리포트")

    # 세션에 저장된 품질 점수 확인
    quality_score = st.session_state.quality_score

    if quality_score is None:
        # 품질 점수 계산
        try:
            from src.quality.scorer import QualityScorer
        except ImportError as e:
            st.warning(f"품질 분석 모듈(scorer)을 불러올 수 없습니다: {e}")
            st.info("pip install 필요 패키지 확인 필요")
            _render_basic_quality_stats(transcription)
            return

        try:
            from src.rag.knowledge_builder import create_knowledge_base
            rag_available = True
        except ImportError:
            rag_available = False
            create_knowledge_base = None

        try:
            # 선거 정보에서 지식 베이스 생성
            election_info = st.session_state.election_info
            knowledge_base = None

            if rag_available and (election_info.get("candidates") or election_info.get("policies")):
                try:
                    knowledge_base = create_knowledge_base(
                        candidates=election_info.get("candidates", []),
                        policies=election_info.get("policies", []),
                        election_type=election_info.get("election_type"),
                        region=election_info.get("region"),
                    )
                    st.session_state.knowledge_base = knowledge_base
                except Exception as kb_error:
                    st.warning(f"지식 베이스 생성 실패 (기본 분석 진행): {kb_error}")
                    knowledge_base = None

            scorer = QualityScorer()
            quality_score = scorer.calculate(transcription, knowledge_base)
            st.session_state.quality_score = quality_score

        except Exception as e:
            st.error(f"품질 분석 오류: {e}")
            _render_basic_quality_stats(transcription)
            return

    # 총점 표시
    col1, col2, col3 = st.columns(3)

    with col1:
        grade_color = {
            "A+": "🟢", "A": "🟢", "B+": "🔵", "B": "🔵",
            "C+": "🟡", "C": "🟡", "D": "🟠", "F": "🔴"
        }.get(quality_score.grade, "⚪")
        st.metric("품질 등급", f"{grade_color} {quality_score.grade}")

    with col2:
        st.metric("총점", f"{quality_score.total:.1%}")

    with col3:
        status = "✅ 양호" if quality_score.is_acceptable else "⚠️ 검토 필요"
        st.metric("상태", status)

    st.divider()

    # 세부 점수
    st.subheader("세부 점수")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("화자 정확도", f"{quality_score.speaker_accuracy:.1%}")
    with col2:
        st.metric("정책 정확도", f"{quality_score.policy_accuracy:.1%}")
    with col3:
        st.metric("평균 신뢰도", f"{quality_score.avg_confidence:.1%}")
    with col4:
        st.metric("타임스탬프", f"{quality_score.timestamp_quality:.1%}")

    # 통계
    st.divider()
    st.subheader("📈 통계")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 세그먼트", quality_score.total_segments)
    with col2:
        st.metric("매칭된 화자", quality_score.matched_speakers)
    with col3:
        st.metric("매칭된 정책", quality_score.matched_policies)
    with col4:
        st.metric("낮은 신뢰도", quality_score.low_confidence_segments)

    # 문제점 목록
    if quality_score.issues:
        st.divider()
        st.subheader("⚠️ 검토 필요 사항")

        for issue in quality_score.issues[:15]:  # 최대 15개
            severity_icon = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }.get(issue.severity, "⚪")

            with st.expander(f"{severity_icon} [{issue.type}] {issue.description[:50]}..."):
                st.write(f"**설명:** {issue.description}")
                if issue.suggestion:
                    st.info(f"**제안:** {issue.suggestion}")
                if issue.segment_index is not None:
                    st.caption(f"세그먼트 #{issue.segment_index}")


def _render_basic_quality_stats(transcription: TranscriptionResult):
    """기본 품질 통계 표시 (품질 모듈 사용 불가 시 폴백)"""
    st.info("품질 분석 모듈이 없어 기본 통계만 표시됩니다.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("세그먼트 수", len(transcription.segments))

    with col2:
        # 평균 신뢰도 계산
        confidences = [
            seg.confidence for seg in transcription.segments
            if seg.confidence is not None
        ]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            st.metric("평균 신뢰도", f"{avg_conf:.1%}")
        else:
            st.metric("평균 신뢰도", "N/A")

    with col3:
        st.metric("화자 수", transcription.num_speakers or "N/A")

    # 낮은 신뢰도 세그먼트 표시
    low_conf_segments = [
        (i, seg) for i, seg in enumerate(transcription.segments)
        if seg.confidence is not None and seg.confidence < 0.7
    ]

    if low_conf_segments:
        st.divider()
        st.subheader(f"⚠️ 낮은 신뢰도 세그먼트 ({len(low_conf_segments)}개)")
        for i, seg in low_conf_segments[:10]:  # 최대 10개
            st.caption(f"#{i}: [{seg.confidence:.2f}] {seg.text[:50]}...")


def render_segment_view(transcription: TranscriptionResult):
    """세그먼트 타임라인 뷰"""
    st.subheader("세그먼트 타임라인")

    # 검색/필터
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 텍스트 검색", placeholder="검색어 입력...")
    with col2:
        speaker_filter = st.selectbox(
            "화자 필터",
            options=["전체"] + transcription.speakers
        )

    # 세그먼트 표시
    for i, seg in enumerate(transcription.segments):
        # 필터 적용
        if search and search.lower() not in seg.text.lower():
            continue
        if speaker_filter != "전체" and seg.speaker != speaker_filter:
            continue

        # 화자별 색상
        speaker_colors = {
            "화자1": "🔵", "화자2": "🟢", "화자3": "🟡",
            "화자4": "🟣", "화자5": "🟠", "화자6": "🔴"
        }
        color = speaker_colors.get(seg.speaker, "⚪")

        # 시간 포맷
        start_time = f"{int(seg.start // 60):02d}:{int(seg.start % 60):02d}"
        end_time = f"{int(seg.end // 60):02d}:{int(seg.end % 60):02d}"

        with st.container():
            col1, col2 = st.columns([1, 5])
            with col1:
                st.caption(f"⏱️ {start_time} - {end_time}")
                st.caption(f"{color} {seg.speaker or '화자'}")
            with col2:
                st.markdown(f"**{seg.text}**")

            st.divider()


def render_speaker_analysis(transcription: TranscriptionResult):
    """화자별 분석"""
    st.subheader("화자별 통계")

    if not transcription.speakers:
        st.info("화자 정보가 없습니다.")
        return

    # 실제 전체 길이 (마지막 세그먼트 종료 시간 기준)
    actual_duration = transcription.duration if transcription.duration > 0 else (
        transcription.segments[-1].end if transcription.segments else 0
    )

    # 화자별 통계 계산 (비중복 시간 계산)
    speaker_stats = {}
    for seg in transcription.segments:
        speaker = seg.speaker or "알 수 없음"
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "time": 0,
                "segments": 0,
                "words": 0,
                "intervals": []  # 시간 구간 저장
            }
        speaker_stats[speaker]["segments"] += 1
        speaker_stats[speaker]["words"] += len(seg.text.split())
        speaker_stats[speaker]["intervals"].append((seg.start, seg.end))

    # 각 화자별 비중복 발화 시간 계산
    for speaker, stats in speaker_stats.items():
        # 구간 정렬 및 병합
        intervals = sorted(stats["intervals"])
        merged = []
        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                # 겹치는 구간 병합
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        # 병합된 구간의 총 시간
        stats["time"] = sum(end - start for start, end in merged)
        del stats["intervals"]  # 정리

    total_time = actual_duration  # 실제 오디오 길이 사용

    # 차트 표시
    import pandas as pd

    df = pd.DataFrame([
        {
            "화자": speaker,
            "발화 시간 (초)": round(stats["time"], 1),
            "발화 비율 (%)": round(stats["time"] / total_time * 100, 1) if total_time > 0 else 0,
            "세그먼트 수": stats["segments"],
            "단어 수": stats["words"]
        }
        for speaker, stats in speaker_stats.items()
    ])

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(df.set_index("화자")["발화 비율 (%)"])

    with col2:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_download_section(outputs: dict):
    """다운로드 섹션 - Base64 Data URI 방식 (Cloud Run 호환)"""
    import base64

    st.subheader("📥 파일 다운로드")

    if not outputs:
        st.info("다운로드 가능한 파일이 없습니다.")
        return

    # MIME 타입 정의 (charset 제거 - 표준 준수)
    mime_types = {
        "srt": "text/plain",
        "vtt": "text/vtt",
        "json": "application/json",
        "txt": "text/plain"
    }

    cols = st.columns(len(outputs))

    for i, (fmt, content) in enumerate(outputs.items()):
        with cols[i]:
            # 포맷별 인코딩 (JSON은 BOM 없이, 나머지는 BOM 포함)
            if isinstance(content, str):
                if fmt == "json":
                    # JSON은 BOM 없이 UTF-8
                    content_bytes = content.encode('utf-8')
                else:
                    # SRT, VTT, TXT는 UTF-8 BOM 추가 (Windows 메모장 호환)
                    content_bytes = ('\ufeff' + content).encode('utf-8')
            else:
                content_bytes = content

            # Base64 인코딩으로 Data URI 생성
            b64_data = base64.b64encode(content_bytes).decode('utf-8')
            mime = mime_types.get(fmt, "text/plain")
            filename = f"transcription.{fmt}"

            # HTML 다운로드 링크 생성 (Cloud Run에서 안정적으로 작동)
            download_link = f'''
            <a href="data:{mime};base64,{b64_data}"
               download="{filename}"
               style="display: inline-block; padding: 0.5rem 1rem;
                      background-color: #FF4B4B; color: white;
                      text-decoration: none; border-radius: 0.5rem;
                      font-weight: 600; text-align: center; width: 100%;
                      box-sizing: border-box;">
                ⬇️ {fmt.upper()} 다운로드
            </a>
            '''
            st.markdown(download_link, unsafe_allow_html=True)
            st.caption(f"📄 {len(content_bytes):,} bytes")

            # 미리보기
            with st.expander(f"📄 {fmt.upper()} 미리보기"):
                if fmt == "json":
                    st.json(json.loads(content))
                else:
                    st.code(content[:2000] + ("..." if len(content) > 2000 else ""), language=None)


def handle_youtube_input(youtube_url: str) -> Optional[str]:
    """YouTube URL 처리 및 다운로드"""
    try:
        from src.input.youtube import YouTubeDownloader

        with st.spinner("📥 YouTube 영상 다운로드 중..."):
            downloader = YouTubeDownloader()

            # 임시 디렉토리에 다운로드
            tmp_dir = Path(tempfile.mkdtemp(prefix="vtt_youtube_"))

            audio_path, video_info = downloader.download_audio_for_transcription(
                youtube_url, tmp_dir
            )

            # 영상 정보 표시
            st.success(f"✅ 다운로드 완료: {video_info.title}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📏 길이", video_info.duration_formatted)
            with col2:
                st.metric("🎬 채널", video_info.channel[:20] + "..." if len(video_info.channel) > 20 else video_info.channel)

            return str(audio_path)

    except Exception as e:
        st.error(f"❌ YouTube 다운로드 실패: {e}")
        return None


def handle_direct_url_input(direct_url: str) -> Optional[str]:
    """직접 URL에서 파일 다운로드 (Google Drive 대용량 파일 지원)"""
    import urllib.request
    import urllib.error
    import ssl
    import traceback
    import re
    import logging

    # 캐시 확인 - 이미 다운로드된 파일이 있으면 재사용
    if direct_url in st.session_state.download_cache:
        cached_path = st.session_state.download_cache[direct_url]
        if Path(cached_path).exists():
            st.success(f"✅ 캐시된 파일 사용: {Path(cached_path).stat().st_size / (1024*1024):.1f} MB")
            return cached_path

    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Google Drive URL인지 확인
    is_gdrive = "drive.google.com" in direct_url
    logger.info(f"[Download] URL: {direct_url[:100]}...")
    logger.info(f"[Download] is_gdrive: {is_gdrive}")

    try:
        with st.spinner("📥 파일 다운로드 중..."):
            # 임시 파일 생성
            tmp_dir = Path(tempfile.mkdtemp(prefix="vtt_direct_"))

            # Google Drive 대용량 파일 다운로드
            if is_gdrive:
                st.info("🔄 Google Drive 파일 다운로드 중... (대용량 파일 지원)")

                # file_id 추출
                file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', direct_url)
                if not file_id_match:
                    file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', direct_url)

                if not file_id_match:
                    st.error("❌ Google Drive 파일 ID를 추출할 수 없습니다")
                    return None

                file_id = file_id_match.group(1)
                logger.info(f"[GDrive] 파일 ID: {file_id}")
                st.text(f"📋 파일 ID: {file_id}")  # UI에 표시
                tmp_file = tmp_dir / "download.mp4"

                # 방법 1: gdown 시도
                download_success = False
                try:
                    import gdown
                    gdrive_url = f"https://drive.google.com/uc?id={file_id}"
                    logger.info(f"[GDrive] gdown 다운로드 시도: {gdrive_url}")
                    st.text(f"🔗 다운로드 URL: {gdrive_url}")

                    output_path = gdown.download(
                        gdrive_url,
                        str(tmp_file),
                        quiet=False,
                        fuzzy=True
                    )
                    logger.info(f"[GDrive] gdown 반환값: {output_path}")

                    if output_path and Path(output_path).exists():
                        tmp_file = Path(output_path)
                        file_size_mb = tmp_file.stat().st_size / (1024 * 1024)
                        logger.info(f"[GDrive] gdown 다운로드 크기: {file_size_mb:.2f} MB")
                        st.text(f"📦 gdown 결과: {file_size_mb:.2f} MB")

                        if file_size_mb > 0.01:
                            download_success = True
                            st.success(f"✅ 다운로드 완료: {file_size_mb:.1f} MB")
                        else:
                            st.warning(f"⚠️ gdown 다운로드 크기가 너무 작음: {file_size_mb:.4f} MB")
                    else:
                        logger.warning(f"[GDrive] gdown 파일 미생성: output_path={output_path}")
                        st.warning("⚠️ gdown이 파일을 생성하지 않았습니다")

                except Exception as e:
                    logger.error(f"[GDrive] gdown 실패: {e}")
                    st.warning(f"⚠️ gdown 오류: {e}")

                # 방법 2: requests + 쿠키 (gdown 실패 시)
                if not download_success:
                    st.info("🔄 requests 방식으로 재시도...")
                    try:
                        import requests

                        session = requests.Session()
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

                        # 첫 번째 요청 (확인 토큰 획득)
                        response = session.get(download_url, stream=True, allow_redirects=True)
                        logger.info(f"[GDrive] requests 응답 상태: {response.status_code}")
                        st.text(f"📡 응답 상태: {response.status_code}")

                        # 응답 헤더 확인
                        content_type = response.headers.get('content-type', '')
                        logger.info(f"[GDrive] Content-Type: {content_type}")

                        # 바이러스 스캔 확인 페이지 처리
                        confirm_token = None
                        for key, value in response.cookies.items():
                            if key.startswith('download_warning'):
                                confirm_token = value
                                break

                        if confirm_token:
                            logger.info(f"[GDrive] 확인 토큰 발견: {confirm_token}")
                            st.text(f"🔑 확인 토큰: {confirm_token}")
                            download_url = f"https://drive.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                            response = session.get(download_url, stream=True)
                        else:
                            # HTML 페이지인 경우 confirm 파라미터 추가
                            if 'text/html' in content_type:
                                st.text("📄 HTML 응답 감지 - confirm 파라미터 추가")
                                download_url = f"https://drive.google.com/uc?export=download&confirm=t&id={file_id}"
                                response = session.get(download_url, stream=True)

                        # 파일 저장
                        with open(tmp_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=32768):
                                if chunk:
                                    f.write(chunk)

                        file_size_mb = tmp_file.stat().st_size / (1024 * 1024)
                        logger.info(f"[GDrive] requests 다운로드 크기: {file_size_mb:.2f} MB")
                        st.text(f"📦 requests 결과: {file_size_mb:.2f} MB")

                        if file_size_mb > 0.01:
                            download_success = True
                            st.success(f"✅ 다운로드 완료: {file_size_mb:.1f} MB")

                    except Exception as e:
                        logger.error(f"[GDrive] requests 실패: {e}")
                        st.error(f"❌ requests 오류: {e}")

                # 다운로드 실패 처리
                if not download_success:
                    st.error("❌ 다운로드 실패: 파일에 접근할 수 없습니다.")
                    st.info("💡 Google Drive에서 파일 우클릭 → '공유' → '링크가 있는 모든 사용자'로 설정 확인")

                    # 파일 내용 확인 (HTML 에러 페이지인지)
                    if tmp_file.exists():
                        try:
                            with open(tmp_file, 'r', errors='ignore') as f:
                                content = f.read(1000)
                                if 'html' in content.lower():
                                    print(f"[GDrive] HTML 에러 페이지: {content[:300]}")
                                    st.error("Google Drive에서 접근이 거부되었습니다. 파일 공유 설정을 확인하세요.")
                        except:
                            pass
                    return None

            # 일반 URL 다운로드 (Google Drive 아닌 경우 또는 gdown 실패 시)
            if not is_gdrive:
                # SSL 인증서 검증 비활성화 (일부 서버 호환성)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # URL에서 파일 확장자 추출
                url_path = direct_url.split("?")[0]  # 쿼리 파라미터 제거
                file_ext = Path(url_path).suffix or ".mp4"

                tmp_file = tmp_dir / f"download{file_ext}"

                # 진행 상황 표시
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 다운로드 요청
                req = urllib.request.Request(
                    direct_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )

                with urllib.request.urlopen(req, context=ssl_context, timeout=300) as response:
                    total_size = int(response.headers.get("Content-Length", 0))
                    downloaded = 0
                    block_size = 8192

                    with open(tmp_file, "wb") as f:
                        while True:
                            buffer = response.read(block_size)
                            if not buffer:
                                break
                            f.write(buffer)
                            downloaded += len(buffer)

                            if total_size > 0:
                                progress = downloaded / total_size
                                progress_bar.progress(progress)
                                status_text.text(f"다운로드 중: {downloaded / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB")
                            else:
                                status_text.text(f"다운로드 중: {downloaded / (1024*1024):.1f} MB")

                progress_bar.progress(1.0)
                status_text.text("다운로드 완료!")

                # 파일 크기 확인
                file_size_mb = tmp_file.stat().st_size / (1024 * 1024)

                if file_size_mb < 0.01:  # 10KB 미만이면 실패로 간주
                    st.error("❌ 다운로드 실패: 파일 크기가 너무 작습니다. URL을 확인하세요.")
                    return None

                st.success(f"✅ 다운로드 완료: {file_size_mb:.1f} MB")

            # 파일 분석 시도
            try:
                analyzer = AudioAnalyzer()
                metadata = analyzer.analyze(str(tmp_file))
                quality = analyzer.get_audio_quality_score(metadata)
                estimate = analyzer.estimate_processing_time(metadata)

                st.session_state.audio_metadata = metadata

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📏 길이", metadata.duration_formatted)
                with col2:
                    st.metric("🎵 샘플레이트", f"{metadata.sample_rate:,} Hz")
                with col3:
                    st.metric("📊 채널", f"{metadata.channels}ch ({estimate['channel_type']})")

                quality_color = "🟢" if quality["score"] >= 80 else "🟡" if quality["score"] >= 50 else "🔴"
                st.metric("품질 점수", f"{quality_color} {quality['score']}/100")

            except Exception as analyze_err:
                st.warning(f"⚠️ 파일 분석 건너뜀: {analyze_err}")
                print(f"[DEBUG] 파일 분석 오류: {analyze_err}")
                print(traceback.format_exc())

            # 캐시에 저장
            st.session_state.download_cache[direct_url] = str(tmp_file)
            return str(tmp_file)

    except urllib.error.HTTPError as e:
        st.error(f"❌ HTTP 오류: {e.code} {e.reason}")
        print(f"[ERROR] HTTP Error: {e.code} {e.reason}")
        return None
    except urllib.error.URLError as e:
        st.error(f"❌ URL 오류: {e.reason}")
        print(f"[ERROR] URL Error: {e.reason}")
        return None
    except Exception as e:
        st.error(f"❌ 다운로드 실패: {e}")
        print(f"[ERROR] Download failed: {e}")
        print(traceback.format_exc())
        return None


def render_history():
    """히스토리 섹션"""
    if not st.session_state.history:
        return

    with st.expander("📜 전사 히스토리"):
        for item in reversed(st.session_state.history[-10:]):
            st.text(
                f"• {item['timestamp']} | {item['duration']} | "
                f"모드: {item['mode']} | 화자: {item['speakers']}명"
            )


def main():
    """메인 대시보드"""
    init_session_state()

    # 헤더
    st.title("🎬 Video to Text")
    st.caption("한국어 토론 화자 분리 및 자막 자동화 시스템")

    # 사이드바 설정
    settings = render_sidebar()

    # 메인 컨텐츠
    col1, col2 = st.columns([2, 3])

    with col1:
        # 입력 (파일 또는 YouTube)
        input_type, input_data = render_input_section()

        file_path = None

        if input_type == "gcs_uri" and input_data:
            # GCS 직접 업로드된 파일 - 서버에서 다운로드 후 처리
            file_path = download_gcs_to_temp(input_data)
            if file_path:
                # 파일 분석 시도
                try:
                    analyzer = AudioAnalyzer()
                    metadata = analyzer.analyze(file_path)
                    quality = analyzer.get_audio_quality_score(metadata)
                    st.session_state.audio_metadata = metadata

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📏 길이", metadata.duration_formatted)
                    with col2:
                        st.metric("🎵 샘플레이트", f"{metadata.sample_rate:,} Hz")
                    with col3:
                        quality_color = "🟢" if quality["score"] >= 80 else "🟡" if quality["score"] >= 50 else "🔴"
                        st.metric("품질 점수", f"{quality_color} {quality['score']}/100")
                except Exception as e:
                    st.warning(f"⚠️ 파일 분석 건너뜀: {e}")

        elif input_type == "file" and input_data:
            file_path = render_file_info(input_data)
        elif input_type == "youtube" and input_data:
            file_path = handle_youtube_input(input_data)
        elif input_type == "direct_url" and input_data:
            file_path = handle_direct_url_input(input_data)

        if file_path and not st.session_state.processing:
            render_transcription_button(file_path, settings)

        if st.session_state.processing:
            st.progress(st.session_state.progress)
            st.info(f"⏳ {st.session_state.progress_text}... {st.session_state.progress}%")

    with col2:
        # 결과 표시
        if st.session_state.transcription_result:
            render_results()
        else:
            st.info("👈 파일을 업로드하거나 YouTube URL을 입력하세요")

            # 사용 가이드
            with st.expander("📖 사용 가이드"):
                st.markdown("""
                ### 🗳️ AI Election Archiver 사용 방법

                **1. 파일 업로드**
                - ☁️ GCS 직접 업로드 탭에서 파일 드래그 앤 드롭
                - 대용량 파일도 브라우저에서 GCS로 직접 업로드 (413 에러 없음)

                **2. 자동 감지**
                - 영상 초반부(1~4분)에서 **선거 정보 자동 감지**
                - 후보자, 정당, 지역, 선거 유형 자동 추출
                - 수동 입력 불필요!

                **3. 전사 시작**
                - `🚀 전사 시작` 버튼 클릭
                - Gemini 3 Flash가 화자 분리 + 전사 수행

                **4. 결과 확인 및 다운로드**
                - 전사 결과, 화자별 통계 확인
                - SRT, TXT 형식으로 다운로드

                ### 💡 팁
                - **선거 토론 특화**: 후보자, 정책명 자동 인식
                - **대용량 파일**: GCS 직접 업로드 탭 사용
                """)

    # 히스토리
    render_history()


def run_dashboard(host: str = "localhost", port: int = 8501):
    """대시보드 실행"""
    import subprocess
    import sys

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        __file__,
        f"--server.address={host}",
        f"--server.port={port}"
    ])


if __name__ == "__main__":
    main()
