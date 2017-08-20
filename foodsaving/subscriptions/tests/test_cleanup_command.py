from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from foodsaving.subscriptions.models import Subscription, SubscriptionTypus
from foodsaving.users.factories import UserFactory


class CleanupChannelCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.subscription = Subscription.objects.create(user=cls.user, typus=SubscriptionTypus.WEBSOCKET, destination='foo')

    def test_keeps_recent_entries(self):
        self.set_lastseen_ago_in_minutes(3)
        call_command('cleanup_channel_subscriptions')
        self.assertIsNotNone(Subscription.objects.get(pk=self.subscription.id))

    def test_deletes_old_entries(self):
        self.set_lastseen_ago_in_minutes(10)
        call_command('cleanup_channel_subscriptions')
        with self.assertRaises(Subscription.DoesNotExist):
            self.assertIsNone(Subscription.objects.get(pk=self.subscription.id))

    def set_lastseen_ago_in_minutes(self, minutes):
        self.subscription.lastseen_at = timezone.now() - relativedelta(minutes=minutes)
        self.subscription.save()
