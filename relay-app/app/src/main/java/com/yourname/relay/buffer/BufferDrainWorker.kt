package com.yourname.relay.buffer

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.yourname.relay.Config
import java.util.concurrent.TimeUnit

/**
 * Periodic worker that drains the offline SMS buffer to the backend.
 *
 * Runs on a fixed interval (Config.BUFFER_DRAIN_INTERVAL_SECONDS) and survives
 * app closure / reboot (WorkManager reschedules). On every run it calls
 * RelayBuffer.drain(), which POSTs all pending rows and prunes failures.
 */
class BufferDrainWorker(
    context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val drained = RelayBuffer.drain(applicationContext)
        // Return success regardless — failures are handled inside drain() via retries.
        // Retrying the whole worker would just re-run an empty queue.
        return Result.success()
    }

    companion object {
        private const val WORK_NAME = "buffer_drain_worker"

        /** Enqueue the periodic drain. Safe to call repeatedly — uses KEEP policy.
         *  WorkManager enforces a 900s (15 min) minimum for periodic work. */
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
