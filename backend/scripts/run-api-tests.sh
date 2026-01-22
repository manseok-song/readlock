#!/bin/bash
# ReadLock 2.0 API 테스트 스크립트
# Ralph Loop용 자동 테스트 및 수정 루프

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 결과 저장
PASSED=0
FAILED=0
ERRORS=()

# 로그 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASSED++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAILED++)); ERRORS+=("$1"); }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 환경 변수
BASE_URL="http://localhost"
ACCESS_TOKEN=""
REFRESH_TOKEN=""
TEST_EMAIL="test_$(date +%s)@readlock.com"
TEST_PASSWORD="TestPassword123!"
TEST_NICKNAME="테스트유저$(date +%s)"

# API 호출 함수
api_call() {
    local method=$1
    local url=$2
    local data=$3
    local auth=$4

    local headers="-H 'Content-Type: application/json'"
    if [ -n "$auth" ]; then
        headers="$headers -H 'Authorization: Bearer $auth'"
    fi

    if [ -n "$data" ]; then
        eval "curl -s -X $method $headers -d '$data' '$url'"
    else
        eval "curl -s -X $method $headers '$url'"
    fi
}

# 헬스체크 테스트
test_health_checks() {
    log_info "=== Phase 0: 서비스 헬스체크 ==="

    local services=("auth:8000" "book:8001" "reading:8002" "community:8003" "user:8004" "map:8005" "ai:8006" "notification:8007" "gamification:8008" "subscription:8009")

    for service in "${services[@]}"; do
        local name="${service%%:*}"
        local port="${service##*:}"
        local response=$(curl -sf "$BASE_URL:$port/health" 2>/dev/null)

        if echo "$response" | grep -q "healthy"; then
            log_success "$name service (port $port) - healthy"
        else
            log_fail "$name service (port $port) - not responding"
        fi
    done
}

