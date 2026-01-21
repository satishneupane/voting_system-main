"""
This module is responsible for:
- Recording votes (Candidate or Party)
- Enforcing one-vote-per-user
- Calling permission checks from STEP 1

IMPORTANT:
- This file is the ONLY place votes are saved
- Views/APIs should never save votes directly
"""

from django.db import transaction

from elections.models import Vote, Party
from elections.services.vote_permissions import (
    validate_user_profile,
    validate_candidate_access,
    VotePermissionError,
)


class VoteSubmissionError(Exception):
    """
    Raised when a vote cannot be submitted
    (duplicate vote, invalid data, etc.)
    """
    pass


def ensure_user_has_not_voted(user):
    """
    Prevent multiple voting.

    Raises:
        VoteSubmissionError if user already voted
    """
    if hasattr(user, "vote"):
        raise VoteSubmissionError("User has already voted")


@transaction.atomic
def submit_candidate_vote(user, candidate_id):
    """
    Submit a FPTP (Candidate-based) vote.

    Flow:
    1. Validate user profile
    2. Ensure user has not voted
    3. Validate candidate access (STEP 1)
    4. Save vote atomically

    Returns:
        Vote instance
    """
    # STEP 1 validations
    validate_user_profile(user)
    ensure_user_has_not_voted(user)

    candidate = validate_candidate_access(user, candidate_id)

    vote = Vote.objects.create(
        voter=user,
        vote_type="FPTP",
        candidate=candidate,
        province=user.province,
        district=user.district,
        electoral_area=user.electoral_area,
    )

    return vote


@transaction.atomic
def submit_party_vote(user, party_id):
    """
    Submit a PR (Party-based) vote.

    Flow:
    1. Validate user profile
    2. Ensure user has not voted
    3. Validate party
    4. Save vote atomically

    Returns:
        Vote instance
    """
    # STEP 1 validations
    validate_user_profile(user)
    ensure_user_has_not_voted(user)

    try:
        party = Party.objects.get(id=party_id, is_active=True)
    except Party.DoesNotExist:
        raise VotePermissionError("Invalid or inactive party")

    vote = Vote.objects.create(
        voter=user,
        vote_type="PR",
        party=party,
        province=user.province,
        district=user.district,
    )

    return vote