import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MyRoomScreen extends ConsumerStatefulWidget {
  const MyRoomScreen({super.key});

  @override
  ConsumerState<MyRoomScreen> createState() => _MyRoomScreenState();
}

class _MyRoomScreenState extends ConsumerState<MyRoomScreen> {
  bool _isEditMode = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('마이룸'),
        actions: [
          IconButton(
            icon: Icon(_isEditMode ? Icons.check : Icons.edit),
            onPressed: () {
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
      body: Column(
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
                  // Background
                  Positioned.fill(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: CustomPaint(
                        painter: _RoomBackgroundPainter(
                          color: theme.colorScheme.surface,
                        ),
                      ),
                    ),
                  ),

                  // Bookshelf placeholder
                  Positioned(
                    left: 20,
                    bottom: 40,
                    child: _RoomItem(
                      icon: Icons.shelves,
                      label: '책장',
                      isEditMode: _isEditMode,
                    ),
                  ),

                  // Desk placeholder
                  Positioned(
                    right: 20,
                    bottom: 40,
                    child: _RoomItem(
                      icon: Icons.desk,
                      label: '책상',
                      isEditMode: _isEditMode,
                    ),
                  ),

                  // Avatar
                  Positioned(
                    left: 0,
                    right: 0,
                    bottom: 60,
                    child: Center(
                      child: Container(
                        width: 60,
                        height: 60,
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.person,
                          color: theme.colorScheme.onPrimary,
                          size: 32,
                        ),
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

          // Inventory
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
                      child: Text(
                        '인벤토리',
                        style: theme.textTheme.titleSmall,
                      ),
                    ),
                    Expanded(
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        children: [
                          _InventoryItem(icon: Icons.chair, label: '의자'),
                          _InventoryItem(icon: Icons.lightbulb_outline, label: '조명'),
                          _InventoryItem(icon: Icons.local_florist, label: '화분'),
                          _InventoryItem(icon: Icons.photo_outlined, label: '액자'),
                          _InventoryItem(icon: Icons.pets, label: '펫'),
                        ],
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
                          _RoomStat(label: '가구', value: '3개'),
                          _RoomStat(label: '책장 도서', value: '0권'),
                          _RoomStat(label: '방문객', value: '0명'),
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
}

class _RoomBackgroundPainter extends CustomPainter {
  final Color color;

  _RoomBackgroundPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color;

    // Floor
    final floorPath = Path()
      ..moveTo(0, size.height * 0.6)
      ..lineTo(size.width, size.height * 0.6)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(floorPath, paint..color = color.withOpacity(0.3));

    // Wall pattern (simple grid)
    final gridPaint = Paint()
      ..color = color.withOpacity(0.1)
      ..strokeWidth = 1;

    for (var i = 0; i < size.width; i += 40) {
      canvas.drawLine(
        Offset(i.toDouble(), 0),
        Offset(i.toDouble(), size.height * 0.6),
        gridPaint,
      );
    }
    for (var i = 0; i < size.height * 0.6; i += 40) {
      canvas.drawLine(
        Offset(0, i.toDouble()),
        Offset(size.width, i.toDouble()),
        gridPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _RoomItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isEditMode;

  const _RoomItem({
    required this.icon,
    required this.label,
    required this.isEditMode,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            color: theme.colorScheme.secondaryContainer,
            borderRadius: BorderRadius.circular(8),
            border: isEditMode
                ? Border.all(color: theme.colorScheme.secondary, width: 2)
                : null,
          ),
          child: Icon(
            icon,
            size: 32,
            color: theme.colorScheme.onSecondaryContainer,
          ),
        ),
        if (isEditMode) ...[
          const SizedBox(height: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall,
          ),
        ],
      ],
    );
  }
}

class _InventoryItem extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InventoryItem({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 24),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall,
          ),
        ],
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
