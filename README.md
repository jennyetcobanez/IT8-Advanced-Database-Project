# IT8-Advanced-Database-Project
# Barangay Health Appointment and Management System

IT8 Advanced Database Project / Final Drill
Authors: Mark Lorince Lloyd L. Cañon, Jenny B. Etcobanez, Joshua Cantor

A web-based system where residents request health appointments, register for health programs, and read announcements. Health workers/administrators manage residents, appointments, medical records, medicines, prescriptions, programs, registrations, and announcements.

**Stack:** MySQL 8 (database) + Python Flask (backend) + HTML/CSS pages rendered by Flask (frontend)

## Repository contents
| Path | Purpose |
|---|---|
| `database/01_schema.sql` | Creates the database, 9 tables, keys, constraints, triggers, and the view |
| `database/seed_data.py` | Generates the sample data (45 rows per table) |
| `database/02_seed_data.sql` | Generated sample data |
| `database/03_queries.sql` | CRUD, join, GROUP BY/HAVING, subquery, transaction, view, and constraint tests |
| `app/app.py` | Backend (routes, database access, transaction) |
| `app/templates/`, `app/static/` | Frontend pages and styling |
| `docs/` | Business rules, sequence diagrams, video script, deliverable templates |

## Requirements
- MySQL 8.0.16 or later
- Python 3.9 or later

## Setup and run
1. Create the database and load the data:
```bash
mysql -u root -p < database/01_schema.sql
mysql -u root -p < database/02_seed_data.sql
```
2. Install and start the app:
```bash
cd app
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
set DB_PASSWORD=your_mysql_password      # Windows   (Mac/Linux: export DB_PASSWORD=...)
python app.py
```
3. Open http://127.0.0.1:5000

Optional environment variables: `DB_HOST` (localhost), `DB_PORT` (3306), `DB_USER` (root), `DB_PASSWORD`, `DB_NAME` (barangay_health_system), `SECRET_KEY`.

## Demo accounts (password for all: `password123`)
- Residents: `resident01` to `resident45`
- Health workers: `worker01` to `worker41` (`worker42` to `worker45` are Inactive and cannot log in)

## Where each requirement is shown
| Requirement | Where |
|---|---|
| CRUD | Appointments, Residents, Medicines, Programs, Announcements pages |
| Multi-table join | Reports page (also Prescriptions and Medical records pages) |
| GROUP BY + HAVING | Reports page |
| Subquery | Reports page |
| Transaction | New prescription (saves prescription and reduces stock together) |
| View | `vw_appointment_details` (Appointments and Reports pages) |
| Constraint / business rule test | Constraint tests page (health worker menu) |

## Known limitations
- Passwords use plain SHA-256 (to match the seed data). A real system should use bcrypt or argon2.
- No CSRF protection and no HTTPS (demo only).
- The app was smoke-tested for page rendering, but your team should test every feature against MySQL before submitting.

See `docs/Business_Rules_and_Deliverables.md` for business rules and the video plan.
