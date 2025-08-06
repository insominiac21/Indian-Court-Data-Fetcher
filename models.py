from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class CourtCase(db.Model):
    """Model for storing court case data and summaries - Enhanced for Indian Courts"""
    
    __tablename__ = 'court_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Search criteria
    case_type = db.Column(db.String(100), nullable=False)  # Civil, Criminal, etc.
    case_number = db.Column(db.String(100), nullable=False)
    filing_year = db.Column(db.Integer, nullable=False)
    court_name = db.Column(db.String(200), nullable=False)
    
    # Case details
    case_title = db.Column(db.Text, nullable=True)
    petitioner_name = db.Column(db.String(300), nullable=True)
    respondent_name = db.Column(db.String(300), nullable=True)
    
    # Important dates
    filing_date = db.Column(db.Date, nullable=True)
    registration_date = db.Column(db.Date, nullable=True)
    next_hearing_date = db.Column(db.Date, nullable=True)
    
    # Case status and details
    case_status = db.Column(db.String(100), nullable=True)
    judge_name = db.Column(db.String(200), nullable=True)
    advocate_petitioner = db.Column(db.String(200), nullable=True)
    advocate_respondent = db.Column(db.String(200), nullable=True)
    
    # Raw data and processing
    raw_response = db.Column(db.Text, nullable=False)  # Complete scraped HTML/data
    parsed_data = db.Column(db.Text, nullable=True)   # JSON string of parsed data
    ai_summary = db.Column(db.Text, nullable=True)    # AI-generated summary
    
    # Metadata
    source_url = db.Column(db.String(500), nullable=True)
    scraping_method = db.Column(db.String(50), nullable=True)  # 'selenium', 'requests', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourtCase {self.case_type}/{self.case_number}/{self.filing_year}>'
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'case_type': self.case_type,
            'case_number': self.case_number,
            'filing_year': self.filing_year,
            'court_name': self.court_name,
            'case_title': self.case_title,
            'petitioner_name': self.petitioner_name,
            'respondent_name': self.respondent_name,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'next_hearing_date': self.next_hearing_date.isoformat() if self.next_hearing_date else None,
            'case_status': self.case_status,
            'judge_name': self.judge_name,
            'advocate_petitioner': self.advocate_petitioner,
            'advocate_respondent': self.advocate_respondent,
            'ai_summary': self.ai_summary,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_parsed_data(self):
        """Get parsed data as dictionary"""
        if self.parsed_data:
            try:
                return json.loads(self.parsed_data)
            except:
                return {}
        return {}
    
    def set_parsed_data(self, data_dict):
        """Set parsed data from dictionary"""
        self.parsed_data = json.dumps(data_dict, default=str)

class CaseOrder(db.Model):
    """Model for storing individual court orders and judgments"""
    
    __tablename__ = 'case_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('court_cases.id'), nullable=False)
    
    # Order details
    order_date = db.Column(db.Date, nullable=False)
    order_type = db.Column(db.String(100), nullable=True)  # 'Order', 'Judgment', 'Notice', etc.
    order_title = db.Column(db.String(300), nullable=True)
    order_description = db.Column(db.Text, nullable=True)
    
    # Document details
    pdf_url = db.Column(db.String(500), nullable=True)
    pdf_filename = db.Column(db.String(200), nullable=True)
    pdf_downloaded = db.Column(db.Boolean, default=False)
    local_pdf_path = db.Column(db.String(300), nullable=True)
    
    # Additional metadata
    order_by = db.Column(db.String(200), nullable=True)  # Judge name
    is_latest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    case = db.relationship('CourtCase', backref=db.backref('orders', lazy=True, order_by='CaseOrder.order_date.desc()'))
    
    def __repr__(self):
        return f'<CaseOrder {self.order_type} - {self.order_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'order_type': self.order_type,
            'order_title': self.order_title,
            'order_description': self.order_description,
            'pdf_url': self.pdf_url,
            'pdf_filename': self.pdf_filename,
            'pdf_downloaded': self.pdf_downloaded,
            'local_pdf_path': self.local_pdf_path,
            'order_by': self.order_by,
            'is_latest': self.is_latest,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SearchQuery(db.Model):
    """Model for logging all search queries and responses"""
    
    __tablename__ = 'search_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Search parameters
    case_type = db.Column(db.String(100), nullable=False)
    case_number = db.Column(db.String(100), nullable=False)
    filing_year = db.Column(db.Integer, nullable=False)
    court_name = db.Column(db.String(200), nullable=False)
    
    # Response details
    query_status = db.Column(db.String(50), nullable=False)  # 'success', 'failed', 'no_data'
    response_time_ms = db.Column(db.Integer, nullable=True)
    raw_response = db.Column(db.Text, nullable=True)  # Complete raw response
    error_message = db.Column(db.Text, nullable=True)
    
    # Linked case (if found)
    case_id = db.Column(db.Integer, db.ForeignKey('court_cases.id'), nullable=True)
    
    # Request metadata
    user_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    query_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    case = db.relationship('CourtCase', backref=db.backref('queries', lazy=True))
    
    def __repr__(self):
        return f'<SearchQuery {self.case_type}/{self.case_number}/{self.filing_year} - {self.query_status}>'

