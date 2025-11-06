import json
import boto3
import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from email_tools import EmailTools
from tool_router import ToolRouter
from bedrock_handler import BedrockHandler
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_handler = BedrockHandler()
email_tools = EmailTools()
tool_router = ToolRouter()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Enterprise Email Intelligence Platform Lambda Handler.
    Processes emails via API Gateway with comprehensive audit logging.
    
    Args:
        event: API Gateway event containing email data
        context: Lambda context object
        
    Returns:
        Dict containing processing status and results
    """
    try:
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        logger.info(f"Processing request {request_id}: {json.dumps(event)}")
        
        # Extract email data from API Gateway event
        email_data = extract_email_from_api_event(event)
        
        # Log audit trail
        audit_log = create_audit_log(request_id, email_data, "PROCESSING_STARTED")
        save_audit_log(audit_log)
        
        # Process email with Claude
        result = process_email_with_claude(email_data, request_id)
        
        # Update audit log with results
        audit_log.update({
            "status": "COMPLETED",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        })
        save_audit_log(audit_log)
        
        logger.info(f"Email processing completed for request {request_id}: {result}")
        
        # Return enterprise-standard response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
                "X-Processing-Time": str(result.get("processing_time_ms", 0))
            },
            "body": json.dumps({
                "request_id": request_id,
                "status": "success",
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}", exc_info=True)
        
        # Log error in audit trail
        error_audit = create_audit_log(request_id if 'request_id' in locals() else str(uuid.uuid4()), 
                                     {"error": str(e)}, "ERROR")
        save_audit_log(error_audit)
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": request_id if 'request_id' in locals() else str(uuid.uuid4())
            },
            "body": json.dumps({
                "request_id": request_id if 'request_id' in locals() else str(uuid.uuid4()),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        }

def extract_email_from_api_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract email data from API Gateway event."""
    try:
        # Handle different event formats
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
            
        # Extract email fields
        email_data = {
            "subject": body.get("subject", ""),
            "sender": body.get("sender", ""),
            "recipient": body.get("recipient", ""),
            "body": body.get("body", ""),
            "user_id": body.get("user_id", "anonymous"),
            "metadata": body.get("metadata", {})
        }
        
        logger.info(f"Extracted email data: {email_data}")
        return email_data
        
    except Exception as e:
        logger.error(f"Failed to extract email from API event: {str(e)}")
        raise

def create_audit_log(request_id: str, email_data: Dict[str, Any], status: str) -> Dict[str, Any]:
    """Create audit log entry for compliance tracking."""
    return {
        "email_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": email_data.get("user_id", "anonymous"),
        "status": status,
        "email_subject": email_data.get("subject", ""),
        "email_sender": email_data.get("sender", ""),
        "processing_started_at": datetime.utcnow().isoformat(),
        "metadata": email_data.get("metadata", {})
    }

def save_audit_log(audit_log: Dict[str, Any]) -> None:
    """Save audit log to DynamoDB for compliance."""
    try:
        table_name = os.getenv('DYNAMODB_AUDIT_TABLE', 'email-audit-log')
        table = dynamodb.Table(table_name)
        
        table.put_item(Item=audit_log)
        logger.info(f"Audit log saved: {audit_log['email_id']}")
        
    except Exception as e:
        logger.error(f"Failed to save audit log: {str(e)}")
        # Don't raise - audit logging failure shouldn't break main flow

