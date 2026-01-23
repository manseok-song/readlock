import 'package:flutter/material.dart';
import 'dart:math' as math;

class PixelBookshelfWidget extends StatelessWidget {
  final List<String> bookIds;
  final int maxSlots;
  final VoidCallback? onAddBook;
  final bool isEditMode;

  const PixelBookshelfWidget({
    super.key,
    required this.bookIds,
    this.maxSlots = 10,
    this.onAddBook,
    this.isEditMode = false,
  });

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(120, 160),
      painter: PixelBookshelfPainter(
        bookIds: bookIds,
        maxSlots: maxSlots,
      ),
      child: isEditMode
          ? _buildEditOverlay(context)
          : null,
    );
  }

  Widget _buildEditOverlay(BuildContext context) {
    return Positioned.fill(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onAddBook,
          borderRadius: BorderRadius.circular(8),
          child: bookIds.length < maxSlots
              ? Center(
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(
                      Icons.add,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),
                )
              : null,
        ),
      ),
    );
  }
}

class PixelBookshelfPainter extends CustomPainter {
  final List<String> bookIds;
  final int maxSlots;

  PixelBookshelfPainter({
    required this.bookIds,
    required this.maxSlots,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final woodPaint = Paint()..color = const Color(0xFF8B6B4F);
    final woodDarkPaint = Paint()..color = const Color(0xFF654321);
    final woodLightPaint = Paint()..color = const Color(0xFFA08060);

    // Draw bookshelf frame
    _drawBookshelfFrame(canvas, size, woodPaint, woodDarkPaint, woodLightPaint);

    // Draw books
    _drawBooks(canvas, size);
  }

  void _drawBookshelfFrame(Canvas canvas, Size size, Paint wood, Paint dark, Paint light) {
    // Back panel
    canvas.drawRect(
      Rect.fromLTWH(4, 4, size.width - 8, size.height - 8),
      wood,
    );

    // Left side
    canvas.drawRect(
      Rect.fromLTWH(0, 0, 8, size.height),
      dark,
    );

    // Right side
    canvas.drawRect(
      Rect.fromLTWH(size.width - 8, 0, 8, size.height),
      dark,
    );

    // Top
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, 8),
      dark,
    );

    // Bottom
    canvas.drawRect(
      Rect.fromLTWH(0, size.height - 8, size.width, 8),
      dark,
    );

    // Shelves (4 rows)
    final shelfHeight = (size.height - 16) / 4;
    for (var i = 1; i < 4; i++) {
      final y = 8 + shelfHeight * i;
      canvas.drawRect(
        Rect.fromLTWH(8, y - 2, size.width - 16, 4),
        light,
      );
    }
  }

  void _drawBooks(Canvas canvas, Size size) {
    if (bookIds.isEmpty) return;

    final shelfHeight = (size.height - 16) / 4;
    final bookWidth = 8.0;
    final booksPerShelf = ((size.width - 24) / bookWidth).floor();

    for (var i = 0; i < bookIds.length && i < maxSlots; i++) {
      final shelfIndex = i ~/ booksPerShelf;
      final posInShelf = i % booksPerShelf;

      if (shelfIndex >= 4) break;

      final bookColor = _getBookColor(bookIds[i]);
      final bookHeight = shelfHeight - 8 + (math.Random(bookIds[i].hashCode).nextDouble() * 6 - 3);

      final x = 12.0 + posInShelf * bookWidth;
      final y = 8 + shelfHeight * shelfIndex + (shelfHeight - bookHeight - 2);

      // Book spine
      final bookPaint = Paint()..color = bookColor;
      canvas.drawRect(
        Rect.fromLTWH(x, y, bookWidth - 2, bookHeight),
        bookPaint,
      );

      // Book spine highlight
      final highlightPaint = Paint()
        ..color = Colors.white.withOpacity(0.2);
      canvas.drawRect(
        Rect.fromLTWH(x, y, 2, bookHeight),
        highlightPaint,
      );

      // Book spine line
      final linePaint = Paint()
        ..color = Colors.black.withOpacity(0.3)
        ..strokeWidth = 1;
      final lineY = y + bookHeight * 0.3;
      canvas.drawLine(
        Offset(x + 1, lineY),
        Offset(x + bookWidth - 3, lineY),
        linePaint,
      );
    }
  }

  Color _getBookColor(String bookId) {
    // Generate consistent color from book ID hash
    final hash = bookId.hashCode;
    final colors = [
      const Color(0xFF8B0000), // Dark red
      const Color(0xFF006400), // Dark green
      const Color(0xFF00008B), // Dark blue
      const Color(0xFF8B4513), // Saddle brown
      const Color(0xFF4B0082), // Indigo
      const Color(0xFF2F4F4F), // Dark slate gray
      const Color(0xFF8B008B), // Dark magenta
      const Color(0xFF556B2F), // Dark olive green
      const Color(0xFF191970), // Midnight blue
      const Color(0xFF800000), // Maroon
    ];
    return colors[hash.abs() % colors.length];
  }

  @override
  bool shouldRepaint(covariant PixelBookshelfPainter oldDelegate) {
    return bookIds != oldDelegate.bookIds ||
        maxSlots != oldDelegate.maxSlots;
  }
}

class BookSelectionDialog extends StatelessWidget {
  final List<Map<String, dynamic>> availableBooks;
  final List<String> selectedBookIds;
  final Function(String bookId) onBookSelected;

  const BookSelectionDialog({
    super.key,
    required this.availableBooks,
    required this.selectedBookIds,
    required this.onBookSelected,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Text('책장에 책 추가'),
      content: SizedBox(
        width: double.maxFinite,
        height: 300,
        child: availableBooks.isEmpty
            ? Center(
                child: Text(
                  '추가할 수 있는 책이 없습니다.\n먼저 책을 읽어보세요!',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              )
            : ListView.builder(
                itemCount: availableBooks.length,
                itemBuilder: (context, index) {
                  final book = availableBooks[index];
                  final bookId = book['id'] as String;
                  final isSelected = selectedBookIds.contains(bookId);

                  return ListTile(
                    leading: Container(
                      width: 40,
                      height: 56,
                      decoration: BoxDecoration(
                        color: _getBookColor(bookId),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    title: Text(
                      book['title'] as String? ?? '제목 없음',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      book['author'] as String? ?? '작가 미상',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: isSelected
                        ? Icon(
                            Icons.check_circle,
                            color: theme.colorScheme.primary,
                          )
                        : const Icon(Icons.add_circle_outline),
                    onTap: () => onBookSelected(bookId),
                  );
                },
              ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('닫기'),
        ),
      ],
    );
  }

  Color _getBookColor(String bookId) {
    final hash = bookId.hashCode;
    final colors = [
      const Color(0xFF8B0000),
      const Color(0xFF006400),
      const Color(0xFF00008B),
      const Color(0xFF8B4513),
      const Color(0xFF4B0082),
    ];
    return colors[hash.abs() % colors.length];
  }
}
