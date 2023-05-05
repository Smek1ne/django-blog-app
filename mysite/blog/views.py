from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import \
    Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from environs import Env
from django.core.mail import send_mail
from django.views.decorators.http import require_POST

env = Env()
env.read_env()  # read .env file, if it exists


def post_list(request):
    posts = Post.published.all()

    paginator = Paginator(posts, 3)  # 3 objects on one page

    # number from get-parameter 'page' or 1
    requested_page = request.GET.get('page', 1)

    try:
        # objects of <page_number> page
        posts_to_show = paginator.page(requested_page)
    except PageNotAnInteger:
        posts_to_show = paginator.page(1)
    except EmptyPage:
        # objects from last page
        posts_to_show = paginator.page(paginator.num_pages)

    return render(request,
                  'blog/post/list.html',
                  {'posts': posts_to_show})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day,
                             status=Post.Status.PUBLISHED)
    comments = post.comments.filter(active=True)
    form = CommentForm()

    return render(request,
                  'blog/post/detail.html',
                  {'post': post, 'comments': comments, 'form': form})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id,
                             status=Post.Status.PUBLISHED)
    sent = False

    if request.method == 'POST':
        form = EmailPostForm(request.POST)

        if form.is_valid():
            cd: dict = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url())
            subj = f"{cd['name']} recommends you read {post.title}"
            msg = f"Read {post.title} at {post_url}\n\n" \
                  f"{cd['name']} comments: {cd['comments']}"
            send_mail(subj, msg, 'audaceuix@gmail.com', [cd['to']])
            sent = True

    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(request, 'blog/post/comment.html',
                  {'post': post, 'form': form, 'comment': comment})