def process_email_with_claude(email_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Process email content with Claude 3 Sonnet using tool calling.
    
    Args:
        email_data: Email data dictionary
        request_id: Unique request identifier
        
    Returns:
        Dict containing processing results
    """
    try:
        start_time = datetime.utcnow()
        
        # Define available tools for Claude
        tools = email_tools.get_available_tools()
        
        # Create system prompt
        system_prompt = create_system_prompt()
        
        # Format email content for Claude
        email_content = format_email_for_claude(email_data)
        
        # Send request to Claude
        response = bedrock_handler.invoke_model_with_tools(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_content}
            ],
            tools=tools
        )
        
        # Process Claude's response
        result = process_claude_response(response, email_data, request_id)
        
        # Add processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        result["processing_time_ms"] = int(processing_time)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing email with Claude: {str(e)}")
        raise

def format_email_for_claude(email_data: Dict[str, Any]) -> str:
    """Format email data for Claude processing."""
    return f"""
Subject: {email_data.get('subject', 'No Subject')}
From: {email_data.get('sender', 'Unknown Sender')}
To: {email_data.get('recipient', 'Unknown Recipient')}

{email_data.get('body', 'No content')}

Metadata: {json.dumps(email_data.get('metadata', {}))}
"""

def create_system_prompt() -> str:
    """Create system prompt for Claude."""
    return """
    You are an AI email assistant that helps process incoming emails. Your job is to:
    
    1. Analyze the email content to determine if a response is needed
    2. If no response is needed, return {"action": "skip", "reason": "brief explanation"}
    3. If a response is needed, use the appropriate tool with ALL required arguments
    
    IMPORTANT: When calling tools, you MUST provide ALL required arguments. Check the tool schema carefully.
    
    Available tools:
    - classify_email: Categorize the email type and priority
    - generate_draft: Create a draft response (requires tone, summary, and urgency)
    - schedule_meeting: Schedule a meeting (requires date, time, duration, and attendees)
    - create_task: Create a follow-up task (requires title, description, and due_date)
    
    Always validate that you have all required arguments before calling any tool.
    """

def process_claude_response(response: Dict[str, Any], email_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Process Claude's response and execute tool calls if needed.
    
    Args:
        response: Claude's response containing tool calls or decisions
        email_data: Original email data
        request_id: Unique request identifier
        
    Returns:
        Dict containing processing results
    """
    try:
        content = response.get('content', [])
        
        if not content:
            return {'status': 'error', 'message': 'No content in Claude response'}
        
        # Check if Claude wants to skip the email
        if len(content) == 1 and 'text' in content[0]:
            try:
                text_content = content[0]['text']
                if 'skip' in text_content.lower():
                    return {'status': 'skipped', 'reason': text_content}
            except:
                pass
        
        # Process tool calls
        for item in content:
            if 'tool_use' in item:
                tool_call = item['tool_use']
                tool_name = tool_call['name']
                tool_args = tool_call['input']
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                # Route tool call to appropriate handler
                result = tool_router.route_tool_call(tool_name, tool_args, email_data, request_id)
                
                if result.get('status') == 'success':
                    # Save classification to DynamoDB
                    save_classification_to_db(result, email_data, request_id)
                    return result
                else:
                    logger.error(f"Tool execution failed: {result}")
                    return result
        
        # If no tool calls, treat as skip
        return {'status': 'skipped', 'reason': 'No action required'}
        
    except Exception as e:
        logger.error(f"Error processing Claude response: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def save_classification_to_db(result: Dict[str, Any], email_data: Dict[str, Any], request_id: str) -> None:
    """Save classification result to DynamoDB for enterprise tracking."""
    try:
        table_name = os.getenv('DYNAMODB_CLASSIFICATION_TABLE', 'email-classifications')
        table = dynamodb.Table(table_name)
        
        classification_item = {
            "classification_id": request_id,
            "email_subject": email_data.get("subject", ""),
            "email_sender": email_data.get("sender", ""),
            "user_id": email_data.get("user_id", "anonymous"),
            "classification_result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "ttl": int((datetime.utcnow().timestamp() + (365 * 24 * 60 * 60)))  # 1 year TTL
        }
        
        table.put_item(Item=classification_item)
        logger.info(f"Classification saved to DynamoDB: {request_id}")
        
    except Exception as e:
        logger.error(f"Failed to save classification to DynamoDB: {str(e)}")
        # Don't raise - classification saving failure shouldn't break main flow
