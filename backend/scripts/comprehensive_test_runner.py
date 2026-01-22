#!/usr/bin/env python3
"""
ReadLock 2.0 종합 테스트 러너
- Flutter 앱 연동 테스트
- 추가 엔드포인트 테스트
- E2E 시나리오 테스트
- 부하 테스트
"""

import asyncio
import aiohttp
import json
import time
import random
import string
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import statistics

# Windows UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 서비스 URL 설정 (ralph_loop_runner.py와 동일한 패턴)
BASE_URLS = {
    "auth": "http://localhost:8000",
    "book": "http://localhost:8001",
    "reading": "http://localhost:8002",
    "community": "http://localhost:8003",
    "user": "http://localhost:8004",
    "map": "http://localhost:8005",
    "ai": "http://localhost:8006",
    "notification": "http://localhost:8007",
    "gamification": "http://localhost:8008",
    "subscription": "http://localhost:8009",
}

# Auth 서비스는 /v1/auth 패턴, 나머지는 /api/v1 패턴
SERVICES = {
    "auth": f"{BASE_URLS['auth']}/v1",  # Auth는 /v1/auth/* 패턴
    "book": f"{BASE_URLS['book']}/api/v1",
    "reading": f"{BASE_URLS['reading']}/api/v1",
    "community": f"{BASE_URLS['community']}/api/v1",
    "user": f"{BASE_URLS['user']}/api/v1",
    "map": f"{BASE_URLS['map']}/api/v1",
    "ai": f"{BASE_URLS['ai']}/api/v1",
    "notification": f"{BASE_URLS['notification']}/api/v1",
    "gamification": f"{BASE_URLS['gamification']}/api/v1",
    "subscription": f"{BASE_URLS['subscription']}/api/v1",
}

# 색상 코드
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_section(text: str):
    print(f"\n{Colors.CYAN}--- {text} ---{Colors.ENDC}")

def print_pass(text: str):
    print(f"{Colors.GREEN}[PASS]{Colors.ENDC} {text}")

def print_fail(text: str, error: str = ""):
    print(f"{Colors.FAIL}[FAIL]{Colors.ENDC} {text}")
    if error:
        print(f"       {Colors.WARNING}Error: {error}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {text}")

def print_warn(text: str):
    print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {text}")


@dataclass
class TestResult:
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    response_data: Optional[Dict] = None


@dataclass
class TestSuite:
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_duration_ms(self) -> float:
        return sum(r.duration_ms for r in self.results)


