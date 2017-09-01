import rules
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rules import predicate, is_authenticated


@predicate
def is_pickup_upcoming(user, pickup):
    if not pickup:
        return None
    return pickup.date > timezone.now() + relativedelta(minutes=1)


@predicate
def is_pickup_full(user, pickup):
    if not pickup:
        return None
    if not pickup.max_collectors:
        return False
    return pickup.collectors.count() >= pickup.max_collectors


@predicate
def is_pickup_collector(user, pickup):
    if not pickup:
        return None
    return pickup.collectors.filter(id=user.id).exists()


@predicate
def is_pickup_empty(user, pickup):
    if not pickup:
        return None
    return pickup.collectors.count() == 0


rules.add_perm('stores.add_pickupdate', is_authenticated)
rules.add_perm('stores.delete_pickupdate', is_authenticated & is_pickup_upcoming & is_pickup_empty)
rules.add_perm('stores.change_pickupdate', is_authenticated & is_pickup_upcoming)
rules.add_perm('stores.join_pickupdate',
               is_authenticated & is_pickup_upcoming & ~is_pickup_full & ~is_pickup_collector)
rules.add_perm('stores.leave_pickupdate', is_authenticated & is_pickup_upcoming & is_pickup_collector)
