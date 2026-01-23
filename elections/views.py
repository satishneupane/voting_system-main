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

from .models import (
    District,
    Party,
    Vote,
    ElectoralArea,
    Province,
    ElectionControl,
)
from .utils import fptp_winners, pr_seat_allocation
from elections.services.vote_submission import submit_vote
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
        province_name = data.get("province_id")
        district_name = data.get("district_id")
        electoral_area_name = data.get("electoral_area")

        if not all([name, email, password, province_name, district_name, electoral_area_name]):
            return JsonResponse({"error": "All fields are required"}, status=400)

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "User already exists"}, status=400)

        province = Province.objects.get(name=province_name)
        district = District.objects.get(name=district_name, province=province)
        electoral_area = ElectoralArea.objects.get(
            name=electoral_area_name,
            province=province,
        )

        with transaction.atomic():
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
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
        email = data.get("email")
        password = data.get("password")

        user = authenticate(request, username=email, password=password)
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
@require_POST
@login_required
def submit_vote_view(request):
    vote_type = request.POST.get("vote_type")
    candidate_id = request.POST.get("candidate_id")
    party_id = request.POST.get("party_id")

    try:
        vote = submit_vote(user=request.user, vote_type=vote_type, candidate_id=candidate_id, party_id=party_id)
        return JsonResponse({"success": "Vote recorded successfully", "vote_id": vote.id}, status=201)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=403)


# ------------------------------
# Candidate / Party Listings
# ------------------------------
@login_required
def get_candidates(request):
    if not request.user.electoral_area:
        return JsonResponse({"error": "User has no electoral area"}, status=400)

    return JsonResponse(
        list(
            request.user.electoral_area.candidates.values("id", "name")
        ),
        safe=False,
    )


def get_parties(request):
    return JsonResponse(
        list(Party.objects.filter(is_active=True).values("id", "name", "symbol")),
        safe=False,
    )


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
    u = request.user
    return JsonResponse({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "province": u.province.name if u.province else None,
        "district": u.district.name if u.district else None,
        "electoral_area": u.electoral_area.name if u.electoral_area else None,
    })
