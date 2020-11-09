from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.title}"


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        "date published", 
        auto_now_add=True,
        db_index=True,
        )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="posts",
        )
    group = models.ForeignKey(
        Group, 
        on_delete=models.SET_NULL, 
        related_name="posts", 
        blank=True, null=True,
        )

    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return f"{self.text}", self.image
    
    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE, 
        related_name="comments",
        )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="comments",
        )
    text = models.TextField()
    created = models.DateTimeField(
        "date published", 
        auto_now_add=True,
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="follower",
        )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="following",
        )
