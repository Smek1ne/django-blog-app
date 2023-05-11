from typing import Dict

from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.forms import Form
from django.http import HttpRequest

from .models import Post as PostModel


def get_similar_posts(post):
    """This function returns up to 4 published posts that share the most tags
     with the given post, excluding the given post itself.
    """
    post_tags_ids = post.tags.values_list('id', flat=True)
    return (
        PostModel.published
        .filter(tags__in=post_tags_ids)
        .exclude(id=post.id)
        .annotate(same_tags=Count('tags' in post_tags_ids))
        .order_by('-same_tags', '-publish')[:4]
    )


def get_posts_from_page(paginator, page):
    """Returns the posts from the given page."""
    try:
        posts_to_show = paginator.page(page)
    except PageNotAnInteger:
        posts_to_show = paginator.page(1)
    except EmptyPage:
        posts_to_show = paginator.page(paginator.num_pages)
    return posts_to_show


def send_post_recommendation(request, form: Form, post: PostModel) -> bool:
    """Sends a post recommendation email to the given user."""

    if form.is_valid():
        cd: Dict[str, str] = form.cleaned_data
        post_url = request.build_absolute_uri(post.get_absolute_url())
        subject = f"{cd['name']} recommends you read {post.title}"
        message = f"Read {post.title} at {post_url}\n\n" \
                  f"{cd['name']} comments: {cd['comments']}"
        send_mail(subject, message, cd['email'], [cd['to']])
        return True
    return False
