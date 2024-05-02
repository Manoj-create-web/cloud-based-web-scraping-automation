from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'amztrend'
urlpatterns = [
    path('trend/', login_required(views.trend_view), name='trend'),
    path('generate_pdf/', login_required(views.generate_pdf), name='generate_pdf'),
    path('generate-csv/', login_required(views.generate_csv), name='generate_csv'),
    path('mail-reports/', login_required(views.mail_reports), name='mail_reports'),
]

