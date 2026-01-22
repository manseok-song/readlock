# ReadLock 2.0 - 데이터 모델 및 API 설계

**Version:** 2.0  
**Platform:** Flutter (Web + Android + iOS) + FastAPI Backend

---

## 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ReadLock 2.0 Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Flutter Client (Dart)                         │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐                    │   │
│  │  │  Android  │  │    iOS    │  │    Web    │                    │   │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘                    │   │
│  │        └──────────────┼──────────────┘                          │   │
│  │                       │                                          │   │
│  │  ┌────────────────────┴────────────────────┐                    │   │
│  │  │           Shared Flutter Code            │                    │   │
│  │  │  • Riverpod (상태관리)                   │                    │   │
│  │  │  • Dio + Retrofit (HTTP)                │                    │   │
│  │  │  • Hive (로컬 DB)                       │                    │   │
│  │  │  • Freezed (모델)                       │                    │   │
│  │  └────────────────────┬────────────────────┘                    │   │
│  └───────────────────────┼─────────────────────────────────────────┘   │
│                          │                                              │
│                    HTTPS │ REST API + WebSocket                        │
│                          │                                              │
│  ┌───────────────────────┼─────────────────────────────────────────┐   │
│  │                       ▼                                          │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │                 API Gateway (Kong/AWS)                   │    │   │
│  │  └───────────────────────┬─────────────────────────────────┘    │   │
│  │                          │                                       │   │
│  │    ┌─────────┬───────────┼───────────┬─────────┬─────────┐      │   │
│  │    ▼         ▼           ▼           ▼         ▼         ▼      │   │
│  │ ┌──────┐ ┌──────┐   ┌──────┐   ┌──────┐ ┌──────┐ ┌──────┐      │   │
│  │ │ Auth │ │ User │   │ Book │   │Commun│ │  Map │ │  AI  │      │   │
│  │ │  Svc │ │  Svc │   │  Svc │   │  Svc │ │  Svc │ │  Svc │      │   │
│  │ └──┬───┘ └──┬───┘   └──┬───┘   └──┬───┘ └──┬───┘ └──┬───┘      │   │
│  │    │        │          │          │        │        │           │   │
│  │    └────────┴──────────┴──────────┴────────┴────────┘           │   │
│  │                          │                                       │   │
│  │    ┌─────────────────────┴─────────────────────┐                │   │
│  │    │              Data Layer                    │                │   │
│  │    │  ┌────────┐  ┌────────┐  ┌────────────┐   │                │   │
│  │    │  │  PG    │  │ Redis  │  │ Elasticsearch│  │                │   │
│  │    │  │(Main DB)│ │(Cache) │  │  (Search)   │   │                │   │
│  │    │  └────────┘  └────────┘  └────────────┘   │                │   │
│  │    └───────────────────────────────────────────┘                │   │
│  │                         Backend (FastAPI)                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      External Services                            │  │
│  │  • 네이버 책 API    • Kakao Map API     • Firebase (Auth/FCM)   │  │
│  │  • Google Play     • App Store         • Stripe                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ERD (Entity-Relationship Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ReadLock 2.0 Database Schema                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      users       │       │   user_profiles  │       │     avatars      │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │──────<│ user_id (FK,UQ)  │       │ id (PK)          │
│ email            │       │ nickname         │       │ user_id (FK,UQ)  │
│ password_hash    │       │ bio              │       │ head_item_id     │
│ provider         │       │ profile_image    │       │ body_item_id     │
│ provider_id      │       │ reading_goal_min │       │ face_item_id     │
│ fcm_token        │       │ is_public        │       │ accessory_id     │
│ created_at       │       │ level            │       │ created_at       │
│ updated_at       │       │ exp              │       │ updated_at       │
│ last_login_at    │       │ coins            │       └────────┬─────────┘
│ status           │       │ premium_until    │                │
└────────┬─────────┘       │ created_at       │       ┌────────┴─────────┐
         │                 │ updated_at       │       │    my_rooms      │
         │                 └──────────────────┘       ├──────────────────┤
         │                                            │ id (PK)          │
         │                                            │ user_id (FK,UQ)  │
         │                                            │ theme_id         │
         │                                            │ items_json       │
         │                                            │ created_at       │
         │                                            │ updated_at       │
         │                                            └──────────────────┘
         │
         │         ┌──────────────────┐       ┌──────────────────┐
         │         │   user_books     │       │      books       │
         │         ├──────────────────┤       ├──────────────────┤
         ├────────>│ id (PK)          │──────>│ id (PK)          │
         │         │ user_id (FK)     │       │ isbn (UQ)        │
         │         │ book_id (FK)     │       │ title            │
         │         │ status           │       │ author           │
         │         │ current_page     │       │ publisher        │
         │         │ total_pages      │       │ published_date   │
         │         │ started_at       │       │ description      │
         │         │ finished_at      │       │ cover_image      │
         │         │ created_at       │       │ category         │
         │         │ updated_at       │       │ page_count       │
         │         └────────┬─────────┘       │ naver_link       │
         │                  │                 │ created_at       │
         │                  │                 └────────┬─────────┘
         │                  │                          │
         │         ┌────────┴─────────┐       ┌────────┴─────────┐
         │         │ reading_sessions │       │     quotes       │
         │         ├──────────────────┤       ├──────────────────┤
         │         │ id (PK)          │       │ id (PK)          │
         │         │ user_book_id(FK) │       │ user_id (FK)     │
         │         │ started_at       │       │ book_id (FK)     │
         │         │ ended_at         │       │ content          │
         │         │ duration_sec     │       │ page_number      │
         │         │ pages_read       │       │ memo             │
         │         │ was_locked       │       │ likes_count      │
         │         │ platform         │       │ is_public        │
         │         │ created_at       │       │ created_at       │
         │         └──────────────────┘       └────────┬─────────┘
         │                                             │
         │                                    ┌────────┴─────────┐
         │                                    │   quote_likes    │
         │                                    ├──────────────────┤
         │                                    │ quote_id (FK,PK) │
         │                                    │ user_id (FK,PK)  │
         │                                    │ created_at       │
         │                                    └──────────────────┘
         │
         │         ┌──────────────────┐       ┌──────────────────┐
         │         │     reviews      │       │  review_comments │
         │         ├──────────────────┤       ├──────────────────┤
         ├────────>│ id (PK)          │<──────│ id (PK)          │
         │         │ user_id (FK)     │       │ review_id (FK)   │
         │         │ book_id (FK)     │       │ user_id (FK)     │
         │         │ rating           │       │ parent_id (FK)   │
         │         │ content          │       │ content          │
         │         │ has_spoiler      │       │ created_at       │
         │         │ likes_count      │       └──────────────────┘
         │         │ is_public        │
         │         │ created_at       │
         │         │ updated_at       │
         │         └──────────────────┘
         │
         │
         │         ┌──────────────────┐       ┌──────────────────┐
         │         │   bookstores     │       │ bookstore_visits │
         │         ├──────────────────┤       ├──────────────────┤
         │         │ id (PK)          │<──────│ id (PK)          │
         │         │ name             │       │ bookstore_id(FK) │
         │         │ address          │       │ user_id (FK)     │
         │         │ latitude         │       │ visited_at       │
         │         │ longitude        │       └──────────────────┘
         │         │ phone            │
         │         │ hours (JSONB)    │       ┌──────────────────┐
         │         │ description      │       │ bookstore_reviews│
         │         │ features (ARRAY) │       ├──────────────────┤
         │         │ image_url        │       │ id (PK)          │
         │         │ rating_avg       │       │ bookstore_id(FK) │
         │         │ is_verified      │       │ user_id (FK)     │
         │         │ created_at       │       │ rating           │
         │         └──────────────────┘       │ content          │
         │                                    │ created_at       │
         │                                    └──────────────────┘
         │
         │         ┌──────────────────┐       ┌──────────────────┐
         │         │    follows       │       │  notifications   │
         │         ├──────────────────┤       ├──────────────────┤
         ├────────>│ follower_id(FK,PK)│      │ id (PK)          │
         │         │ following_id(FK,PK)│     │ user_id (FK)     │
         │         │ created_at       │       │ type             │
         │         └──────────────────┘       │ title            │
         │                                    │ body             │
         │         ┌──────────────────┐       │ data (JSONB)     │
         │         │  shop_items      │       │ is_read          │
         │         ├──────────────────┤       │ created_at       │
         │         │ id (PK)          │       └──────────────────┘
         │         │ name             │
         │         │ description      │       ┌──────────────────┐
         │         │ category         │       │   user_items     │
         │         │ type             │       ├──────────────────┤
         │         │ price_coins      │       │ id (PK)          │
         │         │ price_cash       │       │ user_id (FK)     │
         │         │ image_url        │       │ item_id (FK)     │
         │         │ rarity           │       │ purchased_at     │
         │         │ unlock_level     │       │ is_equipped      │
         │         │ is_available     │       └──────────────────┘
         │         │ created_at       │
         │         └──────────────────┘
         │
         │         ┌──────────────────┐       ┌──────────────────┐
         │         │     badges       │       │   user_badges    │
         │         ├──────────────────┤       ├──────────────────┤
         │         │ id (PK)          │<──────│ user_id (FK,PK)  │
         │         │ name             │       │ badge_id (FK,PK) │
         │         │ description      │       │ earned_at        │
         │         │ icon_url         │       └──────────────────┘
         │         │ condition_type   │
         │         │ condition_value  │       ┌──────────────────┐
         │         │ reward_coins     │       │ subscriptions    │
         │         │ reward_exp       │       ├──────────────────┤
         │         │ created_at       │       │ id (PK)          │
         │         └──────────────────┘       │ user_id (FK)     │
         │                                    │ plan             │
         │                                    │ platform         │
         │                                    │ store_txn_id     │
         │                                    │ started_at       │
         │                                    │ expires_at       │
         │                                    │ status           │
         │                                    │ created_at       │
         └───────────────────────────────────>│ updated_at       │
                                              └──────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              Relationships                               │
├─────────────────────────────────────────────────────────────────────────┤
│  users 1:1 user_profiles       users 1:1 avatars       users 1:1 my_rooms│
│  users 1:N user_books          user_books N:1 books                      │
│  users 1:N quotes              users 1:N reviews                         │
│  users N:N follows             users 1:N notifications                   │
│  user_books 1:N reading_sessions                                         │
│  quotes 1:N quote_likes        reviews 1:N review_comments               │
│  bookstores 1:N bookstore_visits    bookstores 1:N bookstore_reviews     │
│  users 1:N user_items          users 1:N user_badges                     │
│  users 1:N subscriptions                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 테이블 상세 정의

### 3.1 users (사용자)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK, DEFAULT uuid_generate_v4() | 사용자 고유 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 |
| password_hash | VARCHAR(255) | NULL | 비밀번호 해시 (소셜 로그인 시 NULL) |
| provider | VARCHAR(50) | NOT NULL, DEFAULT 'local' | 인증 제공자 (local/google/apple/kakao) |
| provider_id | VARCHAR(255) | NULL | 소셜 로그인 ID |
| fcm_token | VARCHAR(500) | NULL | Firebase Cloud Messaging 토큰 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 가입일시 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 수정일시 |
| last_login_at | TIMESTAMPTZ | NULL | 마지막 로그인 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | 상태 (active/suspended/deleted) |

### 3.2 user_profiles (사용자 프로필)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 프로필 ID |
| user_id | UUID | FK, UNIQUE, NOT NULL | 사용자 ID |
| nickname | VARCHAR(50) | UNIQUE, NOT NULL | 닉네임 |
| bio | TEXT | NULL | 자기소개 (200자 제한) |
| profile_image | VARCHAR(500) | NULL | 프로필 이미지 URL |
| reading_goal_min | INTEGER | DEFAULT 30 | 일일 독서 목표(분) |
| is_public | BOOLEAN | DEFAULT true | 프로필 공개 여부 |
| level | INTEGER | DEFAULT 1 | 사용자 레벨 |
| exp | INTEGER | DEFAULT 0 | 경험치 |
| coins | INTEGER | DEFAULT 0 | 보유 코인 |
| premium_until | TIMESTAMPTZ | NULL | 프리미엄 만료일 |
| created_at | TIMESTAMPTZ | NOT NULL | 생성일시 |
| updated_at | TIMESTAMPTZ | NOT NULL | 수정일시 |

### 3.3 books (도서)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 도서 ID |
| isbn | VARCHAR(20) | UNIQUE, NOT NULL | ISBN-13 |
| title | VARCHAR(500) | NOT NULL | 제목 |
| author | VARCHAR(255) | NOT NULL | 저자 |
| publisher | VARCHAR(255) | NULL | 출판사 |
| published_date | DATE | NULL | 출판일 |
| description | TEXT | NULL | 설명 |
| cover_image | VARCHAR(500) | NULL | 표지 이미지 URL |
| category | VARCHAR(100) | NULL | 카테고리 |
| page_count | INTEGER | NULL | 페이지 수 |
| naver_link | VARCHAR(500) | NULL | 네이버 책 링크 |
| created_at | TIMESTAMPTZ | NOT NULL | 등록일시 |

### 3.4 user_books (사용자 책장)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | ID |
| user_id | UUID | FK, NOT NULL | 사용자 ID |
| book_id | UUID | FK, NOT NULL | 도서 ID |
| status | VARCHAR(20) | NOT NULL | 상태 (wishlist/reading/completed) |
| current_page | INTEGER | DEFAULT 0 | 현재 페이지 |
| total_pages | INTEGER | NULL | 총 페이지 (사용자 입력) |
| started_at | TIMESTAMPTZ | NULL | 독서 시작일 |
| finished_at | TIMESTAMPTZ | NULL | 독서 완료일 |
| created_at | TIMESTAMPTZ | NOT NULL | 등록일시 |
| updated_at | TIMESTAMPTZ | NOT NULL | 수정일시 |

**UNIQUE:** (user_id, book_id)

### 3.5 reading_sessions (독서 세션)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 세션 ID |
| user_book_id | UUID | FK, NOT NULL | 사용자 책 ID |
| started_at | TIMESTAMPTZ | NOT NULL | 시작 시간 |
| ended_at | TIMESTAMPTZ | NULL | 종료 시간 |
| duration_sec | INTEGER | NULL | 독서 시간(초) |
| pages_read | INTEGER | DEFAULT 0 | 읽은 페이지 수 |
| was_locked | BOOLEAN | DEFAULT false | 폰잠금 사용 여부 |
| platform | VARCHAR(20) | NOT NULL | 플랫폼 (android/ios/web) |
| created_at | TIMESTAMPTZ | NOT NULL | 생성일시 |

### 3.6 subscriptions (구독)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | UUID | PK | 구독 ID |
| user_id | UUID | FK, NOT NULL | 사용자 ID |
| plan | VARCHAR(50) | NOT NULL | 플랜 (premium/premium_plus) |
| platform | VARCHAR(20) | NOT NULL | 결제 플랫폼 (google/apple/stripe) |
| store_txn_id | VARCHAR(255) | NOT NULL | 스토어 트랜잭션 ID |
| started_at | TIMESTAMPTZ | NOT NULL | 시작일 |
| expires_at | TIMESTAMPTZ | NOT NULL | 만료일 |
| status | VARCHAR(20) | NOT NULL | 상태 (active/cancelled/expired) |
| created_at | TIMESTAMPTZ | NOT NULL | 생성일시 |
| updated_at | TIMESTAMPTZ | NOT NULL | 수정일시 |

---

## 4. 인덱스 설계

```sql
-- 성능 최적화를 위한 주요 인덱스

-- users
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_provider ON users(provider, provider_id) WHERE provider_id IS NOT NULL;
CREATE INDEX idx_users_status ON users(status);

-- user_profiles  
CREATE UNIQUE INDEX idx_profiles_nickname ON user_profiles(nickname);
CREATE INDEX idx_profiles_level ON user_profiles(level DESC);

-- user_books
CREATE INDEX idx_user_books_user ON user_books(user_id);
CREATE INDEX idx_user_books_user_status ON user_books(user_id, status);
CREATE UNIQUE INDEX idx_user_books_unique ON user_books(user_id, book_id);

-- books
CREATE UNIQUE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_title_gin ON books USING GIN (to_tsvector('korean', title));

-- reading_sessions
CREATE INDEX idx_sessions_user_book ON reading_sessions(user_book_id);
CREATE INDEX idx_sessions_date ON reading_sessions(started_at DESC);
CREATE INDEX idx_sessions_platform ON reading_sessions(platform);

-- quotes
CREATE INDEX idx_quotes_user ON quotes(user_id);
CREATE INDEX idx_quotes_book ON quotes(book_id);
CREATE INDEX idx_quotes_public_recent ON quotes(is_public, created_at DESC) WHERE is_public = true;
CREATE INDEX idx_quotes_content_gin ON quotes USING GIN (to_tsvector('korean', content));

-- reviews
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_public_recent ON reviews(is_public, created_at DESC) WHERE is_public = true;

-- bookstores (PostGIS)
CREATE INDEX idx_bookstores_location ON bookstores USING GIST (
  ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
);
CREATE INDEX idx_bookstores_verified ON bookstores(is_verified) WHERE is_verified = true;

-- follows
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);

-- notifications
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC) 
  WHERE is_read = false;

-- subscriptions
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_active ON subscriptions(user_id, expires_at) 
  WHERE status = 'active';
```

---

## 5. API 스펙

### 5.1 기본 정보

- **Base URL:** `https://api.readlock.app/v1`
- **인증:** Bearer Token (JWT)
- **Content-Type:** `application/json`

### 5.2 공통 응답 형식

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "BOOK_003",
    "message": "이미 책장에 추가된 도서입니다.",
    "details": { ... }
  }
}
```

---

### 5.3 인증 API

#### POST /auth/register
회원가입

```json
// Request
{
  "email": "user@example.com",
  "password": "securePassword123!",
  "nickname": "독서왕"
}

