# FoodWasteChain - Project Diagrams

This document contains two visual diagrams that explain the entire project's architecture and the step-by-step workflow. You can view these diagrams using any Markdown viewer that supports Mermaid (like GitHub, VS Code, or online at [mermaid.live](https://mermaid.live)).

## 1. System Architecture Diagram
This diagram shows the main components of the FoodWasteChain platform and how they interact with each other.

```mermaid
flowchart TD
    %% Define Styles
    classDef client fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef server fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef ai fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef external fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef db fill:#ffebee,stroke:#d32f2f,stroke-width:2px;

    %% Nodes
    subgraph Clients["Client Interface (Frontend)"]
        DonorUI["Donor Dashboard<br/>(Web/Mobile)"]:::client
        CharityUI["Charity Dashboard<br/>(Web/Mobile)"]:::client
        AdminUI["Admin Panel"]:::client
    end

    subgraph Backend["Django Backend Server"]
        Router["URL Router & Views"]:::server
        
        subgraph CoreServices["Core Services"]
            Auth["Auth & Role Guard"]:::server
            QRService["QR Crypto Service<br/>(HMAC Signatures)"]:::server
            ReceiptService["PDF Receipt Gen"]:::server
        end
        
        subgraph Intelligence["AI & Location Layer"]
            AIMatch["AI Matching Engine<br/>(Proximity + Need + Capacity)"]:::ai
            MLForecast["ML Demand Forecast<br/>(Simple Moving Average)"]:::ai
        end
    end

    subgraph External["External Services & APIs"]
        OSRM["OSRM API<br/>(Real-Road Distance)"]:::external
        Blockchain["Ethereum Sepolia<br/>Testnet (Web3.py)"]:::external
        SMTP["Email SMTP<br/>(Notifications)"]:::external
    end

    subgraph Database["Data Layer"]
        DB[(Supabase PostgreSQL<br/>/ SQLite)]:::db
    end

    %% Relationships
    DonorUI -->|Create Listing, Scan QR| Router
    CharityUI -->|Accept Match, Upload Proof| Router
    AdminUI -->|View Metrics| Router

    Router <--> CoreServices
    Router <--> Intelligence
    
    Intelligence -->|Fetch Distance| OSRM
    CoreServices -->|Record Verification| Blockchain
    CoreServices -->|Send Alerts| SMTP

    CoreServices <--> DB
    Intelligence <--> DB
```

---

## 2. System Sequence Flow Diagram
This diagram illustrates the chronological step-by-step interaction between the Donor, the System, the Charity, and the Blockchain during a food donation lifecycle.

```mermaid
sequenceDiagram
    autonumber
    actor Donor
    participant System as AI Backend System
    actor Charity
    participant BC as Ethereum Blockchain

    %% Phase 1: Donation & AI Matching
    Donor->>System: Create Food Listing (Type, Qty, Expiry)
    System->>System: Run AI Matching Engine
    Note over System: 1. Filter charities within 25km<br/>2. Fetch OSRM Road Distance<br/>3. Calculate Need & Capacity Score
    System->>System: Assign best-ranked Charity
    System->>Charity: Email & Dashboard Notification
    
    %% Phase 2: Acceptance & QR Generation
    Charity->>System: Review and Accept Match
    System->>System: Generate HMAC-Signed QR Code
    System->>Donor: Notify Donor of Acceptance

    %% Phase 3: Physical Pickup (QR Security)
    Note over Donor, Charity: Physical Handoff at Donor's Location
    Charity->>Donor: Show Unique QR Code
    Donor->>System: Scan QR Code via App
    System->>System: Verify HMAC Cryptographic Signature
    System-->>Donor: Validate & Update Status to "Picked Up"

    %% Phase 4: Delivery & Blockchain Verification
    Note over Charity: Charity arrives at their own facility
    Charity->>System: Upload Delivery Confirmation Photo
    System->>BC: Create Transaction (Match ID, Food, Hash)
    BC-->>System: Return TX Hash / Etherscan URL
    
    %% Phase 5: Finalization & Receipts
    System->>System: Generate Branded PDF Receipt
    System->>Donor: Email Receipt with Blockchain Proof
    System->>Charity: Email Receipt & Update ML Forecast Data
```
