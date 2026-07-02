# Project Practical Exam Preparation Document

This document contains all the necessary theoretical content structured specifically for your Project Practical Exam.

---

## 1. Title of the Project
**FoodWasteChain** — A Blockchain-Verified, AI-Powered Food Waste Redistribution Platform.

## 2. Introduction
**FoodWasteChain** is a full-stack web platform built with Django designed to tackle the global food waste crisis. It intelligently connects food donors (such as restaurants, hotels, and event caterers) with nearby charities, NGOs, and shelters. The platform utilizes an **AI-powered matching engine** to automatically find the most suitable charity for every donation, **cryptographic QR codes** to authenticate physical handoffs, and **Ethereum Blockchain technology** to create an immutable, transparent audit trail (digital receipt) of every successful donation. 

## 3. Objectives or Scope of Project
**Objectives:**
* **Reduce Food Waste:** To efficiently redistribute surplus food to those in need before it expires.
* **Automate Matching:** To eliminate manual coordination by using an AI engine that matches donors and charities based on proximity, historical demand, and capacity.
* **Ensure Transparency & Trust:** To provide tamper-proof blockchain-verified digital receipts for every donation, preventing fraud or diversion.
* **Predict Future Demand:** To use Machine Learning (ML) to forecast a charity's upcoming food requirements.

**Scope:**
The system is built as a web application accessible by two primary roles: **Donors** and **Charities**. It covers the complete lifecycle of a donation from listing creation, AI matching, QR-secured physical pickup, to final delivery verification and blockchain transaction recording.

## 4. Existing System
In the current, traditional approach to food donation:
* **Manual Coordination:** Donors have to manually call or search for NGOs that are willing to accept surplus food, which is slow and often results in food expiring.
* **Lack of Transparency & Trust:** Donors have no concrete proof that the food actually reached the intended hungry people rather than being diverted or sold.
* **No Predictive Planning:** Charities do not have data-driven insights to predict how much food they will receive or need in the coming days.
* **High Wastage:** Due to logistical inefficiencies, massive amounts of perfectly edible surplus food end up in landfills.

## 5. Proposed System
The proposed **FoodWasteChain** platform overcomes the drawbacks of the existing system by introducing:
* **Instant AI Matching:** An automated engine immediately ranks and matches food listings to charities based on OSRM real-road distance and predicted need.
* **Secure Verification:** A cryptographic, HMAC-signed QR code ensures that food is only handed over to the authorized charity representative at the pickup location.
* **Blockchain Immutability:** Once the charity confirms final delivery, the transaction is logged on the Ethereum Sepolia testnet, generating a permanent, tamper-proof PDF receipt for the donor's tax and CSR records.
* **Zero-Cost Operations:** Utilizing free public APIs (OSRM) and testnets, the platform costs nothing for NGOs to use.

## 6. System Requirements
**Hardware Requirements:**
* **Processor:** Intel Core i3 / AMD Ryzen 3 (or equivalent) and above.
* **RAM:** Minimum 4 GB (8 GB recommended).
* **Storage:** 500 MB of free space.
* **Client Side:** Any device (Mobile, Tablet, Desktop) with a modern web browser and a working camera (for QR scanning and photo uploads).

**Software Requirements:**
* **Operating System:** Windows, macOS, or Linux.
* **Backend Framework:** Python 3.10+ with Django 4.2.
* **Database:** SQLite (for local development) / PostgreSQL (for production via Supabase).
* **Blockchain Integration:** Web3.py connecting to Ethereum Sepolia Testnet.
* **Other Libraries:** qrcode (for QR generation), ReportLab (for PDF generation), Haversine (for distance calculation).

## 7. Design Phase (2 Main Diagrams)

Below are the textual explanations and structure for two main diagrams you can draw or present in your exam.

### Diagram 1: System Architecture & Workflow Diagram
*(You can draw this as a flowchart showing the step-by-step process)*
* **Block 1 (Donor):** Creates Food Listing (Type, Quantity, Expiry).
* **Arrow to Block 2:** Triggers AI Matching Engine.
* **Block 2 (AI Engine):** Filters by 25km radius -> Calculates Proximity Score (40%) + Need Score (40%) + Capacity Score (20%).
* **Arrow to Block 3:** Assigns Match.
* **Block 3 (Charity):** Receives Notification -> Accepts Match on Dashboard.
* **Arrow to Block 4:** Generates Secure QR Code.
* **Block 4 (Physical Pickup):** Charity visits Donor -> Donor scans Charity's QR Code -> Handoff confirmed.
* **Arrow to Block 5:** Delivery to final location.
* **Block 5 (Verification & Blockchain):** Charity uploads proof photo -> System records hash on Ethereum -> Generates PDF Receipt for both parties.

### Diagram 2: Use Case Diagram
*(You can draw this with stick figures for Actors and ovals for Use Cases)*
* **Actor 1: Donor**
  * Use Cases: Register/Login, Create Food Listing, View Dashboard Stats, Scan QR to Confirm Pickup, Download Blockchain Receipt.
* **Actor 2: Charity**
  * Use Cases: Register/Login, View AI-Matched Donations, Accept/Reject Match, View 7-Day ML Demand Forecast, Upload Delivery Proof, Download Receipt.
* **Actor 3: Admin**
  * Use Cases: View Platform Impact Metrics, Monitor All Transactions, Manage Users.

## 8. Future Enhancement
* **Mobile Application:** Developing dedicated Android and iOS native applications to make on-the-go QR scanning and photo uploading even easier.
* **Live GPS Tracking:** Integrating live delivery tracking so donors can see the food in transit to the charity location in real-time.
* **Gamification & Leaderboards:** Introducing a points system and badges for top donors to encourage more corporate and restaurant participation.
* **Wider Blockchain Mainnet:** Moving from the Sepolia Testnet to a low-cost Layer 2 Mainnet (like Polygon) for production-grade legal verification.

## 9. Conclusion
FoodWasteChain successfully bridges the gap between food surplus and food scarcity using modern technology. By automating the logistical nightmare of matching donors to NGOs through AI, and by enforcing strict trust and transparency through HMAC-signed QR codes and Ethereum blockchain records, the platform provides a highly scalable, zero-cost solution to combat global food waste. Ultimately, it ensures that perfectly good food feeds people instead of landfills, while giving donors the verifiable proof they deserve.