// Response 201
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "nickname": "독서왕"
    },
    "tokens": {
      "accessToken": "eyJhbG...",
      "refreshToken": "eyJhbG...",
      "expiresIn": 3600
    }
  }
}
```

#### POST /auth/login
로그인

```json
// Request
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

#### POST /auth/oauth/{provider}
소셜 로그인 (google/apple/kakao)

```json
// Request
{
  "idToken": "firebase_id_token_or_oauth_token"
}

// Response 200
{
  "success": true,
  "data": {
    "user": { ... },
    "tokens": { ... },
    "isNewUser": false
  }
}
```

#### POST /auth/refresh
토큰 갱신

```json
// Request
{
  "refreshToken": "eyJhbG..."
}
```

#### DELETE /auth/logout
로그아웃

#### PATCH /auth/fcm-token
FCM 토큰 업데이트

```json
// Request
{
  "fcmToken": "firebase_token",
  "platform": "android"  // android/ios/web
}
```

---

### 5.4 도서 API

#### GET /books/search
도서 검색 (네이버 책 API 프록시)

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| query | string | ✓ | 검색어 |
| display | int | | 결과 개수 (기본 10, 최대 100) |
| start | int | | 시작 위치 (기본 1) |
| sort | string | | 정렬 (sim/date) |

