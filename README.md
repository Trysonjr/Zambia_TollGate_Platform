# Integrated Automated Self-Service Tollgate & Management Platform for Zambia

> **Academic Prototype — 30% Functional Implementation**  
> **Target Context:** Republic of Zambia &bull; National Road Fund Agency (NRFA) & Road Transport and Safety Agency (RTSA)

---

## 1. Project Overview & Problem Statements

Manual toll collection across Zambia’s national highway network (e.g. Great East Road, Great North Road, and Kafue Corridor) causes severe vehicular congestion, teller bottlenecks, and revenue reconciliation delays. This academic prototype provides a functional proof-of-concept demonstrating a unified, self-service automated tolling ecosystem solving two interconnected problems:

- **Problem Statement 1 — Automated Self-Service Tollgate:**  
  Automates vehicle identification (simulated ANPR optical camera & RFID transponder scan), dynamic toll fee calculation, instant balance verification/deduction (with Mobile Money fallback), automated visual boom barrier state control (CLOSED &rarr; OPEN &rarr; CLOSED), and immutable transaction recording.
- **Problem Statement 2 — Mobile Toll Account & Central Management Platform:**  
  Provides motorists with a self-service web portal to manage prepaid toll accounts, register vehicles, and simulate mobile wallet top-ups (Airtel Money, MTN MoMo, Zamtel Kwacha); provides transport administrators with executive analytics (revenue, traffic volume, plaza breakdown) and forensic audit logging.

---

## 2. 30% Functional Implementation Rule

This project adheres strictly to the **30% functional core rule**. Core functionality is **genuinely operational**; future modules are visually integrated as architectural blueprints.

### ✅ What Constitutes the Working 30% Core:
1. **Database Persistence:** MySQL 8.0/9.0 relational schema with constraints, foreign keys, and automatic zero-crash fallback engine.
2. **Motorist Authentication:** User registration, session state management, and scrypt password hashing.
3. **Vehicle Fleet Registration:** Vehicle plate creation, categorization, and unique RFID/E-Tag association.
4. **Prepaid Toll Accounts:** Real-time balance ledger in Zambian Kwacha (ZMW).
5. **Simulated ANPR Detection:** Optical plate recognition simulation with confidence scoring.
6. **Simulated RFID / E-Tag Interrogation:** Radio-frequency transponder interrogation.
7. **Statutory Toll Tariff Engine:** Automatic Zambian pricing:
   - *Light Vehicle:* **K20.00**
   - *Medium Vehicle:* **K50.00**
   - *Heavy Vehicle:* **K100.00**
   - *Abnormal Load:* **K250.00**
8. **Dual-Path Payment Engine:**
   - *Path A (E-Tag):* Automatic deduction from available balance.
   - *Path B (Mobile Money Fallback):* Instant simulated checkout via Airtel Money, MTN MoMo, or Zamtel Kwacha when balance is insufficient or vehicle is unregistered.
9. **Visual Boom Barrier Simulation:** Animated 90-degree boom arm, traffic light logic (Red &harr; Green), Web Audio API acoustic cues, and 4-second automatic reset timer.
10. **Transaction Ledger:** Stored in database with audit references, timestamps, and printable receipts.
11. **Admin Intelligence Dashboard:** Real-time KPI counters and interactive Chart.js visualizations.
12. **Audit Logging:** System-wide traceability recording registrations, funding, barrier triggers, and logins.

### 🕒 What Constitutes the 70% Future Scope (Clearly Labelled in UI):
All 18 planned modules appear in the dedicated **System Modules** view labelled `[Prototype / Future Implementation]`:
- Real physical ANPR cameras (Hikvision/Dahua optical streams)
- Real UHF/DSRC RFID gantry antennas
- Industrial PLC/microcontroller relay wiring & ground inductive loops
- Live telco API integration (Airtel B2B, MTN MoMo Open API, Zamtel Gateway)
- National RTSA e-ZamTIS electronic account sync
- Dynamic EMVCo QR-code displays
- Distributed edge offline database sync
- FIPS 140-2 Hardware Security Modules (HSM)
- Country-wide multi-plaza deployment across all 10 provinces
- Smart Zambia Government Cloud (G-Cloud) hosting
- SMPP SMS notification gateways
- Cross-platform Flutter mobile application
- AI-powered axle counting & predictive congestion analytics
- National Operations Control Centre (NOCC) video wall
- Police Service stolen vehicle blacklist interception

---

## 3. Technology Stack

