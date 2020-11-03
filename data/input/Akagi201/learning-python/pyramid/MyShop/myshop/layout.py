from pyramid_layout.layout import layout_config
from .models import Annoncement, Category


@layout_config(name="main", template='myshop:templates/main.pt')
class MainLayout(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.annoncements = request.db.query(Annoncement)
        self.categories = request.db.query(Category).filter_by(parent=None).all()
