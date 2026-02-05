"""GCS 클라이언트 직접 업로드 컴포넌트 (간소화 버전)

브라우저 JavaScript에서 GCS로 직접 업로드 (Cloud Run 우회).
파일 선택 → 자동 URL 생성 → 바로 업로드
"""

import html
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path
from typing import Optional

# GCS Helper import
try:
    from src.storage.gcs import get_gcs_helper
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


def get_signed_upload_url(filename: str) -> Optional[dict]:
    """업로드용 Signed URL 생성"""
    if not GCS_AVAILABLE:
        return None

    try:
        gcs = get_gcs_helper()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = Path(filename).name
        blob_name = f"uploads/{timestamp}_{unique_id}_{safe_filename}"

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

        result = gcs.generate_upload_signed_url(
            blob_name=blob_name,
            content_type=content_type,
            expiration_minutes=60
        )

        return result

    except Exception as e:
        print(f"[GCS] Signed URL 생성 실패: {e}")
        return None


def render_client_direct_upload() -> Optional[str]:
    """클라이언트 직접 업로드 UI (간소화)

    파일 선택 → 자동 업로드 → 완료

    Returns:
        GCS URI if upload successful, None otherwise
    """
    if not GCS_AVAILABLE:
        st.warning("GCS 설정이 필요합니다")
        return None

    # 세션 상태 초기화
    if "client_upload_gs_uri" not in st.session_state:
        st.session_state.client_upload_gs_uri = None

    st.markdown("""
    **대용량 파일 직접 업로드** - 파일이 브라우저에서 GCS로 직접 업로드됩니다.

    **지원:** MP4, MKV, AVI, MOV, MP3, WAV, M4A, FLAC (최대 2GB)
    """)

    # 이미 업로드된 파일이 있는 경우
    if st.session_state.get("client_upload_gs_uri"):
        gs_uri = st.session_state.client_upload_gs_uri
        st.success(f"파일 준비 완료")
        st.code(gs_uri)

        if st.button("다른 파일 업로드", key="reset_upload"):
            st.session_state.client_upload_gs_uri = None
            st.rerun()

        return gs_uri

    # 미리 여러 확장자에 대한 Signed URL 생성
    signed_urls = {}
    extensions = [".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a", ".flac"]

    for ext in extensions:
        url_info = get_signed_upload_url(f"upload{ext}")
        if url_info:
            signed_urls[ext] = {
                "upload_url": url_info["upload_url"],
                "gs_uri": url_info["gs_uri"],
                "content_type": url_info["content_type"],
            }

    if not signed_urls:
        st.error("Signed URL 생성 실패")
        return None

    # JSON으로 변환 (JavaScript에서 사용)
    signed_urls_json = json.dumps(signed_urls)

    # JavaScript 업로드 컴포넌트
    upload_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .container {{
                padding: 10px;
            }}
            .drop-zone {{
                border: 2px dashed #666;
                border-radius: 8px;
                padding: 30px 15px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s;
                background: #1a1a1a;
            }}
            .drop-zone:hover {{
                border-color: #FF4B4B;
                background: #2a1a1a;
            }}
            .drop-zone.dragover {{
                border-color: #FF4B4B;
                background: #3a1a1a;
            }}
            .drop-zone-text {{
                color: #aaa;
                font-size: 14px;
            }}
            .file-input {{
                display: none;
            }}
            .progress {{
                width: 100%;
                height: 8px;
                background: #333;
                border-radius: 4px;
                overflow: hidden;
                margin: 15px 0;
                display: none;
            }}
            .progress-bar {{
                height: 100%;
                background: linear-gradient(90deg, #FF4B4B, #FF6B6B);
                width: 0%;
                transition: width 0.2s;
            }}
            .status {{
                padding: 8px 12px;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 13px;
                display: none;
            }}
            .status.uploading {{
                display: block;
                background: #1a3a5c;
                color: #7cb3e8;
            }}
            .status.success {{
                display: block;
                background: #1a3c1a;
                color: #7ce87c;
            }}
            .status.error {{
                display: block;
                background: #3c1a1a;
                color: #e87c7c;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="drop-zone" id="dropZone">
                <div class="drop-zone-text">
                    클릭하거나 파일을 드래그하세요
                </div>
            </div>
            <input type="file" id="fileInput" class="file-input"
                   accept=".mp4,.mkv,.avi,.mov,.mp3,.wav,.m4a,.flac">

            <div class="progress" id="progress">
                <div class="progress-bar" id="progressBar"></div>
            </div>

            <div class="status" id="status"></div>
        </div>

        <script>
            const SIGNED_URLS = {signed_urls_json};

            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const progress = document.getElementById('progress');
            const progressBar = document.getElementById('progressBar');
            const status = document.getElementById('status');

            // 클릭으로 파일 선택
            dropZone.addEventListener('click', () => fileInput.click());

            // 드래그 앤 드롭
            dropZone.addEventListener('dragover', (e) => {{
                e.preventDefault();
                dropZone.classList.add('dragover');
            }});

            dropZone.addEventListener('dragleave', () => {{
                dropZone.classList.remove('dragover');
            }});

            dropZone.addEventListener('drop', (e) => {{
                e.preventDefault();
                dropZone.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {{
                    handleFile(e.dataTransfer.files[0]);
                }}
            }});

            // 파일 선택
            fileInput.addEventListener('change', (e) => {{
                if (e.target.files.length > 0) {{
                    handleFile(e.target.files[0]);
                }}
            }});

            async function handleFile(file) {{
                // 확장자 확인
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                const urlInfo = SIGNED_URLS[ext];

                if (!urlInfo) {{
                    showStatus('error', '지원하지 않는 파일 형식입니다');
                    return;
                }}

                // 크기 확인 (2GB)
                if (file.size > 2 * 1024 * 1024 * 1024) {{
                    showStatus('error', '파일 크기가 2GB를 초과합니다');
                    return;
                }}

                // 업로드 시작
                const sizeMB = (file.size / 1024 / 1024).toFixed(1);
                showStatus('uploading', file.name + ' (' + sizeMB + ' MB) 업로드 중...');
                progress.style.display = 'block';
                dropZone.style.display = 'none';

                try {{
                    const xhr = new XMLHttpRequest();

                    xhr.upload.onprogress = (e) => {{
                        if (e.lengthComputable) {{
                            const percent = (e.loaded / e.total) * 100;
                            progressBar.style.width = percent + '%';
                        }}
                    }};

                    xhr.onload = () => {{
                        if (xhr.status >= 200 && xhr.status < 300) {{
                            progressBar.style.width = '100%';
                            showStatus('success', '업로드 완료! 아래 버튼을 클릭하세요.');

                            // 결과를 부모 창에 전달
                            window.parent.postMessage({{
                                type: 'gcs_upload_complete',
                                gs_uri: urlInfo.gs_uri,
                                filename: file.name
                            }}, '*');
                        }} else {{
                            showStatus('error', '업로드 실패: HTTP ' + xhr.status);
                            dropZone.style.display = 'block';
                        }}
                    }};

                    xhr.onerror = () => {{
                        showStatus('error', '네트워크 오류');
                        dropZone.style.display = 'block';
                    }};

                    xhr.open('PUT', urlInfo.upload_url, true);
                    xhr.setRequestHeader('Content-Type', urlInfo.content_type);
                    xhr.send(file);

                }} catch (error) {{
                    showStatus('error', '오류: ' + error.message);
                    dropZone.style.display = 'block';
                }}
            }}

            function showStatus(type, message) {{
                status.className = 'status ' + type;
                status.textContent = message;
            }}
        </script>
    </body>
    </html>
    '''

    # 컴포넌트 렌더링
    components.html(upload_html, height=180)

    # 업로드 완료 확인 버튼
    st.divider()

    # GCS에서 최근 업로드 파일 확인
    col1, col2 = st.columns(2)

    with col1:
        if st.button("업로드 완료 확인", type="primary", use_container_width=True):
            # 최근 업로드된 파일 확인 (signed_urls의 gs_uri 확인)
            try:
                gcs = get_gcs_helper()
                for ext, info in signed_urls.items():
                    blob_name = info["gs_uri"].replace(f"gs://{gcs.bucket_name}/", "")
                    blob = gcs.bucket.blob(blob_name)
                    if blob.exists():
                        st.session_state.client_upload_gs_uri = info["gs_uri"]
                        st.session_state.gcs_uri = info["gs_uri"]
                        st.rerun()

                st.warning("업로드된 파일을 찾을 수 없습니다. 업로드를 완료한 후 다시 클릭하세요.")
            except Exception as e:
                st.error(f"확인 실패: {e}")

    with col2:
        if st.button("새로고침", use_container_width=True):
            st.rerun()

    return None
