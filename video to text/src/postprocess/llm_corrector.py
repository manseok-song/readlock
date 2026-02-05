"""LLM 기반 전사 교정 모듈 - Claude/Gemini 3단계 Chain-of-Thought + RAG 통합"""

import asyncio
import json
import os
import re
from typing import Optional, Literal, TYPE_CHECKING

from pydantic import BaseModel

from src.stt.base import TranscriptionResult, Segment

if TYPE_CHECKING:
    from src.rag.knowledge_builder import KnowledgeBase


class LLMCorrectorConfig(BaseModel):
    """LLM 교정 설정"""
    provider: Literal["anthropic", "gemini"] = "gemini"  # 기본값을 Gemini로 변경
    model: Optional[str] = None  # None이면 provider별 기본 모델 사용
    api_key: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.3
    batch_size: int = 10  # 한 번에 처리할 세그먼트 수

    def get_model(self) -> str:
        """provider별 기본 모델 반환"""
        if self.model:
            return self.model
        if self.provider == "gemini":
            return "gemini-2.5-pro"  # Flash 대신 Pro 사용
        return "claude-3-5-sonnet-20241022"


class CorrectionResult(BaseModel):
    """교정 결과"""
    original: str
    corrected: str
    changes: list[str]  # 변경 내역
    confidence: float


class LLMCorrector:
    """
    LLM 기반 3단계 Chain-of-Thought 전사 교정기

    지원 provider:
    - gemini: Google Gemini (GEMINI_API_KEY) - 기본값
    - anthropic: Anthropic Claude (ANTHROPIC_API_KEY)

    작동 원리 (WER 11-21% 감소 효과):
    1. 맥락 분석: 전체 대화 흐름과 주제 파악
    2. 오류 감지: 문법, 맞춤법, 고유명사, 동음이의어 오류 식별
    3. 교정 적용: 자연스러운 한국어로 수정
    """

    def __init__(self, config: Optional[LLMCorrectorConfig] = None):
        self.config = config or LLMCorrectorConfig()
        self._client = None
        self._gemini_model = None

    def _get_client(self):
        """LLM 클라이언트 가져오기"""
        if self._client is not None:
            return self._client

        if self.config.provider == "gemini":
            return self._get_gemini_client()
        else:
            return self._get_anthropic_client()

    def _get_gemini_client(self):
        """Gemini 클라이언트 가져오기"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError(
                "google-generativeai 패키지가 설치되지 않았습니다. "
                "'pip install google-generativeai' 실행 필요"
            )

        api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY 환경변수가 설정되지 않았습니다. "
                ".env 파일에 추가하거나 config에 api_key를 전달하세요."
            )

        genai.configure(api_key=api_key)
        self._gemini_model = genai.GenerativeModel(self.config.get_model())
        self._client = "gemini"
        return self._client

    def _get_anthropic_client(self):
        """Anthropic 클라이언트 가져오기"""
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic 패키지가 설치되지 않았습니다. "
                "'pip install anthropic' 실행 필요"
            )

        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다. "
                ".env 파일에 추가하거나 config에 api_key를 전달하세요."
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _call_llm(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.3) -> str:
        """LLM 호출 (provider에 따라 분기)"""
        self._get_client()

        if self.config.provider == "gemini":
            response = self._gemini_model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            return response.text
        else:
            response = self._client.messages.create(
                model=self.config.get_model(),
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

    def _build_context_prompt(self, segments: list[Segment]) -> str:
        """1단계: 맥락 분석 프롬프트"""
        text = "\n".join([
            f"[{seg.speaker or '화자'}] {seg.text}"
            for seg in segments
        ])

        return f"""다음은 음성 인식으로 전사된 한국어 대화입니다.
전체 맥락을 분석하여 다음을 파악하세요:

1. 대화 주제/분야
2. 화자들의 관계 (토론, 인터뷰, 일상대화 등)
3. 전문 용어나 고유명사 후보
4. 대화 톤과 격식 수준

전사 내용:
{text}

