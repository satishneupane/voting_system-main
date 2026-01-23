from django.urls import path
from . import views

urlpatterns = [
    # -------- API endpoints --------
    path("api/voter/register/", views.register_voter, name="register-voter"),
    path("api/voter/login/", views.voter_login, name="voter-login"),
    path("api/voter/logout/", views.voter_logout, name="voter-logout"),
    path("api/voter/profile/", views.voter_profile, name="voter-profile"),
    path("api/candidates/", views.get_candidates, name="candidate-list"),
    path("api/parties/", views.get_parties, name="party-list"),

    # -------- Voting --------
    path("vote/submit/", views.submit_vote_view, name="submit-vote"),

    # -------- Results / Monitoring --------
    path("results/candidates/", views.fptp_votes_summary, name="candidate-results"),
    path("results/parties/", views.pr_votes_summary, name="party-results"),
    #path("results/summary/", views.votes_breakdown, name="voting-summary"),
    path("results/seats/", views.seats_summary, name="seats-summary"),
]