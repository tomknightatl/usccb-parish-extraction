# File: config/settings.py

"""Configuration management for the USCCB Parish Extraction System"""

import os
from dataclasses import dataclass
from typing import Optional
import google.generativeai as genai
from supabase import create_client, Client

@dataclass
class Config:
    """Application configuration"""
    supabase: Optional[Client] = None
    genai_enabled: bool = False
    max_dioceses: int = 5
    request_delay: float = 2.0
    ai_confidence_threshold: int = 7
    webdriver_timeout: int = 30

def setup_environment(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    genai_api_key: Optional[str] = None,
    max_dioceses: int = 5
) -> Config:
    """Setup application environment with provided credentials"""
    
    config = Config(max_dioceses=max_dioceses)
    
    # Validation
    if max_dioceses <= 0:
        raise ValueError("max_dioceses must be positive")
    
    # Setup Supabase with validation
    if supabase_url and supabase_key:
        if not supabase_url.startswith('https://'):
            raise ValueError("Invalid Supabase URL format")
        if len(supabase_key) < 20:  # Basic validation
            raise ValueError("Supabase key appears to be invalid")
            
        try:
            config.supabase = create_client(supabase_url, supabase_key)
            # Test connection
            config.supabase.table('Dioceses').select('Name').limit(1).execute()
            print("✅ Supabase connected and tested")
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            raise
    else:
        print("⚠️ Supabase credentials not provided")
    
    # Setup Google AI with validation
    if genai_api_key:
        if not genai_api_key.startswith('AI'):  # Google AI keys start with AI
            print("⚠️ Google AI key format may be incorrect")
            
        try:
            genai.configure(api_key=genai_api_key)
            # Test API call
            model = genai.GenerativeModel('gemini-1.5-flash')
            model.generate_content("Test")
            config.genai_enabled = True
            print("✅ Google AI configured and tested")
        except Exception as e:
            print(f"❌ Google AI setup failed: {e}")
    else:
        print("⚠️ Google AI API key not provided - will use mock responses")
    
    return config

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        raise RuntimeError("Configuration not initialized. Run setup_environment() first.")
    return _config

def set_config(config: Config):
    """Set the global configuration instance"""
    global _config
    _config = config
