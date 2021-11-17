from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import PAGINATOR_COUNT

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    template = 'posts/index.html'
    index = True
    post_list = cache.get('index_page')
    if not post_list:
        post_list = Post.objects.select_related('group')
        cache.set('index_page', post_list, timeout=20)
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': index
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    profile = get_object_or_404(User, username=username)

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            author=profile,
            user=request.user
        ).exists()
    else:
        following = False
    post_list = Post.objects.filter(author=profile)
    post_count = post_list.count()
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    profile = get_object_or_404(User, username=post.author)
    comments = Comment.objects.filter(post=post.pk)
    posts_count = Post.objects.filter(author=profile).count()
    form = CommentForm(
        request.POST or None,
        files=request.FILES or None
    )
    context = {
        'post': post,
        'posts_count': posts_count,
        'profile': profile,
        'comments': comments,
        'form': form,

    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)

    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    is_edit = True

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'is_edit': is_edit,
        'form': form,
        'post_id': post_id
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follow = True
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, PAGINATOR_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow': follow
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
