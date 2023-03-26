from rest_framework import generics

from borrowing.models import Borrowing
from borrowing.serializers import BorrowingReadSerializer


class BorrowingListApiView(generics.ListAPIView):
    serializer_class = BorrowingReadSerializer
    queryset = Borrowing.objects.select_related("book", "user")


class BorrowingRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = BorrowingReadSerializer
    queryset = Borrowing.objects.select_related("book", "user")
