from django.shortcuts import render, get_object_or_404
from .models import Post
from django.core.paginator import \
    Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm


def post_list(request):
    posts = Post.published.all()

    # number of objects on one page
    paginator = Paginator(posts, 3)

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
    return render(request,
                  'blog/post/detail.html',
                  {'post': post})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(Post,
                             id=post_id,
                             status=Post.Status.PUBLISHED)
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # get posted data in dictionary
            cd: dict = form.cleaned_data
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form})
