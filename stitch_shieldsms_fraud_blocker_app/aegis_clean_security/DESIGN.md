---
name: Aegis Clean Security
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#434656'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#737688'
  outline-variant: '#c3c5d9'
  surface-tint: '#004ced'
  primary: '#003ec7'
  on-primary: '#ffffff'
  primary-container: '#0052ff'
  on-primary-container: '#dfe3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#006b5b'
  on-secondary: '#ffffff'
  secondary-container: '#53f8d9'
  on-secondary-container: '#00705f'
  tertiary: '#005a3c'
  on-tertiary: '#ffffff'
  tertiary-container: '#007550'
  on-tertiary-container: '#72fec0'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001452'
  on-primary-fixed-variant: '#0038b6'
  secondary-fixed: '#57fbdb'
  secondary-fixed-dim: '#2adec0'
  on-secondary-fixed: '#00201a'
  on-secondary-fixed-variant: '#005144'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

The design system projects uncompromised personal mobile safety, high operational precision, and effortless calm. Built specifically for scam protection and fraud filtering, the interface intentionally deviates from stereotypical "dark hacker" cybersecurity aesthetics in favor of an ultra-clean, clinical, daylight-clarity environment. 

The aesthetic is Modern High-Trust Minimalism with tactile clarity. Crisp pure whites, cool slate neutrals, and high-energy optical accents (cyan, electric indigo, and clinical emerald) provide immediate confirmation of safety without inducing cognitive overload or panic. The emotional response is pure relief, transparency, and authoritative vigilance: users feel that their mobile perimeter is actively protected by military-grade intelligence wrapped in consumer-grade simplicity.

## Colors

The system uses a luminous, high-contrast light architecture anchored by an active electric indigo primary and an assertive cyber cyan secondary, supported by instant-recognition security status tokens.

- **Primary (`#0052FF` - Electric Indigo):** Represents active surveillance, system enforcement, verified shield status, and primary action paths.
- **Secondary (`#00D2B4` - Cyber Cyan):** Represents real-time processing, scanning telemetry, heuristic analysis indicators, and focus state accents.
- **Tertiary (`#10B981` - Clinical Emerald):** The foundational "Safe" indicator. Signifies verified senders, zero-threat scan reports, and successfully blocked threats.
- **Neutral (`#0F172A` - Slate Deep):** Provides sharp, crisp contrast for typography, prominent icons, and micro-delimiters against pure white canvas layers.

### Contextual Security Status Tokens
- **Status Safe (`#10B981` / Background `#ECFDF5` / Border `#A7F3D0`):** Confirmed authenticated contacts, clean message scans, and nominal protection status.
- **Status Warning / Suspicious (`#F59E0B` / Background `#FFFBEB` / Border `#FDE68A`):** Heuristic anomaly, unknown caller, spoofing risk, unverified link.
- **Status Threat / Blocked (`#EF4444` / Background `#FEF2F2` / Border `#FECACA`):** Malicious URL detected, high-risk credential harvester, flagged fraud number blocked.
- **Surface Elevation Scale:** Surface base is `#FFFFFF`. Secondary container surface is `#F8FAFC`, and surface elevated is `#F1F5F9`. Thin structural dividers strictly use `#E2E8F0`.

## Typography

The type system balances technical authority with immediate, high-stress legibility.

- **Headlines (Plus Jakarta Sans):** Uses geometric warmth, clean circular forms, and confident weights to deliver optimistic, reassuring, and decisive titles.
- **Body & Metadata (Inter):** Highly structured grotesque font designed for ultra-clear text rendering on high-DPI screens. Used for analyzing sender metadata, risk breakdowns, and message transcripts.
- **Letter Spacing:** `label-sm` utilizes an expanded tracking of `+0.05em` with uppercase transformation for security status badges (`SAFE`, `SCAM DETECTED`, `BLOCKED`). All headlines above `24px` adopt subtle tightening (`-0.02em`) for a solid, authoritative display impact.

## Layout & Spacing

The layout operates on a strict 4px/8px incremental rhythm within a 4-column fluid mobile grid, scaling to 8 columns on tablet devices.

