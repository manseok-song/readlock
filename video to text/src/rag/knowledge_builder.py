"""선거 지식 베이스 구축 모듈

후보자, 정책, 선거 용어 등의 정보를 구조화하여 관리합니다.
전사 교정에 사용되는 참조 데이터를 제공합니다.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Candidate:
    """후보자 정보"""
    name: str                           # 이름
    party: Optional[str] = None         # 소속 정당
    number: Optional[int] = None        # 기호 번호
    region: Optional[str] = None        # 출마 지역
    position: Optional[str] = None      # 출마 직위 (시장, 도지사 등)
    aliases: list[str] = field(default_factory=list)  # 별칭/이명

    @property
    def all_names(self) -> list[str]:
        """모든 이름 변형 목록"""
        names = [self.name]
        names.extend(self.aliases)
        return names


@dataclass
class Policy:
    """정책/공약 정보"""
    name: str                           # 정책명
    description: Optional[str] = None   # 설명
    candidate: Optional[str] = None     # 제안 후보자
    category: Optional[str] = None      # 분류 (경제, 복지, 교육 등)
    keywords: list[str] = field(default_factory=list)  # 관련 키워드

    @property
    def all_terms(self) -> list[str]:
        """정책명과 키워드 모두 포함"""
        terms = [self.name]
        terms.extend(self.keywords)
        return terms


@dataclass
class ElectionTerm:
    """선거 용어"""
    term: str                           # 용어
    definition: Optional[str] = None    # 정의
    category: Optional[str] = None      # 분류


@dataclass
class KnowledgeBase:
    """선거 지식 베이스"""
    candidates: list[Candidate] = field(default_factory=list)
    policies: list[Policy] = field(default_factory=list)
    terminology: list[ElectionTerm] = field(default_factory=list)

    # 메타데이터
    election_type: Optional[str] = None      # 선거 유형 (지방선거, 총선 등)
    election_date: Optional[str] = None      # 선거일
    region: Optional[str] = None             # 지역
    created_at: Optional[str] = None         # 생성 시간
    source: Optional[str] = None             # 데이터 출처

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    @property
    def candidate_names(self) -> list[str]:
        """모든 후보자 이름 목록"""
        names = []
        for candidate in self.candidates:
            names.extend(candidate.all_names)
        return list(set(names))

    @property
    def policy_names(self) -> list[str]:
        """모든 정책명 목록"""
        names = []
        for policy in self.policies:
            names.extend(policy.all_terms)
        return list(set(names))

    @property
    def all_terms(self) -> list[str]:
        """모든 용어 목록"""
        terms = self.candidate_names + self.policy_names
        terms.extend([t.term for t in self.terminology])
        return list(set(terms))

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "candidates": [asdict(c) for c in self.candidates],
            "policies": [asdict(p) for p in self.policies],
            "terminology": [asdict(t) for t in self.terminology],
            "election_type": self.election_type,
            "election_date": self.election_date,
            "region": self.region,
            "created_at": self.created_at,
            "source": self.source,
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save(self, path: str | Path) -> Path:
        """JSON 파일로 저장"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeBase":
        """딕셔너리에서 생성"""
        return cls(
            candidates=[Candidate(**c) for c in data.get("candidates", [])],
            policies=[Policy(**p) for p in data.get("policies", [])],
            terminology=[ElectionTerm(**t) for t in data.get("terminology", [])],
            election_type=data.get("election_type"),
            election_date=data.get("election_date"),
            region=data.get("region"),
            created_at=data.get("created_at"),
            source=data.get("source"),
        )

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        """JSON 파일에서 로드"""
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def merge(self, other: "KnowledgeBase") -> "KnowledgeBase":
        """다른 KnowledgeBase와 병합"""
        # 중복 제거를 위해 이름 기준으로 병합
        existing_candidates = {c.name for c in self.candidates}
        existing_policies = {p.name for p in self.policies}
        existing_terms = {t.term for t in self.terminology}

        new_candidates = self.candidates.copy()
        for c in other.candidates:
            if c.name not in existing_candidates:
                new_candidates.append(c)

        new_policies = self.policies.copy()
        for p in other.policies:
            if p.name not in existing_policies:
                new_policies.append(p)

        new_terminology = self.terminology.copy()
        for t in other.terminology:
            if t.term not in existing_terms:
                new_terminology.append(t)

        return KnowledgeBase(
            candidates=new_candidates,
            policies=new_policies,
            terminology=new_terminology,
            election_type=self.election_type or other.election_type,
            election_date=self.election_date or other.election_date,
            region=self.region or other.region,
            source=f"{self.source}, {other.source}" if self.source and other.source else self.source or other.source,
        )


