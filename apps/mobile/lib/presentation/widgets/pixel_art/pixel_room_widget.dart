import 'package:flutter/material.dart';

class PixelRoomWidget extends StatelessWidget {
  final Map<String, dynamic>? backgroundAssetData;
  final List<Map<String, dynamic>> furnitureItems;
  final bool isEditMode;
  final Function(String itemId, Offset position)? onFurnitureMoved;

  const PixelRoomWidget({
    super.key,
    this.backgroundAssetData,
    this.furnitureItems = const [],
    this.isEditMode = false,
    this.onFurnitureMoved,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: CustomPaint(
        painter: PixelRoomBackgroundPainter(
          assetData: backgroundAssetData,
        ),
        child: Stack(
          children: [
            for (final item in furnitureItems)
              _buildFurnitureItem(context, item),
          ],
        ),
      ),
    );
  }

  Widget _buildFurnitureItem(BuildContext context, Map<String, dynamic> item) {
    final position = item['position'] as Map<String, dynamic>?;
    final x = (position?['x'] as num?)?.toDouble() ?? 0;
    final y = (position?['y'] as num?)?.toDouble() ?? 0;
    final itemId = item['id'] as String? ?? '';
    final assetData = item['asset_data'] as Map<String, dynamic>?;

    Widget furnitureWidget = PixelFurnitureWidget(
      assetData: assetData,
      isEditMode: isEditMode,
    );

    if (isEditMode) {
      return Positioned(
        left: x,
        top: y,
        child: Draggable<String>(
          data: itemId,
          feedback: Opacity(
            opacity: 0.7,
            child: furnitureWidget,
          ),
          childWhenDragging: Opacity(
            opacity: 0.3,
            child: furnitureWidget,
          ),
          onDragEnd: (details) {
            if (onFurnitureMoved != null) {
              final renderBox = context.findRenderObject() as RenderBox?;
              if (renderBox != null) {
                final localPosition = renderBox.globalToLocal(details.offset);
                onFurnitureMoved!(itemId, localPosition);
              }
            }
          },
          child: furnitureWidget,
        ),
      );
    }

    return Positioned(
      left: x,
      top: y,
      child: furnitureWidget,
    );
  }
}

class PixelRoomBackgroundPainter extends CustomPainter {
  final Map<String, dynamic>? assetData;

  PixelRoomBackgroundPainter({this.assetData});

  @override
  void paint(Canvas canvas, Size size) {
    final colors = assetData?['colors'] as Map<String, dynamic>?;

    final wallColor = _parseColor(colors?['wall'] as String? ?? '#E8D4B8');
    final floorColor = _parseColor(colors?['floor'] as String? ?? '#8B6B4F');
    final accentColor = _parseColor(colors?['accent'] as String? ?? '#654321');

    // Draw wall
    final wallPaint = Paint()..color = wallColor;
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, size.height * 0.6),
      wallPaint,
    );

    // Draw floor
    final floorPaint = Paint()..color = floorColor;
    canvas.drawRect(
      Rect.fromLTWH(0, size.height * 0.6, size.width, size.height * 0.4),
      floorPaint,
    );

    // Draw wall pattern (pixel grid)
    final gridPaint = Paint()
      ..color = accentColor.withOpacity(0.1)
      ..strokeWidth = 1;

    const gridSize = 20.0;
    for (var x = 0.0; x < size.width; x += gridSize) {
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height * 0.6),
        gridPaint,
      );
    }
    for (var y = 0.0; y < size.height * 0.6; y += gridSize) {
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        gridPaint,
      );
    }

    // Draw floor boards
    final floorLinePaint = Paint()
      ..color = accentColor.withOpacity(0.2)
      ..strokeWidth = 2;

    for (var y = size.height * 0.6; y < size.height; y += 30) {
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        floorLinePaint,
      );
    }

    // Draw baseboard
    final baseboardPaint = Paint()..color = accentColor;
    canvas.drawRect(
      Rect.fromLTWH(0, size.height * 0.6 - 4, size.width, 8),
      baseboardPaint,
    );
  }

  Color _parseColor(String colorStr) {
    if (colorStr.startsWith('#')) {
      final hex = colorStr.replaceFirst('#', '');
      if (hex.length == 6) {
        return Color(int.parse('FF$hex', radix: 16));
      }
    }
    return Colors.grey;
  }

  @override
  bool shouldRepaint(covariant PixelRoomBackgroundPainter oldDelegate) {
    return assetData != oldDelegate.assetData;
  }
}

class PixelFurnitureWidget extends StatelessWidget {
  final Map<String, dynamic>? assetData;
  final bool isEditMode;

