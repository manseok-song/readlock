/// API endpoint constants
class ApiEndpoints {
  ApiEndpoints._();

  // Base URL - configure based on environment
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.readlock.app/v1',
  );

  // Auth endpoints
  static const String authRegister = '/auth/register';
  static const String authLogin = '/auth/login';
  static const String authOAuth = '/auth/oauth'; // + /{provider}
  static const String authRefresh = '/auth/refresh';
  static const String authLogout = '/auth/logout';
  static const String authFcmToken = '/auth/fcm-token';

  // User endpoints
  static const String me = '/me';
  static const String meProfile = '/me/profile';
  static const String meBooks = '/me/books';
  static const String meReadingStats = '/me/reading-stats';
  static const String meAvatar = '/me/avatar';
  static const String meRoom = '/me/room';
  static const String meBadges = '/me/badges';
  static const String meSubscription = '/me/subscription';
  static const String meFollowers = '/me/followers';
  static const String meFollowing = '/me/following';

  // Book endpoints
  static const String books = '/books';
  static const String booksSearch = '/books/search';
  static const String booksScan = '/books/scan';

  // Reading session endpoints
  static const String readingSessions = '/reading-sessions';

  // Community endpoints
  static const String quotes = '/quotes';
  static const String reviews = '/reviews';
  static const String feed = '/feed';

  // Social endpoints
  static const String users = '/users';

  // Bookstore endpoints
  static const String bookstores = '/bookstores';

  // AI endpoints
  static const String recommendations = '/recommendations';
  static const String readingProfile = '/me/reading-profile';

  // Shop endpoints
  static const String shopItems = '/shop/items';
  static const String shopPurchase = '/shop/purchase';

  // Subscription endpoints
  static const String subscriptionsVerify = '/subscriptions/verify';
  static const String subscriptionsCancel = '/subscriptions/cancel';

  // Notifications
  static const String notifications = '/notifications';
}
