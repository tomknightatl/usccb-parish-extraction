# File: src/pipeline.py

"""Main pipeline for parish extraction process"""

import time
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from config.settings import Config
from .models import Diocese, ExtractionResult, SiteType
from .utils.webdriver import setup_driver, load_page
from .utils.ai_analysis import analyze_with_ai, detect_site_type
from .utils.database import (
    save_parishes_to_database, 
    update_directory_status, 
    get_dioceses_to_process
)
from .extractors import get_extractor

class ParishExtractionPipeline:
    """Main pipeline for extracting parish data from diocese websites"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def run_full_extraction(self) -> List[ExtractionResult]:
        """Run the complete parish extraction pipeline"""
        print(f"🚀 Starting USCCB Parish Extraction Pipeline")
        print(f"📊 Processing up to {self.config.max_dioceses} dioceses")
        
        # Get dioceses to process
        dioceses_data = get_dioceses_to_process(self.config.max_dioceses)
        if not dioceses_data:
            print("❌ No dioceses found to process")
            return []
        
        dioceses = [Diocese.from_dict(d) for d in dioceses_data]
        print(f"📋 Found {len(dioceses)} dioceses to process")
        
        results = []
        
        for i, diocese in enumerate(dioceses, 1):
            print(f"\n🏛️ {i}/{len(dioceses)}: {diocese.name}")
            
            result = self.process_single_diocese(diocese)
            results.append(result)
            
            # Respectful delay between requests
            if i < len(dioceses):
                print(f"   ⏱️ Waiting {self.config.request_delay} seconds...")
                time.sleep(self.config.request_delay)
        
        self.print_summary(results)
        return results
    
    def process_single_diocese(self, diocese: Diocese) -> ExtractionResult:
        """Process a single diocese through the complete pipeline"""
        start_time = time.time()
        
        try:
            # Step 1: Find parish directory
            directory_url = self.find_parish_directory(diocese)
            
            if not directory_url:
                update_directory_status(diocese.url, None, False)
                return ExtractionResult(
                    diocese_name=diocese.name,
                    diocese_url=diocese.url,
                    success=False,
                    errors=["No parish directory found"],
                    processing_time=time.time() - start_time
                )
            
            # Step 2: Extract parishes
            result = self.extract_parishes_from_directory(diocese, directory_url)
            result.processing_time = time.time() - start_time
            
            # Step 3: Save to database
            if result.success:
                saved_count = save_parishes_to_database(
                    result.parishes, 
                    diocese.url, 
                    directory_url,
                    result.site_type.value
                )
                result.saved_count = saved_count
                update_directory_status(diocese.url, directory_url, True)
            else:
                update_directory_status(diocese.url, directory_url, False, "extraction_failed")
            
            return result
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            return ExtractionResult(
                diocese_name=diocese.name,
                diocese_url=diocese.url,
                success=False,
                errors=[error_msg],
                processing_time=time.time() - start_time
            )
    
    def find_parish_directory(self, diocese: Diocese) -> Optional[str]:
        """Find parish directory URL for a diocese"""
        print(f"   🔍 Finding parish directory...")
        
        driver = setup_driver()
        try:
            soup = load_page(driver, diocese.url)
            
            # Find potential directory links
            candidates = self._find_directory_candidates(soup, diocese.url)
            
            if not candidates:
                print(f"   ❌ No potential directory links found")
                return None
            
            print(f"   📋 Evaluating {len(candidates)} potential links...")
            
            # Use AI to evaluate candidates
            best_url = self._evaluate_candidates_with_ai(candidates)
            
            if best_url:
                print(f"   ✅ Selected: {best_url}")
            else:
                print(f"   ❌ No suitable directory found")
            
            return best_url
            
        finally:
            driver.quit()
    
    def extract_parishes_from_directory(self, diocese: Diocese, directory_url: str) -> ExtractionResult:
        """Extract parishes from a directory page"""
        print(f"   📥 Extracting parishes from: {directory_url}")
        
        driver = setup_driver()
        try:
            soup = load_page(driver, directory_url)
            
            # Detect site type
            site_type = detect_site_type(soup, directory_url)
            print(f"   🔍 Detected site type: {site_type.value}")
            
            # Get appropriate extractor and extract parishes
            extractor = get_extractor(site_type.value)
            parishes = extractor.extract(soup, directory_url, driver)
            
            print(f"   ✅ Extracted {len(parishes)} parishes")
            
            return ExtractionResult(
                diocese_name=diocese.name,
                diocese_url=diocese.url,
                directory_url=directory_url,
                parishes=parishes,
                site_type=site_type,
                success=len(parishes) > 0
            )
            
        except Exception as e:
            error_msg = f"Extraction error: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            return ExtractionResult(
                diocese_name=diocese.name,
                diocese_url=diocese.url,
                directory_url=directory_url,
                site_type=SiteType.GENERIC,
                success=False,
                errors=[error_msg]
            )
        finally:
            driver.quit()
    
    def _find_directory_candidates(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Find potential parish directory links on page"""
        candidates = []
        links = soup.find_all('a', href=True)
        
        # Keywords that suggest parish directories
        parish_keywords = [
            'parish', 'church', 'directory', 'finder', 'location', 
            'worship', 'mass', 'congregation', 'faith community'
        ]
        
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            
            # Skip unwanted links
            if (not href or href.startswith('#') or href.startswith('mailto:') or 
                len(text) < 3):
                continue
            
            # Check if text suggests parish directory
            if any(keyword in text.lower() for keyword in parish_keywords):
                # Convert to absolute URL
                if href.startswith('/'):
                    full_url = f"{base_url.rstrip('/')}{href}"
                elif not href.startswith('http'):
                    full_url = f"{base_url.rstrip('/')}/{href}"
                else:
                    full_url = href
                
                candidates.append({
                    'url': full_url,
                    'text': text,
                    'context': text  # Could add surrounding text
                })
        
        return candidates
    
    def _evaluate_candidates_with_ai(self, candidates: List[Dict[str, str]]) -> Optional[str]:
        """Use AI to evaluate directory candidates"""
        best_url = None
        best_score = 0
        
        for candidate in candidates[:5]:  # Limit API calls
            try:
                link_info = f"Text: '{candidate['text']}' URL: {candidate['url']}"
                analysis = analyze_with_ai(link_info, "parish_directory")
                score = analysis.get('score', 0)
                
                print(f"      '{candidate['text']}' -> Score: {score}")
                
                if score > best_score and score >= self.config.ai_confidence_threshold:
                    best_score = score
                    best_url = candidate['url']
                    
            except Exception as e:
                print(f"      Error analyzing candidate: {e}")
                continue
        
        return best_url
    
    def print_summary(self, results: List[ExtractionResult]):
        """Print summary of extraction results"""
        total_parishes = sum(len(r.parishes) for r in results)
        successful = sum(1 for r in results if r.success)
        total_saved = sum(r.saved_count for r in results)
        
        print(f"\n{'='*60}")
        print(f"📊 EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"Dioceses processed: {len(results)}")
        print(f"Successful extractions: {successful}")
        print(f"Success rate: {successful/len(results)*100:.1f}%")
        print(f"Total parishes found: {total_parishes}")
        print(f"Total parishes saved: {total_saved}")
        
        if successful > 0:
            print(f"Average parishes per diocese: {total_parishes/successful:.1f}")
        
        # Show individual results
        print(f"\n📋 Individual Results:")
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.diocese_name}: {len(result.parishes)} parishes")
            if result.errors:
                for error in result.errors:
                    print(f"      Error: {error}")
    
    def save_results_to_file(self, results: List[ExtractionResult], filename: str = None):
        """Save detailed results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"parish_extraction_results_{timestamp}.json"
        
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            serializable_results.append({
                'diocese_name': result.diocese_name,
                'diocese_url': result.diocese_url,
                'directory_url': result.directory_url,
                'parish_count': result.parish_count,
                'site_type': result.site_type.value,
                'success': result.success,
                'saved_count': result.saved_count,
                'processing_time': result.processing_time,
                'errors': result.errors,
                'parishes': [
                    {
                        'name': p.name,
                        'city': p.city,
                        'address': p.address,
                        'phone': p.phone,
                        'website': p.website,
                        'confidence': p.confidence
                    }
                    for p in result.parishes
                ]
            })
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")
