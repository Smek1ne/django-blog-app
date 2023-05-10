from django.core.mail import send_mail
from django.db.models import Count

from .models import Post as PostModel
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_similar_posts(post):
    post_tags_ids = post.tags.values_list('id', flat=True)
    return (
        PostModel.published
        .filter(tags__in=post_tags_ids)
        .exclude(id=post.id)
        .annotate(same_tags=Count('tags' in post_tags_ids))
        .order_by('-same_tags', '-publish')[:4]
    )


def get_posts_from_page(paginator, page):
    try:
        posts_to_show = paginator.page(page)
    except PageNotAnInteger:
        posts_to_show = paginator.page(1)
    except EmptyPage:
        posts_to_show = paginator.page(paginator.num_pages)


def send_post_recommendation(request, form, post):
    if form.is_valid():
        cd: dict = form.cleaned_data
        post_url = request.build_absolute_uri(post.get_absolute_url())
        subj = f"{cd['name']} recommends you read {post.title}"
        msg = f"Read {post.title} at {post_url}\n\n" \
              f"{cd['name']} comments: {cd['comments']}"
        send_mail(subj, msg, cd['email'], [cd['to']])
        return True
    return False
