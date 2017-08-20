from channels.auth import channel_session_user_from_http, channel_session_user
from django.utils import timezone

from foodsaving.subscriptions.models import Subscription, SubscriptionTypus


@channel_session_user_from_http
def ws_connect(message):
    """The user has connected! Register their channel subscription."""
    user = message.user
    if not user.is_anonymous():
        Subscription.objects.create(user=user, typus=SubscriptionTypus.WEBSOCKET, destination=message.reply_channel)
    message.reply_channel.send({"accept": True})


@channel_session_user
def ws_message(message):
    """They sent us a websocket message! We just update the Subscription lastseen time.."""
    user = message.user
    if not user.is_anonymous():
        reply_channel = message.reply_channel.name
        Subscription.objects.filter(user=user, typus=SubscriptionTypus.WEBSOCKET, destination=reply_channel).update(lastseen_at=timezone.now())


@channel_session_user
def ws_disconnect(message):
    """The user has disconnected so we remove all their Subscriptions"""
    user = message.user
    if not user.is_anonymous():
        Subscription.objects.filter(user=user, typus=SubscriptionTypus.WEBSOCKET, destination=message.reply_channel).delete()
