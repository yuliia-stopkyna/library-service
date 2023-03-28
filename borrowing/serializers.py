from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book
from book.serializers import BookSerializer
from borrowing.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingReadSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True, many=False)
    user = serializers.CharField(source="user.get_full_name", read_only=True)


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
            "user",
        )

    def validate(self, attrs) -> dict:
        data = super().validate(attrs=attrs)
        if attrs["book"].inventory > 0:
            return data
        raise ValidationError(detail="Book inventory is 0.")

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data["book"]
            borrowing = Borrowing.objects.create(**validated_data)
            Book.objects.filter(pk=book.id).update(inventory=book.inventory - 1)
            return borrowing
