from django.test import TestCase
from elections.models import User, Province, District, ElectoralArea, Candidate, Party, Vote, ElectionControl
from elections.services.vote_submission import submit_vote
from django.core.exceptions import ValidationError
from django.utils import timezone

class VoteDBConstraintsTest(TestCase):

    def setUp(self):
        self.province = Province.objects.create(name="Province 1")
        self.district = District.objects.create(name="District 1", province=self.province)
        self.ea = ElectoralArea.objects.create(
            name="EA 1",
            province=self.province,
            district=self.district)

        self.user = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123",
            province=self.province,
            district=self.district,
            electoral_area=self.ea
        )
        self.candidate = Candidate.objects.create(name="Candidate 1", electoral_area=self.ea)
        self.party = Party.objects.create(name="Party 1", is_active=True)
        
        ElectionControl.objects.create(
            is_voting_open=True,
            opened_at=timezone.now())

    def test_fptp_vote_success(self):
        vote = submit_vote(self.user, "FPTP", candidate_id=self.candidate.id)
        self.assertEqual(vote.vote_type, "FPTP")

    def test_cross_area_vote_failure(self):
        ea2 = ElectoralArea.objects.create(
            name="EA 2",
            province=self.province,
            district=self.district)

        candidate2 = Candidate.objects.create(name="Candidate 2", electoral_area=ea2)
        with self.assertRaises(ValidationError):
            submit_vote(self.user, "FPTP", candidate_id=candidate2.id)

    def test_pr_vote_success(self):
        vote = submit_vote(self.user, "PR", party_id=self.party.id)
        self.assertEqual(vote.vote_type, "PR")

    def test_double_vote_failure(self):
        submit_vote(self.user, "FPTP", candidate_id=self.candidate.id)
        with self.assertRaises(ValidationError):
            submit_vote(self.user, "FPTP", candidate_id=self.candidate.id)
