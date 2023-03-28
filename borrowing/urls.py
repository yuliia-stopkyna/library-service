from django.urls import path

from borrowing.views import BorrowingListApiView, BorrowingRetrieveApiView

app_name = "borrowing"

urlpatterns = [
    path("", BorrowingListApiView.as_view(), name="borrowing-list"),
    path("<int:pk>/", BorrowingRetrieveApiView.as_view(), name="borrowing-detail")
]