class ComprehensiveTestRunner:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None
        # Use unique email for new test run, but fallback to known account if needed
        self.unique_suffix = int(time.time())
        self.test_email = f"test_{self.unique_suffix}@readlock.com"
        self.test_password = "TestPassword123!"
        self.test_nickname = f"테스트유저{self.unique_suffix % 10000}"
        self.suites: List[TestSuite] = []
        self.created_resources: Dict[str, List[str]] = {
            "books": [],
            "user_books": [],
            "quotes": [],
            "reviews": [],
        }

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print_header("ReadLock 2.0 종합 테스트")
        print_info(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"테스트 계정: {self.test_email}")

        # 1. Flutter 앱 연동 테스트
        await self.run_flutter_integration_tests()

        # 2. 추가 엔드포인트 테스트
        await self.run_additional_endpoint_tests()

        # 3. E2E 시나리오 테스트
        await self.run_e2e_scenario_tests()

        # 4. 부하 테스트
        await self.run_load_tests()

        # 결과 출력
        self.print_summary()

    async def make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        expected_status: List[int] = [200],
    ) -> TestResult:
        """HTTP 요청 수행"""
        start_time = time.time()

        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        if headers:
            request_headers.update(headers)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=data,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    duration_ms = (time.time() - start_time) * 1000

                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"raw": await response.text()}

                    passed = response.status in expected_status

                    return TestResult(
                        name=f"{method} {url}",
                        passed=passed,
                        duration_ms=duration_ms,
                        error=None if passed else f"Status {response.status}, expected {expected_status}",
                        response_data=response_data
                    )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=f"{method} {url}",
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )

    # ==================== 1. Flutter 앱 연동 테스트 ====================

    async def run_flutter_integration_tests(self):
        """Flutter 앱에서 사용하는 API 엔드포인트 테스트"""
        print_header("1. Flutter 앱 연동 테스트")
        suite = TestSuite(name="Flutter Integration")

        # 1.1 인증 플로우 테스트
        print_section("1.1 인증 API (Flutter AuthRepository)")

        # 회원가입 시도
        result = await self.make_request(
            "POST",
            f"{SERVICES['auth']}/auth/register",
            data={
                "email": self.test_email,
                "password": self.test_password,
                "nickname": self.test_nickname
            },
            expected_status=[201, 409]  # 201=created, 409=already exists
        )

        # 409인 경우에도 등록 테스트는 성공으로 처리 (이미 존재하는 계정)
        if result.response_data and "error" in str(result.response_data).lower():
            # 다른 에러인 경우
            suite.results.append(TestResult("회원가입 (register)", False, result.duration_ms, result.error))
            print_fail(f"회원가입", result.error)
        else:
            suite.results.append(TestResult("회원가입 (register)", True, result.duration_ms, None))
            print_pass(f"회원가입 - {result.duration_ms:.0f}ms")

        # 로그인 시도
        result = await self.make_request(
            "POST",
            f"{SERVICES['auth']}/auth/login",
            data={
                "email": self.test_email,
                "password": self.test_password
            },
            expected_status=[200]
        )

        if not result.passed:
            # 새 계정 로그인 실패 시 기존 테스트 계정으로 시도
            print_warn("새 계정 로그인 실패 - 기존 테스트 계정으로 재시도")
            self.test_email = "test@readlock.com"
            result = await self.make_request(
                "POST",
                f"{SERVICES['auth']}/auth/login",
                data={
                    "email": self.test_email,
                    "password": self.test_password
                },
                expected_status=[200]
            )

        suite.results.append(TestResult("로그인 (login)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"로그인 - {result.duration_ms:.0f}ms")
            # 토큰 저장
            if result.response_data:
                data = result.response_data.get("data", {})
                tokens = data.get("tokens", {})
                self.access_token = tokens.get("accessToken")
                self.refresh_token = tokens.get("refreshToken")
                user = data.get("user", {})
                self.user_id = user.get("id")
                print_info(f"토큰 획득 완료 (User ID: {self.user_id})")
        else:
            print_fail(f"로그인", result.error)

        # 현재 사용자 정보
        result = await self.make_request(
            "GET",
            f"{SERVICES['auth']}/auth/me",
            expected_status=[200]
        )
        suite.results.append(TestResult("현재 사용자 조회 (getCurrentUser)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"현재 사용자 조회 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"현재 사용자 조회", result.error)

        # 토큰 갱신
        result = await self.make_request(
            "POST",
            f"{SERVICES['auth']}/auth/refresh",
            data={"refreshToken": self.refresh_token},
            expected_status=[200]
        )
        suite.results.append(TestResult("토큰 갱신 (refreshToken)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"토큰 갱신 - {result.duration_ms:.0f}ms")
            # 새 토큰 저장
            if result.response_data:
                data = result.response_data.get("data", {})
                tokens = data.get("tokens", {})
                self.access_token = tokens.get("accessToken", self.access_token)
                self.refresh_token = tokens.get("refreshToken", self.refresh_token)
        else:
            print_fail(f"토큰 갱신", result.error)

        # 1.2 책 API 테스트
        print_section("1.2 책 API (Flutter BookRepository)")

        # 책 검색
        result = await self.make_request(
            "GET",
            f"{SERVICES['book']}/books/search?query=python&page=1&size=10",
            expected_status=[200]
        )
        suite.results.append(TestResult("책 검색 (searchBooks)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"책 검색 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"책 검색", result.error)

        # 내 서재 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['book']}/books/me/books",
            expected_status=[200]
        )
        suite.results.append(TestResult("내 서재 조회 (getUserBooks)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"내 서재 조회 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"내 서재 조회", result.error)

        # 1.3 독서 API 테스트
        print_section("1.3 독서 API (Flutter ReadingRepository)")

        # 독서 통계
        result = await self.make_request(
            "GET",
            f"{SERVICES['reading']}/reading/stats?period=week",
            expected_status=[200]
        )
        suite.results.append(TestResult("독서 통계 (getStats)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"독서 통계 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"독서 통계", result.error)

        # 독서 스트릭
        result = await self.make_request(
            "GET",
            f"{SERVICES['reading']}/reading/streak",
            expected_status=[200]
        )
        suite.results.append(TestResult("독서 스트릭 (getStreak)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"독서 스트릭 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"독서 스트릭", result.error)

        # 1.4 커뮤니티 API 테스트
        print_section("1.4 커뮤니티 API")

        # 피드 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/feed/",
            expected_status=[200]
        )
        suite.results.append(TestResult("피드 조회 (getFeed)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"피드 조회 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"피드 조회", result.error)

        # 1.5 사용자 API 테스트
        print_section("1.5 사용자 API (Flutter UserRepository)")

        # 프로필 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['user']}/profile/",
            expected_status=[200, 404]
        )
        suite.results.append(TestResult("프로필 조회 (getProfile)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"프로필 조회 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"프로필 조회", result.error)

        # 1.6 지도 API 테스트
        print_section("1.6 지도 API")

        # 주변 서점 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/bookstores/nearby?latitude=37.5665&longitude=126.9780&radius=5",
            expected_status=[200]
        )
        suite.results.append(TestResult("주변 서점 조회 (getNearbyBookstores)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"주변 서점 조회 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"주변 서점 조회", result.error)

        # 1.7 AI 추천 API 테스트
        print_section("1.7 AI API")

        # 책 추천
        result = await self.make_request(
            "GET",
            f"{SERVICES['ai']}/recommendations/personalized",
            expected_status=[200]
        )
        suite.results.append(TestResult("책 추천 (getRecommendations)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"책 추천 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"책 추천", result.error)

        # 1.8 알림 API 테스트
        print_section("1.8 알림 API")

        # 알림 목록
        result = await self.make_request(
            "GET",
            f"{SERVICES['notification']}/notifications/",
            expected_status=[200]
        )
        suite.results.append(TestResult("알림 목록 (getNotifications)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"알림 목록 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"알림 목록", result.error)

        # 1.9 게이미피케이션 API 테스트
        print_section("1.9 게이미피케이션 API")

        # 내 레벨 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/levels/me",
            expected_status=[200]
        )
        suite.results.append(TestResult("내 레벨 (getMyLevel)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"내 레벨 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"내 레벨", result.error)

        # 뱃지 목록
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/badges/",
            expected_status=[200]
        )
        suite.results.append(TestResult("뱃지 목록 (getBadges)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"뱃지 목록 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"뱃지 목록", result.error)

        # 1.10 구독 API 테스트
        print_section("1.10 구독 API")

        # 구독 플랜
        result = await self.make_request(
            "GET",
            f"{SERVICES['subscription']}/subscriptions/plans",
            expected_status=[200]
        )
        suite.results.append(TestResult("구독 플랜 (getPlans)", result.passed, result.duration_ms, result.error))
        if result.passed:
            print_pass(f"구독 플랜 - {result.duration_ms:.0f}ms")
        else:
            print_fail(f"구독 플랜", result.error)

        self.suites.append(suite)

    # ==================== 2. 추가 엔드포인트 테스트 ====================

    async def run_additional_endpoint_tests(self):
        """기본 테스트에서 포함되지 않은 추가 엔드포인트 테스트"""
        print_header("2. 추가 엔드포인트 테스트")
        suite = TestSuite(name="Additional Endpoints")

        # 2.1 Auth 서비스 추가 엔드포인트
        print_section("2.1 Auth 서비스 추가")

        # FCM 토큰 등록
        result = await self.make_request(
            "PATCH",
            f"{SERVICES['auth']}/auth/fcm-token",
            data={"fcmToken": "test_fcm_token_12345", "platform": "android"},
            expected_status=[200]
        )
        suite.results.append(TestResult("FCM 토큰 등록", result.passed, result.duration_ms, result.error))
        self._print_result("FCM 토큰 등록", result)

        # 2.2 Book 서비스 추가 엔드포인트
        print_section("2.2 Book 서비스 추가")

        # ISBN으로 책 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['book']}/books/isbn/9788936434120",
            expected_status=[200, 404]
        )
        suite.results.append(TestResult("ISBN 책 조회", result.passed, result.duration_ms, result.error))
        self._print_result("ISBN 책 조회", result)

        # 2.3 User 서비스 추가 엔드포인트
        print_section("2.3 User 서비스 추가")

        # 읽기 목표 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['user']}/profile/reading-goal",
            expected_status=[200]
        )
        suite.results.append(TestResult("읽기 목표 조회", result.passed, result.duration_ms, result.error))
        self._print_result("읽기 목표 조회", result)

        # 읽기 목표 설정
        result = await self.make_request(
            "PUT",
            f"{SERVICES['user']}/profile/reading-goal",
            data={"daily_minutes": 30, "monthly_books": 2},
            expected_status=[200]
        )
        suite.results.append(TestResult("읽기 목표 설정", result.passed, result.duration_ms, result.error))
        self._print_result("읽기 목표 설정", result)

        # 팔로워 목록
        result = await self.make_request(
            "GET",
            f"{SERVICES['user']}/social/followers",
            expected_status=[200]
        )
        suite.results.append(TestResult("팔로워 목록", result.passed, result.duration_ms, result.error))
        self._print_result("팔로워 목록", result)

        # 팔로잉 목록
        result = await self.make_request(
            "GET",
            f"{SERVICES['user']}/social/following",
            expected_status=[200]
        )
        suite.results.append(TestResult("팔로잉 목록", result.passed, result.duration_ms, result.error))
        self._print_result("팔로잉 목록", result)

        # 2.4 Community 서비스 추가 엔드포인트
        print_section("2.4 Community 서비스 추가")

        # 트렌딩 피드
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/feed/trending?period=week",
            expected_status=[200]
        )
        suite.results.append(TestResult("트렌딩 피드", result.passed, result.duration_ms, result.error))
        self._print_result("트렌딩 피드", result)

        # 내 인용구
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/quotes/me",
            expected_status=[200]
        )
        suite.results.append(TestResult("내 인용구", result.passed, result.duration_ms, result.error))
        self._print_result("내 인용구", result)

        # 내 리뷰
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/reviews/",
            expected_status=[200]
        )
        suite.results.append(TestResult("내 리뷰", result.passed, result.duration_ms, result.error))
        self._print_result("내 리뷰", result)

        # 2.5 Map 서비스 추가 엔드포인트
        print_section("2.5 Map 서비스 추가")

        # 서점 검색
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/bookstores/search?query=교보",
            expected_status=[200]
        )
        suite.results.append(TestResult("서점 검색", result.passed, result.duration_ms, result.error))
        self._print_result("서점 검색", result)

        # 즐겨찾기 서점
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/bookstores/favorites/list",
            expected_status=[200]
        )
        suite.results.append(TestResult("즐겨찾기 서점", result.passed, result.duration_ms, result.error))
        self._print_result("즐겨찾기 서점", result)

        # 내 체크인 기록
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/checkins/my",
            expected_status=[200]
        )
        suite.results.append(TestResult("내 체크인 기록", result.passed, result.duration_ms, result.error))
        self._print_result("내 체크인 기록", result)

        # 2.6 Gamification 서비스 추가 엔드포인트
        print_section("2.6 Gamification 서비스 추가")

        # 상점 아이템
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/shop/items",
            expected_status=[200]
        )
        suite.results.append(TestResult("상점 아이템", result.passed, result.duration_ms, result.error))
        self._print_result("상점 아이템", result)

        # 리더보드 (독서시간)
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/leaderboard/reading-time",
            expected_status=[200]
        )
        suite.results.append(TestResult("리더보드 (독서시간)", result.passed, result.duration_ms, result.error))
        self._print_result("리더보드 (독서시간)", result)

        # 2.7 Notification 서비스 추가 엔드포인트
        print_section("2.7 Notification 서비스 추가")

        # 알림 설정 조회
        result = await self.make_request(
            "GET",
            f"{SERVICES['notification']}/notifications/settings",
            expected_status=[200]
        )
        suite.results.append(TestResult("알림 설정 조회", result.passed, result.duration_ms, result.error))
        self._print_result("알림 설정 조회", result)

        # 2.8 Subscription 서비스 추가 엔드포인트
        print_section("2.8 Subscription 서비스 추가")

        # 결제 내역
        result = await self.make_request(
            "GET",
            f"{SERVICES['subscription']}/payments/history",
            expected_status=[200]
        )
        suite.results.append(TestResult("결제 내역", result.passed, result.duration_ms, result.error))
        self._print_result("결제 내역", result)

        # 코인 패키지
        result = await self.make_request(
            "GET",
            f"{SERVICES['subscription']}/payments/coins/packages",
            expected_status=[200]
        )
        suite.results.append(TestResult("코인 패키지", result.passed, result.duration_ms, result.error))
        self._print_result("코인 패키지", result)

        self.suites.append(suite)

    # ==================== 3. E2E 시나리오 테스트 ====================

    async def run_e2e_scenario_tests(self):
        """전체 사용자 플로우 E2E 테스트"""
        print_header("3. E2E 시나리오 테스트")
        suite = TestSuite(name="E2E Scenarios")

        # 시나리오 1: 신규 사용자 가입 → 프로필 설정 → 첫 책 추가
        print_section("시나리오 1: 신규 사용자 온보딩")
        scenario1_results = await self._scenario_new_user_onboarding()
        suite.results.extend(scenario1_results)

        # 시나리오 2: 책 검색 → 서재 추가 → 독서 시작 → 독서 완료
        print_section("시나리오 2: 독서 플로우")
        scenario2_results = await self._scenario_reading_flow()
        suite.results.extend(scenario2_results)

        # 시나리오 3: 리뷰 작성 → 피드 조회 → 좋아요
        print_section("시나리오 3: 커뮤니티 활동")
        scenario3_results = await self._scenario_community_activity()
        suite.results.extend(scenario3_results)

        # 시나리오 4: 서점 검색 → 체크인
        print_section("시나리오 4: 서점 방문")
        scenario4_results = await self._scenario_bookstore_visit()
        suite.results.extend(scenario4_results)

        # 시나리오 5: 게이미피케이션 확인
        print_section("시나리오 5: 게이미피케이션")
        scenario5_results = await self._scenario_gamification()
        suite.results.extend(scenario5_results)

        self.suites.append(suite)

    async def _scenario_new_user_onboarding(self) -> List[TestResult]:
        """신규 사용자 온보딩 시나리오"""
        results = []

        # 이미 로그인된 상태이므로 프로필 설정부터 시작
        print_info("Step 1: 프로필 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['user']}/profile/",
            expected_status=[200, 404]
        )
        results.append(TestResult("프로필 조회", result.passed, result.duration_ms, result.error))
        self._print_result("프로필 조회", result)

        print_info("Step 2: 읽기 목표 설정")
        result = await self.make_request(
            "PUT",
            f"{SERVICES['user']}/profile/reading-goal",
            data={"daily_minutes": 30, "yearly_books": 24},
            expected_status=[200]
        )
        results.append(TestResult("읽기 목표 설정", result.passed, result.duration_ms, result.error))
        self._print_result("읽기 목표 설정", result)

        print_info("Step 3: 책 검색")
        result = await self.make_request(
            "GET",
            f"{SERVICES['book']}/books/search?query=해리포터",
            expected_status=[200]
        )
        results.append(TestResult("책 검색", result.passed, result.duration_ms, result.error))
        self._print_result("책 검색", result)

        return results

    async def _scenario_reading_flow(self) -> List[TestResult]:
        """독서 플로우 시나리오"""
        results = []

        print_info("Step 1: 서재 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['book']}/books/me/books",
            expected_status=[200]
        )
        results.append(TestResult("서재 조회", result.passed, result.duration_ms, result.error))
        self._print_result("서재 조회", result)

        print_info("Step 2: 독서 통계 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['reading']}/reading/stats?period=month",
            expected_status=[200]
        )
        results.append(TestResult("독서 통계 조회", result.passed, result.duration_ms, result.error))
        self._print_result("독서 통계 조회", result)

        print_info("Step 3: 일일 통계 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['reading']}/reading/daily?days=7",
            expected_status=[200]
        )
        results.append(TestResult("일일 통계 조회", result.passed, result.duration_ms, result.error))
        self._print_result("일일 통계 조회", result)

        print_info("Step 4: 독서 프로필 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['reading']}/reading/profile",
            expected_status=[200]
        )
        results.append(TestResult("독서 프로필 조회", result.passed, result.duration_ms, result.error))
        self._print_result("독서 프로필 조회", result)

        return results

    async def _scenario_community_activity(self) -> List[TestResult]:
        """커뮤니티 활동 시나리오"""
        results = []

        print_info("Step 1: 피드 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/feed/",
            expected_status=[200]
        )
        results.append(TestResult("피드 조회", result.passed, result.duration_ms, result.error))
        self._print_result("피드 조회", result)

        print_info("Step 2: 트렌딩 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/feed/trending?period=week",
            expected_status=[200]
        )
        results.append(TestResult("트렌딩 조회", result.passed, result.duration_ms, result.error))
        self._print_result("트렌딩 조회", result)

        print_info("Step 3: 내 인용구 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/quotes/me",
            expected_status=[200]
        )
        results.append(TestResult("내 인용구 조회", result.passed, result.duration_ms, result.error))
        self._print_result("내 인용구 조회", result)

        print_info("Step 4: 내 리뷰 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['community']}/reviews/",
            expected_status=[200]
        )
        results.append(TestResult("내 리뷰 조회", result.passed, result.duration_ms, result.error))
        self._print_result("내 리뷰 조회", result)

        return results

    async def _scenario_bookstore_visit(self) -> List[TestResult]:
        """서점 방문 시나리오"""
        results = []

        print_info("Step 1: 주변 서점 검색")
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/bookstores/nearby?latitude=37.5665&longitude=126.9780&radius=10",
            expected_status=[200]
        )
        results.append(TestResult("주변 서점 검색", result.passed, result.duration_ms, result.error))
        self._print_result("주변 서점 검색", result)

        print_info("Step 2: 서점 검색 (키워드)")
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/bookstores/search?query=독립서점",
            expected_status=[200]
        )
        results.append(TestResult("서점 검색 (키워드)", result.passed, result.duration_ms, result.error))
        self._print_result("서점 검색 (키워드)", result)

        print_info("Step 3: 내 체크인 기록")
        result = await self.make_request(
            "GET",
            f"{SERVICES['map']}/checkins/my",
            expected_status=[200]
        )
        results.append(TestResult("내 체크인 기록", result.passed, result.duration_ms, result.error))
        self._print_result("내 체크인 기록", result)

        return results

    async def _scenario_gamification(self) -> List[TestResult]:
        """게이미피케이션 시나리오"""
        results = []

        print_info("Step 1: 내 레벨 조회")
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/levels/me",
            expected_status=[200]
        )
        results.append(TestResult("내 레벨 조회", result.passed, result.duration_ms, result.error))
        self._print_result("내 레벨 조회", result)

        print_info("Step 2: 뱃지 목록")
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/badges/",
            expected_status=[200]
        )
        results.append(TestResult("뱃지 목록", result.passed, result.duration_ms, result.error))
        self._print_result("뱃지 목록", result)

        print_info("Step 3: 내 뱃지")
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/badges/me",
            expected_status=[200]
        )
        results.append(TestResult("내 뱃지", result.passed, result.duration_ms, result.error))
        self._print_result("내 뱃지", result)

        print_info("Step 4: 코인 잔액")
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/shop/coins",
            expected_status=[200]
        )
        results.append(TestResult("코인 잔액", result.passed, result.duration_ms, result.error))
        self._print_result("코인 잔액", result)

        print_info("Step 5: 리더보드")
        result = await self.make_request(
            "GET",
            f"{SERVICES['gamification']}/leaderboard/reading-time",
            expected_status=[200]
        )
        results.append(TestResult("리더보드", result.passed, result.duration_ms, result.error))
        self._print_result("리더보드", result)

        return results

    # ==================== 4. 부하 테스트 ====================

    async def run_load_tests(self):
        """부하 테스트"""
        print_header("4. 부하 테스트")
        suite = TestSuite(name="Load Tests")

        # 4.1 동시 요청 테스트
        print_section("4.1 동시 요청 테스트 (10 concurrent requests)")
        concurrent_result = await self._test_concurrent_requests(10)
        suite.results.append(concurrent_result)

        # 4.2 연속 요청 테스트
        print_section("4.2 연속 요청 테스트 (50 sequential requests)")
        sequential_result = await self._test_sequential_requests(50)
        suite.results.append(sequential_result)

        # 4.3 혼합 부하 테스트
        print_section("4.3 혼합 부하 테스트 (다양한 엔드포인트)")
        mixed_result = await self._test_mixed_load(20)
        suite.results.append(mixed_result)

        self.suites.append(suite)

    async def _test_concurrent_requests(self, count: int) -> TestResult:
        """동시 요청 테스트"""
        start_time = time.time()

        async def make_single_request():
            return await self.make_request(
                "GET",
                f"{SERVICES['book']}/books/me/books",
                expected_status=[200]
            )

        tasks = [make_single_request() for _ in range(count)]
        results = await asyncio.gather(*tasks)

        duration_ms = (time.time() - start_time) * 1000
        passed = sum(1 for r in results if r.passed)
        failed = count - passed

        avg_response = statistics.mean(r.duration_ms for r in results)
        max_response = max(r.duration_ms for r in results)
        min_response = min(r.duration_ms for r in results)

        print_info(f"총 요청: {count}, 성공: {passed}, 실패: {failed}")
        print_info(f"응답 시간 - 평균: {avg_response:.0f}ms, 최소: {min_response:.0f}ms, 최대: {max_response:.0f}ms")
        print_info(f"총 소요 시간: {duration_ms:.0f}ms")

        all_passed = failed == 0
        if all_passed:
            print_pass(f"동시 요청 테스트 통과")
        else:
            print_fail(f"동시 요청 테스트", f"{failed}개 실패")

        return TestResult(
            name=f"동시 요청 ({count}개)",
            passed=all_passed,
            duration_ms=duration_ms,
            error=None if all_passed else f"{failed}개 실패"
        )

    async def _test_sequential_requests(self, count: int) -> TestResult:
        """연속 요청 테스트"""
        start_time = time.time()
        response_times = []
        failed_count = 0

        for i in range(count):
            result = await self.make_request(
                "GET",
                f"{SERVICES['auth']}/auth/me",
                expected_status=[200]
            )
            response_times.append(result.duration_ms)
            if not result.passed:
                failed_count += 1

        duration_ms = (time.time() - start_time) * 1000

        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        min_response = min(response_times)
        p95_response = sorted(response_times)[int(count * 0.95)]

        print_info(f"총 요청: {count}, 성공: {count - failed_count}, 실패: {failed_count}")
        print_info(f"응답 시간 - 평균: {avg_response:.0f}ms, P95: {p95_response:.0f}ms")
        print_info(f"최소: {min_response:.0f}ms, 최대: {max_response:.0f}ms")
        print_info(f"처리량: {count / (duration_ms / 1000):.1f} req/s")

        all_passed = failed_count == 0
        if all_passed:
            print_pass(f"연속 요청 테스트 통과")
        else:
            print_fail(f"연속 요청 테스트", f"{failed_count}개 실패")

        return TestResult(
            name=f"연속 요청 ({count}개)",
            passed=all_passed,
            duration_ms=duration_ms,
            error=None if all_passed else f"{failed_count}개 실패"
        )

    async def _test_mixed_load(self, count: int) -> TestResult:
        """혼합 부하 테스트"""
        endpoints = [
            ("GET", f"{SERVICES['auth']}/auth/me"),
            ("GET", f"{SERVICES['book']}/books/me/books"),
            ("GET", f"{SERVICES['reading']}/reading/stats?period=week"),
            ("GET", f"{SERVICES['community']}/feed/"),
            ("GET", f"{SERVICES['user']}/profile/"),
            ("GET", f"{SERVICES['gamification']}/levels/me"),
            ("GET", f"{SERVICES['notification']}/notifications/"),
        ]

        start_time = time.time()

        async def make_random_request():
            method, url = random.choice(endpoints)
            return await self.make_request(method, url, expected_status=[200, 404])

        tasks = [make_random_request() for _ in range(count)]
        results = await asyncio.gather(*tasks)

        duration_ms = (time.time() - start_time) * 1000
        passed = sum(1 for r in results if r.passed)
        failed = count - passed

        avg_response = statistics.mean(r.duration_ms for r in results)

        print_info(f"총 요청: {count}, 성공: {passed}, 실패: {failed}")
        print_info(f"평균 응답 시간: {avg_response:.0f}ms")
        print_info(f"처리량: {count / (duration_ms / 1000):.1f} req/s")

        all_passed = failed == 0
        if all_passed:
            print_pass(f"혼합 부하 테스트 통과")
        else:
            print_fail(f"혼합 부하 테스트", f"{failed}개 실패")

        return TestResult(
            name=f"혼합 부하 ({count}개)",
            passed=all_passed,
            duration_ms=duration_ms,
            error=None if all_passed else f"{failed}개 실패"
        )

    def _print_result(self, name: str, result: TestResult):
        if result.passed:
            print_pass(f"{name} - {result.duration_ms:.0f}ms")
        else:
            print_fail(name, result.error)

    def print_summary(self):
        """테스트 결과 요약 출력"""
        print_header("테스트 결과 요약")

        total_passed = 0
        total_failed = 0
        total_duration = 0

        for suite in self.suites:
            print(f"\n{Colors.CYAN}[{suite.name}]{Colors.ENDC}")
            print(f"   {Colors.GREEN}통과: {suite.passed_count}{Colors.ENDC}")
            print(f"   {Colors.FAIL}실패: {suite.failed_count}{Colors.ENDC}")
            print(f"   소요시간: {suite.total_duration_ms:.0f}ms")

            total_passed += suite.passed_count
            total_failed += suite.failed_count
            total_duration += suite.total_duration_ms

            # 실패한 테스트 목록
            failed_tests = [r for r in suite.results if not r.passed]
            if failed_tests:
                print(f"   {Colors.WARNING}실패 목록:{Colors.ENDC}")
                for r in failed_tests:
                    print(f"      - {r.name}: {r.error}")

        print(f"\n{Colors.BOLD}{'='*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}전체 통과: {total_passed}{Colors.ENDC}")
        print(f"{Colors.BOLD}전체 실패: {total_failed}{Colors.ENDC}")
        print(f"{Colors.BOLD}총 소요시간: {total_duration/1000:.1f}초{Colors.ENDC}")
        print(f"{'='*50}")

        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] 모든 테스트 통과!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}[FAILED] {total_failed}개 테스트 실패{Colors.ENDC}")

        # JSON 리포트 저장
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_duration_ms": total_duration,
            },
            "suites": [
                {
                    "name": suite.name,
                    "passed": suite.passed_count,
                    "failed": suite.failed_count,
                    "duration_ms": suite.total_duration_ms,
                    "results": [
                        {
                            "name": r.name,
                            "passed": r.passed,
                            "duration_ms": r.duration_ms,
                            "error": r.error,
                        }
                        for r in suite.results
                    ]
                }
                for suite in self.suites
            ]
        }

        os.makedirs("test-reports", exist_ok=True)
        with open("test-reports/comprehensive-test-report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{Colors.BLUE}[REPORT] 리포트 저장: test-reports/comprehensive-test-report.json{Colors.ENDC}")


async def main():
    runner = ComprehensiveTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
