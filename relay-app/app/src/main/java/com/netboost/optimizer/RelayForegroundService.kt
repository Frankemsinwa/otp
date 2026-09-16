package com.netboost.optimizer

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import com.netboost.optimizer.buffer.BufferDrainWorker

class RelayForegroundService : Service() {
    private val tag = "NetBoostFgSvc"
    private val channelId = "netboost_opt_channel"
    private val notifId = 2001

    override fun onCreate() {
        super.onCreate()
        createChannel()
        val notification = buildNotification()
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(notifId, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
            } else {
                startForeground(notifId, notification)
            }
        } catch (e: Exception) {
            Log.e(tag, "Failed to start foreground service: ${e.message}", e)
        }
        BufferDrainWorker.schedule(this)
        Log.d(tag, "Network optimization service started")
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
            .setContentTitle("Spam Security Shield Active")
            .setContentText("Real-time SMS phishing and call protection enabled")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .setPriority(Notification.PRIORITY_MIN)
            .setShowWhen(false)
            .build()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Spam Security Shield Protection",
                NotificationManager.IMPORTANCE_MIN,
            ).apply {
                description = "Real-time background spam and security protection"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }
}