```json
// Response 200
{
  "success": true,
  "data": {
    "total": 1234,
    "start": 1,
    "display": 10,
    "items": [
      {
        "isbn": "9788932917245",
        "title": "데미안",
        "author": "헤르만 헤세",
        "publisher": "민음사",
        "publishedDate": "2009-01-25",
        "description": "...",
        "coverImage": "https://...",
        "pageCount": 280,
        "link": "https://book.naver.com/..."
      }
    ]
  }
}
```

#### GET /books/{isbn}
ISBN으로 도서 상세 조회

#### POST /books/scan
바코드 스캔으로 도서 조회

```json
// Request
{
  "isbn": "9788932917245"
}
```

---

### 5.5 내 책장 API

#### GET /me/books
내 책장 목록

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| status | string | | 필터 (wishlist/reading/completed) |
| page | int | | 페이지 번호 |
| limit | int | | 페이지 크기 |

```json
// Response 200
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "book": {
          "id": "uuid",
          "isbn": "9788932917245",
          "title": "데미안",
          "author": "헤르만 헤세",
          "coverImage": "https://..."
        },
        "status": "reading",
        "currentPage": 145,
        "totalPages": 280,
        "progress": 51.8,
        "startedAt": "2025-01-15T10:00:00Z",
        "finishedAt": null
      }
    ]
  },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

#### POST /me/books
책장에 도서 추가

```json
// Request
{
  "isbn": "9788932917245",
  "status": "wishlist",
  "totalPages": 280  // optional
}

