# Changelog

모든 주요 변경 사항이 이 파일에 기록됩니다.

## [2.0.1] - 2026-01-22

### Flutter 웹 빌드 완성

#### 추가된 파일
- `lib/core/errors/exceptions.dart`: `UnauthorizedException`, `ConflictException`, `NotFoundException` 예외 클래스 추가
- `lib/presentation/providers/repository_providers.dart`: Repository Provider 정의 파일 생성
  - `secureStorageProvider`
  - `authRepositoryProvider`
  - `bookRepositoryProvider`
  - `readingRepositoryProvider`

#### 수정된 파일
- `lib/core/errors/failures.dart`: Failure 팩토리 메서드 추가
  - `AuthFailure`: `invalidCredentials()`, `emailAlreadyInUse()`, `sessionExpired()`, `networkError()`, `validation()`, `unknown()`
  - `BookFailure`: `notFound()`, `alreadyInLibrary()`, `networkError()`, `unknown()`
  - `ReadingFailure`: `sessionAlreadyActive()`, `sessionNotFound()`, `networkError()`, `unknown()`

- `lib/data/datasources/remote/api_client.dart`:
  - `ApiClient` 래퍼 클래스 구현 (GET/POST/PATCH/DELETE/PUT)
  - `apiClientProvider` 추가
  - ErrorInterceptor에서 새 예외 클래스 사용

- `lib/domain/entities/reading_session.dart`:
  - `ReadingSession` 엔티티 필드 업데이트 (startTime, endTime, startPage, endPage, focusScore, isOffline 등)
  - `ReadingSessionResult`에 `isOffline` 필드 추가
  - `SessionRewards`에 `bonusCoins`, `bonusExp` 필드 추가

- `lib/data/repositories/auth_repository_impl.dart`:
  - `updateFcmToken` 메서드 추가

- `lib/presentation/routes/app_router.dart`:
  - `ReadingSessionResult` import 추가

- `lib/presentation/providers/auth_provider.dart`:
  - `repository_providers.dart` import 추가
  - socialLogin 파라미터명 수정

- `lib/presentation/screens/profile/my_room_screen.dart`:
  - 존재하지 않는 아이콘 대체 (`Icons.lamp` → `Icons.lightbulb_outline`, `Icons.photo_frame` → `Icons.photo_outlined`)

- `lib/main.dart`:
  - `SystemUiOverlayStyle` 오타 수정
  - 웹 플랫폼에서 사용 불가능한 API를 `!kIsWeb` 조건으로 분기 처리

- `pubspec.yaml`:
  - 누락된 폰트 파일 주석 처리 (Pretendard 폰트)

#### 빌드 결과
- Flutter 웹 빌드 성공 (`flutter build web --release`)
- 빌드 출력: `apps/mobile/build/web`

---

## [2.0.0] - 2026-01-22

### 개요
ReadLock 2.0 전체 백엔드 시스템 구현 및 종합 테스트 완료. 10개의 마이크로서비스와 Flutter 앱 기반 구조 완성.

### 추가된 기능

#### 백엔드 서비스
- **Auth Service** (포트 8000)
  - 이메일/비밀번호 회원가입 및 로그인
  - JWT 기반 토큰 인증 (Access/Refresh Token)
  - OAuth 소셜 로그인 구조 (Google, Apple, Kakao)
  - FCM 토큰 관리

- **Book Service** (포트 8001)
  - 네이버 책 검색 API 연동
  - ISBN 기반 책 조회 및 DB 캐싱
  - 사용자 서재 관리 (CRUD)
  - 독서 상태 관리 (wishlist, reading, completed, dropped)

- **Reading Service** (포트 8002)
  - 독서 세션 관리 (시작/종료/일시정지)
  - 독서 통계 (일간/주간/월간)
  - 연속 독서 기록 (스트릭)
  - 독서 프로필 및 일일 통계

- **Community Service** (포트 8003)
  - 인용구 작성 및 공유
  - 책 리뷰 작성
  - 좋아요/댓글 기능
  - 피드 (팔로잉, 트렌딩, 책별, 사용자별)

