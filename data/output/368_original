from django.db.models.fields import TextField

from bs4 import BeautifulSoup


class HtmlField(TextField):

    def cleanup_html(self, value):
        try:
            # Parse with html5lib to attempt and fix invalid httml
            soup = BeautifulSoup(value, 'html5lib')
            soup.body.hidden=True
            value = soup.body.prettify().encode('ascii', 'ignore')
        except Exception as ex:
            value = value
        return value

    def to_python(self, value):
        value = super(HtmlField, self).to_python(value)
        if value is not None:
            value = self.cleanup_html(value)
        return value
