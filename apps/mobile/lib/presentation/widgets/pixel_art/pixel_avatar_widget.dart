import 'package:flutter/material.dart';

class PixelAvatarWidget extends StatelessWidget {
  final Map<String, dynamic>? faceAssetData;
  final Map<String, dynamic>? hairAssetData;
  final Map<String, dynamic>? outfitAssetData;
  final Map<String, dynamic>? accessoryAssetData;
  final String skinColor;
  final double scale;

  const PixelAvatarWidget({
    super.key,
    this.faceAssetData,
    this.hairAssetData,
    this.outfitAssetData,
    this.accessoryAssetData,
    this.skinColor = '#FFD5B8',
    this.scale = 1.0,
  });

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(64 * scale, 80 * scale),
      painter: PixelAvatarPainter(
        faceAssetData: faceAssetData,
        hairAssetData: hairAssetData,
        outfitAssetData: outfitAssetData,
        accessoryAssetData: accessoryAssetData,
        skinColor: skinColor,
        scale: scale,
      ),
    );
  }
}

class PixelAvatarPainter extends CustomPainter {
  final Map<String, dynamic>? faceAssetData;
  final Map<String, dynamic>? hairAssetData;
  final Map<String, dynamic>? outfitAssetData;
  final Map<String, dynamic>? accessoryAssetData;
  final String skinColor;
  final double scale;

