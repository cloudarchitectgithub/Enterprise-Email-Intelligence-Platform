"""
Utility functions for voice interaction
Supports both Google Speech Recognition (demo) and AWS Transcribe (production)
"""
import os
import logging
from typing import Optional, Tuple

# Try to import speech_recognition for local demo
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️  speech_recognition not installed. Voice features will use fallback mode.")
    print("   Install with: pip install speechrecognition pyaudio")

# Setup logging
logger = logging.getLogger(__name__)

def setup_microphone() -> Tuple[Optional[any], Optional[any]]:
    """
    Initialize microphone for speech recognition
    
    Returns:
        Tuple of (recognizer, microphone) or (None, None) if setup fails
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        logger.warning("SpeechRecognition not available")
        return None, None
    
    try:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Calibrate for ambient noise
        print("[Calibrating] Calibrating microphone for ambient noise...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("[OK] Microphone ready")
        logger.info("Microphone initialized successfully")
        return recognizer, microphone
        
    except OSError as e:
        print(f"[ERROR] Microphone not found: {e}")
        print("   Please check your microphone connection")
        logger.error(f"Microphone setup failed: {e}")
        return None, None
        
    except Exception as e:
        print(f"[ERROR] Microphone setup failed: {e}")
        logger.error(f"Unexpected error in microphone setup: {e}")
        return None, None

def listen_for_speech(recognizer, microphone, timeout: int = 10, phrase_time_limit: int = 15) -> Optional[str]:
    """
    Listen for speech and return transcribed text
    
    Args:
        recognizer: SpeechRecognition Recognizer object
        microphone: SpeechRecognition Microphone object
        timeout: Maximum seconds to wait for speech to start
        phrase_time_limit: Maximum seconds for a phrase
        
    Returns:
        Transcribed text or None if failed
    """
    if not SPEECH_RECOGNITION_AVAILABLE or not recognizer or not microphone:
        # Fallback to text input
        print("[Voice Input] Voice input (type your command):")
        return input("You: ").strip()
    
    try:
        with microphone as source:
            print("[Listening] Listening... (speak now)")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        
        print("[Processing] Processing speech...")
        
        # Try Google Speech Recognition first (free, no API key needed)
        try:
            text = recognizer.recognize_google(audio)
            print(f"[OK] Heard: '{text}'")
            logger.info(f"Speech recognized: {text}")
            return text
        except sr.UnknownValueError:
            print("[ERROR] Could not understand audio")
            logger.warning("Speech not understood")
            return ""
        except sr.RequestError as e:
            print(f"[ERROR] Speech service error: {e}")
            logger.error(f"Speech recognition service error: {e}")
            return None
            
    except sr.WaitTimeoutError:
        print("[Timeout] No speech detected (timeout)")
        logger.info("Speech timeout")
        return None
        
    except Exception as e:
        print(f"[ERROR] Speech recognition error: {e}")
        logger.error(f"Unexpected error in speech recognition: {e}")
        return None

def listen_with_fallback(recognizer=None, microphone=None, prompt: str = "Voice command") -> str:
    """
    Listen for speech with automatic fallback to text input
    
    Args:
        recognizer: Optional recognizer object
        microphone: Optional microphone object
        prompt: Prompt message for user
        
    Returns:
        User input (from voice or keyboard)
    """
    if recognizer and microphone and SPEECH_RECOGNITION_AVAILABLE:
        result = listen_for_speech(recognizer, microphone)
        
        if result is not None and result != "":
            return result
        
        # If speech failed, offer text input
        print(f"\n💬 {prompt} (type your command):")
        return input("You: ").strip()
    else:
        # No voice capability, use text input
        print(f"\n💬 {prompt} (type your command):")
        return input("You: ").strip()

def test_microphone() -> bool:
    """
    Test microphone setup
    
    Returns:
        True if microphone works, False otherwise
    """
    print("\n[Microphone] Testing microphone setup...")
    
    recognizer, microphone = setup_microphone()
    
    if not recognizer or not microphone:
        print("[ERROR] Microphone test failed")
        return False
    
    print("Say something to test your microphone...")
    result = listen_for_speech(recognizer, microphone, timeout=5)
    
    if result:
        print(f"[SUCCESS] Microphone test successful! You said: '{result}'")
        return True
    else:
        print("[ERROR] No speech detected or error occurred")
        return False

# AWS Transcribe integration (for production)
def transcribe_with_aws(audio_file_path: str) -> Optional[str]:
    """
    Transcribe audio using AWS Transcribe (production)
    
    Args:
        audio_file_path: Path to audio file
        
    Returns:
        Transcribed text or None
    """
    try:
        import boto3
        import time
        import uuid
        
        # Initialize AWS clients
        transcribe_client = boto3.client('transcribe', region_name='us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Upload audio to S3 (required by Transcribe)
        bucket_name = os.environ.get('TRANSCRIBE_BUCKET', 'email-assistant-transcribe')
        job_name = f"transcribe-{uuid.uuid4()}"
        s3_key = f"audio/{job_name}.wav"
        
        s3_client.upload_file(audio_file_path, bucket_name, s3_key)
        
        # Start transcription job
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{s3_key}'},
            MediaFormat='wav',
            LanguageCode='en-US'
        )
        
        # Wait for completion
        print("[Processing] AWS Transcribe processing...")
        while True:
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # Download and parse transcript
                import requests
                transcript_response = requests.get(transcript_uri)
                transcript_data = transcript_response.json()
                
                text = transcript_data['results']['transcripts'][0]['transcript']
                print(f"[SUCCESS] AWS Transcribe result: '{text}'")
                return text
                
            elif job_status == 'FAILED':
                print("[ERROR] AWS Transcribe failed")
                return None
                
            time.sleep(2)
            
    except Exception as e:
        logger.error(f"AWS Transcribe error: {e}")
        print(f"[ERROR] AWS Transcribe error: {e}")
        return None

if __name__ == "__main__":
    # Run microphone test
    print("="*60)
    print("Voice Utils Test")
    print("="*60)
    test_microphone()

