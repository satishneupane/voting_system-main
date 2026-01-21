🗳️ Voting System Backend

1.This repository contains the backend logic for a Nepalese voting system. It supports:
2.Candidate-based (FPTP) voting
3.Party-based (Proportional Representation, PR) voting
4.Region-based voting restrictions (province → district → electoral area)
5.Vote monitoring and seat allocation (FPTP winners & PR seats)
6.Admin dashboards for vote counting and monitoring
    The frontend team can interact via REST-like JSON APIs.

Table of Contents
1.Project Setup
2.Models
3.Endpoints
4.Vote Submission Rules
5.Seat Allocation
6.Admin Monitoring
7.Frontend Integration Notes 

#Project Setup
1. Environment
     conda create -n voting_system python=3.13
     conda activate voting_system
     pip install -r requirements.txt
2. Database
-->MySQL
Run migrations
python manage.py makemigrations
python manage.py migrate
3. Create Superuser
python manage.py createsuperuser
4. Run Server
python manage.py runserver

#Models Overview
User
  Custom user model with voting region:
    province
    district
    electoral_area

Province / District / ElectoralArea
  Hierarchical structure to lock voting regionally.

Party
  Represents political parties in PR voting.

Candidate
  Represents FPTP candidates, linked to electoral areas.

Vote
  Supports both FPTP (candidate) and PR (party) votes.

Fields:
    voter (OneToOne → User)
    vote_type (FPTP / PR)
    candidate / party
    province / district / electoral_area
    timestamp (created_at)

#Endpoints
All endpoints return JSON.
 1. Voter Info
     GET /api/voter/profile/ → returns logged-in user’s profile.
 2. Candidate & Party
    GET /api/candidates/ → candidates in user’s electoral area
    GET /api/parties/ → active parties
3. Vote Submission
    POST /vote/submit/
       Payload: {"vote_type": "FPTP", "candidate_id": 1}  or   {"vote_type": "PR", "party_id": 2}
    Voting restricted to the user’s province/district/electoral area
    Prevents double voting
    Closed voting blocked
4. Vote Results
    GET /results/candidates/ → FPTP votes per candidate
    GET /results/parties/ → PR votes per party
    GET /results/summary/ → total FPTP vs PR
    GET /results/province/ → optional province filter
    GET /results/district/ → optional district filter
    GET /results/seats-summary/ → FPTP winners & PR seat allocation

#Vote Submission Rules
  FPTP vote: only one candidate per user
  PR vote: only one party per user
  User cannot vote outside assigned province, district, or electoral area
  System enforces one vote per type

#Seat Allocation
 FPTP
  Winner-takes-all per electoral area
  Candidate with highest votes wins
 PR
  Seats allocated proportionally using simple quota
  Only active parties are considered
  Total PR seats configurable (default 110)

#Admin Monitoring
  Admin can view:
    FPTP votes per candidate
    PR votes per party
    Seat allocation results
    Total votes summary
    Filter results by province/district/electoral area

#Frontend Integration Notes
1.All responses are JSON, ready for JavaScript consumption.
2.Authentication required for voting endpoints.
3.Region locks: province → district → electoral area.
4.Use /api/candidates/ and /api/parties/ to populate dropdowns.
5.Submit votes via /vote/submit/ POST endpoint.
6.Use /results/* endpoints to fetch live results

#Optional: Temporary Testing Endpoints
/validate/candidate/ → Check if user can vote for a candidate
/vote/candidate/ → Test submit candidate vote
/vote/party/ → Test submit party vote
/vote/context → Get voting context
--These are backend-only endpoints for testing. Frontend can ignore.

#Project Structure
elections/
├── models.py           # All models: User, Candidate, Party, Vote, Province/District/EA
├── admin.py            # Admin dashboard configuration
├── views.py            # Vote submission, candidate/party listing, result views
├── urls.py             # API routes
├── services/
│   ├── vote_submission.py  # Core logic for vote creation
│   ├── vote_permissions.py # Validation & access control
│   ├── vote_visibility.py  # Voting context for users
│   └── seat_allocation.py  # FPTP and PR seat allocation logic
└── utils.py                # Helper functions (optional)