import 'package:freezed_annotation/freezed_annotation.dart';

part 'avatar.freezed.dart';
part 'avatar.g.dart';

@freezed
class AvatarConfig with _$AvatarConfig {
  const AvatarConfig._();

  const factory AvatarConfig({
    String? id,
    required String userId,
    String? faceItemId,
    String? hairItemId,
    String? outfitItemId,
    String? accessoryItemId,
    @Default('#FFD5B8') String skinColor,
    ShopItem? faceItem,
    ShopItem? hairItem,
    ShopItem? outfitItem,
    ShopItem? accessoryItem,
  }) = _AvatarConfig;

  factory AvatarConfig.fromJson(Map<String, dynamic> json) =>
      _$AvatarConfigFromJson(json);

  factory AvatarConfig.empty(String userId) => AvatarConfig(userId: userId);
}

@freezed
class ShopItem with _$ShopItem {
  const factory ShopItem({
    required String id,
    required String name,
    required String description,
    required String category,
    String? subcategory,
    required int priceCoins,
    double? priceReal,
    required String previewUrl,
    @Default(false) bool isLimited,
    DateTime? availableUntil,
    @Default(1) int requiredLevel,
    Map<String, dynamic>? assetData,
  }) = _ShopItem;

  factory ShopItem.fromJson(Map<String, dynamic> json) =>
      _$ShopItemFromJson(json);
}

@freezed
class PixelData with _$PixelData {
  const factory PixelData({
    required int x,
    required int y,
    required String color,
  }) = _PixelData;

  factory PixelData.fromJson(Map<String, dynamic> json) =>
      _$PixelDataFromJson(json);
}

@freezed
class PixelLayer with _$PixelLayer {
  const factory PixelLayer({
    required String name,
    @Default(0) int zIndex,
    required List<PixelData> pixels,
  }) = _PixelLayer;

  factory PixelLayer.fromJson(Map<String, dynamic> json) =>
      _$PixelLayerFromJson(json);
}

@freezed
class AvatarAssetData with _$AvatarAssetData {
  const factory AvatarAssetData({
    required String type,
    String? variant,
    @Default(4) int pixelSize,
    @Default(16) int width,
    @Default(16) int height,
    @Default([]) List<PixelLayer> layers,
  }) = _AvatarAssetData;

  factory AvatarAssetData.fromJson(Map<String, dynamic> json) =>
      _$AvatarAssetDataFromJson(json);
}
