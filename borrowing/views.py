from rest_framework import mixins, viewsets

from borrowing.models import Borrowing
from borrowing.serializers import BorrowingReadSerializer, BorrowingCreateSerializer


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        queryset = Borrowing.objects.select_related("book", "user")
        if not self.request.user.is_staff:
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return BorrowingReadSerializer
        if self.action == "create":
            return BorrowingCreateSerializer

    def perform_create(self, serializer) -> None:
        serializer.save(user=self.request.user)