JSON 형식으로 분석 결과를 출력하세요:
```json
{{
  "topic": "대화 주제",
  "domain": "분야 (정치/경제/기술/일상 등)",
  "formality": "격식 수준 (formal/informal/mixed)",
  "key_terms": ["전문용어1", "전문용어2"],
  "proper_nouns": ["고유명사1", "고유명사2"],
  "speaker_relationship": "화자 관계 설명"
}}
```"""

    def _build_error_detection_prompt(
        self,
        segment: Segment,
        context: dict
    ) -> str:
        """2단계: 오류 감지 프롬프트"""
        return f"""당신은 한국어 전사 교정 전문가입니다.

맥락 정보:
- 주제: {context.get('topic', '알 수 없음')}
- 분야: {context.get('domain', '일반')}
- 전문용어: {', '.join(context.get('key_terms', []))}
- 고유명사: {', '.join(context.get('proper_nouns', []))}

다음 전사 텍스트에서 오류를 찾아주세요:
화자: {segment.speaker or '알 수 없음'}
텍스트: "{segment.text}"

오류 유형:
1. 맞춤법 오류 (띄어쓰기, 철자)
2. 문법 오류 (조사, 어미)
3. 동음이의어 오류 (문맥에 맞지 않는 단어)
4. 고유명사 오류 (잘못 인식된 이름/용어)
5. 누락/추가 (빠지거나 잘못 추가된 음절)

JSON 형식으로 출력:
```json
{{
  "errors": [
    {{
      "type": "오류유형",
      "original": "원본",
      "suggested": "수정",
      "reason": "이유"
    }}
  ],
  "confidence": 0.0~1.0
}}
```
오류가 없으면 빈 배열을 반환하세요."""

    def _build_correction_prompt(
        self,
        segment: Segment,
        errors: list[dict]
    ) -> str:
        """3단계: 교정 적용 프롬프트"""
        error_list = "\n".join([
            f"- {e['type']}: '{e['original']}' → '{e['suggested']}' ({e['reason']})"
            for e in errors
        ])

        return f"""다음 텍스트에 감지된 오류를 적용하여 교정하세요.

원본: "{segment.text}"

감지된 오류:
{error_list if error_list else "없음"}

교정 규칙:
1. 의미가 변하지 않도록 최소한의 수정만 적용
2. 자연스러운 한국어가 되도록 수정
3. 확실하지 않은 수정은 하지 않음
4. 원본 화자의 말투와 톤 유지

