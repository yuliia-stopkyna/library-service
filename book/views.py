from rest_framework import viewsets

from book.models import Book
from book.serializers import BookSerializer, BookListSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()

    def get_serializer_class(self) -> BookSerializer | BookListSerializer:
        if self.action == "list":
            return BookListSerializer
        return BookSerializer
