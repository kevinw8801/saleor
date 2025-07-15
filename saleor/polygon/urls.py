from django.urls import path
from . import views

app_name = 'polygon'

urlpatterns = [
    path('webhook/', views.PolygonWebhookView.as_view(), name='webhook'),
    path('wallet/<str:wallet_address>/balance/', views.polygon_wallet_balance, name='wallet_balance'),
]