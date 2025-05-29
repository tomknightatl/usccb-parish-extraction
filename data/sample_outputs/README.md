# File: data/sample_outputs/README.md

# Sample Outputs

This directory contains sample outputs from the parish extraction system to help users understand the expected data formats.

## Files

- `sample_dioceses.json` - Example dioceses data from USCCB scraping
- `sample_extraction_results.json` - Example parish extraction results
- `sample_parishes.json` - Example parish data with all fields

## Data Structure

### Diocese Data
```json
{
  "Name": "Diocese of Example",
  "Address": "123 Church St, Example City, ST 12345",
  "Website": "https://dioceseofexample.org",
  "extracted_at": "2024-01-15T10:30:00"
}
```

### Parish Data
```json
{
  "Name": "St. Mary Parish",
  "City": "Example City",
  "Street Address": "456 Parish Ave",
  "Phone Number": "(555) 123-4567",
  "Web": "https://stmary.org",
  "latitude": 40.1234,
  "longitude": -80.5678,
  "confidence_score": 0.9,
  "extraction_method": "parish_finder",
  "extracted_at": "2024-01-15T10:35:00"
}
```

### Extraction Results
```json
{
  "diocese_name": "Diocese of Example",
  "diocese_url": "https://dioceseofexample.org",
  "directory_url": "https://dioceseofexample.org/parishes",
  "parish_count": 25,
  "site_type": "parish_finder",
  "success": true,
  "saved_count": 25,
  "processing_time": 45.2,
  "errors": [],
  "parishes": [...]
}
```
