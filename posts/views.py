from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required
from .forms import CommentForm, PostForm
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page, 
                  "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "posts": posts, 
                  "paginator": paginator, "page": page})


@login_required
def new_post(request):
    if request.method != "POST":
        form = PostForm()
        return render(request, "new.html", {"form": form})
    form = PostForm(request.POST, files=request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new.html", {"form": form})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = author.following.filter(user=user.id).exists()
    following = author.following.count()
    follower = author.follower.count()
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "profile.html", {"paginator": paginator, 
                  "page": page, "author": author, "following": following, 
                  "follow": follow, "follower": follower})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author = post.author
    form = CommentForm()
    comments = post.comments.all()
    posts = Post.objects.filter(author__username=username)
    count_posts = len(posts)
    return render(request, "post.html", {"post": post, "author": author, "form": form, "comments": comments, "count_posts": count_posts})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    profile = get_object_or_404(User, username=username)

    if post.author != request.user:
        return redirect(reverse("post", kwargs={"post": post}))
    
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(reverse("post", kwargs={"username": username, 
                            "post_id": post.pk}))
    form = PostForm(instance=post)
    return render(request, "new.html", {"form": form, "post": post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=request.user)
    if request.method != "POST":
        form = CommentForm()
        return redirect("post", username, post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = author
        comment.save()
        return redirect("post", username, post_id)
    return redirect("post", username, post_id)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    user = request.user
    authors = Follow.objects.values("author").filter(user=request.user)    
    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    url = reverse("profile", kwargs={"username": author.username})
    if user == author:
        return redirect(url)
    follow = author.following.filter(user=user.id).exists()
    if follow:
        return redirect(url)
    follow = Follow.objects.create(author=author, user=user)    
    follow.save()
    return redirect(url)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    follow = Follow.objects.get(author=author, user=user)
    follow.delete()
    url = reverse("profile", kwargs={"username": author.username})
    return redirect(url)
