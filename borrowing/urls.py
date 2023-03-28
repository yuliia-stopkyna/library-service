from django.urls import path

from borrowing.views import BorrowingViewSet, BorrowingReturnAPIView

app_name = "borrowing"

borrowing_list = BorrowingViewSet.as_view(actions={"get": "list", "post": "create"})

borrowing_detail = BorrowingViewSet.as_view(actions={"get": "retrieve"})

urlpatterns = [
    path("", borrowing_list, name="borrowing-list"),
    path("<int:pk>/", borrowing_detail, name="borrowing-detail"),
    path("<int:pk>/return/", BorrowingReturnAPIView.as_view(), name="borrowing-return"),
]
