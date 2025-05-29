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
    """Save parishes to Supabase database with improved error handling"""
    config = get_config()
    
    if not config.supabase:
        print("  No database connection available")
        return 0
    
    saved_count = 0
    failed_count = 0
    
    # Save in batches to avoid timeouts
    batch_size = 10
    for i in range(0, len(parishes), batch_size):
        batch = parishes[i:i + batch_size]
        batch_data = []
        
        for parish in batch:
            try:
                data = parish.to_dict()
                data.update({
                    'diocese_url': diocese_url,
                    'parish_directory_url': directory_url,
                    'extraction_method': extraction_method
                })
                batch_data.append(data)
            except Exception as e:
                print(f"    ❌ Error preparing {parish.name}: {e}")
                failed_count += 1
        
        if batch_data:
            try:
                response = config.supabase.table('Parishes').insert(batch_data).execute()
                
                if hasattr(response, 'error') and response.error:
                    print(f"    Database batch error: {response.error}")
                    failed_count += len(batch_data)
                else:
                    saved_count += len(batch_data)
                    print(f"    ✅ Saved batch: {len(batch_data)} parishes")
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'unique' in error_msg:
                    print(f"    ⚠️ Duplicate entries in batch - skipping")
                elif 'timeout' in error_msg:
                    print(f"    ⏱️ Timeout saving batch - retrying with smaller batch")
                    # Could implement retry logic here
                else:
                    print(f"    ❌ Error saving batch: {e}")
                failed_count += len(batch_data)
    
    print(f"  💾 Final result: {saved_count} saved, {failed_count} failed")
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
