from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from book.models import Book
from book.serializers import BookListSerializer, BookSerializer

BOOKS_URL = reverse("book:book-list")
BOOK_URL = reverse("book:book-detail", args=[1])


def books_create() -> None:
    book_data = (
        ("Book1", "Author1", "Hard", 5, 1.99),
        ("Book2", "Author2", "Hard", 5, 1.99),
        ("Book3", "Author3", "Hard", 5, 1.99),
    )
    for title, author, cover, inventory, daily_fee in book_data:
        Book.objects.create(
            title=title,
            author=author,
            cover=cover,
            inventory=inventory,
            daily_fee=daily_fee,
        )


class UnauthenticatedBookTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        books_create()

    def test_book_list(self):
        res = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for book in serializer.data:
            self.assertIn(book, res.data["results"])

    def test_auth_required(self):
        res = self.client.get(BOOK_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBookTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        books_create()
        self.user = get_user_model().objects.create_user(
            email="user@test.com", password="test12345"
        )
        self.client.force_authenticate(self.user)

    def test_book_retrieve(self):
        res = self.client.get(BOOK_URL)
        book = Book.objects.get(pk=1)
        serializer = BookSerializer(book)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_permission_required(self):
        new_book = {
            "title": "Test book",
            "author": "Test author",
            "cover": "Hard",
            "inventory": 5,
            "daily_fee": 1.99,
        }
        res_post = self.client.post(BOOKS_URL, data=new_book)
        res_delete = self.client.delete(BOOK_URL)
        res_put = self.client.put(BOOK_URL, data=new_book)
        res_patch = self.client.patch(BOOK_URL, data={"title": "Patched"})
        responses = [res_post, res_put, res_patch, res_delete]

        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminBookTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        books_create()
        self.admin = get_user_model().objects.create_superuser(
            email="user@test.com", password="test12345"
        )
        self.client.force_authenticate(self.admin)

    def test_book_create(self):
        new_book = {
            "title": "Test book",
            "author": "Test author",
            "cover": "Hard",
            "inventory": 5,
            "daily_fee": 1.99,
        }
        res_post = self.client.post(BOOKS_URL, data=new_book)
        book = Book.objects.get(title=new_book["title"])
        new_book_url = reverse("book:book-detail", args=[book.id])
        res_detail = self.client.get(new_book_url)
        serializer = BookSerializer(book)

        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        self.assertEqual(serializer.data, res_detail.data)

    def test_book_update(self):
        new_book_info = {
            "title": "Updated title",
            "author": "Updated author",
            "cover": "Soft",
            "inventory": 3,
            "daily_fee": 3.99,
        }
        res_put = self.client.put(BOOK_URL, data=new_book_info)
        res_detail = self.client.get(BOOK_URL)

        self.assertEqual(res_put.status_code, status.HTTP_200_OK)
        self.assertEqual(new_book_info["title"], res_detail.data["title"])
        self.assertEqual(new_book_info["author"], res_detail.data["author"])
        self.assertEqual(new_book_info["cover"], res_detail.data["cover"])
        self.assertEqual(new_book_info["inventory"], res_detail.data["inventory"])
        self.assertEqual(
            new_book_info["daily_fee"], float(res_detail.data["daily_fee"])
        )

    def test_book_delete(self):
        res_delete = self.client.delete(BOOK_URL)
        empty_queryset = Book.objects.filter(pk=1)

        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(empty_queryset.count(), 0)
