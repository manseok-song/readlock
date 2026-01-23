import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../widgets/pixel_art/pixel_avatar_widget.dart';
import '../../widgets/pixel_art/pixel_room_widget.dart';
import '../../widgets/pixel_art/pixel_bookshelf_widget.dart';
import '../../providers/avatar_room_provider.dart';

class MyRoomScreen extends ConsumerStatefulWidget {
  const MyRoomScreen({super.key});

  @override
  ConsumerState<MyRoomScreen> createState() => _MyRoomScreenState();
}

class _MyRoomScreenState extends ConsumerState<MyRoomScreen> {
  bool _isEditMode = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    await ref.read(roomProvider.notifier).loadRoomLayout();
    await ref.read(avatarProvider.notifier).loadAvatarConfig();
    await ref.read(shopItemsProvider.notifier).loadShopItems();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final roomState = ref.watch(roomProvider);
    final avatarState = ref.watch(avatarProvider);
    final shopState = ref.watch(shopItemsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('마이룸'),
        actions: [
          IconButton(
            icon: Icon(_isEditMode ? Icons.check : Icons.edit),
            onPressed: () async {
              if (_isEditMode) {
                // Save when exiting edit mode
                await ref.read(roomProvider.notifier).updateRoomLayout(
                  layoutData: roomState.layoutData,
                );
              }
              setState(() {
                _isEditMode = !_isEditMode;
              });
            },
          ),
          IconButton(
            icon: const Icon(Icons.shopping_bag_outlined),
            onPressed: () {
              // TODO: Navigate to shop
            },
          ),
        ],
      ),
      body: roomState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Room view
                Expanded(
                  flex: 2,
                  child: Container(
                    margin: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(16),
                      border: _isEditMode
                          ? Border.all(
                              color: theme.colorScheme.primary,
                              width: 2,
                              strokeAlign: BorderSide.strokeAlignOutside,
                            )
                          : null,
                    ),
                    child: Stack(
                      children: [
                        // Pixel art background
                        Positioned.fill(
                          child: PixelRoomWidget(
                            backgroundAssetData:
                                roomState.backgroundItem?['asset_data'],
                            furnitureItems: _prepareFurnitureItems(roomState),
                            isEditMode: _isEditMode,
                            onFurnitureMoved: (itemId, position) {
                              ref.read(roomProvider.notifier).moveFurniture(
                                    itemId,
                                    position.dx,
                                    position.dy,
                                  );
                            },
                          ),
                        ),

                        // Bookshelf with books
                        Positioned(
                          left: 20,
                          bottom: 60,
                          child: GestureDetector(
                            onTap: _isEditMode ? _showBookshelfDialog : null,
                            child: PixelBookshelfWidget(
                              bookIds: roomState.bookshelfBooks,
                              maxSlots: 10,
                              isEditMode: _isEditMode,
                              onAddBook: _showBookshelfDialog,
                            ),
                          ),
                        ),

                        // Avatar in the room
                        Positioned(
                          left: 0,
                          right: 0,
                          bottom: 80,
                          child: Center(
                            child: PixelAvatarWidget(
                              faceAssetData:
                                  avatarState.faceItem?['asset_data'],
                              hairAssetData:
                                  avatarState.hairItem?['asset_data'],
                              outfitAssetData:
                                  avatarState.outfitItem?['asset_data'],
                              accessoryAssetData:
                                  avatarState.accessoryItem?['asset_data'],
                              skinColor: avatarState.skinColor,
                              scale: 1.5,
                            ),
                          ),
                        ),

                        // Edit mode hint
                        if (_isEditMode)
                          Positioned(
                            top: 8,
                            left: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: theme.colorScheme.primary,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                '편집 모드',
                                style: theme.textTheme.labelSmall?.copyWith(
                                  color: theme.colorScheme.onPrimary,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),

                // Inventory when editing
                if (_isEditMode)
                  Expanded(
                    flex: 1,
                    child: Container(
                      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surface,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: theme.colorScheme.outline),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(12),
                            child: Row(
                              children: [
                                Text(
                                  '인벤토리',
                                  style: theme.textTheme.titleSmall,
                                ),
                                const Spacer(),
                                _buildCategoryChip(context, '배경', 'background'),
                                const SizedBox(width: 8),
                                _buildCategoryChip(context, '가구', 'furniture'),
                                const SizedBox(width: 8),
                                _buildCategoryChip(context, '장식', 'decoration'),
                              ],
                            ),
                          ),
                          Expanded(
                            child: ListView(
                              scrollDirection: Axis.horizontal,
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 12),
                              children: _buildInventoryItems(
                                  shopState.roomItems, theme),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                // Stats when not editing
                if (!_isEditMode)
                  Container(
                    margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '마이룸 정보',
                              style: theme.textTheme.titleMedium,
                            ),
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                _RoomStat(
                                  label: '가구',
                                  value: '${roomState.furnitureItems.length}개',
                                ),
                                _RoomStat(
                                  label: '책장 도서',
                                  value: '${roomState.bookshelfBooks.length}권',
                                ),
                                const _RoomStat(
                                  label: '방문객',
                                  value: '0명',
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }

  List<Map<String, dynamic>> _prepareFurnitureItems(RoomLayoutState state) {
    return state.furnitureItems.map((item) {
      final itemId = item['id'] as String?;
      final position = state.layoutData[itemId];
      return {
        ...item,
        'position': position != null
            ? {'x': position['x'], 'y': position['y']}
            : {'x': 0.0, 'y': 0.0},
      };
    }).toList();
  }

  Widget _buildCategoryChip(
      BuildContext context, String label, String category) {
    final theme = Theme.of(context);
    return ActionChip(
      label: Text(label),
      labelStyle: theme.textTheme.labelSmall,
      onPressed: () {
        // Filter inventory by category
      },
    );
  }

  List<Widget> _buildInventoryItems(
      List<Map<String, dynamic>> items, ThemeData theme) {
    return items.map((item) {
      return _InventoryItem(
        item: item,
        onTap: () {
          // Place item in room
          final itemId = item['id'] as String;
          ref.read(roomProvider.notifier).moveFurniture(itemId, 100, 100);
        },
      );
    }).toList();
  }

  void _showBookshelfDialog() {
    // TODO: Get user's completed books from reading service
    final mockBooks = <Map<String, dynamic>>[
      {'id': 'book1', 'title': '도구라 마구라 1', 'author': '유메노 큐사쿠'},
      {'id': 'book2', 'title': '도구라 마구라 2', 'author': '유메노 큐사쿠'},
      {'id': 'book3', 'title': '백야', 'author': '도스토예프스키'},
      {'id': 'book4', 'title': '겨울밤에 읽는 일본 문학 단편선', 'author': '해밀누리'},
      {'id': 'book5', 'title': '소녀지옥', 'author': '유메노 큐사쿠'},
      {'id': 'book6', 'title': '걷기의 철학', 'author': '프레데릭 그로'},
    ];

    final roomState = ref.read(roomProvider);

    showDialog(
      context: context,
      builder: (context) => BookSelectionDialog(
        availableBooks: mockBooks,
        selectedBookIds: roomState.bookshelfBooks,
        onBookSelected: (bookId) {
          final currentBooks = List<String>.from(roomState.bookshelfBooks);
          if (currentBooks.contains(bookId)) {
            currentBooks.remove(bookId);
          } else if (currentBooks.length < 10) {
            currentBooks.add(bookId);
          }
          ref.read(roomProvider.notifier).updateBookshelf(currentBooks);
        },
      ),
    );
  }
}

class _InventoryItem extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback? onTap;

  const _InventoryItem({required this.item, this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final name = item['name'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: GestureDetector(
        onTap: onTap,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: theme.colorScheme.outline.withOpacity(0.5),
                ),
              ),
              child: const Icon(Icons.chair, size: 28),
            ),
            const SizedBox(height: 4),
            SizedBox(
              width: 56,
              child: Text(
                name,
                style: theme.textTheme.labelSmall,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RoomStat extends StatelessWidget {
  final String label;
  final String value;

  const _RoomStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        Text(
          value,
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
