CREATE DATABASE IF NOT EXISTS dermosphere_db;
USE dermosphere_db;

-- 1. Roles Entity Table
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- 2. Users Entity Table (Handles both Patients and Doctors)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Joins Table for User-to-Role Relationship (RBAC Core)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- 4. Scan Records Table (Stores metadata and coordinates responses from the AI Microservice)
CREATE TABLE IF NOT EXISTS scan_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_file_path VARCHAR(555) NOT NULL,
    predicted_class VARCHAR(20),
    confidence_score DOUBLE,
    triage_tier VARCHAR(20) NOT NULL DEFAULT 'STANDARD', -- HIGH vs STANDARD sorting key
    heatmap_path VARCHAR(555),
    doctor_feedback VARCHAR(20) DEFAULT 'PENDING',       -- AGREE, DISAGREE, PENDING loops
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Seed Essential Roles into the System Topology
INSERT IGNORE INTO roles (name) VALUES ('ROLE_PATIENT');
INSERT IGNORE INTO roles (name) VALUES ('ROLE_DOCTOR');

-- Inject the God-Level Admin Role
INSERT IGNORE INTO roles (name) VALUES ('ROLE_ADMIN');

-- Expand the scan_records table to track longitudinal disease metrics and structural depth
ALTER TABLE scan_records
ADD COLUMN disease_onset_date DATE,
ADD COLUMN severity_score DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN skin_layers_penetrated INT DEFAULT 1,
ADD COLUMN structural_analysis_data JSON;

-- Create an Admin Audit table to track Developer Mode access
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    action_type VARCHAR(50),
    target_file VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id)
);