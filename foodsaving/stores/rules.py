from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rules import RuleSet

from foodsaving.utils.ruletools import predicate, create_permission_class


# a bunch of predicates

@predicate(messages=('Pickup is in the future', 'Pickup is in the past'))
def is_pickup_upcoming(_, pickup):
    if not pickup:
        return None
    return pickup.date > timezone.now() + relativedelta(minutes=1)


@predicate(messages=('Pickup is full', 'Pickup is not full'))
def is_pickup_full(_, pickup):
    if not pickup:
        return None
    if not pickup.max_collectors:
        return False
    return pickup.collectors.count() >= pickup.max_collectors


@predicate(messages=('You are a pickup collector', 'You are not a pickup collector'))
def is_pickup_collector(user, pickup):
    if not pickup:
        return None
    return pickup.collectors.filter(id=user.id).exists()


@predicate(messages=('Pickup is empty', 'Pickup is not empty'))
def is_pickup_empty(_, pickup):
    if not pickup:
        return None
    return pickup.collectors.count() == 0


# combine predicates to make our main rules (they are still predicates themselves)
# don't need to define them separately, but makes them usable anywhere

can_delete_pickup = is_pickup_upcoming & is_pickup_empty
can_edit_pickup = is_pickup_upcoming
can_join_pickup = is_pickup_upcoming & ~is_pickup_full & ~is_pickup_collector
can_leave_pickup = is_pickup_upcoming & is_pickup_collector

# put the rules in a RuleSet (which is basically just a dict)
# this is used to choose what to show in a serializer

pickup_rules = RuleSet()

pickup_rules.add_rule('delete', can_delete_pickup)
pickup_rules.add_rule('edit', can_edit_pickup)
pickup_rules.add_rule('join', can_join_pickup)
pickup_rules.add_rule('leave', can_leave_pickup)

# create some rest framework permissions classes from the rules
# will raise errors using the messages defined in the predicates

CanDeletePickup = create_permission_class('CanDeletePickup', can_delete_pickup)
CanEditPickup = create_permission_class('CanEditPickup', can_edit_pickup)
CanJoinPickup = create_permission_class('CanJoinPickup', can_join_pickup)
CanLeavePickup = create_permission_class('CanLeavePickup', can_leave_pickup)
