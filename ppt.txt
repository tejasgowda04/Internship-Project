# ═══════════════════════════════════════════════════════════════════════════════
#  FOODWASTECHAIN — COMPLETE PROJECT DOCUMENTATION
#  A Blockchain-Verified, AI-Powered Food Waste Redistribution Platform
# ═══════════════════════════════════════════════════════════════════════════════


## TABLE OF CONTENTS

1.  Project Overview
2.  Problem Statement
3.  Solution & How It Works
4.  Complete Workflow (Both Sides — Donor & Charity)
5.  System Architecture
6.  Technology Stack
7.  Database Schema & Models
8.  Service Layer (Backend Engines)
9.  All Features & Functionalities
10. URL Routes & API Endpoints
11. User Roles & Access Control
12. Benefits & Impact
13. Security Mechanisms
14. File/Folder Structure
15. How to Run the Project
16. Future Scope


---


## 1. PROJECT OVERVIEW

**FoodWasteChain** is a full-stack web platform built with Django that tackles the
global food waste crisis by intelligently connecting food donors (restaurants,
hotels, catering services) with nearby charities, NGOs, and shelters. 

The platform uses:
- **AI-powered matching** to find the best charity for each food donation
- **Blockchain verification** (Ethereum Sepolia testnet) for tamper-proof records
- **QR code authentication** for secure pickup and delivery confirmation
- **ML demand forecasting** to predict charity needs
- **Geolocation routing** using OSRM for real-world road distances
- **Automated email notifications** at every stage of the donation lifecycle
- **Digital PDF receipts** with blockchain proof for verified donations

The entire system operates at **zero cost** — no paid APIs, no proprietary
services — making it ideal for NGOs and social enterprises.


---


## 2. PROBLEM STATEMENT

**The Global Food Waste Crisis:**

- Approximately **1.3 billion tonnes** of food is wasted globally every year
  (source: FAO/UN)
- Meanwhile, over **800 million people** face hunger and food insecurity
- Surplus food from restaurants, hotels, and events often ends up in landfills
  simply because there is no efficient system to redistribute it
- Existing solutions lack **transparency**, **traceability**, and **trust**
  between donors and recipients
- Manual coordination between donors and charities is slow, error-prone, and
  does not scale

**Core Challenges Addressed:**

1. How to efficiently match surplus food with the charities that need it most
2. How to ensure food reaches the intended recipient (no diversion/fraud)
3. How to create an immutable, transparent audit trail of every donation
4. How to predict future food demand at charities for better planning
5. How to make the entire process zero-cost and accessible to all


---


## 3. SOLUTION & HOW IT WORKS

FoodWasteChain solves these problems through a **5-stage automated pipeline**:

```
┌──────────┐    ┌───────────┐    ┌───────────┐    ┌──────────────┐    ┌───────────────┐
│  DONATE   │───>│  AI MATCH  │───>│  ACCEPT   │───>│  QR PICKUP   │───>│  BLOCKCHAIN   │
│  (Donor)  │    │  (Engine)  │    │ (Charity) │    │ VERIFICATION │    │  VERIFICATION │
└──────────┘    └───────────┘    └───────────┘    └──────────────┘    └───────────────┘
     |                |                |                  |                    |
  Creates          Scores &        Accepts/           Scans QR             Records TX
  food listing     ranks all       rejects match      to confirm           on Ethereum
  with details     nearby           via dashboard      physical pickup      Sepolia +
  + photo          charities                          of food items         PDF receipt
```

**High-Level Flow:**

1. **Donor** creates a food surplus listing (type, quantity, expiry, photo)
2. The **AI Matching Engine** automatically finds the best nearby charity based
   on proximity, predicted need, and historical reliability
3. The matched **Charity** receives an email notif and reviews the match on
   their dashboard — they can accept or reject
4. On acceptance, a **unique QR code** (with HMAC signature) is generated for
   tamper-proof pickup verification
