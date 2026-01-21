from django.http import JsonResponse
from django.db.models import Count
from .models import Vote, Candidate, Party

def candidate_vote_results(request):
    """
    Returns total votes per candidate (FPTP)
    """
    results = (
        Vote.objects
        .filter(vote_type="FPTP", candidate__isnull=False)
        .values("candidate__id", "candidate__name")
        .annotate(total_votes=Count("id"))
        .order_by("-total_votes")
    )

    return JsonResponse(list(results), safe=False)

def party_vote_results(request):
    """
    Returns total votes per party (PR)
    """
    results = (
        Vote.objects
        .filter(vote_type="PR", party__isnull=False)
        .values("party__id", "party__name")
        .annotate(total_votes=Count("id"))
        .order_by("-total_votes")
    )

    return JsonResponse(list(results), safe=False)

def voting_summary(request):
    """
    High-level voting summary
    """
    summary = {
        "total_votes": Vote.objects.count(),
        "fptp_votes": Vote.objects.filter(vote_type="FPTP").count(),
        "pr_votes": Vote.objects.filter(vote_type="PR").count(),
    }

    return JsonResponse(summary)

def votes_by_province(request):
    results = (
        Vote.objects
        .values("province__name")
        .annotate(total_votes=Count("id"))
        .order_by("-total_votes")
    )

    return JsonResponse(list(results), safe=False)

def votes_by_district(request):
    results = (
        Vote.objects
        .values("district__name")
        .annotate(total_votes=Count("id"))
        .order_by("-total_votes")
    )

    return JsonResponse(list(results), safe=False)