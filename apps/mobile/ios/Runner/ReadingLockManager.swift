import Foundation
import UIKit
import AVFoundation
import UserNotifications

/// Manager for reading focus mode on iOS
/// Uses background audio and screen brightness management
class ReadingLockManager: NSObject {

    static let shared = ReadingLockManager()

    private var isReading = false
    private var isPaused = false
    private var sessionId: String = ""
    private var bookTitle: String = ""
    private var startTime: Date?
    private var elapsedTime: TimeInterval = 0

    private var audioPlayer: AVAudioPlayer?
    private var timer: Timer?
    private var originalBrightness: CGFloat = 0.5

    // Callback to Flutter
    var onStatusChanged: ((String, String, Int) -> Void)?

    private override init() {
        super.init()
        setupAudioSession()
        setupNotifications()
    }

    // MARK: - Public Methods

    func startReading(bookTitle: String, sessionId: String) {
        guard !isReading else { return }

        self.bookTitle = bookTitle
        self.sessionId = sessionId
        self.isReading = true
        self.isPaused = false
        self.startTime = Date()
        self.elapsedTime = 0

        // Keep screen on
        UIApplication.shared.isIdleTimerDisabled = true
        originalBrightness = UIScreen.main.brightness

        // Start silent audio for background
        startSilentAudio()

        // Start timer for elapsed time
        startTimer()

        // Enable Focus mode if available (iOS 15+)
        enableFocusMode()

        // Notify Flutter
        onStatusChanged?("started", sessionId, 0)
    }

    func stopReading() {
        guard isReading else { return }

        // Calculate duration
        if !isPaused, let start = startTime {
            elapsedTime += Date().timeIntervalSince(start)
        }
        let duration = Int(elapsedTime)

        // Reset state
        isReading = false
        isPaused = false

        // Allow screen to sleep
        UIApplication.shared.isIdleTimerDisabled = false

        // Stop audio
        stopSilentAudio()

        // Stop timer
        stopTimer()

        // Disable Focus mode
        disableFocusMode()

        // Notify Flutter
        onStatusChanged?("stopped", sessionId, duration)

        // Reset
        elapsedTime = 0
        startTime = nil
    }

    func pauseReading() {
        guard isReading, !isPaused else { return }

        isPaused = true

        // Save elapsed time
        if let start = startTime {
            elapsedTime += Date().timeIntervalSince(start)
        }

        // Allow screen to sleep during pause
        UIApplication.shared.isIdleTimerDisabled = false

        // Stop audio
        stopSilentAudio()

        // Notify Flutter
        onStatusChanged?("paused", sessionId, Int(elapsedTime))
    }

    func resumeReading() {
        guard isReading, isPaused else { return }

        isPaused = false
        startTime = Date()

        // Keep screen on
        UIApplication.shared.isIdleTimerDisabled = true

        // Restart audio
        startSilentAudio()

        // Notify Flutter
        onStatusChanged?("resumed", sessionId, Int(elapsedTime))
    }

    var isReadingActive: Bool {
        return isReading
    }

    // MARK: - Audio Session

    private func setupAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playback, mode: .default, options: [.mixWithOthers])
            try audioSession.setActive(true)
        } catch {
            print("Failed to setup audio session: \(error)")
        }
    }

    private func startSilentAudio() {
        // Create silent audio for background execution
        guard let url = Bundle.main.url(forResource: "silence", withExtension: "mp3") else {
            // If no silence file, create empty audio data
            createSilentAudioPlayer()
            return
        }

        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.numberOfLoops = -1 // Loop indefinitely
            audioPlayer?.volume = 0.01 // Nearly silent
            audioPlayer?.play()
        } catch {
            print("Failed to play silent audio: \(error)")
            createSilentAudioPlayer()
        }
    }

    private func createSilentAudioPlayer() {
        // Generate silent audio data programmatically
        let sampleRate = 44100.0
        let duration = 1.0 // 1 second of silence
        let samples = Int(sampleRate * duration)

        var audioData = Data()
        for _ in 0..<samples {
            var sample: Int16 = 0
            audioData.append(Data(bytes: &sample, count: 2))
        }

        // This is a simplified approach; in production, use a proper silence.mp3 file
    }

    private func stopSilentAudio() {
        audioPlayer?.stop()
        audioPlayer = nil
    }

    // MARK: - Timer

    private func startTimer() {
        timer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            self?.sendPeriodicUpdate()
        }
    }

    private func stopTimer() {
        timer?.invalidate()
        timer = nil
    }

    private func sendPeriodicUpdate() {
        guard isReading, !isPaused, let start = startTime else { return }

        let currentElapsed = elapsedTime + Date().timeIntervalSince(start)

        // Send heartbeat to Flutter
        onStatusChanged?("heartbeat", sessionId, Int(currentElapsed))
    }

    // MARK: - Focus Mode (iOS 15+)

    private func enableFocusMode() {
        // iOS Focus mode is controlled by the user, but we can suggest it
        // through local notification
        sendFocusModeReminder()
    }

    private func disableFocusMode() {
        // Cannot programmatically disable Focus mode
    }

    private func sendFocusModeReminder() {
        let content = UNMutableNotificationContent()
        content.title = "독서 모드 활성화됨"
        content.body = "\(bookTitle) 독서 중입니다. 집중 모드를 켜보세요!"
        content.sound = nil

        let request = UNNotificationRequest(
            identifier: "reading_mode_reminder",
            content: content,
            trigger: nil // Immediate
        )

        UNUserNotificationCenter.current().add(request)
    }

    // MARK: - Notifications

    private func setupNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }

        // Listen for app state changes
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidEnterBackground),
            name: UIApplication.didEnterBackgroundNotification,
            object: nil
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appWillEnterForeground),
            name: UIApplication.willEnterForegroundNotification,
            object: nil
        )
    }

    @objc private func appDidEnterBackground() {
        guard isReading else { return }

        // Send local notification to remind user to return
        let content = UNMutableNotificationContent()
        content.title = "독서 세션 진행 중"
        content.body = "앱으로 돌아와서 독서를 계속하세요"
        content.sound = .default

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 30, repeats: false)
        let request = UNNotificationRequest(
            identifier: "reading_reminder",
            content: content,
            trigger: trigger
        )

        UNUserNotificationCenter.current().add(request)
    }

    @objc private func appWillEnterForeground() {
        // Remove reminder notification
        UNUserNotificationCenter.current().removePendingNotificationRequests(
            withIdentifiers: ["reading_reminder"]
        )
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
