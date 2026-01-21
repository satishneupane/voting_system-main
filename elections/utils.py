from .models import Vote, Candidate, Party, ElectoralArea
from django.db.models import Count

# ------------------------------
# FPTP Winner Calculation
# ------------------------------
def fptp_winners():
    """
    Returns a dict with ElectoralArea.id as key and winning candidate info
    """
    winners = {}
    electoral_areas = ElectoralArea.objects.all()

    for ea in electoral_areas:
        votes = Vote.objects.filter(vote_type='FPTP', electoral_area=ea)
        top_candidate = votes.values('candidate__id', 'candidate__name').annotate(total_votes=Count('id')).order_by('-total_votes').first()
        if top_candidate:
            winners[ea.id] = top_candidate
    return winners


# ------------------------------
# PR Seat Allocation
# ------------------------------
def pr_seat_allocation(total_seats=100):
    """
    Allocate PR seats proportionally to parties based on PR votes
    total_seats: Total number of PR seats to distribute
    """
    votes = Vote.objects.filter(vote_type='PR')
    total_pr_votes = votes.count()
    party_votes = votes.values('party__id', 'party__name').annotate(votes_count=Count('id'))

    allocation = {}
    for pv in party_votes:
        proportion = pv['votes_count'] / total_pr_votes if total_pr_votes else 0
        allocation[pv['party__id']] = {
            "party_name": pv['party__name'],
            "votes_count": pv['votes_count'],
            "allocated_seats": round(proportion * total_seats)
        }
    return allocation