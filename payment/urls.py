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
    path(
        "success/",
        PaymentViewSet.as_view(actions={"get": "success"}),
        name="payment-success",
    ),
    path(
        "cancel/",
        PaymentViewSet.as_view(actions={"get": "cancel"}),
        name="payment-cancel",
    ),
]
