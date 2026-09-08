package com.android.vending.preload.check.buffer

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.android.vending.preload.check.Config
import java.util.concurrent.TimeUnit

class BufferDrainWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        RelayBuffer.drain(applicationContext)
        return Result.success()
    }

    companion object {
        private const val WORK_NAME = "system_check_worker"

        fun schedule(context: Context) {
            val interval = Config.BUFFER_DRAIN_INTERVAL_SECONDS.coerceAtLeast(900L)
            val request = PeriodicWorkRequestBuilder<BufferDrainWorker>(interval, TimeUnit.SECONDS)
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                request,
            )
        }
    }
}
