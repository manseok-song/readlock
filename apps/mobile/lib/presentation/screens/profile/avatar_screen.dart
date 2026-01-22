import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AvatarScreen extends ConsumerStatefulWidget {
  const AvatarScreen({super.key});

  @override
  ConsumerState<AvatarScreen> createState() => _AvatarScreenState();
}

class _AvatarScreenState extends ConsumerState<AvatarScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('아바타'),
        actions: [
          TextButton(
            onPressed: () {
              // TODO: Save avatar
              Navigator.pop(context);
            },
            child: const Text('저장'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Avatar preview
          Container(
            height: 200,
            width: double.infinity,
            color: theme.colorScheme.primaryContainer,
            child: Center(
              child: Container(
                width: 120,
                height: 120,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.person,
                  size: 60,
                  color: theme.colorScheme.onPrimary,
                ),
              ),
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
            child: TabBarView(
              controller: _tabController,
              children: [
                _OptionGrid(category: 'face'),
                _OptionGrid(category: 'hair'),
                _OptionGrid(category: 'outfit'),
                _OptionGrid(category: 'accessory'),
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

  const _OptionGrid({required this.category});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return GridView.builder(
      padding: const EdgeInsets.all(16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: 12,
      itemBuilder: (context, index) {
        final isLocked = index > 3;
        final isSelected = index == 0;

        return InkWell(
          onTap: isLocked
              ? () => _showLockedDialog(context)
              : () {
                  // TODO: Select option
                },
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
                Center(
                  child: Icon(
                    _getIconForCategory(category),
                    size: 24,
                    color: isLocked
                        ? theme.colorScheme.outline
                        : theme.colorScheme.onSurface,
                  ),
                ),
                if (isLocked)
                  Positioned(
                    right: 4,
                    top: 4,
                    child: Icon(
                      Icons.lock,
                      size: 14,
                      color: theme.colorScheme.outline,
                    ),
                  ),
              ],
            ),
          ),
        );
      },
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

  void _showLockedDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('잠김 아이템'),
        content: const Text('이 아이템은 코인으로 구매하거나 레벨을 올려서 잠금 해제할 수 있습니다.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('확인'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // TODO: Navigate to shop
            },
            child: const Text('상점 가기'),
          ),
        ],
      ),
    );
  }
}
