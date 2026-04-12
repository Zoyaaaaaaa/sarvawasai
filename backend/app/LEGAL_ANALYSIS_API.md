# Legal Document Analysis API

## Overview

The Legal Document Analysis API is a FastAPI endpoint that analyzes PDF documents with a specialized focus on **Indian real estate law and regulations**. It uses Google's Gemini 2.5 Flash model to provide expert-level legal analysis.

## Key Features

- 📄 **PDF Analysis**: Analyze legal documents from Google Cloud Storage
- ⚖️ **Legal Expertise**: Specialized in Indian real estate law (RERA, Property Transfer Act, etc.)
- 🎯 **Focused Analysis**: Multiple focus areas (property transfer, mortgage, tenant rights, RERA compliance)
- 🌐 **Multi-language Support**: English, Hindi, and mixed language responses
- 📦 **Batch Processing**: Analyze up to 10 documents in a single request
- 🔍 **Structured Output**: Key points, recommendations, and risk factors extracted

## Prerequisites

1. **Google API Key**
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   ```

2. **Install Dependencies**
   ```bash
   pip install google-genai
   # Or from requirements.txt
   pip install -r backend/app/requirements.txt
   ```

3. **PDF in Google Cloud Storage**
   - Upload your PDF to a GCS bucket
   - Note the GCS URI (e.g., `gs://your-bucket/documents/legal-doc.pdf`)

## API Endpoints

### 1. Analyze Single PDF
```
POST /legal/analyze-pdf
```

**Request Body:**
```json
{
  "file_uri": "gs://your-bucket/legal_document.pdf",
  "analysis_type": "comprehensive",
  "focus_area": "property_transfer",
  "language": "english"
}
```

**Parameters:**
- `file_uri` (string, required): Google Cloud Storage path (must start with `gs://`)
- `analysis_type` (string): `comprehensive` | `summary` | `specific` (default: `comprehensive`)
- `focus_area` (string): Specialization area
  - `general` - All relevant legal aspects
  - `property_transfer` - Title verification, ownership, transfer taxes, registration
  - `mortgage` - Loan terms, default clauses, foreclosure procedures
  - `tenant_rights` - Rent control, lease terms, eviction, security deposits
  - `rera_compliance` - Project registration, disclosure, timeline, buyer protection
- `language` (string): `english` | `hindi` | `mixed` (default: `english`)

**Response:**
```json
{
  "status": "success",
  "analysis": "Comprehensive legal analysis text...",
  "key_points": [
    "Point about property transfer",
    "Point about registration requirements"
  ],
  "recommendations": [
    "Verify title with local registrar",
    "Conduct legal due diligence"
  ],
  "risk_factors": [
    "Potential encumbrance on property"
  ],
  "model_used": "gemini-2.5-flash"
}
```

### 2. Get Analysis Types
```
GET /legal/analysis-types
```

Returns available analysis types, focus areas, and languages.

### 3. Batch Analyze Documents
```
POST /legal/batch-analyze
```

**Request Body:**
```json
[
  {
    "file_uri": "gs://bucket/doc1.pdf",
    "focus_area": "property_transfer"
  },
  {
    "file_uri": "gs://bucket/doc2.pdf",
    "focus_area": "mortgage"
  }
]
```

**Limits:** Maximum 10 documents per batch

### 4. Health Check
```
GET /legal/
```

Check if the legal analysis service is active and available.

### 5. Help & Documentation
```
GET /legal/help
```

Get help documentation and API examples.

## Usage Examples

### Python Example
```python
import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

# Analyze a property transfer agreement
request_data = {
    "file_uri": "gs://your-bucket/property_transfer_agreement.pdf",
    "analysis_type": "comprehensive",
    "focus_area": "property_transfer",
    "language": "english"
}

response = requests.post(
    f"{BASE_URL}/legal/analyze-pdf",
    json=request_data
)

result = response.json()
print("Analysis Status:", result['status'])
print("\nKey Legal Points:")
for point in result['key_points']:
    print(f"  - {point}")
print("\nRecommendations:")
for rec in result['recommendations']:
    print(f"  - {rec}")
```

### cURL Example
```bash
curl -X POST http://localhost:8000/legal/analyze-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "file_uri": "gs://your-bucket/legal_doc.pdf",
    "focus_area": "rera_compliance",
    "language": "english"
  }'
```

