import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/entities/reading_session.dart';
import '../../data/repositories/reading_repository_impl.dart';
import '../../services/reading_lock_service.dart';

/// Current reading session state
class ReadingState {
  final ReadingSession? activeSession;
  final bool isReading;
  final bool isPaused;
  final int elapsedSeconds;
  final int currentPage;
  final String? error;

  const ReadingState({
    this.activeSession,
    this.isReading = false,
    this.isPaused = false,
    this.elapsedSeconds = 0,
    this.currentPage = 0,
    this.error,
  });

  ReadingState copyWith({
    ReadingSession? activeSession,
    bool? isReading,
    bool? isPaused,
    int? elapsedSeconds,
    int? currentPage,
    String? error,
  }) {
    return ReadingState(
      activeSession: activeSession ?? this.activeSession,
      isReading: isReading ?? this.isReading,
      isPaused: isPaused ?? this.isPaused,
      elapsedSeconds: elapsedSeconds ?? this.elapsedSeconds,
      currentPage: currentPage ?? this.currentPage,
      error: error,
    );
  }
}

/// Reading session notifier
class ReadingNotifier extends StateNotifier<ReadingState> {
  final ReadingRepository _repository;
  final ReadingLockService _lockService;

  Timer? _timer;
  StreamSubscription? _statusSubscription;

  ReadingNotifier({
    required ReadingRepository repository,
    required ReadingLockService lockService,
  })  : _repository = repository,
        _lockService = lockService,
        super(const ReadingState()) {
    _init();
  }

  Future<void> _init() async {
    // Check for active session on startup
    final result = await _repository.getActiveSession();
    result.fold(
      (failure) => null,
      (session) {
        if (session != null) {
          state = state.copyWith(
            activeSession: session,
            isReading: true,
            isPaused: session.isPaused ?? false,
          );
        }
      },
    );

    // Listen to native status changes
    _statusSubscription = _lockService.statusStream.listen(_handleStatusChange);
  }

  void _handleStatusChange(ReadingStatus status) {
    switch (status.status) {
      case 'started':
        _startTimer();
        break;
      case 'paused':
        _stopTimer();
        state = state.copyWith(isPaused: true);
        break;
      case 'resumed':
        _startTimer();
        state = state.copyWith(isPaused: false);
        break;
      case 'stopped':
        _stopTimer();
        break;
      case 'heartbeat':
        state = state.copyWith(elapsedSeconds: status.duration);
        break;
    }
  }

  /// Start a new reading session
  Future<void> startSession({
    required String userBookId,
    required String bookTitle,
    int? startPage,
  }) async {
    state = state.copyWith(error: null);

    final result = await _repository.startSession(
      userBookId: userBookId,
      startPage: startPage,
    );

    result.fold(
      (failure) {
        state = state.copyWith(error: failure.message);
      },
      (session) async {
        state = state.copyWith(
          activeSession: session,
          isReading: true,
          isPaused: false,
          elapsedSeconds: 0,
          currentPage: startPage ?? 0,
        );

        // Start native phone lock
        await _lockService.startReading(
          bookTitle: bookTitle,
          sessionId: session.id,
        );

        _startTimer();
      },
    );
  }

  /// End the current reading session
  Future<ReadingSessionResult?> endSession({
    required int endPage,
    int? focusScore,
  }) async {
    final session = state.activeSession;
    if (session == null) return null;

    // Stop native phone lock
    await _lockService.stopReading();
    _stopTimer();

    final result = await _repository.endSession(
      sessionId: session.id,
      endPage: endPage,
      focusScore: focusScore,
    );

    ReadingSessionResult? sessionResult;

    result.fold(
      (failure) {
        state = state.copyWith(error: failure.message);
      },
      (res) {
        sessionResult = res;
        state = const ReadingState(); // Reset state
      },
    );

    return sessionResult;
  }

  /// Pause the current session
  Future<void> pauseSession() async {
    final session = state.activeSession;
    if (session == null || state.isPaused) return;

    await _lockService.pauseReading();
    await _repository.pauseSession(session.id);

    _stopTimer();
    state = state.copyWith(isPaused: true);
  }

  /// Resume a paused session
  Future<void> resumeSession() async {
    final session = state.activeSession;
    if (session == null || !state.isPaused) return;

    await _lockService.resumeReading();
    await _repository.resumeSession(session.id);

    _startTimer();
    state = state.copyWith(isPaused: false);
  }

  /// Update current page
  void updateCurrentPage(int page) {
    state = state.copyWith(currentPage: page);
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!state.isPaused) {
        state = state.copyWith(elapsedSeconds: state.elapsedSeconds + 1);
      }
    });
  }

  void _stopTimer() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void dispose() {
    _timer?.cancel();
    _statusSubscription?.cancel();
    super.dispose();
  }
}

/// Reading state provider
final readingProvider = StateNotifierProvider<ReadingNotifier, ReadingState>((ref) {
  // TODO: Get proper repository and service instances
  throw UnimplementedError('Provider not properly initialized');
});

/// Reading stats provider
final readingStatsProvider = FutureProvider.family<ReadingStats?, String>((ref, period) async {
  // TODO: Implement reading stats fetching
  return null;
});

/// Daily stats provider for charts
final dailyStatsProvider = FutureProvider.family<List<DailyStat>, int>((ref, days) async {
  // TODO: Implement daily stats fetching
  return [];
});

/// Reading streak provider
final readingStreakProvider = FutureProvider<ReadingStreak?>((ref) async {
  // TODO: Implement streak fetching
  return null;
});

/// Reading profile provider
final readingProfileProvider = FutureProvider<ReadingProfile?>((ref) async {
  // TODO: Implement reading profile fetching
  return null;
});

// Helper classes for stats
class DailyStat {
  final String date;
  final int minutes;
  final int pages;
  final int sessions;

  const DailyStat({
    required this.date,
    required this.minutes,
    required this.pages,
    required this.sessions,
  });
}

class ReadingStreak {
  final int currentStreak;
  final int longestStreak;
  final String? lastReadingDate;
  final bool streakMaintainedToday;

  const ReadingStreak({
    required this.currentStreak,
    required this.longestStreak,
    this.lastReadingDate,
    required this.streakMaintainedToday,
  });
}
