from django.db import models
from django.db.models import Q, F
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from datetime import timezone

# ==============================
# Province & District
# ==============================
class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(
        Province,
        related_name="districts",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("name", "province")

    def __str__(self):
        return f"{self.name}, {self.province.name}"


# ==============================
# Electoral Area
# ==============================
class ElectoralArea(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("name", "district")

    def __str__(self):
        return f"{self.name} - ({self.district.name})"


# ==============================
# Custom User
# ==============================
class User(AbstractUser):
    province = models.ForeignKey(
        Province,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    district = models.ForeignKey(
        District,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    electoral_area = models.ForeignKey(
        ElectoralArea,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.username
    
    district = models.ForeignKey(
        'District',
        on_delete=models.CASCADE,
        null=False,   # allow null temporarily
        blank=False
    )
    
    electoral_area = models.ForeignKey(
        'ElectoralArea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


# ==============================
# Party (PR system)
# ==============================
class Party(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ==============================
# Candidate (FPTP system)
# ==============================
class Candidate(models.Model):
    name = models.CharField(max_length=100)
    electoral_area = models.ForeignKey(
        ElectoralArea,
        related_name="candidates",
        on_delete=models.CASCADE
    )
    party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="candidates"
    )
    is_nota = models.BooleanField(default=False)  # None of the Above option

    def __str__(self):
        return f"{self.name} ({self.electoral_area})"


# ==============================
# Vote (supports FPTP + PR)
# ==============================
class Vote(models.Model):
    FPTP = "FPTP"
    PR = "PR"

    VOTE_TYPE_CHOICES = (
        (FPTP, "Candidate Vote"),
        (PR, "Party Vote"),
    )

    voter = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="votes",
    )

    vote_type = models.CharField(
        max_length=4,
        choices=VOTE_TYPE_CHOICES,
    )

    candidate = models.ForeignKey(
        "Candidate",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="votes",
    )

    party = models.ForeignKey(
        "Party",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="votes",
    )

    province = models.ForeignKey(
        "Province",
        on_delete=models.PROTECT,
    )

    district = models.ForeignKey(
        "District",
        on_delete=models.PROTECT,
    )

    electoral_area = models.ForeignKey(
        "ElectoralArea",
        on_delete=models.PROTECT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
        # 1️⃣ One vote per user per vote type
            models.UniqueConstraint(fields=["voter", "vote_type"], name="unique_vote_per_user_per_type"),

        # 2️⃣ Vote type consistency: FPTP <-> candidate, PR <-> party
            models.CheckConstraint(
                condition=(
                    Q(vote_type="FPTP", candidate__isnull=False, party__isnull=True) |
                    Q(vote_type="PR", party__isnull=False, candidate__isnull=True)
                ),
                name="vote_type_candidate_party_consistency",
            ),

        # 3️⃣ Location fields must never be NULL
            models.CheckConstraint(
                condition=Q(province__isnull=False) & Q(district__isnull=False) & Q(electoral_area__isnull=False),
                name="vote_location_not_null",
            ),

        # 4️⃣ Candidate must belong to user's electoral area
            models.CheckConstraint(
                condition=Q(candidate__isnull=True) | Q(candidate__electoral_area=F("electoral_area")),
                name="candidate_electoral_area_match",
            ),
        ]

    def __str__(self):
        return f"{self.voter} - {self.vote_type}"

    # =====================================================
    # DATABASE CONSTRAINTS (NON-NEGOTIABLE)
    # =====================================================
    class Meta:
        constraints = [
            # FPTP must have candidate ONLY
            models.CheckConstraint(
                name="fptp_requires_candidate",
                condition=Q(
                    vote_type="FPTP",
                    candidate__isnull=False,
                    party__isnull=True,
                )
                | Q(vote_type="PR"),
            ),

            # PR must have party ONLY
            models.CheckConstraint(
                name="pr_requires_party",
                condition=Q(
                    vote_type="PR",
                    party__isnull=False,
                    candidate__isnull=True,
                )
                | Q(vote_type="FPTP"),
            ),

            # One vote per user per vote type
            models.UniqueConstraint(
                fields=["voter", "vote_type"],
                name="unique_vote_per_user_per_type",
            ),
        ]

    def clean(self):
        """
        Extra safety at model validation level.
        """
        if self.vote_type == "FPTP" and not self.candidate:
            raise ValidationError("FPTP vote requires a candidate.")

        if self.vote_type == "PR" and not self.party:
            raise ValidationError("PR vote requires a party.")

    def __str__(self):
        return f"{self.voter} - {self.vote_type}"


    class Meta:
        """
        Enforces:
        - one FPTP vote per user
        - one PR vote per user
        """
        unique_together = ("voter", "vote_type")

    def __str__(self):
        return f"{self.voter.email} - {self.vote_type}"


# ==============================
# Election Control
# ==============================
class ElectionControl(models.Model):
    is_voting_open = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    def clean(self):
        if self.opened_at and self.closed_at and self.closed_at < self.opened_at:
            raise ValidationError("Election cannot be closed earlier than it starts.")
    def save(self, *args, **kwargs):
        self.clean()
        now = timezone.now()
        if self.opened_at and self.closed_at:
            self.is_voting_open = self.opened_at <= now <= self.closed_at
        super().save(*args, **kwargs)

    def __str__(self):
        return "Voting Open" if self.is_voting_open else "Voting Closed"

    class Meta:
        verbose_name = "Election Control"
        verbose_name_plural = "Election Controls"


# ==============================
# FPTP Result
# ==============================
class FPTPResult(models.Model):
    electoral_area = models.OneToOneField(
        ElectoralArea,
        on_delete=models.CASCADE,
        related_name="fptp_result"
    )
    winner = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE
    )
    total_votes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.electoral_area} → {self.winner}"


# ==============================
# PR Result (Party Seats)
# ==============================
class PRResult(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    total_votes = models.PositiveIntegerField()
    seats_allocated = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.party} → {self.seats_allocated} seats"