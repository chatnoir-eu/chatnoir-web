from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from chatnoir_api.models import ApiPendingUser


class Command(BaseCommand):
    help = 'Delete unverified pending API users older than the configured age threshold.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=48,
            help='Delete pending users older than this many hours (default: 48).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many pending users would be deleted without deleting them.',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        queryset = ApiPendingUser.objects.filter(email_verified=False, created_at__lt=cutoff)
        count = queryset.count()

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'Would delete {count} unverified pending API user(s) older than {options["hours"]} hours.'
            ))
            return

        with transaction.atomic():
            for pending_user in queryset.iterator():
                pending_user.delete()

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {count} unverified pending API user(s) older than {options["hours"]} hours.'
        ))
