import json
import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmailTools:
    """
    Email processing tools with robust argument validation.
    Addresses the tool calling issues mentioned in the interview.
    """
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools with complete schemas."""
        return [
            {
                "name": "classify_email",
                "description": "Classify the email type and determine priority level",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "email_type": {
                            "type": "string",
                            "enum": ["inquiry", "complaint", "meeting_request", "task_assignment", "spam", "other"],
                            "description": "The type of email received"
                        },
                        "priority": {
                            "type": "string", 
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Priority level of the email"
                        },
                        "category": {
                            "type": "string",
                            "description": "Brief category description"
                        }
                    },
                    "required": ["email_type", "priority", "category"]
                }
            },
            {
                "name": "generate_draft",
                "description": "Generate a professional draft response to the email",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tone": {
                            "type": "string",
                            "enum": ["formal", "friendly", "neutral", "apologetic"],
                            "description": "Tone of the response"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary of the email content"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Urgency level for response"
                        },
                        "response_type": {
                            "type": "string",
                            "enum": ["acknowledgment", "information_request", "meeting_proposal", "task_confirmation"],
                            "description": "Type of response needed"
                        }
                    },
                    "required": ["tone", "summary", "urgency", "response_type"]
                }
            },
            {
                "name": "schedule_meeting",
                "description": "Schedule a meeting based on email request",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "format": "date",
                            "description": "Meeting date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Meeting time in HH:MM format"
                        },
                        "duration": {
                            "type": "integer",
                            "minimum": 15,
                            "maximum": 480,
                            "description": "Meeting duration in minutes"
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "description": "List of attendee email addresses"
                        },
                        "meeting_title": {
                            "type": "string",
                            "description": "Title/subject of the meeting"
                        }
                    },
                    "required": ["date", "time", "duration", "attendees", "meeting_title"]
                }
            },
            {
                "name": "create_task",
                "description": "Create a follow-up task based on email content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed task description"
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date",
                            "description": "Due date in YYYY-MM-DD format"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Task priority"
                        },
                        "assignee": {
                            "type": "string",
                            "description": "Email of person assigned to task"
                        }
                    },
                    "required": ["title", "description", "due_date", "priority", "assignee"]
                }
            }
        ]
    
    def classify_email(self, email_type: str, priority: str, category: str) -> Dict[str, Any]:
        """
        Classify email with validation.
        
        Args:
            email_type: Type of email
            priority: Priority level
            category: Category description
            
        Returns:
            Classification result
        """
        try:
            # Validate required arguments
            if not all([email_type, priority, category]):
                return {
                    "status": "error",
                    "message": "Missing required arguments: email_type, priority, category"
                }
            
            # Validate enum values
            valid_types = ["inquiry", "complaint", "meeting_request", "task_assignment", "spam", "other"]
            valid_priorities = ["low", "medium", "high", "urgent"]
            
            if email_type not in valid_types:
                return {
                    "status": "error", 
                    "message": f"Invalid email_type. Must be one of: {valid_types}"
                }
            
            if priority not in valid_priorities:
                return {
                    "status": "error",
                    "message": f"Invalid priority. Must be one of: {valid_priorities}"
                }
            
            classification = {
                "status": "success",
                "classification": {
                    "email_type": email_type,
                    "priority": priority,
                    "category": category,
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": 0.95
                }
            }
            
            logger.info(f"Email classified: {classification}")
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying email: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def generate_draft(self, tone: str, summary: str, urgency: str, response_type: str) -> Dict[str, Any]:
        """
        Generate email draft with validation.
        
        Args:
            tone: Response tone
            summary: Email summary
            urgency: Urgency level
            response_type: Type of response
            
        Returns:
            Generated draft
        """
        try:
            # Validate required arguments
            required_args = {"tone": tone, "summary": summary, "urgency": urgency, "response_type": response_type}
            missing_args = [k for k, v in required_args.items() if not v]
            
            if missing_args:
                return {
                    "status": "error",
                    "message": f"Missing required arguments: {', '.join(missing_args)}"
                }
            
            # Validate enum values
            valid_tones = ["formal", "friendly", "neutral", "apologetic"]
            valid_urgencies = ["low", "medium", "high"]
            valid_response_types = ["acknowledgment", "information_request", "meeting_proposal", "task_confirmation"]
            
            if tone not in valid_tones:
                return {
                    "status": "error",
                    "message": f"Invalid tone. Must be one of: {valid_tones}"
                }
            
            if urgency not in valid_urgencies:
                return {
                    "status": "error",
                    "message": f"Invalid urgency. Must be one of: {valid_urgencies}"
                }
            
            if response_type not in valid_response_types:
                return {
                    "status": "error",
                    "message": f"Invalid response_type. Must be one of: {valid_response_types}"
                }
            
            # Generate draft based on parameters
            draft_content = self._create_draft_content(tone, summary, urgency, response_type)
            
            draft = {
                "status": "success",
                "draft": {
                    "content": draft_content,
                    "tone": tone,
                    "urgency": urgency,
                    "response_type": response_type,
                    "summary": summary,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Draft generated: {draft}")
            return draft
            
        except Exception as e:
            logger.error(f"Error generating draft: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def schedule_meeting(self, date: str, time: str, duration: int, attendees: List[str], meeting_title: str) -> Dict[str, Any]:
        """
        Schedule meeting with validation.
        
        Args:
            date: Meeting date
            time: Meeting time
            duration: Duration in minutes
            attendees: List of attendee emails
            meeting_title: Meeting title
            
        Returns:
            Meeting scheduling result
        """
        try:
            # Validate required arguments
            required_args = {"date": date, "time": time, "duration": duration, "attendees": attendees, "meeting_title": meeting_title}
            missing_args = [k for k, v in required_args.items() if not v]
            
            if missing_args:
                return {
                    "status": "error",
                    "message": f"Missing required arguments: {', '.join(missing_args)}"
                }
            
            # Validate duration
            if not isinstance(duration, int) or duration < 15 or duration > 480:
                return {
                    "status": "error",
                    "message": "Duration must be an integer between 15 and 480 minutes"
                }
            
            # Validate attendees
            if not isinstance(attendees, list) or len(attendees) < 1:
                return {
                    "status": "error",
                    "message": "Attendees must be a non-empty list"
                }
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return {
                    "status": "error",
                    "message": "Date must be in YYYY-MM-DD format"
                }
            
            # Validate time format
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                return {
                    "status": "error",
                    "message": "Time must be in HH:MM format"
                }
            
            meeting = {
                "status": "success",
                "meeting": {
                    "title": meeting_title,
                    "date": date,
                    "time": time,
                    "duration": duration,
                    "attendees": attendees,
                    "meeting_id": f"meeting_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Meeting scheduled: {meeting}")
            return meeting
            
        except Exception as e:
            logger.error(f"Error scheduling meeting: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def create_task(self, title: str, description: str, due_date: str, priority: str, assignee: str) -> Dict[str, Any]:
        """
        Create task with validation.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date
            priority: Task priority
            assignee: Assignee email
            
        Returns:
            Task creation result
        """
        try:
            # Validate required arguments
            required_args = {"title": title, "description": description, "due_date": due_date, "priority": priority, "assignee": assignee}
            missing_args = [k for k, v in required_args.items() if not v]
            
            if missing_args:
                return {
                    "status": "error",
                    "message": f"Missing required arguments: {', '.join(missing_args)}"
                }
            
            # Validate priority
            valid_priorities = ["low", "medium", "high"]
            if priority not in valid_priorities:
                return {
                    "status": "error",
                    "message": f"Invalid priority. Must be one of: {valid_priorities}"
                }
            
            # Validate date format
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "status": "error",
                    "message": "Due date must be in YYYY-MM-DD format"
                }
            
            task = {
                "status": "success",
                "task": {
                    "title": title,
                    "description": description,
                    "due_date": due_date,
                    "priority": priority,
                    "assignee": assignee,
                    "task_id": f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "status": "pending",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Task created: {task}")
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_draft_content(self, tone: str, summary: str, urgency: str, response_type: str) -> str:
        """Create draft email content based on parameters."""
        
        # Tone-based greetings
        greetings = {
            "formal": "Dear Sir/Madam,",
            "friendly": "Hi there!",
            "neutral": "Hello,",
            "apologetic": "Dear [Name],"
        }
        
        # Urgency-based language
        urgency_language = {
            "low": "I'll get back to you when I have a chance.",
            "medium": "I'll respond to this shortly.",
            "high": "I'll prioritize this and respond as soon as possible."
        }
        
        # Response type templates
        templates = {
            "acknowledgment": f"Thank you for reaching out regarding {summary}. {urgency_language[urgency]}",
            "information_request": f"I received your inquiry about {summary}. Let me gather the information you need. {urgency_language[urgency]}",
            "meeting_proposal": f"Thank you for your meeting request regarding {summary}. I'd be happy to schedule a time to discuss this further. {urgency_language[urgency]}",
            "task_confirmation": f"I've received your request about {summary} and will add it to my task list. {urgency_language[urgency]}"
        }
        
        greeting = greetings.get(tone, "Hello,")
        template = templates.get(response_type, templates["acknowledgment"])
        
        draft = f"""{greeting}

{template}

Best regards,
AI Assistant"""
        
        return draft