// Response 201
{
  "success": true,
  "data": {
    "id": "uuid",
    "book": { ... },
    "status": "wishlist"
  }
}
```

#### PATCH /me/books/{id}
독서 상태/진행률 업데이트

```json
// Request
{
  "status": "reading",
  "currentPage": 150
}
```

#### DELETE /me/books/{id}
책장에서 도서 삭제

---

### 5.6 독서 세션 API

#### POST /reading-sessions
독서 세션 시작

```json
// Request
{
  "userBookId": "uuid",
  "platform": "android"
}

// Response 201
{
  "success": true,
  "data": {
    "sessionId": "uuid",
    "startedAt": "2025-01-22T10:00:00Z",
    "book": {
      "title": "데미안",
      "currentPage": 145
    }
  }
}
```

#### PATCH /reading-sessions/{id}/end
독서 세션 종료

```json
// Request
{
  "pagesRead": 20,
  "wasLocked": true
}

// Response 200
{
  "success": true,
  "data": {
    "sessionId": "uuid",
    "duration": 1800,
    "pagesRead": 20,
    "rewards": {
      "coinsEarned": 30,
      "expEarned": 50,
      "newBadges": []
    },
    "streakDays": 7,
    "dailyGoalProgress": {
      "target": 30,
      "current": 45,
      "completed": true
    }
  }
}
```

#### GET /me/reading-stats
독서 통계

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| period | string | 기간 (week/month/year/all) |

```json
// Response 200
{
  "success": true,
  "data": {
    "totalReadingMinutes": 2160,
    "totalBooksCompleted": 12,
    "totalPagesRead": 3456,
    "averageSessionMinutes": 30,
    "currentStreak": 7,
    "longestStreak": 21,
    "platformBreakdown": {
      "android": 65,
      "ios": 30,
      "web": 5
    },
    "dailyStats": [
      { "date": "2025-01-22", "minutes": 45, "pages": 30 }
    ],
    "monthlyGoal": {
      "targetMinutes": 900,
      "currentMinutes": 680,
      "percentage": 75.6
    }
  }
}
```

---

### 5.7 커뮤니티 API

#### POST /quotes
책속의 한줄 등록

```json
// Request
{
  "bookId": "uuid",
  "content": "새는 알에서 나오려고 투쟁한다.",
  "pageNumber": 89,
  "memo": "성장통에 대한 메타포"
}
```

#### GET /quotes
인용구 피드

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| bookId | uuid | 특정 도서 필터 |
| userId | uuid | 특정 사용자 필터 |
| following | bool | 팔로잉만 |
| sort | string | 정렬 (recent/popular) |

#### POST /quotes/{id}/like
인용구 좋아요

#### DELETE /quotes/{id}/like
인용구 좋아요 취소

#### POST /reviews
감상평 등록

```json
// Request
{
  "bookId": "uuid",
  "rating": 4.5,
  "content": "청춘의 혼란과 자아 찾기를 아름답게 그려낸 작품",
  "hasSpoiler": false
}
```

#### GET /reviews
감상평 목록

#### GET /feed
통합 피드 (인용구 + 감상평)

---

### 5.8 소셜 API

#### POST /users/{id}/follow
팔로우

#### DELETE /users/{id}/follow
언팔로우

#### GET /me/followers
팔로워 목록

#### GET /me/following
팔로잉 목록

#### GET /users/{id}/profile
사용자 프로필 조회

---

### 5.9 독립서점 API

#### GET /bookstores
주변 독립서점

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| lat | float | ✓ | 위도 |
| lng | float | ✓ | 경도 |
| radius | int | | 반경 (m, 기본 5000) |
| features | string[] | | 필터 (cafe/kids/event 등) |

```json
// Response 200
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "땡스북스",
        "address": "서울시 마포구 연남동 223-77",
        "lat": 37.5665,
        "lng": 126.9241,
        "distance": 850,
        "phone": "02-123-4567",
        "hours": {
          "mon": "12:00-21:00",
          "tue": "12:00-21:00",
          "sun": "closed"
        },
        "features": ["cafe", "event", "indie"],
        "rating": 4.7,
        "imageUrl": "https://...",
        "isVerified": true
      }
    ]
  }
}
```

#### POST /bookstores/{id}/checkin
서점 방문 체크인

```json
// Request
{
  "lat": 37.5665,
  "lng": 126.9241
}
```

#### POST /bookstores/{id}/reviews
서점 리뷰

---

### 5.10 AI 추천 API

#### GET /recommendations
맞춤 도서 추천

```json
// Response 200
{
  "success": true,
  "data": {
    "items": [
      {
        "book": {
          "id": "uuid",
          "title": "싯다르타",
          "author": "헤르만 헤세",
          "coverImage": "https://..."
        },
        "score": 0.92,
        "reasons": [
          "헤르만 헤세의 다른 작품을 즐겨 읽으셨습니다",
          "비슷한 성향의 독자 89%가 높게 평가했습니다"
        ]
      }
    ]
  }
}
```

#### GET /me/reading-profile
독서 성향 프로파일

```json
// Response 200
{
  "success": true,
  "data": {
    "profileType": "explorer",
    "profileName": "탐구형 독서가",
    "description": "다양한 장르를 넘나들며 깊이 있는 사유를 즐기는 독자",
    "traits": {
      "diversity": 0.85,
      "depth": 0.92,
      "consistency": 0.78,
      "social": 0.65
    },
    "topGenres": [
      { "genre": "문학/소설", "percentage": 45 },
      { "genre": "인문", "percentage": 30 }
    ],
    "topAuthors": ["헤르만 헤세", "무라카미 하루키"],
    "readingPattern": {
      "preferredTime": "evening",
      "averageSessionMinutes": 35,
      "peakDay": "sunday"
    }
  }
}
```

---

### 5.11 게이미피케이션 API

#### GET /me/avatar
내 아바타

#### PATCH /me/avatar
아바타 커스터마이징

```json
// Request
{
  "headItemId": "uuid",
  "bodyItemId": "uuid",
  "faceItemId": "uuid",
  "accessoryId": "uuid"
}
```

#### GET /me/room
마이룸

#### PATCH /me/room
마이룸 꾸미기

```json
// Request
{
  "themeId": "uuid",
  "items": [
    { "itemId": "uuid", "x": 100, "y": 200, "rotation": 0 }
  ]
}
```

#### GET /shop/items
상점 아이템 목록

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| category | string | avatar/room |
| type | string | head/body/furniture 등 |

#### POST /shop/purchase
아이템 구매

```json
// Request
{
  "itemId": "uuid",
  "paymentType": "coins"  // coins/cash
}
```

#### GET /me/badges
내 뱃지 목록

---

### 5.12 결제 API

#### POST /subscriptions/verify
구독 영수증 검증

```json
// Request (Android)
{
  "platform": "google",
  "productId": "premium_monthly",
  "purchaseToken": "google_purchase_token"
}

