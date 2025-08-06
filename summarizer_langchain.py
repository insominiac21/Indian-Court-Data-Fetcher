import os
import json
import logging
from typing import Dict, Any
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CourtDataSummarizer:
    """
    Court data summarizer using Groq's LLaMA model via LangChain
    Provides intelligent summarization of court case data
    """
    
    def __init__(self):
        """Initialize the summarizer with Groq LLaMA model via LangChain"""
        self.logger = logging.getLogger(__name__)
        
        try:
            # Load environment variables first
            load_dotenv()
            
            # Initialize Groq client using LangChain
            self.groq_api_key = os.getenv('GROQ_API_KEY')
            if not self.groq_api_key:
                self.logger.error("GROQ_API_KEY not found in environment variables")
                self.client = None
                return
            
            # Use the exact working pattern from the minimal test
            model_name = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
            self.client = ChatGroq(
                model=model_name, 
                api_key=self.groq_api_key,
                temperature=0.7,
                base_url="https://api.groq.com"
            )
            self.model_name = model_name
            
            self.logger.info(f"Initialized LangChain ChatGroq client with model {self.model_name}")
            self.logger.info(f"API Key present: {bool(self.groq_api_key)}")
            
        except Exception as e:
            self.logger.error(f"Error initializing LangChain ChatGroq client: {e}")
            self.client = None
    
    def summarize_court_data(self, court_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive summary of court case data
        
        Args:
            court_data (dict): Court case data to summarize
            
        Returns:
            str: Generated summary
        """
        try:
            if not self.client:
                self.logger.warning("No Groq client available, using fallback summary")
                return self._fallback_summary(court_data)
            
            # Prepare input text for the model
            input_text = self._prepare_input_text(court_data)
            
            # Generate summary using LangChain ChatGroq
            summary = self._generate_summary_langchain(input_text)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return self._fallback_summary(court_data)
    
    def _prepare_input_text(self, court_data: Dict[str, Any]) -> str:
        """
        Prepare structured input text for the model
        
        Args:
            court_data (dict): Court case data
            
        Returns:
            str: Formatted input text
        """
        try:
            input_parts = []
            
            # Add instruction for the model
            input_parts.append("Please provide a comprehensive summary of the following court case information:")
            input_parts.append("")
            
            # Handle different types of court data
            if 'case_number' in court_data:
                # Single case data
                input_parts.extend(self._format_single_case(court_data))
            elif 'cases' in court_data:
                # Multiple cases data
                input_parts.extend(self._format_multiple_cases(court_data))
            else:
                # Fallback formatting
                input_parts.append(f"Court Data: {json.dumps(court_data, indent=2)}")
            
            input_parts.append("")
            input_parts.append("Please provide a clear, professional summary focusing on key legal details:")
            
            return "\\n".join(input_parts)
            
        except Exception as e:
            self.logger.error(f"Error preparing input text: {e}")
            return f"Court case data: {str(court_data)}\\n\\nSummary:"
    
    def _format_single_case(self, case_data: Dict[str, Any]) -> list:
        """Format single case data for model input"""
        parts = []
        
        if 'case_number' in case_data:
            parts.append(f"Case Number: {case_data['case_number']}")
        
        if 'court_name' in case_data:
            parts.append(f"Court: {case_data['court_name']}")
            
        if 'case_title' in case_data:
            parts.append(f"Case Title: {case_data['case_title']}")
            
        if 'filing_date' in case_data:
            parts.append(f"Filing Date: {case_data['filing_date']}")
            
        # Handle both case_status and status fields
        if 'case_status' in case_data:
            parts.append(f"Status: {case_data['case_status']}")
        elif 'status' in case_data:
            parts.append(f"Status: {case_data['status']}")
            
        # Handle next hearing date variations
        if 'next_hearing_date' in case_data:
            parts.append(f"Next Hearing: {case_data['next_hearing_date']}")
        elif 'next_hearing' in case_data:
            parts.append(f"Next Hearing: {case_data['next_hearing']}")
        
        # Add petitioner and respondent
        if 'petitioner_name' in case_data:
            parts.append(f"Petitioner: {case_data['petitioner_name']}")
        if 'respondent_name' in case_data:
            parts.append(f"Respondent: {case_data['respondent_name']}")
            
        # Add judge information
        if 'judge_name' in case_data:
            parts.append(f"Judge: {case_data['judge_name']}")
            
        # Add advocate information
        if 'advocate_petitioner' in case_data:
            parts.append(f"Advocate for Petitioner: {case_data['advocate_petitioner']}")
        if 'advocate_respondent' in case_data:
            parts.append(f"Advocate for Respondent: {case_data['advocate_respondent']}")
        
        # Handle parties field (legacy format)
        if 'parties' in case_data:
            parties = case_data['parties']
            if 'petitioner' in parties:
                parts.append(f"Petitioner: {parties['petitioner']}")
            if 'respondent' in parties:
                parts.append(f"Respondent: {parties['respondent']}")
        
        # Add case details
        if 'case_details' in case_data:
            details = case_data['case_details']
            for key, value in details.items():
                parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        # Add orders information
        if 'orders' in case_data:
            parts.append("Recent Orders:")
            for order in case_data['orders']:
                date = order.get('date', 'N/A')
                title = order.get('title', order.get('order', 'N/A'))
                parts.append(f"  - {date}: {title}")
        
        return parts
    
    def _format_multiple_cases(self, court_data: Dict[str, Any]) -> list:
        """Format multiple cases data for model input"""
        parts = []
        
        if 'court_name' in court_data:
            parts.append(f"Court: {court_data['court_name']}")
        
        if 'date_range' in court_data:
            parts.append(f"Date Range: {court_data['date_range']}")
        
        if 'total_cases' in court_data:
            parts.append(f"Total Cases: {court_data['total_cases']}")
        
        parts.append("")
        parts.append("Cases:")
        
        for i, case in enumerate(court_data.get('cases', []), 1):
            parts.append(f"\\n{i}. Case Number: {case.get('case_number', 'N/A')}")
            if 'case_title' in case:
                parts.append(f"   Title: {case['case_title']}")
            if 'filing_date' in case:
                parts.append(f"   Filing Date: {case['filing_date']}")
            if 'status' in case:
                parts.append(f"   Status: {case['status']}")
        
        return parts
    
    def _generate_summary_langchain(self, input_text: str) -> str:
        """
        Generate summary using LangChain ChatGroq
        
        Args:
            input_text (str): Prepared input text
            
        Returns:
            str: Generated summary
        """
        try:
            self.logger.info("Generating summary with LangChain ChatGroq")
            
            # Use LangChain's invoke method (similar to your Streamlit example)
            response = self.client.invoke(input_text)
            
            # Extract the summary from response
            summary = response.content.strip()
            self.logger.info("Successfully generated AI summary")
            
            return summary if summary else self._fallback_summary_text()
            
        except Exception as e:
            self.logger.error(f"Error generating summary with LangChain ChatGroq: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            return self._fallback_summary_text()
    
    def _fallback_summary(self, court_data: Dict[str, Any]) -> str:
        """
        Generate a rule-based summary when model is not available
        
        Args:
            court_data (dict): Court case data
            
        Returns:
            str: Rule-based summary
        """
        try:
            summary_parts = []
            
            if 'case_number' in court_data:
                # Single case summary
                case_num = court_data.get('case_number', 'Unknown')
                court = court_data.get('court_name', 'Unknown Court')
                title = court_data.get('case_title', 'Case details not available')
                status = court_data.get('case_status', court_data.get('status', 'Status unknown'))
                
                summary_parts.append(f"Case Summary for {case_num}:")
                summary_parts.append(f"This case titled '{title}' is being heard in {court}.")
                summary_parts.append(f"Current Status: {status}")
                
                if 'filing_date' in court_data:
                    summary_parts.append(f"Filed on: {court_data['filing_date']}")
                
                if 'next_hearing' in court_data:
                    summary_parts.append(f"Next hearing scheduled for: {court_data['next_hearing']}")
                
                if 'parties' in court_data:
                    parties = court_data['parties']
                    petitioner = parties.get('petitioner', 'Unknown')
                    respondent = parties.get('respondent', 'Unknown')
                    summary_parts.append(f"Parties involved: {petitioner} vs {respondent}")
                
                if 'orders' in court_data and court_data['orders']:
                    summary_parts.append(f"Latest order: {court_data['orders'][-1].get('order', 'No recent orders')}")
                    
            elif 'cases' in court_data:
                # Multiple cases summary
                court = court_data.get('court_name', 'Multiple Courts')
                total = len(court_data.get('cases', []))
                
                summary_parts.append(f"Court Cases Summary for {court}:")
                summary_parts.append(f"Total cases found: {total}")
                
                if court_data.get('cases'):
                    summary_parts.append("Case highlights:")
                    for case in court_data['cases'][:3]:  # Show first 3 cases
                        case_num = case.get('case_number', 'N/A')
                        title = case.get('case_title', 'Title not available')
                        status = case.get('status', 'Status unknown')
                        summary_parts.append(f"  - {case_num}: {title} (Status: {status})")
                    
                    if total > 3:
                        summary_parts.append(f"  ... and {total - 3} more cases")
            
            else:
                # Generic summary
                summary_parts.append("Court Data Summary:")
                summary_parts.append("Retrieved court information from the legal database.")
                summary_parts.append(f"Data contains: {', '.join(court_data.keys())}")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error in fallback summary: {e}")
            return "Unable to generate summary for the provided court data."
    
    def _fallback_summary_text(self) -> str:
        """Default summary when all else fails"""
        return ("Summary: Court case information has been processed and retrieved from the legal database. "
                "The case details include relevant parties, filing information, current status, and procedural history. "
                "This information provides a comprehensive overview of the legal proceedings.")
    
    def test_langchain_connection(self) -> bool:
        """
        Test LangChain ChatGroq connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info("Testing LangChain ChatGroq connection...")
            
            # Simple test message
            test_response = self.client.invoke("Say hello in one sentence.")
            self.logger.info(f"LangChain ChatGroq test response: {test_response.content}")
            print("✅ LangChain ChatGroq connection successful!")
            return True
            
        except Exception as e:
            self.logger.error(f"LangChain ChatGroq connection test failed: {e}")
            print("❌ LangChain ChatGroq connection failed!")
            return False
