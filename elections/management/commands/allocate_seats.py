from django.core.management.base import BaseCommand
from elections.services.seat_allocation import (
    allocate_fptp_seats,
    allocate_pr_seats
)

class Command(BaseCommand):
    help = "Allocate FPTP and PR seats"

    def handle(self, *args, **options):
        allocate_fptp_seats()
        allocate_pr_seats()

        self.stdout.write(
            self.style.SUCCESS("Seat allocation completed successfully.")
        )