5. At physical pickup (donor's location), the **QR code is scanned and
   verified** — both parties are present to confirm the handoff
6. After the charity receives the food at their location, a **delivery
   photo is uploaded** and the transaction is **recorded on the Ethereum
   blockchain** (Sepolia testnet) — no QR scan needed here since the
   donor is not present
7. Both parties receive a **digital PDF receipt** with blockchain proof
8. Platform-wide **impact metrics** are updated in real-time


---


## 4. COMPLETE WORKFLOW (BOTH SIDES)

### ══════════════════════════════════════════
###  DONOR SIDE (Restaurants / Hotels / Caterers)
### ══════════════════════════════════════════

**Step 1: Registration**
  - Donor signs up with: username, email, password, organization name, phone,
    address, and geolocation (latitude/longitude — auto-captured or manual)
  - Role is set to "donor"
  - Platform impact metrics are updated (total_donors counter)
  - Donor is auto-logged-in after registration

**Step 2: Donor Dashboard**
  - Shows all their food listings with statuses
  - Real-time stats: total listings, active count, matched count, verified count
  - Shows total kg donated and total monetary value saved
  - Quick access to create new listings

**Step 3: Create Food Listing**
  - Donor fills out: food type (8 categories), description, quantity in kg,
    expiry date/time, and optional photo
  - Estimated monetary value is **optional** — only needed for tax deduction
    records and impact reporting (default: ₹0)
  - **On submission, AI matching is IMMEDIATELY triggered:**
    a) The engine finds all charities within 25km (Haversine filter)
    b) For each candidate, it calculates:
       - Proximity Score (40%): Based on OSRM real road distance
       - Need Score (40%): ML-predicted demand from historical data
       - Capacity Score (20%): Past acceptance/completion rate
    c) Charities are ranked by composite score
    d) A Match record is created linking listing → top-ranked charity
  - A QR code is generated for the match
  - Email notifications are sent to both donor and charity
  - Listing status changes: available → matched

**Step 4: Monitor & Track**
  - Donor can view listing details and all associated matches
  - Can confirm pickup when charity arrives (QR scan required — both present)
  - Can download a PDF receipt after delivery is verified

**Step 5: Receipt & Proof**
  - After verification, donor can download a branded PDF receipt containing:
    - Donation details, matching metrics, delivery timeline
    - Blockchain transaction hash + Etherscan URL
    - QR code embedded in the receipt


### ══════════════════════════════════════════
###  CHARITY SIDE (NGOs / Shelters / Food Banks)
### ══════════════════════════════════════════

**Step 1: Registration**
  - Charity signs up similarly, with role set to "charity"
  - Geolocation is critical — it determines which donors they get matched with

**Step 2: Charity Dashboard**
  - Shows all matches: pending (awaiting decision), accepted, verified
  - Stats: pending count, accepted count, verified count, total kg received
  - **7-day demand forecast chart** (ML-powered) showing predicted daily demand
  - Each match card shows: food details, donor info, distance, match score

**Step 3: Review & Accept Matches**
  - When a donor posts food, the charity gets an email notification
  - On dashboard, charity sees pending matches with full details
  - **Accept:** Match status → accepted, QR code is regenerated,
    donor gets notified via email
  - **Reject:** Match is cancelled, listing status reverts to "available",
    the AI engine re-runs to find the next best charity

**Step 4: Pickup (QR Verification at Donor's Location)**
  - Charity goes to the donor's location to pick up the food
  - They must scan/enter the QR code data to confirm pickup
  - The QR is cryptographically signed (HMAC with server secret key)
  - If the QR data doesn't match (wrong match ID or tampered signature),
    the pickup is REJECTED
  - Both donor and charity are physically present at this step
  - On success: match status → picked_up, timestamp recorded

**Step 5: Delivery Verification (Photo + Blockchain)**
  - After receiving the food at their own location, the charity
    goes to "Verify Delivery"
  - **No QR scan required** — the donor is NOT present at the charity's
    location, so QR re-verification adds no security value
  - Charity uploads a delivery confirmation photo as proof
  - The platform then:
    a) Records the verification on Ethereum Sepolia blockchain
    b) Updates match/listing status to "verified"
    c) Creates a DemandHistory entry (for future ML predictions)
    d) Updates platform-wide ImpactMetrics
    e) Sends verification email with attached PDF receipt to both parties

**Step 6: Receipt & History**
  - Charity can download the PDF receipt
  - Their demand history builds over time, improving future match accuracy


### ══════════════════════════════════════════
###  ADMIN SIDE (Platform Administrators)
### ══════════════════════════════════════════

