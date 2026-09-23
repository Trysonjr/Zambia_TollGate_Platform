-- ====================================================================
-- Integrated Automated Self-Service Tollgate & Management Platform
-- Republic of Zambia - National Road Fund Agency (NRFA) Academic Simulation
-- Target Database: MySQL 8.0 / 9.0 (Compatible with MariaDB)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS `zambia_tollgate` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `zambia_tollgate`;

-- Drop existing tables to allow clean re-initialization
DROP TABLE IF EXISTS `audit_logs`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `transactions`;
DROP TABLE IF EXISTS `vehicles`;
DROP TABLE IF EXISTS `toll_accounts`;
DROP TABLE IF EXISTS `tollgates`;
DROP TABLE IF EXISTS `users`;

-- 1. Users Table (Administrators and Motorists)
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('motorist', 'admin') NOT NULL DEFAULT 'motorist',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Toll Accounts Table (Prepaid Wallet per Motorist)
CREATE TABLE `toll_accounts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `account_number` VARCHAR(30) NOT NULL UNIQUE,
    `balance` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `status` ENUM('ACTIVE', 'SUSPENDED', 'CLOSED') NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_toll_accounts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Vehicles Table
CREATE TABLE `vehicles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `registration_number` VARCHAR(20) NOT NULL UNIQUE,
    `vehicle_type` ENUM('Light Vehicle', 'Medium Vehicle', 'Heavy Vehicle', 'Abnormal Load') NOT NULL DEFAULT 'Light Vehicle',
    `make_model` VARCHAR(100) DEFAULT 'Unspecified',
    `rfid_tag` VARCHAR(50) NOT NULL UNIQUE,
    `status` ENUM('ACTIVE', 'BLACKLISTED', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_vehicles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    INDEX `idx_vehicles_reg` (`registration_number`),
    INDEX `idx_vehicles_rfid` (`rfid_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Tollgates Table (Zambian National Toll Plazas)
CREATE TABLE `tollgates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `location` VARCHAR(150) NOT NULL,
    `province` VARCHAR(50) NOT NULL,
    `lanes_count` INT NOT NULL DEFAULT 4,
    `status` ENUM('OPERATIONAL', 'MAINTENANCE', 'OFFLINE') NOT NULL DEFAULT 'OPERATIONAL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Transactions Table (Toll Crossing Records)
CREATE TABLE `transactions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `transaction_ref` VARCHAR(50) NOT NULL UNIQUE,
    `vehicle_reg` VARCHAR(20) NOT NULL,
    `vehicle_type` VARCHAR(50) NOT NULL,
    `tollgate_id` INT NOT NULL,
    `lane_number` VARCHAR(20) NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `payment_method` VARCHAR(50) NOT NULL,
    `status` ENUM('SUCCESSFUL', 'INSUFFICIENT_FUNDS', 'FAILED') NOT NULL DEFAULT 'SUCCESSFUL',
    `balance_before` DECIMAL(10, 2) DEFAULT NULL,
    `balance_after` DECIMAL(10, 2) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_transactions_tollgate` FOREIGN KEY (`tollgate_id`) REFERENCES `tollgates` (`id`) ON DELETE RESTRICT,
    INDEX `idx_tx_reg` (`vehicle_reg`),
    INDEX `idx_tx_status` (`status`),
    INDEX `idx_tx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Payments Table (Account Top-ups & Mobile Money)
CREATE TABLE `payments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `account_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL,
    `provider` VARCHAR(50) NOT NULL,
    `reference` VARCHAR(60) NOT NULL UNIQUE,
    `status` ENUM('SUCCESSFUL', 'PENDING', 'FAILED') NOT NULL DEFAULT 'SUCCESSFUL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_payments_account` FOREIGN KEY (`account_id`) REFERENCES `toll_accounts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Audit Logs Table (Central Integrity & System Actions)
CREATE TABLE `audit_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `action` VARCHAR(80) NOT NULL,
    `actor_email` VARCHAR(120) NOT NULL,
    `reference_id` VARCHAR(60) DEFAULT NULL,
    `details` TEXT DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT '127.0.0.1',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_audit_action` (`action`),
    INDEX `idx_audit_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ====================================================================
-- SEED DATA (Zambian Plazas, Demo Accounts, and Vehicles)
-- ====================================================================

-- Insert Zambian Toll Plazas
INSERT INTO `tollgates` (`name`, `code`, `location`, `province`, `lanes_count`, `status`) VALUES
('Lusaka East Toll Plaza', 'TP-LUS-01', 'Great East Road, Chongwe District', 'Lusaka Province', 6, 'OPERATIONAL'),
('Shimabala Toll Plaza', 'TP-KAF-02', 'Great North/Kafue Road, Kafue', 'Lusaka Province', 4, 'OPERATIONAL'),
('Katuba Toll Plaza', 'TP-KAT-03', 'Great North Road, Chibombo', 'Central Province', 4, 'OPERATIONAL'),
('Chongwe Toll Plaza', 'TP-CHO-04', 'Great East Road, Chongwe', 'Lusaka Province', 4, 'OPERATIONAL'),
('Manyumbi Toll Plaza', 'TP-MAN-05', 'Great North Road, Kapiri Mposhi', 'Central Province', 4, 'OPERATIONAL'),
('Michael Chilufya Sata Plaza', 'TP-NDO-06', 'Ndola-Kitwe Dual Carriageway', 'Copperbelt Province', 6, 'OPERATIONAL'),
('Kafulafuta Toll Plaza', 'TP-KAF-07', 'Kapiri-Ndola Road, Masaiti', 'Copperbelt Province', 4, 'OPERATIONAL');

-- Passwords hashed using Werkzeug scrypt (compatible with werkzeug.security):
-- 'Admin@123' -> scrypt:32768:8:1$i86m7...
-- 'Motorist@123' -> scrypt:32768:8:1$k82d...
-- (Note: init_db.py generates standard compatible hashes via generate_password_hash)
