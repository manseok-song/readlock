import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/constants/api_endpoints.dart';
import '../../data/datasources/local/secure_storage.dart';

// Avatar Config State
class AvatarConfigState {
  final String? id;
  final String userId;
  final String? faceItemId;
  final String? hairItemId;
  final String? outfitItemId;
  final String? accessoryItemId;
  final String skinColor;
  final Map<String, dynamic>? faceItem;
  final Map<String, dynamic>? hairItem;
  final Map<String, dynamic>? outfitItem;
  final Map<String, dynamic>? accessoryItem;
  final bool isLoading;
  final String? error;

  AvatarConfigState({
    this.id,
    required this.userId,
    this.faceItemId,
    this.hairItemId,
    this.outfitItemId,
    this.accessoryItemId,
    this.skinColor = '#FFD5B8',
    this.faceItem,
    this.hairItem,
    this.outfitItem,
    this.accessoryItem,
    this.isLoading = false,
    this.error,
  });

  AvatarConfigState copyWith({
    String? id,
    String? userId,
    String? faceItemId,
    String? hairItemId,
    String? outfitItemId,
    String? accessoryItemId,
    String? skinColor,
    Map<String, dynamic>? faceItem,
    Map<String, dynamic>? hairItem,
    Map<String, dynamic>? outfitItem,
    Map<String, dynamic>? accessoryItem,
    bool? isLoading,
    String? error,
  }) {
    return AvatarConfigState(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      faceItemId: faceItemId ?? this.faceItemId,
      hairItemId: hairItemId ?? this.hairItemId,
      outfitItemId: outfitItemId ?? this.outfitItemId,
      accessoryItemId: accessoryItemId ?? this.accessoryItemId,
      skinColor: skinColor ?? this.skinColor,
      faceItem: faceItem ?? this.faceItem,
      hairItem: hairItem ?? this.hairItem,
      outfitItem: outfitItem ?? this.outfitItem,
      accessoryItem: accessoryItem ?? this.accessoryItem,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AvatarNotifier extends StateNotifier<AvatarConfigState> {
  final Dio _dio;
  final SecureStorage _storage;

  AvatarNotifier(this._dio, this._storage)
      : super(AvatarConfigState(userId: ''));

  Future<void> loadAvatarConfig() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      final response = await _dio.get(
        '${ApiEndpoints.baseUrl}/v1/avatar/config',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      final data = response.data;
      state = AvatarConfigState(
        id: data['id'],
        userId: data['user_id'] ?? '',
        faceItemId: data['face_item_id'],
        hairItemId: data['hair_item_id'],
        outfitItemId: data['outfit_item_id'],
        accessoryItemId: data['accessory_item_id'],
        skinColor: data['skin_color'] ?? '#FFD5B8',
        faceItem: data['face_item'],
        hairItem: data['hair_item'],
        outfitItem: data['outfit_item'],
        accessoryItem: data['accessory_item'],
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '아바타 설정을 불러오는데 실패했습니다.',
      );
    }
  }

  Future<void> updateAvatarConfig({
    String? faceItemId,
    String? hairItemId,
    String? outfitItemId,
    String? accessoryItemId,
    String? skinColor,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      final body = <String, dynamic>{};

      if (faceItemId != null) body['face_item_id'] = faceItemId;
      if (hairItemId != null) body['hair_item_id'] = hairItemId;
      if (outfitItemId != null) body['outfit_item_id'] = outfitItemId;
      if (accessoryItemId != null) body['accessory_item_id'] = accessoryItemId;
      if (skinColor != null) body['skin_color'] = skinColor;

      final response = await _dio.put(
        '${ApiEndpoints.baseUrl}/v1/avatar/config',
        data: body,
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      final data = response.data;
      state = AvatarConfigState(
        id: data['id'],
        userId: data['user_id'] ?? '',
        faceItemId: data['face_item_id'],
        hairItemId: data['hair_item_id'],
        outfitItemId: data['outfit_item_id'],
        accessoryItemId: data['accessory_item_id'],
        skinColor: data['skin_color'] ?? '#FFD5B8',
        faceItem: data['face_item'],
        hairItem: data['hair_item'],
        outfitItem: data['outfit_item'],
        accessoryItem: data['accessory_item'],
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '아바타 설정 저장에 실패했습니다.',
      );
    }
  }

  void setSkinColor(String color) {
    state = state.copyWith(skinColor: color);
  }
}

// Room Layout State
class RoomLayoutState {
  final String? id;
  final String userId;
  final String? backgroundItemId;
  final Map<String, dynamic>? backgroundItem;
  final Map<String, Map<String, double>> layoutData;
  final List<Map<String, dynamic>> furnitureItems;
  final List<String> bookshelfBooks;
  final bool isLoading;
  final String? error;

  RoomLayoutState({
    this.id,
    required this.userId,
    this.backgroundItemId,
    this.backgroundItem,
    this.layoutData = const {},
    this.furnitureItems = const [],
    this.bookshelfBooks = const [],
    this.isLoading = false,
    this.error,
  });

  RoomLayoutState copyWith({
    String? id,
    String? userId,
    String? backgroundItemId,
    Map<String, dynamic>? backgroundItem,
    Map<String, Map<String, double>>? layoutData,
    List<Map<String, dynamic>>? furnitureItems,
    List<String>? bookshelfBooks,
    bool? isLoading,
    String? error,
  }) {
    return RoomLayoutState(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      backgroundItemId: backgroundItemId ?? this.backgroundItemId,
      backgroundItem: backgroundItem ?? this.backgroundItem,
      layoutData: layoutData ?? this.layoutData,
      furnitureItems: furnitureItems ?? this.furnitureItems,
      bookshelfBooks: bookshelfBooks ?? this.bookshelfBooks,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class RoomNotifier extends StateNotifier<RoomLayoutState> {
  final Dio _dio;
  final SecureStorage _storage;

  RoomNotifier(this._dio, this._storage)
      : super(RoomLayoutState(userId: ''));

  Future<void> loadRoomLayout() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      final response = await _dio.get(
        '${ApiEndpoints.baseUrl}/v1/room/layout',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      final data = response.data;
      final layoutData = <String, Map<String, double>>{};

      if (data['layout_data'] != null) {
        (data['layout_data'] as Map<String, dynamic>).forEach((key, value) {
          layoutData[key] = {
            'x': (value['x'] as num?)?.toDouble() ?? 0,
            'y': (value['y'] as num?)?.toDouble() ?? 0,
            'rotation': (value['rotation'] as num?)?.toDouble() ?? 0,
          };
        });
      }

      state = RoomLayoutState(
        id: data['id'],
        userId: data['user_id'] ?? '',
        backgroundItemId: data['background_item_id'],
        backgroundItem: data['background_item'],
        layoutData: layoutData,
        furnitureItems: List<Map<String, dynamic>>.from(
          data['furniture_items'] ?? [],
        ),
        bookshelfBooks: List<String>.from(data['bookshelf_books'] ?? []),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '방 정보를 불러오는데 실패했습니다.',
      );
    }
  }

  Future<void> updateRoomLayout({
    String? backgroundItemId,
    Map<String, Map<String, double>>? layoutData,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      final body = <String, dynamic>{};

      if (backgroundItemId != null) body['background_item_id'] = backgroundItemId;
      if (layoutData != null) body['layout_data'] = layoutData;

      final response = await _dio.put(
        '${ApiEndpoints.baseUrl}/v1/room/layout',
        data: body,
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      await loadRoomLayout();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '방 설정 저장에 실패했습니다.',
      );
    }
  }

  Future<void> updateBookshelf(List<String> bookIds) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      await _dio.put(
        '${ApiEndpoints.baseUrl}/v1/room/bookshelf',
        data: {'book_ids': bookIds},
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      state = state.copyWith(
        bookshelfBooks: bookIds,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '책장 업데이트에 실패했습니다.',
      );
    }
  }

  void moveFurniture(String itemId, double x, double y) {
    final newLayoutData = Map<String, Map<String, double>>.from(state.layoutData);
    newLayoutData[itemId] = {
      'x': x,
      'y': y,
      'rotation': newLayoutData[itemId]?['rotation'] ?? 0,
    };
    state = state.copyWith(layoutData: newLayoutData);
  }
}

// Shop Items State
class ShopItemsState {
  final List<Map<String, dynamic>> avatarItems;
  final List<Map<String, dynamic>> roomItems;
  final bool isLoading;
  final String? error;

  ShopItemsState({
    this.avatarItems = const [],
    this.roomItems = const [],
    this.isLoading = false,
    this.error,
  });

  ShopItemsState copyWith({
    List<Map<String, dynamic>>? avatarItems,
    List<Map<String, dynamic>>? roomItems,
    bool? isLoading,
    String? error,
  }) {
    return ShopItemsState(
      avatarItems: avatarItems ?? this.avatarItems,
      roomItems: roomItems ?? this.roomItems,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }

  List<Map<String, dynamic>> getItemsBySubcategory(String subcategory) {
    return avatarItems
        .where((item) => item['subcategory'] == subcategory)
        .toList();
  }

  List<Map<String, dynamic>> getRoomItemsBySubcategory(String subcategory) {
    return roomItems
        .where((item) => item['subcategory'] == subcategory)
        .toList();
  }
}

class ShopItemsNotifier extends StateNotifier<ShopItemsState> {
  final Dio _dio;
  final SecureStorage _storage;

  ShopItemsNotifier(this._dio, this._storage) : super(ShopItemsState());

  Future<void> loadShopItems() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final token = await _storage.getAccessToken();
      final headers = {'Authorization': 'Bearer $token'};

      final avatarResponse = await _dio.get(
        '${ApiEndpoints.baseUrl}/v1/shop/items',
        queryParameters: {'category': 'avatar'},
        options: Options(headers: headers),
      );

      final roomResponse = await _dio.get(
        '${ApiEndpoints.baseUrl}/v1/shop/items',
        queryParameters: {'category': 'room'},
        options: Options(headers: headers),
      );

      state = state.copyWith(
        avatarItems: List<Map<String, dynamic>>.from(avatarResponse.data ?? []),
        roomItems: List<Map<String, dynamic>>.from(roomResponse.data ?? []),
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: '상점 아이템을 불러오는데 실패했습니다.',
      );
    }
  }
}

// Providers
final dioProvider = Provider<Dio>((ref) => Dio());
final secureStorageProvider = Provider<SecureStorage>((ref) => SecureStorage());

final avatarProvider = StateNotifierProvider<AvatarNotifier, AvatarConfigState>(
  (ref) => AvatarNotifier(
    ref.watch(dioProvider),
    ref.watch(secureStorageProvider),
  ),
);

final roomProvider = StateNotifierProvider<RoomNotifier, RoomLayoutState>(
  (ref) => RoomNotifier(
    ref.watch(dioProvider),
    ref.watch(secureStorageProvider),
  ),
);

final shopItemsProvider = StateNotifierProvider<ShopItemsNotifier, ShopItemsState>(
  (ref) => ShopItemsNotifier(
    ref.watch(dioProvider),
    ref.watch(secureStorageProvider),
  ),
);
