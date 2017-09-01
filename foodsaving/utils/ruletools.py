from functools import update_wrapper

import rules
from rest_framework import permissions
from rest_framework.fields import Field
from rules.predicates import NO_VALUE, Context, _context


class RulePermissionBase(permissions.BasePermission):
    rule = None

    def has_object_permission(self, request, view, pickup):
        permitted, message = self.rule.test_with_message(request.user, pickup)
        if permitted:
            return True
        else:
            return view.permission_denied(request, message=message)


def create_permission_class(classname, rule):
    return type(classname, (RulePermissionBase,), {'rule': rule})


def _build_actions_dict(ruleset, user, obj):
    actions = {}
    for name in ruleset:
        allowed, message = ruleset[name].test_with_message(user, obj)
        actions[name] = {'allowed': allowed}
        if not allowed:
            actions[name]['reason'] = message
    return actions


class RulesetSerializerField(Field):
    def __init__(self, ruleset, **kwargs):
        self.ruleset = ruleset
        kwargs['source'] = '*'
        kwargs['read_only'] = True
        super(RulesetSerializerField, self).__init__(**kwargs)

    def to_representation(self, value):
        if self.context.get('request', None):
            user = self.context['request'].user
            return _build_actions_dict(self.ruleset, user, value)
        else:
            return None


class Predicate(rules.Predicate):
    def __init__(self, fn, name=None, bind=False, messages=None):
        super().__init__(fn, name=name, bind=bind)
        self.messages = messages

    def __invert__(self):
        def INVERT(*args):
            result = self._apply(*args)
            return None if result is None else not result

        if self.name.startswith('~'):
            name = self.name[1:]
        else:
            name = '~' + self.name

        messages = (self.messages[1], self.messages[0])
        return type(self)(INVERT, name, messages=messages)

    def _apply(self, *args):
        result = super()._apply(*args)
        if result is False and self.messages:
            self.context['message'] = self.messages[1]
        return result

    def test_with_message(self, obj=NO_VALUE, target=NO_VALUE):
        args = tuple(arg for arg in (obj, target) if arg is not NO_VALUE)
        _context.stack.append(Context(args))
        rules.predicates.logger.debug('Testing %s', self)
        try:
            result = bool(self._apply(*args))
            if result:
                return result, None
            else:
                return result, self.context.get('message', None)

        finally:
            _context.stack.pop()


def predicate(fn=None, name=None, messages=None, **options):
    if not name and not callable(fn):
        name = fn
        fn = None

    def inner(fn):
        if isinstance(fn, Predicate):
            return fn
        p = Predicate(fn, name, messages=messages, **options)
        update_wrapper(p, fn)
        return p

    if fn:
        return inner(fn)
    else:
        return inner
