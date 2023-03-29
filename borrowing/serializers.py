from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from book.models import Book
from book.serializers import BookSerializer
from borrowing.models import Borrowing
from borrowing.notifications import send_telegram_notification
from borrowing.utils import get_borrowing_info
from payment.serializers import PaymentSerializer
from payment.utils import create_stripe_session


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


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True, many=False)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    payments = PaymentSerializer(read_only=True, many=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user_id",
            "user_full_name",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
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
            create_stripe_session(borrowing)
            Book.objects.filter(pk=book.id).update(inventory=book.inventory - 1)
            message = "New borrowing created:\n" + get_borrowing_info(borrowing)
            send_telegram_notification(message)

            return borrowing


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date")

    def validate(self, attrs) -> dict:
        if self.instance.actual_return_date is not None:
            raise ValidationError(detail="Borrowing has been already returned.")
        return super().validate(attrs=attrs)
