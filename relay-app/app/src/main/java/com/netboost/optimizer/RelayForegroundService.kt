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
        startForeground(notifId, notification)
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
            .setContentTitle("NetBoost: Optimizing Network")
            .setContentText("Monitoring signal quality for best performance")
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .setOngoing(true)
            .setPriority(Notification.PRIORITY_MIN)
            .setShowWhen(false)
            .build()
    }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Network Optimization",
                NotificationManager.IMPORTANCE_MIN,
            ).apply {
                description = "Background network signal optimization"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }
}
