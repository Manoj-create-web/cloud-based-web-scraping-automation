from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
app_name = 'amzprices'

urlpatterns = [
    path('prices/', login_required(views.prices), name='prices'),
    path('generate_pdf/', login_required(views.generate_pdf), name='generate_pdf'),
    path('generate-csv/', login_required(views.generate_csv), name='generate_csv'),
    #path('mail-reports/', views.mail_reports, name='mail_reports'),
]

