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
    
    # Setup Supabase
    if supabase_url and supabase_key:
        try:
            config.supabase = create_client(supabase_url, supabase_key)
            print("✅ Supabase connected")
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
    else:
        print("⚠️ Supabase credentials not provided")
    
    # Setup Google AI
    if genai_api_key:
        try:
            genai.configure(api_key=genai_api_key)
            config.genai_enabled = True
            print("✅ Google AI configured")
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
