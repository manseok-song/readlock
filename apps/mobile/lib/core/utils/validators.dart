import '../constants/app_constants.dart';

/// Validation utilities
class Validators {
  Validators._();

  /// Validate email
  static String? email(String? value) {
    if (value == null || value.isEmpty) {
      return '이메일을 입력해주세요.';
    }
    if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
      return '올바른 이메일 형식이 아닙니다.';
    }
    return null;
  }

  /// Validate password
  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return '비밀번호를 입력해주세요.';
    }
    if (value.length < AppConstants.minPasswordLength) {
      return '비밀번호는 ${AppConstants.minPasswordLength}자 이상이어야 합니다.';
    }
    if (value.length > AppConstants.maxPasswordLength) {
      return '비밀번호는 ${AppConstants.maxPasswordLength}자 이하여야 합니다.';
    }
    if (!RegExp(r'[A-Za-z]').hasMatch(value)) {
      return '비밀번호에 영문자가 포함되어야 합니다.';
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return '비밀번호에 숫자가 포함되어야 합니다.';
    }
    return null;
  }

  /// Validate password confirmation
  static String? passwordConfirmation(String? value, String? password) {
    if (value == null || value.isEmpty) {
      return '비밀번호 확인을 입력해주세요.';
    }
    if (value != password) {
      return '비밀번호가 일치하지 않습니다.';
    }
    return null;
  }

  /// Validate nickname
  static String? nickname(String? value) {
    if (value == null || value.isEmpty) {
      return '닉네임을 입력해주세요.';
    }
    if (value.length < AppConstants.minNicknameLength) {
      return '닉네임은 ${AppConstants.minNicknameLength}자 이상이어야 합니다.';
    }
    if (value.length > AppConstants.maxNicknameLength) {
      return '닉네임은 ${AppConstants.maxNicknameLength}자 이하여야 합니다.';
    }
    if (!RegExp(r'^[가-힣a-zA-Z0-9_]+$').hasMatch(value)) {
      return '닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용 가능합니다.';
    }
    return null;
  }

  /// Validate bio
  static String? bio(String? value) {
    if (value != null && value.length > AppConstants.maxBioLength) {
      return '자기소개는 ${AppConstants.maxBioLength}자 이하여야 합니다.';
    }
    return null;
  }

  /// Validate ISBN
  static String? isbn(String? value) {
    if (value == null || value.isEmpty) {
      return 'ISBN을 입력해주세요.';
    }
    final cleanIsbn = value.replaceAll(RegExp(r'[^0-9X]'), '');
    if (cleanIsbn.length != AppConstants.isbn10Length &&
        cleanIsbn.length != AppConstants.isbn13Length) {
      return '올바른 ISBN 형식이 아닙니다.';
    }
    return null;
  }

  /// Validate quote content
  static String? quote(String? value) {
    if (value == null || value.isEmpty) {
      return '인용구를 입력해주세요.';
    }
    if (value.length > AppConstants.maxQuoteLength) {
      return '인용구는 ${AppConstants.maxQuoteLength}자 이하여야 합니다.';
    }
    return null;
  }

  /// Validate review content
  static String? review(String? value) {
    if (value == null || value.isEmpty) {
      return '감상평을 입력해주세요.';
    }
    if (value.length > AppConstants.maxReviewLength) {
      return '감상평은 ${AppConstants.maxReviewLength}자 이하여야 합니다.';
    }
    return null;
  }

  /// Validate rating
  static String? rating(double? value) {
    if (value == null) {
      return '별점을 선택해주세요.';
    }
    if (value < 1 || value > 5) {
      return '별점은 1~5 사이여야 합니다.';
    }
    return null;
  }

  /// Validate page number
  static String? pageNumber(String? value, {int? maxPages}) {
    if (value == null || value.isEmpty) {
      return null; // optional field
    }
    final page = int.tryParse(value);
    if (page == null || page < 0) {
      return '올바른 페이지 번호를 입력해주세요.';
    }
    if (maxPages != null && page > maxPages) {
      return '최대 페이지($maxPages)를 초과할 수 없습니다.';
    }
    return null;
  }

  /// Validate reading goal
  static String? readingGoal(String? value) {
    if (value == null || value.isEmpty) {
      return '독서 목표를 입력해주세요.';
    }
    final minutes = int.tryParse(value);
    if (minutes == null) {
      return '올바른 숫자를 입력해주세요.';
    }
    if (minutes < AppConstants.minReadingGoalMinutes) {
      return '독서 목표는 ${AppConstants.minReadingGoalMinutes}분 이상이어야 합니다.';
    }
    if (minutes > AppConstants.maxReadingGoalMinutes) {
      return '독서 목표는 ${AppConstants.maxReadingGoalMinutes}분 이하여야 합니다.';
    }
    return null;
  }

  /// Required field validator
  static String? required(String? value, [String fieldName = '필드']) {
    if (value == null || value.trim().isEmpty) {
      return '$fieldName을(를) 입력해주세요.';
    }
    return null;
  }

  /// Min length validator
  static String? minLength(String? value, int minLength, [String fieldName = '입력값']) {
    if (value != null && value.length < minLength) {
      return '$fieldName은(는) $minLength자 이상이어야 합니다.';
    }
    return null;
  }

  /// Max length validator
  static String? maxLength(String? value, int maxLength, [String fieldName = '입력값']) {
    if (value != null && value.length > maxLength) {
      return '$fieldName은(는) $maxLength자 이하여야 합니다.';
    }
    return null;
  }
}
