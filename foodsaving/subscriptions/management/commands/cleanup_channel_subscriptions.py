from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from foodsaving.subscriptions.models import Subscription, SubscriptionTypus


class Command(BaseCommand):
    """If we have not received a message a websocket channel for a while, we delete our entries."""

    def handle(self, *args, **options):
        Subscription.objects.filter(typus=SubscriptionTypus.WEBSOCKET, lastseen_at__lt=timezone.now() - relativedelta(minutes=5)).delete()
