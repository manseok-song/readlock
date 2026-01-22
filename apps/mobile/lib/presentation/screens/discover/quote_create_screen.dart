import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class QuoteCreateScreen extends ConsumerStatefulWidget {
  final String? bookId;
  final String? bookTitle;

  const QuoteCreateScreen({
    super.key,
    this.bookId,
    this.bookTitle,
  });

  @override
  ConsumerState<QuoteCreateScreen> createState() => _QuoteCreateScreenState();
}

class _QuoteCreateScreenState extends ConsumerState<QuoteCreateScreen> {
  final _quoteController = TextEditingController();
  final _thoughtController = TextEditingController();
  final _pageController = TextEditingController();
  bool _isPublic = true;
  Color _backgroundColor = Colors.white;

  final _backgroundColors = [
    Colors.white,
    const Color(0xFFFFF8E7),
    const Color(0xFFE7F5FF),
    const Color(0xFFE7FFE7),
    const Color(0xFFFFE7F5),
    const Color(0xFFF5E7FF),
  ];

  @override
  void dispose() {
    _quoteController.dispose();
    _thoughtController.dispose();
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('인용구 작성'),
        actions: [
          TextButton(
            onPressed: _quoteController.text.isNotEmpty ? _save : null,
            child: const Text('저장'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Book info
            if (widget.bookTitle != null)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.book),
                  title: Text(widget.bookTitle!),
                  trailing: TextButton(
                    onPressed: () {
                      // TODO: Change book
                    },
                    child: const Text('변경'),
                  ),
                ),
              )
            else
              Card(
                child: ListTile(
                  leading: const Icon(Icons.add),
                  title: const Text('책 선택'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: Select book
                  },
                ),
              ),

            const SizedBox(height: 16),

            // Quote preview
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: _backgroundColor,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.format_quote,
                    size: 32,
                    color: Colors.black.withOpacity(0.2),
                  ),
                  TextField(
                    controller: _quoteController,
                    decoration: const InputDecoration(
                      hintText: '인상적인 문장을 입력하세요',
                      border: InputBorder.none,
                    ),
                    maxLines: null,
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      fontStyle: FontStyle.italic,
                      color: Colors.black87,
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Background color picker
            SizedBox(
              height: 48,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _backgroundColors.length,
                itemBuilder: (context, index) {
                  final color = _backgroundColors[index];
                  final isSelected = color == _backgroundColor;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: InkWell(
                      onTap: () {
                        setState(() {
                          _backgroundColor = color;
                        });
                      },
                      borderRadius: BorderRadius.circular(24),
                      child: Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: isSelected
                                ? theme.colorScheme.primary
                                : Colors.grey.shade300,
                            width: isSelected ? 3 : 1,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 24),

            // Page number
            TextField(
              controller: _pageController,
              decoration: InputDecoration(
                labelText: '페이지 (선택)',
                prefixIcon: const Icon(Icons.bookmark),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              keyboardType: TextInputType.number,
            ),

            const SizedBox(height: 16),

            // Thoughts
            TextField(
              controller: _thoughtController,
              decoration: InputDecoration(
                labelText: '나의 생각 (선택)',
                hintText: '이 문장에 대한 당신의 생각을 적어보세요',
                prefixIcon: const Icon(Icons.edit_note),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              maxLines: 3,
            ),

            const SizedBox(height: 16),

            // Privacy toggle
            SwitchListTile(
              title: const Text('공개'),
              subtitle: Text(
                _isPublic ? '다른 사람들이 이 인용구를 볼 수 있습니다' : '나만 볼 수 있습니다',
              ),
              value: _isPublic,
              onChanged: (value) {
                setState(() {
                  _isPublic = value;
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  void _save() {
    if (_quoteController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('인용구를 입력해주세요')),
      );
      return;
    }

    // TODO: Save quote
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('인용구가 저장되었습니다')),
    );
    Navigator.pop(context);
  }
}
