from django.db.models import Count
from elections.models import Vote, Candidate, Party


# ------------------------------
# FPTP Results (Candidate Wins)
# ------------------------------
def fptp_results():
    """
    Returns winning candidate per electoral area
    """
    results = (
        Vote.objects
        .filter(vote_type="FPTP")
        .values(
            "electoral_area__id",
            "electoral_area__name",
            "candidate__id",
            "candidate__name",
        )
        .annotate(total_votes=Count("id"))
        .order_by("electoral_area__id", "-total_votes")
    )

    winners = {}
    for row in results:
        ea_id = row["electoral_area__id"]
        if ea_id not in winners:
            winners[ea_id] = row

    return list(winners.values())


# ------------------------------
# PR Results (Party Totals)
# ------------------------------
def pr_results():
    """
    Returns total party votes (PR system)
    """
    return (
        Vote.objects
        .filter(vote_type="PR")
        .values("party__id", "party__name")
        .annotate(total_votes=Count("id"))
        .order_by("-total_votes")
    )