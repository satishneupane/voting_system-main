from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from elections.models import Vote, Candidate, Party, ElectionControl


# =====================================================
# Election State
# =====================================================
def is_voting_open():
    """
    Returns True only if voting is globally enabled.
    """
    control = ElectionControl.objects.first()
    return bool(control and control.is_voting_open)


# =====================================================
# Vote Guards
# =====================================================
def ensure_user_has_not_voted(user, vote_type):
    """
    Enforces ONE vote per user per vote type (FPTP / PR).
    """
    if Vote.objects.filter(voter=user, vote_type=vote_type).exists():
        raise ValidationError(f"You have already voted ({vote_type}).")


# =====================================================
# Candidate Validation (CRITICAL SECURITY RULE)
# =====================================================
def validate_candidate_strict(user, candidate_id):
    """
    HARD SECURITY RULE (NON-NEGOTIABLE)

    A candidate is valid ONLY IF:
    - User has an electoral area
    - Candidate exists
    - Candidate.electoral_area == user.electoral_area

    ⚠️ This rule MUST be enforced at QUERY LEVEL.
    """
    if not user.electoral_area:
        raise ValidationError("User has no electoral area assigned.")

    # 🔒 IMPORTANT:
    # Candidate from another electoral area can NEVER be fetched
    candidate = get_object_or_404(
        Candidate,
        id=candidate_id,
        electoral_area=user.electoral_area,
    )

    return candidate


# =====================================================
# FPTP Vote Submission
# =====================================================
@transaction.atomic
def submit_vote(user, vote_type, candidate_id=None, party_id=None):
    from elections.models import Vote, Candidate, Party, ElectionControl

    # 1️⃣ Voting open check
    control = ElectionControl.objects.first()
    if not control or not control.is_voting_open:
        raise ValidationError("Voting is currently closed.")

    # 2️⃣ One vote per user per type
    if Vote.objects.filter(voter=user, vote_type=vote_type).exists():
        raise ValidationError(f"You have already voted ({vote_type}).")

    # 3️⃣ FPTP vote
    if vote_type == "FPTP":
        if candidate_id is None:
            # NOTA vote
            return Vote.objects.create(
                voter=user,
                vote_type="FPTP",
                candidate=None,
                province=user.province,
                district=user.district,
                electoral_area=user.electoral_area,
            )
        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            raise ValidationError("Candidate does not exist.")

        if candidate.electoral_area_id != user.electoral_area_id:
            raise ValidationError("You cannot vote for a candidate outside your electoral area.")
        return Vote.objects.create(
            voter=user,
            vote_type="FPTP",
            candidate=candidate,
            province=user.province,
            district=user.district,
            electoral_area=user.electoral_area,
        )

    # 4️⃣ PR vote
    elif vote_type == "PR":
        if not party_id:
            raise ValidationError("party_id is required for PR vote.")
        party = get_object_or_404(Party, id=party_id, is_active=True)
        return Vote.objects.create(
            voter=user,
            vote_type="PR",
            party=party,
            province=user.province,
            district=user.district,
            electoral_area=user.electoral_area,
        )

    else:
        raise ValidationError("Invalid vote_type")


# =====================================================
# PR Vote Submission
# =====================================================
@transaction.atomic
def submit_party_vote(user, party_id):
    """
    Submit PR (Party) vote.

    Guarantees:
    - Voting is open
    - User votes only once (PR)
    - Party is active
    - Vote geography is locked to user profile
    """
    if not is_voting_open():
        raise ValidationError("Voting is currently closed.")

    ensure_user_has_not_voted(user, "PR")

    party = get_object_or_404(
        Party,
        id=party_id,
        is_active=True
    )

    return Vote.objects.create(
        voter=user,
        vote_type="PR",
        party=party,
        province=user.province,
        district=user.district,
        electoral_area=user.electoral_area,
    )
#=========================
# Check if User has Voted
#=========================
def has_user_voted(user, vote_type):
    """
    Returns True if the given user has already voted for the specified vote_type.
    vote_type must be 'FPTP' or 'PR'.
    """
    return Vote.objects.filter(
        voter=user,
        vote_type=vote_type
    ).exists()
    
