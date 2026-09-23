# Database Setup & Configuration Guide

This platform supports **MySQL 8.0 / 9.0** as the primary enterprise database engine, with an intelligent zero-configuration fallback to local SQLite for seamless academic demonstrations.

---

## 1. Automated Setup (Recommended)

The easiest way to initialize all tables, foreign keys, and seed data is to use the Python initialization script:

```powershell
python init_db.py
```

### What this script does:
1. Detects your active database engine (MySQL if configured; SQLite if MySQL credentials are not yet set).
2. Generates all 7 relational tables with indexes and foreign key constraints.
3. Seeds the 7 operational Zambian national toll plazas:
   - *Lusaka East Toll Plaza* (Great East Road, Chongwe District)
   - *Shimabala Toll Plaza* (Great North/Kafue Road, Kafue)
   - *Katuba Toll Plaza* (Great North Road, Chibombo)
   - *Chongwe Toll Plaza* (Great East Road, Chongwe)
   - *Manyumbi Toll Plaza* (Great North Road, Kapiri Mposhi)
   - *Michael Chilufya Sata Plaza* (Ndola-Kitwe Dual Carriageway)
   - *Kafulafuta Toll Plaza* (Kapiri-Ndola Road, Masaiti)
4. Creates default Administrator (`admin@tollgate.gov.zm` / `Admin@123`).
5. Creates demo motorists with pre-linked vehicles (`ABC 1234`, `BLZ 8899`, `ALZ 5522`) and balances (**K150.00** and **K15.00**).
6. Seeds initial baseline transactions and system initialization audit logs.

---

## 2. Manual MySQL Setup via `schema.sql`

If you prefer to import directly into your MySQL server via MySQL Command Line or MySQL Workbench:

### Step 1: Log in to MySQL
```powershell
& "C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe" -u root -p
```
*(Enter your MySQL root password when prompted)*

### Step 2: Execute `schema.sql`
Inside the MySQL shell:
```sql
SOURCE C:/Users/HP/.gemini/antigravity/scratch/zambia_tollgate_platform/schema.sql;
```
Or directly from PowerShell:
```powershell
Get-Content schema.sql | & "C:\Program Files\MySQL\MySQL Server 9.0\bin\mysql.exe" -u root -p
```

---

## 3. Configuring Database Credentials (`.env`)

Create a `.env` file in the project root (or copy `.env.example` to `.env`):

```ini
# Flask Secret
SECRET_KEY=nrfa-zambia-tollgate-secret-key-2026

# MySQL Connection Details
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DB=zambia_tollgate
```

Once configured, restart the application with:
```powershell
python app.py
```
The console will display:
```
Successfully connected to MySQL database: zambia_tollgate
Active Database: MySQL 9.0
```

---

## 4. Entity-Relationship (ER) Schema Overview

```
 [ users ]
    │ 1
    │
    ├───< 1:1 >─── [ toll_accounts ]
    │                     │ 1
    │                     └───< 1:N >─── [ payments ]
    │
    └───< 1:N >─── [ vehicles ]
                          │ 
                          ▼
                   [ transactions ] ───< N:1 >─── [ tollgates ]
                          ▲
                          │ (Cross-Reference)
                   [ audit_logs ]
```

### Table Specifications:

| Table | Description | Key Fields |
| :--- | :--- | :--- |
| `users` | System actors (motorists & administrators) | `id`, `email`, `role`, `password_hash`, `phone` |
| `toll_accounts` | Motorist prepaid toll wallets | `id`, `user_id`, `account_number`, `balance`, `status` |
| `vehicles` | Motorist registered vehicles | `id`, `user_id`, `registration_number`, `vehicle_type`, `rfid_tag` |
| `tollgates` | Gazetted Zambian toll plazas | `id`, `name`, `code`, `location`, `province`, `lanes_count` |
| `transactions` | Official toll crossing event ledger | `id`, `transaction_ref`, `vehicle_reg`, `amount`, `payment_method`, `status` |
| `payments` | Wallet top-up funding log | `id`, `account_id`, `amount`, `provider`, `reference`, `status` |
| `audit_logs` | Immutable system security trail | `id`, `action`, `actor_email`, `reference_id`, `details`, `timestamp` |
