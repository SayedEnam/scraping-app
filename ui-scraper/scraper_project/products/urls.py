from django.urls import path
from . import views

urlpatterns = [
    path('scrape/', views.scrape_products, name='scrape_products'),
    path('download/', views.download_excel, name='download_excel'),
]
