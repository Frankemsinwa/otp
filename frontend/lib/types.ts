export type Provider = "google" | "yahoo" | "other";
export type TargetStatus = "active" | "compromised" | "inactive" | "pending";

export interface Target {
  id: string;
  email: string;
  provider: Provider;
  status: TargetStatus;
  created_at: string;
  password?: string;
}

export interface LiveEvent {
  type: string;
  target_id: string;
  target_email: string;
  extracted_code?: string;
  confidence?: string;
  sender?: string;
  subject?: string;
  captured_at?: string;
  otp?: any;
  sms?: any;
}

export const __keep = true;

