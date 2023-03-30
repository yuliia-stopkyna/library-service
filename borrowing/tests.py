import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from book.models import Book
from borrowing.models import Borrowing
from borrowing.serializers import BorrowingReadSerializer

BORROWINGS_URL = reverse("borrowing:borrowing-list")


def create_book() -> Book:
    return Book.objects.create(
        title="Test book",
        author="Test Author",
        cover="Soft",
        inventory=20,
        daily_fee=1.99,
    )


class UnauthenticatedBorrowingTests(TestCase):
    def test_auth_required(self):
        self.client = APIClient()
        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user1 = get_user_model().objects.create_user(
            email="firstuser@test.com", password="test12345"
        )
        self.user2 = get_user_model().objects.create_user(
            email="seconduser@test.com", password="test12345"
        )
        self.book = create_book()
        self.user1_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
            book=self.book,
            user=self.user1,
        )
        self.user2_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timezone.timedelta(days=14),
            book=self.book,
            user=self.user2,
        )
        self.client.force_authenticate(self.user1)

    def test_borrowings_list_user(self):
        res = self.client.get(BORROWINGS_URL)
        serializer_user1 = BorrowingReadSerializer(self.user1_borrowing)
        serializer_user2 = BorrowingReadSerializer(self.user2_borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_user1.data, res.data["results"])
        self.assertNotIn(serializer_user2.data, res.data["results"])

    def test_borrowings_list_is_active_filter(self):
        self.user1_borrowing_returned = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timezone.timedelta(days=1),
            actual_return_date=timezone.now().date(),
            book=self.book,
            user=self.user1,
        )
        res = self.client.get(BORROWINGS_URL, data={"is_active": "true"})
        serializer_active = BorrowingReadSerializer(self.user1_borrowing)
        serializer_returned = BorrowingReadSerializer(self.user1_borrowing_returned)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_active.data, res.data["results"])
        self.assertNotIn(serializer_returned.data, res.data["results"])

    def test_retrieve_borrowing(self):
        detail_url = reverse(
            "borrowing:borrowing-detail", args=[self.user1_borrowing.id]
        )
        res = self.client.get(detail_url)
        serializer = BorrowingReadSerializer(self.user1_borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_borrowing_create(self):
        new_book = Book.objects.create(
            title="Borrowing create test book",
            author="Author",
            cover="Hard",
            inventory=5,
            daily_fee=2.99,
        )
        data = {
            "expected_return_date": timezone.now().date() + timezone.timedelta(days=8),
            "book": new_book.id,
        }
        res_post = self.client.post(BORROWINGS_URL, data=data)

        new_borrowing = Borrowing.objects.get(book=new_book)
        serializer = BorrowingReadSerializer(new_borrowing)
        detail_url = reverse("borrowing:borrowing-detail", args=[new_borrowing.id])
        res_detail = self.client.get(detail_url)

        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        self.assertEqual(serializer.data, res_detail.data)
        self.assertEqual(new_borrowing.book.inventory, 4)

    def test_borrowing_return(self):
        before_url = reverse(
            "borrowing:borrowing-detail", args=[self.user1_borrowing.id]
        )
        res_before = self.client.get(before_url)
        return_url = reverse(
            "borrowing:borrowing-return", args=[self.user1_borrowing.id]
        )
        res_return = self.client.post(return_url)
        res_double_return = self.client.post(return_url)
        string_return_date = res_return.data["actual_return_date"]
        return_date = datetime.datetime.strptime(string_return_date, "%Y-%m-%d").date()

        self.assertEqual(res_return.status_code, status.HTTP_200_OK)
        self.assertEqual(return_date, timezone.now().date())
        self.assertEqual(res_double_return.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res_double_return.data["non_field_errors"][0],
            "Borrowing has been already returned.",
        )
        self.assertEqual(
            res_return.data["book"]["inventory"],
            res_before.data["book"]["inventory"] + 1,
        )


class AdminBorrowingTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com", password="test12345"
        )
        self.book = create_book()
        self.user_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timezone.timedelta(days=7),
            book=self.book,
            user=self.user,
        )
        self.admin_borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timezone.timedelta(days=14),
            book=self.book,
            user=self.admin,
        )
        self.client.force_authenticate(self.admin)

    def test_user_id_filter(self):
        res = self.client.get(BORROWINGS_URL, data={"user_id": str(self.user.id)})
        serializer_user = BorrowingReadSerializer(self.user_borrowing)
        serializer_admin = BorrowingReadSerializer(self.admin_borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_user.data, res.data["results"])
        self.assertNotIn(serializer_admin.data, res.data["results"])