class CourtWebsite(db.Model):
    """Model for managing different court websites and their configurations"""
    
    __tablename__ = 'court_websites'
    
    id = db.Column(db.Integer, primary_key=True)
    court_name = db.Column(db.String(200), nullable=False, unique=True)
    court_type = db.Column(db.String(50), nullable=False)  # 'high_court', 'district_court', 'supreme_court'
    
    # Website details
    base_url = db.Column(db.String(500), nullable=False)
    search_url = db.Column(db.String(500), nullable=True)
    case_details_url_pattern = db.Column(db.String(500), nullable=True)
    
    # Scraping configuration
    requires_captcha = db.Column(db.Boolean, default=False)
    has_viewstate = db.Column(db.Boolean, default=False)
    scraping_method = db.Column(db.String(50), default='requests')  # 'requests', 'selenium', 'playwright'
    
    # Selectors for parsing (JSON format)
    form_selectors = db.Column(db.Text, nullable=True)  # JSON with form field selectors
    data_selectors = db.Column(db.Text, nullable=True)  # JSON with data extraction selectors
    
    # Status and maintenance
    is_active = db.Column(db.Boolean, default=True)
    last_successful_scrape = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    
    # Rate limiting
    request_delay_seconds = db.Column(db.Float, default=1.0)
    max_requests_per_minute = db.Column(db.Integer, default=10)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourtWebsite {self.court_name}>'
    
    def get_form_selectors(self):
        """Get form selectors as dictionary"""
        if self.form_selectors:
            try:
                return json.loads(self.form_selectors)
            except:
                return {}
        return {}
    
    def get_data_selectors(self):
        """Get data selectors as dictionary"""
        if self.data_selectors:
            try:
                return json.loads(self.data_selectors)
            except:
                return {}
        return {}

class PDFDownload(db.Model):
    """Model for tracking PDF downloads and storage"""
    
    __tablename__ = 'pdf_downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('case_orders.id'), nullable=False)
    
    # Download details
    original_url = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    local_path = db.Column(db.String(300), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    file_hash = db.Column(db.String(64), nullable=True)  # SHA-256 hash
    
    # Download status
    download_status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed'
    download_attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    downloaded_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    order = db.relationship('CaseOrder', backref=db.backref('pdf_download', uselist=False))
    
    def __repr__(self):
        return f'<PDFDownload {self.filename} - {self.download_status}>'

# Database utility functions
def init_database(app):
    """Initialize database with sample data for Indian courts"""
    with app.app_context():
        db.create_all()
        
        # Add sample court websites configuration
        if not CourtWebsite.query.first():
            sample_courts = [
                CourtWebsite(
                    court_name="Delhi High Court",
                    court_type="high_court",
                    base_url="https://delhihighcourt.nic.in/",
                    search_url="https://delhihighcourt.nic.in/case_status.asp",
                    requires_captcha=True,
                    has_viewstate=True,
                    scraping_method="selenium",
                    form_selectors=json.dumps({
                        "case_type": "select[name='ddl_case_type']",
                        "case_number": "input[name='txt_case_no']",
                        "filing_year": "select[name='ddl_filing_year']",
                        "submit_button": "input[name='btn_search']"
                    }),
                    data_selectors=json.dumps({
                        "case_title": "td:contains('Case Title')",
                        "petitioner": "td:contains('Petitioner')",
                        "respondent": "td:contains('Respondent')",
                        "filing_date": "td:contains('Filing Date')",
                        "status": "td:contains('Status')",
                        "next_hearing": "td:contains('Next Hearing')"
                    }),
                    is_active=True
                ),
                CourtWebsite(
                    court_name="Faridabad District Court",
                    court_type="district_court",
                    base_url="https://districts.ecourts.gov.in/",
                    search_url="https://districts.ecourts.gov.in/faridabad/case_status",
                    requires_captcha=False,
                    has_viewstate=False,
                    scraping_method="requests",
                    form_selectors=json.dumps({
                        "case_type": "select[name='case_type']",
                        "case_number": "input[name='case_number']",
                        "filing_year": "select[name='filing_year']"
                    }),
                    is_active=True
                )
            ]
            
            for court in sample_courts:
                db.session.add(court)
            
            db.session.commit()
            print("Sample court configurations added to database")

def get_database_stats():
    """Get database statistics"""
    stats = {
        'total_cases': CourtCase.query.count(),
        'total_queries': SearchQuery.query.count(),
        'active_courts': CourtWebsite.query.filter_by(is_active=True).count(),
        'recent_cases': CourtCase.query.filter(
            CourtCase.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        'pending_downloads': PDFDownload.query.filter_by(download_status='pending').count(),
        'total_orders': CaseOrder.query.count()
    }
    return stats

def get_court_types():
    """Get available case types for Indian courts"""
    return [
        'Civil Appeal',
        'Criminal Appeal', 
        'Writ Petition',
        'Civil Writ Petition',
        'Criminal Writ Petition',
        'Civil Suit',
        'Criminal Case',
        'Matrimonial',
        'Company Petition',
        'Arbitration',
        'Execution',
        'Misc. Application',
        'Review Petition',
        'Special Leave Petition',
        'Contempt Petition'
    ]

def get_filing_years():
    """Get available filing years"""
    current_year = datetime.now().year
    return list(range(current_year, 1990, -1))  # From current year back to 1990
