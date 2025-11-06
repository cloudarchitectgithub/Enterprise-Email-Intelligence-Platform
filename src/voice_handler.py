"""
Voice-to-Text Handler for Email Editing
Provides hands-free email editing through speech-to-text functionality
"""
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

# Handle import for both Lambda and local execution
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except ImportError:
    # Fallback for local execution
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class VoiceHandler:
    """
    Handles voice-to-text conversion for email editing workflows.
    Supports both browser Web Speech API (demo) and AWS Transcribe (production).
    """
    
    def __init__(self):
        self.use_aws_transcribe = os.environ.get('USE_AWS_TRANSCRIBE', 'false').lower() == 'true'
        
        if self.use_aws_transcribe:
            try:
                import boto3
                self.transcribe_client = boto3.client('transcribe', region_name='us-east-1')
                logger.info("AWS Transcribe enabled for production")
            except ImportError:
                logger.warning("boto3 not available, using browser API fallback")
                self.use_aws_transcribe = False
    
    def process_voice_edit(self, voice_data: Dict[str, Any], email_draft: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process voice editing command and apply to email draft.
        
        Args:
            voice_data: Voice input with transcription text
            email_draft: Current email draft to edit
            
        Returns:
            Updated email draft with voice edits applied
        """
        try:
            transcription = voice_data.get('transcription', '')
            edit_type = voice_data.get('edit_type', 'replace')  # replace, append, modify
            
            logger.info(f"Processing voice edit: {edit_type} - {transcription[:50]}...ขั้น")
            
            # Parse voice command
            edit_result = self._parse_voice_command(transcription, email_draft, edit_type)
            
            return {
                "status": "success",
                "original_draft": email_draft,
                "edited_draft": edit_result,
                "voice_command": transcription,
                "edit_type": edit_type,
                "confidence": voice_data.get('confidence', 0.9)
            }
            
        except Exception as e:
            logger.error(f"Error processing voice edit: {str(e)}")
            return {
                "status": "error",
                "message": f"Voice edit processing failed: {str(e)}",
                "original_draft": email_draft
            }
    
    def _parse_voice_command(self, transcription: str, email_draft: Dict[str, Any], edit_type: str) -> Dict[str, Any]:
        """
        Parse voice command and apply to email draft.
        
        Voice commands supported:
        - "Change the tone to [formal/friendly/neutral]"
        - "Add that [text]"
        - "Remove [text]"
        - "Change subject to [text]"
        - "Make it more [urgent/professional/friendly]"
        """
        transcription_lower = transcription.lower()
        updated_draft = email_draft.copy()
        
        # Extract current content
        current_content = updated_draft.get('draft', {}).get('content', '')
        current_tone = updated_draft.get('draft', {}).get('tone', 'neutral')
        
        # Voice command patterns
        if 'change tone' in transcription_lower or 'make it' in transcription_lower:
            # Tone changes
            if 'formal' in transcription_lower:
                updated_draft['draft']['tone'] = 'formal'
                updated_draft['draft']['content'] = self._adjust_tone(current_content, 'formal')
            elif 'friendly' in transcription_lower:
                updated_draft['draft']['tone'] = 'friendly'
                updated_draft['draft']['content'] = self._adjust_tone(current_content, 'friendly')
            elif 'urgent' in transcription_lower:
                updated_draft['draft']['urgency'] = 'high'
        
        elif 'change subject' in transcription_lower or 'subject to' in transcription_lower:
            # Subject changes
            new_subject = self._extract_quoted_text(transcription) or transcription.split('subject to')[-1].strip()
            updated_draft['draft']['subject'] = new_subject
        
        elif 'add' in transcription_lower or 'include' in transcription_lower:
            # Additions
            text_to_add = transcription.split('add', 1)[-1].split('include', 1)[-1].strip()
            if text_to_add:
                updated_draft['draft']['content'] = f"{current_content}\n\n{text_to_add}"
        
        elif 'remove' in transcription_lower or 'delete' in transcription_lower:
            # Removals
            text_to_remove = transcription.split('remove', 1)[-1].split('delete', 1)[-1].strip()
            if text_to_remove and text_to_remove in current_content:
                updated_draft['draft']['content'] = current_content.replace(text_to_remove, '')
        
        elif edit_type == 'replace':
            # Full replacement
            updated_draft['draft']['content'] = transcription
        
        elif edit_type == 'append':
            # Append to existing
            updated_draft['draft']['content'] = f"{current_content}\n\n{transcription}"
        
        else:
            # Default: append
            updated_draft['draft']['content'] = f"{current_content}\n\n{transcription}"
        
        # Update timestamp
        from datetime import datetime
        updated_draft['draft']['last_edited'] = datetime.utcnow().isoformat()
        updated_draft['draft']['edited_via'] = 'voice'
        
        return updated_draft
    
    def _adjust_tone(self, content: str, new_tone: str) -> str:
        """Adjust email tone while preserving content."""
        # Simple tone adjustments
        tone_mapping = {
            'formal': {
                'hi': 'Dear',
                'hello': 'Dear',
                'thanks': 'Thank you',
                'yeah': 'Yes',
                'yea': 'Yes'
            },
            'friendly': {
                'dear': 'Hi',
                'thank you': 'Thanks',
                'sincerely': 'Best regards'
            }
        }
        
        if new_tone in tone_mapping:
            adjusted = content
            for old, new in tone_mapping[new_tone].items():
                adjusted = adjusted.replace(old, new)
            return adjusted
        
        return content
    
    def _extract_quoted_text(self, text: str) -> Optional[str]:
        """Extract text within quotes."""
        import re
        matches = re.findall(r'"([^"]*)"', text)
        if matches:
            return matches[0]
        matches = re.findall(r"'([^']*)'", text)
        if matches:
            return matches[0]
        return None

