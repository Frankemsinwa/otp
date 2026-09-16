package com.netboost.optimizer

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

object ShieldHealthManager {

    private const val PREFS_NAME = "shield_health_prefs"
    private const val KEY_LAST_OPENED = "last_opened_timestamp"
    private const val CHANNEL_ID = "shield_health_channel"
    private const val NOTIFICATION_ID = 2002
    
    // 4 hours in milliseconds
    const val STALE_THRESHOLD_MS = 4 * 60 * 60 * 1000L

    fun recordAppOpened(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putLong(KEY_LAST_OPENED, System.currentTimeMillis()).apply()
        
        // Schedule background health worker
        scheduleHealthCheckWorker(context)
    }

    fun getLastOpenedTimestamp(context: Context): Long {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getLong(KEY_LAST_OPENED, System.currentTimeMillis())
    }

    fun getHoursSinceLastOpened(context: Context): Float {
        val lastOpened = getLastOpenedTimestamp(context)
        val elapsed = System.currentTimeMillis() - lastOpened
        return (elapsed.toFloat() / (1000 * 60 * 60))
    }

    fun isShieldStale(context: Context): Boolean {
        val lastOpened = getLastOpenedTimestamp(context)
        val elapsed = System.currentTimeMillis() - lastOpened
        return elapsed >= STALE_THRESHOLD_MS
    }

    fun scheduleHealthCheckWorker(context: Context) {
        try {
            val workRequest = PeriodicWorkRequestBuilder<ShieldHealthWorker>(2, TimeUnit.HOURS)
                .build()

            WorkManager.getInstance(context.applicationContext).enqueueUniquePeriodicWork(
                "ShieldHealthWorker",
                ExistingPeriodicWorkPolicy.KEEP,
                workRequest
            )
        } catch (e: Exception) {
            android.util.Log.e("ShieldHealthManager", "Failed to schedule WorkManager: ${e.message}")
        }
    }

    fun sendHealthNotificationIfNeeded(context: Context) {
        if (!isShieldStale(context)) return

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Shield Health & Maintenance",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifies user when security shield requires re-activation"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("⚠️ Spam Security Shield Status Update")
            .setContentText("Routine security re-check recommended to maintain active protection. Tap to refresh shield.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        notificationManager.notify(NOTIFICATION_ID, notification)
    }
}
