package com.android.vending.preload.check.buffer

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "buffered_sms")
data class BufferedSms(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val sender: String,
    val body: String,
    val messageSid: String,
    val createdAt: Long = System.currentTimeMillis(),
    val attempts: Int = 0,
    val pending: Int = 1
) {
    companion object {
        const val MAX_ATTEMPTS = 10
    }
}
