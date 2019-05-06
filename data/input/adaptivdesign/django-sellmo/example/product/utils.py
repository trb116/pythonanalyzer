from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(request, products, num=None):
    paginator = Paginator(products, num if num else 28)
    try:
        products = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    return products

