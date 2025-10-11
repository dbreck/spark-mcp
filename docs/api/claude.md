# Spark API Documentation Extraction Task

## Objective
Extract complete API documentation from https://api-docs.spark.re to enable WordPress integration for Miramar project registration forms.

## Context
- **Client**: Miramar (WordPress site with Salient theme)
- **Goal**: Integrate Spark CRM registration forms into WordPress 
- **Issue**: API docs are JS-heavy SPA that blocks standard scraping
- **Solution**: Selenium-based scraper to extract all content

## Knowledge Base Already Captured
Located in project directory with complete Spark registration form documentation:
- Registration Forms Overview
- Creating Registration Forms  
- Registration Form Settings
- Developer Guide (critical for integration)
- Recaptcha & Anti-Spam
- Submissions Log

## Current Task
Run `spark_api_scraper.py` to extract:
- API endpoints (especially registration/contact creation)
- Authentication methods
- Request/response formats
- Error handling
- Rate limits

## Script Details
- **Location**: `/Users/dannybreckenridge/Documents/Clear ph/Clients/Mira Mar/Spark/API/`
- **Dependencies**: `pip install selenium beautifulsoup4 webdriver-manager`
- **Output**: `spark_api_complete.json` with structured content
- **Options**: Set `headless=False` to monitor progress

## Next Steps After Extraction
1. Review API endpoints for contact creation
2. Identify authentication requirements
3. Plan WordPress integration approach
4. Create custom form handlers for Salient theme

## Key Integration Points
From developer guide:
- Form action: `https://spark.re/{company}/{project}/register/{form-id}`
- Required field: `contact[email]`
- Special fields: `agent`, `source`, `full_name`
- Built-in spam protection: `are_you_simulated` field
- Redirect handling: `redirect_success`, `redirect_error`

## Support
- Spark support: support@spark.re
- API issues: Contact if authentication/access problems arise