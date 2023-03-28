from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowing.models import Borrowing
from borrowing.serializers import (
    BorrowingReadSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)


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


class BorrowingReturnAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            borrowing = get_object_or_404(Borrowing, pk=pk)
            book = borrowing.book
            actual_return_date = timezone.now().date()
            serializer = BorrowingReturnSerializer(
                borrowing, data={"actual_return_date": actual_return_date}, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                book.inventory += 1
                book.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
