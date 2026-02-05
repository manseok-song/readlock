"""Gemini STT 엔진 - Google Gemini 3 Flash 기반 전사 및 화자분리"""

import json
import os
import re
import subprocess
import tempfile
import time
import random
from pathlib import Path
from typing import Optional, List

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import BaseModel

from src.stt.base import STTEngine, TranscriptionResult, Segment
from src.audio.chunker import AudioChunker, AudioChunk, ChunkConfig, merge_transcriptions


# GCS 버킷 설정
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "video-to-text-uploads-causal-binder")

# 청크 분할 임계값 (초)
# - 영상 모드: 30분 (Gemini 45분 제한, 안전 마진)
# - 오디오 모드: 4시간 (Gemini 8.4시간 제한, 안전 마진)
VIDEO_CHUNK_THRESHOLD_SECONDS = 1800   # 30분
AUDIO_CHUNK_THRESHOLD_SECONDS = 14400  # 4시간


class GeminiConfig(BaseModel):
    """Gemini STT 설정"""
    model: str = "gemini-3-flash-preview"  # Gemini 3 Flash (2026-02)
    api_key: Optional[str] = None
    max_retries: int = 3
    timeout: int = 600  # 대용량 파일을 위해 10분으로 증가
    use_gcs: bool = True  # GCS 사용 여부
    enable_chunking: bool = True  # 긴 오디오 자동 분할 활성화
    use_video_mode: bool = False  # 영상 모드 (화면 텍스트 인식 포함)
    # Gemini 3 전용 파라미터
    thinking_level: str = "medium"  # minimal, low, medium, high (화자 분리에 효과적)
    media_resolution: str = "low"  # low, medium, high (TV 콘텐츠는 low로 충분)
    temperature: float = 1.0  # Gemini 3 권장값 (낮으면 예기치 않은 동작)


