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
from payment.models import Payment
from payment.serializers import PaymentSerializer
from payment.utils import create_stripe_session


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


class BorrowingReturnAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: int) -> Response:
        with transaction.atomic():
            borrowing = get_object_or_404(Borrowing, pk=pk)
            book = borrowing.book
            actual_return_date = timezone.now().date()
            expected_return_date = borrowing.expected_return_date

            serializer = BorrowingReturnSerializer(
                borrowing, data={"actual_return_date": actual_return_date}, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                book.inventory += 1
                book.save()
                data = {**serializer.validated_data}

                if actual_return_date > expected_return_date:
                    overdue = (actual_return_date - expected_return_date).days
                    session = create_stripe_session(
                        borrowing,
                        self.request,
                        payment_type="Fine",
                        overdue_days=overdue,
                    )

                    payment = Payment.objects.get(session_id=session.id)
                    payment_serializer = PaymentSerializer(payment)
                    data.update(
                        {
                            "message": "Your return is overdue. Please provide fine payment.",
                            **payment_serializer.data,
                        }
                    )

                return Response(data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
