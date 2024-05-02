from django.shortcuts import render, redirect
from amazon_buddy import AmazonBuddy, SortType, Category
import pandas as pd
import matplotlib.pyplot as plt
import os
import base64
import io
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from django.http import HttpResponse
import csv
from django.contrib.auth.decorators import login_required

# Set Matplotlib backend to Agg
plt.switch_backend('Agg')

# Initialize Amazon Buddy
ab = AmazonBuddy(debug=True, user_agent='ADD_USER_AGENT')

@login_required
def prices(request):
    if request.method == 'POST':
        # Retrieve form data
        keyword = request.POST.get('keyword')
        sort_type = request.POST.get('sort_type').upper().replace(' ', '_')
        min_price = float(request.POST.get('min_price', 0))
        category = request.POST.get('category').upper().replace(' ', '_')
        max_results = int(request.POST.get('max_results', 20))
        min_rating = float(request.POST.get('min_rating', 0))
        
        # Fetch list of products
        products = ab.search_products(
            keyword,
            sort_type=SortType[sort_type],
            min_price=min_price,
            category=Category[category],
            max_results=max_results,
            min_rating=min_rating
        )
        
        if products is None:
            return redirect('amzprices:prices_form.html')  # Assuming 'index' is the name of your index view
        
        # Create lists to store ASINs and prices of products
        asins = []
        prices = []
        
        # Fetch ASIN and price of each product
        for product in products:
            asins.append(product.asin)
            prices.append(product.price)
        
        if not asins:
            return HttpResponse("No products found for the given criteria.", status=400)

        # Plot price fluctuation
        num_products = len(asins)
        figsize = (max(10, num_products * 0.5), 6)  # Adjust the multiplier as needed
        
        plt.figure(figsize=figsize)  # Set the figure size dynamically
        plt.plot(asins, prices, marker='o', linestyle='-')
        plt.xlabel('ASIN')
        plt.ylabel('Price')
        plt.title('Price Comparison of Face Wash Products')
        plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
        
        # Adjust margins to prevent cropping of the bottom part
        plt.subplots_adjust(bottom=0.2)  # Adjust bottom margin as needed
        
        # Convert the plot to a base64-encoded image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='jpg')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode()
        plt.close()  # Close the plot
        
        # Pass parameters to template
        context = {
            'asins': asins,
            'prices': prices,
            'image_data': image_data,
            'keyword':keyword,
            'sort_type':sort_type,
            'min_price':min_price,
            'category':category,
            'max_results':max_results,
            'min_rating':min_rating,
        }
        
        # Render HTML template with the price graph
        return render(request, 'amzprices/result.html', context)
    
    else:

        # Get available sort types and categories for the form
        sort_types = [sort_type.name.lower().replace('_', ' ') for sort_type in SortType]
        categories = [category.name.lower().replace('_', ' ') for category in Category]
        
        # Render HTML template with the form
        return render(request, 'amzprices/prices_form.html', {'sort_types': sort_types, 'categories': categories})

@login_required
def generate_pdf(request):
    if request.method == 'POST':
        # Retrieve data from request context
        keyword = request.POST.get('keyword')
        sort_type = request.POST.get('sort_type')
        min_price = request.POST.get('min_price')
        category = request.POST.get('category')
        max_results = request.POST.get('max_results')
        min_rating = request.POST.get('min_rating')
        image_data = request.POST.get('image_data')

        # Render HTML template with the data
        html_string = render_to_string('amzprices/result_without_base.html', {
            'keyword': keyword,
            'sort_type': sort_type,
            'min_price': min_price,
            'category': category,
            'max_results': max_results,
            'min_rating': min_rating,
            'image_data': image_data,
        })

        # Specify file paths for PDF generation
        html_file_path = os.path.join(settings.BASE_DIR,'amzprices', 'result_without_base.html')
        pdf_file_path = os.path.join(settings.BASE_DIR, 'generated_pdf.pdf')

        # Write HTML content to a temporary file
        with open(html_file_path, 'w') as f:
            f.write(html_string)

        # Generate PDF from HTML content using WeasyPrint
        HTML(html_file_path).write_pdf(pdf_file_path)

        # Delete temporary HTML file
        #os.remove(html_file_path)

        # Serve the generated PDF as a download
        with open(pdf_file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="amazon_prices_report.pdf"'
            return response
    else:
        return HttpResponse("Method not allowed", status=405)

@login_required
def generate_csv(request):
    if request.method == 'POST':
        # Retrieve ASINs and prices from the request or context
        asins = request.POST.getlist('asins')
        prices = request.POST.getlist('prices')

        # Create an HttpResponse object with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="amazon_prices.csv"'

        # Create a CSV writer
        writer = csv.writer(response)

        # Write header row
        writer.writerow(['ASIN', 'Price'])

        # Write data rows
        for asin, price in zip(asins, prices):
            writer.writerow([asin, price])

        return response
    else:
        return HttpResponse("Method not allowed", status=405)
