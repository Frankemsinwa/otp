# Railway Deployment Guide — OTP Backend

## Prerequisites

- GitHub account (repo pushed)
- Railway account (sign up at railway.app — free tier gives $5/month credit)
- A terminal with `railway` CLI optional but helpful

---

## Step 1: Create a Railway Project

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `otp` repository
6. Railway will detect the `backend/Dockerfile` and create a service

> **If Railway doesn't auto-detect:** After creating the project, click **"+ New"** → **"Service"** → **"GitHub Repo"** → select your repo, then set the **Root Directory** to `backend/` in the service settings.

---

## Step 2: Add PostgreSQL

1. In your Railway project dashboard, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway creates a Postgres instance and **automatically sets `DATABASE_URL`** as an environment variable on all services in the project
3. Verify: go to your backend service → **"Variables"** tab → you should see `DATABASE_URL` already populated (format: `postgresql://postgres:xxx@xxx.railway.internal:5432/railway`)

---

## Step 3: Add Redis

1. Same dashboard, click **"+ New"** → **"Database"** → **"Redis"**
2. Railway creates a Redis instance and **automatically sets `REDIS_URL`** as an environment variable
3. Verify: go to your backend service → **"Variables"** tab → you should see `REDIS_URL` already populated (format: `redis://default:xxx@xxx.railway.internal:6379`)

---

## Step 4: Set Environment Variables

Go to your backend service → **"Variables"** tab → add these **manually**:

### Required (generate these yourself)

| Variable | How to generate | Example |
|---|---|---|
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | `aBcDeFgHiJkLmNoPqRsTuVwXyZ01234567890=` |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` | `a1b2c3d4e5f6...` (64 hex chars) |
| `RELAY_APP_SECRET` | `python -c "import secrets; print(secrets.token_hex(16))"` | `070c7d6a29debce56db11d474ff1b4db` |

> **CRITICAL:** Save `RELAY_APP_SECRET` — you'll bake the same value into the APK.

### Required (your existing credentials)

| Variable | Value |
|---|---|
| `GMAIL_CLIENT_ID` | Your Google OAuth client ID |
| `GMAIL_CLIENT_SECRET` | Your Google OAuth client secret |
| `GMAIL_REDIRECT_URI` | `https://YOUR-RAILWAY-URL/api/v1/oauth/gmail/callback` |
| `CORS_ORIGINS` | `'["https://YOUR-VERCEL-URL.vercel.app"]'` |

### Auto-set by Railway (don't override)

| Variable | Set by |
|---|---|
| `DATABASE_URL` | PostgreSQL plugin |
| `REDIS_URL` | Redis plugin |
| `PORT` | Railway (defaults to 8000, Railway overrides) |

### Optional (leave empty unless using)

| Variable | Notes |
|---|---|
| `TWILIO_*` | Only needed for Path 1 (virtual number) |
| `YAHOO_*` | Only if monitoring Yahoo targets |
| `PROXY_LIST` | `'[]'` for no proxies |

---

## Step 5: Deploy

1. After setting variables, Railway **auto-deploys** on every push to your connected branch
2. Watch the deploy logs in the **"Deployments"** tab — you should see:
   ```
   ▶ Running database migrations...
   ▶ Starting uvicorn on 0.0.0.0:PORT...
   INFO:     Uvicorn running on http://0.0.0.0:PORT
   ```
3. Once deployed, Railway gives you a **public URL** like:
   ```
   https://otp-backend-production.up.railway.app
   ```

### Verify it works

```bash
# Root endpoint
curl https://YOUR-RAILWAY-URL/

# Should return:
# {"message":"OTP Harvesting & Monitoring Engine Active"}

# Targets endpoint
curl https://YOUR-RAILWAY-URL/api/v1/targets/

# Should return: []
```

---

## Step 6: Update the APK Config

Once you have your Railway URL, update `relay-app/app/src/main/java/com/yourname/relay/Config.kt`:

```kotlin
const val BACKEND_WEBHOOK = "https://YOUR-RAILWAY-URL.up.railway.app/api/v1/sms/webhook"
```

Then build the APK with the same relay secret:

```bash
cd relay-app
./gradlew assembleRelease -PRELAY_SECRET=070c7d6a29debce56db11d474ff1b4db
```

> Replace `070c7d6a29debce56db11d474ff1b4db` with your actual `RELAY_APP_SECRET`.

---

## Step 7: Update Gmail OAuth Redirect URI

In your [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Go to your OAuth 2.0 Client ID
2. Add to **Authorized redirect URIs**:
   ```
   https://YOUR-RAILWAY-URL.up.railway.app/api/v1/oauth/gmail/callback
   ```
3. Remove the old `http://localhost:8000/...` URI (no longer needed for production)

---

## Cost Estimate

| Service | Plan | Cost |
|---|---|---|
| Backend (Railway) | Starter | $5/mo (or free with $5 trial credit) |
| PostgreSQL (Railway) | Starter | $1-5/mo usage-based |
| Redis (Railway) | Starter | $1-5/mo usage-based |
| Frontend (Vercel) | Hobby | $0 |
| **Total** | | **~$5-15/mo** |

> The $5 trial credit covers ~1 month of light usage. After that, hobby plan is $5/mo + usage.

---

## Troubleshooting

### "Application startup failed" in deploy logs
- Check that `DATABASE_URL` and `REDIS_URL` are set (should be automatic from plugins)
- Check `ENCRYPTION_KEY` is a valid Fernet key (starts with letters/numbers, ends with `=`)

### "RELAY_APP_SECRET not configured" warning
- Add `RELAY_APP_SECRET` to your Railway environment variables

### Migrations fail
- Railway's Postgres may need a moment after creation. Redeploy after 30 seconds.
- Check that `DATABASE_URL` starts with `postgresql://` (Railway default)

### APK gets 401 Unauthorized
- `RELAY_APP_SECRET` in Railway must **exactly match** the `-PRELAY_SECRET` used when building the APK
- No trailing spaces, no quotes around the value in Railway

### CORS errors from frontend
- Set `CORS_ORIGINS` to include your Vercel URL: `'["https://your-app.vercel.app"]'`

---

## Redeployment

Railway auto-deploys on git push. To force a manual redeploy:

1. Go to your backend service → **"Deployments"** tab
2. Click **"Redeploy"** on the latest deployment

Or via CLI:
```bash
railway login
railway link
railway up
```
