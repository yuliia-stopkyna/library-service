import stripe
from django.db.models import QuerySet
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from payment.models import Payment
from payment.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        queryset = Payment.objects.select_related("borrowing")

        if not self.request.user.is_staff:
            return queryset.filter(borrowing__user=self.request.user)

        return queryset

    @action(
        methods=["GET"], detail=False, url_path="success", url_name="payment-success"
    )
    def success(self, request: Request) -> Response:
        """Endpoint for successful stripe payment session"""
        session_id = request.query_params.get("session_id")
        payment = Payment.objects.get(session_id=session_id)
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            serializer = PaymentSerializer(
                payment, data={"status": "Paid"}, partial=True
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