JSON 형식으로 출력:
```json
{{
  "corrected": "교정된 텍스트",
  "changes": ["변경1", "변경2"],
  "confidence": 0.0~1.0
}}
```"""

    def _parse_json_response(self, text: str) -> dict:
        """JSON 응답 파싱"""
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}

    async def _analyze_context(self, segments: list[Segment]) -> dict:
        """1단계: 맥락 분석"""
        prompt = self._build_context_prompt(segments)
        response_text = self._call_llm(prompt, max_tokens=1024, temperature=0.3)
        return self._parse_json_response(response_text)

    async def _detect_errors(
        self,
        segment: Segment,
        context: dict
    ) -> list[dict]:
        """2단계: 오류 감지"""
        prompt = self._build_error_detection_prompt(segment, context)
        response_text = self._call_llm(prompt, max_tokens=1024, temperature=0.2)
        result = self._parse_json_response(response_text)
        return result.get("errors", [])

    async def _apply_correction(
        self,
        segment: Segment,
        errors: list[dict]
    ) -> CorrectionResult:
        """3단계: 교정 적용"""
        if not errors:
            return CorrectionResult(
                original=segment.text,
                corrected=segment.text,
                changes=[],
                confidence=1.0
            )

        prompt = self._build_correction_prompt(segment, errors)
        response_text = self._call_llm(prompt, max_tokens=1024, temperature=0.1)
        result = self._parse_json_response(response_text)

        return CorrectionResult(
            original=segment.text,
            corrected=result.get("corrected", segment.text),
            changes=result.get("changes", []),
            confidence=result.get("confidence", 0.8)
        )

    async def correct(
        self,
        transcription: TranscriptionResult,
        context_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """
        전사 결과 교정

        Args:
            transcription: 원본 전사 결과
            context_hint: 추가 문맥 힌트 (주제, 화자 정보 등)

        Returns:
            교정된 TranscriptionResult
        """
        # 1단계: 맥락 분석
        context = await self._analyze_context(transcription.segments)
        if context_hint:
            context["hint"] = context_hint

        # 2-3단계: 배치 처리
        corrected_segments = []

        for i in range(0, len(transcription.segments), self.config.batch_size):
            batch = transcription.segments[i:i + self.config.batch_size]

            # 병렬로 오류 감지 및 교정
            tasks = []
            for seg in batch:
                tasks.append(self._process_segment(seg, context))

            results = await asyncio.gather(*tasks)

            for seg, correction in zip(batch, results):
                corrected_segments.append(Segment(
                    start=seg.start,
                    end=seg.end,
                    text=correction.corrected,
                    speaker=seg.speaker,
                    confidence=correction.confidence
                ))

        return TranscriptionResult(
            segments=corrected_segments,
            language=transcription.language,
            duration=transcription.duration,
            num_speakers=transcription.num_speakers,
            engine=f"{transcription.engine}+llm_corrected",
            model=transcription.model
        )

    async def _process_segment(
        self,
        segment: Segment,
        context: dict
    ) -> CorrectionResult:
        """단일 세그먼트 처리"""
        # 2단계: 오류 감지
        errors = await self._detect_errors(segment, context)

        # 3단계: 교정 적용
        return await self._apply_correction(segment, errors)

    def correct_sync(
        self,
        transcription: TranscriptionResult,
        context_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """동기 버전 (직접 호출용)"""
        return asyncio.run(self.correct(transcription, context_hint))

    async def quick_correct(
        self,
        transcription: TranscriptionResult
    ) -> TranscriptionResult:
        """
        빠른 교정 (맥락 분석 생략)

        단순한 맞춤법/문법 오류만 교정
        """
        corrected_segments = []

        for seg in transcription.segments:
            prompt = f"""다음 한국어 문장의 맞춤법과 문법만 교정하세요. 의미 변경 금지.
