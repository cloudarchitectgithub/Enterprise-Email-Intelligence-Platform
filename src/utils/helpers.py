import os
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import boto3

def validate_email_format(email: str) -> bool:
    """
    Validate email format using enterprise regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid enterprise email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate date format for enterprise compliance.
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        True if valid date format
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_time_format(time_str: str, format_str: str = "%H:%M") -> bool:
    """
    Validate time format for enterprise scheduling.
    
    Args:
        time_str: Time string to validate
        format_str: Expected time format
        
    Returns:
        True if valid time format
    """
    try:
        datetime.strptime(time_str, format_str)
        return True
    except ValueError:
        return False

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for enterprise security.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized.strip()

def extract_email_addresses(text: str) -> List[str]:
    """
    Extract email addresses from text for enterprise processing.
    
    Args:
        text: Text to search for emails
        
    Returns:
        List of email addresses found
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format timestamp for enterprise consistency.
    
    Args:
        timestamp: Timestamp to format (defaults to now)
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    return timestamp.isoformat()

def parse_email_content(email_text: str) -> Dict[str, Any]:
    """
    Parse email content to extract enterprise information.
    
    Args:
        email_text: Raw email text
        
    Returns:
        Parsed email information with enterprise metadata
    """
    try:
        # Extract subject (look for Subject: line)
        subject_match = re.search(r'Subject:\s*(.+)', email_text, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "No Subject"
        
        # Extract sender (look for From: line)
        from_match = re.search(r'From:\s*(.+)', email_text, re.IGNORECASE)
        sender = from_match.group(1).strip() if from_match else "Unknown Sender"
        
        # Extract recipient (look for To: line)
        to_match = re.search(r'To:\s*(.+)', email_text, re.IGNORECASE)
        recipient = to_match.group(1).strip() if to_match else "Unknown Recipient"
        
        # Extract date (look for Date: line)
        date_match = re.search(r'Date:\s*(.+)', email_text, re.IGNORECASE)
        date = date_match.group(1).strip() if date_match else "Unknown Date"
        
        # Extract body (everything after headers)
        body_match = re.search(r'\n\n(.+)', email_text, re.DOTALL)
        body = body_match.group(1).strip() if body_match else email_text
        
        return {
            "subject": subject,
            "sender": sender,
            "recipient": recipient,
            "date": date,
            "body": body,
            "sender_emails": extract_email_addresses(sender),
            "recipient_emails": extract_email_addresses(recipient),
            "enterprise_metadata": {
                "parsed_at": format_timestamp(),
                "content_length": len(email_text),
                "has_attachments": "attachment" in email_text.lower()
            }
        }
        
    except Exception as e:
        return {
            "subject": "Parse Error",
            "sender": "Unknown",
            "recipient": "Unknown", 
            "date": "Unknown",
            "body": email_text,
            "sender_emails": [],
            "recipient_emails": [],
            "error": str(e),
            "enterprise_metadata": {
                "parse_error": True,
                "parsed_at": format_timestamp()
            }
        }

def create_dynamodb_key(prefix: str, identifier: str, timestamp: Optional[datetime] = None) -> str:
    """
    Create DynamoDB key with enterprise timestamp.
    
    Args:
        prefix: Key prefix
        identifier: Unique identifier
        timestamp: Timestamp for key (defaults to now)
        
    Returns:
        DynamoDB key string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}#{identifier}#{timestamp_str}"

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string for enterprise use.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON for enterprise use.
    
    Args:
        obj: Object to serialize
        default: Default string if serialization fails
        
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        return default

def get_aws_region() -> str:
    """
    Get AWS region from environment or default.
    
    Returns:
        AWS region string
    """
    return os.getenv('AWS_REGION', 'us-east-1')

def is_development() -> bool:
    """
    Check if running in development environment.
    
    Returns:
        True if development environment
    """
    return os.getenv('ENVIRONMENT', 'dev').lower() in ['dev', 'development', 'local']

def is_enterprise_mode() -> bool:
    """
    Check if running in enterprise mode.
    
    Returns:
        True if enterprise mode
    """
    return os.getenv('ENTERPRISE_MODE', 'true').lower() == 'true'
