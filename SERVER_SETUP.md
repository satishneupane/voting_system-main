# Voting System - Server Setup & API Documentation

## 🚀 How to Run the Server

### Prerequisites
- Python 3.8+
- pip

### Step 1: Navigate to the Project
```powershell
cd "C:\Users\ideapad 3\Downloads\day1\voting_system"
```

### Step 2: Create Virtual Environment (if not already done)
```powershell
python -m venv .venv
```

### Step 3: Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install Django
```powershell
pip install django
```

### Step 5: Run Migrations (if needed)
```powershell
python manage.py migrate
```

### Step 6: Create Superuser (Optional - for admin access)
```powershell
python manage.py createsuperuser
```

### Step 7: Start the Server
```powershell
python manage.py runserver
```

The server will start at: **http://127.0.0.1:8000/**

---

## 📡 API Endpoints Documentation

### Base URL
```
http://localhost:8000/elections
```

---

## Authentication & Voter Registration

### 1. Register a New Voter
**POST** `/elections/api/voter/register/`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "province_id": 1,
  "district_id": 1,
  "electoral_area": 1
}
```

**Response (201):**
```json
{
  "success": "Voter registered successfully"
}
```

**Error Responses:**
- `400` - All fields required or user already exists
- `400` - Invalid province/district/electoral area

---

### 2. Get Voter Profile
**GET** `/elections/api/voter/profile/`

**Authentication:** Required (Login needed)

**Response (200):**
```json
{
  "id": 1,
  "username": "john@example.com",
  "email": "john@example.com",
  "province": {
    "id": 1,
    "name": "Ontario"
  },
  "district": {
    "id": 1,
    "name": "Toronto Centre"
  },
  "electoral_area": {
    "id": 1,
    "name": "Toronto Centre Electoral Area"
  }
}
```

---

## Candidates & Parties

### 3. Get Candidates (for user's electoral area)
**GET** `/elections/api/candidates/`

**Authentication:** Required

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Alice Smith"
  },
  {
    "id": 2,
    "name": "Bob Johnson"
  }
]
```

---

### 4. Get All Parties
**GET** `/elections/api/parties/`

**Authentication:** Not required

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Democratic Party",
    "symbol": "DP"
  },
  {
    "id": 2,
    "name": "Republican Party",
    "symbol": "RP"
  }
]
```

---

## Voting

### 5. Submit Vote (Generic)
**POST** `/elections/vote/submit/`

**Authentication:** Required

**Request Body (Form Data):**
- For FPTP (Candidate Vote):
  ```
  vote_type=FPTP
  candidate_id=1
  ```

- For PR (Party Vote):
  ```
  vote_type=PR
  party_id=1
  ```

**Response (201):**
```json
{
  "success": "Vote recorded successfully."
}
```

**Error Responses:**
- `401` - Authentication required
- `403` - Voting is closed or candidate not in electoral area
- `409` - Already voted

---

### 6. Submit Candidate Vote (Test Endpoint)
**GET** `/elections/test/vote/candidate/?candidate_id=1`

**Authentication:** Required

**Response (200):**
```json
{
  "status": "success",
  "vote_id": 5,
  "type": "FPTP"
}
```

---

### 7. Submit Party Vote (Test Endpoint)
**GET** `/elections/test/vote/party/?party_id=1`

**Authentication:** Required

**Response (200):**
```json
{
  "status": "success",
  "vote_id": 6,
  "type": "PR"
}
```

---

### 8. Test Candidate Validation
**GET** `/elections/test/validate/candidate/?candidate_id=1`

**Authentication:** Required

**Response (200/403):**
```json
{
  "status": "success",
  "message": "User is allowed to vote for this candidate."
}
```

---

### 9. Get Voting Context
**GET** `/elections/test/voting/context/`

**Authentication:** Required

**Response (200):**
```json
{
  "user_id": 1,
  "electoral_area": "Toronto Centre",
  "candidates": [...],
  "can_vote": true
}
```

---

## Results & Monitoring

### 10. Get FPTP Vote Results (Candidate Results)
**GET** `/elections/results/candidates/`

**Query Parameters (Optional):**
- `province_id` - Filter by province
- `district_id` - Filter by district
- `electoral_area_id` - Filter by electoral area

**Response (200):**
```json
[
  {
    "candidate__id": 1,
    "candidate__name": "Alice Smith",
    "electoral_area__name": "Toronto Centre",
    "total_votes": 250
  },
  {
    "candidate__id": 2,
    "candidate__name": "Bob Johnson",
    "electoral_area__name": "Toronto Centre",
    "total_votes": 180
  }
]
```

---

### 11. Get PR Vote Results (Party Results)
**GET** `/elections/results/parties/`

**Query Parameters (Optional):**
- `province_id` - Filter by province
- `district_id` - Filter by district

**Response (200):**
```json
[
  {
    "party__id": 1,
    "party__name": "Democratic Party",
    "total_votes": 5000
  },
  {
    "party__id": 2,
    "party__name": "Republican Party",
    "total_votes": 4500
  }
]
```

---

### 12. Get Voting Summary (Vote Breakdown)
**GET** `/elections/results/summary/`

**Response (200):**
```json
{
  "FPTP": 2450,
  "PR": 4500,
  "Total": 6950
}
```

---

### 13. Get Seats Summary (Seat Allocation Results)
**GET** `/elections/results/seats/`

**Response (200):**
```json
{
  "fptp_winners": [
    {"electoral_area": "Toronto Centre", "winner": "Alice Smith", "votes": 250},
    {"electoral_area": "Vancouver East", "winner": "Charlie Brown", "votes": 190}
  ],
  "pr_seats": {
    "Democratic Party": 45,
    "Republican Party": 40,
    "Green Party": 15
  }
}
```

---

## Database Models

### User (Custom User Model)
- username
- email
- password
- first_name
- province (FK)
- district (FK)
- electoral_area (FK)

### Candidate
- name
- electoral_area (FK)
- party (FK, optional)

### Party
- name
- symbol
- is_active (boolean)

### Vote
- voter (One-to-One FK to User)
- vote_type (FPTP or PR)
- candidate (FK, for FPTP votes)
- party (FK, for PR votes)
- province (FK)
- district (FK)
- electoral_area (FK)

### Province
- name

### District
- name
- province (FK)

### ElectoralArea
- name
- province (FK)

---

## Testing with cURL Examples

### Register a Voter
```bash
curl -X POST http://localhost:8000/elections/api/voter/register/ \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"pass123","province_id":1,"district_id":1,"electoral_area":1}'
```

### Get Candidates (requires login)
```bash
curl -X GET http://localhost:8000/elections/api/candidates/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Parties
```bash
curl -X GET http://localhost:8000/elections/api/parties/
```

### Get Vote Results
```bash
curl -X GET http://localhost:8000/elections/results/summary/
```

---

## Troubleshooting

### Virtual Environment Issues
- If Activate.ps1 fails, use: `& .venv\Scripts\Activate.ps1`
- Or use: `.venv\Scripts\python.exe` for direct Python execution

### Port Already in Use
```powershell
python manage.py runserver 0.0.0.0:8001
```

### Database Issues
```powershell
python manage.py migrate
```

### Admin Access
Visit: `http://localhost:8000/admin/`
(Requires superuser account created via `createsuperuser`)

---

## Additional Notes

- The voting system supports both FPTP (First-Past-The-Post) and PR (Proportional Representation) voting systems
- Voters are restricted by electoral area and can only vote once per vote type
- Results can be filtered by geographic boundaries (province, district, electoral area)