- **User Service** (포트 8004)
  - 프로필 관리
  - 팔로우/팔로잉 시스템
  - 독서 목표 설정

- **Map Service** (포트 8005)
  - 주변 서점 검색 (위치 기반)
  - 서점 즐겨찾기
  - 체크인 기능
  - 서점 리뷰

- **AI Service** (포트 8006)
  - 개인화 책 추천
  - 유사 도서 추천
  - 트렌딩 추천
  - 독서 인사이트

- **Notification Service** (포트 8007)
  - 알림 목록 관리
  - 알림 설정
  - 읽음 처리

- **Gamification Service** (포트 8008)
  - 레벨 시스템
  - 뱃지 수집
  - 상점 (아바타 아이템)
  - 리더보드

- **Subscription Service** (포트 8009)
  - 구독 플랜 관리
  - 결제 연동 구조
  - 코인 시스템

#### Flutter 앱 구조
- Clean Architecture (Domain, Data, Presentation 레이어)
- Riverpod 상태 관리
- GoRouter 라우팅
- Dio HTTP 클라이언트
- 플랫폼 채널 (Android/iOS 폰잠금)

#### 인프라
- Docker Compose 멀티 서비스 구성
- PostgreSQL 15 + Redis 7
- Alembic DB 마이그레이션
- Terraform AWS 모듈 (VPC, ECS, RDS, ElastiCache)
- GitHub Actions CI/CD 파이프라인

### 수정된 사항

#### 데이터베이스 스키마 정합성 수정
- `Book` 모델: `authors` → `author` (String), `published_date` (Date)
- `UserBook` 모델: `completed_at` → `finished_at`, `total_pages` 추가
- `User` 모델: `oauth_provider` → `provider`, `oauth_id` → `provider_id`
- `UserProfile` 모델: `avatar_url` → `profile_image`
- `ReadingSession` 모델: `duration` → `duration_sec`, `start_time` → `started_at`
- `Quote` 모델: `thought` → `memo`, `likes_count` 추가
- `Review` 모델: `contains_spoiler` → `has_spoiler`
- `Bookstore` 모델: `photos` → `image_urls`

#### 서비스 로직 수정
- `BookstoreService.get_nearby()`: SQL 거리 계산 → Python Haversine 공식
- `FeedService`: `QuoteLike.id` 제거, `likes_count` 직접 사용
- `StatsService`: UserBook 조인 추가, 컬럼명 정합성
- `ProfileService`: ReadingGoal 새 스키마 대응

### 테스트

#### 테스트 스크립트 작성
- `ralph_loop_runner.py`: 기본 API 테스트 (36개)
- `comprehensive_test_runner.py`: 종합 테스트 (55개)
  - Flutter 앱 연동 테스트
  - 추가 엔드포인트 테스트
  - E2E 시나리오 테스트
  - 부하 테스트

#### 테스트 결과
| 카테고리 | 테스트 수 | 결과 |
|---------|----------|------|
| 서비스 헬스체크 | 10 | 모두 통과 |
| Auth API | 4 | 모두 통과 |
| Book API | 6 | 모두 통과 |
| Reading API | 5 | 모두 통과 |
| Community API | 5 | 모두 통과 |
| User API | 4 | 모두 통과 |
| Map API | 4 | 모두 통과 |
| AI API | 1 | 모두 통과 |
| Notification API | 2 | 모두 통과 |
| Gamification API | 8 | 모두 통과 |
| Subscription API | 6 | 모두 통과 |

### 성능

- 동시 요청 10개: 평균 응답 시간 182ms
- 연속 요청 50개: 처리량 125.2 req/s, P95 11ms
- 혼합 부하 20개: 처리량 201.6 req/s

### 알려진 이슈

- 네이버 API 인증 키 설정 필요 (책 검색 기능)
- OAuth 소셜 로그인 실제 연동 미완료
- Push 알림 FCM 연동 미완료

### 다음 단계

1. Flutter 앱 UI 완성 및 테스트
2. OAuth 소셜 로그인 연동
3. FCM Push 알림 연동
4. AWS 배포 및 프로덕션 환경 구성
5. 네이버 API 키 발급 및 연동
