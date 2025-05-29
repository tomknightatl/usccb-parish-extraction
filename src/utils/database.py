# File: src/utils/database.py

"""Database utilities for Supabase integration"""

from typing import List, Optional
from datetime import datetime

from config.settings import get_config
from ..models import Parish, ExtractionResult

def save_parishes_to_database(
    parishes: List[Parish], 
    diocese_url: str, 
    directory_url: str,
    extraction_method: str
) -> int:
    """Save parishes to Supabase database"""
    config = get_config()
    
    if not config.supabase:
        print("  No database connection available")
        return 0
    
    saved_count = 0
    
    for parish in parishes:
        try:
            # Prepare data for database
            data = parish.to_dict()
            data.update({
                'diocese_url': diocese_url,
                'parish_directory_url': directory_url,
                'extraction_method': extraction_method
            })
            
            # Insert into database
            response = config.supabase.table('Parishes').insert(data).execute()
            
            # Check for errors
            if hasattr(response, 'error') and response.error:
                print(f"    Database error for {parish.name}: {response.error}")
            else:
                saved_count += 1
                print(f"    ✅ Saved: {parish.name}")
            
        except Exception as e:
            print(f"    ❌ Error saving {parish.name}: {e}")
    
    print(f"  💾 Saved {saved_count}/{len(parishes)} parishes to database")
    return saved_count

def update_directory_status(
    diocese_url: str, 
    directory_url: Optional[str], 
    success: bool, 
    method: str = "ai_analysis"
):
    """Update the DiocesesParishDirectory table with extraction results"""
    config = get_config()
    
    if not config.supabase:
        return
    
    try:
        data = {
            'diocese_url': diocese_url,
            'parish_directory_url': directory_url,
            'found': 'Success' if success and directory_url else 'Not Found',
            'found_method': method,
            'updated_at': datetime.now().isoformat()
        }
        
        config.supabase.table('DiocesesParishDirectory').upsert(data).execute()
        print(f"  📊 Updated directory status for {diocese_url}")
        
    except Exception as e:
        print(f"  Error updating directory status: {e}")

def get_dioceses_to_process(limit: Optional[int] = None) -> List[dict]:
    """Get dioceses that need processing from database"""
    config = get_config()
    
    if not config.supabase:
        print("❌ No database connection")
        return []
    
    try:
        # Get dioceses without successful extractions
        query = config.supabase.table('Dioceses').select('Website, Name')
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
        
    except Exception as e:
        print(f"❌ Error fetching dioceses: {e}")
        return []

def check_existing_parishes(directory_url: str) -> int:
    """Check how many parishes already exist for a directory URL"""
    config = get_config()
    
    if not config.supabase:
        return 0
    
    try:
        response = config.supabase.table('Parishes').select(
            'id', count='exact'
        ).eq('parish_directory_url', directory_url).execute()
        
        return response.count or 0
        
    except Exception as e:
        print(f"Error checking existing parishes: {e}")
        return 0
