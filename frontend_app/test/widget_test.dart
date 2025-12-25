import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_app/main.dart';

void main() {
  testWidgets('Interview app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const InterviewApp());

    // Verify that the app title is present
    expect(find.text('AI Interview System'), findsOneWidget);

    // Verify that the start button is present
    expect(find.text('Start Interview'), findsOneWidget);

    // Verify that the app has rendered successfully
    expect(find.byType(MaterialApp), findsOneWidget);
  });

  testWidgets('Navigation to interview screen', (WidgetTester tester) async {
    // Build the app
    await tester.pumpWidget(const InterviewApp());

    // Find and tap the start button
    final startButton = find.text('Start Interview');
    expect(startButton, findsOneWidget);

    await tester.tap(startButton);
    await tester.pumpAndSettle();

    // Verify navigation occurred by checking for the interview screen title
    expect(find.text('Interview in Progress'), findsOneWidget);
  });
}