- Overview dashboard with:
  - Platform-wide ImpactMetrics (total kg saved, value saved, verifications)
  - User breakdown by role (donor/charity/admin counts)
  - Recent 10 food listings with donor details
  - Recent 10 matches with full context
- Full read access to all listings, matches, and user data
- Access to the Django Admin panel for data management


---


## 5. SYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (WEB BROWSER)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   Landing    │  │   Donor     │  │  Charity    │  │   Admin      │  │
│  │   Page       │  │  Dashboard  │  │  Dashboard  │  │  Dashboard   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │
│         │                │                │                 │          │
│  Django Templates (HTML/CSS/JS) + QR Scanner        JSON API Endpoints │
└─────────┼────────────────┼────────────────┼─────────────────┼──────────┘
          │                │                │                 │
          ▼                ▼                ▼                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     DJANGO APPLICATION (Python 3 / Django 4.2)          │
│                                                                         │
│  ┌───────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │   Views   │  │    Forms     │  │  Decorators  │  │   Context     │  │
│  │  (views.py│  │  (forms.py)  │  │ (decorators  │  │  Processors   │  │
│  │   660 LOC)│  │              │  │   .py)       │  │               │  │
│  └─────┬─────┘  └──────────────┘  └──────────────┘  └───────────────┘  │
│        │                                                                │
│        ▼                                                                │
│  ┌──────────────────────── SERVICE LAYER ─────────────────────────────┐ │
│  │                                                                    │ │
│  │  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐  │ │
│  │  │  Matching    │   │   ML Demand  │   │    Geo Service        │  │ │
│  │  │  Engine      │   │  Forecasting │   │ (Haversine + OSRM)   │  │ │
│  │  │              │   │              │   │                       │  │ │
│  │  │ • Proximity  │   │ • Need Score │   │ • haversine_distance  │  │ │
│  │  │   40%        │   │   0.0 – 1.0  │   │ • osrm_road_distance  │  │ │
│  │  │ • Need 40%   │   │ • 7-day      │   │ • filter_by_radius    │  │ │
│  │  │ • Capacity   │   │   forecast   │   │ • route_details       │  │ │
│  │  │   20%        │   │   (SMA)      │   │                       │  │ │
│  │  └──────┬───────┘   └──────┬───────┘   └───────────┬───────────┘  │ │
│  │         │                  │                        │              │ │
│  │  ┌──────┴───────┐   ┌──────┴───────┐   ┌───────────┴───────────┐  │ │
│  │  │  Blockchain  │   │  QR Service  │   │    Email Service      │  │ │
│  │  │  Service     │   │              │   │                       │  │ │
│  │  │              │   │ • generate   │   │ • notify_match_created│  │ │
│  │  │ • Ethereum   │   │   pickup QR  │   │ • notify_accepted     │  │ │
│  │  │   Sepolia    │   │ • verify QR  │   │ • notify_verified     │  │ │
│  │  │ • web3.py    │   │   signature  │   │ • Gmail SMTP          │  │ │
│  │  │ • mock hash  │   │ • HMAC auth  │   │ • PDF attachment      │  │ │
│  │  └──────────────┘   └──────────────┘   └───────────────────────┘  │ │
│  │                                                                    │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │               Receipt Service (PDF Generation)               │  │ │
│  │  │                                                              │  │ │
│  │  │  • Branded layout with emerald/dark theme                    │  │ │
│  │  │  • Donor + Charity info, food details, matching metrics      │  │ │
│  │  │  • Complete delivery timeline                                │  │ │
│  │  │  • Blockchain proof (TX hash + Etherscan link)               │  │ │
│  │  │  • Embedded QR code                                          │  │ │
│  │  │  • ReportLab library (pure Python, zero-cost)                │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────── DATA LAYER (MODELS) ───────────────────────────┐ │
│  │  UserProfile  │  FoodListing  │  Match  │  DemandHistory  │ Impact │ │
│  └───────────────┴───────────────┴─────────┴─────────────────┴────────┘ │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES / INFRA                          │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Supabase    │  │   Ethereum   │  │  OSRM Public │  │   Gmail    │ │
│  │  PostgreSQL  │  │   Sepolia    │  │   Router API │  │   SMTP     │ │
│  │  (or SQLite) │  │   Testnet    │  │  (Free, OSS) │  │            │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```


---


## 6. TECHNOLOGY STACK

| Layer             | Technology                        | Purpose                              |
|-------------------|-----------------------------------|--------------------------------------|
| Backend Framework | Django 4.2 (Python)               | Web framework, ORM, auth, templating |
| Database          | Supabase PostgreSQL / SQLite      | Persistent data storage              |
| Blockchain        | Ethereum Sepolia + web3.py 6.15   | Immutable transaction recording      |
| Geolocation       | Haversine formula + OSRM API      | Distance calculation & road routing  |
| ML Forecasting    | Custom SMA (Simple Moving Average)| Demand prediction for charities      |
| QR Codes          | qrcode[pil] 7.4.2 + Pillow       | Secure pickup/delivery verification  |
| PDF Generation    | ReportLab 4.1.0                   | Branded digital receipts             |
| Email             | Django SMTP (Gmail)               | Automated notifications              |
| HTTP Client       | requests 2.31.0                   | OSRM API calls                       |
| Environment       | python-dotenv 1.0.1               | Secrets management                   |
| Frontend          | Django Templates + Vanilla CSS/JS | Server-side rendered UI              |


---


## 7. DATABASE SCHEMA & MODELS

### UserProfile
Extends Django's built-in User model with:
- `role` — 'donor', 'charity', or 'admin'
- `organization_name` — name of restaurant/NGO
- `phone`, `address` — contact details
- `latitude`, `longitude` — geolocation (default: Bangalore 12.9716, 77.5946)
- `is_verified` — admin verification flag
- `created_at` — registration timestamp

### FoodListing
Represents a food surplus donation:
- `id` — UUID primary key (non-guessable)
- `donor` — FK to User
- `food_type` — 8 categories: cooked_meals, raw_vegetables, fruits, dairy,
  bakery, packaged, beverages, mixed
- `description`, `quantity_kg`, `estimated_value` — donation details
- `expiry_time` — when the food expires
- `photo` — uploaded image
- `status` — available → matched → picked_up → verified (or expired/cancelled)
- Properties: `is_expired`, `time_remaining`

### Match
Links a FoodListing to a Charity, contains matching & verification data:
- `id` — UUID primary key
- `listing` — FK to FoodListing
- `charity` — FK to User
- `distance_km` — Haversine (crow-flies) distance
- `road_distance_km` — OSRM real road distance
- `need_score` — ML-predicted need (0.0–1.0)
- `match_score` — Composite score: (0.4 × proximity + 0.4 × need + 0.2 × capacity)
- `status` — pending → accepted → picked_up → verified (or rejected/cancelled)
- `blockchain_tx_hash` — Ethereum transaction hash after verification
- `qr_code` — generated QR code image
- `delivery_photo` — uploaded delivery proof
- `accepted_at`, `picked_up_at`, `verified_at` — timeline timestamps
- Property: `etherscan_url` — link to Sepolia Etherscan

### DemandHistory
Historical food demand data used by the ML forecasting engine:
- `charity` — FK to User
- `food_type` — what type of food was received
- `quantity_kg` — how much
- `timestamp` — when

### ImpactMetrics
Singleton model for platform-wide statistics:
- `total_kg_saved` — total food redistributed (kg)
- `total_value_saved` — total monetary value saved (₹)
- `total_verifications` — total blockchain verifications
- `total_matches` — total matches created
- `total_donors`, `total_charities` — user counts


---


## 8. SERVICE LAYER (BACKEND ENGINES)

### 8.1 AI Matching Engine (matching_engine.py)

**Purpose:** Automatically find the best charity for each food listing.

**Algorithm:**
1. Filter: All charities within 25km radius (Haversine pre-filter)
2. For each candidate charity, calculate three scores:
   - **Proximity Score (Weight: 40%)**
     - ≤ 2km → 1.0 | ≤ 5km → 0.85 | ≤ 10km → 0.65
     - ≤ 15km → 0.45 | ≤ 25km → 0.25 | > 25km → 0.1
     - Uses OSRM real road distance (not crow-flies)
   - **Need Score (Weight: 40%)**
     - ML-predicted demand based on 30-day history
     - Factors: trend (recent 7-day vs monthly average), recency of last delivery
     - New charities get a default score of 0.6
   - **Capacity Score (Weight: 20%)**
     - Historical acceptance rate (accepted ÷ total matches)
     - New charities get a default score of 0.7
3. Composite score = 0.4 × proximity + 0.4 × need + 0.2 × capacity
4. Rank all charities by composite score, select the highest
5. Create a Match record and update listing status to "matched"

**Re-matching:** If a charity rejects a match, the engine re-runs to find
the next best charity automatically.


### 8.2 ML Demand Forecasting (ml_forecast.py)

**Purpose:** Predict how much food a charity will need in the coming days.

**Two Functions:**

1. **calculate_need_score(charity, food_type)** → float (0.0–1.0)
   - Looks at 30-day demand history
   - Compares 7-day recent average vs. monthly average (trend factor)
   - Checks recency of last verified delivery (recency factor)
   - Formula: need = 0.4 × trend + 0.4 × recency + 0.2 × baseline

2. **get_demand_forecast(charity, periods=7)** → list of {date, predicted_kg}
   - 7-day Simple Moving Average over historical daily demand data
   - Adds slight random variance (±15%) for realistic predictions
   - Used to render forecast charts on the charity dashboard


### 8.3 Geo Service (geo_service.py)

**Purpose:** Calculate distances between donors and charities.

**Two Distance Methods:**

1. **Haversine Distance** — Great-circle (crow-flies) distance
   - Fast, no API dependency
   - Used as a pre-filter to eliminate distant charities quickly

2. **OSRM Road Distance** — Real-world driving distance via road network
   - Uses the free, public OSRM API (router.project-osrm.org)
   - Returns distance in km and estimated duration in minutes
   - Fallback: If OSRM is unavailable, uses haversine × 1.3 factor

**Key Functions:**
- `filter_charities_by_radius()` — quick spatial pre-filter
- `get_route_details()` — full route info (haversine + road + duration)


### 8.4 Blockchain Service (blockchain_service.py)

**Purpose:** Record an immutable, tamper-proof verification of every donation.

**How It Works:**
- Uses web3.py to connect to an Ethereum Sepolia testnet RPC
- Creates a zero-value self-transfer transaction (data-only)
- The transaction `data` field encodes:
  - Match ID, Donor username, Charity username
  - Food type, Quantity, Match score
- Signs and broadcasts the transaction
- Returns the transaction hash (viewable on Sepolia Etherscan)

**Fallback:** If web3 is not installed or blockchain credentials are missing,
a deterministic mock hash (SHA-256) is generated for demo/dev purposes.


### 8.5 QR Code Service (qr_service.py)

**Purpose:** Generate and verify cryptographically signed QR codes for
pickup/delivery authentication.

**QR Payload Contains:**
- Header: "FOODWASTECHAIN-PICKUP"
- Match ID, Food type, Quantity
- Donor and Charity organization names
- Timestamp (ISO format)
- **HMAC Signature** (first 16 chars of SHA-256 hash of:
  match_id + listing_id + charity_username + timestamp + SECRET_KEY)

**Verification Process:**
1. Check that the scanned QR data contains the correct Match ID
2. Extract the timestamp and signature from the QR data
3. Recompute the expected signature using the server's SECRET_KEY
4. Compare signatures — if they don't match, the QR is REJECTED

This prevents:
- Using someone else's QR code
- Tampering with QR data
- Replaying old QR codes (different timestamp → different signature)


### 8.6 Email Service (email_service.py)

**Purpose:** Send automated email notifications at every stage.

**Notification Types:**
1. **Match Created** — Notifies both donor and charity with full details
2. **Match Accepted** — Notifies donor that charity accepted pickup
3. **Verification Complete** — Notifies both parties with blockchain proof
   and attaches the PDF receipt as an email attachment

**Tech:** Django SMTP backend with Gmail. Uses `EmailMultiAlternatives` for
rich emails with PDF attachments.


### 8.7 Receipt Service (receipt_service.py)

**Purpose:** Generate professional, branded PDF receipts for verified donations.

**PDF Contents (320 LOC, ReportLab):**
- FoodWasteChain branded header (emerald green theme)
- Receipt number (FWC-XXXXXXXX)
- Donor and Charity details (org name, address, phone)
- Donation details (food type, quantity, value, description, expiry)
- Matching metrics (match score %, road distance, need score %)
- Complete delivery timeline (created → accepted → picked up → verified)
- Blockchain verification section (TX hash, Etherscan URL, network info)
- Embedded QR code
- Legal footer with dispute contact info


---


## 9. ALL FEATURES & FUNCTIONALITIES

### Authentication & User Management
- [x] Multi-role registration (Donor / Charity)
- [x] Login by username or email
- [x] Session-based authentication
- [x] Role-based access control decorators
- [x] Auto-redirect: authenticated users skip login/register pages

### Donor Features
- [x] Create food surplus listing with 8 food type categories
- [x] Upload food photos
- [x] Set expiry date/time
- [x] View listing details with all associated matches
- [x] Confirm pickup via QR scan
- [x] Verify delivery + upload proof photo
- [x] Download PDF receipt after verification
- [x] Dashboard with real-time stats

### Charity Features
- [x] View pending match notifications
- [x] Accept or reject matches
- [x] View QR code for accepted matches
- [x] Confirm pickup via QR scan
- [x] Verify delivery via QR scan + photo upload
- [x] Download PDF receipt after verification
- [x] 7-day demand forecast chart on dashboard
- [x] Dashboard with real-time stats

### AI & ML
- [x] Automatic AI charity scoring (proximity + need + capacity)
- [x] OSRM road distance calculation
- [x] Haversine spatial pre-filtering
- [x] ML demand prediction (trend + recency factors)
- [x] 7-day demand forecasting with SMA
- [x] Auto re-matching on rejection

### Blockchain
- [x] Ethereum Sepolia testnet verification
- [x] Zero-value data-only transactions
- [x] Transaction hash stored per match
- [x] Etherscan URL generation
- [x] Mock hash fallback for dev/demo

### Security
- [x] HMAC-signed QR codes
- [x] QR signature verification (prevents tampering)
- [x] Role-based view decorators (donor_required, charity_required, admin_required)
- [x] Access control on every view (only relevant parties can access)
- [x] UUID primary keys (non-guessable)
- [x] CSRF protection (Django middleware)
- [x] Password validation (4 built-in validators)

### Notifications
- [x] Email on match creation (to both parties)
- [x] Email on match acceptance (to donor)
- [x] Email on verification (to both + PDF attachment)
- [x] In-app flash messages at every action

### Reports & Analytics
- [x] Platform-wide ImpactMetrics (kg saved, value saved, counts)
- [x] Donor stats (total listings, active, matched, verified, kg, value)
- [x] Charity stats (pending, accepted, verified, total received kg)
- [x] Admin overview with user breakdown by role
- [x] PDF receipt generation with full audit trail

### API Endpoints (JSON)
- [x] GET /api/listings/ — available food listings (for maps)
- [x] GET /api/impact/ — platform impact metrics
- [x] GET /api/matches/{id}/ — match detail with blockchain + geo data


---


## 10. URL ROUTES & API ENDPOINTS

| URL Pattern                             | View Function     | Purpose                        |
|-----------------------------------------|-------------------|--------------------------------|
| /                                       | landing_page      | Public homepage + metrics      |
| /register/                              | register_view     | User registration              |
| /login/                                 | login_view        | User login                     |
| /logout/                                | logout_view       | User logout                    |
| /dashboard/                             | dashboard         | Role-based dashboard redirect  |
| /listings/create/                       | create_listing    | Create food listing + AI match |
| /listings/{uuid}/                       | listing_detail    | View listing + matches         |
| /matches/{uuid}/accept/                 | accept_match      | Charity accepts match          |
| /matches/{uuid}/reject/                 | reject_match      | Charity rejects match          |
| /matches/{uuid}/pickup/                 | confirm_pickup    | QR-verified pickup             |
| /matches/{uuid}/verify/                 | verify_delivery   | QR + photo + blockchain verify |
| /matches/{uuid}/qr/                     | match_qr          | View/regenerate QR code        |
| /matches/{uuid}/receipt/                | download_receipt  | Download PDF receipt           |
| /api/listings/                          | api_listings      | JSON: available listings       |
| /api/impact/                            | api_impact        | JSON: impact metrics           |
| /api/matches/{uuid}/                    | api_match_detail  | JSON: match details            |


---


## 11. USER ROLES & ACCESS CONTROL

| Role    | Can Do                                                                |
|---------|-----------------------------------------------------------------------|
| Donor   | Create listings, view own listings, confirm pickup, verify delivery,  |
|         | download receipts, view QR codes for own matches                      |
| Charity | View pending matches, accept/reject, confirm pickup, verify delivery, |
|         | download receipts, view QR codes, see demand forecast                 |
| Admin   | View all listings, all matches, all users, impact metrics,            |
|         | access Django admin panel, download any receipt                       |

**Enforcement:**
- `@login_required` — requires authentication
- `@donor_required` — restricts to donor role
- `@charity_required` — restricts to charity role
- `@admin_required` — restricts to admin role
- In-view checks: match.charity == request.user, match.listing.donor == request.user


---


## 12. BENEFITS & IMPACT

### For Donors (Restaurants / Hotels / Caterers)
- **Zero-effort redistribution:** Just list surplus food — AI handles matching
- **Tax compliance:** Permanent digital receipt with blockchain proof
- **Social responsibility:** Demonstrable impact metrics (kg saved, value saved)
- **Brand value:** Association with transparent, verified charitable giving
- **Regulatory compliance:** Food waste regulations are tightening globally

### For Charities (NGOs / Shelters / Food Banks)
- **Intelligent allocation:** AI ensures they receive the food they need most
- **Demand forecasting:** 7-day ML predictions help plan resources
- **Transparency:** Blockchain-verified records for donor reporting
- **Reduced overhead:** Automated matching replaces manual coordination
- **Trust building:** Verifiable delivery proof for funders/donors

### For the Platform / Society
- **Reduces food waste** going to landfills → lower methane emissions
- **Feeds the hungry** using existing surplus → addresses food insecurity
- **Creates trust** via blockchain audit trail → encourages more participation
- **Costs nothing** — all services (OSRM, Sepolia, Gmail) are free/open-source
- **Scalable** — the model works for any city with minor config changes
- **Data-driven** — impact metrics quantify the social & environmental benefit

### Environmental Impact
- Every 1 kg of food waste prevented saves ~2.5 kg CO₂ equivalent
- Platform tracks total kg saved → directly quantifiable carbon impact
- Reduces landfill burden and associated environmental costs


---


## 13. SECURITY MECHANISMS

1. **HMAC-Signed QR Codes** — Each QR code contains a signature computed from
   match_id + listing_id + charity_username + timestamp + SECRET_KEY. Tampering
   with any field invalidates the signature.

2. **UUID Primary Keys** — All listings and matches use UUIDs instead of
   auto-increment integers. This prevents enumeration attacks.

3. **Role-Based Access Control** — Custom decorators ensure only the correct
   role can access specific views.

4. **Per-Object Access Control** — Even within a role, users can only access
   their own listings/matches (donor can't see another donor's data).

5. **CSRF Protection** — Django's built-in CSRF middleware is active.

6. **Password Validation** — 4 built-in validators (similarity, length,
   common passwords, numeric).

7. **SSL for Database** — Supabase PostgreSQL connections use `sslmode=require`.

8. **Blockchain Immutability** — Once recorded on Ethereum, verification data
   cannot be altered or deleted.

9. **Environment Variables** — All secrets (DB credentials, blockchain keys,
   email passwords) are stored in .env, never in code.


---


## 14. FILE / FOLDER STRUCTURE

```
Pro FInal/
├── .env                          # Environment variables (secrets)
├── .gitignore                    # Git ignore rules
├── README.md                     # Project readme
├── manage.py                     # Django management entry point
├── requirements.txt              # Python dependencies
├── db.sqlite3                    # SQLite database (local dev)
│
├── config/                       # Django project configuration
│   ├── __init__.py
│   ├── settings.py               # Database, email, blockchain config
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py                   # WSGI entry point
│   └── asgi.py                   # ASGI entry point
│
├── core/                         # Main application
│   ├── __init__.py
│   ├── admin.py                  # Django admin registration
│   ├── apps.py                   # App configuration
│   ├── context_processors.py     # Global template variables
│   ├── decorators.py             # Role-based access decorators
│   ├── forms.py                  # Registration, listing, delivery forms
│   ├── models.py                 # Database models (5 models)
│   ├── urls.py                   # URL routing (16 routes)
│   ├── views.py                  # All view functions (660 lines)
│   │
│   ├── services/                 # Backend service layer
│   │   ├── __init__.py
│   │   ├── matching_engine.py    # AI charity scoring & matching
│   │   ├── ml_forecast.py        # ML demand forecasting
│   │   ├── geo_service.py        # Haversine + OSRM distance
│   │   ├── blockchain_service.py # Ethereum Sepolia verification
│   │   ├── qr_service.py         # QR generation & HMAC verification
│   │   ├── email_service.py      # Automated email notifications
│   │   └── receipt_service.py    # PDF receipt generation
│   │
│   └── migrations/               # Database migration files
│
├── templates/
│   └── core/                     # HTML templates (12 files)
│       ├── base.html             # Base layout template
│       ├── landing.html          # Public homepage
│       ├── register.html         # Registration form
│       ├── login.html            # Login form
│       ├── dashboard_donor.html  # Donor dashboard
│       ├── dashboard_charity.html# Charity dashboard + forecast chart
│       ├── dashboard_admin.html  # Admin overview
│       ├── create_listing.html   # Create food listing form
│       ├── listing_detail.html   # Listing details + matches
│       ├── confirm_pickup.html   # QR-verified pickup page
│       ├── verify_delivery.html  # Delivery verification + photo upload
│       └── match_qr.html         # QR code display page
│
├── static/
│   └── css/                      # Stylesheets
│
├── media/                        # User-uploaded files
│   ├── listings/                 # Food photos
│   ├── qr_codes/                 # Generated QR code images
│   └── delivery_photos/          # Delivery confirmation photos
│
└── scratch/                      # Utility scripts
    ├── reset_match.py            # Admin script to reset match status
    └── check_match.py            # Debug script to inspect matches
