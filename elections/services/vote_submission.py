from django.db import transaction
from django.core.exceptions import ValidationError

from elections.models import Vote, Candidate, Party, ElectionControl


def is_voting_open():
    control = ElectionControl.objects.first()
    return bool(control and control.is_voting_open)


def ensure_user_has_not_voted(user, vote_type):
    if Vote.objects.filter(voter=user, vote_type=vote_type).exists():
        raise ValidationError(f"You have already voted ({vote_type}).")


def validate_candidate_strict(user, candidate_id):
    """
    HARD rule:
    Candidate MUST belong to user's electoral area
    """
    if not user.electoral_area:
        raise ValidationError("User has no electoral area assigned.")

    try:
        candidate = Candidate.objects.select_related("electoral_area").get(id=candidate_id)
    except Candidate.DoesNotExist:
        raise ValidationError("Invalid candidate.")

    if candidate.electoral_area_id != user.electoral_area_id:
        raise ValidationError(
            "You are not allowed to vote for candidates outside your electoral area."
        )

    return candidate


@transaction.atomic
def submit_candidate_vote(user, candidate_id):
    """
    Submit FPTP vote (STRICT)
    """
    if not is_voting_open():
        raise ValidationError("Voting is currently closed.")

    ensure_user_has_not_voted(user, "FPTP")

    candidate = validate_candidate_strict(user, candidate_id)

    return Vote.objects.create(
        voter=user,
        vote_type="FPTP",
        candidate=candidate,
        province=user.province,
        district=user.district,
        electoral_area=user.electoral_area,
    )


@transaction.atomic
def submit_party_vote(user, party_id):
    """
    Submit PR vote
    """
    if not is_voting_open():
        raise ValidationError("Voting is currently closed.")

    ensure_user_has_not_voted(user, "PR")

    try:
        party = Party.objects.get(id=party_id, is_active=True)
    except Party.DoesNotExist:
        raise ValidationError("Invalid party.")

    return Vote.objects.create(
        voter=user,
        vote_type="PR",
        party=party,
        province=user.province,
        district=user.district,
        electoral_area=user.electoral_area,
    )
