import json
import logging
from typing import Dict, Any, List
from email_tools import EmailTools
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ToolRouter:
    """
    Enterprise Tool Router with comprehensive validation and audit logging.
    Addresses tool calling challenges with robust error handling.
    """
    
    def __init__(self):
        self.email_tools = EmailTools()
        self.tool_handlers = {
            "classify_email": self.email_tools.classify_email,
            "generate_draft": self.email_tools.generate_draft,
            "schedule_meeting": self.email_tools.schedule_meeting,
            "create_task": self.email_tools.create_task
        }
    
    def route_tool_call(self, tool_name: str, tool_args: Dict[str, Any], email_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Route tool call to appropriate handler with enterprise validation.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            email_data: Original email data for context
            request_id: Unique request identifier
            
        Returns:
            Tool execution result with enterprise metadata
        """
        try:
            logger.info(f"Routing tool call: {tool_name} with args: {tool_args}")
            
            # Validate tool exists
            if tool_name not in self.tool_handlers:
                return {
                    "status": "error",
                    "message": f"Unknown tool: {tool_name}. Available tools: {list(self.tool_handlers.keys())}",
                    "request_id": request_id
                }
            
            # Get tool handler
            handler = self.tool_handlers[tool_name]
            
            # Validate arguments before calling
            validation_result = self._validate_tool_args(tool_name, tool_args)
            if validation_result["status"] != "valid":
                return {
                    "status": "error",
                    "message": validation_result["message"],
                    "request_id": request_id,
                    "validation_errors": validation_result.get("errors", [])
                }
            
            # Execute tool with enterprise context
            result = handler(**tool_args)
            
            # Add enterprise metadata
            result["request_id"] = request_id
            result["tool_name"] = tool_name
            result["email_context"] = {
                "subject": email_data.get("subject", ""),
                "sender": email_data.get("sender", ""),
                "user_id": email_data.get("user_id", "anonymous")
            }
            
            logger.info(f"Tool execution completed: {tool_name}")
            return result
            
        except TypeError as e:
            logger.error(f"Type error in tool call {tool_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Invalid arguments for {tool_name}: {str(e)}",
                "request_id": request_id
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Tool execution failed: {str(e)}",
                "request_id": request_id
            }
    
    def _validate_tool_args(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tool arguments against enterprise schema.
        
        Args:
            tool_name: Name of the tool
            tool_args: Arguments to validate
            
        Returns:
            Validation result with detailed error information
        """
        try:
            # Get tool schema
            tools = self.email_tools.get_available_tools()
            tool_schema = None
            
            for tool in tools:
                if tool["name"] == tool_name:
                    tool_schema = tool["input_schema"]
                    break
            
            if not tool_schema:
                return {
                    "status": "error",
                    "message": f"No schema found for tool: {tool_name}",
                    "errors": []
                }
            
            # Check required fields
            required_fields = tool_schema.get("required", [])
            missing_fields = []
            
            for field in required_fields:
                if field not in tool_args or tool_args[field] is None or tool_args[field] == "":
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    "status": "error",
                    "message": f"Missing required fields for {tool_name}: {', '.join(missing_fields)}",
                    "errors": [{"field": field, "error": "required"} for field in missing_fields]
                }
            
            # Validate field types and constraints
            properties = tool_schema.get("properties", {})
            validation_errors = []
            
            for field, value in tool_args.items():
                if field in properties:
                    field_schema = properties[field]
                    field_validation = self._validate_field(field, value, field_schema)
                    if field_validation["status"] != "valid":
                        validation_errors.append({
                            "field": field,
                            "error": field_validation["message"],
                            "value": value
                        })
            
            if validation_errors:
                return {
                    "status": "error",
                    "message": f"Validation errors for {tool_name}",
                    "errors": validation_errors
                }
            
            return {"status": "valid"}
            
        except Exception as e:
            logger.error(f"Error validating tool args: {str(e)}")
            return {
                "status": "error",
                "message": f"Validation error: {str(e)}",
                "errors": []
            }
    
    def _validate_field(self, field_name: str, value: Any, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate individual field against enterprise schema.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            field_schema: Schema for the field
            
        Returns:
            Validation result
        """
        try:
            # Check type
            expected_type = field_schema.get("type")
            if expected_type:
                if expected_type == "string" and not isinstance(value, str):
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must be a string"
                    }
                elif expected_type == "integer" and not isinstance(value, int):
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must be an integer"
                    }
                elif expected_type == "array" and not isinstance(value, list):
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must be an array"
                    }
            
            # Check enum values
            enum_values = field_schema.get("enum")
            if enum_values and value not in enum_values:
                return {
                    "status": "error",
                    "message": f"Field '{field_name}' must be one of: {enum_values}"
                }
            
            # Check minimum/maximum for integers
            if expected_type == "integer":
                min_val = field_schema.get("minimum")
                max_val = field_schema.get("maximum")
                if min_val is not None and value < min_val:
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must be at least {min_val}"
                    }
                if max_val is not None and value > max_val:
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must be at most {max_val}"
                    }
            
            # Check array constraints
            if expected_type == "array":
                min_items = field_schema.get("minItems")
                if min_items is not None and len(value) < min_items:
                    return {
                        "status": "error",
                        "message": f"Field '{field_name}' must have at least {min_items} items"
                    }
            
            return {"status": "valid"}
            
        except Exception as e:
            logger.error(f"Error validating field {field_name}: {str(e)}")
            return {
                "status": "error",
                "message": f"Field validation error: {str(e)}"
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with their enterprise schemas."""
        return self.email_tools.get_available_tools()
    
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Get enterprise schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema or error
        """
        tools = self.get_available_tools()
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        
        return {
            "status": "error",
            "message": f"Tool '{tool_name}' not found"
        }
