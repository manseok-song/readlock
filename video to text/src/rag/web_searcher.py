"""선거 정보 웹 검색 모듈

Google Custom Search API를 사용하여 선거 관련 정보를 검색합니다.
후보자 정보, 정책/공약 정보를 수집합니다.
"""

import os
import re
from dataclasses import dataclass
from typing import Optional

try:
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


@dataclass
class SearchResult:
    """검색 결과"""
    title: str
    snippet: str
    link: str
    type: str  # "candidate", "policy", "general"
    extracted_data: Optional[dict] = None


class ElectionWebSearcher:
    """선거 관련 정보 웹 검색"""

    # 검색 쿼리 템플릿
    CANDIDATE_QUERY_TEMPLATE = "{year} {region} {position} 후보"
    POLICY_QUERY_TEMPLATE = "{candidate} 공약 정책"
    GENERAL_QUERY_TEMPLATE = "{year} {election_type} {region}"

    def __init__(
        self,
        api_key: Optional[str] = None,
        cx: Optional[str] = None,
        max_results: int = 10
    ):
        """
        Args:
            api_key: Google Custom Search API 키
            cx: Custom Search Engine ID
            max_results: 최대 검색 결과 수
        """
        self.api_key = api_key or os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        self.cx = cx or os.getenv("GOOGLE_CUSTOM_SEARCH_CX")
        self.max_results = max_results
        self._service = None

    @property
    def is_available(self) -> bool:
        """API 사용 가능 여부"""
        return GOOGLE_API_AVAILABLE and bool(self.api_key) and bool(self.cx)

    @property
    def service(self):
        """Google Custom Search API 서비스"""
        if not self.is_available:
            raise RuntimeError(
                "Google Custom Search API를 사용할 수 없습니다. "
                "GOOGLE_CUSTOM_SEARCH_API_KEY와 GOOGLE_CUSTOM_SEARCH_CX 환경 변수를 설정하세요."
            )

        if self._service is None:
            self._service = build("customsearch", "v1", developerKey=self.api_key)

        return self._service

    def _search(self, query: str, num_results: Optional[int] = None) -> list[SearchResult]:
        """기본 검색 수행"""
        if not self.is_available:
            return []

        num_results = num_results or self.max_results

        try:
            result = self.service.cse().list(
                q=query,
                cx=self.cx,
                num=min(num_results, 10),  # API 최대 10개
                lr="lang_ko",  # 한국어 결과 우선
            ).execute()

            items = result.get("items", [])
            search_results = []

            for item in items:
                search_results.append(SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    link=item.get("link", ""),
                    type="general",
                ))

            return search_results

        except Exception as e:
            print(f"[WebSearcher] 검색 오류: {e}")
            return []

    async def search_candidates(
        self,
        region: str,
        election_type: Optional[str] = None,
        position: Optional[str] = None,
        year: int = 2026
    ) -> list[dict]:
        """
        후보자 정보 검색

        Args:
            region: 지역 (예: "서울시", "경기도")
            election_type: 선거 유형 (예: "지방선거", "총선")
            position: 직위 (예: "시장", "도지사", "국회의원")
            year: 선거 연도

        Returns:
            후보자 정보 목록
        """
        # 직위 자동 추론
        if position is None:
            if "시" in region:
                position = "시장"
            elif "도" in region:
                position = "도지사"
            elif "구" in region or "군" in region:
                position = "구청장" if "구" in region else "군수"
            else:
                position = ""

        query = self.CANDIDATE_QUERY_TEMPLATE.format(
            year=year,
            region=region,
            position=position
        )

        results = self._search(query)
        candidates = []

        for result in results:
            # 검색 결과에서 후보자 정보 추출 시도
            extracted = self._extract_candidate_info(result)
            if extracted:
                extracted["type"] = "candidate"
                candidates.append(extracted)

        return candidates

    async def search_policies(
        self,
        candidate: str,
        region: Optional[str] = None
    ) -> list[dict]:
        """
        후보자 공약/정책 검색

        Args:
            candidate: 후보자 이름
            region: 지역 (선택)

        Returns:
            정책 정보 목록
        """
        query = self.POLICY_QUERY_TEMPLATE.format(candidate=candidate)
        if region:
            query += f" {region}"

        results = self._search(query)
        policies = []

        for result in results:
            extracted = self._extract_policy_info(result, candidate)
            if extracted:
                extracted["type"] = "policy"
                policies.append(extracted)

        return policies

    async def search_all(
        self,
        region: Optional[str] = None,
        election_type: Optional[str] = None,
        candidates: Optional[list[str]] = None,
        year: int = 2026
    ) -> list[dict]:
        """
        모든 관련 정보 통합 검색

        Args:
            region: 지역
            election_type: 선거 유형
            candidates: 알려진 후보자 목록
            year: 선거 연도

        Returns:
            모든 검색 결과 목록
        """
        all_results = []

        # 1. 후보자 검색
        if region:
            candidate_results = await self.search_candidates(
                region=region,
                election_type=election_type,
                year=year
            )
            all_results.extend(candidate_results)

        # 2. 알려진 후보자의 정책 검색
        if candidates:
            for candidate in candidates:
                policy_results = await self.search_policies(
                    candidate=candidate,
                    region=region
                )
                all_results.extend(policy_results)

        return all_results

    def _extract_candidate_info(self, result: SearchResult) -> Optional[dict]:
        """검색 결과에서 후보자 정보 추출"""
        text = f"{result.title} {result.snippet}"

        # 이름 패턴 (2-4글자 한글 이름)
        name_pattern = r"([가-힣]{2,4})\s*(후보|의원|시장|도지사|구청장|군수)"
        name_match = re.search(name_pattern, text)

        if not name_match:
            return None

        name = name_match.group(1)

        # 정당 추출
        party_pattern = r"(더불어민주당|국민의힘|정의당|진보당|녹색당|무소속|[가-힣]+당)"
        party_match = re.search(party_pattern, text)
        party = party_match.group(1) if party_match else None

        # 기호 번호 추출
        number_pattern = r"기호\s*(\d+)번?"
        number_match = re.search(number_pattern, text)
        number = int(number_match.group(1)) if number_match else None

        return {
            "name": name,
            "party": party,
            "number": number,
            "source_url": result.link,
            "source_snippet": result.snippet[:200],
        }

    def _extract_policy_info(self, result: SearchResult, candidate: str) -> Optional[dict]:
        """검색 결과에서 정책 정보 추출"""
        text = f"{result.title} {result.snippet}"

        # 정책명 패턴 (따옴표, 괄호 안 또는 특정 키워드와 함께)
        policy_patterns = [
            r"['\"]([^'\"]{5,30})['\"]",  # 따옴표 안
            r"'([^']{5,30})'",            # 홑따옴표
            r"「([^」]{5,30})」",          # 낫표
            r"정책[:\s]+([가-힣\s]{5,30})",  # 정책: 이름
            r"공약[:\s]+([가-힣\s]{5,30})",  # 공약: 이름
        ]

        policy_name = None
        for pattern in policy_patterns:
            match = re.search(pattern, text)
            if match:
                policy_name = match.group(1).strip()
                break

        if not policy_name:
            return None

        # 카테고리 추출
        categories = {
            "경제": ["경제", "일자리", "고용", "창업", "기업"],
            "복지": ["복지", "의료", "건강", "노인", "아동", "장애인"],
            "교육": ["교육", "학교", "대학", "청소년"],
            "주거": ["주거", "주택", "아파트", "임대"],
            "교통": ["교통", "도로", "지하철", "버스"],
            "환경": ["환경", "기후", "탄소", "녹색"],
        }

        category = None
        for cat, keywords in categories.items():
            if any(kw in text for kw in keywords):
                category = cat
                break

        return {
            "name": policy_name,
            "candidate": candidate,
            "category": category,
            "description": result.snippet[:300],
            "source_url": result.link,
        }


