import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../widgets/pixel_art/pixel_avatar_widget.dart';
import '../../providers/avatar_room_provider.dart';

class AvatarScreen extends ConsumerStatefulWidget {
  const AvatarScreen({super.key});

  @override
  ConsumerState<AvatarScreen> createState() => _AvatarScreenState();
}

class _AvatarScreenState extends ConsumerState<AvatarScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _selectedSkinColor = '#FFD5B8';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    await ref.read(avatarProvider.notifier).loadAvatarConfig();
    await ref.read(shopItemsProvider.notifier).loadShopItems();

    final avatarState = ref.read(avatarProvider);
    setState(() {
      _selectedSkinColor = avatarState.skinColor;
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final avatarState = ref.watch(avatarProvider);
    final shopState = ref.watch(shopItemsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('아바타'),
        actions: [
          if (avatarState.isLoading)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            TextButton(
              onPressed: () async {
                await ref.read(avatarProvider.notifier).updateAvatarConfig(
                  skinColor: _selectedSkinColor,
                );
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('아바타가 저장되었습니다.')),
                  );
                  Navigator.pop(context);
                }
              },
              child: const Text('저장'),
            ),
        ],
      ),
      body: Column(
        children: [
          // Avatar preview
          Container(
            height: 220,
            width: double.infinity,
            color: theme.colorScheme.primaryContainer.withOpacity(0.3),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                PixelAvatarWidget(
                  faceAssetData: avatarState.faceItem?['asset_data'],
                  hairAssetData: avatarState.hairItem?['asset_data'],
                  outfitAssetData: avatarState.outfitItem?['asset_data'],
                  accessoryAssetData: avatarState.accessoryItem?['asset_data'],
                  skinColor: _selectedSkinColor,
                  scale: 2.0,
                ),
                const SizedBox(height: 16),
                // Skin color picker
                SkinColorPicker(
                  selectedColor: _selectedSkinColor,
                  onColorSelected: (color) {
                    setState(() {
                      _selectedSkinColor = color;
                    });
                    ref.read(avatarProvider.notifier).setSkinColor(color);
                  },
                ),
              ],
            ),
          ),

          // Category tabs
          TabBar(
            controller: _tabController,
            tabs: const [
              Tab(text: '얼굴'),
              Tab(text: '헤어'),
              Tab(text: '의상'),
              Tab(text: '소품'),
            ],
          ),

          // Options grid
          Expanded(
            child: shopState.isLoading
                ? const Center(child: CircularProgressIndicator())
                : TabBarView(
                    controller: _tabController,
                    children: [
                      _OptionGrid(
                        category: 'face',
                        items: shopState.getItemsBySubcategory('face'),
                        selectedItemId: avatarState.faceItemId,
                        onItemSelected: (itemId) {
                          ref.read(avatarProvider.notifier).updateAvatarConfig(
                            faceItemId: itemId,
                          );
                        },
                      ),
                      _OptionGrid(
                        category: 'hair',
                        items: shopState.getItemsBySubcategory('hair'),
                        selectedItemId: avatarState.hairItemId,
                        onItemSelected: (itemId) {
                          ref.read(avatarProvider.notifier).updateAvatarConfig(
                            hairItemId: itemId,
                          );
                        },
                      ),
                      _OptionGrid(
                        category: 'outfit',
                        items: shopState.getItemsBySubcategory('outfit'),
                        selectedItemId: avatarState.outfitItemId,
                        onItemSelected: (itemId) {
                          ref.read(avatarProvider.notifier).updateAvatarConfig(
                            outfitItemId: itemId,
                          );
                        },
                      ),
                      _OptionGrid(
                        category: 'accessory',
                        items: shopState.getItemsBySubcategory('accessory'),
                        selectedItemId: avatarState.accessoryItemId,
                        onItemSelected: (itemId) {
                          ref.read(avatarProvider.notifier).updateAvatarConfig(
                            accessoryItemId: itemId,
                          );
                        },
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _OptionGrid extends StatelessWidget {
  final String category;
  final List<Map<String, dynamic>> items;
  final String? selectedItemId;
  final Function(String) onItemSelected;

  const _OptionGrid({
    required this.category,
    required this.items,
    required this.selectedItemId,
    required this.onItemSelected,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.inventory_2_outlined,
              size: 48,
              color: theme.colorScheme.outline,
            ),
            const SizedBox(height: 8),
            Text(
              '아이템이 없습니다',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
          ],
        ),
      );
    }

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.8,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        final itemId = item['id'] as String;
        final isSelected = itemId == selectedItemId;
        final requiredLevel = item['required_level'] as int? ?? 1;
        final price = item['price_coins'] as int? ?? 0;
        final isLocked = false; // TODO: Check user level and inventory

        return InkWell(
          onTap: isLocked
              ? () => _showLockedDialog(context, item)
              : () => onItemSelected(itemId),
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              color: isSelected
                  ? theme.colorScheme.primaryContainer
                  : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
              border: isSelected
                  ? Border.all(color: theme.colorScheme.primary, width: 2)
                  : null,
            ),
            child: Stack(
              children: [
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Expanded(
                      child: Center(
                        child: _buildItemPreview(item, theme),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(4),
                      child: Text(
                        item['name'] as String? ?? '',
                        style: theme.textTheme.labelSmall,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.center,
                      ),
                    ),
                    if (price > 0)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.monetization_on,
                              size: 12,
                              color: theme.colorScheme.tertiary,
                            ),
                            const SizedBox(width: 2),
                            Text(
                              '$price',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: theme.colorScheme.tertiary,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
                if (isLocked)
                  Positioned(
                    right: 4,
                    top: 4,
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surface,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.lock,
                        size: 14,
                        color: theme.colorScheme.outline,
                      ),
                    ),
                  ),
                if (isSelected)
                  Positioned(
                    right: 4,
                    top: 4,
                    child: Container(
                      padding: const EdgeInsets.all(2),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.check,
                        size: 14,
                        color: theme.colorScheme.onPrimary,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildItemPreview(Map<String, dynamic> item, ThemeData theme) {
    final assetData = item['asset_data'] as Map<String, dynamic>?;

    // For now, show a simple icon preview
    // In full implementation, render pixel preview
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(
        _getIconForCategory(category),
        size: 24,
        color: theme.colorScheme.onSurface,
      ),
    );
  }

  IconData _getIconForCategory(String category) {
    switch (category) {
      case 'face':
        return Icons.face;
      case 'hair':
        return Icons.face_retouching_natural;
      case 'outfit':
        return Icons.checkroom;
      case 'accessory':
        return Icons.auto_awesome;
      default:
        return Icons.circle;
    }
  }

  void _showLockedDialog(BuildContext context, Map<String, dynamic> item) {
    final requiredLevel = item['required_level'] as int? ?? 1;
    final price = item['price_coins'] as int? ?? 0;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(item['name'] as String? ?? '잠김 아이템'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('이 아이템을 사용하려면:'),
            const SizedBox(height: 8),
            if (requiredLevel > 1)
              Text('• 레벨 $requiredLevel 이상 필요'),
            if (price > 0)
              Text('• $price 코인으로 구매 가능'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('확인'),
          ),
          if (price > 0)
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                // TODO: Navigate to shop or purchase directly
              },
              child: const Text('구매하기'),
            ),
        ],
      ),
    );
  }
}
