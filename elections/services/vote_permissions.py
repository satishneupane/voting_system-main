"""
Vote Permission & Validation Service
-----------------------------------

This module contains all business rules related to:
- Who can vote
- Where they can vote
- Which candidate/party they are allowed to vote for

IMPORTANT:
- This file does NOT save votes
- This file ONLY validates permissions
- Reusable across APIs, views, admin actions
"""

from elections.models import Candidate, ElectoralArea


class VotePermissionError(Exception):
    """
    Custom exception raised when voting rules are violated.
    This keeps error handling clean and consistent.
    """
    pass


def validate_user_profile(user):
    """
    Ensure the user profile is complete before voting.

    Rules:
    - User must have a province
    - User must have a district
    - User must have an electoral area

    Raises:
        VotePermissionError if profile is incomplete
    """
    if not user.province:
        raise VotePermissionError("User province is not assigned")

    if not user.district:
        raise VotePermissionError("User district is not assigned")

    if not user.electoral_area:
        raise VotePermissionError("User electoral area is not assigned")


def validate_electoral_area_access(user, electoral_area_id):
    """
    Ensure the electoral area belongs to the user's province.

    Args:
        user (User): Logged-in voter
        electoral_area_id (int): Electoral area selected

    Returns:
        ElectoralArea instance

    Raises:
        VotePermissionError if invalid or unauthorized
    """
    try:
        area = ElectoralArea.objects.select_related("province").get(
            id=electoral_area_id
        )
    except ElectoralArea.DoesNotExist:
        raise VotePermissionError("Invalid electoral area")

    if area.province != user.province:
        raise VotePermissionError(
            "Electoral area does not belong to user's province"
        )

    return area


def validate_candidate_access(user, candidate_id):
    """
    Ensure candidate belongs to the user's electoral area.

    Args:
        user (User): Logged-in voter
        candidate_id (int): Candidate selected

    Returns:
        Candidate instance

    Raises:
        VotePermissionError if invalid or unauthorized
    """
    try:
        candidate = Candidate.objects.select_related(
            "electoral_area",
            "electoral_area__province"
        ).get(id=candidate_id)
    except Candidate.DoesNotExist:
        raise VotePermissionError("Invalid candidate")

    if candidate.electoral_area != user.electoral_area:
        raise VotePermissionError(
            "Candidate does not belong to user's electoral area"
        )

    return candidate