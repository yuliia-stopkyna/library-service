from rest_framework import serializers

from book.serializers import BookSerializer
from borrowing.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "actual_return_date", "book", "user")


class BorrowingReadSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True, many=False)
    user = serializers.CharField(source="user.get_full_name", read_only=True)
