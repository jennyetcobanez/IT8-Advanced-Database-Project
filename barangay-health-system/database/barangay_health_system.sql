-- Barangay Health Appointment and Management System
-- IT8 Advanced Database Project
-- DBMS: MySQL 8.0+

CREATE DATABASE barangay_health_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE barangay_health_system;

-- 1. Residents
CREATE TABLE Residents (
    resident_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    birth_date     DATE         NOT NULL,
    contact_number CHAR(11)     NOT NULL,
    address        VARCHAR(255) NOT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username       VARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    CONSTRAINT uq_resident_contact  UNIQUE (contact_number),
    CONSTRAINT uq_resident_username UNIQUE (username),
    CONSTRAINT chk_resident_contact CHECK (contact_number REGEXP '^09[0-9]{9}$')
) ENGINE=InnoDB;

-- 2. Health Workers
CREATE TABLE Health_Workers (
    worker_id      INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    position       VARCHAR(60)  NOT NULL,
    contact_number CHAR(11)     NOT NULL,
    status         ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    username       VARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    CONSTRAINT uq_worker_contact  UNIQUE (contact_number),
    CONSTRAINT uq_worker_username UNIQUE (username),
    CONSTRAINT chk_worker_contact CHECK (contact_number REGEXP '^09[0-9]{9}$')
) ENGINE=InnoDB;

