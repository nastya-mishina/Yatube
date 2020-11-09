from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post


User = get_user_model()


class StaticURLTests(TestCase):
    pass
  