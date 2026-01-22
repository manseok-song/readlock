import 'package:intl/intl.dart';

/// Formatting utilities
class Formatters {
  Formatters._();

  /// Format number with thousand separators
  static String number(int value) {
    return NumberFormat('#,###').format(value);
  }

  /// Format double with decimal places
  static String decimal(double value, [int decimals = 1]) {
    return value.toStringAsFixed(decimals);
  }

  /// Format as percentage
  static String percentage(double value, [int decimals = 1]) {
    return '${value.toStringAsFixed(decimals)}%';
  }

  /// Format minutes to readable time string
  static String readingTime(int minutes) {
    if (minutes < 60) {
      return '$minutes분';
    }
    final hours = minutes ~/ 60;
    final mins = minutes % 60;
    if (mins == 0) {
      return '$hours시간';
    }
    return '$hours시간 $mins분';
  }

  /// Format seconds to MM:SS
  static String timerMMSS(int seconds) {
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  /// Format seconds to HH:MM:SS
  static String timerHHMMSS(int seconds) {
    final hours = seconds ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    final secs = seconds % 60;
    if (hours > 0) {
      return '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
    }
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  /// Format date as 'yyyy-MM-dd'
  static String dateString(DateTime date) {
    return DateFormat('yyyy-MM-dd').format(date);
  }

  /// Format date as 'yyyy-MM-dd HH:mm'
  static String dateTimeString(DateTime date) {
    return DateFormat('yyyy-MM-dd HH:mm').format(date);
  }

  /// Format date as Korean style 'M월 d일'
  static String koreanDate(DateTime date) {
    return DateFormat('M월 d일').format(date);
  }

  /// Format date as Korean full style 'yyyy년 M월 d일'
  static String koreanFullDate(DateTime date) {
    return DateFormat('yyyy년 M월 d일').format(date);
  }

  /// Format relative time
  static String relativeTime(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

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

  /// Format ISBN with hyphens
  static String isbn(String value) {
    final clean = value.replaceAll(RegExp(r'[^0-9X]'), '');
    if (clean.length == 13) {
      return '${clean.substring(0, 3)}-${clean.substring(3, 4)}-${clean.substring(4, 8)}-${clean.substring(8, 12)}-${clean.substring(12)}';
    } else if (clean.length == 10) {
      return '${clean.substring(0, 1)}-${clean.substring(1, 5)}-${clean.substring(5, 9)}-${clean.substring(9)}';
    }
    return value;
  }

  /// Format phone number
  static String phone(String value) {
    final clean = value.replaceAll(RegExp(r'[^0-9]'), '');
    if (clean.length == 11) {
      return '${clean.substring(0, 3)}-${clean.substring(3, 7)}-${clean.substring(7)}';
    } else if (clean.length == 10) {
      return '${clean.substring(0, 3)}-${clean.substring(3, 6)}-${clean.substring(6)}';
    }
    return value;
  }

  /// Format file size
  static String fileSize(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    } else if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    } else if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    } else {
      return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
    }
  }

  /// Format compact number (e.g., 1.2K, 3.4M)
  static String compactNumber(int value) {
    if (value < 1000) {
      return value.toString();
    } else if (value < 1000000) {
      return '${(value / 1000).toStringAsFixed(1)}K';
    } else if (value < 1000000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    } else {
      return '${(value / 1000000000).toStringAsFixed(1)}B';
    }
  }

  /// Format book progress
  static String bookProgress(int currentPage, int totalPages) {
    if (totalPages <= 0) return '-';
    final percentage = (currentPage / totalPages * 100).clamp(0, 100);
    return '${percentage.toStringAsFixed(1)}%';
  }

  /// Format level with exp
  static String levelWithExp(int level, int exp, int expForNextLevel) {
    return 'Lv.$level ($exp/$expForNextLevel)';
  }

  /// Format streak days
  static String streakDays(int days) {
    return '$days일 연속';
  }
}
