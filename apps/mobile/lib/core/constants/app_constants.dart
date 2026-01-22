/// Application constants
class AppConstants {
  AppConstants._();

  // App info
  static const String appName = 'ReadLock';
  static const String appVersion = '2.0.0';

  // Reading
  static const int defaultReadingGoalMinutes = 30;
  static const int maxReadingGoalMinutes = 480; // 8 hours
  static const int minReadingGoalMinutes = 5;

  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;

  // Cache
  static const int cacheExpireHours = 24;
  static const int feedCacheExpireMinutes = 5;

  // Validation
  static const int minPasswordLength = 8;
  static const int maxPasswordLength = 128;
  static const int minNicknameLength = 2;
  static const int maxNicknameLength = 20;
  static const int maxBioLength = 200;
  static const int maxQuoteLength = 500;
  static const int maxReviewLength = 2000;

  // ISBN
  static const int isbn10Length = 10;
  static const int isbn13Length = 13;

  // Gamification
  static const int expPerReadingMinute = 2;
  static const int coinsPerReadingMinute = 1;
  static const int bonusCoinsForLockedReading = 10;
  static const int streakBonusMultiplier = 2;

  // Level
  static const int baseExpPerLevel = 100;
  static const double levelExpMultiplier = 1.5;

  // Animation
  static const int defaultAnimationMs = 300;
  static const int longAnimationMs = 500;

  // Image
  static const int maxImageSizeBytes = 5 * 1024 * 1024; // 5MB
  static const int thumbnailSize = 200;
  static const int coverImageWidth = 400;
}
