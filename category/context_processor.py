from category.models import Category


def menu_link(request):
    links = Category.objects.all()
    return dict(links=links)
