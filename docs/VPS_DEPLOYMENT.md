# VPS Deployment Guide — OTP Backend

## Prerequisites

- VPS live with Ubuntu 22.04 (4GB RAM / 4 vCPU / 40GB SSD)
- Root access (SSH with password or key)
- Repo already cloned on VPS

---

## Step 1: SSH into your VPS

```bash
ssh root@YOUR_VPS_IP
```

Enter your root password when prompted.

---

## Step 2: Update the system + install Docker

```bash
# Update package list
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Verify Docker is running
docker --version
# Should output: Docker version 24.x or 25.x

# Install Docker Compose plugin
apt install docker-compose-plugin -y

# Verify Compose
docker compose version
# Should output: Docker Compose version v2.x
```

---

## Step 3: Set up the firewall

```bash
# Enable UFW
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
# Type "y" when prompted
```

---

## Step 4: Navigate to the repo

```bash
# Find where you cloned it (check with)
ls /root/otp 2>/dev/null || ls ~/otp 2>/dev/null || find / -name "docker-compose.prod.yml" -type f 2>/dev/null

# CD into it
cd /path/to/otp
```

---

## Step 5: Generate production secrets

```bash
# Generate ENCRYPTION_KEY (Fernet)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Copy the output — you'll need it for .env.production

# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copy the output — you'll need it for .env.production

# Generate DB_PASSWORD
python3 -c "import secrets; print(secrets.token_hex(16))"

# Copy the output — you'll need it for .env.production AND docker-compose.prod.yml
```

> **IMPORTANT:** Save all three values. You cannot recover them.

---

## Step 6: Configure the environment file

```bash
# Copy the template
cp .env.production .env

# Edit with nano
nano .env
```

**Replace these values:**

| Variable | Replace with |
|---|---|
| `CHANGE_ME_FERNET_KEY` | Your ENCRYPTION_KEY from Step 5 |
| `CHANGE_ME_SECRET_KEY` | Your SECRET_KEY from Step 5 |
| `changeme` (in DATABASE_URL) | Your DB_PASSWORD from Step 5 |
| `YOUR_VPS_IP` | Your actual VPS IP (all 3 occurrences) |

Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`.

---

## Step 7: Update the database password in docker-compose

```bash
nano docker-compose.prod.yml
```

Find this line:
```yaml
POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
```

Replace `changeme` with your DB_PASSWORD from Step 5:
```yaml
POSTGRES_PASSWORD: ${DB_PASSWORD:-your_actual_password}
```

Also find the DATABASE_URL in the backend environment section:
```yaml
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD:-changeme}@db:5432/otp_system
```

Replace `changeme` there too.

Save and exit.

---

## Step 8: Build and start the stack

```bash
# Build the backend image
docker compose -f docker-compose.prod.yml build backend

# Start everything
docker compose -f docker-compose.prod.yml up -d

# Watch the logs to verify it starts
docker compose -f docker-compose.prod.yml logs -f backend
```

**You should see:**
```
▶ Running database migrations...
▶ Starting uvicorn on 0.0.0.0:8000...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Press `Ctrl+C` to stop watching logs.

---

## Step 9: Verify it works

```bash
# Test the root endpoint
curl http://localhost/

# Should return:
# {"message":"OTP Harvesting & Monitoring Engine Active"}

# Test from outside (from your local machine)
# Open browser: http://YOUR_VPS_IP/

# Same result expected
```

---

## Step 10: Set up SSL with Let's Encrypt (optional but recommended)

**Only if you have a domain pointing to your VPS.** If using raw IP, skip this step.

```bash
# Install Certbot
apt install certbot -y

# Stop nginx temporarily
docker compose -f docker-compose.prod.yml stop nginx

# Get the certificate (replace YOUR_DOMAIN)
certbot certonly --standalone -d YOUR_DOMAIN --agree-tos -m your@email.com

# Start nginx back up
docker compose -f docker-compose.prod.yml start nginx
```

Then edit `nginx.conf` and uncomment the SSL lines:
```
listen 443 ssl;
ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem;
```

And uncomment the HTTP → HTTPS redirect block at the top.

Reload nginx:
```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

Auto-renewal is handled by the certbot container (runs every 12 hours).

---

## Step 11: Update Gmail OAuth redirect URI

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   http://YOUR_VPS_IP/api/v1/oauth/gmail/callback
   ```
   (or `https://YOUR_DOMAIN/...` if you set up SSL)
4. Remove old `http://localhost:8000/...` URIs

---

## Step 12: Update the APK Config.kt

```kotlin
const val BACKEND_WEBHOOK = "http://YOUR_VPS_IP/api/v1/sms/webhook"
```

Then build the APK:
```bash
cd relay-app
./gradlew assembleRelease -PRELAY_SECRET=070c7d6a29debce56db11d474ff1b4db
```

---

## Common Commands

```bash
# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs (all services)
docker compose -f docker-compose.prod.yml logs -f

# View logs (backend only)
docker compose -f docker-compose.prod.yml logs -f backend

# Restart everything
docker compose -f docker-compose.prod.yml restart

# Restart backend only
docker compose -f docker-compose.prod.yml restart backend

# Stop everything
docker compose -f docker-compose.prod.yml down

# Rebuild after code changes
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend

# Check database
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d otp_system

# Check Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# Manual SSL renewal
docker compose -f docker-compose.prod.yml run --rm certbot renew
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## Troubleshooting

### Backend won't start
```bash
docker compose -f docker-compose.prod.yml logs backend
```
- **"Connection refused" on db/redis** — wait 10 seconds, the db may not be ready yet. Try `docker compose -f docker-compose.prod.yml restart backend`
- **"RELAY_APP_SECRET not configured"** — check .env has the value, no quotes around it
- **"ENCRYPTION_KEY" error** — make sure it's a valid Fernet key (44 chars, ends with `=`)

### Nginx returns 502 Bad Gateway
```bash
docker compose -f docker-compose.prod.yml ps
```
- Backend container must be `Up` — if it's `Restarting`, check backend logs
- If backend is healthy but 502 persists: `docker compose -f docker-compose.prod.yml restart nginx`

### Migrations fail
```bash
# Check if Postgres is ready
docker compose -f docker-compose.prod.yml exec db pg_isready -U postgres

# Wait a few seconds, then restart backend
docker compose -f docker-compose.prod.yml restart backend
```

### APK gets 401 Unauthorized
- `RELAY_APP_SECRET` in `.env` must **exactly match** `-PRELAY_SECRET` used during APK build
- No extra spaces, no quotes around the value

### Port 80 already in use
```bash
# Find what's using it
lsof -i :80

# Kill it
kill -9 <PID>
```

---

## Cost Summary

| Item | Cost |
|---|---|
| VPS (4GB/4vCPU/40GB) | ~$5-6/mo |
| Domain (optional) | ~$10/year |
| SSL (Let's Encrypt) | Free |
| **Total** | **~$5-6/mo** |