  PixelAvatarPainter({
    this.faceAssetData,
    this.hairAssetData,
    this.outfitAssetData,
    this.accessoryAssetData,
    required this.skinColor,
    required this.scale,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final pixelSize = 4.0 * scale;
    final skinPaint = Paint()..color = _parseColor(skinColor);

    // Draw default avatar if no asset data
    if (faceAssetData == null) {
      _drawDefaultAvatar(canvas, size, pixelSize, skinPaint);
      return;
    }

    // Draw layers in order: face -> outfit -> hair -> accessory
    _drawAssetLayers(canvas, faceAssetData, pixelSize, skinPaint);
    _drawAssetLayers(canvas, outfitAssetData, pixelSize, skinPaint);
    _drawAssetLayers(canvas, hairAssetData, pixelSize, skinPaint);
    _drawAssetLayers(canvas, accessoryAssetData, pixelSize, skinPaint);
  }

  void _drawDefaultAvatar(Canvas canvas, Size size, double pixelSize, Paint skinPaint) {
    // Default face pixels
    final defaultFacePixels = [
      // Face outline
      [4, 4], [5, 4], [6, 4], [7, 4], [8, 4], [9, 4], [10, 4], [11, 4],
      [3, 5], [4, 5], [5, 5], [6, 5], [7, 5], [8, 5], [9, 5], [10, 5], [11, 5], [12, 5],
      [3, 6], [4, 6], [6, 6], [7, 6], [8, 6], [9, 6], [11, 6], [12, 6],
      [3, 7], [4, 7], [5, 7], [6, 7], [7, 7], [8, 7], [9, 7], [10, 7], [11, 7], [12, 7],
      [4, 8], [5, 8], [6, 8], [9, 8], [10, 8], [11, 8],
      [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [10, 9],
      [6, 10], [7, 10], [8, 10], [9, 10],
    ];

    // Eyes
    final eyePixels = [[5, 6], [10, 6]];
    final eyePaint = Paint()..color = Colors.black;

    // Blush
    final blushPixels = [[7, 8], [8, 8]];
    final blushPaint = Paint()..color = const Color(0xFFFF9999);

    // Draw face
    for (final pixel in defaultFacePixels) {
      canvas.drawRect(
        Rect.fromLTWH(pixel[0] * pixelSize, pixel[1] * pixelSize, pixelSize, pixelSize),
        skinPaint,
      );
    }

    // Draw eyes
    for (final pixel in eyePixels) {
      canvas.drawRect(
        Rect.fromLTWH(pixel[0] * pixelSize, pixel[1] * pixelSize, pixelSize, pixelSize),
        eyePaint,
      );
    }

    // Draw blush
    for (final pixel in blushPixels) {
      canvas.drawRect(
        Rect.fromLTWH(pixel[0] * pixelSize, pixel[1] * pixelSize, pixelSize, pixelSize),
        blushPaint,
      );
    }

    // Default hair
    final hairPaint = Paint()..color = const Color(0xFF3D2314);
    final hairHighlight = Paint()..color = const Color(0xFF5C3A21);
    final defaultHairPixels = [
      [5, 2], [6, 2], [7, 2], [8, 2], [9, 2], [10, 2],
      [4, 3], [11, 3],
      [3, 4], [12, 4],
      [2, 5], [13, 5],
      [2, 6], [13, 6],
      [2, 7], [13, 7],
    ];

    for (final pixel in defaultHairPixels) {
      canvas.drawRect(
        Rect.fromLTWH(pixel[0] * pixelSize, pixel[1] * pixelSize, pixelSize, pixelSize),
        hairPaint,
      );
    }

    // Default outfit
    final outfitPaint = Paint()..color = const Color(0xFF4A90D9);
    final defaultOutfitPixels = [
      [5, 11], [6, 11], [7, 11], [8, 11], [9, 11], [10, 11],
      [4, 12], [5, 12], [6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12],
      [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13],
      [3, 14], [4, 14], [5, 14], [6, 14], [7, 14], [8, 14], [9, 14], [10, 14], [11, 14], [12, 14],
    ];

    for (final pixel in defaultOutfitPixels) {
      canvas.drawRect(
        Rect.fromLTWH(pixel[0] * pixelSize, pixel[1] * pixelSize, pixelSize, pixelSize),
        outfitPaint,
      );
    }
  }

  void _drawAssetLayers(Canvas canvas, Map<String, dynamic>? assetData, double pixelSize, Paint skinPaint) {
    if (assetData == null) return;

    final layers = assetData['layers'] as List<dynamic>? ?? [];

    for (final layer in layers) {
      final pixels = layer['pixels'] as List<dynamic>? ?? [];

      for (final pixel in pixels) {
        final x = (pixel['x'] as num).toDouble();
        final y = (pixel['y'] as num).toDouble();
        final colorStr = pixel['color'] as String;

        Paint paint;
        if (colorStr == 'skin') {
          paint = skinPaint;
        } else {
          paint = Paint()..color = _parseColor(colorStr);
        }

        canvas.drawRect(
          Rect.fromLTWH(x * pixelSize, y * pixelSize, pixelSize, pixelSize),
          paint,
        );
      }
    }
  }

  Color _parseColor(String colorStr) {
    if (colorStr.startsWith('#')) {
      final hex = colorStr.replaceFirst('#', '');
      if (hex.length == 6) {
        return Color(int.parse('FF$hex', radix: 16));
      } else if (hex.length == 8) {
        return Color(int.parse(hex, radix: 16));
      }
    }
    return Colors.grey;
  }

  @override
  bool shouldRepaint(covariant PixelAvatarPainter oldDelegate) {
    return faceAssetData != oldDelegate.faceAssetData ||
        hairAssetData != oldDelegate.hairAssetData ||
        outfitAssetData != oldDelegate.outfitAssetData ||
        accessoryAssetData != oldDelegate.accessoryAssetData ||
        skinColor != oldDelegate.skinColor ||
        scale != oldDelegate.scale;
  }
}

class SkinColorPicker extends StatelessWidget {
  final String selectedColor;
  final ValueChanged<String> onColorSelected;

  static const skinColors = [
    '#FFE4C4', // bisque
    '#FFD5B8', // light
    '#F5C8A8', // medium light
    '#D4A574', // medium
    '#C68E5F', // medium dark
    '#8B6914', // dark
  ];

  const SkinColorPicker({
    super.key,
    required this.selectedColor,
    required this.onColorSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: skinColors.map((color) {
        final isSelected = color.toUpperCase() == selectedColor.toUpperCase();
        return GestureDetector(
          onTap: () => onColorSelected(color),
          child: Container(
            width: 36,
            height: 36,
            margin: const EdgeInsets.symmetric(horizontal: 4),
            decoration: BoxDecoration(
              color: _parseColor(color),
              shape: BoxShape.circle,
              border: isSelected
                  ? Border.all(color: Theme.of(context).colorScheme.primary, width: 3)
                  : Border.all(color: Colors.grey.shade300, width: 1),
            ),
          ),
        );
      }).toList(),
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
}