```


---


## 15. HOW TO RUN THE PROJECT

### Prerequisites
- Python 3.10+
- pip (Python package manager)

### Setup Steps

1. Clone the repository:
   ```
   git clone <repository-url>
   cd "Pro FInal"
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate      (Windows)
   source venv/bin/activate   (macOS/Linux)
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (.env file):
   ```
   SECRET_KEY=your-django-secret-key
   DEBUG=True

   # Database (Supabase PostgreSQL or leave blank for SQLite)
   POSTGRES_URL_NON_POOLING=postgresql://...
   # OR individual vars:
   POSTGRES_HOST=...
   POSTGRES_USER=...
   POSTGRES_PASSWORD=...
   POSTGRES_DATABASE=...

   # Email (Gmail SMTP)
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password

   # Blockchain (Sepolia — optional, mock hash used if absent)
   ETH_PRIVATE_KEY=0x...
   SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
   ```

5. Run database migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser (admin):
   ```
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```
   python manage.py runserver
   ```

8. Access the application:
   - Homepage: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/


---


## 16. FUTURE SCOPE

- **Mobile App** — React Native / Flutter app for on-the-go donors and charities
- **Real-time Tracking** — Live GPS tracking of food pickup vehicles
- **Advanced ML** — Upgrade from SMA to LSTM/Prophet for better demand forecasting
- **Multi-city Deployment** — City-specific instances with centralized analytics
- **Gamification** — Leaderboards, badges, and rewards for top donors/charities
- **Mainnet Deployment** — Move from Sepolia testnet to Ethereum mainnet (or L2)
- **Government Integration** — Automated reporting for food safety compliance
- **IoT Sensors** — Temperature monitoring during food transport
- **Multi-language Support** — Hindi, Kannada, Tamil, etc.
- **Notification Channels** — WhatsApp, SMS, push notifications in addition to email


---


## SUMMARY

FoodWasteChain is a **production-grade, zero-cost socio-tech platform** that
uses AI + Blockchain + IoT-principles to create a transparent, trustworthy
food redistribution ecosystem. Every donation is:

  ✅ **AI-Matched** — to the charity that needs it most
  ✅ **QR-Verified** — at both pickup and delivery
  ✅ **Blockchain-Recorded** — on Ethereum for permanent, immutable proof
  ✅ **PDF-Receipted** — with full audit trail and blockchain reference
  ✅ **ML-Forecasted** — charity needs are predicted for better planning

The platform bridges the gap between food surplus and food insecurity,
creating measurable social impact while maintaining full transparency and
accountability.

---
Document prepared: April 2026
Project: FoodWasteChain (Pro Final)
Framework: Django 4.2 | Python 3.x | Ethereum Sepolia | OSRM | ReportLab
