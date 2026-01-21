"""
This module controls:
- What data a voter can see
- Before voting
- After voting

IMPORTANT:
- Frontend must rely on this output
- Do NOT expose unrestricted querysets
"""

from elections.models import Candidate, Party
from elections.services.vote_permissions import validate_user_profile


class VoteVisibilityError(Exception):
    """Raised when visibility rules are violated"""
    pass


def user_has_voted(user):
    """
    Check if user has already voted
    """
    return hasattr(user, "vote")


def get_voting_context_for_user(user):
    """
    Returns voting data the user is allowed to see.

    If user already voted → limited response
    If not voted → show valid voting options only

    Returns dict
    """
    validate_user_profile(user)

    if user_has_voted(user):
        return {
            "has_voted": True,
            "message": "User has already voted",
            "vote_type": user.vote.vote_type,
        }

    # User has NOT voted → show valid options
    candidates = Candidate.objects.filter(
        electoral_area=user.electoral_area
    ).select_related("electoral_area")

    parties = Party.objects.filter(is_active=True)

    return {
        "has_voted": False,
        "province": {
            "id": user.province.id,
            "name": user.province.name,
        },
        "district": {
            "id": user.district.id,
            "name": user.district.name,
        },
        "electoral_area": {
            "id": user.electoral_area.id,
            "name": user.electoral_area.name,
        },
        "candidates": [
            {"id": c.id, "name": c.name}
            for c in candidates
        ],
        "parties": [
            {"id": p.id, "name": p.name}
            for p in parties
        ],
    }