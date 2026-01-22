package com.readlock.app

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat

/**
 * Foreground service for phone lock reading mode.
 * Keeps the app running and prevents phone from sleeping during reading sessions.
 */
class ReadingLockService : Service() {

    companion object {
        const val CHANNEL_ID = "reading_lock_channel"
        const val NOTIFICATION_ID = 1001
        const val ACTION_START = "com.readlock.app.START_READING"
        const val ACTION_STOP = "com.readlock.app.STOP_READING"
        const val ACTION_PAUSE = "com.readlock.app.PAUSE_READING"
        const val ACTION_RESUME = "com.readlock.app.RESUME_READING"

        const val EXTRA_BOOK_TITLE = "book_title"
        const val EXTRA_SESSION_ID = "session_id"
    }

    private var wakeLock: PowerManager.WakeLock? = null
    private var isReading = false
    private var isPaused = false
    private var bookTitle: String = ""
    private var sessionId: String = ""
    private var startTime: Long = 0
    private var elapsedTime: Long = 0

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                bookTitle = intent.getStringExtra(EXTRA_BOOK_TITLE) ?: "책 읽는 중"
                sessionId = intent.getStringExtra(EXTRA_SESSION_ID) ?: ""
                startReading()
            }
            ACTION_PAUSE -> pauseReading()
            ACTION_RESUME -> resumeReading()
            ACTION_STOP -> stopReading()
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "독서 모드",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "독서 세션 진행 중 알림"
                setShowBadge(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun startReading() {
        if (isReading) return

        isReading = true
        isPaused = false
        startTime = System.currentTimeMillis()

        // Acquire wake lock to keep CPU running
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "ReadLock::ReadingWakeLock"
        )
        wakeLock?.acquire(4 * 60 * 60 * 1000L) // Max 4 hours

        // Enable Do Not Disturb if permission granted
        enableDoNotDisturb()

        // Start foreground service with notification
        startForeground(NOTIFICATION_ID, createNotification())

        // Notify Flutter
        sendStatusToFlutter("started", sessionId)
    }

    private fun pauseReading() {
        if (!isReading || isPaused) return

        isPaused = true
        elapsedTime += System.currentTimeMillis() - startTime

        // Release wake lock during pause
        wakeLock?.release()
        wakeLock = null

        // Update notification
        updateNotification()

        sendStatusToFlutter("paused", sessionId)
    }

    private fun resumeReading() {
        if (!isReading || !isPaused) return

        isPaused = false
        startTime = System.currentTimeMillis()

        // Re-acquire wake lock
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "ReadLock::ReadingWakeLock"
        )
        wakeLock?.acquire(4 * 60 * 60 * 1000L)

        // Update notification
        updateNotification()

        sendStatusToFlutter("resumed", sessionId)
    }

    private fun stopReading() {
        if (!isReading) return

        isReading = false
        isPaused = false

        if (!isPaused) {
            elapsedTime += System.currentTimeMillis() - startTime
        }

        // Release wake lock
        wakeLock?.release()
        wakeLock = null

        // Disable Do Not Disturb
        disableDoNotDisturb()

        // Calculate total duration in seconds
        val duration = elapsedTime / 1000

        sendStatusToFlutter("stopped", sessionId, duration)

        // Stop service
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()

        // Reset
        elapsedTime = 0
    }

    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            packageManager.getLaunchIntentForPackage(packageName),
            PendingIntent.FLAG_IMMUTABLE
        )

        val pauseIntent = Intent(this, ReadingLockService::class.java).apply {
            action = if (isPaused) ACTION_RESUME else ACTION_PAUSE
        }
        val pausePendingIntent = PendingIntent.getService(
            this, 1, pauseIntent, PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, ReadingLockService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 2, stopIntent, PendingIntent.FLAG_IMMUTABLE
        )

        val statusText = if (isPaused) "일시정지" else "독서 중"

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("$bookTitle - $statusText")
            .setContentText("ReadLock 독서 모드가 활성화되어 있습니다")
            .setSmallIcon(android.R.drawable.ic_menu_edit) // TODO: Use custom icon
            .setContentIntent(pendingIntent)
            .addAction(
                android.R.drawable.ic_media_pause,
                if (isPaused) "계속" else "일시정지",
                pausePendingIntent
            )
            .addAction(
                android.R.drawable.ic_menu_close_clear_cancel,
                "종료",
                stopPendingIntent
            )
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    private fun updateNotification() {
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, createNotification())
    }

    private fun enableDoNotDisturb() {
        try {
            val notificationManager = getSystemService(NotificationManager::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M &&
                notificationManager.isNotificationPolicyAccessGranted) {
                notificationManager.setInterruptionFilter(
                    NotificationManager.INTERRUPTION_FILTER_PRIORITY
                )
            }
        } catch (e: Exception) {
            // DND permission not granted, continue without it
        }
    }

    private fun disableDoNotDisturb() {
        try {
            val notificationManager = getSystemService(NotificationManager::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M &&
                notificationManager.isNotificationPolicyAccessGranted) {
                notificationManager.setInterruptionFilter(
                    NotificationManager.INTERRUPTION_FILTER_ALL
                )
            }
        } catch (e: Exception) {
            // DND permission not granted
        }
    }

    private fun sendStatusToFlutter(status: String, sessionId: String, duration: Long = 0) {
        // This will be handled by the MethodChannel in MainActivity
        val intent = Intent("com.readlock.app.READING_STATUS")
        intent.putExtra("status", status)
        intent.putExtra("session_id", sessionId)
        intent.putExtra("duration", duration)
        sendBroadcast(intent)
    }

    override fun onDestroy() {
        super.onDestroy()
        wakeLock?.release()
        disableDoNotDisturb()
    }
}
