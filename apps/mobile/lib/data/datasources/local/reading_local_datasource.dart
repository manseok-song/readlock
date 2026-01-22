import 'package:hive/hive.dart';
import 'package:uuid/uuid.dart';

import '../../../domain/entities/reading_session.dart';

/// Local datasource for reading session data
class ReadingLocalDatasource {
  static const _sessionsBoxName = 'reading_sessions_cache';
  static const _activeSessionKey = 'active_session';
  static const _pendingSyncBoxName = 'pending_sync_sessions';

  late Box<Map> _sessionsBox;
  late Box<Map> _pendingSyncBox;

  final _uuid = const Uuid();

  Future<void> init() async {
    _sessionsBox = await Hive.openBox<Map>(_sessionsBoxName);
    _pendingSyncBox = await Hive.openBox<Map>(_pendingSyncBoxName);
  }

  // Active session management
  Future<void> saveActiveSession(ReadingSession session) async {
    await _sessionsBox.put(_activeSessionKey, session.toJson());
  }

  Future<ReadingSession?> getActiveSession() async {
    final data = _sessionsBox.get(_activeSessionKey);
    if (data == null) return null;
    return ReadingSession.fromJson(Map<String, dynamic>.from(data));
  }

  Future<void> clearActiveSession() async {
    await _sessionsBox.delete(_activeSessionKey);
  }

  // Offline session creation
  Future<ReadingSession> createOfflineSession({
    required String userBookId,
    required int startPage,
  }) async {
    final session = ReadingSession(
      id: 'offline_${_uuid.v4()}',
      userBookId: userBookId,
      startTime: DateTime.now(),
      startPage: startPage,
      endTime: null,
      endPage: null,
      duration: 0,
      focusScore: null,
      isOffline: true,
    );

    await saveActiveSession(session);
    await _pendingSyncBox.put(session.id, session.toJson());

    return session;
  }

  // Session state management
  Future<void> pauseSession(String sessionId) async {
    final session = await getActiveSession();
    if (session != null && session.id == sessionId) {
      final updated = session.copyWith(
        pausedAt: DateTime.now(),
        isPaused: true,
      );
      await saveActiveSession(updated);
    }
  }

  Future<void> resumeSession(String sessionId) async {
    final session = await getActiveSession();
    if (session != null && session.id == sessionId) {
      final pauseDuration = session.pausedAt != null
          ? DateTime.now().difference(session.pausedAt!)
          : Duration.zero;

      final updated = session.copyWith(
        pausedAt: null,
        isPaused: false,
        totalPauseDuration: (session.totalPauseDuration ?? Duration.zero) + pauseDuration,
      );
      await saveActiveSession(updated);
    }
  }

  // Sync management
  Future<void> markSessionForSync({
    required String sessionId,
    required int endPage,
    int? focusScore,
  }) async {
    final session = await getActiveSession();
    if (session != null && session.id == sessionId) {
      final endedSession = session.copyWith(
        endTime: DateTime.now(),
        endPage: endPage,
        focusScore: focusScore,
        needsSync: true,
      );
      await _pendingSyncBox.put(sessionId, endedSession.toJson());
    }
  }

  Future<List<ReadingSession>> getPendingSyncSessions() async {
    return _pendingSyncBox.values.map((data) {
      return ReadingSession.fromJson(Map<String, dynamic>.from(data));
    }).toList();
  }

  Future<void> markSessionSynced(String sessionId) async {
    await _pendingSyncBox.delete(sessionId);
  }

  // Estimate session result for offline mode
  Future<ReadingSessionResult> estimateSessionResult({
    required String sessionId,
    required int endPage,
  }) async {
    final session = await getActiveSession();

    final duration = session != null
        ? DateTime.now().difference(session.startTime).inSeconds
        : 0;

    final pagesRead = session != null
        ? endPage - session.startPage
        : 0;

    return ReadingSessionResult(
      sessionId: sessionId,
      duration: duration,
      pagesRead: pagesRead,
      streakDays: 1, // Will be updated after sync
      rewards: SessionRewards(
        coinsEarned: (duration ~/ 60) * 10, // 10 coins per minute estimate
        expEarned: pagesRead * 5, // 5 exp per page estimate
        bonusCoins: 0,
        bonusExp: 0,
      ),
      isOffline: true,
    );
  }

  // Session history caching
  Future<void> cacheSessions(List<ReadingSession> sessions) async {
    for (final session in sessions) {
      await _sessionsBox.put('history_${session.id}', session.toJson());
    }
  }

  Future<List<ReadingSession>> getCachedSessions({
    String? userBookId,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    final allSessions = _sessionsBox.keys
        .where((key) => key.toString().startsWith('history_'))
        .map((key) {
          final data = _sessionsBox.get(key);
          if (data == null) return null;
          return ReadingSession.fromJson(Map<String, dynamic>.from(data));
        })
        .whereType<ReadingSession>()
        .toList();

    return allSessions.where((session) {
      if (userBookId != null && session.userBookId != userBookId) {
        return false;
      }
      if (startDate != null && session.startTime.isBefore(startDate)) {
        return false;
      }
      if (endDate != null && session.startTime.isAfter(endDate)) {
        return false;
      }
      return true;
    }).toList();
  }

  // Clear all
  Future<void> clearAll() async {
    await _sessionsBox.clear();
    await _pendingSyncBox.clear();
  }
}
