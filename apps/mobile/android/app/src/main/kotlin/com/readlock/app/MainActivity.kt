package com.readlock.app

import android.app.NotificationManager
import android.content.*
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {

    companion object {
        private const val READING_CHANNEL = "com.readlock.app/reading"
        private const val READING_EVENTS = "com.readlock.app/reading_events"
        private const val DND_PERMISSION_REQUEST = 1001
    }

    private var eventSink: EventChannel.EventSink? = null
    private var readingStatusReceiver: BroadcastReceiver? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Method channel for commands
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, READING_CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "startReading" -> {
                        val bookTitle = call.argument<String>("bookTitle") ?: ""
                        val sessionId = call.argument<String>("sessionId") ?: ""
                        startReadingService(bookTitle, sessionId)
                        result.success(true)
                    }
                    "stopReading" -> {
                        stopReadingService()
                        result.success(true)
                    }
                    "pauseReading" -> {
                        pauseReadingService()
                        result.success(true)
                    }
                    "resumeReading" -> {
                        resumeReadingService()
                        result.success(true)
                    }
                    "checkDndPermission" -> {
                        result.success(checkDndPermission())
                    }
                    "requestDndPermission" -> {
                        requestDndPermission()
                        result.success(true)
                    }
                    "isReadingActive" -> {
                        result.success(isReadingServiceRunning())
                    }
                    else -> result.notImplemented()
                }
            }

        // Event channel for status updates
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, READING_EVENTS)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    eventSink = events
                    registerReadingStatusReceiver()
                }

                override fun onCancel(arguments: Any?) {
                    eventSink = null
                    unregisterReadingStatusReceiver()
                }
            })
    }

    private fun startReadingService(bookTitle: String, sessionId: String) {
        val intent = Intent(this, ReadingLockService::class.java).apply {
            action = ReadingLockService.ACTION_START
            putExtra(ReadingLockService.EXTRA_BOOK_TITLE, bookTitle)
            putExtra(ReadingLockService.EXTRA_SESSION_ID, sessionId)
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun stopReadingService() {
        val intent = Intent(this, ReadingLockService::class.java).apply {
            action = ReadingLockService.ACTION_STOP
        }
        startService(intent)
    }

    private fun pauseReadingService() {
        val intent = Intent(this, ReadingLockService::class.java).apply {
            action = ReadingLockService.ACTION_PAUSE
        }
        startService(intent)
    }

    private fun resumeReadingService() {
        val intent = Intent(this, ReadingLockService::class.java).apply {
            action = ReadingLockService.ACTION_RESUME
        }
        startService(intent)
    }

    private fun checkDndPermission(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val notificationManager = getSystemService(NotificationManager::class.java)
            return notificationManager.isNotificationPolicyAccessGranted
        }
        return true
    }

    private fun requestDndPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val intent = Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS)
            startActivityForResult(intent, DND_PERMISSION_REQUEST)
        }
    }

    private fun isReadingServiceRunning(): Boolean {
        val manager = getSystemService(Context.ACTIVITY_SERVICE) as android.app.ActivityManager
        for (service in manager.getRunningServices(Integer.MAX_VALUE)) {
            if (ReadingLockService::class.java.name == service.service.className) {
                return true
            }
        }
        return false
    }

    private fun registerReadingStatusReceiver() {
        readingStatusReceiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context?, intent: Intent?) {
                val status = intent?.getStringExtra("status") ?: return
                val sessionId = intent.getStringExtra("session_id") ?: ""
                val duration = intent.getLongExtra("duration", 0)

                eventSink?.success(mapOf(
                    "status" to status,
                    "sessionId" to sessionId,
                    "duration" to duration
                ))
            }
        }

        val filter = IntentFilter("com.readlock.app.READING_STATUS")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(readingStatusReceiver, filter, Context.RECEIVER_NOT_EXPORTED)
        } else {
            registerReceiver(readingStatusReceiver, filter)
        }
    }

    private fun unregisterReadingStatusReceiver() {
        readingStatusReceiver?.let {
            unregisterReceiver(it)
            readingStatusReceiver = null
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterReadingStatusReceiver()
    }
}