### JavaScript/Fetch Example
```javascript
const analyzeDocument = async (fileUri, focusArea) => {
  const response = await fetch('http://localhost:8000/legal/analyze-pdf', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_uri: fileUri,
      analysis_type: 'comprehensive',
      focus_area: focusArea,
      language: 'english'
    })
  });
  
  return await response.json();
};

// Usage
analyzeDocument('gs://bucket/property_lease.pdf', 'tenant_rights')
  .then(result => console.log(result));
```

## Indian Real Estate Regulations Covered

The API provides expertise in:

1. **RERA (Real Estate Regulation and Development Act)**
   - Project registration requirements
   - Disclosure obligations
   - Timeline and completion clauses
   - Buyer protection mechanisms

2. **Property Transfer**
   - Title verification under Registration Act
   - Chain of ownership verification
   - Encumbrances and liabilities
   - Stamp duty and tax implications
   - Registration procedures

3. **Mortgage & Financing**
   - Loan agreement terms
   - Default clauses and penalties
   - Prepayment options
   - Foreclosure procedures under Hindu Succession Act

4. **Tenant Rights**
   - Rent control regulations (vary by state)
   - Lease agreement terms
   - Eviction procedures
   - Security deposit handling
   - Maintenance obligations

5. **Environmental & Municipal**
   - Environmental clearance requirements
   - Municipal compliance
   - Zoning regulations

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "detail": "File URI must be a Google Cloud Storage path (gs://...)"
}
```

**503 Service Unavailable**
```json
{
  "detail": "Legal service unavailable: GOOGLE_API_KEY not set"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Error analyzing document: [error message]"
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend/app
pip install -r requirements.txt
```

### 2. Set Google API Key
```bash
# Linux/Mac
export GOOGLE_API_KEY="your-api-key"

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your-api-key"

# Or add to .env file
echo GOOGLE_API_KEY=your-api-key > .env
```

### 3. Run the Backend
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Test the API
```bash
# Get available analysis types
curl http://localhost:8000/legal/analysis-types

# Test health check
curl http://localhost:8000/legal/

# Analyze a document
curl -X POST http://localhost:8000/legal/analyze-pdf \
  -H "Content-Type: application/json" \
  -d '{"file_uri":"gs://your-bucket/sample.pdf","focus_area":"property_transfer"}'
```

## Model Information

- **Model**: Gemini 2.5 Flash
- **API Version**: v1
- **Expertise**: Indian Real Estate Law
- **Languages**: English, Hindi, Mixed
- **Response**: 300-500 words (summary format)

## Rate Limiting

- **Single Analysis**: No strict limit (depends on PDF size/complexity)
- **Batch Analysis**: Max 10 documents per request
- **API Key**: Subject to Google's API quotas

## Files Modified

- `backend/app/requirements.txt` - Added `google-genai`
- `backend/app/legal_analysis_service.py` - New service file
- `backend/app/routes/legal_routes.py` - New route file
- `backend/app/main.py` - Updated to include legal routes

## Testing

Run the included test script:
```bash
python test_legal_analysis.py
```

## Troubleshooting

### "GOOGLE_API_KEY not set"
- Ensure you've set the environment variable correctly
- Check with: `echo $GOOGLE_API_KEY` (Unix) or `echo $env:GOOGLE_API_KEY` (Windows)

### "File URI must be gs://"
- Use Google Cloud Storage paths only
- Example: `gs://my-bucket/documents/legal.pdf`

### "google-genai not available"
- Install with: `pip install google-genai`

### "Model not responding"
- Check your Google API key has Generative AI API enabled
- Verify GCS file exists and is accessible
- Check file is in supported format (PDF recommended)

## API Response Examples

### Property Transfer Analysis
```json
{
  "status": "success",
  "analysis": "The document is a property transfer deed prepared under the Indian Registration Act... [full analysis]",
  "key_points": [
    "Title is clear with no encumbrances",
    "RERA registration is up-to-date",
    "Stamp duty has been paid"
  ],
  "recommendations": [
    "Conduct final title search before registration",
    "Verify GST implications for this transaction"
  ],
  "risk_factors": [
    "Ensure environmental clearance if applicable"
  ],
  "model_used": "gemini-2.5-flash"
}
```

## Support & Documentation

For more information:
- Google Genai Docs: https://ai.google.dev/
- India Real Estate Regulations: https://rera.gov.in/
- RERA Timeline: https://www.rera.gov.in/guideline.html
