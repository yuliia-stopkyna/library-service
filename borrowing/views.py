from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from borrowing.models import Borrowing
from borrowing.serializers import BorrowingReadSerializer, BorrowingCreateSerializer


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        queryset = Borrowing.objects.select_related("book", "user")

        if is_active and is_active.lower() == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        if self.request.user.is_staff and user_id:
            queryset = queryset.filter(user_id=int(user_id))

        return queryset

    def get_serializer_class(
        self,
    ) -> BorrowingReadSerializer | BorrowingCreateSerializer:
        if self.action in ("list", "retrieve"):
            return BorrowingReadSerializer
        if self.action == "create":
            return BorrowingCreateSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
