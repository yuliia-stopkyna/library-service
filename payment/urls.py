from django.urls import path

from payment.views import PaymentViewSet

app_name = "payment"

urlpatterns = [
    path("", PaymentViewSet.as_view(actions={"get": "list"}), name="payment-list"),
    path(
        "<int:pk>/",
        PaymentViewSet.as_view(actions={"get": "retrieve"}),
        name="payment-detail",
    ),
]