- **Backend:** Python 3.11+ &bull; Flask 3.1 &bull; Flask-SQLAlchemy 3.1 &bull; Werkzeug Security
- **Database:** MySQL 9.0 / 8.0 (PyMySQL driver) with automated SQLite fallback engine
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Font Awesome 6
- **Visuals & Charts:** Chart.js, CSS Keyframe Boom Barrier, Web Audio API Sound Synthesizer
- **Architecture:** Modular Flask Blueprints (`auth`, `simulation`, `motorist`, `admin`, `modules`, `api`)

---

## 4. Installation & Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Optional: MySQL Server (if using MySQL; otherwise, the built-in fallback runs automatically)

### Step 1: Open the Project Directory
```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\zambia_tollgate_platform
```

### Step 2: Install Python Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Initialize Database & Seed Data
Run the database bootstrapper:
```powershell
python init_db.py
```
*This command creates all tables, seeds the 7 national Zambian toll plazas, the default administrator, and preloads demo motorists with vehicles and balances.*

### Step 4: Run the Application
```powershell
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

---

## 5. Default Demonstration Credentials

| Role | Email | Password | Initial State / Demo Assets |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@tollgate.gov.zm` | `Admin@123` | Full access to KPIs, Plaza Charts, and Audit Logs |
| **Demo Motorist 1** | `motorist@test.zm` | `Motorist@123` | **Vehicle:** `ABC 1234` &bull; **E-Tag:** `TAG-001` &bull; **Balance:** **K150.00** |
| **Demo Motorist 2** | `kondwani@test.zm` | `Motorist@123` | **Vehicle:** `BLZ 8899` &bull; **E-Tag:** `TAG-002` &bull; **Low Balance:** **K15.00** |

*Note: Quick-fill buttons are integrated on the Login page and Simulation page for rapid panel presentation.*

---

## 6. Official 21-Step Panel Demonstration Script

The platform is designed to execute this exact demonstration sequence:

1. Navigate to **Tollgate Simulation** (`/simulation`).
2. Click the preset: **`ABC 1234` (Light Vehicle, K150 Balance)**.
3. Select **Lusaka East Toll Plaza**, **Lane 1**.
4. Click **`Vehicle Arrives`**.
5. Observe the simulated **ANPR camera scanline** recognize plate `ABC 1234` (98.4% confidence).
6. Observe the system retrieve the registered toll account (`NRFA-ACC-1001`), owner (`Chileshe Mwewa`), and windshield E-Tag (`TAG-001`).
7. Observe automatic toll calculation: **K20.00** statutory fee.
8. Click **`Simulate RFID/E-Tag Scan`** to confirm windshield transponder active status.
9. Click **`Verify & Deduct Toll Fee (E-Tag)`**.
10. The system checks balance (**K150.00 &ge; K20.00**), deducts **K20.00**, leaving **K130.00**.
11. Observe the notification: **"Payment Successful!"**.
12. Observe the software boom barrier physical simulation:
    - Arm rotates smoothly from **CLOSED (0&deg;) &rarr; OPEN (-85&deg;)**.
    - Traffic light turns **Green**.
    - Audio clearance chime plays.
13. After 4 seconds, the barrier resets from **OPEN &rarr; CLOSED** and traffic light returns to **Red**.
14. Navigate to **Transactions** (`/transactions`) to see the newly generated crossing in the ledger.
15. Click the receipt icon on the transaction to display the printable **NRFA Toll Crossing Slip**.
16. Log in as motorist **`motorist@test.zm`** (using the one-click demo button).
17. Open **Toll Account** (`/motorist/dashboard`) to verify the balance has updated to **K130.00**.
18. Click **`Fund Toll Account`**, enter **K100.00**, select **Airtel Money**, and click **`Add Funds`**. Verify the balance increases to **K230.00**.
19. Return to **Tollgate Simulation**, select preset **`BLZ 8899` (Medium Vehicle, K50 fee)**. Click **`Vehicle Arrives`**.
20. Observe the system detect **Insufficient Balance** (K15.00 available < K50.00 required) and present **`Pay Using Mobile Money`**. Complete simulated mobile payment; observe the barrier open.
21. Log in as Administrator (**`admin@tollgate.gov.zm`**). Review updated revenue and plaza volume in **Admin Dashboard**, and inspect the immutable trail in **Audit Logs**.

---

## 7. Automated Testing Suite

To run the automated test suite verifying all 10 core test cases:
```powershell
python -m unittest tests/test_tollgate.py
```
All tests validate tariff calculation, balance deductions, mobile money fallback, and authentication.
