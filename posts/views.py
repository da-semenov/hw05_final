from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


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
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method != "POST":
        return render(request, "new.html", {"form": form,
                                            "is_edit": False})
    if not form.is_valid():
        return render(request, "new.html", {"form": form,
                                            "is_edit": False})
    form.instance.author = request.user
    form.save()
    return redirect("index")


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get("page")
    page = paginator.get_page(page_num)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    return render(request, "profile.html", {"author": author,
                                            "page": page,
                                            "following": following,
                                            "paginator": paginator})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    return render(request, "post.html", {"post": post,
                                         "author": post.author,
                                         "form": form,
                                         "comments": comments, })


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
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("post", username=post.author.username,
                            post_id=post_id)
    form = CommentForm()
    return redirect("post", username=post.author.username, post_id=post_id)


@login_required
def follow_index(request):
    author = get_object_or_404(User, username=request.user.username)
    post_list = (
        Post.objects.select_related("author").
        filter(author__following__user=request.user)
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page,
                  "paginator": paginator, "author": author})


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
