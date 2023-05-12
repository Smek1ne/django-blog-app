from django.contrib.postgres.search import (SearchVector,
                                            SearchQuery,
                                            SearchRank, )
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from environs import Env
from taggit.models import Tag

from .forms import CommentForm, EmailPostForm, SearchForm
from .models import Post
from .services import (get_posts_from_page,
                       get_similar_posts,
                       retrieve_search_query, send_post_recommendation, )

env = Env()
env.read_env()  # read .env txt file, if it exists


def post_list(request, tag_slug: str = None):
    """
    Returns a rendered HTML template displaying a list of published posts,
    optionally filtered by tag.
    If there are no posts to display, an empty list will be shown.
    """
    posts = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 3)
    requested_page = request.GET.get('page', 1)
    posts_to_show = get_posts_from_page(paginator, requested_page)

    context = {'posts': posts_to_show, 'tag': tag}

    return render(request, 'blog/post/list.html', context)


def post_detail(request, year: int, month: int, day: int, post_slug: str):
    """
    Returns a rendered HTML template displaying a detail page
    of requested post by published date.
    """
    post_slug = get_object_or_404(
        Post,
        slug=post_slug,
        status=Post.Status.PUBLISHED,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )

    comments = post_slug.comments.filter(active=True)
    form = CommentForm()
    similar_posts = get_similar_posts(post_slug)

    context = {
        'post': post_slug,
        'comments': comments,
        'form': form,
        'similar_posts': similar_posts
    }
    return render(request, 'blog/post/detail.html', context)


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    """
    Displays a form to share a published post with other users via email.
    If the form is submitted, it sends a post recommendation email
    and updates the "sent" variable to True.
    """
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        sent = send_post_recommendation(request, form, post)
    else:
        form = EmailPostForm()

    context = {'post': post, 'form': form, 'sent': sent}

    return render(request, 'blog/post/share.html', context)


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    comment = None
    comment_form = CommentForm(data=request.POST)
    if comment_form.is_valid():  # server side check
        comment = comment_form.save(commit=False)
        comment.post = post
        comment.save()

    context = {'post': post, 'form': comment_form, 'comment': comment}

    return render(request, 'blog/post/comment.html', context)


def post_search(request):
    """Search posts on query looking in title and body"""
    form, search_results = SearchForm(), []
    form_query = retrieve_search_query(request.GET)

    if form_query:  # query exists
        search_vector = (
                SearchVector('title', weight='A') +
                SearchVector('body', weight='B')
        )
        search_query = SearchQuery(form_query)  # filter based on user input
        search_rank = SearchRank(search_vector, search_query)  # results order

        # Querying Post model, annotating with search and rank,
        # filtering by rank and ordering by descending rank
        search_results = (
            Post.published
            .annotate(search=search_vector, rank=search_rank)
            .filter(rank__gte=0.1)
            .order_by('-rank')
        )

    context = {'form': form, 'query': form_query, 'results': search_results}

    return render(request, 'blog/post/search.html', context)
