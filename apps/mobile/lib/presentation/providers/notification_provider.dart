import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../data/datasources/remote/api_client.dart';

part 'notification_provider.freezed.dart';

// Notification Entity
class AppNotification {
  final String id;
  final String type;
  final String title;
  final String body;
  final Map<String, dynamic>? data;
  final bool isRead;
  final DateTime createdAt;

  AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    this.data,
    required this.isRead,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'],
      type: json['type'],
      title: json['title'],
      body: json['body'],
      data: json['data'],
      isRead: json['is_read'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

// Notification Settings
class NotificationSettings {
  final bool pushEnabled;
  final bool readingReminder;
  final String readingReminderTime;
  final bool socialNotifications;
  final bool marketingNotifications;
  final bool streakReminder;
  final bool goalNotifications;

  NotificationSettings({
    required this.pushEnabled,
    required this.readingReminder,
    required this.readingReminderTime,
    required this.socialNotifications,
    required this.marketingNotifications,
    required this.streakReminder,
    required this.goalNotifications,
  });

  factory NotificationSettings.fromJson(Map<String, dynamic> json) {
    return NotificationSettings(
      pushEnabled: json['push_enabled'] ?? true,
      readingReminder: json['reading_reminder'] ?? true,
      readingReminderTime: json['reading_reminder_time'] ?? '21:00',
      socialNotifications: json['social_notifications'] ?? true,
      marketingNotifications: json['marketing_notifications'] ?? false,
      streakReminder: json['streak_reminder'] ?? true,
      goalNotifications: json['goal_notifications'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'push_enabled': pushEnabled,
      'reading_reminder': readingReminder,
      'reading_reminder_time': readingReminderTime,
      'social_notifications': socialNotifications,
      'marketing_notifications': marketingNotifications,
      'streak_reminder': streakReminder,
      'goal_notifications': goalNotifications,
    };
  }

  NotificationSettings copyWith({
    bool? pushEnabled,
    bool? readingReminder,
    String? readingReminderTime,
    bool? socialNotifications,
    bool? marketingNotifications,
    bool? streakReminder,
    bool? goalNotifications,
  }) {
    return NotificationSettings(
      pushEnabled: pushEnabled ?? this.pushEnabled,
      readingReminder: readingReminder ?? this.readingReminder,
      readingReminderTime: readingReminderTime ?? this.readingReminderTime,
      socialNotifications: socialNotifications ?? this.socialNotifications,
      marketingNotifications: marketingNotifications ?? this.marketingNotifications,
      streakReminder: streakReminder ?? this.streakReminder,
      goalNotifications: goalNotifications ?? this.goalNotifications,
    );
  }
}

// Notification State
@freezed
class NotificationState with _$NotificationState {
  const factory NotificationState({
    @Default([]) List<AppNotification> notifications,
    @Default(0) int unreadCount,
    @Default(false) bool isLoading,
    @Default(false) bool hasMore,
    @Default(1) int currentPage,
    String? error,
  }) = _NotificationState;
}

// Settings State
@freezed
class NotificationSettingsState with _$NotificationSettingsState {
  const factory NotificationSettingsState({
    NotificationSettings? settings,
    @Default(false) bool isLoading,
    @Default(false) bool isSaving,
    String? error,
  }) = _NotificationSettingsState;
}

// Notification Provider
class NotificationNotifier extends StateNotifier<NotificationState> {
  final ApiClient _apiClient;

  NotificationNotifier(this._apiClient) : super(const NotificationState());

  Future<void> loadNotifications({bool refresh = false}) async {
    if (state.isLoading) return;

    state = state.copyWith(
      isLoading: true,
      error: null,
      currentPage: refresh ? 1 : state.currentPage,
    );

    try {
      final response = await _apiClient.get(
        '/notifications',
        queryParameters: {
          'page': refresh ? 1 : state.currentPage,
          'page_size': 20,
        },
      );

      final notifications = (response.data['items'] as List)
          .map((json) => AppNotification.fromJson(json))
          .toList();

      state = state.copyWith(
        notifications: refresh ? notifications : [...state.notifications, ...notifications],
        unreadCount: response.data['unread_count'] ?? 0,
        isLoading: false,
        hasMore: response.data['has_more'] ?? false,
        currentPage: refresh ? 2 : state.currentPage + 1,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadUnreadCount() async {
    try {
      final response = await _apiClient.get('/notifications/unread-count');
      state = state.copyWith(unreadCount: response.data['count'] ?? 0);
    } catch (e) {
      // Silent fail
    }
  }

  Future<void> markAsRead(String notificationId) async {
    try {
      await _apiClient.post('/notifications/$notificationId/read');

      final updatedNotifications = state.notifications.map((n) {
        if (n.id == notificationId) {
          return AppNotification(
            id: n.id,
            type: n.type,
            title: n.title,
            body: n.body,
            data: n.data,
            isRead: true,
            createdAt: n.createdAt,
          );
        }
        return n;
      }).toList();

      state = state.copyWith(
        notifications: updatedNotifications,
        unreadCount: state.unreadCount > 0 ? state.unreadCount - 1 : 0,
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> markAllAsRead() async {
    try {
      await _apiClient.post('/notifications/read-all');

      final updatedNotifications = state.notifications.map((n) {
        return AppNotification(
          id: n.id,
          type: n.type,
          title: n.title,
          body: n.body,
          data: n.data,
          isRead: true,
          createdAt: n.createdAt,
        );
      }).toList();

      state = state.copyWith(
        notifications: updatedNotifications,
        unreadCount: 0,
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }
}

// Settings Provider
class NotificationSettingsNotifier extends StateNotifier<NotificationSettingsState> {
  final ApiClient _apiClient;

  NotificationSettingsNotifier(this._apiClient) : super(const NotificationSettingsState());

  Future<void> loadSettings() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/notifications/settings');
      final settings = NotificationSettings.fromJson(response.data);

      state = state.copyWith(settings: settings, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> updateSettings(NotificationSettings settings) async {
    state = state.copyWith(isSaving: true, error: null);

    try {
      await _apiClient.put('/notifications/settings', data: settings.toJson());

      state = state.copyWith(settings: settings, isSaving: false);
      return true;
    } catch (e) {
      state = state.copyWith(isSaving: false, error: e.toString());
      return false;
    }
  }

  Future<void> registerDevice(String token, String platform) async {
    try {
      await _apiClient.post('/notifications/device', data: {
        'token': token,
        'platform': platform,
      });
    } catch (e) {
      // Silent fail
    }
  }

  Future<void> unregisterDevice(String token) async {
    try {
      await _apiClient.delete(
        '/notifications/device',
        queryParameters: {'token': token},
      );
    } catch (e) {
      // Silent fail
    }
  }
}

// Providers
final notificationProvider = StateNotifierProvider<NotificationNotifier, NotificationState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return NotificationNotifier(apiClient);
});

final notificationSettingsProvider = StateNotifierProvider<NotificationSettingsNotifier, NotificationSettingsState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return NotificationSettingsNotifier(apiClient);
});

final unreadCountProvider = Provider<int>((ref) {
  return ref.watch(notificationProvider).unreadCount;
});
