"""
Enhanced Interactive Demo with Voice Editing
Demonstrates voice-controlled email editing capabilities
"""
import sys
import os
import json
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from src.voice_handler import VoiceHandler
    from src.voice_utils import setup_microphone, listen_with_fallback
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Run this script from the project root directory")
    sys.exit(1)

def mock_email_processing(email_content: str, client_email: str) -> Dict[str, Any]:
    """
    Mock email processing - simulates your Lambda/Bedrock workflow
    In production, this would call your actual Lambda function
    """
    # Determine priority based on keywords
    priority = "urgent" if "URGENT" in email_content or "immediately" in email_content.lower() else "medium"
    
    # Determine type based on keywords
    if "access" in email_content.lower() or "login" in email_content.lower():
        email_type = "technical_support"
        response = f"""Dear Valued Client,

Thank you for contacting us regarding your account access issue.

Our technical team has been notified and is working to resolve this {priority} priority matter. You can expect an update within the next business day.

In the meantime, please try:
- Clearing your browser cache
- Using a different browser
- Resetting your password at portal.example.com/reset

Best regards,
Technical Support Team"""
    elif "budget" in email_content.lower() or "invoice" in email_content.lower():
        email_type = "billing_inquiry"
        response = """Dear Valued Client,

Thank you for your inquiry regarding the billing details.

I've reviewed your account and will prepare a detailed breakdown of the generative AI service charges. This will include:
- Service usage breakdown
- Cost optimization recommendations
- Alignment with your AI budget goals

I'll send this analysis within 24 hours.

Best regards,
Billing Department"""
    else:
        email_type = "general_inquiry"
        response = """Dear Valued Client,

Thank you for reaching out to us.

We've received your inquiry and our team will review it carefully. You can expect a response within one business day.

Best regards,
Client Support Team"""
    
    return {
        "status": "success",
        "result": {
            "classification": {
                "email_type": email_type,
                "priority": priority,
                "category": f"Client {email_type.replace('_', ' ')}"
            },
            "draft": {
                "subject": "Re: Your inquiry",
                "content": response,
                "tone": "professional",
                "urgency": priority
            }
        }
    }

