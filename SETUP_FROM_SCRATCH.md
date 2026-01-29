# Django Voting System - Fresh Setup Guide

This guide will help you set up the Django Voting System backend on a new machine from scratch.

## Prerequisites

Before starting, ensure you have the following installed:

- **Git** - [Download](https://git-scm.com/download/win)
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **pip** - Usually comes with Python

Verify installations:

```powershell
git --version
python --version
pip --version
```

## Step 1: Clone the Repository

```powershell
git clone <your-repo-url>
cd voting_system
```

Replace `<your-repo-url>` with your actual GitHub repository URL.

## Step 2: Create Virtual Environment

```powershell
python -m venv .venv
```

## Step 3: Activate Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

## Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

This will install all required packages including Django, mysqlclient, and other dependencies.

## Step 5: Configure MySQL Database

### Option A: Local MySQL Installation

1. **Install MySQL**: Download from [mysql.com](https://www.mysql.com/downloads/)

2. **Create Database and User**:

   ```sql
   CREATE DATABASE voting_system;
   CREATE USER 'voting_user'@'localhost' IDENTIFIED BY 'voting_password';
   GRANT ALL PRIVILEGES ON voting_system.* TO 'voting_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Configure Environment Variables**:
   - Copy `.env.example` to `.env`
   - Update with your MySQL credentials if different:
   ```env
   DB_NAME=voting_system
   DB_USER=voting_user
   DB_PASSWORD=voting_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

### Option B: Docker (Recommended)

Use Docker Compose to run MySQL in a container:

```powershell
docker-compose up -d
```

This will:

- Start MySQL 8.0 container
- Create the database and user automatically
- Start the Django web server
- All environment variables are pre-configured

## Step 6: Run Migrations

```powershell
python manage.py migrate
```

This will create all necessary database tables in MySQL.

## Step 7: Create Superuser (Optional)

For admin access at `http://localhost:8000/admin/`:

```powershell
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

## Step 8: Start the Server

**Option A: Local Development (with local MySQL)**

```powershell
python manage.py runserver
```

**Option B: Docker (with containerized MySQL)**

```powershell
docker-compose up
```

Server will be available at: **http://127.0.0.1:8000/**

---

## Verification Checklist

- [ ] Git cloned successfully
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (Django, mysqlclient, requests, etc.)
- [ ] MySQL installed and running (or Docker configured)
- [ ] Database and user created
- [ ] `.env` file configured with correct credentials
- [ ] Migrations applied successfully
- [ ] Server started without errors
- [ ] Access `http://localhost:8000/` in browser
- [ ] Admin panel accessible at `http://localhost:8000/admin/`

## Common Issues & Solutions

### Issue: "No module named 'MySQLdb'"

**Solution:** Install mysqlclient:

```powershell
pip install mysqlclient==2.2.0
```

### Issue: "Access denied for user 'voting_user'@'localhost'"

**Solution:** Verify MySQL credentials in `.env` file match your MySQL setup:

```powershell
# Test MySQL connection
mysql -u voting_user -p -h localhost
```

Enter the password from your `.env` file.

### Issue: "Port 3306 already in use" (Docker)

**Solution:** Change port in `docker-compose.yml`:

```yaml
ports:
  - "3307:3306" # Use 3307 instead
```

### Issue: "Port 8000 already in use"

**Solution:** Run on a different port:

```powershell
python manage.py runserver 8001
```

Or in Docker:

```yaml
ports:
  - "8001:8000"
```

### Issue: "Cannot connect to MySQL" (Docker)

**Solution:** Ensure containers are running:

```powershell
docker-compose ps
docker-compose logs db
docker-compose up --build
```

### Issue: "InconsistentMigrationHistory"

**Solution:** Fresh database setup:

```powershell
# For local MySQL
mysql -u voting_user -p voting_system
DROP DATABASE voting_system;
CREATE DATABASE voting_system;
exit

python manage.py migrate
```

```powershell
# For Docker
docker-compose down -v
docker-compose up
```

## Project Structure

```
voting_system/
├── elections/                 # Main app
│   ├── models.py             # Database models
│   ├── views.py              # API views
│   ├── urls.py               # URL routing
│   └── admin.py              # Admin configuration
├── voting_system/            # Project settings
│   ├── settings.py           # Configuration
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI configuration
├── manage.py                 # Django management
├── db.sqlite3                # SQLite database (auto-created)
└── requirements.txt          # Python dependencies
```
