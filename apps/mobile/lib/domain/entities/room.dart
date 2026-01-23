import 'package:freezed_annotation/freezed_annotation.dart';
import 'avatar.dart';

part 'room.freezed.dart';
part 'room.g.dart';

@freezed
class RoomLayout with _$RoomLayout {
  const RoomLayout._();

  const factory RoomLayout({
    String? id,
    required String userId,
    String? backgroundItemId,
    ShopItem? backgroundItem,
    @Default({}) Map<String, FurniturePosition> layoutData,
    @Default([]) List<ShopItem> furnitureItems,
    @Default([]) List<String> bookshelfBooks,
  }) = _RoomLayout;

  factory RoomLayout.fromJson(Map<String, dynamic> json) =>
      _$RoomLayoutFromJson(json);

  factory RoomLayout.empty(String userId) => RoomLayout(userId: userId);
}

@freezed
class FurniturePosition with _$FurniturePosition {
  const factory FurniturePosition({
    required double x,
    required double y,
    @Default(0) double rotation,
  }) = _FurniturePosition;

  factory FurniturePosition.fromJson(Map<String, dynamic> json) =>
      _$FurniturePositionFromJson(json);
}

@freezed
class RoomBackgroundData with _$RoomBackgroundData {
  const factory RoomBackgroundData({
    required String type,
    String? variant,
    @Default(4) int pixelSize,
    @Default(80) int width,
    @Default(60) int height,
    Map<String, String>? colors,
  }) = _RoomBackgroundData;

  factory RoomBackgroundData.fromJson(Map<String, dynamic> json) =>
      _$RoomBackgroundDataFromJson(json);
}

@freezed
class FurnitureAssetData with _$FurnitureAssetData {
  const factory FurnitureAssetData({
    required String type,
    String? furnitureType,
    @Default(4) int pixelSize,
    @Default(24) int width,
    @Default(40) int height,
    @Default(0) int bookSlots,
    @Default([]) List<Map<String, dynamic>> layers,
  }) = _FurnitureAssetData;

  factory FurnitureAssetData.fromJson(Map<String, dynamic> json) =>
      _$FurnitureAssetDataFromJson(json);
}
