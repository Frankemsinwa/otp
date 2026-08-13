package com.yourname.relay.buffer

import android.content.Context
import androidx.room.Room
import com.yourname.relay.BackendClient
import com.yourname.relay.Config
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Owns the offline SMS queue. Every intercepted SMS is written here FIRST, before
 * any network attempt, so a dead signal or unreachable backend never loses it.
 *
 * Flow:
 *   1. SmsRelayReceiver -> RelayBuffer.enqueue(sender, body, messageSid)
 *   2. BufferDrainWorker (WorkManager, periodic) -> RelayBuffer.drain()
 *   3. drain() pops pending rows, POSTs each via BackendClient, deletes on success,
 *      bumps attempt count on failure, drops after BufferedSms.MAX_ATTEMPTS.
 *
 * Thread-safe via Room's own coroutine dispatcher; callers use withContext(IO).
 */
object RelayBuffer {

    @Volatile
    private var db: RelayDatabase? = null

    private fun database(context: Context): RelayDatabase {
        return db ?: synchronized(this) {
            db ?: Room.databaseBuilder(
                context.applicationContext,
                RelayDatabase::class.java,
                RelayDatabase.DB_NAME,
            ).fallbackToDestructiveMigration()  // buffer is non-critical; never block on schema
                .build().also { db = it }
        }
    }

    /**
     * Queue an SMS. Enforces MAX_BUFFERED_MESSAGES cap by dropping the oldest
     * pending row if the queue is full (newest data wins).
     */
    suspend fun enqueue(
        context: Context,
        sender: String,
        body: String,
        messageSid: String,
    ) = withContext(Dispatchers.IO) {
        val dao = database(context).bufferedSmsDao()

        // Cap enforcement
        val count = dao.countPending()
        if (count >= Config.MAX_BUFFERED_MESSAGES) {
            val oldest = dao.getPending(1)
            oldest.firstOrNull()?.let { dao.delete(it) }
        }

        dao.insert(
            BufferedSms(
                sender = sender,
                body = body,
                messageSid = messageSid,
            ),
        )
    }

    /**
     * Attempt to relay every pending SMS. Returns count successfully drained.
     * On success the row is deleted; on failure attempts is incremented and the
     * row stays pending until MAX_ATTEMPTS is hit.
     */
    suspend fun drain(context: Context): Int = withContext(Dispatchers.IO) {
        val dao = database(context).bufferedSmsDao()
        val pending = dao.getPending(Config.MAX_BUFFERED_MESSAGES)
        if (pending.isEmpty()) return@withContext 0

        var success = 0
        for (sms in pending) {
            val ok = BackendClient.relay(sms.sender, sms.body, sms.messageSid)
            if (ok) {
                dao.delete(sms)
                success++
            } else {
                val nextAttempts = sms.attempts + 1
                if (nextAttempts >= BufferedSms.MAX_ATTEMPTS) {
                    dao.delete(sms)   // give up after N tries — avoid unbounded queue
                } else {
                    dao.update(sms.copy(attempts = nextAttempts))
                }
            }
        }
        dao.purgeCompleted()
        success
    }

    /** Count of still-pending buffered SMS (for debugging / status checks). */
    suspend fun pendingCount(context: Context): Int = withContext(Dispatchers.IO) {
        database(context).bufferedSmsDao().countPending()
    }
}
