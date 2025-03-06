from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from .scraper import scrape_revibe_products


def scrape_products(request):
    file_path, products_data = scrape_revibe_products()
    
    context = {
        'products': products_data,
        'file_path': file_path
    }
    return render(request, 'products/products_list.html', context)


def download_excel(request):
    file_path, _ = scrape_revibe_products()
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='scraped_products.xlsx')
