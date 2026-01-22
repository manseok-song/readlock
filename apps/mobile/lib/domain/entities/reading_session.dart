import 'package:freezed_annotation/freezed_annotation.dart';

part 'reading_session.freezed.dart';
part 'reading_session.g.dart';

@freezed
class ReadingSession with _$ReadingSession {
  const factory ReadingSession({
    required String id,
    required String userBookId,
    required DateTime startTime,
    DateTime? endTime,
    required int startPage,
    int? endPage,
    @Default(0) int duration,
    int? focusScore,
    @Default(false) bool isOffline,
    @Default(false) bool needsSync,
    DateTime? pausedAt,
    @Default(false) bool isPaused,
    Duration? totalPauseDuration,
    String? platform,
    DateTime? createdAt,
  }) = _ReadingSession;

  factory ReadingSession.fromJson(Map<String, dynamic> json) =>
      _$ReadingSessionFromJson(json);
}

@freezed
class ReadingSessionResult with _$ReadingSessionResult {
  const factory ReadingSessionResult({
    required String sessionId,
    required int duration,
    required int pagesRead,
    required SessionRewards rewards,
    required int streakDays,
    DailyGoalProgress? dailyGoalProgress,
    @Default(false) bool isOffline,
  }) = _ReadingSessionResult;

  factory ReadingSessionResult.fromJson(Map<String, dynamic> json) =>
      _$ReadingSessionResultFromJson(json);
}

@freezed
class SessionRewards with _$SessionRewards {
  const factory SessionRewards({
    required int coinsEarned,
    required int expEarned,
    @Default(0) int bonusCoins,
    @Default(0) int bonusExp,
    @Default([]) List<Badge> newBadges,
  }) = _SessionRewards;

  factory SessionRewards.fromJson(Map<String, dynamic> json) =>
      _$SessionRewardsFromJson(json);
}

@freezed
class DailyGoalProgress with _$DailyGoalProgress {
  const factory DailyGoalProgress({
    required int target,
    required int current,
    required bool completed,
  }) = _DailyGoalProgress;

  factory DailyGoalProgress.fromJson(Map<String, dynamic> json) =>
      _$DailyGoalProgressFromJson(json);
}

@freezed
class Badge with _$Badge {
  const factory Badge({
    required String id,
    required String name,
    required String description,
    required String iconUrl,
    DateTime? earnedAt,
  }) = _Badge;

  factory Badge.fromJson(Map<String, dynamic> json) => _$BadgeFromJson(json);
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

@freezed
class GenreStat with _$GenreStat {
  const factory GenreStat({
    required String genre,
    required int percentage,
  }) = _GenreStat;

  factory GenreStat.fromJson(Map<String, dynamic> json) =>
      _$GenreStatFromJson(json);
}

@freezed
class ReadingPattern with _$ReadingPattern {
  const factory ReadingPattern({
    required String preferredTime,
    required int averageSessionMinutes,
    required String peakDay,
  }) = _ReadingPattern;

  factory ReadingPattern.fromJson(Map<String, dynamic> json) =>
      _$ReadingPatternFromJson(json);
}
