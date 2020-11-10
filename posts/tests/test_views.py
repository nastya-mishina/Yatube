from django.test import TestCase
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from posts.models import Post, Group
from django.shortcuts import reverse
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from io import BytesIO
from PIL import Image

User = get_user_model()


class StaticURLTests(TestCase):
    def test_homepage(self):
        client = Client()
        url = reverse("index")
        response = client.get(url)
        cache.clear()
        self.assertEqual(response.status_code, 200)


class Test(TestCase):
    @classmethod
    def setUp(cls):
        super().setUpClass()
        cache.clear()
        cls.user_auth = User.objects.create_user(username="NastyaMishina")
        cls.user_auth.save()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_auth)
        cls.unauthorized_client = Client()
        cls.group = Group.objects.create(title="test_title", 
                    slug="test_slug", description="test_description")
        cls.key = make_template_fragment_key("index_page")
        
        cls.img = BytesIO()
        cls.image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
        cls.image.save(cls.img, 'png')
        cls.img.name = 'test.png'
        cls.img.seek(0)

    def test_profile(self):
        self.username = self.user_auth.username
        url = reverse("profile", kwargs={"username": self.username})
        response = self.authorized_client.get(url)
        cache.clear()
        self.assertEqual(response.status_code, 200)


    def test_post_new_auth(self):
        current_posts_count = Post.objects.count()
        url = reverse("new_post")
        text = "Это текст публикации"
        response = self.authorized_client.post(url, {'author': self.user_auth,
                  "group": self.group.pk, 'text': text}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count +1)
        post = Post.objects.first()
        cache.clear()
        self.assertEqual(text, post.text)
        self.assertEqual(self.group, post.group)
        self.assertEqual(self.user_auth, post.author)
        

    def test_link_pages(self):
        url = reverse("new_post")
        text = "Это текст публикации"
        response = self.authorized_client.post(url, {"text": text, 
                  "author": self.user_auth}, follow=True)
        
        url_index = reverse("index")
        url_profile = reverse("profile", kwargs={"username": self.user_auth.username})
        url_post = reverse("post", kwargs={"username": self.user_auth.username, 
                      "post_id": Post.objects.first().pk})
        
        cache.clear()
        
        list_link_pages = [url_index, url_profile, url_post]
        for url in list_link_pages:
            response = self.authorized_client.get(url)
            paginator = response.context.get("paginator")
            if paginator is not None:
                post = response.context["page"][0]
            else:
                post = response.context["post"]
            self.assertEqual(Post.objects.all()[0], post)
        

    def test_post_new_not_auth(self):
        current_posts_count = Post.objects.count()
        url = reverse("new_post")
        response = self.unauthorized_client.post(url, {"text": "Это текст публикации", 
                  "group": self.group.pk, "author": self.user_auth}, follow=True)
        url = reverse("login") + "?next=" + reverse("new_post")
        cache.clear()
        self.assertRedirects(response, url, status_code=302, target_status_code=200)
        self.assertEqual(Post.objects.count(), current_posts_count)


    def test_post_edit(self):
        text = "hello"
        text_edit = "hello world"

        post = Post.objects.create(text=text, author=self.user_auth, group=self.group)
        url = reverse("post_edit", kwargs={"username": self.user_auth.username, "post_id": post.pk})
        self.authorized_client.post(url, {"text": text_edit}, follow=True)
        post_edited = Post.objects.first()
        self.assertEqual(post, post_edited)

        url_index = reverse("index")
        url_profile = reverse("profile", kwargs={"username": self.user_auth.username})
        url_post = reverse("post", kwargs={"username": self.user_auth.username, "post_id": post.pk})

        cache.clear()
        
        list_link_pages = [url_index, url_profile, url_post]

        for url in list_link_pages:
            response = self.authorized_client.get(url)
            paginator = response.context.get("paginator")
            if paginator is not None:
                post = response.context["page"][0]
            else:
                post = response.context["post"]
            self.assertEqual(post.text, post_edited.text)
            self.assertEqual(post.author, post_edited.author)


    def test_page_not_found(self):
        url = reverse("page_not_found")
        response = self.authorized_client.get(url)
        cache.clear()
        self.assertEqual(response.status_code, 404)

    
    def test_post_with_image(self):
        url = reverse("new_post")
        response = self.authorized_client.post(url, {'author': self.user_auth, 
                  "group": self.group.pk, 'text': 'post with image', 'image': self.img})
        post = Post.objects.all()[0]
        url = reverse("post", kwargs={"username": self.user_auth.username, "post_id": post.pk})
        response = self.authorized_client.get(url)
        cache.clear()
        self.assertContains(response, "<img")
        

    def test_all_pages_image(self):
        url = reverse("new_post")
        
        response = self.authorized_client.post(url, {'author': self.user_auth, 
                      "group": self.group.pk,'text': 'post with image', 'image': self.img}) 
        post = Post.objects.all()[0]

        url_index = reverse("index")
        url_profile = reverse("profile", kwargs={"username": self.user_auth.username})
        url_group_posts = reverse("group_posts", kwargs={"slug": self.group.slug})

        cache.clear()

        list_link_pages = [url_index, url_profile, url_group_posts]

        for url in list_link_pages:
            response = self.authorized_client.get(url)
            self.assertContains(response, "<img")


    def test_upload_not_image(self):
        url = reverse("new_post")

        with open('media/posts/text.txt','r', encoding='utf-8') as img:
            response = self.authorized_client.post(url, {'author': self.user_auth, 
                      "group": self.group.pk, 'text': 'post with image', 'image': img}) 
        count_posts = Post.objects.count()
        cache.clear()
        self.assertFormError(response, "form", "image", "Отправленный файл пуст.")


    def test_cache(self):
        url = reverse("index")
        old_response = self.authorized_client.get(url)
        post = Post.objects.create(text="Текст", author=self.user_auth, group=self.group)
        new_response = self.authorized_client.get(url)
        self.assertEqual(old_response.content, new_response.content)

        cache.touch(self.key, 0)
        newest_response = self.authorized_client.get(url)
        self.assertNotEqual(old_response.content, newest_response.content)


    def test_follow_auth(self):
        author = User.objects.create_user(username="MaksMishin")
        author.save()
        url_follow = reverse("profile_follow", kwargs={"username": author.username})
        response = self.authorized_client.post(url_follow, follow=True)
        self.assertEqual(response.status_code, 200)
        follow = author.following.filter(user=self.user_auth.id).exists()
        self.assertEqual(follow, True)

        
    def unfollow_auth(self):
        author = User.objects.create_user(username="MaksMishin")
        author.save()
        url_unfollow = reverse("profile_unfollow", kwargs={"username": author.username})
        response = self.authorized_client.post(url_unfollow, follow=True)
        self.assertEqual(response.status_code, 200)
        unfollow = author.following.filter(user=self.user_auth.id).exists()
        self.assertEqual(unfollow, False)


    def test_new_post_follow(self):
        author = User.objects.create_user(username="MaksMishin")
        author.save()
        other_user = User.objects.create_user(username="VasyaPupkin")
        other_user.save()
        url_follow = reverse("profile_follow", kwargs={"username": author.username})
        self.authorized_client.post(url_follow, follow=True)
        new_post = Post.objects.create(author=author,
                  group=self.group, text="Тук-тук") 
        other_client = Client()
        other_client.force_login(other_user)   
        url = reverse("follow_index")
        response_auth = self.authorized_client.get(url)
        response_other = other_client.get(url)
        
        paginator = response_auth.context.get("paginator")
        if paginator is not None:
            post = response_auth.context["page"][0]
        self.assertEqual(Post.objects.all()[0], post)

        paginator = response_other.context.get("paginator")
        count_posts = paginator.count
        self.assertEqual(count_posts, 0)


    def test_comment_auth(self):
        author = User.objects.create_user(username="MaksMishin")
        author.save()
        post = Post.objects.create(author=author,
                  group=self.group, text="Тук-тук")
                  
        url = reverse("post", kwargs={"username": post.author, "post_id": post.pk})
        response = self.authorized_client.get(url)
        self.assertContains(response, "<form")

        response = self.unauthorized_client.get(url)
        self.assertNotContains(response, "<form")
