import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../core/utils/formatters.dart';

class ReadingScreen extends ConsumerStatefulWidget {
  final String bookId;

  const ReadingScreen({super.key, required this.bookId});

  @override
  ConsumerState<ReadingScreen> createState() => _ReadingScreenState();
}

class _ReadingScreenState extends ConsumerState<ReadingScreen> {
  int _elapsedSeconds = 0;
  bool _isReading = true;
  bool _isLocked = false;

  @override
  void initState() {
    super.initState();
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    _startTimer();
  }

  @override
  void dispose() {
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    super.dispose();
  }

  void _startTimer() {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 1));
      if (_isReading && mounted) {
        setState(() {
          _elapsedSeconds++;
        });
        return true;
      }
      return mounted;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            _buildHeader(context),

            // Main content
            Expanded(
              child: _buildMainContent(context),
            ),

            // Controls
            _buildControls(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => _showExitDialog(context),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  '독서 중',
                  style: theme.textTheme.titleMedium,
                ),
              ],
            ),
          ),
          if (_isLocked)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.lock, size: 14, color: Colors.green),
                  SizedBox(width: 4),
                  Text(
                    '잠금',
                    style: TextStyle(
                      color: Colors.green,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMainContent(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Book cover placeholder
        Container(
          width: 150,
          height: 200,
          decoration: BoxDecoration(
            color: theme.colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(8),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: Icon(
            Icons.book,
            size: 60,
            color: theme.colorScheme.primary,
          ),
        ).animate().fadeIn().scale(),

        const SizedBox(height: 48),

        // Timer
        Text(
          Formatters.timerHHMMSS(_elapsedSeconds),
          style: theme.textTheme.displayLarge?.copyWith(
            fontWeight: FontWeight.w300,
            fontFeatures: [const FontFeature.tabularFigures()],
          ),
        ).animate().fadeIn(delay: 300.ms),

        const SizedBox(height: 8),

        Text(
          _isReading ? '독서 중...' : '일시정지',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildControls(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _ControlButton(
            icon: _isReading ? Icons.pause : Icons.play_arrow,
            label: _isReading ? '일시정지' : '재개',
            onPressed: () {
              setState(() {
                _isReading = !_isReading;
              });
            },
          ),
          _ControlButton(
            icon: Icons.check_circle,
            label: '완료',
            isPrimary: true,
            onPressed: () => _showCompleteDialog(context),
          ),
        ],
      ),
    );
  }

  Future<void> _showExitDialog(BuildContext context) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('독서 종료'),
        content: const Text('독서를 종료하시겠습니까?\n현재까지의 기록이 저장됩니다.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('종료'),
          ),
        ],
      ),
    );

    if (result == true && mounted) {
      Navigator.pop(context);
    }
  }

  Future<void> _showCompleteDialog(BuildContext context) async {
    final result = await showDialog<int>(
      context: context,
      builder: (context) => _PagesReadDialog(),
    );

    if (result != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$result 페이지 읽음!')),
      );
      Navigator.pop(context);
    }
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final bool isPrimary;

  const _ControlButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.isPrimary = false,
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
            color: isPrimary
                ? theme.colorScheme.primary
                : theme.colorScheme.surfaceVariant,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: Icon(
              icon,
              color: isPrimary
                  ? theme.colorScheme.onPrimary
                  : theme.colorScheme.onSurfaceVariant,
            ),
            iconSize: 28,
            onPressed: onPressed,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: theme.textTheme.bodySmall,
        ),
      ],
    );
  }
}

class _PagesReadDialog extends StatefulWidget {
  @override
  State<_PagesReadDialog> createState() => _PagesReadDialogState();
}

class _PagesReadDialogState extends State<_PagesReadDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('독서 완료'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('이번 세션에서 읽은 페이지 수를 입력해주세요.'),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: '읽은 페이지 수',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('취소'),
        ),
        ElevatedButton(
          onPressed: () {
            final pages = int.tryParse(_controller.text) ?? 0;
            Navigator.pop(context, pages);
          },
          child: const Text('완료'),
        ),
      ],
    );
  }
}
