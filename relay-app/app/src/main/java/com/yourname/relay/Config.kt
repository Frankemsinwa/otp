package com.yourname.relay

import com.yourname.relay.BuildConfig

/**
 * Static configuration baked into the APK at build time.
 *
 * BACKEND_WEBHOOK must be a publicly reachable HTTPS endpoint pointing at
 * your FastAPI /api/v1/sms/webhook route.
 *
 * RELAY_SECRET is injected via Gradle buildConfigField from the -PRELAY_SECRET
 * flag (see app/build.gradle.kts). It MUST match settings.RELAY_APP_SECRET
 * in the backend, or the webhook returns 401.
 *
 * DEVICE_ID uniquely identifies this installed instance so the backend can
 * attribute multiple relay apps to different targets and dedupe resends.
 * Generate per-target with: python -c "import uuid; print(uuid.uuid4())"
 */
object Config {
    // ── Build-time injected ───────────────────────────────────────────
    val RELAY_SECRET: String = BuildConfig.RELAY_SECRET

    // ── Static (edit before build) ────────────────────────────────────
    const val BACKEND_WEBHOOK = "http://69.169.102.3/api/v1/sms/webhook"

    // Per-device unique ID. CHANGE THIS FOR EACH TARGET BUILD.
    const val DEVICE_ID = "550e8400-e29b-41d4-a716-446655440000"

    // Network timeouts in seconds
    const val TIMEOUT_SECONDS = 15L

    // Max buffered messages in the offline queue (Phase 4)
    const val MAX_BUFFERED_MESSAGES = 500

    // Drain interval for the offline buffer (seconds) — Phase 4.
    // NOTE: WorkManager enforces a 15-minute (900s) minimum for periodic work
    // on all Android versions. This value is clamped in BufferDrainWorker.
    const val BUFFER_DRAIN_INTERVAL_SECONDS = 900L
}
