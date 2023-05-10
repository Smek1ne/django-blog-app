from django.shortcuts import render, get_object_or_404
from .models import Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from environs import Env
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from .services import get_similar_posts, get_posts_from_page, send_post_recommendation

env = Env()
env.read_env()  # read .env txt file, if it exists


def post_list(request, tag_slug=None):
    posts = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 3)
    requested_page = request.GET.get('page', 1)
    posts_to_show = get_posts_from_page(paginator, requested_page)

    return render(request, 'blog/post/list.html',
                  {'posts': posts_to_show, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post, slug=post, status=Post.Status.PUBLISHED,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    comments = post.comments.filter(active=True)
    form = CommentForm()
    similar_posts = get_similar_posts(post)

    return render(
        request, 'blog/post/detail.html',
        {
            'post': post,
            'comments': comments,
            'form': form,
            'similar_posts': similar_posts
        }
    )


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        sent: bool = send_post_recommendation(request, form, post)
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html',
                  {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():  # server side check
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(request, 'blog/post/comment.html',
                  {'post': post, 'form': form, 'comment': comment})
