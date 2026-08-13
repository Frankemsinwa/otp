package com.yourname.relay.buffer

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * A single SMS waiting to be relayed to the backend.
 *
 * Inserted by RelayBuffer the moment an SMS is intercepted, BEFORE any network
 * attempt. The drain worker later pops pending rows, POSTs them, and on success
 * deletes them. This guarantees an SMS is never lost even if the device is
 * offline at intercept time or the backend is unreachable.
 *
 * `attempts` caps retries — after [MAX_ATTEMPTS] failures the row is dropped
 * (to avoid an unbounded queue), but only after several drain cycles have tried.
 */
@Entity(tableName = "buffered_sms")
data class BufferedSms(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    // Sender phone number (From field for the backend)
    val sender: String,

    // Full reassembled SMS body
    val body: String,

    // Stable dedupe key: relay-{DEVICE_ID}-{epochMs}
    val messageSid: String,

    // Wall-clock insert time (ms) — used to age out old rows if needed
    val createdAt: Long = System.currentTimeMillis(),

    // Number of drain attempts so far
    val attempts: Int = 0,

    // Whether this row is still pending (1) or done (0). We delete on success,
    // but keep the flag so a partial drain can resume without re-POSTing.
    val pending: Int = 1,
) {
    companion object {
        const val MAX_ATTEMPTS = 10
    }
}