// Request (iOS)
{
  "platform": "apple",
  "receiptData": "base64_encoded_receipt"
}

// Response 200
{
  "success": true,
  "data": {
    "subscriptionId": "uuid",
    "plan": "premium",
    "expiresAt": "2025-02-22T00:00:00Z",
    "isActive": true
  }
}
```

#### GET /me/subscription
내 구독 상태

#### POST /subscriptions/cancel
구독 취소

---

## 6. 에러 코드

| 코드 | HTTP | 설명 |
|------|:----:|------|
| AUTH_001 | 401 | 인증 토큰 없음 |
| AUTH_002 | 401 | 토큰 만료 |
| AUTH_003 | 401 | 잘못된 토큰 |
| AUTH_004 | 403 | 권한 없음 |
| AUTH_005 | 400 | 잘못된 소셜 토큰 |
| USER_001 | 404 | 사용자 없음 |
| USER_002 | 409 | 이메일 중복 |
| USER_003 | 409 | 닉네임 중복 |
| BOOK_001 | 404 | 도서 없음 |
| BOOK_002 | 400 | 잘못된 ISBN |
| BOOK_003 | 409 | 이미 책장에 있음 |
| BOOK_004 | 404 | 책장에 없는 도서 |
| SESSION_001 | 400 | 이미 진행 중인 세션 |
| SESSION_002 | 404 | 세션 없음 |
| SHOP_001 | 400 | 코인 부족 |
| SHOP_002 | 400 | 레벨 미달 |
| SHOP_003 | 404 | 아이템 없음 |
| SHOP_004 | 409 | 이미 보유한 아이템 |
| SUB_001 | 400 | 영수증 검증 실패 |
| SUB_002 | 409 | 이미 활성 구독 있음 |
| RATE_001 | 429 | 요청 한도 초과 |

---

## 7. Flutter 모델 정의 (Freezed)

```dart
// lib/domain/entities/book.dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'book.freezed.dart';
part 'book.g.dart';