class ElectionKnowledgeBuilder:
    """선거 지식 베이스 빌더"""

    # 기본 선거 용어
    DEFAULT_TERMINOLOGY = [
        ElectionTerm("투표율", "전체 유권자 중 투표에 참여한 비율"),
        ElectionTerm("기권", "투표하지 않음"),
        ElectionTerm("무효표", "인정되지 않는 투표"),
        ElectionTerm("사전투표", "선거일 이전에 미리 하는 투표"),
        ElectionTerm("당선", "선거에서 이김"),
        ElectionTerm("낙선", "선거에서 짐"),
        ElectionTerm("공약", "후보자가 당선 후 이행하겠다고 약속한 정책"),
        ElectionTerm("공천", "정당이 후보자를 지명함"),
        ElectionTerm("출마", "선거에 후보로 나섬"),
        ElectionTerm("유권자", "투표할 자격이 있는 사람"),
    ]

    def __init__(self):
        self._knowledge_base: Optional[KnowledgeBase] = None

    def build_from_manual_input(
        self,
        candidates: list[dict] | list[str],
        policies: Optional[list[dict] | list[str]] = None,
        election_type: Optional[str] = None,
        region: Optional[str] = None,
        include_default_terms: bool = True
    ) -> KnowledgeBase:
        """
        수동 입력으로 지식 베이스 구축

        Args:
            candidates: 후보자 목록 (문자열 또는 딕셔너리)
            policies: 정책 목록 (문자열 또는 딕셔너리)
            election_type: 선거 유형
            region: 지역
            include_default_terms: 기본 선거 용어 포함 여부

        Returns:
            KnowledgeBase
        """
        # 후보자 처리
        candidate_list = []
        for c in candidates:
            if isinstance(c, str):
                candidate_list.append(Candidate(name=c))
            elif isinstance(c, dict):
                candidate_list.append(Candidate(**c))
            elif isinstance(c, Candidate):
                candidate_list.append(c)

        # 정책 처리
        policy_list = []
        if policies:
            for p in policies:
                if isinstance(p, str):
                    policy_list.append(Policy(name=p))
                elif isinstance(p, dict):
                    policy_list.append(Policy(**p))
                elif isinstance(p, Policy):
                    policy_list.append(p)

        # 용어 처리
        terminology = self.DEFAULT_TERMINOLOGY.copy() if include_default_terms else []

        self._knowledge_base = KnowledgeBase(
            candidates=candidate_list,
            policies=policy_list,
            terminology=terminology,
            election_type=election_type,
            region=region,
            source="manual_input",
        )

        return self._knowledge_base

    def build_from_search_results(
        self,
        search_results: list[dict],
        election_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> KnowledgeBase:
        """
        웹 검색 결과로 지식 베이스 구축

        Args:
            search_results: 웹 검색 결과 목록
            election_type: 선거 유형
            region: 지역

        Returns:
            KnowledgeBase
        """
        candidates = []
        policies = []

        for result in search_results:
            result_type = result.get("type", "unknown")

            if result_type == "candidate":
                candidates.append(Candidate(
                    name=result.get("name", ""),
                    party=result.get("party"),
                    number=result.get("number"),
                    region=result.get("region", region),
                    position=result.get("position"),
                    aliases=result.get("aliases", []),
                ))
            elif result_type == "policy":
                policies.append(Policy(
                    name=result.get("name", ""),
                    description=result.get("description"),
                    candidate=result.get("candidate"),
                    category=result.get("category"),
                    keywords=result.get("keywords", []),
                ))

        self._knowledge_base = KnowledgeBase(
            candidates=candidates,
            policies=policies,
            terminology=self.DEFAULT_TERMINOLOGY.copy(),
            election_type=election_type,
            region=region,
            source="web_search",
        )

        return self._knowledge_base

    async def build(
        self,
        region: Optional[str] = None,
        election_type: Optional[str] = None,
        candidates: Optional[list[str]] = None,
        policies: Optional[list[str]] = None,
        search_enabled: bool = False
    ) -> KnowledgeBase:
        """
        지식 베이스 구축 (통합 인터페이스)

        Args:
            region: 지역
            election_type: 선거 유형
            candidates: 후보자 이름 목록
            policies: 정책명 목록
            search_enabled: 웹 검색 활성화 여부

        Returns:
            KnowledgeBase
        """
        # 기본 지식 베이스 생성
        kb = self.build_from_manual_input(
            candidates=candidates or [],
            policies=policies or [],
            election_type=election_type,
            region=region,
        )

        # 웹 검색이 활성화되어 있으면 추가 정보 수집
        if search_enabled and (region or election_type):
            try:
                from src.rag.web_searcher import ElectionWebSearcher
                searcher = ElectionWebSearcher()
                search_results = await searcher.search_all(
                    region=region,
                    election_type=election_type
                )
                search_kb = self.build_from_search_results(
                    search_results,
                    election_type=election_type,
                    region=region
                )
                kb = kb.merge(search_kb)
            except ImportError:
                pass  # 웹 검색 모듈이 없으면 스킵
            except Exception as e:
                print(f"[RAG] 웹 검색 실패 (수동 입력만 사용): {e}")

        self._knowledge_base = kb
        return kb

    @property
    def knowledge_base(self) -> Optional[KnowledgeBase]:
        """현재 지식 베이스 반환"""
        return self._knowledge_base


# 팩토리 함수
def create_knowledge_base(
    candidates: list[str],
    policies: Optional[list[str]] = None,
    election_type: Optional[str] = None,
    region: Optional[str] = None
) -> KnowledgeBase:
    """간편 지식 베이스 생성"""
    builder = ElectionKnowledgeBuilder()
    return builder.build_from_manual_input(
        candidates=candidates,
        policies=policies,
        election_type=election_type,
        region=region,
    )
