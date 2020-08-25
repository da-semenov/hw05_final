from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page,
                                          "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page,
                                          "paginator": paginator})


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    form = PostForm(files=request.FILES or None)
    return render(request, "new.html", {"form": form,
                                        "is_edit": False})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get("page")
    page = paginator.get_page(page_num)
    posts_count = posts.count()
    following_count = author.following.count()
    follower_count = author.follower.count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    return render(request, "profile.html", {"author": author,
                                            "page": page,
                                            "following": following,
                                            "paginator": paginator,
                                            "posts_count": posts_count,
                                            "following_count": following_count,
                                            "follower_count": follower_count,
                                            })


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    following_count = user.following.count()
    follower_count = user.follower.count()
    posts_count = Post.objects.filter(author=user).count()
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=user).exists()
    return render(request, "post.html", {"post": post,
                                         "author": post.author,
                                         "form": form,
                                         "comments": comments,
                                         "following_count": following_count,
                                         "follower_count": follower_count,
                                         "posts_count": posts_count,
                                         "following": following, })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "new.html", {"form": form, "post": post,
                                        "is_edit": True})


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path},
                  status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("post", username, post_id)
    return redirect("post", username, post_id)


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).all()
    authors = []
    for author in following:
        authors.append(author.author.id)
    posts = Post.objects.filter(author__in=authors).all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page,
                                           "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not request.user == author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect("follow_index")
