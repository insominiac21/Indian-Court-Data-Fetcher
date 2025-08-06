# Indian Court Data Fetcher

A Flask web application that provides easy access to Indian court case information with AI-powered summarization capabilities. This application allows users to search for court cases and get intelligent summaries using LLaMA AI technology.

## Features

- **Court Case Search**: Search for cases by case number, party names, or keywords
- **Multiple Court Support**: Support for various Indian courts including Delhi High Court and District Courts
- **AI-Powered Summaries**: Generate intelligent case summaries using Groq LLaMA-3.1-8b-instant model
- **PDF Reports**: Download case details and summaries as PDF reports
- **Search History**: Track and revisit previous searches
- **Responsive Design**: Mobile-friendly interface with modern UI
- **Demo Data**: Built-in demo data for testing and demonstration

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Python 3.8+
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **AI/ML**: LangChain, Groq API, LLaMA-3.1-8b-instant
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Web Scraping**: Selenium WebDriver
- **PDF Generation**: ReportLab
- **Deployment**: Gunicorn (production ready)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Chrome browser (for web scraping)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/insominiac21/Indian-Court-Data-Fetcher.git
   cd Indian-Court-Data-Fetcher
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   ```

5. **Initialize the database**:
   ```bash
   python app.py
   ```
   The database will be created automatically on first run.

## Usage

### Running the Application

1. **Start the Flask development server**:
   ```bash
   python app.py
   ```

2. **Access the application**:
   Open your web browser and navigate to `http://localhost:5000`

### Using the Search Feature

1. **Enter search criteria**:
   - Case Number: Enter the full case number (e.g., "CS(OS) 123/2023")
   - Party Names: Enter plaintiff or defendant names
   - Court: Select the appropriate court from the dropdown

2. **Submit the search**:
   Click the "Search Case" button to retrieve case information

3. **View results**:
   - Case details will be displayed with all available information
   - AI summary will be generated automatically
   - Download PDF report using the "Download PDF Report" button

### API Endpoints

The application provides RESTful API endpoints:

- `GET /` - Main search form
- `POST /search` - Submit search query
- `GET /result/<query_id>` - View search results
- `GET /history` - View search history
- `POST /download-pdf/<case_id>` - Download PDF report
- `GET /api/case/<case_id>` - Get case data as JSON

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key for AI summaries
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `FLASK_ENV`: Environment mode (development/production)
- `DATABASE_URL`: Database connection string (optional)

### Court Configuration

The application supports multiple courts. To add new courts, update the court configuration in `models.py`.

## Demo Data

The application includes built-in demo data for testing:

- Civil cases (CS(OS))
- Criminal cases (CRL)
- Family cases (MAT)
- Commercial cases (CS(COMM))

Demo data includes realistic case details, party information, and order histories.

## Development

### Project Structure

```
Indian-Court-Data-Fetcher/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── scraper.py             # Web scraping functionality
├── summarizer_langchain.py # AI summarization
├── requirements.txt       # Python dependencies
├── static/
│   └── style.css         # CSS styles
├── templates/
│   ├── form.html         # Search form
│   ├── result.html       # Results display
│   └── history.html      # Search history
└── instance/
    └── court_data.db     # SQLite database
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## Deployment

### Production Deployment

1. **Set environment variables**:
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=postgresql://user:password@localhost/courtdata
   ```

2. **Use Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

3. **Docker Deployment** (optional):
   ```bash
   docker build -t court-data-fetcher .
   docker run -p 8000:8000 court-data-fetcher
   ```

## API Documentation

### Search API

**POST /search**

Request:
```json
{
  "case_number": "CS(OS) 123/2023",
  "court": "Delhi High Court",
  "plaintiff": "John Doe",
  "defendant": "Jane Smith"
}
```

Response:
```json
{
  "status": "success",
  "query_id": "12345",
  "redirect_url": "/result/12345"
}
```

### Case Data API

**GET /api/case/{case_id}**

Response:
```json
{
  "case_id": "12345",
  "case_number": "CS(OS) 123/2023",
  "court": "Delhi High Court",
  "plaintiff": "John Doe",
  "defendant": "Jane Smith",
  "case_type": "Civil",
  "filing_date": "2023-01-15",
  "status": "Active",
  "orders": [...],
  "summary": "AI-generated summary..."
}
```

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**:
   - Ensure Chrome browser is installed
   - WebDriver Manager will automatically download the correct driver

2. **API Key Errors**:
   - Verify your Groq API key is correct
   - Check if you have sufficient API credits

3. **Database Issues**:
   - Delete `instance/court_data.db` and restart the application
   - Check file permissions in the instance directory

### Logs

Check application logs for detailed error information:
```bash
tail -f app.log
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and SQLAlchemy
- AI summaries powered by Groq and LangChain
- Web scraping with Selenium
- UI components inspired by modern web design principles

## Support

For support, please open an issue on GitHub or contact the development team.

---

**Note**: This application is designed for educational and research purposes. Please ensure compliance with relevant court website terms of service when using web scraping features.


## Demo Video
https://youtu.be/6FXtT0fQj8E