  const PixelFurnitureWidget({
    super.key,
    this.assetData,
    this.isEditMode = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final furnitureType = assetData?['furnitureType'] as String? ?? 'unknown';
    final width = ((assetData?['width'] as num?) ?? 24).toDouble() * 2;
    final height = ((assetData?['height'] as num?) ?? 40).toDouble() * 2;

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        border: isEditMode
            ? Border.all(color: theme.colorScheme.primary, width: 2)
            : null,
      ),
      child: CustomPaint(
        painter: PixelFurniturePainter(
          furnitureType: furnitureType,
          assetData: assetData,
        ),
      ),
    );
  }
}

class PixelFurniturePainter extends CustomPainter {
  final String furnitureType;
  final Map<String, dynamic>? assetData;

  PixelFurniturePainter({
    required this.furnitureType,
    this.assetData,
  });

  @override
  void paint(Canvas canvas, Size size) {
    switch (furnitureType) {
      case 'bookshelf':
        _drawBookshelf(canvas, size);
        break;
      case 'desk':
        _drawDesk(canvas, size);
        break;
      case 'chair':
        _drawChair(canvas, size);
        break;
      case 'lamp':
        _drawLamp(canvas, size);
        break;
      default:
        _drawDefault(canvas, size);
    }
  }

  void _drawBookshelf(Canvas canvas, Size size) {
    final woodPaint = Paint()..color = const Color(0xFF8B6B4F);
    final woodDarkPaint = Paint()..color = const Color(0xFF654321);

    // Main frame
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), woodPaint);

    // Shelves
    for (var i = 0; i < 4; i++) {
      final y = size.height * (0.2 + i * 0.2);
      canvas.drawRect(
        Rect.fromLTWH(0, y, size.width, 4),
        woodDarkPaint,
      );
    }

    // Side panels
    canvas.drawRect(Rect.fromLTWH(0, 0, 4, size.height), woodDarkPaint);
    canvas.drawRect(Rect.fromLTWH(size.width - 4, 0, 4, size.height), woodDarkPaint);
  }

  void _drawDesk(Canvas canvas, Size size) {
    final woodPaint = Paint()..color = const Color(0xFF8B6B4F);
    final woodDarkPaint = Paint()..color = const Color(0xFF654321);

    // Desktop
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, size.height * 0.15),
      woodPaint,
    );

    // Legs
    canvas.drawRect(
      Rect.fromLTWH(4, size.height * 0.15, 8, size.height * 0.85),
      woodDarkPaint,
    );
    canvas.drawRect(
      Rect.fromLTWH(size.width - 12, size.height * 0.15, 8, size.height * 0.85),
      woodDarkPaint,
    );
  }

  void _drawChair(Canvas canvas, Size size) {
    final fabricPaint = Paint()..color = const Color(0xFF8B4513);
    final woodPaint = Paint()..color = const Color(0xFF654321);

    // Back
    canvas.drawRect(
      Rect.fromLTWH(size.width * 0.1, 0, size.width * 0.8, size.height * 0.5),
      fabricPaint,
    );

    // Seat
    canvas.drawRect(
      Rect.fromLTWH(0, size.height * 0.45, size.width, size.height * 0.2),
      fabricPaint,
    );

    // Legs
    canvas.drawRect(
      Rect.fromLTWH(4, size.height * 0.65, 4, size.height * 0.35),
      woodPaint,
    );
    canvas.drawRect(
      Rect.fromLTWH(size.width - 8, size.height * 0.65, 4, size.height * 0.35),
      woodPaint,
    );
  }

  void _drawLamp(Canvas canvas, Size size) {
    final shadePaint = Paint()..color = const Color(0xFFFFF8DC);
    final basePaint = Paint()..color = const Color(0xFF2F2F2F);
    final polePaint = Paint()..color = const Color(0xFF4A4A4A);

    // Shade
    final shadePath = Path()
      ..moveTo(size.width * 0.2, 0)
      ..lineTo(size.width * 0.8, 0)
      ..lineTo(size.width * 0.7, size.height * 0.3)
      ..lineTo(size.width * 0.3, size.height * 0.3)
      ..close();
    canvas.drawPath(shadePath, shadePaint);

    // Pole
    canvas.drawRect(
      Rect.fromLTWH(size.width * 0.45, size.height * 0.3, size.width * 0.1, size.height * 0.6),
      polePaint,
    );

    // Base
    canvas.drawRect(
      Rect.fromLTWH(size.width * 0.25, size.height * 0.9, size.width * 0.5, size.height * 0.1),
      basePaint,
    );
  }

  void _drawDefault(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.grey;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);
  }

  @override
  bool shouldRepaint(covariant PixelFurniturePainter oldDelegate) {
    return furnitureType != oldDelegate.furnitureType ||
        assetData != oldDelegate.assetData;
  }
}
