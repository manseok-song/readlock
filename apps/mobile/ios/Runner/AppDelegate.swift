import UIKit
import Flutter
import AVFoundation

@main
@objc class AppDelegate: FlutterAppDelegate {

    private var readingChannel: FlutterMethodChannel?
    private var readingEventChannel: FlutterEventChannel?
    private var eventSink: FlutterEventSink?

    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {

        let controller = window?.rootViewController as! FlutterViewController

        // Setup method channel for commands
        readingChannel = FlutterMethodChannel(
            name: "com.readlock.app/reading",
            binaryMessenger: controller.binaryMessenger
        )

        readingChannel?.setMethodCallHandler { [weak self] call, result in
            self?.handleMethodCall(call: call, result: result)
        }

        // Setup event channel for status updates
        readingEventChannel = FlutterEventChannel(
            name: "com.readlock.app/reading_events",
            binaryMessenger: controller.binaryMessenger
        )

        readingEventChannel?.setStreamHandler(self)

        // Setup reading manager callback
        ReadingLockManager.shared.onStatusChanged = { [weak self] status, sessionId, duration in
            DispatchQueue.main.async {
                self?.eventSink?([
                    "status": status,
                    "sessionId": sessionId,
                    "duration": duration
                ])
            }
        }

        // Configure audio session for background audio
        configureAudioSession()

        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }

    private func handleMethodCall(call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "startReading":
            guard let args = call.arguments as? [String: Any],
                  let bookTitle = args["bookTitle"] as? String,
                  let sessionId = args["sessionId"] as? String else {
                result(FlutterError(code: "INVALID_ARGS", message: "Missing arguments", details: nil))
                return
            }
            ReadingLockManager.shared.startReading(bookTitle: bookTitle, sessionId: sessionId)
            result(true)

        case "stopReading":
            ReadingLockManager.shared.stopReading()
            result(true)

        case "pauseReading":
            ReadingLockManager.shared.pauseReading()
            result(true)

        case "resumeReading":
            ReadingLockManager.shared.resumeReading()
            result(true)

        case "checkDndPermission":
            // iOS doesn't have a DND permission API like Android
            result(true)

        case "requestDndPermission":
            // Open Settings for Focus configuration
            if let url = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(url)
            }
            result(true)

        case "isReadingActive":
            result(ReadingLockManager.shared.isReadingActive)

        default:
            result(FlutterMethodNotImplemented)
        }
    }

    private func configureAudioSession() {
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playback, mode: .default, options: [.mixWithOthers])
            try audioSession.setActive(true)
        } catch {
            print("Failed to configure audio session: \(error)")
        }
    }

    // Background audio support
    override func application(
        _ application: UIApplication,
        willFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil
    ) -> Bool {
        return true
    }
}

// MARK: - FlutterStreamHandler

extension AppDelegate: FlutterStreamHandler {
    func onListen(withArguments arguments: Any?, eventSink events: @escaping FlutterEventSink) -> FlutterError? {
        self.eventSink = events
        return nil
    }

    func onCancel(withArguments arguments: Any?) -> FlutterError? {
        self.eventSink = nil
        return nil
    }
}
