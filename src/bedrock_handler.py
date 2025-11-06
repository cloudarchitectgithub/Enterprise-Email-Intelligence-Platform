import json
import boto3
import logging
import time
import re
import os
from typing import Dict, Any, List, Optional

# Robust logger setup with fallback
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    # Fallback to basic logging if custom logger unavailable
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

class BedrockHandler:
    """
    Bedrock handler with multi-tier fallback strategy.
    
    Fallback Strategy:
    1. Primary: Claude 3 Sonnet (high capability)
    2. Fallback 1: Claude 3 Haiku (faster, cheaper)
    3. Fallback 2: Rule-based classification (no AI)
    
    Includes retry logic, exponential backoff, and comprehensive error handling.
    """
    
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Model hierarchy: Primary -> Fallback
        # Allow environment variable override for flexibility
        self.models = {
            'primary': os.environ.get('BEDROCK_PRIMARY_MODEL', "anthropic.claude-3-sonnet-20240229-v1:0"),
            'fallback': os.environ.get('BEDROCK_FALLBACK_MODEL', "anthropic.claude-3-haiku-20240307-v1:0")
        }
        
        self.current_model = self.models['primary']
        self.max_retries = int(os.environ.get('BEDROCK_MAX_RETRIES', '3'))
        self.retry_delay = int(os.environ.get('BEDROCK_RETRY_DELAY', '1'))  # seconds
        
    def invoke_model_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], 
                               max_tokens: int = 4000, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Invoke Claude model with enterprise tool calling support and fallback logic.
        
        Args:
            messages: List of message objects with role and content
            tools: List of available tools with enterprise schemas
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Model response with enterprise metadata
        """
        # Try primary model with retries
        response = self._invoke_with_retry(
            messages, tools, max_tokens, temperature, self.models['primary']
        )
        
        if response:
            return response
        
        # Fallback to Haiku model
        logger.warning("Primary model failed, falling back to Claude Haiku")
        response = self._invoke_with_retry(
            messages, tools, max_tokens, temperature, self.models['fallback']
        )
        
        if response:
            return response
        
        # Final fallback: Rule-based classification
        logger.error("All AI models failed, using rule-based fallback")
        return self._rule_based_fallback(messages)
    
    def _invoke_with_retry(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]], 
                          max_tokens: int, temperature: float, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Invoke model with retry logic and exponential backoff.
        
        Args:
            messages: Message list
            tools: Tool definitions
            max_tokens: Token limit
            temperature: Sampling temperature
            model_id: Model identifier
            
        Returns:
            Model response or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.max_retries} with model: {model_id}")
                
                # Prepare request body
                request_body = {
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "anthropic_version": "bedrock-2023-05-31"
                }
                
                # Invoke model
                response = self.bedrock_client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body),
                    contentType="application/json"
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                logger.info(f"✓ Model {model_id} responded successfully")
                return response_body
                
            except self.bedrock_client.exceptions.ModelNotReadyException as e:
                logger.warning(f"Model not ready: {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
            except self.bedrock_client.exceptions.ThrottlingException as e:
                logger.warning(f"Throttling detected: {str(e)}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Backing off for {delay} seconds...")
                    time.sleep(delay)
                    
            except self.bedrock_client.exceptions.ModelTimeoutException as e:
                logger.warning(f"Model timeout: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying with shorter timeout...")
                    time.sleep(self.retry_delay)
                    
            except self.bedrock_client.exceptions.AccessDeniedException as e:
                logger.error(f"Access denied to model {model_id}: {str(e)}")
                logger.error("Check Bedrock model access permissions in AWS console")
                return None  # No point retrying access denied
                
            except Exception as e:
                logger.error(f"Unexpected error invoking model: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        logger.error(f"All {self.max_retries} attempts failed for model {model_id}")
        return None
    
    def _rule_based_fallback(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Rule-based email classification when AI models are unavailable.
        Uses keyword matching and heuristics.
        
        Args:
            messages: Message list containing email content
            
        Returns:
            Simulated model response with classification
        """
        logger.info("Using rule-based fallback classification")
        
        # Extract email content
        email_content = ""
        for msg in messages:
            if msg.get('role') == 'user':
                email_content = msg.get('content', '').lower()
                break
        
        # Rule-based classification
        classification = self._classify_by_rules(email_content)
        
        # Return in Claude response format - mimics tool_use structure
        return {
            'content': [
                {
                    'type': 'tool_use',
                    'id': 'fallback_001',
                    'name': 'classify_email',
                    'input': classification
                }
            ],
            'fallback_mode': 'rule_based',
            'stop_reason': 'end_turn',
            'usage': {
                'input_tokens': 0,
                'output_tokens': 0
            }
        }
    
    def _classify_by_rules(self, email_content: str) -> Dict[str, str]:
        """
        Classify email using keyword-based rules.
        
        Args:
            email_content: Email text (lowercase)
            
        Returns:
            Classification dictionary
        """
        # Meeting keywords
        meeting_keywords = ['meeting', 'schedule', 'calendar', 'appointment', 'call', 'zoom', 'teams']
        
        # Urgency keywords
        urgent_keywords = ['urgent', 'asap', 'immediately', 'critical', 'emergency', 'important']
        
        # Task keywords
        task_keywords = ['task', 'todo', 'action item', 'follow up', 'deadline', 'deliverable']
        
        # Complaint keywords
        complaint_keywords = ['complaint', 'issue', 'problem', 'not working', 'broken', 'error', 'bug']
        
        # Inquiry keywords
        inquiry_keywords = ['question', 'inquiry', 'asking', 'wondering', 'clarification', 'information']
        
        # Determine email type
        email_type = "other"
        if any(keyword in email_content for keyword in meeting_keywords):
            email_type = "meeting_request"
        elif any(keyword in email_content for keyword in task_keywords):
            email_type = "task_assignment"
        elif any(keyword in email_content for keyword in complaint_keywords):
            email_type = "complaint"
        elif any(keyword in email_content for keyword in inquiry_keywords):
            email_type = "inquiry"
        
        # Determine priority
        priority = "medium"
        if any(keyword in email_content for keyword in urgent_keywords):
            priority = "urgent"
        elif len(email_content) < 100:
            priority = "low"
        elif email_type == "complaint":
            priority = "high"
        
        # Generate category
        category = f"Rule-based classification: {email_type}"
        
        logger.info(f"Rule-based classification: type={email_type}, priority={priority}")
        
        return {
            "email_type": email_type,
            "priority": priority,
            "category": category
        }
    
    def invoke_model_simple(self, prompt: str, max_tokens: int = 1000, 
                           temperature: float = 0.1) -> str:
        """
        Simple model invocation with fallback support.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        # Try primary model
        result = self._simple_invoke_with_retry(messages, max_tokens, temperature, self.models['primary'])
        if result:
            return result
        
        # Try fallback model
        logger.warning("Primary model failed, using Haiku for simple invocation")
        result = self._simple_invoke_with_retry(messages, max_tokens, temperature, self.models['fallback'])
        if result:
            return result
        
        # Final fallback
        return "AI models unavailable. Please try again later or contact support."
    
    def _simple_invoke_with_retry(self, messages: List[Dict[str, str]], max_tokens: int, 
                                  temperature: float, model_id: str) -> Optional[str]:
        """Simple invocation with retry logic."""
        for attempt in range(self.max_retries):
            try:
                request_body = {
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "anthropic_version": "bedrock-2023-05-31"
                }
                
                response = self.bedrock_client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body),
                    contentType="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                content = response_body.get('content', [])
                
                if content and 'text' in content[0]:
                    return content[0]['text']
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        return None
    
    def validate_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool call from the model with enterprise standards.
        
        Args:
            tool_call: Tool call object from model
            
        Returns:
            Validation result with enterprise metadata
        """
        try:
            required_fields = ['name', 'input']
            missing_fields = [field for field in required_fields if field not in tool_call]
            
            if missing_fields:
                return {
                    "status": "error",
                    "message": f"Tool call missing required fields: {missing_fields}",
                    "enterprise_validation": "failed"
                }
            
            tool_name = tool_call['name']
            tool_input = tool_call['input']
            
            if not isinstance(tool_input, dict):
                return {
                    "status": "error",
                    "message": f"Tool input must be a dictionary for tool: {tool_name}",
                    "enterprise_validation": "failed"
                }
            
            return {
                "status": "valid",
                "tool_name": tool_name,
                "tool_input": tool_input,
                "enterprise_validation": "passed"
            }
            
        except Exception as e:
            logger.error(f"Error validating tool call: {str(e)}")
            return {
                "status": "error",
                "message": f"Tool call validation error: {str(e)}",
                "enterprise_validation": "failed"
            }
    
    def extract_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool calls from model response with enterprise validation.
        Handles both Claude's native format and fallback format.
        
        Args:
            response: Model response
            
        Returns:
            List of validated tool calls
        """
        try:
            tool_calls = []
            content = response.get('content', [])
            
            for item in content:
                # Handle both formats: {'tool_use': {...}} and {'type': 'tool_use', ...}
                if 'tool_use' in item:
                    # Original format from Claude
                    tool_call = item['tool_use']
                    validation_result = self.validate_tool_call(tool_call)
                    
                    if validation_result['status'] == 'valid':
                        tool_calls.append(tool_call)
                    else:
                        logger.warning(f"Invalid tool call: {validation_result['message']}")
                        
                elif item.get('type') == 'tool_use':
                    # Fallback format (rule-based or alternative)
                    tool_call = {
                        'name': item.get('name'),
                        'input': item.get('input')
                    }
                    validation_result = self.validate_tool_call(tool_call)
                    
                    if validation_result['status'] == 'valid':
                        tool_calls.append(tool_call)
                    else:
                        logger.warning(f"Invalid tool call: {validation_result['message']}")
            
            return tool_calls
            
        except Exception as e:
            logger.error(f"Error extracting tool calls: {str(e)}")
            return []
    
    def has_tool_calls(self, response: Dict[str, Any]) -> bool:
        """
        Check if response contains tool calls.
        
        Args:
            response: Model response
            
        Returns:
            True if tool calls are present
        """
        return len(self.extract_tool_calls(response)) > 0
    
    def get_text_content(self, response: Dict[str, Any]) -> str:
        """
        Extract text content from model response.
        
        Args:
            response: Model response
            
        Returns:
            Text content
        """
        try:
            content = response.get('content', [])
            
            for item in content:
                if 'text' in item:
                    return item['text']
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
            return ""
    
    def create_system_prompt(self, context: str = "") -> str:
        """
        Create enterprise system prompt for email processing.
        
        Args:
            context: Additional enterprise context
            
        Returns:
            Enterprise system prompt
        """
        base_prompt = """
        You are an enterprise AI email assistant designed for professional organizations. Your responsibilities include:

        1. ANALYZE email content to determine if a response is needed
        2. CLASSIFY emails by type, priority, and category with enterprise standards
        3. GENERATE appropriate responses when needed with enterprise tone
        4. SCHEDULE meetings when requested with enterprise validation
        5. CREATE tasks for follow-up actions with enterprise metadata

        ENTERPRISE RULES:
        - When calling tools, you MUST provide ALL required arguments
        - Validate your tool calls before executing them
        - If unsure about any argument, ask for clarification rather than guessing
        - Always provide meaningful summaries and descriptions
        - Use appropriate enterprise tone and urgency levels
        - Maintain professional standards throughout

        Available enterprise tools:
        - classify_email: Requires email_type, priority, category
        - generate_draft: Requires tone, summary, urgency, response_type  
        - schedule_meeting: Requires date, time, duration, attendees, meeting_title
        - create_task: Requires title, description, due_date, priority, assignee

        If no response is needed, return: {"action": "skip", "reason": "brief explanation"}
        """
        
        if context:
            base_prompt += f"\n\nAdditional enterprise context: {context}"
        
        return base_prompt.strip()
    
    def get_fallback_status(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get information about which fallback tier was used.
        
        Args:
            response: Model response
            
        Returns:
            Fallback status information
        """
        return {
            "fallback_used": response.get('fallback_mode') is not None,
            "fallback_type": response.get('fallback_mode', 'none'),
            "model_used": self.current_model
        }