원본: "{seg.text}"
교정된 문장만 출력하세요 (따옴표 없이):"""

            response_text = self._call_llm(prompt, max_tokens=512, temperature=0.1)
            corrected_text = response_text.strip().strip('"\'')

            corrected_segments.append(Segment(
                start=seg.start,
                end=seg.end,
                text=corrected_text,
                speaker=seg.speaker,
                confidence=seg.confidence
            ))

        return TranscriptionResult(
            segments=corrected_segments,
            language=transcription.language,
            duration=transcription.duration,
            num_speakers=transcription.num_speakers,
            engine=f"{transcription.engine}+quick_corrected",
            model=transcription.model
        )

    async def correct_with_rag(
        self,
        transcription: TranscriptionResult,
        knowledge_base: "KnowledgeBase",
        use_llm: bool = True
    ) -> TranscriptionResult:
        """
        RAG 데이터를 활용한 전사 교정

        Args:
            transcription: 원본 전사 결과
            knowledge_base: 선거 지식 베이스 (후보자, 정책 등)
            use_llm: LLM 추가 교정 사용 여부

        Returns:
            교정된 TranscriptionResult (오류 시 원본 반환)
        """
        import logging
        logger = logging.getLogger(__name__)

        # Phonetic matcher 로드 시도
        try:
            from src.rag.phonetic_matcher import get_phonetic_matcher
            matcher = get_phonetic_matcher()
        except ImportError as e:
            logger.warning(f"RAG phonetic_matcher 모듈 로드 실패: {e}")
            print(f"[RAG] phonetic_matcher 모듈 없음 - RAG 교정 건너뜀")
            return transcription
        except Exception as e:
            logger.error(f"RAG matcher 초기화 오류: {e}")
            print(f"[RAG] matcher 초기화 실패: {e}")
            return transcription

        corrected_segments = []

        # RAG 데이터에서 후보 목록 추출 (안전하게)
        try:
            candidate_names = knowledge_base.candidate_names if knowledge_base else []
            policy_names = knowledge_base.policy_names if knowledge_base else []
        except Exception as e:
            logger.warning(f"지식 베이스에서 이름 추출 실패: {e}")
            candidate_names = []
            policy_names = []

        for idx, segment in enumerate(transcription.segments):
            try:
                corrected_text = segment.text
                corrected_speaker = segment.speaker
                confidence_adjustments = []

                # 1. 화자 이름 교정 (RAG 매칭)
                if segment.speaker and candidate_names:
                    try:
                        match = matcher.match(segment.speaker, candidate_names, threshold=0.7)
                        if match and match.confidence > 0.75:
                            corrected_speaker = match.matched
                            confidence_adjustments.append(match.confidence)
                    except Exception as e:
                        logger.debug(f"세그먼트 {idx} 화자 매칭 실패: {e}")

                # 2. 텍스트 내 후보자 이름 교정
                if candidate_names:
                    try:
                        corrected_text, name_matches = matcher.find_and_replace(
                            corrected_text,
                            candidate_names,
                            threshold=0.75
                        )
                        for m in name_matches:
                            confidence_adjustments.append(m.confidence)
                    except Exception as e:
                        logger.debug(f"세그먼트 {idx} 후보자 이름 교정 실패: {e}")

                # 3. 정책명 교정
                if policy_names:
                    try:
                        corrected_text, policy_matches = matcher.find_and_replace(
                            corrected_text,
                            policy_names,
                            threshold=0.7
                        )
                        for m in policy_matches:
                            confidence_adjustments.append(m.confidence)
                    except Exception as e:
                        logger.debug(f"세그먼트 {idx} 정책명 교정 실패: {e}")

                # 평균 신뢰도 계산
                if confidence_adjustments:
                    avg_confidence = sum(confidence_adjustments) / len(confidence_adjustments)
                    new_confidence = (segment.confidence + avg_confidence) / 2
                else:
                    new_confidence = segment.confidence

                corrected_segments.append(Segment(
                    start=segment.start,
                    end=segment.end,
                    text=corrected_text,
                    speaker=corrected_speaker,
                    confidence=new_confidence
                ))

            except Exception as seg_error:
                # 개별 세그먼트 처리 실패 시 원본 유지
                logger.warning(f"세그먼트 {idx} 교정 실패, 원본 유지: {seg_error}")
                corrected_segments.append(segment)

        # RAG 교정 적용된 결과
        rag_corrected = TranscriptionResult(
            segments=corrected_segments,
            language=transcription.language,
            duration=transcription.duration,
            num_speakers=transcription.num_speakers,
            engine=f"{transcription.engine}+rag_corrected",
            model=transcription.model
        )

        # LLM 추가 교정 (선택적)
        if use_llm:
            try:
                # RAG 데이터를 맥락 힌트로 전달
                context_hint = self._build_rag_context_hint(knowledge_base)
                return await self.correct(rag_corrected, context_hint)
            except Exception as llm_error:
                logger.warning(f"LLM 추가 교정 실패, RAG 결과만 반환: {llm_error}")
                print(f"[RAG] LLM 교정 실패: {llm_error}")
                return rag_corrected

        return rag_corrected

    def _build_rag_context_hint(self, knowledge_base: "KnowledgeBase") -> str:
        """RAG 지식 베이스에서 맥락 힌트 생성"""
        hints = []

        if knowledge_base.election_type:
            hints.append(f"선거 유형: {knowledge_base.election_type}")

        if knowledge_base.region:
            hints.append(f"지역: {knowledge_base.region}")

        if knowledge_base.candidates:
            candidate_info = []
            for c in knowledge_base.candidates:
                info = c.name
                if c.party:
                    info += f"({c.party})"
                if c.number:
                    info += f" 기호{c.number}"
                candidate_info.append(info)
            hints.append(f"후보자: {', '.join(candidate_info)}")

        if knowledge_base.policies:
            policy_names = [p.name for p in knowledge_base.policies[:10]]
            hints.append(f"주요 정책: {', '.join(policy_names)}")

        return "\n".join(hints)

    def correct_with_rag_sync(
        self,
        transcription: TranscriptionResult,
        knowledge_base: "KnowledgeBase",
        use_llm: bool = True
    ) -> TranscriptionResult:
        """RAG 교정의 동기 버전"""
        return asyncio.run(self.correct_with_rag(transcription, knowledge_base, use_llm))