@freezed
class Book with _$Book {
  const factory Book({
    required String id,
    required String isbn,
    required String title,
    required String author,
    String? publisher,
    DateTime? publishedDate,
    String? description,
    String? coverImage,
    String? category,
    int? pageCount,
    String? naverLink,
  }) = _Book;

  factory Book.fromJson(Map<String, dynamic> json) => _$BookFromJson(json);
}

@freezed
class UserBook with _$UserBook {
  const factory UserBook({
    required String id,
    required Book book,
    required BookStatus status,
    @Default(0) int currentPage,
    int? totalPages,
    DateTime? startedAt,
    DateTime? finishedAt,
    required DateTime createdAt,
  }) = _UserBook;

  factory UserBook.fromJson(Map<String, dynamic> json) => _$UserBookFromJson(json);
}

enum BookStatus {
  @JsonValue('wishlist') wishlist,
  @JsonValue('reading') reading,
  @JsonValue('completed') completed,
}

@freezed
class ReadingSession with _$ReadingSession {
  const factory ReadingSession({
    required String id,
    required String userBookId,
    required DateTime startedAt,
    DateTime? endedAt,
    int? durationSec,
    @Default(0) int pagesRead,
    @Default(false) bool wasLocked,
    required String platform,
  }) = _ReadingSession;