-- 3. Appointments
CREATE TABLE Appointments (
    appointment_id   INT AUTO_INCREMENT PRIMARY KEY,
    appointment_date DATE        NOT NULL,
    start_time       TIME        NOT NULL,
    end_time         TIME        NOT NULL,
    reason           VARCHAR(255) NOT NULL,
    status           ENUM('Pending','Approved','Completed','Cancelled','Rejected')
                     NOT NULL DEFAULT 'Pending',
    resident_id      INT NOT NULL,
    worker_id        INT NOT NULL,
    CONSTRAINT fk_appt_resident FOREIGN KEY (resident_id) REFERENCES Residents(resident_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appt_worker FOREIGN KEY (worker_id) REFERENCES Health_Workers(worker_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_appt_time CHECK (end_time > start_time),
    -- a worker cannot be booked twice for the same slot
    CONSTRAINT uq_worker_slot UNIQUE (worker_id, appointment_date, start_time)
) ENGINE=InnoDB;

-- 4. Medical Records
CREATE TABLE Medical_Records (
    record_id   INT AUTO_INCREMENT PRIMARY KEY,
    visit_date  DATE         NOT NULL,
    diagnosis   VARCHAR(255) NOT NULL,
    notes       TEXT,
    resident_id INT NOT NULL,
    worker_id   INT NOT NULL,
    CONSTRAINT fk_rec_resident FOREIGN KEY (resident_id) REFERENCES Residents(resident_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_rec_worker FOREIGN KEY (worker_id) REFERENCES Health_Workers(worker_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. Medicines
CREATE TABLE Medicines (
    medicine_id         INT AUTO_INCREMENT PRIMARY KEY,
    medicine_name       VARCHAR(100) NOT NULL,
    category            VARCHAR(60)  NOT NULL,
    quantity            INT          NOT NULL DEFAULT 0,
    availability_status ENUM('Available','Low Stock','Out of Stock') NOT NULL DEFAULT 'Out of Stock',
    CONSTRAINT uq_medicine_name UNIQUE (medicine_name),
    CONSTRAINT chk_medicine_qty CHECK (quantity >= 0)
) ENGINE=InnoDB;

-- 6. Prescriptions
CREATE TABLE Prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    quantity        INT          NOT NULL,
    instructions    VARCHAR(255) NOT NULL,
    prescribed_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resident_id     INT NOT NULL,
    worker_id       INT NOT NULL,
    medicine_id     INT NOT NULL,
    record_id       INT NOT NULL,
    CONSTRAINT fk_presc_resident FOREIGN KEY (resident_id) REFERENCES Residents(resident_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_presc_worker FOREIGN KEY (worker_id) REFERENCES Health_Workers(worker_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_presc_medicine FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_presc_record FOREIGN KEY (record_id) REFERENCES Medical_Records(record_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_presc_qty CHECK (quantity > 0)
) ENGINE=InnoDB;

-- 7. Health Programs
CREATE TABLE Health_Programs (
    program_id   INT AUTO_INCREMENT PRIMARY KEY,
    program_name VARCHAR(100) NOT NULL,
    description  TEXT,
    schedule     DATETIME     NOT NULL,
    status       ENUM('Upcoming','Ongoing','Completed','Cancelled') NOT NULL DEFAULT 'Upcoming',
    worker_id    INT NOT NULL,
    CONSTRAINT uq_program_name UNIQUE (program_name),
    CONSTRAINT fk_prog_worker FOREIGN KEY (worker_id) REFERENCES Health_Workers(worker_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 8. Program Registrations
CREATE TABLE Program_Registrations (
    registration_id INT AUTO_INCREMENT PRIMARY KEY,
    registered_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('Registered','Attended','Cancelled') NOT NULL DEFAULT 'Registered',
    resident_id     INT NOT NULL,
    program_id      INT NOT NULL,
    CONSTRAINT fk_reg_resident FOREIGN KEY (resident_id) REFERENCES Residents(resident_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reg_program FOREIGN KEY (program_id) REFERENCES Health_Programs(program_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    -- a resident can register only once per program
    CONSTRAINT uq_resident_program UNIQUE (resident_id, program_id)
) ENGINE=InnoDB;

-- 9. Announcements
CREATE TABLE Announcements (
    announcement_id INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(150) NOT NULL,
    content         TEXT         NOT NULL,
    date_posted     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    worker_id       INT NOT NULL,
    CONSTRAINT fk_ann_worker FOREIGN KEY (worker_id) REFERENCES Health_Workers(worker_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

DELIMITER $$

CREATE TRIGGER trg_resident_birth_bi BEFORE INSERT ON Residents
FOR EACH ROW
BEGIN
    IF NEW.birth_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Birth date cannot be in the future.';
    END IF;
END$$

CREATE TRIGGER trg_resident_birth_bu BEFORE UPDATE ON Residents
FOR EACH ROW
BEGIN
    IF NEW.birth_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Birth date cannot be in the future.';
    END IF;
END$$

CREATE TRIGGER trg_appt_worker_active_bi BEFORE INSERT ON Appointments
FOR EACH ROW
BEGIN
    IF (SELECT status FROM Health_Workers WHERE worker_id = NEW.worker_id) <> 'Active' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Appointment cannot be assigned to an inactive health worker.';
    END IF;
END$$

CREATE TRIGGER trg_medicine_status_bi BEFORE INSERT ON Medicines
FOR EACH ROW
BEGIN
    SET NEW.availability_status = CASE
        WHEN NEW.quantity = 0  THEN 'Out of Stock'
        WHEN NEW.quantity <= 20 THEN 'Low Stock'
        ELSE 'Available' END;
END$$

CREATE TRIGGER trg_medicine_status_bu BEFORE UPDATE ON Medicines
FOR EACH ROW
BEGIN
    SET NEW.availability_status = CASE
        WHEN NEW.quantity = 0  THEN 'Out of Stock'
        WHEN NEW.quantity <= 20 THEN 'Low Stock'
        ELSE 'Available' END;
END$$

CREATE TRIGGER trg_presc_check_bi BEFORE INSERT ON Prescriptions
FOR EACH ROW
BEGIN
    IF NEW.quantity > (SELECT quantity FROM Medicines WHERE medicine_id = NEW.medicine_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Prescription quantity exceeds available medicine stock.';
    END IF;
    IF NEW.resident_id <> (SELECT resident_id FROM Medical_Records WHERE record_id = NEW.record_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Prescription resident does not match the medical record resident.';
    END IF;
END$$

DELIMITER ;

CREATE VIEW vw_appointment_details AS
SELECT a.appointment_id, a.appointment_date, a.start_time, a.end_time, a.reason, a.status,
       r.resident_id, r.full_name AS resident_name,
       w.worker_id,   w.full_name AS worker_name, w.position
FROM Appointments a
JOIN Residents r      ON r.resident_id = a.resident_id
JOIN Health_Workers w ON w.worker_id   = a.worker_id;