# Auth 서비스 테스트
test_auth_service() {
    log_info "=== Phase 1: Auth Service 테스트 ==="

    # 회원가입
    log_info "회원가입 테스트..."
    local register_response=$(api_call POST "$BASE_URL:8000/v1/auth/register" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"nickname\":\"$TEST_NICKNAME\"}")

    if echo "$register_response" | grep -qE "(user|created|success|id)"; then
        log_success "회원가입 성공"
    elif echo "$register_response" | grep -q "already"; then
        log_warn "이미 존재하는 사용자 - 기존 계정으로 로그인 시도"
        TEST_EMAIL="test@readlock.com"
    else
        log_fail "회원가입 실패: $register_response"
    fi

    # 로그인
    log_info "로그인 테스트..."
    local login_response=$(api_call POST "$BASE_URL:8000/v1/auth/login" "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

    ACCESS_TOKEN=$(echo "$login_response" | grep -oP '"accessToken"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
    REFRESH_TOKEN=$(echo "$login_response" | grep -oP '"refreshToken"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")

    if [ -n "$ACCESS_TOKEN" ]; then
        log_success "로그인 성공 - 토큰 획득"
    else
        log_fail "로그인 실패: $login_response"
        return 1
    fi

    # 사용자 정보 조회
    log_info "현재 사용자 정보 조회..."
    local me_response=$(api_call GET "$BASE_URL:8000/v1/auth/me" "" "$ACCESS_TOKEN")

    if echo "$me_response" | grep -qE "(email|id|user)"; then
        log_success "사용자 정보 조회 성공"
    else
        log_fail "사용자 정보 조회 실패: $me_response"
    fi

    # 토큰 갱신
    log_info "토큰 갱신 테스트..."
    local refresh_response=$(api_call POST "$BASE_URL:8000/v1/auth/refresh" "{\"refreshToken\":\"$REFRESH_TOKEN\"}")

    if echo "$refresh_response" | grep -q "accessToken"; then
        log_success "토큰 갱신 성공"
    else
        log_fail "토큰 갱신 실패: $refresh_response"
    fi
}

# Gamification 서비스 테스트
test_gamification_service() {
    log_info "=== Phase 9: Gamification Service 테스트 ==="

    if [ -z "$ACCESS_TOKEN" ]; then
        log_fail "인증 토큰 없음 - Auth 테스트 먼저 실행 필요"
        return 1
    fi

    # 뱃지 목록 조회
    log_info "전체 뱃지 조회..."
    local badges_response=$(api_call GET "$BASE_URL:8008/api/v1/badges/" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "뱃지 목록 조회 성공"
    else
        log_fail "뱃지 목록 조회 실패"
    fi

    # 내 뱃지 조회
    log_info "내 뱃지 조회..."
    local my_badges=$(api_call GET "$BASE_URL:8008/api/v1/badges/me" "" "$ACCESS_TOKEN")
    if echo "$my_badges" | grep -qE "(badges|\\[)"; then
        log_success "내 뱃지 조회 성공"
    else
        log_fail "내 뱃지 조회 실패: $my_badges"
    fi

    # 레벨 조회
    log_info "내 레벨 조회..."
    local level_response=$(api_call GET "$BASE_URL:8008/api/v1/levels/me" "" "$ACCESS_TOKEN")
    if echo "$level_response" | grep -qE "(level|exp)"; then
        log_success "레벨 조회 성공"
    else
        log_fail "레벨 조회 실패: $level_response"
    fi

    # 상점 아이템 조회
    log_info "상점 아이템 조회..."
    local shop_response=$(api_call GET "$BASE_URL:8008/api/v1/shop/items" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "상점 아이템 조회 성공"
    else
        log_fail "상점 아이템 조회 실패"
    fi

    # 코인 잔액 조회
    log_info "코인 잔액 조회..."
    local coins_response=$(api_call GET "$BASE_URL:8008/api/v1/shop/coins" "" "$ACCESS_TOKEN")
    if echo "$coins_response" | grep -qE "(balance|coins)"; then
        log_success "코인 잔액 조회 성공"
    else
        log_fail "코인 잔액 조회 실패: $coins_response"
    fi

    # 리더보드 조회
    log_info "리더보드 조회..."
    local leaderboard=$(api_call GET "$BASE_URL:8008/api/v1/leaderboard/reading-time" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "리더보드 조회 성공"
    else
        log_fail "리더보드 조회 실패"
    fi
}

# Subscription 서비스 테스트
test_subscription_service() {
    log_info "=== Phase 10: Subscription Service 테스트 ==="

    if [ -z "$ACCESS_TOKEN" ]; then
        log_fail "인증 토큰 없음"
        return 1
    fi

    # 구독 플랜 조회
    log_info "구독 플랜 조회..."
    local plans=$(api_call GET "$BASE_URL:8009/api/v1/subscriptions/plans" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "구독 플랜 조회 성공"
    else
        log_fail "구독 플랜 조회 실패"
    fi

    # 내 구독 조회
    log_info "내 구독 정보 조회..."
    local my_sub=$(api_call GET "$BASE_URL:8009/api/v1/subscriptions/me" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "구독 정보 조회 성공"
    else
        log_fail "구독 정보 조회 실패"
    fi

    # 결제 수단 조회
    log_info "결제 수단 조회..."
    local methods=$(api_call GET "$BASE_URL:8009/api/v1/payments/methods" "" "$ACCESS_TOKEN")
    if [ $? -eq 0 ]; then
        log_success "결제 수단 조회 성공"
    else
        log_fail "결제 수단 조회 실패"
    fi

    # 코인 패키지 조회
    log_info "코인 패키지 조회..."
    local packages=$(api_call GET "$BASE_URL:8009/api/v1/payments/coins/packages" "" "$ACCESS_TOKEN")
    if echo "$packages" | grep -qE "(coins|price|\\[)"; then
        log_success "코인 패키지 조회 성공"
    else
        log_fail "코인 패키지 조회 실패: $packages"
    fi
}

# 기타 서비스 테스트 (간단 버전)
test_other_services() {
    log_info "=== 기타 서비스 간단 테스트 ==="

    if [ -z "$ACCESS_TOKEN" ]; then
        log_fail "인증 토큰 없음"
        return 1
    fi

    # Book Service
    log_info "Book Service - 서재 조회..."
    local library=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8001/api/v1/books/library" 2>/dev/null)
    [ $? -eq 0 ] && log_success "Book Service 정상" || log_fail "Book Service 오류"

    # Reading Service
    log_info "Reading Service - 통계 조회..."
    local stats=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8002/api/v1/reading/stats" 2>/dev/null)
    [ $? -eq 0 ] && log_success "Reading Service 정상" || log_fail "Reading Service 오류"

    # Community Service
    log_info "Community Service - 피드 조회..."
    local feed=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8003/api/v1/community/feed" 2>/dev/null)
    [ $? -eq 0 ] && log_success "Community Service 정상" || log_fail "Community Service 오류"

    # Map Service
    log_info "Map Service - 서점 검색..."
    local nearby=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8005/api/v1/map/bookstores/nearby?latitude=37.5665&longitude=126.9780" 2>/dev/null)
    [ $? -eq 0 ] && log_success "Map Service 정상" || log_fail "Map Service 오류"

    # AI Service
    log_info "AI Service - 추천 조회..."
    local recs=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8006/api/v1/recommendations/personalized" 2>/dev/null)
    [ $? -eq 0 ] && log_success "AI Service 정상" || log_fail "AI Service 오류"

    # Notification Service
    log_info "Notification Service - 알림 조회..."
    local notifs=$(curl -sf -H "Authorization: Bearer $ACCESS_TOKEN" "$BASE_URL:8007/api/v1/notifications" 2>/dev/null)
    [ $? -eq 0 ] && log_success "Notification Service 정상" || log_fail "Notification Service 오류"
}

# 결과 요약
print_summary() {
    echo ""
    echo "========================================"
    echo "          테스트 결과 요약"
    echo "========================================"
    echo -e "통과: ${GREEN}$PASSED${NC}"
    echo -e "실패: ${RED}$FAILED${NC}"
    echo ""

    if [ ${#ERRORS[@]} -gt 0 ]; then
        echo "실패한 테스트:"
        for error in "${ERRORS[@]}"; do
            echo -e "  ${RED}✗${NC} $error"
        done
    fi

    echo ""
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}모든 테스트 통과!${NC}"
        exit 0
    else
        echo -e "${RED}일부 테스트 실패 - 수정이 필요합니다.${NC}"
        exit 1
    fi
}

# 메인 실행
main() {
    echo "========================================"
    echo "   ReadLock 2.0 API 테스트 시작"
    echo "========================================"
    echo ""

    test_health_checks
    echo ""

    test_auth_service
    echo ""

    test_gamification_service
    echo ""

    test_subscription_service
    echo ""

    test_other_services
    echo ""

    print_summary
}

# 스크립트 실행
main "$@"
