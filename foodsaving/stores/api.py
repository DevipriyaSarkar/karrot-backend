from django.dispatch import Signal
from rest_framework import filters
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.compat import is_authenticated
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated, DjangoObjectPermissions
from rest_framework.viewsets import GenericViewSet

from foodsaving.stores.filters import PickupDatesFilter, PickupDateSeriesFilter
from foodsaving.stores.models import (
    Store as StoreModel,
    PickupDate as PickupDateModel,
    PickupDateSeries as PickupDateSeriesModel,
    Feedback as FeedbackModel
)
from foodsaving.stores.serializers import (
    StoreSerializer, PickupDateSerializer, PickupDateSeriesSerializer,
    PickupDateJoinSerializer, PickupDateLeaveSerializer, FeedbackSerializer)
from foodsaving.utils.mixins import PartialUpdateModelMixin

pre_pickup_delete = Signal()
pre_series_delete = Signal()
post_store_delete = Signal()


class StoreViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    Stores

    # Query parameters
    - `?group` - filter by store group id
    - `?search` - search in name and description
    """
    serializer_class = StoreSerializer
    queryset = StoreModel.objects.filter(deleted=False)
    filter_fields = ('group', 'name')
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    search_fields = ('name', 'description')
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(group__members=self.request.user)

    def perform_destroy(self, store):
        store.deleted = True
        store.save()
        post_store_delete.send(
            sender=self.__class__,
            group=store.group,
            store=store,
            user=self.request.user,
        )
        # implicit action: delete all pickups and series, but don't send out signals for them
        PickupDateModel.objects.filter(store=store).delete()
        PickupDateSeriesModel.objects.filter(store=store).delete()


class FeedbackViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    serializer_class = FeedbackSerializer
    queryset = FeedbackModel.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(about__store__group__members=self.request.user)


class PickupDateSeriesViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = PickupDateSeriesSerializer
    queryset = PickupDateSeriesModel.objects
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PickupDateSeriesFilter
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(store__group__members=self.request.user)

    def perform_destroy(self, series):
        pre_series_delete.send(
            sender=self.__class__,
            group=series.store.group,
            store=series.store,
            user=self.request.user,
        )
        super().perform_destroy(series)


class DjangoRulesPermissions(DjangoObjectPermissions):
    def has_permission(self, request, view):

        permission_names = getattr(view, 'permission_names', None)

        if permission_names is None:
            return super().has_permission(request, view)
        else:
            return (
                request.user and
                (is_authenticated(request.user) or not self.authenticated_users_only) and
                request.user.has_perms(permission_names)
            )

    def has_object_permission(self, request, view, obj):
        permission_names = getattr(view, 'permission_names', None)

        user = request.user

        if permission_names is None:
            return super().has_object_permission(request, view, obj)
        else:
            # doesn't do that fancy 404 vs 403 thing... but is simpler
            return user.has_perms(permission_names, obj)


class PickupDateViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    """
    Pickup Dates

    # Query parameters
    - `?series` - filter by pickup date series id
    - `?store` - filter by store id
    - `?group` - filter by group id
    - `?date_0=<from_date>`&`date_1=<to_date>` - filter by date, can also either give date_0 or date_1
    """
    serializer_class = PickupDateSerializer
    queryset = PickupDateModel.objects.filter(deleted=False)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = PickupDatesFilter
    permission_classes = (DjangoRulesPermissions,)
    permission_names = None

    def get_queryset(self):
        if self.request.user.is_anonymous:
            return self.queryset.none()
        return self.queryset.filter(store__group__members=self.request.user)

    def perform_destroy(self, pickup):
        # set deleted flag to make the pickup date invisible
        pickup.deleted = True

        pre_pickup_delete.send(
            sender=self.__class__,
            group=pickup.store.group,
            store=pickup.store,
            user=self.request.user
        )
        pickup.save()

    @detail_route(
        methods=['POST'],
        serializer_class=PickupDateJoinSerializer,
        permission_names=['stores.join_pickupdate']
    )
    def add(self, request, pk=None):
        return self.partial_update(request)

    @detail_route(
        methods=['POST'],
        serializer_class=PickupDateLeaveSerializer,
        permission_names=['stores.leave_pickupdate']
    )
    def remove(self, request, pk=None):
        return self.partial_update(request)
