# Legal Analysis API - Quick Setup Guide

## 🚀 Quick Start

### Step 1: Get Your Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### Step 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY = "YOUR-API-KEY-HERE"
# Verify it's set
echo $env:GOOGLE_API_KEY
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_API_KEY=YOUR-API-KEY-HERE
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="YOUR-API-KEY-HERE"
# Verify with
echo $GOOGLE_API_KEY
```

**Or create `.env` file in `backend/app/`:**
```env
GOOGLE_API_KEY=YOUR-API-KEY-HERE
```

### Step 3: Install Dependencies

```bash
cd backend
pip install -r app/requirements.txt
```

Specifically, ensure `google-genai` is installed:
```bash
pip install google-genai
```

### Step 4: Start the Backend

```bash
cd backend/app
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Or use the VS Code task:
```
Ctrl+Shift+B → Select "Run FastAPI server"
```

### Step 5: Test the API

**Option A: Using cURL**
```bash
curl http://localhost:8000/legal/
```

**Option B: Using Python**
```python
import requests

response = requests.get("http://localhost:8000/legal/")
print(response.json())
```

**Option C: Using the browser**
Open: http://localhost:8000/legal/
Then: http://localhost:8000/legal/analysis-types

## 📋 Common Use Cases

### Use Case 1: Analyze a Property Transfer Agreement

```python
import requests

api_url = "http://localhost:8000/legal/analyze-pdf"

# Your GCS path to the property transfer document
request_data = {
    "file_uri": "gs://your-bucket/agreements/property_transfer_2024.pdf",
    "focus_area": "property_transfer",
    "language": "english"
}

response = requests.post(api_url, json=request_data)
result = response.json()

print(f"Status: {result['status']}")
print(f"\nFull Analysis:\n{result['analysis']}")
print(f"\nKey Points: {result['key_points']}")
print(f"Recommendations: {result['recommendations']}")
```

### Use Case 2: Check RERA Compliance

```python
import requests

request_data = {
    "file_uri": "gs://my-bucket/rera/project_brochure.pdf",
    "focus_area": "rera_compliance",
    "analysis_type": "comprehensive",
    "language": "hindi"  # Response in Hindi
}

response = requests.post(
    "http://localhost:8000/legal/analyze-pdf",
    json=request_data
)

if response.status_code == 200:
    result = response.json()
    print("RERA Analysis:")
    print(result['analysis'])
    print("\nCompliance Issues:")
    for risk in result['risk_factors']:
        print(f"  ⚠️ {risk}")
```

### Use Case 3: Analyze Mortgage Agreement

```javascript
// Frontend example - Analyze mortgage agreement
const analyzeMortgage = async (gcsFilePath) => {
  try {
    const response = await fetch('http://localhost:8000/legal/analyze-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_uri: gcsFilePath,
        focus_area: 'mortgage',
        language: 'english'
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      console.log('Mortgage Terms Analysis:', result.analysis);
      console.log('Key Terms:', result.key_points);
      console.log('Risks:', result.risk_factors);
      console.log('What to Do:', result.recommendations);
    } else {
      console.error('Error:', result.detail);
    }
  } catch (error) {
    console.error('API Error:', error);
  }
};

// Usage
analyzeMortgage('gs://my-bucket/loan-agreements/home_loan_2024.pdf');
```

### Use Case 4: Batch Analysis

```python
import requests

documents = [
    {
        "file_uri": "gs://bucket/doc1.pdf",
        "focus_area": "property_transfer"
    },
    {
        "file_uri": "gs://bucket/doc2.pdf",
        "focus_area": "rera_compliance"
    },
    {
        "file_uri": "gs://bucket/doc3.pdf",
        "focus_area": "mortgage"
    }
]

response = requests.post(
    "http://localhost:8000/legal/batch-analyze",
    json=documents
)

result = response.json()
print(f"Analyzed: {result['successful']}/{result['total_documents']}")

for item in result['results']:
    print(f"\nDocument {item['index']}: {item['file_uri']}")
    print(f"Analysis: {item['result']['analysis'][:200]}...")
```

## 🔗 Frontend Integration

### React Component Example

```jsx
// LegalAnalyzer.jsx
import React, { useState } from 'react';

const LegalAnalyzer = () => {
  const [fileUri, setFileUri] = useState('');
  const [focusArea, setFocusArea] = useState('general');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/legal/analyze-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_uri: fileUri,
          focus_area: focusArea,
          language: 'english'
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="legal-analyzer">
      <h2>Legal Document Analyzer</h2>
      
      <div className="form-group">
        <label>GCS File Path (gs://...)</label>
        <input
          type="text"
          value={fileUri}
          onChange={(e) => setFileUri(e.target.value)}
          placeholder="gs://your-bucket/document.pdf"
        />
      </div>

      <div className="form-group">
        <label>Focus Area</label>
        <select value={focusArea} onChange={(e) => setFocusArea(e.target.value)}>
          <option value="general">General</option>
          <option value="property_transfer">Property Transfer</option>
          <option value="mortgage">Mortgage</option>
          <option value="tenant_rights">Tenant Rights</option>
          <option value="rera_compliance">RERA Compliance</option>
        </select>
      </div>

      <button onClick={handleAnalyze} disabled={loading || !fileUri}>
        {loading ? 'Analyzing...' : 'Analyze Document'}
      </button>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="result">
          <h3>Analysis Result</h3>
          <p><strong>Status:</strong> {result.status}</p>
          
          <h4>Analysis</h4>
          <p>{result.analysis}</p>

          <h4>Key Points</h4>
          <ul>
            {result.key_points.map((point, i) => (
              <li key={i}>{point}</li>
            ))}
          </ul>

          <h4>Recommendations</h4>
          <ul>
            {result.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>

          <h4>Risk Factors</h4>
          <ul>
            {result.risk_factors.map((risk, i) => (
              <li key={i}>{risk}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default LegalAnalyzer;
```

## 🧪 Run Tests

```bash
# From backend directory
python test_legal_analysis.py
```

## 📚 API Documentation

Full documentation available at: `backend/app/LEGAL_ANALYSIS_API.md`

Or access via endpoint:
```
GET http://localhost:8000/legal/help
```

## ✅ Verification Checklist

- [ ] Google API Key set in environment
- [ ] `google-genai` installed (`pip list | grep google-genai`)
- [ ] Backend running on port 8000
- [ ] Can access `http://localhost:8000/legal/` (shows health status)
- [ ] Can get analysis types at `http://localhost:8000/legal/analysis-types`
- [ ] Have valid GCS PDF file path (starts with `gs://`)
- [ ] Can successfully analyze a document

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "GOOGLE_API_KEY not set" | Set env variable: `$env:GOOGLE_API_KEY="..."`  |
| "google-genai not available" | Run: `pip install google-genai` |
| "Service unavailable" | Check backend is running on port 8000 |
| "File URI must be gs://" | Use Google Cloud Storage URIs only |
| Timeout errors | Large PDFs may take longer; increase timeout |
| 503 error | Check Google API quotas and billing |

## 📞 Support

- Refer: `backend/app/LEGAL_ANALYSIS_API.md`
- Test script: `backend/test_legal_analysis.py`
- Check logs: Backend console output
