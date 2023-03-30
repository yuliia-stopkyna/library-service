from django.db.models import QuerySet
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

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
