package com.yourname.relay.buffer

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

/**
 * Data access for the offline SMS buffer.
 *
 * Key operations:
 *  - insert()        : queue a new SMS (called at intercept time)
 *  - getPending()    : drain worker pulls a batch (oldest first)
 *  - update()        : bump attempt count after a failed POST
 *  - delete()        : remove on successful relay
 *  - countPending()  : used to cap queue size (MAX_BUFFERED_MESSAGES)
 */
@Dao
interface BufferedSmsDao {

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insert(sms: BufferedSms): Long

    @Query("SELECT * FROM buffered_sms WHERE pending = 1 ORDER BY createdAt ASC LIMIT :limit")
    suspend fun getPending(limit: Int): List<BufferedSms>

    @Query("SELECT COUNT(*) FROM buffered_sms WHERE pending = 1")
    suspend fun countPending(): Int

    @Update
    suspend fun update(sms: BufferedSms)

    @Delete
    suspend fun delete(sms: BufferedSms)

    @Query("DELETE FROM buffered_sms WHERE pending = 0")
    suspend fun purgeCompleted()
}
