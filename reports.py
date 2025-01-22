from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from .views import * 
from martpro import settings

# booking report
def fetch_records(start_date, end_date):
    records = Order.objects.filter(created_at__range=[start_date, end_date])  
    # print("SQL Query:", records.query)
    # print("Records count:", records.count())
    return records

def get_shop_info():
    shop = Company.objects.first()
    return shop

def generate_report(request, date_range):
    time_periods = {
        'today': (timezone.now(), timezone.now()),
        'last_7_days': (timezone.now() - timezone.timedelta(days=7), timezone.now()),
        'this_month': (timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0), timezone.now()),
        'last_month': ((timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=1)).replace(day=1), timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=1)),
    }

    start_date, end_date = time_periods[date_range]
    records = fetch_records(start_date, end_date)
    date_generated = timezone.now().strftime('%d-%m-%Y')
    shop = get_shop_info()

    template = get_template('booking_report.html')

    html = template.render({'records': records, 'shop': shop, 'date_generated': date_generated})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{date_range}_booking_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    
    # image_path = os.path.join(settings.STATIC_ROOT, 'images/c_logo.png')
    # print("Image Path:", image_path)

    return response
