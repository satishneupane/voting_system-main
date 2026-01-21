import json
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required

from .models import (
    District,
    Candidate,
    Party,
    Vote,
    ElectoralArea,
    Province,
    ElectionControl
)
from .utils import fptp_winners, pr_seat_allocation
from elections.services.vote_permissions import (
    validate_user_profile,
    validate_candidate_access,
    VotePermissionError,
)
from elections.services.vote_submission import (
    submit_candidate_vote,
    submit_party_vote,
    VoteSubmissionError,
)
from elections.services.vote_visibility import (
    get_voting_context_for_user,
    VoteVisibilityError,
)
from elections.services.results import fptp_results, pr_results

User = get_user_model()


# ------------------------------
# Home / Test
# ------------------------------
def home(request):
    return HttpResponse("Welcome to Voting System!")


# ------------------------------
# Voter Registration
# ------------------------------
@csrf_exempt
def register_voter(request):
    """
    Register a new voter. Method: POST
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        province_id = data.get("province_id")
        district_id = data.get("district_id")
        electoral_area_id = data.get("electoral_area")

        # Basic validation
        if not all([name, email, password, province_id, district_id, electoral_area_id]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "User already exists"}, status=400)

        # Validate region mapping
        province = Province.objects.get(name=province_id)
        district = District.objects.get(name=district_id, province=province)
        electoral_area = ElectoralArea.objects.get(name=electoral_area_id, province=province)

        # Atomic creation
        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
                province=province,
                district=district,
                electoral_area=electoral_area
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
# Login
# ------------------------------
@csrf_exempt  # Only if you are handling CSRF manually in React
def voter_login(request):
    """
    Log in a voter. POST: { "email": "...", "password": "..." }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return JsonResponse({"error": "Email and password are required"}, status=400)

        # Authenticate user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.is_active:
                return JsonResponse({"error": "Account is inactive."}, status=403)

            login(request, user)  # Creates session cookie
            return JsonResponse({"success": "Logged in successfully."}, status=200)
        else:
            return JsonResponse({"error": "Invalid credentials."}, status=401)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@login_required
def voter_logout(request):
    """
    Log out the current voter.
    """
    logout(request)
    return JsonResponse({"success": "Logged out successfully."}, status=200)

# ------------------------------
# Utility: Check voting status
# ------------------------------
def is_voting_open():
    control = ElectionControl.objects.first()
    return bool(control and control.is_voting_open)


# ------------------------------
# Vote Submission
# ------------------------------
@require_POST
@login_required
def submit_vote(request):
    """
    Submit FPTP (candidate) or PR (party) vote
    """
    user = request.user

    if not is_voting_open():
        return JsonResponse({"error": "Voting is currently closed."}, status=403)

    if not user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    vote_type = request.POST.get("vote_type")
    if vote_type not in ("FPTP", "PR"):
        return JsonResponse({"error": "Invalid vote type."}, status=400)

    if Vote.objects.filter(voter=user, vote_type=vote_type).exists():
        return JsonResponse({"error": "You have already voted."}, status=409)

    vote = Vote(
        voter=user,
        vote_type=vote_type,
        province=user.province,
        district=user.district,
        electoral_area=user.electoral_area,
    )

    if vote_type == "FPTP":
        candidate_id = request.POST.get("candidate_id")
        if not candidate_id:
            return JsonResponse({"error": "candidate_id is required for FPTP vote."}, status=400)
        candidate = get_object_or_404(Candidate, id=candidate_id)
        if candidate.electoral_area != user.electoral_area:
            return JsonResponse({"error": "Candidate is not in your electoral area."}, status=403)
        vote.candidate = candidate

    elif vote_type == "PR":
        party_id = request.POST.get("party_id")
        if not party_id:
            return JsonResponse({"error": "party_id is required for PR vote."}, status=400)
        party = get_object_or_404(Party, id=party_id)
        vote.party = party

    vote.save()
    return JsonResponse({"success": "Vote recorded successfully."}, status=201)