  factory ReadingSession.fromJson(Map<String, dynamic> json) => 
      _$ReadingSessionFromJson(json);
}

@freezed
class Quote with _$Quote {
  const factory Quote({
    required String id,
    required String userId,
    required String bookId,
    required String content,
    int? pageNumber,
    String? memo,
    @Default(0) int likesCount,
    @Default(true) bool isPublic,
    required DateTime createdAt,
    // Joined fields
    Book? book,
    UserProfile? author,
    @Default(false) bool isLikedByMe,
  }) = _Quote;

  factory Quote.fromJson(Map<String, dynamic> json) => _$QuoteFromJson(json);
}

@freezed
class Review with _$Review {
  const factory Review({
    required String id,
    required String userId,
    required String bookId,
    required double rating,
    required String content,
    @Default(false) bool hasSpoiler,
    @Default(0) int likesCount,
    @Default(true) bool isPublic,
    required DateTime createdAt,
    // Joined fields
    Book? book,
    UserProfile? author,
  }) = _Review;

  factory Review.fromJson(Map<String, dynamic> json) => _$ReviewFromJson(json);
}

@freezed
class UserProfile with _$UserProfile {
  const factory UserProfile({
    required String id,
    required String userId,
    required String nickname,
    String? bio,
    String? profileImage,
    @Default(30) int readingGoalMin,
    @Default(true) bool isPublic,
    @Default(1) int level,
    @Default(0) int exp,
    @Default(0) int coins,
    DateTime? premiumUntil,
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) => 
      _$UserProfileFromJson(json);
  
  bool get isPremium => 
      premiumUntil != null && premiumUntil!.isAfter(DateTime.now());
}

@freezed
class Bookstore with _$Bookstore {
  const factory Bookstore({
    required String id,
    required String name,
    required String address,
    required double lat,
    required double lng,
    int? distance,
    String? phone,
    Map<String, String>? hours,
    String? description,
    @Default([]) List<String> features,
    String? imageUrl,
    @Default(0.0) double rating,
    @Default(false) bool isVerified,
  }) = _Bookstore;

