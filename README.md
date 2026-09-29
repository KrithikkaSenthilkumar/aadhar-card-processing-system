# AADHAR CARD PROCESSING SYSTEM

A beginner-friendly DBMS mini-project built using **Python Flask + MySQL**.

## Features

- Citizen registration
- Aadhaar application processing
- Document verification
- Application status checking
- Citizen search
- Aadhaar detail update requests
- Dynamic application reports
- Dynamic approved/pending/rejected counts
- Aadhaar card information through the existing database logic/trigger

## Project Structure

```text
AADHAR_CARD_PROCESSING_SYSTEM/
├── app.py
├── main.py
├── index.html
├── style.css
├── requirements.txt
├── aadhar_card_processing_system.sql
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10+ recommended
- MySQL Server
- MySQL database named `AADHAR_CARD_PROCESSING_SYSTEM`

## Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

## Database

The project uses these existing tables from the original DBMS project:

- `Citizen`
- `Application`
- `Verification`
- `Update_Request`
- `Aadhaar_Card`

The uploaded SQL file supplied with this project contains the existing `Aadhaar_Card` query. It is retained as supplied and is not replaced with an invented schema.

Check the database before running Flask:

```sql
USE AADHAR_CARD_PROCESSING_SYSTEM;
SHOW TABLES;
DESC Citizen;
DESC Application;
DESC Verification;
DESC Update_Request;
DESC Aadhaar_Card;
SHOW TRIGGERS;
```

## MySQL Configuration

For security, the GitHub version does **not** store the MySQL password in source code.

Set these environment variables before running:

### Windows PowerShell

```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="YOUR_MYSQL_PASSWORD"
$env:DB_NAME="AADHAR_CARD_PROCESSING_SYSTEM"
$env:FLASK_SECRET_KEY="aadhar-local-secret"
python app.py
```

### Windows Command Prompt

```cmd
set DB_HOST=localhost
set DB_USER=root
set DB_PASSWORD=YOUR_MYSQL_PASSWORD
set DB_NAME=AADHAR_CARD_PROCESSING_SYSTEM
set FLASK_SECRET_KEY=aadhar-local-secret
python app.py
```

## Run the Website

```bash
python app.py
```

Then open:

http://127.0.0.1:5000/

## Important

The Flask application does not manually create an `Aadhaar_Card` row after approval. It updates the `Application` and `Verification` records and leaves any existing database trigger/logic responsible for Aadhaar card creation.

Do not commit a real MySQL password to a public GitHub repository.
