from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from scraper import IndianCourtScraper
from summarizer_langchain import CourtDataSummarizer
from models import db, CourtCase, CaseOrder, SearchQuery, PDFDownload, init_database, get_court_types, get_filing_years
import os
from datetime import datetime
import json
import time
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///court_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize database
db.init_app(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour", "10 per minute"]
)

# Initialize components
scraper = IndianCourtScraper()
summarizer = CourtDataSummarizer()

# Captcha functions removed for easier access

@app.route('/')
def index():
    """Main page with enhanced search form for Indian courts"""
    court_types = get_court_types()
    filing_years = get_filing_years()
    
    return render_template('form.html', 
                         court_types=court_types, 
                         filing_years=filing_years)

@app.route('/search', methods=['POST'])
@limiter.limit("5 per minute")
def search():
    """Handle court case search with enhanced Indian court support"""
    start_time = time.time()
    
    try:
        # Get search parameters from form with validation
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        filing_year = request.form.get('filing_year', '').strip()
        court_name = request.form.get('court_name', 'Delhi High Court').strip()
        
        # Comprehensive validation
        validation_errors = []
        
        # Validate required fields
        if not case_type:
            validation_errors.append("Case Type is required")
        elif case_type not in get_court_types():
            validation_errors.append("Invalid Case Type selected")
            
        if not case_number:
            validation_errors.append("Case Number is required")
        elif not case_number.isdigit():
            validation_errors.append("Case Number must contain only numbers (e.g., 123)")
        elif len(case_number) > 10:
            validation_errors.append("Case Number is too long (maximum 10 digits)")
        elif len(case_number) < 1:
            validation_errors.append("Case Number cannot be empty")
            
        if not filing_year:
            validation_errors.append("Filing Year is required")
        else:
            try:
                filing_year_int = int(filing_year)
                current_year = datetime.now().year
                if filing_year_int < 1947:  # India's independence year
                    validation_errors.append("Filing Year cannot be before 1947")
                elif filing_year_int > current_year:
                    validation_errors.append(f"Filing Year cannot be in the future (current year: {current_year})")
            except ValueError:
                validation_errors.append("Filing Year must be a valid number")
        
        if not court_name:
            validation_errors.append("Court Name is required")
        
        # If there are validation errors, return them
        if validation_errors:
            # Get court types and filing years for the form
            court_types = get_court_types()
            filing_years = get_filing_years()
            
            # Preserve form data
            form_data = {
                'case_type': request.form.get('case_type', ''),
                'case_number': request.form.get('case_number', ''),
                'filing_year': request.form.get('filing_year', ''),
                'court_name': request.form.get('court_name', 'Delhi High Court')
            }
            
            error_message = "Please fix the following errors:\n• " + "\n• ".join(validation_errors)
            return render_template('form.html', 
                                 court_types=court_types, 
                                 filing_years=filing_years,
                                 error=error_message,
                                 form_data=form_data)
        
        # Convert filing_year to int after validation
        filing_year = int(filing_year)
        
        # Log the search query
        query = SearchQuery(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            court_name=court_name,
            query_status='in_progress',
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(query)
        db.session.commit()
        
        # Check if case already exists in database
        existing_case = CourtCase.query.filter_by(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            court_name=court_name
        ).first()
        
        if existing_case:
            # Update query status
            query.query_status = 'cache_hit'
            query.case_id = existing_case.id
            query.response_time_ms = int((time.time() - start_time) * 1000)
            db.session.commit()
            
            return render_template('result.html',
                                 court_data=existing_case.get_parsed_data() if existing_case.get_parsed_data() else existing_case.to_dict(),
                                 case_data=existing_case,
                                 summary=existing_case.ai_summary,
                                 from_cache=True,
                                 current_date=datetime.now().strftime('%B %d, %Y at %H:%M'))
        
        # Scrape fresh data
        scraped_data = scraper.scrape_case_data(case_type, case_number, filing_year, court_name)
        
        if not scraped_data:
            # Update query status
            query.query_status = 'no_data'
            query.response_time_ms = int((time.time() - start_time) * 1000)
            query.error_message = "No data found for the given case details"
            db.session.commit()
            
            return render_template('result.html', 
                                 error="No case found with the provided details. Please verify the case information.",
                                 current_date=datetime.now().strftime('%B %d, %Y at %H:%M'))
        
        # Generate AI summary
        summary = summarizer.summarize_court_data(scraped_data)
        
        # Save case to database
        new_case = CourtCase(
            case_type=case_type,
            case_number=case_number,
            filing_year=filing_year,
            court_name=court_name,
            case_title=scraped_data.get('case_title'),
            petitioner_name=scraped_data.get('petitioner_name'),
            respondent_name=scraped_data.get('respondent_name'),
            case_status=scraped_data.get('case_status'),
            judge_name=scraped_data.get('judge_name'),
            advocate_petitioner=scraped_data.get('advocate_petitioner'),
            advocate_respondent=scraped_data.get('advocate_respondent'),
            raw_response=scraped_data.get('raw_html', ''),
            ai_summary=summary,
            source_url=scraped_data.get('source_url'),
            scraping_method=scraped_data.get('scraping_method')
        )
        
        # Parse and set dates
        try:
            if scraped_data.get('filing_date'):
                new_case.filing_date = datetime.strptime(scraped_data['filing_date'], '%Y-%m-%d').date()
        except:
            pass
        
        try:
            if scraped_data.get('next_hearing_date'):
                new_case.next_hearing_date = datetime.strptime(scraped_data['next_hearing_date'], '%Y-%m-%d').date()
        except:
            pass
        
        # Set parsed data - clean the data first to avoid serialization issues
        try:
            # Create a clean copy of scraped_data for JSON serialization
            clean_scraped_data = {}
            for key, value in scraped_data.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    clean_scraped_data[key] = value
                elif isinstance(value, (list, dict)):
                    clean_scraped_data[key] = value
                else:
                    clean_scraped_data[key] = str(value)
            
            new_case.set_parsed_data(clean_scraped_data)
        except Exception as e:
            app.logger.warning(f"Could not set parsed data: {e}")
            # Continue without setting parsed data
        
        db.session.add(new_case)
        db.session.flush()  # Get the ID
        
        # Save orders/judgments
        for order_data in scraped_data.get('orders', []):
            order = CaseOrder(
                case_id=new_case.id,
                order_title=order_data.get('title'),
                pdf_url=order_data.get('url'),
                order_type=order_data.get('type', 'order'),
                is_latest=len(scraped_data.get('orders', [])) == 1
            )
            
            try:
                if order_data.get('date'):
                    order.order_date = datetime.strptime(order_data['date'], '%Y-%m-%d').date()
            except:
                order.order_date = datetime.now().date()
            
            db.session.add(order)
        
        # Update query status
        query.query_status = 'success'
        query.case_id = new_case.id
        query.response_time_ms = int((time.time() - start_time) * 1000)
        
        db.session.commit()
        
        return render_template('result.html',
                             court_data=scraped_data,
                             case_data=new_case,
                             summary=summary,
                             scraped_data=scraped_data,
                             current_date=datetime.now().strftime('%B %d, %Y at %H:%M'))
        
    except Exception as e:
        # Update query status if query exists
        try:
            if 'query' in locals():
                query.query_status = 'failed'
                query.error_message = str(e)
                query.response_time_ms = int((time.time() - start_time) * 1000)
                db.session.commit()
        except:
            pass
        
        app.logger.error(f"Search error: {e}")
        
        # Provide more specific error messages
        error_message = "An unexpected error occurred while processing your request."
        if "connection" in str(e).lower():
            error_message = "Unable to connect to court website. Please try again later."
        elif "timeout" in str(e).lower():
            error_message = "Request timed out. The court website may be busy. Please try again."
        elif "database" in str(e).lower():
            error_message = "Database error occurred. Please try again."
        
        return render_template('result.html', 
                             error=error_message,
                             current_date=datetime.now().strftime('%B %d, %Y at %H:%M'))

@app.route('/download_pdf/<int:order_id>')
def download_pdf(order_id):
    """Download PDF for a specific order"""
    try:
        order = CaseOrder.query.get_or_404(order_id)
        
        if not order.pdf_url:
            return jsonify({'error': 'No PDF URL available'}), 404
        
        # Download PDF if not already downloaded
        if not order.pdf_downloaded and order.pdf_url:
            filename = f"order_{order_id}_{order.case.case_number.replace('/', '_')}.pdf"
            local_path = scraper.download_pdf(order.pdf_url, filename)
            
            if local_path:
                order.local_pdf_path = local_path
                order.pdf_downloaded = True
                order.pdf_filename = filename
                db.session.commit()
                
                return send_file(local_path, as_attachment=True, download_name=filename)
            else:
                return jsonify({'error': 'Failed to download PDF'}), 500
        
        elif order.local_pdf_path and os.path.exists(order.local_pdf_path):
            return send_file(order.local_pdf_path, as_attachment=True, download_name=order.pdf_filename)
        
        else:
            return jsonify({'error': 'PDF not available'}), 404
            
    except Exception as e:
        app.logger.error(f"PDF download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for court data search"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', '')
        case_number = data.get('case_number', '')
        filing_year = data.get('filing_year', '')
        court_name = data.get('court_name', 'Delhi High Court')
        
        if not all([case_type, case_number, filing_year]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        court_data = scraper.scrape_case_data(case_type, case_number, int(filing_year), court_name)
        
        if not court_data:
            return jsonify({'error': 'No data found'}), 404
        
        summary = summarizer.summarize_court_data(court_data)
        
        return jsonify({
            'case_data': court_data,
            'summary': summary,
            'case_type': case_type,
            'case_number': case_number,
            'filing_year': filing_year
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    """View search history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    cases = CourtCase.query.order_by(CourtCase.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('history.html', cases=cases)

@app.route('/analytics')
def analytics():
    """Basic analytics dashboard"""
    from models import get_database_stats
    stats = get_database_stats()
    
    return render_template('analytics.html', stats=stats)

@app.route('/case/<int:case_id>')
def case_detail(case_id):
    """View detailed case information"""
    case = CourtCase.query.get_or_404(case_id)
    return render_template('case_detail.html', case=case)

@app.route('/download_case_pdf/<int:case_id>')
def download_case_pdf(case_id):
    """Generate and download PDF for a specific case"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from io import BytesIO
    import re
    
    case = CourtCase.query.get_or_404(case_id)
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        textColor=HexColor('#2c3e50'),
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=20,
        textColor=HexColor('#34495e'),
        borderWidth=1,
        borderColor=HexColor('#bdc3c7'),
        borderPadding=10,
        backColor=HexColor('#ecf0f1')
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        textColor=HexColor('#2980b9'),
        fontName='Helvetica-Bold'
    )
    
    bullet_style = ParagraphStyle(
        'BulletPoint',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leftIndent=20,
        bulletIndent=10
    )
    
    def format_ai_summary_for_pdf(summary_text):
        """Format AI summary to match the web display structure"""
        if not summary_text:
            return []
        
        formatted_elements = []
        
        # Clean up the summary text
        clean_text = summary_text.replace('<br><br>', '\n\n').replace('<br>', '\n')
        clean_text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', clean_text)
        
        # Split into paragraphs
        paragraphs = clean_text.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            para = para.strip()
            
            # Check if paragraph contains bullet points
            if '• ' in para or para.startswith('*'):
                # Handle bullet points
                lines = para.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('• ') or line.startswith('* '):
                        # Remove bullet and format
                        bullet_text = line.lstrip('• *').strip()
                        bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
                        formatted_elements.append(Paragraph(f"• {bullet_text}", bullet_style))
                    elif line:
                        # Regular line within bullet section
                        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                        formatted_elements.append(Paragraph(line, styles['Normal']))
            else:
                # Regular paragraph
                # Handle bold text
                para = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
                
                # Check if it's a heading (starts with bold text followed by colon)
                if re.match(r'^<b>[^<]+</b>:', para):
                    formatted_elements.append(Paragraph(para, subheading_style))
                else:
                    formatted_elements.append(Paragraph(para, styles['Normal']))
            
            # Add spacing between sections
            formatted_elements.append(Spacer(1, 0.1*inch))
        
        return formatted_elements
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph("COURT CASE COMPREHENSIVE REPORT", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Case Information
    story.append(Paragraph("📋 CASE INFORMATION", heading_style))
    story.append(Paragraph(f"<b>Case Number:</b> {case.case_number}", styles['Normal']))
    story.append(Paragraph(f"<b>Case Type:</b> {case.case_type}", styles['Normal']))
    story.append(Paragraph(f"<b>Filing Year:</b> {case.filing_year}", styles['Normal']))
    story.append(Paragraph(f"<b>Court:</b> {case.court_name}", styles['Normal']))
    if case.case_status:
        story.append(Paragraph(f"<b>Status:</b> {case.case_status}", styles['Normal']))
    if case.case_title:
        story.append(Paragraph(f"<b>Case Title:</b> {case.case_title}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Parties
    if case.petitioner_name or case.respondent_name:
        story.append(Paragraph("👥 PARTIES INVOLVED", heading_style))
        if case.petitioner_name:
            story.append(Paragraph(f"<b>Petitioner:</b> {case.petitioner_name}", styles['Normal']))
        if case.respondent_name:
            story.append(Paragraph(f"<b>Respondent:</b> {case.respondent_name}", styles['Normal']))
        if case.judge_name:
            story.append(Paragraph(f"<b>Judge:</b> {case.judge_name}", styles['Normal']))
        if case.advocate_petitioner:
            story.append(Paragraph(f"<b>Advocate (Petitioner):</b> {case.advocate_petitioner}", styles['Normal']))
        if case.advocate_respondent:
            story.append(Paragraph(f"<b>Advocate (Respondent):</b> {case.advocate_respondent}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Dates
    if case.filing_date or case.next_hearing_date:
        story.append(Paragraph("📅 IMPORTANT DATES", heading_style))
        if case.filing_date:
            story.append(Paragraph(f"<b>Filing Date:</b> {case.filing_date.strftime('%B %d, %Y')}", styles['Normal']))
        if case.next_hearing_date:
            story.append(Paragraph(f"<b>Next Hearing:</b> {case.next_hearing_date.strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # AI Summary with proper formatting
    if case.ai_summary:
        story.append(Paragraph("🤖 AI-GENERATED CASE SUMMARY", heading_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Add formatted summary elements
        summary_elements = format_ai_summary_for_pdf(case.ai_summary)
        story.extend(summary_elements)
        
        story.append(Spacer(1, 0.2*inch))
    
    # Orders if available
    orders = CaseOrder.query.filter_by(case_id=case.id).all()
    if orders:
        story.append(Paragraph("📄 CASE ORDERS & PROCEEDINGS", heading_style))
        for order in orders:
            if order.order_title:
                story.append(Paragraph(f"<b>{order.order_title}</b>", styles['Normal']))
            if order.order_date:
                story.append(Paragraph(f"Date: {order.order_date.strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    # Footer
    story.append(Spacer(1, 0.4*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#7f8c8d'),
        alignment=1  # Center alignment
    )
    story.append(Paragraph("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", footer_style))
    story.append(Paragraph("Generated by Court Data Fetcher System", footer_style))
    story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Paragraph("This is an AI-generated summary for informational purposes only", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Return PDF
    buffer.seek(0)
    filename = f"Court_Case_{case.case_type}_{case.case_number}_{case.filing_year}_Report.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/download_summary_pdf')
def download_summary_pdf():
    """Generate PDF for the most recent search result"""
    # Get the most recent case
    case = CourtCase.query.order_by(CourtCase.created_at.desc()).first()
    if not case:
        return "No cases found", 404
    
    return redirect(url_for('download_case_pdf', case_id=case.id))

@app.teardown_appcontext
def cleanup(error):
    """Clean up resources"""
    if error:
        app.logger.error(f"Application error: {error}")

if __name__ == '__main__':
    with app.app_context():
        init_database(app)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        scraper.close()
