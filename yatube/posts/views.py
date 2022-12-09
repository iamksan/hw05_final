from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Comment, Follow
from .utils import paginations


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paginations(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    post_list = Post.objects.select_related('group')
    page_obj = paginations(request, post_list)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, template, context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = (
        Post.objects.select_related("author", "group")
        .filter(author=profile).all()
    )
    posts_count = post_list.count()
    page_obj = paginations(request, post_list)
    context = {
        'profile': profile,
        'posts_count': posts_count,
        'page_obj': page_obj,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница поста и количество постов пользователя."""

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = Comment.objects.select_related('post')
    template = "posts/post_detail.html"
    context = {
        "post": post,
        "form": form,
        "comments": comments
    }

    return render(request, template, context)


@login_required(login_url="users:login")
def post_create(request):
    """Добавления поста."""

    template = "posts/create_post.html"

    form = PostForm(request.POST or None)
    context = {
        "form": form,
    }
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.save()
        return redirect("posts:profile", request.user)

    return render(request, template, context)


@login_required(login_url="users:login")
def post_edit(request, post_id):
    """Редактирование поста. Доступно только автору."""

    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        "form": form,
        "is_edit": True,
    }
    template = "posts/create_post.html"
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginations(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def follow_can_be_created(user, author):
    following_exists = Follow.objects.filter(
        author=author,
        user=user
    ).exists()
    return (user != author and not following_exists)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginations(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get(
            user=request.user,
            author=author
        ).delete()
    return redirect("posts:profile", username)
