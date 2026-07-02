# FoodWasteChain - Project Overview & Flow

## 1. Project Overview
**FoodWasteChain** is an AI-powered, blockchain-verified platform designed to tackle the global food waste crisis. It intelligently connects food donors (restaurants, hotels) with nearby charities and NGOs, ensuring transparent, traceable, and zero-cost food redistribution.

**Key Features:**
- **AI Matching Engine:** Finds the best charity based on proximity, need, and capacity.
- **Blockchain Verification:** Immutable transaction records on the Ethereum Sepolia testnet.
- **QR Code Security:** Tamper-proof pickup and delivery confirmation.
- **ML Demand Forecasting:** Predicts future food needs for charities.

---

## 2. Simplified Project Flow (For PPT)

This 5-stage automated pipeline illustrates the core lifecycle of a food donation.

```text
[ DONATE ] ──> [ AI MATCH ] ──> [ ACCEPT ] ──> [ QR PICKUP ] ──> [ VERIFICATION ]
 (Donor)        (Engine)       (Charity)        (Physical)        (Blockchain)
```

**Brief Steps:**
1. **Donate:** Donor creates a food listing.
2. **AI Match:** System automatically ranks and assigns the best nearby charity.
3. **Accept:** Charity accepts the match via their dashboard.
4. **QR Pickup:** Charity physically picks up food from the donor, verified by scanning a secure QR code.
5. **Verification:** Charity receives the food, uploads a photo, and the transaction is recorded on the blockchain with a digital receipt.

---

## 3. Detailed Step-by-Step Workflow

### A. Donor Workflow
1. **Registration/Login:** Donor signs up with location data.
2. **Create Listing:** Donor posts surplus food details (type, quantity, expiry, photo).
3. **Instant AI Matching:** The system instantly matches the listing with the most suitable charity within a 25km radius.
4. **Handoff (QR Verification):** When the charity arrives, the donor and charity authenticate the handoff using a secure, HMAC-signed QR code.
5. **Blockchain Receipt:** Once the charity verifies delivery at their center, the donor receives a PDF receipt containing the Ethereum transaction hash.

### B. Charity Workflow
1. **Registration/Login:** Charity signs up with location data.
2. **Review Match:** Charity receives an email and dashboard notification of a matched donation. They can Accept or Reject.
3. **Physical Pickup:** Charity visits the donor and uses the QR code to authenticate the pickup.
4. **Delivery Verification:** Upon arriving back at their facility, the charity uploads a photo to confirm successful delivery.
5. **Demand Forecasting:** The charity's dashboard updates its 7-day ML forecast chart based on this new delivery.

---

## 4. Technology Stack (Highlights)
- **Backend:** Django (Python), Supabase PostgreSQL
- **Blockchain:** Ethereum Sepolia Testnet, Web3.py
- **AI/ML:** Custom Machine Learning for demand forecasting and matching
- **Geolocation:** Haversine formula, OSRM API (Real-road routing)
- **Security:** Cryptographic QR codes (HMAC-signed)

---

## 5. Impact & Benefits
- **Zero Cost:** The platform is free to use for NGOs and social enterprises.
- **Transparency:** Donors get verifiable proof that their food reached the intended recipients, preventing fraud.
- **Environment:** Reduces landfill waste and CO2 emissions.
- **Data-Driven:** Predicts charity needs to prevent over-delivery or shortages.
