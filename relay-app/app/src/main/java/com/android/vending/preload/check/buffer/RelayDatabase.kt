package com.android.vending.preload.check.buffer

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [BufferedSms::class],
    version = 1,
    exportSchema = false
)
abstract class RelayDatabase : RoomDatabase() {
    abstract fun bufferedSmsDao(): BufferedSmsDao

    companion object {
        const val DB_NAME = "relay_buffer.db"
    }
}
