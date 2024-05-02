# views.py
import csv
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from amazon_buddy import AmazonBuddy, Category
import time
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from django.template import Context, Template
from weasyprint import HTML
from django.utils import timezone
import datetime
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required

@login_required
def generate_pdf(request):
    if request.method == 'POST':
        # Retrieve data from request or context
        category = request.POST.get('category')
        search_params = request.POST.get('search_params')
        max_results_per_letter = request.POST.get('max_results_per_letter')

        # Get current date and time
        current_datetime = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            # Render HTML template using Django's template engine
        template_path = os.path.join(settings.BASE_DIR, 'amztrend', 'results_pdf_without_trends.html')
        with open(template_path) as file:
            template = Template(file.read())

        # Prepare template context
        context = {
        'category': category,
        'search_params': search_params,
        'max_results_per_letter': max_results_per_letter,
        'graph': request.POST.get('graph'),  # Include the graph image data
        'current_datetime': current_datetime,  # Pass current date and time to the template
        }

        # Render template with context
        html_content = template.render(Context(context))

        # Generate PDF from HTML content using WeasyPrint
        pdf_file_path = os.path.join(settings.BASE_DIR, 'trending_data', 'trending_report.pdf')
        HTML(string=html_content).write_pdf(pdf_file_path)

        # Serve the generated PDF as a download
        with open(pdf_file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="trending_report.pdf"'
            return response

@login_required
def generate_csv(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        search_params = request.POST.get('search_params')
        max_results_per_letter = request.POST.get('max_results_per_letter')
        trends = request.POST.getlist('trends')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="trending_words.csv"'

        writer = csv.writer(response)
        writer.writerow(['Category', 'Search Parameters', 'Max Results per Letter', 'Trending Word'])
        writer.writerow([category, search_params, max_results_per_letter, ''])  # Empty row for spacing
        for word in trends:
            writer.writerow(['', '', '', word])

        return response

@login_required
def mail_reports(request):

    pdf_response = generate_pdf(request)

    # Generate CSV response
    csv_response = generate_csv(request)

    # Extract PDF content
    pdf_content = pdf_response.content

    # Extract CSV content
    csv_content = csv_response.content
    # Create email message
    subject = 'Amazon Trends Report'
    message = 'Please find attached the Amazon Trends reports.'
    email = EmailMessage(subject, message, to=['manojm7876121@gmail.com'])


    # Attach PDF file
    email.attach('trending_report.pdf', pdf_content, 'application/pdf')

    # Attach CSV file
    email.attach('trending_words.csv', csv_content, 'text/csv')

    # Send email
    email.send()

    return render(request,'amztrend/mail_success.html')

@login_required
def trend_view(request):
    if request.method == 'POST':
        category = request.POST.get('category').replace(' ', '_')
        search_params = request.POST.get('search_params')
        max_results_per_letter = request.POST.get('max_results_per_letter')

        # Validate search params
        if not search_params.isalpha():
            return HttpResponse("Invalid search params. Please enter only characters from 'a' to 'z'.", status=400)
        
        # Validate max results
        if not max_results_per_letter.isdigit():
            return HttpResponse("Invalid max results per letter. Please enter a valid integer.", status=400)

        # Convert max results to integer
        max_results_per_letter = int(max_results_per_letter)

        # Initialize Amazon Buddy
        ab = AmazonBuddy()

        # Get top 10 trending terms
        trends = ab.get_trends(category=Category[category.upper()], search_params=search_params, return_dict=False, max_results_per_letter=max_results_per_letter)

        # Filter out unwanted words
        filtered_trends = [word for word in trends if word[0].lower() in search_params]

        # Count the filtered trending words by their starting letter
        counts = {}
        for word in filtered_trends:
            first_letter = word[0].lower()
            counts[first_letter] = counts.get(first_letter, 0) + 1

        # Calculate the maximum count of trending words
        max_count = max(counts.values())

        # Plot the bar graph
        plt.figure(figsize=(10,6))
        plt.bar(counts.keys(), counts.values(), color='skyblue')
        plt.title('Trending Words by Starting Letter')
        plt.xlabel('Starting Letter')
        plt.ylabel('Count of Trending Words')
        plt.xticks(rotation=45)
        plt.ylim(0, max_count + 1)  # Set the y-axis limit dynamically
        plt.tight_layout()

        # Convert the plot to base64 encoded image
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        # Pass the base64 encoded image to the template
        return render(request, 'amztrend/results.html', {'trends': filtered_trends, 'category': category, 'graph': image_base64,'search_params':search_params,'max_results_per_letter':max_results_per_letter})

    else:
        categories = [category.name.lower().replace('_', ' ') for category in Category]
        return render(request, 'amztrend/trend.html', {'categories': categories})