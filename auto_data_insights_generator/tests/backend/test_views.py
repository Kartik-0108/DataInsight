"""
Backend test suite for Auto Data Insights Generator.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User


class UserAuthTests(TestCase):
    """Tests for user authentication flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_register_page_loads(self):
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post('/users/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_profile_requires_login(self):
        response = self.client.get('/users/profile/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_upload_requires_login(self):
        response = self.client.get('/upload/')
        self.assertEqual(response.status_code, 302)


class HomePageTests(TestCase):
    """Tests for the home page."""

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DataInsights')
