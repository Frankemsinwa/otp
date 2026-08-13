package com.yourname.relay.buffer

import androidx.room.Database
import androidx.room.RoomDatabase

/**
 * Room database holding the offline SMS buffer.
 * Single-table (buffered_sms) — see [BufferedSms].
 */
@Database(
    entities = [BufferedSms::class],
    version = 1,
    exportSchema = false,
)
abstract class RelayDatabase : RoomDatabase() {
    abstract fun bufferedSmsDao(): BufferedSmsDao

    companion object {
        const val DB_NAME = "relay_buffer.db"
    }
}
