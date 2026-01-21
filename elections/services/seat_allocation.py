from django.db.models import Count
from elections.models import (
    Vote,
    Candidate,
    ElectoralArea,
    Party,
    FPTPResult,
    PRResult,
)

# =========================================================
# FPTP SEAT ALLOCATION
# =========================================================
def allocate_fptp_seats():
    """
    First-Past-The-Post (FPTP) seat allocation.

    Rule:
    - Each electoral area gets exactly ONE seat
    - Candidate with the highest votes in that area wins

    Result is stored in FPTPResult table.
    """

    # Clear previous results (safe re-run)
    FPTPResult.objects.all().delete()

    # Loop through each electoral area
    for area in ElectoralArea.objects.all():

        votes = (
            Vote.objects.filter(
                vote_type="FPTP",
                candidate__electoral_area=area
            )
            .values("candidate")
            .annotate(total_votes=Count("id"))
            .order_by("-total_votes")
        )

        if not votes:
            continue

        top = votes[0]
        winner = Candidate.objects.get(id=top["candidate"])

        FPTPResult.objects.create(
            electoral_area=area,
            winner=winner,
            total_votes=top["total_votes"],
        )


# =========================================================
# PR SEAT ALLOCATION
# =========================================================
def allocate_pr_seats(total_pr_seats=110):
    """
    Proportional Representation (PR) seat allocation.

    Rule:
    - Seats distributed proportionally based on PR votes
    - Uses simple quota method
    - Only active parties are considered

    Result is stored in PRResult table.
    """

    # Clear previous PR results
    PRResult.objects.all().delete()

    party_votes = (
        Vote.objects.filter(vote_type="PR", party__is_active=True)
        .values("party")
        .annotate(total_votes=Count("id"))
    )

    total_votes = sum(p["total_votes"] for p in party_votes)

    if total_votes == 0:
        return

    quota = total_votes / total_pr_seats

    for p in party_votes:
        seats = int(p["total_votes"] / quota)

        PRResult.objects.create(
            party=Party.objects.get(id=p["party"]),
            total_votes=p["total_votes"],
            seats_allocated=seats,
        )


# =========================================================
# MASTER RUNNER (OPTIONAL, RECOMMENDED)
# =========================================================
def run_seat_allocation():
    """
    Runs full election result calculation.
    Safe to call multiple times.
    """
    allocate_fptp_seats()
    allocate_pr_seats()