import json
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    District,
    Party,
    Vote,
    ElectoralArea,
    Province,
    ElectionControl,
)
from .utils import fptp_winners, pr_seat_allocation
from elections.services.vote_submission import submit_vote, has_user_voted
from elections.services.vote_visibility import (
    get_voting_context_for_user,
    VoteVisibilityError,
)
from elections.services.results import fptp_results, pr_results

User = get_user_model()


# ------------------------------
# Home
# ------------------------------
def home(request):
    return HttpResponse("Welcome to Voting System!")


# ------------------------------
# Voter Registration
# ------------------------------
@csrf_exempt
def register_voter(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        voter_id = data.get("voter_id")
        province_name = data.get("province_name")
        district_name = data.get("district_name")
        electoral_area_name = data.get("electoral_area_name")

        if not all([name, email, password, voter_id, province_name, district_name, electoral_area_name]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "User already exists"}, status=400)
        if User.objects.filter(voter_id=voter_id).exists():
            return JsonResponse({"error": "Voter ID already registered"}, status=400)

        province = Province.objects.get(name=province_name)
        district = District.objects.get(name=district_name, province=province)
        electoral_area = ElectoralArea.objects.get(
            name=electoral_area_name,
            province=province,
        )

        with transaction.atomic():
            User.objects.create_user(
                username=name,
                email=email,
                password=password,
                first_name=name,
                voter_id=voter_id,
                province=province,
                district=district,
                electoral_area=electoral_area,
            )

        return JsonResponse({"success": "Voter registered successfully"}, status=201)

    except Province.DoesNotExist:
        return JsonResponse({"error": "Invalid province"}, status=400)
    except District.DoesNotExist:
        return JsonResponse({"error": "Invalid district for selected province"}, status=400)
    except ElectoralArea.DoesNotExist:
        return JsonResponse({"error": "Invalid electoral area"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ------------------------------
# Authentication
# ------------------------------
@csrf_exempt
def voter_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)
        identifier = data.get("identifier")  # can be email or voter_id
        password = data.get("password")

        user = authenticate(request, username=identifier, password=password)
        if not user:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        if not user.is_active:
            return JsonResponse({"error": "Account inactive"}, status=403)

        login(request, user)
        return JsonResponse({"success": "Logged in successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def voter_logout(request):
    logout(request)
    return JsonResponse({"success": "Logged out"})


# ------------------------------
# Vote Submission (ONLY ENTRY POINT)
# ------------------------------
@csrf_exempt
@require_POST
@login_required
def submit_vote_view(request):
    # Parse JSON or fallback to form data
    try:
        content_type = (request.content_type or "").lower()
        if "application/json" in content_type:
            data = json.loads(request.body or b"{}")
        else:
            # If client sent form-encoded or multipart data, use request.POST
            # `request.POST` will be an empty QueryDict for JSON bodies, so
            # this fallback is safe.
            data = request.POST.dict() if request.POST else {}
    except json.JSONDecodeError:
        # Fall back to POST data if JSON was invalid
        data = request.POST.dict() if request.POST else {}

    vote_type = data.get("vote_type")
    candidate_id = data.get("candidate_id")
    party_id = data.get("party_id")

    # Convert NOTA votes from frontend (id=0) to None
    if vote_type == "FPTP" and str(candidate_id) == "0":
        candidate_id = None  # Treat FPTP NOTA as None

    # Check if user already voted for this type
    if has_user_voted(request.user, vote_type):
        return JsonResponse(
            {"error": "You have already voted for this type", "already_voted": True},
            status=403
        )

    try:
        vote = submit_vote(
            user=request.user,
            vote_type=vote_type,
            candidate_id=candidate_id,
            party_id=party_id
        )
        return JsonResponse(
            {
                "success": "Vote recorded successfully",
                "vote_id": vote.id,
                "already_voted": False
            },
            status=201
        )
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=403)


# ------------------------------
# Candidate / Party Listings
# ------------------------------
@login_required
def get_candidates(request):
    user = request.user
    user_area = user.electoral_area

    if not user_area:
        return JsonResponse({"error": "User has no electoral area"}, status=400)

    # Include all candidates in this electoral area
    candidates = list(
        user_area.candidates.values("id", "name", "party__name")
    )

    # Add NOTA dynamically if not present
    if not any(c.get("is_nota") for c in candidates):
        candidates.append({
            "id": 0,  # frontend treats id=0 as NOTA
            "name": "None of the Above (NOTA)",
            "party__name": None,
            "is_nota": True,
        })

    # Voting status
    voting_status = {
        "FPTP": has_user_voted(user, "FPTP"),
        "PR": has_user_voted(user, "PR"),
    }

    return JsonResponse({
        "candidates": candidates,
        "voting_status": voting_status
    })


@login_required
def get_parties(request):
    # Active parties
    parties = list(
        Party.objects.filter(is_active=True).values("id", "name", "symbol")
    )

    # Voting status
    voting_status = {
        "FPTP": has_user_voted(request.user, "FPTP"),
        "PR": has_user_voted(request.user, "PR"),
    }

    return JsonResponse({
        "parties": parties,
        "voting_status": voting_status
    })


# ------------------------------
# Voting Context
# ------------------------------
@login_required
def voting_context(request):
    try:
        return JsonResponse(get_voting_context_for_user(request.user))
    except VoteVisibilityError as e:
        return JsonResponse({"error": str(e)}, status=403)


# ------------------------------
# Results / Monitoring
# ------------------------------
@staff_member_required
def fptp_results_view(request):
    return JsonResponse({"results": fptp_results()})


@staff_member_required
def pr_results_view(request):
    return JsonResponse({"results": list(pr_results())})


def fptp_votes_summary(request):
    votes = Vote.objects.filter(vote_type="FPTP")
    if pid := request.GET.get("province_id"):
        votes = votes.filter(province_id=pid)
    if did := request.GET.get("district_id"):
        votes = votes.filter(district_id=did)
    if ea := request.GET.get("electoral_area_id"):
        votes = votes.filter(electoral_area_id=ea)

    return JsonResponse(
        list(
            votes.values(
                "candidate__id",
                "candidate__name",
                "electoral_area__name",
            ).annotate(total_votes=Count("id"))
        ),
        safe=False,
    )


def pr_votes_summary(request):
    votes = Vote.objects.filter(vote_type="PR")
    if pid := request.GET.get("province_id"):
        votes = votes.filter(province_id=pid)
    if did := request.GET.get("district_id"):
        votes = votes.filter(district_id=did)

    return JsonResponse(
        list(
            votes.values("party__id", "party__name")
            .annotate(total_votes=Count("id"))
        ),
        safe=False,
    )


def seats_summary(request):
    return JsonResponse({
        "fptp_winners": fptp_winners(),
        "pr_seats": pr_seat_allocation(total_seats=110),
    })


# ------------------------------
# Voter Profile
# ------------------------------
@login_required
def voter_profile(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)

    user = request.user
    full_name = f"{user.first_name} {user.last_name}".strip()
    # ✅ Check if already voted
    fptp_voted = Vote.objects.filter(voter=user, vote_type="FPTP").exists()
    pr_voted = Vote.objects.filter(voter=user, vote_type="PR").exists()
    full_name = f"{user.first_name} {user.last_name}".strip()
    return JsonResponse({
        "username": full_name or user.username,
        "email": user.email,
        "voter_id": user.voter_id,
        "province": user.province.name if user.province else None,
        "district": user.district.name if user.district else None,
        "electoral_area": user.electoral_area.name if user.electoral_area else None,
        "has_voted": {
            "FPTP": fptp_voted,
            "PR": pr_voted,
        }
    })

#---------------------------
# Voter Status Check
#---------------------------
@login_required
def voter_status(request):
    user = request.user
    full_name = f"{user.first_name} {user.last_name}".strip()
    has_fptp = has_user_voted(user, "FPTP")
    has_pr = has_user_voted(user, "PR")

    return JsonResponse({
        "username": full_name ,
        "email": user.email,
        "province": user.province.name if user.province else None,
        "district": user.district.name if user.district else None,
        "electoral_area": str(user.electoral_area) if user.electoral_area else None,
        "has_voted_fptp": has_fptp,
        "has_voted_pr": has_pr,
    })


#-lock check--------
def is_election_active():
    control = ElectionControl.objects.first()
    if not control:
        return False
        
    now = timezone.now()
    
    # Check if we are currently within the time window
    if control.opened_at and control.closed_at:
        return control.opened_at <= now <= control.closed_at
        
    # Fallback to the manual switch if dates aren't set
    return control.is_voting_open