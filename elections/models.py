from django.db import models
from django.contrib.auth.models import AbstractUser

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
    province = models.ForeignKey(
        Province,
        related_name="electoral_areas",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("name", "province")

    def __str__(self):
        return f"{self.name} - {self.province.name}"


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

    def __str__(self):
        return f"{self.name} ({self.electoral_area})"


# ==============================
# Vote (supports FPTP + PR)
# ==============================
class Vote(models.Model):
    VOTE_TYPE_CHOICES = (
        ("FPTP", "Candidate Vote"),
        ("PR", "Party Vote"),
    )

    voter = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="vote"
    )

    vote_type = models.CharField(
        max_length=10,
        choices=VOTE_TYPE_CHOICES
    )

    # Candidate vote (FPTP)
    candidate = models.ForeignKey(
        Candidate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes"
    )

    # Party vote (PR)
    party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes"
    )

    # Locked geography (must match user)
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE
    )
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE
    )
    electoral_area = models.ForeignKey(
        ElectoralArea,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter} - {self.vote_type}"


# ==============================
# Election Control
# ==============================
class ElectionControl(models.Model):
    is_voting_open = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "Voting Open" if self.is_voting_open else "Voting Closed"

    class Meta:
        verbose_name = "Election Control"
        verbose_name_plural = "Election Control"


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