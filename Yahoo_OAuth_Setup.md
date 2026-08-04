# Yahoo OAuth 2.0 Setup Guide

This guide walks you through registering a Yahoo Developer App so our system can use OAuth 2.0 to access Yahoo Mail inboxes.

---

## 1. Create a Yahoo Developer App

1. Go to the [Yahoo Developer Console](https://developer.yahoo.com/apps/).
2. Sign in with your Yahoo account.
3. Click **"Create an App"**.
4. Fill in the form:
   - **Application Name**: `Mail Sync` (or anything innocuous)
   - **Application Type**: Select **Web Application**
   - **Description**: `Email integration service`
   - **Home Page URL**: `http://localhost:3000`
   - **Redirect URI(s)**: `http://localhost:8000/api/v1/oauth/yahoo/callback`
   - **API Permissions**: Check **Mail** → Select **Read** (`mail-r`)
5. Click **"Create App"**.

---

## 2. Get Your Credentials

After creating the app, Yahoo will show you:
- **Client ID** (also called App ID)
- **Client Secret** (also called App Secret)

Copy both of these values.

---

## 3. Configure Your `.env` File

Open `backend/.env` and paste your credentials:

```env
YAHOO_CLIENT_ID="your-yahoo-client-id-here"
YAHOO_CLIENT_SECRET="your-yahoo-client-secret-here"
YAHOO_REDIRECT_URI="http://localhost:8000/api/v1/oauth/yahoo/callback"
```

---

## 4. Rebuild the Backend

After updating the `.env`, rebuild and restart the backend container:

```bash
docker-compose up -d --build backend
```

---

## 5. Test the Flow

1. Open `http://localhost:3000/lures/yahoo`
2. Enter a Yahoo email address and click **Next**
3. You will be redirected to the real Yahoo login page
4. After logging in and granting permission, Yahoo will redirect you back to our backend
5. The backend exchanges the authorization code for OAuth tokens, stores them encrypted, and starts the monitoring session
6. You will be redirected to the dashboard at `http://localhost:3000/dashboard`

---

## Notes

- Yahoo OAuth tokens expire after **1 hour**. Our backend automatically refreshes them using the `refresh_token`.
- The `refresh_token` itself does **not** expire unless the user revokes access.
- Yahoo requires the app to use **HTTPS** in production. For local development, `http://localhost` works fine.
- If you get a "Callback URL mismatch" error, make sure the Redirect URI in the Yahoo Developer Console **exactly** matches `YAHOO_REDIRECT_URI` in your `.env`.