class VoiceInteractiveDemo:
    def __init__(self):
        self.voice_handler = VoiceHandler()
        
        # Setup microphone (optional - falls back to keyboard if unavailable)
        print("[Voice] Initializing voice input...")
        self.recognizer, self.microphone = setup_microphone()
        if self.recognizer and self.microphone:
            print("[OK] Voice input ready! You can use your microphone.")
        else:
            print("[INFO] Voice input unavailable. Using keyboard input mode.")
        
        self.demo_emails = [
            {
                "name": "Urgent Client Portal Issue",
                "content": """URGENT: Our team cannot access the client portal. 
We have a major presentation in 2 hours and need our project files immediately. 
This is blocking a critical client deliverable.""",
                "client": "ceo@bigcompany.com",
                "initial_draft": None
            },
            {
                "name": "Budget Inquiry", 
                "content": """Hi, I'm reviewing our quarterly invoices and noticed significant charges 
for generative AI services. Can you provide a detailed breakdown of what this includes 
and how it aligns with our AI budget optimization goals?""",
                "client": "cfo@enterprise.com",
                "initial_draft": None
            }
        ]
    
    def speak(self, text: str):
        """Simple text output simulating TTS"""
        print(f"\n[SYSTEM] {text}")
    
    def listen(self) -> Dict[str, Any]:
        """Listen for voice or keyboard input"""
        print("\n[Voice] Voice Editing:")
        print("   Examples: 'Make it more formal', 'Add please contact support', 'Change tone to friendly'")
        
        # Use voice utilities with automatic fallback
        user_input = listen_with_fallback(
            self.recognizer, 
            self.microphone, 
            prompt="Edit command"
        )
        
        if not user_input:
            return {"transcription": "", "confidence": 0.0, "edit_type": "replace"}
        
        return {
            "transcription": user_input,
            "confidence": 0.85 if self.microphone else 0.95,  # Higher confidence for keyboard
            "edit_type": self._detect_edit_type(user_input)
        }
    
    def _detect_edit_type(self, text: str) -> str:
        """Detect edit type from voice command"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['add', 'include', 'also']):
            return "append"
        elif any(word in text_lower for word in ['remove', 'delete', 'take out']):
            return "remove" 
        elif any(word in text_lower for word in ['change', 'modify', 'edit', 'tone', 'make it']):
            return "modify"
        else:
            return "replace"
    
    def display_draft(self, draft: Dict[str, Any], title: str = "DRAFT"):
        """Display email draft"""
        print(f"\n{'='*70}")
        print(f"[EMAIL] {title}")
        print(f"{'='*70}")
        
        draft_content = draft.get('draft', {})
        
        print(f"Subject: {draft_content.get('subject', 'No Subject')}")
        print(f"Tone: {draft_content.get('tone', 'professional').upper()}")
        print(f"Urgency: {draft_content.get('urgency', 'medium').upper()}")
        print("\n" + "-" * 70)
        print(draft_content.get('content', 'No content'))
        print("-" * 70)
        
        if draft_content.get('edited_via'):
            print(f"[EDIT] Edited via: {draft_content.get('edited_via')}")
        
        print(f"{'='*70}\n")
    
    def run_demo(self):
        """Main demo execution"""
        print("\n" + "="*70)
        print("EMAIL ASSISTANT - VOICE EDITING DEMO")
        print("="*70)
        self.speak("Welcome! This demo shows voice-controlled email editing.")
        print("\n[INFO] This demonstrates:")
        print("   • AI-powered email drafting")
        print("   • Voice-controlled editing")
        print("   • Human-in-the-loop workflow\n")
        
        time.sleep(2)
        
        for i, email in enumerate(self.demo_emails, 1):
            print(f"\n[EMAIL {i}/{len(self.demo_emails)}] {email['name']}")
            print("=" * 70)
            print("Original Email:")
            print(email['content'])
            print("=" * 70)
            
            # Step 1: AI processes email
            self.speak(f"Processing email through AI workflow...")
            time.sleep(1)
            
            result = mock_email_processing(email['content'], email['client'])
            initial_draft = self._result_to_draft(result, email)
            
            self.display_draft(initial_draft, "AI-GENERATED DRAFT")
            
            # Step 2: Voice editing
            self.speak("Draft ready for review. Use voice commands to edit.")
            
            edit_count = 0
            while True:
                print("\n[OPTIONS]")
                print("  1. [Voice] Voice edit")
                print("  2. [OK] Approve & next")
                print("  3. [Refresh] Regenerate")
                
                choice = input("\nChoose (1-3): ").strip()
                
                if choice == "1":
                    voice_data = self.listen()
                    
                    if voice_data['transcription']:
                        print(f"\n[Processing] Processing: '{voice_data['transcription']}'...")
                        
                        edited = self.voice_handler.process_voice_edit(
                            voice_data, initial_draft
                        )
                        
                        if edited['status'] == 'success':
                            edit_count += 1
                            self.display_draft(edited['edited_draft'], f"VOICE-EDITED DRAFT (Edit #{edit_count})")
                            self.speak("[OK] Edit applied")
                            initial_draft = edited['edited_draft']
                        else:
                            print(f"[ERROR] Edit failed: {edited.get('message')}")
                
                elif choice == "2":
                    self.speak("✓ Draft approved!")
                    break
                
                elif choice == "3":
                    self.speak("Regenerating draft...")
                    result = mock_email_processing(email['content'], email['client'])
                    initial_draft = self._result_to_draft(result, email)
                    self.display_draft(initial_draft, "REGENERATED DRAFT")
                
                else:
                    print("[ERROR] Invalid choice")
            
            if i < len(self.demo_emails):
                time.sleep(1)
        
        # Conclusion
        print("\n" + "="*70)
        print("[SUCCESS] DEMO COMPLETE!")
        print("="*70)
        print("\n[SUCCESS] Features Demonstrated:")
        print("   • AI email classification and drafting")
        print("   • Voice-controlled editing (hands-free)")
        print("   • Human review workflow")
        print("   • Professional client communications")
        print("   • AWS-ready architecture\n")
    
    def _result_to_draft(self, result: Dict[str, Any], email: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI result to draft format"""
        if 'draft' in result.get('result', {}):
            draft_data = result['result']['draft']
            return {
                "draft": {
                    "subject": draft_data.get('subject', f"Re: {email['name']}"),
                    "content": draft_data.get('content', ''),
                    "tone": draft_data.get('tone', 'professional'),
                    "urgency": draft_data.get('urgency', 'medium'),
                    "last_edited": None,
                    "edited_via": "ai"
                },
                "metadata": {
                    "original_email": email['content'],
                    "client": email['client']
                }
            }
        
        return {
            "draft": {
                "subject": f"Re: {email['name']}",
                "content": str(result),
                "tone": "professional",
                "urgency": "medium",
                "last_edited": None,
                "edited_via": "ai"
            }
        }

def quick_demo():
    """2-minute quick demo for interviews"""
    print("\n" + "="*70)
    print("[VOICE] QUICK VOICE DEMO - 2 Minutes")
    print("="*70)
    print("\n[1] AI Draft: 'Dear Client, thank you for contacting us...'")
    time.sleep(2)
    print("[2] Voice Edit: 'Make it more formal'")
    time.sleep(2)
    print("[3] Result: 'Dear Valued Client, we appreciate your inquiry...'")
    time.sleep(2)
    print("\n[SUCCESS] Voice editing enables hands-free email editing!")
    print("   Perfect for multitasking client service agents.\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_demo()
    else:
        demo = VoiceInteractiveDemo()
        demo.run_demo()