# ------------------------------
# Candidate / Party Listings
# ------------------------------
@login_required
def get_candidates(request):
    user = request.user
    if not user.electoral_area:
        return JsonResponse({"error": "User has no electoral area assigned."}, status=400)

    candidates = user.electoral_area.candidates.all().values("id", "name")
    return JsonResponse(list(candidates), safe=False)


def get_parties(request):
    parties = Party.objects.filter(is_active=True).values("id", "name", "symbol")
    return JsonResponse(list(parties), safe=False)


# ------------------------------
# Test / Temporary Endpoints
# ------------------------------
@login_required
def test_candidate_validation(request):
    candidate_id = request.GET.get("candidate_id")
    if not candidate_id:
        return JsonResponse({"error": "candidate_id is required"}, status=400)

    try:
        candidate = Candidate.objects.select_related("electoral_area").get(id=candidate_id)
    except Candidate.DoesNotExist:
        return JsonResponse({"error": "Invalid candidate"}, status=400)

    if candidate.electoral_area != request.user.electoral_area:
        return JsonResponse({"status": "error", "message": "You are not allowed to vote for this candidate."}, status=403)

    return JsonResponse({"status": "success", "message": "User is allowed to vote for this candidate."})


@login_required
def test_submit_candidate_vote(request):
    candidate_id = request.GET.get("candidate_id")
    if not candidate_id:
        return JsonResponse({"error": "candidate_id is required"}, status=400)
    try:
        vote = submit_candidate_vote(request.user, candidate_id)
        return JsonResponse({"status": "success", "vote_id": vote.id, "type": vote.vote_type})
    except (VoteSubmissionError, VotePermissionError) as e:
        return JsonResponse({"error": str(e)}, status=403)


@login_required
def test_submit_party_vote(request):
    party_id = request.GET.get("party_id")
    if not party_id:
        return JsonResponse({"error": "party_id is required"}, status=400)
    try:
        vote = submit_party_vote(request.user, party_id)
        return JsonResponse({"status": "success", "vote_id": vote.id, "type": vote.vote_type})
    except (VoteSubmissionError, VotePermissionError) as e:
        return JsonResponse({"error": str(e)}, status=403)


@login_required
def voting_context(request):
    try:
        context = get_voting_context_for_user(request.user)
        return JsonResponse(context)
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
    province_id = request.GET.get("province_id")
    district_id = request.GET.get("district_id")
    ea_id = request.GET.get("electoral_area_id")
    if province_id:
        votes = votes.filter(province_id=province_id)
    if district_id:
        votes = votes.filter(district_id=district_id)
    if ea_id:
        votes = votes.filter(electoral_area_id=ea_id)
    summary = votes.values("candidate__id", "candidate__name", "electoral_area__name").annotate(total_votes=Count("id"))
    return JsonResponse(list(summary), safe=False)


def pr_votes_summary(request):
    votes = Vote.objects.filter(vote_type="PR")
    province_id = request.GET.get("province_id")
    district_id = request.GET.get("district_id")
    if province_id:
        votes = votes.filter(province_id=province_id)
    if district_id:
        votes = votes.filter(district_id=district_id)
    summary = votes.values("party__id", "party__name").annotate(total_votes=Count("id"))
    return JsonResponse(list(summary), safe=False)


def votes_breakdown(request):
    fptp_count = Vote.objects.filter(vote_type="FPTP").count()
    pr_count = Vote.objects.filter(vote_type="PR").count()
    return JsonResponse({"FPTP": fptp_count, "PR": pr_count, "Total": fptp_count + pr_count})


def seats_summary(request):
    fptp = fptp_winners()
    pr = pr_seat_allocation(total_seats=110)
    return JsonResponse({"fptp_winners": fptp, "pr_seats": pr})


# ------------------------------
# Voter Profile (for frontend)
# ------------------------------
@login_required
def voter_profile(request):
    user = request.user
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "province": {"id": user.province.id if user.province else None, "name": user.province.name if user.province else None},
        "district": {"id": user.district.id if user.district else None, "name": user.district.name if user.district else None},
        "electoral_area": {"id": user.electoral_area.id if user.electoral_area else None, "name": user.electoral_area.name if user.electoral_area else None},
    }
    return JsonResponse(data, status=200)