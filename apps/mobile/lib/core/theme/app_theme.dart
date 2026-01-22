import 'package:flutter/material.dart';
import 'app_colors.dart';
import 'app_typography.dart';

/// Application theme configuration
class AppTheme {
  AppTheme._();

  // Light Theme
  static ThemeData get light => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        colorScheme: _lightColorScheme,
        textTheme: AppTypography.lightTextTheme,
        fontFamily: AppTypography.fontFamily,
        scaffoldBackgroundColor: AppColors.backgroundLight,
        appBarTheme: _lightAppBarTheme,
        cardTheme: _lightCardTheme,
        elevatedButtonTheme: _elevatedButtonTheme,
        outlinedButtonTheme: _outlinedButtonTheme,
        textButtonTheme: _textButtonTheme,
        inputDecorationTheme: _inputDecorationTheme,
        bottomNavigationBarTheme: _lightBottomNavTheme,
        floatingActionButtonTheme: _fabTheme,
        dividerTheme: _lightDividerTheme,
        chipTheme: _lightChipTheme,
        snackBarTheme: _snackBarTheme,
        dialogTheme: _dialogTheme,
        bottomSheetTheme: _bottomSheetTheme,
      );

  // Dark Theme
  static ThemeData get dark => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: _darkColorScheme,
        textTheme: AppTypography.darkTextTheme,
        fontFamily: AppTypography.fontFamily,
        scaffoldBackgroundColor: AppColors.backgroundDark,
        appBarTheme: _darkAppBarTheme,
        cardTheme: _darkCardTheme,
        elevatedButtonTheme: _elevatedButtonTheme,
        outlinedButtonTheme: _outlinedButtonTheme,
        textButtonTheme: _textButtonTheme,
        inputDecorationTheme: _inputDecorationThemeDark,
        bottomNavigationBarTheme: _darkBottomNavTheme,
        floatingActionButtonTheme: _fabTheme,
        dividerTheme: _darkDividerTheme,
        chipTheme: _darkChipTheme,
        snackBarTheme: _snackBarTheme,
        dialogTheme: _dialogThemeDark,
        bottomSheetTheme: _bottomSheetThemeDark,
      );

  // Color Schemes
  static const ColorScheme _lightColorScheme = ColorScheme(
    brightness: Brightness.light,
    primary: AppColors.primary,
    onPrimary: AppColors.white,
    primaryContainer: Color(0xFFE0E7FF),
    onPrimaryContainer: Color(0xFF1E1B4B),
    secondary: AppColors.secondary,
    onSecondary: AppColors.white,
    secondaryContainer: Color(0xFFD1FAE5),
    onSecondaryContainer: Color(0xFF064E3B),
    tertiary: AppColors.accent,
    onTertiary: AppColors.white,
    tertiaryContainer: Color(0xFFFEF3C7),
    onTertiaryContainer: Color(0xFF78350F),
    error: AppColors.error,
    onError: AppColors.white,
    errorContainer: AppColors.errorLight,
    onErrorContainer: Color(0xFF7F1D1D),
    background: AppColors.backgroundLight,
    onBackground: AppColors.textPrimaryLight,
    surface: AppColors.surfaceLight,
    onSurface: AppColors.textPrimaryLight,
    surfaceVariant: AppColors.gray100,
    onSurfaceVariant: AppColors.gray600,
    outline: AppColors.gray300,
    outlineVariant: AppColors.gray200,
    shadow: AppColors.black,
    scrim: AppColors.black,
    inverseSurface: AppColors.gray800,
    onInverseSurface: AppColors.gray100,
    inversePrimary: AppColors.primaryLight,
  );

  static const ColorScheme _darkColorScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: AppColors.primaryLight,
    onPrimary: Color(0xFF1E1B4B),
    primaryContainer: AppColors.primaryDark,
    onPrimaryContainer: Color(0xFFE0E7FF),
    secondary: AppColors.secondaryLight,
    onSecondary: Color(0xFF064E3B),
    secondaryContainer: AppColors.secondaryDark,
    onSecondaryContainer: Color(0xFFD1FAE5),
    tertiary: AppColors.accentLight,
    onTertiary: Color(0xFF78350F),
    tertiaryContainer: AppColors.accentDark,
    onTertiaryContainer: Color(0xFFFEF3C7),
    error: Color(0xFFFCA5A5),
    onError: Color(0xFF7F1D1D),
    errorContainer: Color(0xFF991B1B),
    onErrorContainer: AppColors.errorLight,
    background: AppColors.backgroundDark,
    onBackground: AppColors.textPrimaryDark,
    surface: AppColors.surfaceDark,
    onSurface: AppColors.textPrimaryDark,
    surfaceVariant: AppColors.gray800,
    onSurfaceVariant: AppColors.gray400,
    outline: AppColors.gray600,
    outlineVariant: AppColors.gray700,
    shadow: AppColors.black,
    scrim: AppColors.black,
    inverseSurface: AppColors.gray100,
    onInverseSurface: AppColors.gray800,
    inversePrimary: AppColors.primaryDark,
  );

  // AppBar Themes
  static const AppBarTheme _lightAppBarTheme = AppBarTheme(
    backgroundColor: AppColors.surfaceLight,
    foregroundColor: AppColors.textPrimaryLight,
    elevation: 0,
    scrolledUnderElevation: 1,
    centerTitle: true,
    titleTextStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: AppColors.textPrimaryLight,
    ),
  );

  static const AppBarTheme _darkAppBarTheme = AppBarTheme(
    backgroundColor: AppColors.surfaceDark,
    foregroundColor: AppColors.textPrimaryDark,
    elevation: 0,
    scrolledUnderElevation: 1,
    centerTitle: true,
    titleTextStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: AppColors.textPrimaryDark,
    ),
  );

  // Card Themes
  static const CardTheme _lightCardTheme = CardTheme(
    color: AppColors.surfaceLight,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(16)),
    ),
    margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
  );

  static const CardTheme _darkCardTheme = CardTheme(
    color: AppColors.surfaceDark,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(16)),
    ),
    margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
  );

  // Button Themes
  static final ElevatedButtonThemeData _elevatedButtonTheme =
      ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.primary,
      foregroundColor: AppColors.white,
      elevation: 0,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      textStyle: const TextStyle(
        fontFamily: AppTypography.fontFamily,
        fontSize: 16,
        fontWeight: FontWeight.w600,
      ),
    ),
  );

  static final OutlinedButtonThemeData _outlinedButtonTheme =
      OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: AppColors.primary,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      side: const BorderSide(color: AppColors.primary, width: 1.5),
      textStyle: const TextStyle(
        fontFamily: AppTypography.fontFamily,
        fontSize: 16,
        fontWeight: FontWeight.w600,
      ),
    ),
  );

  static final TextButtonThemeData _textButtonTheme = TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: AppColors.primary,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      textStyle: const TextStyle(
        fontFamily: AppTypography.fontFamily,
        fontSize: 14,
        fontWeight: FontWeight.w600,
      ),
    ),
  );

  // Input Decoration Theme
  static final InputDecorationTheme _inputDecorationTheme = InputDecorationTheme(
    filled: true,
    fillColor: AppColors.gray50,
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.primary, width: 2),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.error, width: 1),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.error, width: 2),
    ),
    hintStyle: const TextStyle(color: AppColors.gray400),
    labelStyle: const TextStyle(color: AppColors.gray600),
    errorStyle: const TextStyle(color: AppColors.error, fontSize: 12),
  );

  static final InputDecorationTheme _inputDecorationThemeDark =
      InputDecorationTheme(
    filled: true,
    fillColor: AppColors.gray800,
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.primaryLight, width: 2),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.error, width: 1),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: AppColors.error, width: 2),
    ),
    hintStyle: const TextStyle(color: AppColors.gray500),
    labelStyle: const TextStyle(color: AppColors.gray400),
    errorStyle: TextStyle(color: Colors.red.shade300, fontSize: 12),
  );

  // Bottom Navigation
  static const BottomNavigationBarThemeData _lightBottomNavTheme =
      BottomNavigationBarThemeData(
    backgroundColor: AppColors.surfaceLight,
    selectedItemColor: AppColors.primary,
    unselectedItemColor: AppColors.gray400,
    type: BottomNavigationBarType.fixed,
    elevation: 8,
    selectedLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 12,
      fontWeight: FontWeight.w600,
    ),
    unselectedLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 12,
    ),
  );

  static const BottomNavigationBarThemeData _darkBottomNavTheme =
      BottomNavigationBarThemeData(
    backgroundColor: AppColors.surfaceDark,
    selectedItemColor: AppColors.primaryLight,
    unselectedItemColor: AppColors.gray500,
    type: BottomNavigationBarType.fixed,
    elevation: 8,
    selectedLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 12,
      fontWeight: FontWeight.w600,
    ),
    unselectedLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 12,
    ),
  );

  // FAB Theme
  static const FloatingActionButtonThemeData _fabTheme =
      FloatingActionButtonThemeData(
    backgroundColor: AppColors.primary,
    foregroundColor: AppColors.white,
    elevation: 4,
    shape: CircleBorder(),
  );

  // Divider Theme
  static const DividerThemeData _lightDividerTheme = DividerThemeData(
    color: AppColors.gray200,
    thickness: 1,
    space: 1,
  );

  static const DividerThemeData _darkDividerTheme = DividerThemeData(
    color: AppColors.gray700,
    thickness: 1,
    space: 1,
  );

  // Chip Theme
  static const ChipThemeData _lightChipTheme = ChipThemeData(
    backgroundColor: AppColors.gray100,
    selectedColor: AppColors.primary,
    labelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 14,
      color: AppColors.textPrimaryLight,
    ),
    secondaryLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 14,
      color: AppColors.white,
    ),
    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(20)),
    ),
  );

  static const ChipThemeData _darkChipTheme = ChipThemeData(
    backgroundColor: AppColors.gray800,
    selectedColor: AppColors.primaryLight,
    labelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 14,
      color: AppColors.textPrimaryDark,
    ),
    secondaryLabelStyle: TextStyle(
      fontFamily: AppTypography.fontFamily,
      fontSize: 14,
      color: AppColors.black,
    ),
    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(20)),
    ),
  );

  // SnackBar Theme
  static const SnackBarThemeData _snackBarTheme = SnackBarThemeData(
    behavior: SnackBarBehavior.floating,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
  );

  // Dialog Theme
  static const DialogTheme _dialogTheme = DialogTheme(
    backgroundColor: AppColors.surfaceLight,
    elevation: 8,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(20)),
    ),
  );

  static const DialogTheme _dialogThemeDark = DialogTheme(
    backgroundColor: AppColors.surfaceDark,
    elevation: 8,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(20)),
    ),
  );

  // Bottom Sheet Theme
  static const BottomSheetThemeData _bottomSheetTheme = BottomSheetThemeData(
    backgroundColor: AppColors.surfaceLight,
    elevation: 8,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(20),
        topRight: Radius.circular(20),
      ),
    ),
  );

  static const BottomSheetThemeData _bottomSheetThemeDark = BottomSheetThemeData(
    backgroundColor: AppColors.surfaceDark,
    elevation: 8,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(20),
        topRight: Radius.circular(20),
      ),
    ),
  );
}