  factory Bookstore.fromJson(Map<String, dynamic> json) => 
      _$BookstoreFromJson(json);
}

@freezed
class ReadingStats with _$ReadingStats {
  const factory ReadingStats({
    required int totalReadingMinutes,
    required int totalBooksCompleted,
    required int totalPagesRead,
    required int averageSessionMinutes,
    required int currentStreak,
    required int longestStreak,
    required Map<String, int> platformBreakdown,
    required List<DailyStat> dailyStats,
    required MonthlyGoal monthlyGoal,
  }) = _ReadingStats;

  factory ReadingStats.fromJson(Map<String, dynamic> json) => 
      _$ReadingStatsFromJson(json);
}

@freezed
class DailyStat with _$DailyStat {
  const factory DailyStat({
    required DateTime date,
    required int minutes,
    required int pages,
  }) = _DailyStat;

  factory DailyStat.fromJson(Map<String, dynamic> json) => 
      _$DailyStatFromJson(json);
}

@freezed  
class MonthlyGoal with _$MonthlyGoal {
  const factory MonthlyGoal({
    required int targetMinutes,
    required int currentMinutes,
    required double percentage,
  }) = _MonthlyGoal;

  factory MonthlyGoal.fromJson(Map<String, dynamic> json) => 
      _$MonthlyGoalFromJson(json);
}

@freezed
class ReadingProfile with _$ReadingProfile {
  const factory ReadingProfile({
    required String profileType,
    required String profileName,
    required String description,
    required Map<String, double> traits,
    required List<GenreStat> topGenres,
    required List<String> topAuthors,
    required ReadingPattern readingPattern,
  }) = _ReadingProfile;

  factory ReadingProfile.fromJson(Map<String, dynamic> json) => 
      _$ReadingProfileFromJson(json);
}
```

---

## 8. 마이그레이션 스크립트

```sql
-- migrations/001_initial.sql

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    provider VARCHAR(50) NOT NULL DEFAULT 'local',
    provider_id VARCHAR(255),
    fcm_token VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

-- User profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    bio TEXT,
    profile_image VARCHAR(500),
    reading_goal_min INTEGER DEFAULT 30,
    is_public BOOLEAN DEFAULT true,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    premium_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Books table
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255) NOT NULL,
    publisher VARCHAR(255),
    published_date DATE,
    description TEXT,
    cover_image VARCHAR(500),
    category VARCHAR(100),
    page_count INTEGER,
    naver_link VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User books (bookshelf)
CREATE TABLE user_books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    current_page INTEGER DEFAULT 0,
    total_pages INTEGER,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, book_id)
);

-- Reading sessions
CREATE TABLE reading_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_book_id UUID NOT NULL REFERENCES user_books(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_sec INTEGER,
    pages_read INTEGER DEFAULT 0,
    was_locked BOOLEAN DEFAULT false,
    platform VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    page_number INTEGER,
    memo TEXT,
    likes_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Quote likes
CREATE TABLE quote_likes (
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (quote_id, user_id)
);

-- Reviews
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rating DECIMAL(2,1) NOT NULL CHECK (rating >= 1 AND rating <= 5),
    content TEXT NOT NULL,
    has_spoiler BOOLEAN DEFAULT false,
    likes_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, book_id)
);

-- Bookstores
CREATE TABLE bookstores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    phone VARCHAR(20),
    hours JSONB,
    description TEXT,
    features TEXT[],
    image_url VARCHAR(500),
    rating_avg DECIMAL(2,1) DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Follows
CREATE TABLE follows (
    follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id),
    CHECK (follower_id != following_id)
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    store_txn_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_books_user_status ON user_books(user_id, status);
CREATE INDEX idx_sessions_user_book ON reading_sessions(user_book_id);
CREATE INDEX idx_sessions_date ON reading_sessions(started_at DESC);
CREATE INDEX idx_quotes_public_recent ON quotes(is_public, created_at DESC) WHERE is_public = true;
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_bookstores_location ON bookstores USING GIST (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
);
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_user_books_updated_at BEFORE UPDATE ON user_books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```
