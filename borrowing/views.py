from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status
from rest_framework.pagination import PageNumberPagination
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
from payment.utils import create_stripe_session


class BorrowingPagination(PageNumberPagination):
    page_size = 5


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    pagination_class = BorrowingPagination

    def get_queryset(self) -> QuerySet:
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        queryset = Borrowing.objects.select_related("book", "user").prefetch_related(
            "payments"
        )

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

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()

        if self.action == "create":
            context["request"] = self.request

        return context

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "is_active",
                type=bool,
                description="Filter by borrowing status: whether borrowing was returned or not",
            ),
            OpenApiParameter(
                "user_id",
                type=int,
                description="Filter borrowings by user id: available only for admin users",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class BorrowingReturnAPIView(APIView):
    """Endpoint for borrowing return"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        methods=["POST"],
        request=BorrowingReturnSerializer,
        responses={200: BorrowingReadSerializer},
    )
    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            borrowing = get_object_or_404(Borrowing, pk=pk)
            book = borrowing.book
            actual_return_date = timezone.now().date()
            expected_return_date = borrowing.expected_return_date

            serializer_update = BorrowingReturnSerializer(
                borrowing, data={"actual_return_date": actual_return_date}, partial=True
            )

            if serializer_update.is_valid():
                serializer_update.save()
                book.inventory += 1
                book.save()

                if actual_return_date > expected_return_date:
                    overdue = (actual_return_date - expected_return_date).days
                    create_stripe_session(
                        borrowing,
                        self.request,
                        payment_type="Fine",
                        overdue_days=overdue,
                    )

                    message = "Your return is overdue. Please provide fine payment."

                else:
                    message = "Your borrowing was successfully returned."

                serializer_read = BorrowingReadSerializer(borrowing)
                data = {"message": message, **serializer_read.data}

                return Response(data, status=status.HTTP_200_OK)

            return Response(
                serializer_update.errors, status=status.HTTP_400_BAD_REQUEST
            )
