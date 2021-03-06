from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    group = Post.objects.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'page': page,
        'group': group
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by("-pub_date")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        "group": group,
        "page": page
    }

    return render(request, "posts/group.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all().order_by("-pub_date")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()

    context = {
        'page': page,
        'author': author,
        'posts_count': author.posts.count(),
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comment = Comment.objects.filter(post=post).order_by("-created")
    form = CommentForm()

    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()

    context = {
        "post": post,
        "author": post.author,
        "posts_count": post.author.posts.count(),
        "comments": comment,
        "form": form,
        'following': following,
    }

    return render(request, "posts/post.html", context)


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("post", username=username, post_id=post_id)
    else:
        form = CommentForm()

    context = {
        "form": form,
        "post": post,
        "comments": comments,
        "author": author,
    }

    return render(request, "posts/post.html", context)


@login_required
def new_post(request):
    is_new = True
    if request.method == "POST":
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    form = PostForm()

    context = {
        "form": form,
        "is_new": is_new,
    }

    return render(request, "posts/post_form.html", context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)

    if request.user == post.author:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None, instance=post)

        if form.is_valid():
            form.save()

            return redirect('post', username=username, post_id=post_id)

        context = {
            'form': form,
            'post': post
        }

        return render(request, 'posts/post_form.html', context)

    else:
        return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    # ???????????????????? ?? ?????????????? ???????????????????????? ???????????????? ?? ???????????????????? request.user
    post_list = Post.objects.filter(
        author__following__user=request.user).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {'page': page}

    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)

    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)

    if author != request.user:
        Follow.objects.filter(
            author__username=username, user=request.user).delete()

    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
