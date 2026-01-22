/// Local storage key constants
class StorageKeys {
  StorageKeys._();

  // Hive box names
  static const String settingsBox = 'settings';
  static const String cacheBox = 'cache';
  static const String userBox = 'user';

  // Secure storage keys
  static const String accessToken = 'access_token';
  static const String refreshToken = 'refresh_token';
  static const String userId = 'user_id';

  // Settings keys
  static const String themeMode = 'theme_mode';
  static const String locale = 'locale';
  static const String onboardingCompleted = 'onboarding_completed';
  static const String notificationsEnabled = 'notifications_enabled';
  static const String readingGoalMinutes = 'reading_goal_minutes';
  static const String lockModeEnabled = 'lock_mode_enabled';
  static const String dndModeEnabled = 'dnd_mode_enabled';

  // Cache keys
  static const String cachedUser = 'cached_user';
  static const String cachedBooks = 'cached_books';
  static const String cachedFeed = 'cached_feed';
  static const String lastFetchTime = 'last_fetch_time';

  // Session keys
  static const String currentSession = 'current_session';
  static const String sessionStartTime = 'session_start_time';
}