class MockElectionWebSearcher(ElectionWebSearcher):
    """테스트/오프라인용 목 검색기"""

    def __init__(self):
        super().__init__()
        self._mock_candidates = [
            {
                "type": "candidate",
                "name": "홍길동",
                "party": "무소속",
                "number": 1,
            },
            {
                "type": "candidate",
                "name": "김철수",
                "party": "국민의힘",
                "number": 2,
            },
        ]
        self._mock_policies = [
            {
                "type": "policy",
                "name": "청년 일자리 10만개 창출",
                "candidate": "홍길동",
                "category": "경제",
            },
            {
                "type": "policy",
                "name": "무상 교육 확대",
                "candidate": "김철수",
                "category": "교육",
            },
        ]

    @property
    def is_available(self) -> bool:
        return True

    async def search_candidates(self, **kwargs) -> list[dict]:
        return self._mock_candidates

    async def search_policies(self, **kwargs) -> list[dict]:
        return self._mock_policies

    async def search_all(self, **kwargs) -> list[dict]:
        return self._mock_candidates + self._mock_policies


def get_web_searcher(use_mock: bool = False) -> ElectionWebSearcher:
    """웹 검색기 인스턴스 반환"""
    if use_mock:
        return MockElectionWebSearcher()

    searcher = ElectionWebSearcher()
    if not searcher.is_available:
        print("[WebSearcher] API 키가 없어 목 검색기를 사용합니다.")
        return MockElectionWebSearcher()

    return searcher
