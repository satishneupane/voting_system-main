# MySQL Setup Instructions for Voting System

## Quick Start with Docker (Recommended)

The easiest way to get MySQL running is with Docker:

```powershell
# Build and start all services
docker-compose up --build

# On first run, this will:
# - Download MySQL 8.0 image
# - Create voting_system database
# - Create voting_user with appropriate permissions
# - Start the Django web server
# - Run migrations automatically
```

Access the application at: **http://localhost:8000**

## Manual MySQL Setup (Local Development)

If you prefer to install MySQL locally:

### 1. Install MySQL

**Windows:**

- Download from: https://dev.mysql.com/downloads/mysql/
- Run installer and follow setup wizard
- Note your root password

### 2. Create Database and User

Open MySQL command line:

```bash
mysql -u root -p
```

Enter your root password, then run:

```sql
-- Create database
CREATE DATABASE voting_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'voting_user'@'localhost' IDENTIFIED BY 'voting_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON voting_system.* TO 'voting_user'@'localhost';
FLUSH PRIVILEGES;

-- Verify
SHOW GRANTS FOR 'voting_user'@'localhost';
```

### 3. Configure .env file

Copy `.env.example` to `.env` and verify settings:

```env
DB_NAME=voting_system
DB_USER=voting_user
DB_PASSWORD=voting_password
DB_HOST=localhost
DB_PORT=3306
```

### 4. Run Migrations

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 5. Start Development Server

```powershell
python manage.py runserver
```

Visit: **http://localhost:8000**

## Troubleshooting

### Test MySQL Connection

```powershell
mysql -u voting_user -p -h localhost voting_system
```

### View Docker Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f db
docker-compose logs -f web
```

### Rebuild Docker Container

```powershell
docker-compose down -v
docker-compose up --build
```

### Reset Database

**Docker:**

```powershell
docker-compose down -v  # Removes volumes
docker-compose up       # Recreates fresh database
```

**Local MySQL:**

```sql
DROP DATABASE voting_system;
CREATE DATABASE voting_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then run migrations again.

## Environment Variables Reference

| Variable      | Default                 | Description       |
| ------------- | ----------------------- | ----------------- |
| DB_NAME       | voting_system           | Database name     |
| DB_USER       | voting_user             | MySQL username    |
| DB_PASSWORD   | voting_password         | MySQL password    |
| DB_HOST       | db (Docker) / localhost | Database host     |
| DB_PORT       | 3306                    | MySQL port        |
| DEBUG         | True                    | Django debug mode |
| ALLOWED_HOSTS | localhost,127.0.0.1     | Allowed domains   |

## Database Details

- **Engine**: MySQL 8.0
- **Charset**: utf8mb4 (supports emojis and special characters)
- **Default Port**: 3306
- **Volume** (Docker): `mysql_data` (persists data between restarts)
