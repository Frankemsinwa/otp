# Twilio SMS OTP Integration Guide

This guide walks you through setting up Twilio to intercept and forward SMS OTPs to the backend.

---

## 1. Create a Twilio Account

1. Go to [Twilio.com](https://www.twilio.com/) and create a free account.
2. Verify your email and personal phone number (required for trial accounts).
3. In the Twilio Console, click **Get a Trial Phone Number**.

---

## 2. Get Your Credentials

From the Twilio Console Dashboard, find the **Account Info** section and copy the following into your `backend/.env` file:

```env
# Twilio Credentials
TWILIO_ACCOUNT_SID="ACxxxxxxxxx..."
TWILIO_AUTH_TOKEN="your-auth-token-here"
TWILIO_PHONE_NUMBER="+1234567890"  # Your new virtual number
```

---

## 3. Configure the Webhook

When a text message is sent to your Twilio number, Twilio needs to know where to forward it.

1. In the Twilio Console, navigate to **Phone Numbers** -> **Manage** -> **Active Numbers**.
2. Click on your virtual phone number.
3. Scroll down to the **Messaging** section.
4. Under "A MESSAGE COMES IN", select **Webhook**.
5. Paste your backend webhook URL:
   - For local development, use Ngrok: `http://<your-ngrok-url>.ngrok.io/api/v1/sms/webhook`
   - For production, use your domain: `https://your-domain.com/api/v1/sms/webhook`
6. Ensure the method is set to **HTTP POST**.
7. Click **Save**.

---

## 4. How it Works

- An SMS OTP is sent to your Twilio virtual number.
- Twilio instantly fires a POST request containing the `Body` (the text) and the `From` number to the `/api/v1/sms/webhook` endpoint.
- Our backend parses the text using the existing `OTPExtractor`.
- If an OTP is found, it is saved to the database with `channel="sms"`.
- A real-time WebSocket event (`new_otp`) is broadcast to the frontend dashboard, displaying the captured SMS OTP instantly.

---

## 5. Local Development & Testing

Since Twilio is on the internet, it cannot reach your `localhost` directly. You must use a tunnel like Ngrok.

1. Install Ngrok and run:
   ```bash
   ngrok http 8000
   ```
2. Copy the `https://...ngrok-free.app` URL and paste it into the Twilio Webhook settings as described in Step 3.
3. Send a test SMS from your personal phone to your Twilio number:
   *Text: "Your Google verification code is G-482917"*
4. Check the frontend dashboard! The SMS OTP should appear automatically.
