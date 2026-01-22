import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
class User with _$User {
  const factory User({
    required String id,
    required String email,
    required UserProfile profile,
    String? provider,
    DateTime? lastLoginAt,
    required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

@freezed
class UserProfile with _$UserProfile {
  const UserProfile._();

  const factory UserProfile({
    required String id,
    required String userId,
    required String nickname,
    String? bio,
    String? profileImage,
    @Default(30) int readingGoalMin,
    @Default(true) bool isPublic,
    @Default(1) int level,
    @Default(0) int exp,
    @Default(0) int coins,
    DateTime? premiumUntil,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _UserProfile;

  factory UserProfile.fromJson(Map<String, dynamic> json) =>
      _$UserProfileFromJson(json);

  bool get isPremium =>
      premiumUntil != null && premiumUntil!.isAfter(DateTime.now());

  int get expForNextLevel => (100 * (level * 1.5)).toInt();

  double get levelProgress => exp / expForNextLevel;
}

@freezed
class AuthResult with _$AuthResult {
  const factory AuthResult({
    required User user,
    required AuthTokens tokens,
    @Default(false) bool isNewUser,
  }) = _AuthResult;

  factory AuthResult.fromJson(Map<String, dynamic> json) =>
      _$AuthResultFromJson(json);
}

@freezed
class AuthTokens with _$AuthTokens {
  const factory AuthTokens({
    required String accessToken,
    required String refreshToken,
    required int expiresIn,
  }) = _AuthTokens;

  factory AuthTokens.fromJson(Map<String, dynamic> json) =>
      _$AuthTokensFromJson(json);
}

@freezed
class PublicUserProfile with _$PublicUserProfile {
  const factory PublicUserProfile({
    required String id,
    required String nickname,
    String? bio,
    String? profileImage,
    required int level,
    @Default(0) int totalBooks,
    @Default(0) int totalReadingMinutes,
    @Default(0) int followersCount,
    @Default(0) int followingCount,
    @Default(false) bool isFollowing,
  }) = _PublicUserProfile;

  factory PublicUserProfile.fromJson(Map<String, dynamic> json) =>
      _$PublicUserProfileFromJson(json);
}
