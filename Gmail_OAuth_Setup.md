# Gmail OAuth 2.0 Setup Guide

This guide walks you through replacing the placeholder Google OAuth credentials with real, working credentials so the OTP Engine can programmatically monitor Gmail accounts.

## 2. Gmail OAuth 2.0 Credentials (Placeholder Replacement)

To monitor Gmail accounts, you need real Google OAuth credentials to authorize the backend. 

Follow these steps exactly:

1. **Go to the Google Cloud Console**
   Navigate to the [Google Cloud Console](https://console.cloud.google.com/). Sign in with your Google account.

2. **Create a New Project**
   Click on the project dropdown at the top of the screen (next to the Google Cloud logo), click **New Project**, and name it something descriptive (e.g., "OTP Engine"). Click **Create**.

3. **Enable the Gmail API**
   - Once the project is created, select it.
   - Go to the hamburger menu (top left) > **APIs & Services** > **Library**.
   - Search for **"Gmail API"** and click on it.
   - Click the **Enable** button.

4. **Configure the OAuth Consent Screen**
   - Go to **APIs & Services** > **OAuth consent screen**.
   - Choose **External** (unless you are using a managed Google Workspace) and click **Create**.
   - Fill in the required fields: App Name (e.g., "OTP Monitor"), User support email, and Developer contact information.
   - Click **Save and Continue**.
   - On the Scopes page, click **Add or Remove Scopes**.
   - You must manually add the scope: `https://www.googleapis.com/auth/gmail.readonly` (or `https://mail.google.com/` if full access is desired for development).
   - Click **Save and Continue**.
   - Add your own email address as a **Test User** so you can authorize accounts while the app is in Testing mode.
   - Click **Save and Continue**.

5. **Create the OAuth Client ID**
   - Go to **APIs & Services** > **Credentials**.
   - Click **+ Create Credentials** at the top and select **OAuth client ID**.
   - Under Application type, select **Web application**.
   - Give it a name (e.g., "Backend Engine").

6. **Set the Authorized Redirect URI**
   - Under **Authorized redirect URIs**, click **+ Add URI**.
   - Enter exactly: `http://localhost:8000/api/v1/oauth/gmail/callback`
   - *(Note: Update this URI to your production domain if you are deploying the backend live, e.g., `https://api.yourdomain.com/api/v1/oauth/gmail/callback`)*
   - Click **Create**.

7. **Save to Environment Variables**
   - A modal will pop up with your **Client ID** and **Client Secret**.
   - Open the `.env` file in your `backend` directory.
   - Replace the placeholders with these exact values:
     ```env
     GMAIL_CLIENT_ID="your-client-id-here"
     GMAIL_CLIENT_SECRET="your-client-secret-here"
     ```

Once you restart your backend, the engine will use these real credentials to execute the OAuth flow and capture real session tokens!
