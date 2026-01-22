import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// DateTime extensions
extension DateTimeExtension on DateTime {
  /// Format as 'yyyy-MM-dd'
  String toDateString() => DateFormat('yyyy-MM-dd').format(this);

  /// Format as 'yyyy-MM-dd HH:mm'
  String toDateTimeString() => DateFormat('yyyy-MM-dd HH:mm').format(this);

  /// Format as 'MM월 dd일'
  String toKoreanDate() => DateFormat('MM월 dd일').format(this);

  /// Format as 'yyyy년 MM월 dd일'
  String toKoreanFullDate() => DateFormat('yyyy년 MM월 dd일').format(this);

  /// Format as relative time (e.g., '방금 전', '5분 전', '3시간 전')
  String toRelativeTime() {
    final now = DateTime.now();
    final difference = now.difference(this);

    if (difference.inSeconds < 60) {
      return '방금 전';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}분 전';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}시간 전';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}일 전';
    } else if (difference.inDays < 30) {
      return '${(difference.inDays / 7).floor()}주 전';
    } else if (difference.inDays < 365) {
      return '${(difference.inDays / 30).floor()}개월 전';
    } else {
      return '${(difference.inDays / 365).floor()}년 전';
    }
  }

  /// Check if date is today
  bool get isToday {
    final now = DateTime.now();
    return year == now.year && month == now.month && day == now.day;
  }

  /// Check if date is yesterday
  bool get isYesterday {
    final yesterday = DateTime.now().subtract(const Duration(days: 1));
    return year == yesterday.year && month == yesterday.month && day == yesterday.day;
  }

  /// Get start of day
  DateTime get startOfDay => DateTime(year, month, day);

  /// Get end of day
  DateTime get endOfDay => DateTime(year, month, day, 23, 59, 59);

  /// Get start of week (Monday)
  DateTime get startOfWeek {
    final weekDay = weekday;
    return subtract(Duration(days: weekDay - 1)).startOfDay;
  }

  /// Get start of month
  DateTime get startOfMonth => DateTime(year, month, 1);
}

/// Duration extensions
extension DurationExtension on Duration {
  /// Format as 'HH:MM:SS'
  String toHHMMSS() {
    final hours = inHours;
    final minutes = inMinutes.remainder(60);
    final seconds = inSeconds.remainder(60);

    if (hours > 0) {
      return '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    }
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// Format as readable string (e.g., '1시간 30분')
  String toReadableString() {
    final hours = inHours;
    final minutes = inMinutes.remainder(60);

    if (hours > 0 && minutes > 0) {
      return '$hours시간 $minutes분';
    } else if (hours > 0) {
      return '$hours시간';
    } else {
      return '$minutes분';
    }
  }
}

/// String extensions
extension StringExtension on String {
  /// Capitalize first letter
  String get capitalize {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }

  /// Check if string is valid email
  bool get isValidEmail {
    return RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(this);
  }

  /// Check if string is valid ISBN
  bool get isValidIsbn {
    final cleanIsbn = replaceAll(RegExp(r'[^0-9X]'), '');
    return cleanIsbn.length == 10 || cleanIsbn.length == 13;
  }

  /// Clean ISBN (remove hyphens and spaces)
  String get cleanIsbn => replaceAll(RegExp(r'[^0-9X]'), '');

  /// Truncate with ellipsis
  String truncate(int maxLength, {String suffix = '...'}) {
    if (length <= maxLength) return this;
    return '${substring(0, maxLength - suffix.length)}$suffix';
  }

  /// Check if string is null or empty
  bool get isNullOrEmpty => isEmpty;

  /// Check if string is not null or empty
  bool get isNotNullOrEmpty => isNotEmpty;
}

/// Nullable String extensions
extension NullableStringExtension on String? {
  /// Check if string is null or empty
  bool get isNullOrEmpty => this == null || this!.isEmpty;

  /// Check if string is not null or empty
  bool get isNotNullOrEmpty => this != null && this!.isNotEmpty;

  /// Return value or default
  String orDefault([String defaultValue = '']) => this ?? defaultValue;
}

/// int extensions
extension IntExtension on int {
  /// Format with thousand separators
  String toFormattedString() => NumberFormat('#,###').format(this);

  /// Format as reading time
  String toReadingTime() {
    if (this < 60) {
      return '$this분';
    }
    final hours = this ~/ 60;
    final minutes = this % 60;
    if (minutes == 0) {
      return '$hours시간';
    }
    return '$hours시간 $minutes분';
  }
}

/// double extensions
extension DoubleExtension on double {
  /// Format as percentage
  String toPercentString([int decimals = 1]) =>
      '${toStringAsFixed(decimals)}%';

  /// Format with fixed decimals
  String toFixed([int decimals = 1]) => toStringAsFixed(decimals);
}

/// BuildContext extensions
extension BuildContextExtension on BuildContext {
  /// Get theme
  ThemeData get theme => Theme.of(this);

  /// Get color scheme
  ColorScheme get colorScheme => Theme.of(this).colorScheme;

  /// Get text theme
  TextTheme get textTheme => Theme.of(this).textTheme;

  /// Get screen size
  Size get screenSize => MediaQuery.of(this).size;

  /// Get screen width
  double get screenWidth => MediaQuery.of(this).size.width;

  /// Get screen height
  double get screenHeight => MediaQuery.of(this).size.height;

  /// Get safe area padding
  EdgeInsets get safeArea => MediaQuery.of(this).padding;

  /// Check if keyboard is visible
  bool get isKeyboardVisible => MediaQuery.of(this).viewInsets.bottom > 0;

  /// Check if dark mode
  bool get isDarkMode => Theme.of(this).brightness == Brightness.dark;

  /// Show snackbar
  void showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? colorScheme.error : null,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  /// Pop with result
  void pop<T>([T? result]) => Navigator.of(this).pop(result);
}

/// List extensions
extension ListExtension<T> on List<T> {
  /// Get first or null
  T? get firstOrNull => isEmpty ? null : first;

  /// Get last or null
  T? get lastOrNull => isEmpty ? null : last;

  /// Safe element at index
  T? elementAtOrNull(int index) {
    if (index < 0 || index >= length) return null;
    return this[index];
  }
}