- **Canvas Margins:** Mobile viewports leverage a fixed `margin` of `1rem` (16px) to maximize touch target width and data card density while guarding safe boundaries against bezel edges.
- **Gutter Distribution:** `1rem` (16px) separates interactive metric cards, split action dialogs, and stat grids.
- **Vertical Hierarchy:** Vertical stack distances follow strict intent tiers:
  - `space-xs` (4px): Micro-pairings, such as status dot to badge text or sub-header timestamps.
  - `space-sm` (8px): Related inline items, badge groups, and card internal item rows.
  - `space-md` (16px): Standard padding within message inspection cards and control containers.
  - `space-lg` (24px): Logical section breaks between active scan status headers and recent incident feeds.
  - `space-xl` (32px): Major structural transitions, such as canvas tops and primary dashboard hero modules.

## Elevation & Depth

To preserve the daylight, ultra-clean aesthetic, depth is constructed using layered flat surfaces and ultra-soft, daylight-diffused shadows tinted with cool indigo/slate.

- **Surface Layering:** Base screen foundation is pure white (`#FFFFFF`). Content cards sit on Level 1 (`#F8FAFC`), outlined by micro-borders (`1px solid #E2E8F0`).
- **Tactile Hover/Active Depth:**
  - **Level 0 (Flat):** Message scan items, data rows, and standard list items rely exclusively on a 1px border (`#E2E8F0`) with zero drop-shadow.
  - **Level 1 (Ambient Shield):** Critical threat cards and primary monitoring widgets use `box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05)`.
  - **Level 2 (Floating Action / Sticky Perimeter):** Quick-action toolbars, bottom navigation, and security alert modals use `box-shadow: 0 12px 32px -4px rgba(0, 82, 255, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04)`.
- **Glow Accents:** Active protection shields feature a subtle atmospheric radial glow: `0 0 32px rgba(0, 210, 180, 0.15)`.

## Shapes

The design system adheres to a consistent, rounded architectural profile (Level 2). This eliminates clinical harshness while avoiding overly childish toy-like roundedness.

- **Cards and Hero Panels:** Default to `rounded-xl` (1.5rem / 24px) for organic, protective visual envelopes.
- **Interactive Controls (Buttons, Inputs):** Default to `rounded-lg` (1rem / 16px) ensuring comfortable, ergonomic thumb targets.
- **Chips, Pills, and Security Tags:** Utilize full pill encapsulation (`rounded-full` / 9999px) to distinctly contrast metadata against structural cards.

## Components

### Buttons
- **Primary Action (Active Defense):** Solid Electric Indigo (`#0052FF`), text white, `rounded-lg` (16px), 48px height for thumb ergonomics. Subtle pressed-state scaling (`0.98`).
- **Secondary / Action Ghost:** Surface `#F1F5F9`, text `#0F172A`, zero border, `rounded-lg`.
- **Destructive Shield Action:** Solid Threat Red (`#EF4444`) with white text, applied exclusively for irrevocable actions such as "Block & Purge Sender".

### Badges & Status Indicators
- **Security Badges:** Pill-shaped (`rounded-full`), height 24px, horizontal padding `space-sm` (8px). 
  - **Verified Safe:** Emerald background `#ECFDF5`, text `#065F46`, paired with a solid 6px pulsating green status dot.
  - **High-Risk Scam:** Red background `#FEF2F2`, text `#991B1B`, accompanied by an alert icon.
  - **AI Scan in Progress:** Cyan tint `#ECFEFF`, text `#155E75`, with rotating telemetry indicator.

### Input Fields
- Height 48px, background `#F8FAFC`, border 1px solid `#E2E8F0`, `rounded-lg` (16px), text `#0F172A`, placeholder `#94A3B8`.
- Focus state triggers a 2px outer ring in Electric Indigo (`#0052FF`) with zero blur.

### Cards & Threat Detail Panels
- Dual-surface design: `#FFFFFF` base wrapped with a 1px border (`#E2E8F0`), padding `space-md` (16px), and `rounded-xl` (24px).
- Threat cards feature a 4px solid left-accent border matching the status color (Green, Amber, Red).

### Lists (Message & Call Logs)
- Separated items with 8px margin gaps rather than continuous rule lines. Each list item features leading sender avatar badges, middle content previews with highlighted suspicious links (rendered in high-contrast red underline), and trailing timestamp/status badge.

### Domain-Specific Components
- **Shield Radar Hero:** Central circular SVG visual communicating current protection posture (Green pulse = Protected, Blue sweep = Scanning, Amber pulse = Action Required).
- **Phishing URL Inspector:** Monospaced, highlighted URL visualizer dissecting deceptive subdomains and IP addresses into distinct tokenized capsules for user review.