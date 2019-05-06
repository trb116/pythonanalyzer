# aristotle_ddi_utils
from aristotle_mdr.utils import get_download_template_path_for_item
import cgi
import cStringIO as StringIO
from django.http import HttpResponse, Http404
# from django.shortcuts import render
from django.template.loader import select_template
from django.template import Context
import xhtml2pdf.pisa as pisa
import csv


def render_to_pdf(template_src, context_dict):
    # If the request template doesnt exist, we will give a default one.
    template = select_template([
        template_src,
        'aristotle_mdr/downloads/pdf/managedContent.html'
    ])
    context = Context(context_dict)
    html = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(
        StringIO.StringIO(html.encode("UTF-8")),
        result,
        encoding='UTF-8'
    )
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))


def download(request, downloadType, item):
    """Built in download method"""
    template = get_download_template_path_for_item(item, downloadType)
    from django.conf import settings
    page_size = getattr(settings, 'PDF_PAGE_SIZE', "A4")
    if downloadType == "pdf":
        subItems = item.get_download_items()
        return render_to_pdf(
            template,
            {
                'item': item,
                'subitems': subItems,
                'tableOfContents': len(subItems) > 0,
                'view': request.GET.get('view', '').lower(),
                'pagesize': request.GET.get('pagesize', page_size),
            }
        )

    elif downloadType == "csv-vd":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            item.name
        )

        writer = csv.writer(response)
        writer.writerow(['value', 'meaning', 'start date', 'end date', 'role'])
        for v in item.permissibleValues.all():
            writer.writerow(
                [v.value, v.meaning, v.start_date, v.end_date, "permissible"]
            )
        for v in item.supplementaryValues.all():
            writer.writerow(
                [v.value, v.meaning, v.start_date, v.end_date, "supplementary"]
            )

        return response