class GeminiSTT(STTEngine):
    """Gemini 기반 STT 엔진"""

    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self._setup_api()

    def _setup_api(self) -> None:
        """API 설정"""
        api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY 환경변수가 설정되지 않았습니다. "
                ".env 파일에 GEMINI_API_KEY=your-key를 추가하거나 "
                "환경변수로 설정하세요."
            )
        genai.configure(api_key=api_key)

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def supports_diarization(self) -> bool:
        return True

    def _build_prompt(
        self,
        num_speakers: Optional[int],
        language: str,
        proper_nouns: Optional[List[str]] = None,
        use_video_mode: bool = False,
        remove_fillers: bool = False,
        election_debate_mode: bool = False
    ) -> str:
        """전사 프롬프트 생성

        Args:
            num_speakers: 화자 수 힌트
            language: 언어 코드
            proper_nouns: 고유명사/인명 힌트 리스트 (예: ["황금석", "삼성전자", "GPT-4"])
            use_video_mode: 영상 모드 (화면 텍스트 인식 포함)
            remove_fillers: 필러(어, 음, 그) 및 더듬거림 제거 여부
            election_debate_mode: 선거 토론회 모드 (화자를 사회자/후보명으로 구분)
        """
        speaker_hint = ""
        if num_speakers:
            speaker_hint = f"이 오디오에는 약 {num_speakers}명의 화자가 있습니다. "

        # 고유명사 힌트 섹션 (화자 이름 강조)
        proper_noun_section = ""
        if proper_nouns and len(proper_nouns) > 0:
            noun_list = ", ".join(proper_nouns)
            proper_noun_section = f"""
## ⚠️ 화자/고유명사 힌트 (필수 적용!)
다음 이름/용어들이 **이미 확인**되었습니다. **반드시** 아래 표기를 사용하세요:
### 📛 확인된 이름/용어: {noun_list}

### 화자 이름 적용 규칙 (중요!)
1. **발음이 비슷하면 힌트 이름 사용**:
   - 힌트: "박강산" → "박광선", "박강선", "박 강산" 모두 "박강산"으로 표기
   - 힌트: "황금석" → "환금석", "황 금석", "한금석" 모두 "황금석"으로 표기

2. **화자 레이블에 힌트 적용**:
   - 힌트에 인명이 있으면 speaker 필드에 해당 이름 사용
   - 예: 힌트에 "박강산"이 있고, 누군가 "저는 박강산입니다"라고 하면 → speaker: "박강산"

3. **인명 표기 규칙**:
   - 띄어쓰기 없이 붙여서 표기 (예: "박강산", "김철수")
   - 절대로 "박 강산", "박강 산" 처럼 띄어쓰지 말 것

4. **⚠️ 환각 방지 (매우 중요!)**:
   - 확실하지 않은 고유명사는 **"[확인 불가]"**로 표기
   - 발음이 불명확해도 **추측하거나 지어내지 마세요**
   - 힌트에 없는 이름이 들리면 들리는 대로 표기 (지어내지 말 것)
"""

        # 영상 모드: 화면 텍스트를 참고하여 전사 보정
        video_mode_section = ""
        if use_video_mode:
            video_mode_section = """
## 화면 텍스트 참고 (보정용)
이것은 영상 파일입니다. **음성을 텍스트로 변환**하되, 화면에 표시된 텍스트를 **참고**하여 정확도를 높이세요:

1. **화자 이름 확인**: 화면에 화자 이름이 표시되면 해당 이름을 화자 레이블로 사용
   - 예: 화면에 "홍길동 교수"가 보이고 그 사람이 말하면 → speaker: "홍길동"
   - 이름이 안 보이면 "화자1", "화자2" 사용

2. **전문 용어/고유명사 보정**: 화면 자막에 나온 용어나 이름을 참고하여 음성 인식 결과 보정
   - 화면에 "GPT-4o"가 보이는데 음성이 "GPT 포오"로 들리면 → "GPT-4o"로 표기
   - 화면에 "삼성전자"가 보이는데 음성이 "삼성 전자"로 들리면 → "삼성전자"로 표기

3. **메인은 음성**: 기본적으로 음성을 전사하고, 화면 텍스트는 **보정 참고용**
   - 화면 자막을 그대로 복사하지 말고, 실제 발화 내용을 전사
   - 화면 정보는 철자/표기 확인에만 활용
"""

        # 필러 제거 모드: 더듬거림, 필러워드 정리
        filler_removal_section = ""
        if remove_fillers:
            filler_removal_section = """
## 필러 및 더듬거림 제거 (중요!)
전사 시 다음 규칙을 적용하여 **깔끔한 문장**으로 정리하세요:

1. **필러워드 제거**: "어", "음", "그", "저기", "뭐", "이제", "그러니까" 등 의미 없는 추임새 삭제
   - 원본: "어... 그러니까 음... 제가 말씀드리고 싶은 건..."
   - 정리: "제가 말씀드리고 싶은 건..."

2. **더듬거림/반복 정리**: 말을 더듬거나 반복한 부분을 자연스럽게 정리
   - 원본: "그, 그, 그래서 저, 저희가..."
   - 정리: "그래서 저희가..."
   - 원본: "이게 뭐냐면은, 뭐냐면은..."
   - 정리: "이게 뭐냐면..."

3. **의미 보존**: 내용을 지어내거나 바꾸지 말고, 화자가 전달하려던 **원래 의미만 보존**
   - 불필요한 반복과 망설임만 제거
   - 실제 발화 내용은 그대로 유지

4. **문장 완성**: 끊어진 문장은 자연스럽게 이어지도록 정리
   - 원본: "그래서 이게, 아 뭐더라, 이게 중요한 게..."
   - 정리: "그래서 이게 중요한 게..."
"""

        # 선거 토론회 모드: 속기록 스타일 + 정책명 정확 전사
        election_debate_section = ""
        if election_debate_mode:
            # 비디오 모드에서 화면 텍스트 참고 안내
            screen_text_hint = ""
            if use_video_mode:
                screen_text_hint = """
### 📺 화면 텍스트 활용 (비디오 모드)
영상 화면에 표시되는 텍스트를 적극 활용하세요:
- 화면에 나오는 **정책명, 공약, 법안명** → 정확한 표기 참고
- 자막/하단 텍스트에 표시된 **후보 이름, 소속** → 화자 식별에 활용
- 인포그래픽의 **숫자, 날짜, 예산** → 정확한 수치 확인
"""

            election_debate_section = f"""
## 🗳️ 선거 토론회 속기록 모드 (필수!)
{screen_text_hint}
### 1. 속기록 스타일 전사 원칙
**더듬거림, 망설임, 반복을 그대로 유지**하세요. 속기록처럼 있는 그대로 기록합니다:

- ✅ 올바른 예: "어... 그, 그러니까 제가 말씀드리고 싶은 건..."
- ❌ 잘못된 예: "제가 말씀드리고 싶은 건..." (정리됨)
- ✅ 올바른 예: "그, 그, 그래서 저, 저희가..."
- ❌ 잘못된 예: "그래서 저희가..." (더듬거림 제거됨)

### 2. 화자 레이블 규칙
"화자1", "화자2" 대신 **실제 역할과 이름**을 사용하세요:

- **사회자**: 토론 진행자 → speaker: "사회자" 또는 실제 이름
- **후보자**: 영상에서 이름이 언급되거나 화면에 표시되면 해당 이름 사용
  - 예: "기호 1번 홍길동입니다" → speaker: "홍길동"
  - 화면 자막에 "홍길동 후보" 표시 → speaker: "홍길동"
- **이름 모를 때**: "후보1", "후보2"로 시작, 이름 밝혀지면 소급 적용

### 3. 정책명 정확 전사 (핵심!)
**발음이 뭉개져도 정책명은 정확하게** 전사하세요. 맥락과 화면 정보로 추론:

- **정책/법안명**: 화면에 표시된 정확한 명칭 사용
  - 발화: "주거복지법을..." (발음 불명확)
  - 화면: "주거복지기본법" 표시 → "주거복지기본법을..."
- **숫자/예산**: 화면의 인포그래픽 참고하여 정확히
  - 발화: "백억... 아니 천억 예산..." (혼란)
  - 화면: "1,000억 원" 표시 → 화면 기준으로 "1,000억 원 예산..."
- **공약명**: 맥락상 명확한 공약명으로 전사
  - 발화: "그 뭐냐... 청년 정책..." (불명확)
  - 맥락: 청년주거지원정책 논의 중 → "청년주거지원정책..."

### 4. 말투/어투 보존
- "~입니다", "~거든요", "~잖아요" 등 **화자 말투 그대로**
- 사투리, 비격식체 모두 **원본 그대로**
- ⚠️ 절대 문어체로 바꾸지 말 것!

예시:
- 원본: "그래서 저는요, 어... 그 뭐냐, 주거복... 주거복지법을 개정해서요..."
- 정확한 전사: "그래서 저는요, 어... 그 뭐냐, 주거복지기본법을 개정해서요..."
  (더듬거림 유지 + 정책명 정확)
"""

        media_type = "영상" if use_video_mode else "오디오"
        return f"""당신은 전문 전사 시스템입니다. 이 {media_type}를 정확하게 전사하세요.

## 요구사항
1. 언어: {language} (한국어)
2. {speaker_hint}각 화자를 구분하여 레이블링하세요.
3. 타임스탬프를 포함하세요.
4. 결과는 반드시 JSON 형식으로 출력하세요.
{video_mode_section}{filler_removal_section}{election_debate_section}{proper_noun_section}
## 출력 형식 (JSON)
```json
{{
  "segments": [
    {{
      "start": 0.0,
      "end": 3.5,
      "speaker": "사회자",
      "text": "안녕하십니까? 오늘 토론회 사회를 맡은 000입니다."
    }},
    {{
      "start": 3.5,
      "end": 7.2,
      "speaker": "홍길동",
      "text": "안녕하세요. 기호 1번 홍길동입니다."
    }}
  ],
  "num_speakers": 2,
  "language": "ko"
}}
```

## 주의사항
- **중요**: 타임스탬프는 반드시 **초 단위 숫자**로 표시
  - 올바른 예: 12.5, 125.3, 762.0
  - 잘못된 예: "12:42", "1:25", "00:12:42"
  - 12분 42초 = 762초 (12*60 + 42 = 762)
- 화자는 "화자1", "화자2" 형식으로 일관되게 레이블링
- 알아듣기 어려운 부분은 [불명확] 표시
- 비언어적 소리는 (웃음), (박수), (침묵) 등으로 표시
- JSON 외의 텍스트는 출력하지 마세요."""

    def _normalize_timestamp(self, value, audio_duration: float = 0) -> float:
        """타임스탬프 정규화 - 다양한 형식 처리"""
        if isinstance(value, (int, float)):
            ts = float(value)
            # 비정상적으로 큰 값 감지 (예: 1242 대신 12:42의 오해석)
            if audio_duration > 0 and ts > audio_duration * 1.5:
                # MMSS 형식으로 해석 시도 (1242 -> 12분 42초 -> 762초)
                if ts >= 100:
                    minutes = int(ts) // 100
                    seconds = int(ts) % 100
                    converted = minutes * 60 + seconds
                    if converted <= audio_duration * 1.2:
                        print(f"[Gemini] 타임스탬프 보정: {ts} -> {converted}초")
                        return float(converted)
            return ts
        elif isinstance(value, str):
            # "12:42" 또는 "00:12:42" 형식 처리
            if ':' in value:
                parts = value.split(':')
                try:
                    if len(parts) == 2:  # MM:SS
                        return float(parts[0]) * 60 + float(parts[1])
                    elif len(parts) == 3:  # HH:MM:SS
                        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except ValueError:
                    pass
            # 숫자 문자열
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def _parse_response(self, response_text: str, audio_duration: float = 0) -> dict:
        """응답 파싱"""
        # JSON 블록 추출
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # JSON 블록이 없으면 전체 텍스트에서 시도
            json_str = response_text.strip()
            # 마크다운 코드 블록 제거
            if json_str.startswith('```'):
                json_str = re.sub(r'^```\w*\n?', '', json_str)
                json_str = re.sub(r'\n?```$', '', json_str)

        try:
            data = json.loads(json_str)
            # 타임스탬프 정규화
            if "segments" in data:
                for seg in data["segments"]:
                    seg["start"] = self._normalize_timestamp(seg.get("start", 0), audio_duration)
                    seg["end"] = self._normalize_timestamp(seg.get("end", 0), audio_duration)
            return data
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 수동 파싱 시도
            return self._fallback_parse(response_text)

    def _fallback_parse(self, text: str) -> dict:
        """폴백 파싱 - 텍스트에서 대화 추출"""
        segments = []
        lines = text.strip().split('\n')
        current_time = 0.0

        # 패턴: [화자N] 텍스트 또는 화자N: 텍스트
        pattern = re.compile(r'(?:\[?(화자\d+|Speaker\s*\d+)\]?[:\s]+)?(.+)', re.IGNORECASE)

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if match:
                speaker = match.group(1) or "화자1"
                text_content = match.group(2).strip()

                if text_content:
                    # 대략적인 타임스탬프 추정 (단어당 0.3초)
                    word_count = len(text_content.split())
                    duration = max(1.0, word_count * 0.3)

                    segments.append({
                        "start": current_time,
                        "end": current_time + duration,
                        "speaker": speaker,
                        "text": text_content
                    })
                    current_time += duration + 0.2  # 간격

        return {
            "segments": segments,
            "num_speakers": len(set(s["speaker"] for s in segments)),
            "language": "ko"
        }

    def _upload_to_gcs(self, file_path: Path) -> str:
        """파일을 GCS에 업로드하고 gs:// URI 반환"""
        try:
            from google.cloud import storage
            import uuid
            from datetime import datetime

            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)

            # 고유한 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            blob_name = f"{timestamp}_{unique_id}_{file_path.name}"

            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(file_path))

            gs_uri = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
            print(f"[GCS] 업로드 완료: {gs_uri}")
            return gs_uri

        except Exception as e:
            print(f"[GCS] 업로드 실패: {e}, 기본 방식으로 전환")
            return None

    def _delete_from_gcs(self, gs_uri: str) -> None:
        """GCS에서 파일 삭제"""
        try:
            from google.cloud import storage

            # gs://bucket/path 형식에서 blob 이름 추출
            if gs_uri.startswith(f"gs://{GCS_BUCKET_NAME}/"):
                blob_name = gs_uri[len(f"gs://{GCS_BUCKET_NAME}/"):]
                client = storage.Client()
                bucket = client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(blob_name)
                blob.delete()
                print(f"[GCS] 삭제 완료: {blob_name}")
        except Exception as e:
            print(f"[GCS] 삭제 실패 (무시): {e}")

    def _get_audio_duration(self, audio_path: Path) -> float:
        """오디오 파일 길이 조회 (초)"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return 0.0  # 실패 시 0 반환
            return float(result.stdout.strip())
        except FileNotFoundError:
            # ffprobe가 설치되지 않은 경우
            print("[Gemini] ffprobe 없음 - 파일 길이 추정 생략")
            return 0.0
        except (subprocess.TimeoutExpired, ValueError, Exception) as e:
            print(f"[Gemini] 파일 길이 조회 실패: {e}")
            return 0.0

    async def _call_with_retry(
        self,
        model,
        audio_input,
        prompt: str,
        audio_duration: float
    ):
        """
        Gemini API 호출 (429 Rate Limit 재시도 로직 포함)

        Args:
            model: Gemini GenerativeModel 인스턴스
            audio_input: 오디오 파일 또는 GCS URI
            prompt: 전사 프롬프트
            audio_duration: 오디오 길이 (타임스탬프 보정용)

        Returns:
            Gemini API 응답
        """
        max_retries = self.config.max_retries
        base_delay = 30  # 기본 대기 시간 (초)

        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    [audio_input, prompt],
                    generation_config=genai.GenerationConfig(
                        temperature=self.config.temperature,  # Gemini 3: 1.0 권장
                        max_output_tokens=65536,  # 최대 출력 토큰
                    ),
                    request_options={"timeout": self.config.timeout}
                )
                return response

            except google_exceptions.ResourceExhausted as e:
                # 429 Rate Limit 에러
                if attempt < max_retries - 1:
                    # 지수 백오프 + 지터
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 10)
                    print(f"[Gemini] ⚠️ Rate limit (429) - {delay:.0f}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"[Gemini] ❌ Rate limit 초과 - 최대 재시도 횟수 도달")
                    raise RuntimeError(
                        f"Gemini API Rate Limit 초과. {max_retries}회 재시도 후에도 실패. "
                        "잠시 후 다시 시도하거나, API 할당량을 확인하세요."
                    ) from e

            except google_exceptions.DeadlineExceeded as e:
                # 타임아웃 에러
                if attempt < max_retries - 1:
                    delay = 10 * (attempt + 1)
                    print(f"[Gemini] ⚠️ 타임아웃 - {delay}초 후 재시도 ({attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Gemini API 타임아웃. 오디오가 너무 길거나 네트워크 문제일 수 있습니다."
                    ) from e

            except Exception as e:
                # 기타 에러는 바로 raise
                error_str = str(e).lower()
                if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 10)
                        print(f"[Gemini] ⚠️ Rate limit 감지 - {delay:.0f}초 후 재시도 ({attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise RuntimeError(f"API Rate Limit 초과: {e}") from e
                else:
                    raise

    async def transcribe(
        self,
        audio_path: str,
        language: str = "ko",
        num_speakers: Optional[int] = None,
        proper_nouns: Optional[List[str]] = None,
        use_video_mode: bool = False,
        original_video_path: Optional[str] = None,
        remove_fillers: bool = False,
        election_debate_mode: bool = False,
    ) -> TranscriptionResult:
        """
        Gemini를 사용하여 오디오/영상 전사

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드
            num_speakers: 화자 수 힌트
            proper_nouns: 고유명사/인명 힌트 리스트 (예: ["황금석", "삼성전자"])
            use_video_mode: 영상 모드 (화면 텍스트 인식 포함)
            original_video_path: 원본 영상 파일 경로 (영상 모드일 때 사용)
            remove_fillers: 필러(어, 음) 및 더듬거림 제거 여부
            election_debate_mode: 선거 토론회 모드 (사회자/후보명 구분, 정책 정확 전사)

        Returns:
            TranscriptionResult 객체
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        # 영상 모드 설정 (config 또는 파라미터)
        use_video = use_video_mode or self.config.use_video_mode

        # 영상 모드일 때 원본 영상 사용
        media_path = audio_path
        if use_video and original_video_path:
            video_path = Path(original_video_path)
            if video_path.exists() and video_path.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                media_path = video_path
                print(f"[Gemini] 🎬 영상 모드 활성화 - 화면 텍스트 인식 포함")

        # 파일 크기 및 길이 확인
        file_size_mb = media_path.stat().st_size / (1024 * 1024)
        audio_duration = self._get_audio_duration(media_path)
        print(f"[Gemini] 파일 크기: {file_size_mb:.1f} MB, 길이: {audio_duration:.0f}초 ({audio_duration/60:.1f}분)")

        if proper_nouns:
            print(f"[Gemini] 고유명사 힌트: {', '.join(proper_nouns)}")

        if remove_fillers:
            print(f"[Gemini] 🧹 필러 제거 모드 활성화")

        if election_debate_mode:
            print(f"[Gemini] 🗳️ 선거 토론회 모드 활성화 (사회자/후보명 구분)")

        # 청크 분할 여부 결정 (영상/오디오 모드에 따라 다른 임계값)
        if use_video:
            # 영상 모드: 45분 제한 → 30분 임계값
            chunk_threshold = VIDEO_CHUNK_THRESHOLD_SECONDS
            needs_chunking = (
                self.config.enable_chunking and
                audio_duration > chunk_threshold
            )
            if needs_chunking:
                print(f"[Gemini] 🎬 영상 분할 모드 - {audio_duration/60:.0f}분 영상을 청크로 분할 (영상 모드 유지)")
                return await self._transcribe_with_video_chunks(
                    media_path, language, num_speakers, proper_nouns, remove_fillers, election_debate_mode
                )
        else:
            # 오디오 모드: 8.4시간 제한 → 4시간 임계값
            chunk_threshold = AUDIO_CHUNK_THRESHOLD_SECONDS
            needs_chunking = (
                self.config.enable_chunking and
                (audio_duration > chunk_threshold or file_size_mb > 1000)  # 1GB 이상
            )
            if needs_chunking:
                print(f"[Gemini] 🎵 긴 오디오 감지 ({audio_duration/3600:.1f}시간) - 청크 분할 처리")
                return await self._transcribe_with_chunks(audio_path, language, num_speakers, proper_nouns, remove_fillers, election_debate_mode)

        # 일반 전사 (분할 불필요)
        return await self._transcribe_single(
            media_path, language, num_speakers, proper_nouns, use_video, remove_fillers, election_debate_mode
        )

    async def _transcribe_with_chunks(
        self,
        audio_path: Path,
        language: str,
        num_speakers: Optional[int],
        proper_nouns: Optional[List[str]] = None,
        remove_fillers: bool = False,
        election_debate_mode: bool = False
    ) -> TranscriptionResult:
        """청크 분할을 사용한 긴 오디오 전사"""
        # 청크 분할 설정
        chunk_config = ChunkConfig(
            target_chunk_duration=600,  # 목표 10분
            max_chunk_duration=900,     # 최대 15분
            silence_threshold_db=-40,
            min_silence_duration=0.5,
            overlap_duration=2.0
        )
        chunker = AudioChunker(chunk_config)

        # 임시 디렉토리에 청크 생성
        with tempfile.TemporaryDirectory(prefix="vtt_chunks_") as tmp_dir:
            chunks = chunker.split_audio(audio_path, tmp_dir)
            total_chunks = len(chunks)
            print(f"[Gemini] {total_chunks}개 청크로 분할됨")

            # 화자 이름 누적 (청크 간 전달용)
            discovered_speakers: set = set()
            if proper_nouns:
                discovered_speakers.update(proper_nouns)

            # 각 청크 전사
            chunk_results = []
            for i, chunk in enumerate(chunks):
                print(f"[Gemini] ━━━ 청크 {i+1}/{total_chunks} 전사 시작 ━━━")
                print(f"[Gemini]   📍 구간: {chunk.start_time:.0f}초 ~ {chunk.end_time:.0f}초 ({chunk.duration:.0f}초)")

                # 현재까지 발견된 화자 이름을 힌트로 전달
                current_hints = list(discovered_speakers) if discovered_speakers else None
                if current_hints:
                    print(f"[Gemini]   👥 화자 힌트: {', '.join(current_hints)}")

                try:
                    result = await self._transcribe_single(
                        chunk.path, language, num_speakers, current_hints,
                        False, remove_fillers, election_debate_mode
                    )

                    # dict 형태로 변환
                    chunk_result = {
                        "segments": [
                            {
                                "start": seg.start,
                                "end": seg.end,
                                "text": seg.text,
                                "speaker": seg.speaker
                            }
                            for seg in result.segments
                        ],
                        "language": result.language,
                        "num_speakers": result.num_speakers
                    }
                    chunk_results.append(chunk_result)

                    # 새로 발견된 화자 이름 추출 (다음 청크에 전달)
                    for seg in result.segments:
                        if seg.speaker and seg.speaker not in ["화자1", "화자2", "화자3", "화자4", "화자5",
                                                                "후보1", "후보2", "후보3", "후보4", "후보5",
                                                                "사회자", "진행자", "Unknown"]:
                            if seg.speaker not in discovered_speakers:
                                discovered_speakers.add(seg.speaker)
                                print(f"[Gemini]   🆕 새 화자 발견: {seg.speaker}")

                    print(f"[Gemini] ✅ 청크 {i+1}/{total_chunks} 완료 ({len(result.segments)}개 세그먼트)")

                except Exception as e:
                    print(f"[Gemini] ❌ 청크 {i+1} 전사 실패: {e}")
                    chunk_results.append({"segments": [], "language": language})

            # 결과 병합
            merged = merge_transcriptions(chunk_results, chunks, chunk_config.overlap_duration)

            # Segment 객체 리스트 생성
            segments = []
            for seg_data in merged.get("segments", []):
                segments.append(Segment(
                    start=float(seg_data.get("start", 0)),
                    end=float(seg_data.get("end", 0)),
                    text=seg_data.get("text", ""),
                    speaker=seg_data.get("speaker"),
                    confidence=None
                ))

            # 전체 길이 계산
            total_duration = segments[-1].end if segments else 0.0

            return TranscriptionResult(
                segments=segments,
                language=merged.get("language", language),
                duration=total_duration,
                num_speakers=merged.get("num_speakers", 1),
                engine=self.name,
                model=self.config.model
            )

    async def _transcribe_with_video_chunks(
        self,
        video_path: Path,
        language: str,
        num_speakers: Optional[int],
        proper_nouns: Optional[List[str]] = None,
        remove_fillers: bool = False,
        election_debate_mode: bool = False
    ) -> TranscriptionResult:
        """영상 분할을 사용한 전사 (영상 모드 유지)

        영상을 20분 단위로 분할하여 각 청크를 영상 모드로 처리.
        화면 텍스트 인식을 유지하면서 45분 제한을 준수.
        """
        # 영상 길이 확인
        video_duration = self._get_audio_duration(video_path)
        target_chunk_duration = 1200  # 20분 (45분 제한의 안전 마진)

        # 청크 수 계산
        num_chunks = max(1, int(video_duration / target_chunk_duration) + 1)
        chunk_duration = video_duration / num_chunks

        print(f"[Gemini] 🎬 영상 {num_chunks}개 청크로 분할 (각 {chunk_duration/60:.1f}분)")

        # 임시 디렉토리에 영상 청크 생성
        with tempfile.TemporaryDirectory(prefix="vtt_video_chunks_") as tmp_dir:
            video_chunks = []

            # FFmpeg로 영상 분할
            for i in range(num_chunks):
                start_time = i * chunk_duration
                # 마지막 청크는 끝까지
                end_time = min((i + 1) * chunk_duration, video_duration)
                duration = end_time - start_time

                chunk_path = Path(tmp_dir) / f"chunk_{i:03d}{video_path.suffix}"

                # FFmpeg 영상 분할 명령
                cmd = [
                    "ffmpeg",
                    "-i", str(video_path),
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-c", "copy",  # 빠른 복사 (재인코딩 없음)
                    "-y",
                    str(chunk_path)
                ]

                try:
                    subprocess.run(cmd, capture_output=True, timeout=300, check=True)
                    video_chunks.append({
                        "path": chunk_path,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "index": i
                    })
                    print(f"[Gemini]   ✅ 청크 {i+1}/{num_chunks}: {start_time/60:.1f}분 ~ {end_time/60:.1f}분")
                except subprocess.CalledProcessError as e:
                    print(f"[Gemini]   ❌ 청크 {i+1} 분할 실패: {e}")
                    continue

            if not video_chunks:
                raise RuntimeError("영상 분할 실패 - 청크가 생성되지 않음")

            # 화자 이름 누적
            discovered_speakers: set = set()
            if proper_nouns:
                discovered_speakers.update(proper_nouns)

            # 각 영상 청크 전사 (영상 모드 유지!)
            chunk_results = []
            for chunk in video_chunks:
                print(f"[Gemini] ━━━ 영상 청크 {chunk['index']+1}/{len(video_chunks)} 전사 시작 ━━━")
                print(f"[Gemini]   📍 구간: {chunk['start_time']/60:.1f}분 ~ {chunk['end_time']/60:.1f}분")

                current_hints = list(discovered_speakers) if discovered_speakers else None

                try:
                    # 영상 모드 유지! (use_video_mode=True)
                    result = await self._transcribe_single(
                        chunk["path"], language, num_speakers, current_hints,
                        True,  # 🎬 영상 모드 유지
                        remove_fillers, election_debate_mode
                    )

                    # 타임스탬프 오프셋 적용
                    chunk_result = {
                        "segments": [
                            {
                                "start": seg.start + chunk["start_time"],  # 원본 기준으로 변환
                                "end": seg.end + chunk["start_time"],
                                "text": seg.text,
                                "speaker": seg.speaker
                            }
                            for seg in result.segments
                        ],
                        "language": result.language,
                        "num_speakers": result.num_speakers
                    }
                    chunk_results.append(chunk_result)

                    # 새 화자 발견 시 추가
                    for seg in result.segments:
                        if seg.speaker and seg.speaker not in ["화자1", "화자2", "화자3", "화자4", "화자5",
                                                                "후보1", "후보2", "사회자", "진행자", "Unknown"]:
                            if seg.speaker not in discovered_speakers:
                                discovered_speakers.add(seg.speaker)
                                print(f"[Gemini]   🆕 새 화자 발견: {seg.speaker}")

                    print(f"[Gemini] ✅ 청크 {chunk['index']+1} 완료 ({len(result.segments)}개 세그먼트)")

                except Exception as e:
                    print(f"[Gemini] ❌ 청크 {chunk['index']+1} 전사 실패: {e}")
                    chunk_results.append({"segments": [], "language": language})

            # 결과 병합 (중복 제거 로직 적용)
            merged_segments = []
            for result in chunk_results:
                merged_segments.extend(result.get("segments", []))

            # 타임스탬프 기준 정렬
            merged_segments.sort(key=lambda x: x["start"])

            # Segment 객체 리스트 생성
            segments = [
                Segment(
                    start=float(seg.get("start", 0)),
                    end=float(seg.get("end", 0)),
                    text=seg.get("text", ""),
                    speaker=seg.get("speaker"),
                    confidence=None
                )
                for seg in merged_segments
            ]

            total_duration = segments[-1].end if segments else 0.0

            return TranscriptionResult(
                segments=segments,
                language=language,
                duration=total_duration,
                num_speakers=len(discovered_speakers) if discovered_speakers else 1,
                engine=self.name,
                model=self.config.model
            )

    async def _transcribe_single(
        self,
        audio_path: Path,
        language: str,
        num_speakers: Optional[int],
        proper_nouns: Optional[List[str]] = None,
        use_video_mode: bool = False,
        remove_fillers: bool = False,
        election_debate_mode: bool = False
    ) -> TranscriptionResult:
        """단일 오디오/영상 파일 전사 (청크 분할 없음) - 429 에러 재시도 포함"""
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        audio_duration = self._get_audio_duration(audio_path)  # 타임스탬프 보정용

        media_file = None

        # Files API 사용 (GCS 방식 비활성화 - API 호환성 문제)
        print(f"[Gemini] Files API 업로드 중... ({file_size_mb:.1f} MB)")
        media_file = genai.upload_file(str(audio_path))

        # 파일이 ACTIVE 상태가 될 때까지 대기
        while media_file.state.name == "PROCESSING":
            print(f"[Gemini] 파일 처리 중... (상태: {media_file.state.name})")
            time.sleep(2)
            media_file = genai.get_file(media_file.name)

        if media_file.state.name != "ACTIVE":
            raise RuntimeError(f"파일 처리 실패: {media_file.state.name}")

        print(f"[Gemini] 파일 준비 완료 (상태: ACTIVE)")
        media_input = media_file

        # 모델 생성 및 전사
        model = genai.GenerativeModel(self.config.model)
        prompt = self._build_prompt(num_speakers, language, proper_nouns, use_video_mode, remove_fillers, election_debate_mode)

        # 전사 요청 (429 재시도 로직 포함)
        mode_str = "영상 모드 (화면 참고)" if use_video_mode else "오디오 모드"
        print(f"[Gemini] 전사 시작... ({mode_str})")
        response = await self._call_with_retry(
            model, media_input, prompt, audio_duration
        )
        print(f"[Gemini] 전사 완료")

        # 응답 파싱 (오디오 길이 전달하여 타임스탬프 보정)
        result_data = self._parse_response(response.text, audio_duration)

        # Segment 객체 리스트 생성
        segments = []
        for seg_data in result_data.get("segments", []):
            segments.append(Segment(
                start=float(seg_data.get("start", 0)),
                end=float(seg_data.get("end", 0)),
                text=seg_data.get("text", ""),
                speaker=seg_data.get("speaker"),
                confidence=seg_data.get("confidence")
            ))

        # 파일 정리
        if media_file:
            try:
                genai.delete_file(media_file.name)
            except Exception:
                pass  # 삭제 실패해도 무시

        # 전체 길이 계산
        total_duration = segments[-1].end if segments else 0.0

        return TranscriptionResult(
            segments=segments,
            language=result_data.get("language", language),
            duration=total_duration,
            num_speakers=result_data.get("num_speakers", 1),
            engine=self.name,
            model=self.config.model
        )

    def _get_mime_type(self, file_path: Path) -> str:
        """파일 확장자에 따른 MIME 타입 반환"""
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
        }
        return mime_types.get(file_path.suffix.lower(), "audio/mpeg")

    async def health_check(self) -> bool:
        """API 연결 상태 확인"""
        try:
            model = genai.GenerativeModel(self.config.model)
            response = model.generate_content("Hello")
            return bool(response.text)
        except Exception:
            return False
