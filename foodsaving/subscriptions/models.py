from django.db.models import ForeignKey, TextField, DateTimeField
from django.utils import timezone
from django_enumfield import enum

from config import settings
from foodsaving.base.base_models import BaseModel


class SubscriptionTypus(enum.Enum):
    WEBSOCKET = 0  # django channels websocket channel


class Subscription(BaseModel):
    """A subscription to receive messages over variety of mechanisms."""

    user = ForeignKey(settings.AUTH_USER_MODEL)
    typus = enum.EnumField(SubscriptionTypus, default=SubscriptionTypus.WEBSOCKET)

    # where to send the message to, depends on subscription type
    # WEBSOCKET = a django channels reply_channel value
    destination = TextField()

    # websocket subscriptions should expire if not seen for a while, other types may not use this
    lastseen_at = DateTimeField(default=timezone.now, null=True)
