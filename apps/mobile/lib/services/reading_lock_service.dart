import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Service for managing phone lock during reading sessions
class ReadingLockService {
  static const _channel = MethodChannel('com.pubstation.readlock/lock');

  /// Enable reading lock mode
  Future<void> enableLock() async {
    if (kIsWeb) {
      // Web: Request fullscreen mode
      return;
    }

    if (Platform.isAndroid) {
      try {
        await _channel.invokeMethod('enableLock');
      } on PlatformException catch (e) {
        debugPrint('Failed to enable lock: ${e.message}');
      }
    } else if (Platform.isIOS) {
      // iOS: Keep screen on and suggest Focus mode
      try {
        await _channel.invokeMethod('keepScreenOn', {'on': true});
      } catch (e) {
        debugPrint('Failed to keep screen on: $e');
      }
    }
  }

  /// Disable reading lock mode
  Future<void> disableLock() async {
    if (kIsWeb) return;

    if (Platform.isAndroid) {
      try {
        await _channel.invokeMethod('disableLock');
      } on PlatformException catch (e) {
        debugPrint('Failed to disable lock: ${e.message}');
      }
    } else if (Platform.isIOS) {
      try {
        await _channel.invokeMethod('keepScreenOn', {'on': false});
      } catch (e) {
        debugPrint('Failed to disable keep screen on: $e');
      }
    }
  }

  /// Check if lock permission is granted (Android only)
  Future<bool> hasLockPermission() async {
    if (kIsWeb || Platform.isIOS) return false;

    try {
      return await _channel.invokeMethod('hasLockPermission') ?? false;
    } catch (e) {
      return false;
    }
  }

  /// Request lock permission (Android only)
  Future<void> requestLockPermission() async {
    if (!Platform.isAndroid) return;

    try {
      await _channel.invokeMethod('requestLockPermission');
    } catch (e) {
      debugPrint('Failed to request permission: $e');
    }
  }

  /// Check if DND (Do Not Disturb) permission is granted
  Future<bool> hasDndPermission() async {
    if (kIsWeb || Platform.isIOS) return false;

    try {
      return await _channel.invokeMethod('hasDndPermission') ?? false;
    } catch (e) {
      return false;
    }
  }

  /// Request DND permission (Android only)
  Future<void> requestDndPermission() async {
    if (!Platform.isAndroid) return;

    try {
      await _channel.invokeMethod('requestDndPermission');
    } catch (e) {
      debugPrint('Failed to request DND permission: $e');
    }
  }

  /// Enable Do Not Disturb mode
  Future<void> enableDnd() async {
    if (!Platform.isAndroid) return;

    try {
      await _channel.invokeMethod('enableDnd');
    } catch (e) {
      debugPrint('Failed to enable DND: $e');
    }
  }

  /// Disable Do Not Disturb mode
  Future<void> disableDnd() async {
    if (!Platform.isAndroid) return;

    try {
      await _channel.invokeMethod('disableDnd');
    } catch (e) {
      debugPrint('Failed to disable DND: $e');
    }
  }

  /// Open iOS Focus settings (for guidance)
  Future<void> openFocusSettings() async {
    if (!Platform.isIOS) return;

    try {
      await _channel.invokeMethod('openFocusSettings');
    } catch (e) {
      debugPrint('Failed to open Focus settings: $e');
    }
  }

  /// Get current lock state
  Future<LockState> getLockState() async {
    if (kIsWeb) {
      return LockState(
        isLockEnabled: false,
        isDndEnabled: false,
        platform: 'web',
      );
    }

    try {
      final result = await _channel.invokeMethod<Map>('getLockState');
      return LockState(
        isLockEnabled: result?['isLockEnabled'] ?? false,
        isDndEnabled: result?['isDndEnabled'] ?? false,
        platform: Platform.operatingSystem,
      );
    } catch (e) {
      return LockState(
        isLockEnabled: false,
        isDndEnabled: false,
        platform: Platform.operatingSystem,
      );
    }
  }
}

/// Lock state data class
class LockState {
  final bool isLockEnabled;
  final bool isDndEnabled;
  final String platform;

  const LockState({
    required this.isLockEnabled,
    required this.isDndEnabled,
    required this.platform,
  });

  bool get isAndroid => platform == 'android';
  bool get isIOS => platform == 'ios';
  bool get isWeb => platform == 'web';
}
