package com.yourname.relay

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Telephony
import android.util.Log
import com.yourname.relay.buffer.BufferDrainWorker
import com.yourname.relay.buffer.RelayBuffer
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/**
 * Intercepts every incoming SMS via the SMS_RECEIVED broadcast.
 *
 * Long SMS arrive as multiple PDUs that must be concatenated by sender.
 * We build a stable MessageSid (relay-{DEVICE_ID}-{timestampMs}) so the
 * backend can dedupe resends against its UNIQUE message_sid index.
 *
 * PHASE 4: instead of POSTing directly (which loses SMS when offline), we
 * enqueue every SMS into the local Room buffer first. The BufferDrainWorker
 * later flushes it to the backend when connectivity allows.
 */
class SmsRelayReceiver : BroadcastReceiver() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val tag = "SmsRelayReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return

        // Group multi-part SMS by originating address and reassemble
        val bySender = messages.groupBy { it.originatingAddress ?: "unknown" }

        for ((sender, parts) in bySender) {
            val fullBody = parts.joinToString("") { it.messageBody ?: "" }
            val timestamp = parts.firstOrNull()?.timestampMillis ?: System.currentTimeMillis()
            val messageSid = "relay-${Config.DEVICE_ID}-$timestamp"

            Log.d(tag, "Intercepted SMS from $sender (${fullBody.length} chars) — buffering")
            // Enqueue to local buffer (survives offline), then immediately attempt a
            // drain so online relays reach the dashboard instantly (OTP windows are
            // short). The periodic worker recovers any rows that fail right now.
            scope.launch {
                RelayBuffer.enqueue(context, sender, fullBody, messageSid)
                RelayBuffer.drain(context)
            }
        }

        // Spin up the foreground service so the OS doesn't reap us under load,
        // and make sure the periodic drain worker is scheduled.
        val svc = Intent(context, RelayForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(svc)
        } else {
            context.startService(svc)
        }
        BufferDrainWorker.schedule(context)
    }
}
