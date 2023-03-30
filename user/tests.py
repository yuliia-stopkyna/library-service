from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user.serializers import UserSerializer

USER_CREATE_URL = reverse("user:create")
USER_MANAGE_URL = reverse("user:manage")


class UnauthenticatedUserTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_user_with_email(self):
        data = {"email": "test@test.com", "password": "test12345"}
        self.client.post(USER_CREATE_URL, data=data)

        user = get_user_model().objects.filter(email="test@test.com")

        self.assertEqual(user.count(), 1)


class AuthenticatedUserTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user1 = get_user_model().objects.create_user(
            email="firstuser@test.com", password="test12345"
        )
        self.user2 = get_user_model().objects.create_user(
            email="seconduser@test.com", password="test12345"
        )
        self.client.force_authenticate(self.user1)

    def test_user_manage_view(self):
        res = self.client.get(USER_MANAGE_URL)
        serializer_user1 = UserSerializer(self.user1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer_user1.data)
        self.assertNotEqual(res.data["email"], self.user2.email)
