# Frontend Integration Guide - Legal Document Analysis API

## 🎯 Objective
Integrate the Legal Document Analysis API into your React frontend to provide users with legal document analysis capabilities.

## 📦 Complete Integration Example

### Step 1: Create a Custom Hook

Create `frontend/src/hooks/useLegalAnalysis.js`:

```javascript
import { useState, useCallback } from 'react';

export const useLegalAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const analyzeDocument = useCallback(async (fileUri, focusArea = 'general', language = 'english') => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/legal/analyze-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_uri: fileUri,
          focus_area: focusArea,
          language: language,
          analysis_type: 'comprehensive'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Analysis error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const batchAnalyze = useCallback(async (documents) => {
    if (documents.length > 10) {
      throw new Error('Maximum 10 documents allowed per batch');
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/legal/batch-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(documents),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      console.error('Batch analysis error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    result,
    analyzeDocument,
    batchAnalyze,
  };
};
```

### Step 2: Create the Legal Analyzer Component

Create `frontend/src/components/LegalAnalyzer.jsx`:

```jsx
import React, { useState } from 'react';
import { useLegalAnalysis } from '../hooks/useLegalAnalysis';
import './LegalAnalyzer.css';

const FOCUS_AREAS = [
  { value: 'general', label: 'General Analysis', icon: '📋' },
  { value: 'property_transfer', label: 'Property Transfer', icon: '🏠' },
  { value: 'mortgage', label: 'Mortgage Agreement', icon: '💰' },
  { value: 'tenant_rights', label: 'Tenant Rights', icon: '👥' },
  { value: 'rera_compliance', label: 'RERA Compliance', icon: '✅' },
];

const LANGUAGES = [
  { value: 'english', label: 'English' },
  { value: 'hindi', label: 'Hindi' },
  { value: 'mixed', label: 'Mixed (English/Hindi)' },
];

export const LegalAnalyzer = () => {
  const [fileUri, setFileUri] = useState('');
  const [focusArea, setFocusArea] = useState('general');
  const [language, setLanguage] = useState('english');
  const [tab, setTab] = useState('analysis'); // 'analysis' or 'batch'
  
  const { loading, error, result, analyzeDocument, batchAnalyze } = useLegalAnalysis();

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!fileUri.trim()) {
      alert('Please enter a file URI');
      return;
    }
    try {
      await analyzeDocument(fileUri, focusArea, language);
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  return (
    <div className="legal-analyzer-container">
      <header className="analyzer-header">
        <h1>⚖️ Legal Document Analyzer</h1>
        <p>Analyze legal documents with AI-powered legal expertise</p>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${tab === 'analysis' ? 'active' : ''}`}
          onClick={() => setTab('analysis')}
        >
          Single Document
        </button>
        <button 
          className={`tab ${tab === 'batch' ? 'active' : ''}`}
          onClick={() => setTab('batch')}
        >
          Batch Analysis
        </button>
      </div>

      {tab === 'analysis' && (
        <div className="single-analysis">
          <form onSubmit={handleAnalyze} className="analyzer-form">
            <div className="form-group">
              <label htmlFor="fileUri">
                🔗 Google Cloud Storage File Path
              </label>
              <input
                id="fileUri"
                type="text"
                value={fileUri}
                onChange={(e) => setFileUri(e.target.value)}
                placeholder="gs://your-bucket/documents/legal-doc.pdf"
                className="input-field"
                disabled={loading}
              />
              <small>Must be a valid gs:// URL to a PDF file</small>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="focusArea">📌 Focus Area</label>
                <select
                  id="focusArea"
                  value={focusArea}
                  onChange={(e) => setFocusArea(e.target.value)}
                  className="select-field"
                  disabled={loading}
                >
                  {FOCUS_AREAS.map(area => (
                    <option key={area.value} value={area.value}>
                      {area.icon} {area.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="language">🌐 Language</label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="select-field"
                  disabled={loading}
                >
                  {LANGUAGES.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !fileUri.trim()}
            >
              {loading ? '⏳ Analyzing...' : '🔍 Analyze Document'}
            </button>
          </form>

          {error && (
            <div className="error-box">
              <strong>❌ Error:</strong> {error}
            </div>
          )}

          {result && (
            <div className="result-container">
              <div className="result-header">
                <h2>✅ Analysis Complete</h2>
                <span className="badge">{result.model_used}</span>
              </div>

              <div className="result-section">
                <h3>📄 Full Analysis</h3>
                <div className="analysis-text">
                  {result.analysis}
                </div>
              </div>

              <div className="result-row">
                <div className="result-section">
                  <h3>🔑 Key Legal Points</h3>
                  {result.key_points.length > 0 ? (
                    <ul className="points-list">
                      {result.key_points.map((point, idx) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="empty-state">No key points extracted</p>
                  )}
                </div>

                <div className="result-section">
                  <h3>⚠️ Risk Factors</h3>
                  {result.risk_factors.length > 0 ? (
                    <ul className="risks-list">
                      {result.risk_factors.map((risk, idx) => (
                        <li key={idx} className="risk-item">
                          {risk}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="success-state">✅ No major risk factors identified</p>
                  )}
                </div>
              </div>

              <div className="result-section">
                <h3>💡 Recommendations</h3>
                {result.recommendations.length > 0 ? (
                  <ol className="recommendations-list">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="empty-state">No specific recommendations</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'batch' && (
        <BatchAnalyzer onAnalyze={batchAnalyze} loading={loading} />
      )}
    </div>
  );
};

// Batch Analyzer Component
const BatchAnalyzer = ({ onAnalyze, loading }) => {
  const [documents, setDocuments] = useState([{ file_uri: '', focus_area: 'general' }]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAddDocument = () => {
    if (documents.length < 10) {
      setDocuments([...documents, { file_uri: '', focus_area: 'general' }]);
    }
  };

  const handleUpdateDocument = (idx, field, value) => {
    const updated = [...documents];
    updated[idx][field] = value;
    setDocuments(updated);
  };

  const handleRemoveDocument = (idx) => {
    setDocuments(documents.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validDocs = documents.filter(doc => doc.file_uri.trim());
    
    if (validDocs.length === 0) {
      alert('Please add at least one document');
      return;
    }

    try {
      const data = await onAnalyze(validDocs);
      setResult(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="batch-analyzer">
      <form onSubmit={handleSubmit} className="batch-form">
        <div className="documents-list">
          {documents.map((doc, idx) => (
            <div key={idx} className="document-item">
              <input
                type="text"
                value={doc.file_uri}
                onChange={(e) => handleUpdateDocument(idx, 'file_uri', e.target.value)}
                placeholder="gs://bucket/document.pdf"
                className="input-field"
                disabled={loading}
              />
              <select
                value={doc.focus_area}
                onChange={(e) => handleUpdateDocument(idx, 'focus_area', e.target.value)}
                className="select-field small"
                disabled={loading}
              >
                {FOCUS_AREAS.map(area => (
                  <option key={area.value} value={area.value}>
                    {area.label}
                  </option>
                ))}
              </select>
              {documents.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveDocument(idx)}
                  className="btn-remove"
                  disabled={loading}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="batch-actions">
          <button
            type="button"
            onClick={handleAddDocument}
            className="btn-secondary"
            disabled={documents.length >= 10 || loading}
          >
            + Add Document
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || documents.every(d => !d.file_uri.trim())}
          >
            {loading ? '⏳ Analyzing...' : '🔍 Analyze Batch'}
          </button>
        </div>
      </form>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <div className="batch-result">
          <h3>📊 Batch Results</h3>
          <summary className="batch-summary">
            ✅ {result.successful} / {result.total_documents} documents analyzed successfully
          </summary>
          
          {result.results.map((item, idx) => (
            <div key={idx} className="batch-item-result">
              <h4>Document {item.index + 1}</h4>
              <p className="file-uri">{item.file_uri}</p>
              <p className="preview">{item.result.analysis.substring(0, 300)}...</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LegalAnalyzer;
```

### Step 3: Add Styles

Create `frontend/src/components/LegalAnalyzer.css`:

```css
.legal-analyzer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.analyzer-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #4a90e2;
}

.analyzer-header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin: 0 0 10px 0;
}

.analyzer-header p {
  color: #7f8c8d;
  font-size: 1.1em;
  margin: 0;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
}

.tab {
  padding: 10px 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1em;
  color: #7f8c8d;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
}

.tab:hover {
  color: #4a90e2;
}

.tab.active {
  color: #4a90e2;
  border-bottom-color: #4a90e2;
}

.analyzer-form,
.batch-form {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
}

.input-field,
.select-field {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
  transition: border-color 0.3s ease;
}

.input-field:focus,
.select-field:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.input-field:disabled,
.select-field:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #95a5a6;
  font-size: 0.9em;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  font-size: 1em;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
  color: white;
  width: 100%;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #4a90e2;
  border: 1px solid #4a90e2;
}

.btn-secondary:hover:not(:disabled) {
  background: #f0f5ff;
}

.error-box {
  background: #fee;
  border-left: 4px solid #e74c3c;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  color: #c0392b;
}

.result-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #ecf0f1;
}

.result-header h2 {
  margin: 0;
  color: #27ae60;
}

.badge {
  background: #e8f5e9;
  color: #27ae60;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
}

.result-section {
  margin-bottom: 25px;
}

.result-section h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1.2em;
}

.analysis-text {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
  line-height: 1.6;
  color: #34495e;
  max-height: 400px;
  overflow-y: auto;
}

.points-list,
.risks-list,
.recommendations-list {
  padding-left: 20px;
}

.points-list li,
.recommendations-list li {
  margin-bottom: 10px;
  line-height: 1.5;
  color: #34495e;
}

.risk-item {
  color: #e74c3c;
  font-weight: 500;
}

.success-state {
  color: #27ae60;
  font-weight: 500;
}

.empty-state {
  color: #95a5a6;
  font-size: 0.95em;
  font-style: italic;
}

.result-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.documents-list {
  margin-bottom: 15px;
}

.document-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.document-item input {
  flex: 1;
}

.document-item select.small {
  width: 150px;
}

.btn-remove {
  padding: 10px 15px;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.btn-remove:hover {
  background: #c0392b;
}

.batch-actions {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
}

.batch-actions .btn-secondary {
  width: auto;
}

.batch-result {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.batch-summary {
  background: #e8f5e9;
  padding: 10px;
  border-left: 4px solid #27ae60;
  margin: 10px 0;
  color: #27ae60;
  font-weight: 600;
}

.batch-item-result {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
  border-left: 4px solid #4a90e2;
}

.batch-item-result h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.file-uri {
  color: #7f8c8d;
  font-size: 0.9em;
  margin: 5px 0;
  word-break: break-all;
}

.preview {
  color: #34495e;
  margin: 10px 0 0 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .form-row,
  .result-row {
    grid-template-columns: 1fr;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .analyzer-form,
  .batch-form,
  .result-container {
    padding: 15px;
  }

  .analyzer-header h1 {
    font-size: 2em;
  }
}
```

### Step 4: Integrate into Your App

Update `frontend/src/App.jsx`:

```jsx
import { LegalAnalyzer } from './components/LegalAnalyzer';
import './App.css';

function App() {
  return (
    <div className="App">
      <main>
        {/* Your other components */}
        <LegalAnalyzer />
      </main>
    </div>
  );
}

export default App;
```

## 🚀 Usage in Your Application

### For Property Buyers
- Analyze property transfer documents before signing
- Check for legal compliance and risks
- Get recommendations before final purchase

### For Investors
- Review RERA compliance of projects
- Analyze mortgage agreements
- Assess legal risks in investment documents

### For Tenants
- Review rental agreements
- Understand tenant rights
- Identify unfair terms

### For Real Estate Agents
- Quick legal document verification
- Batch analysis of multiple properties
- Client report generation

## 🔗 API Endpoints Used

- `POST /legal/analyze-pdf` - Single document analysis
- `POST /legal/batch-analyze` - Batch processing (max 10 docs)
- `GET /legal/analysis-types` - Get available options

## ⚠️ Important Notes

1. **GCS Access**: Ensure PDFs are stored in Google Cloud Storage and paths start with `gs://`
2. **API Key**: Backend must have `GOOGLE_API_KEY` environment variable set
3. **CORS**: If frontend and backend are on different domains, ensure CORS is properly configured
4. **File Size**: Large PDFs may take longer to analyze
5. **Rate Limiting**: Monitor API quota usage

## 🎨 Customization

### Theme Colors
- Primary: `#4a90e2` (Blue)
- Success: `#27ae60` (Green)  
- Error: `#e74c3c` (Red)
- Text: `#2c3e50` (Dark gray)

Modify the CSS variables to match your application's branding.

### Response Display
Customize how results are displayed by modifying the component JSX to match your design system.

## 📱 Mobile Responsive
The component is fully responsive and works well on:
- Desktop browsers
- Tablets
- Mobile devices

## 🐛 Debugging Tips

1. Check browser console for API errors
2. Verify GCS file exists and is accessible
3. Test with sample PDF from Google's documentation
4. Check backend logs for API processing errors
5. Use provided test script to verify API is working

## ✅ Testing

Test the integration:
```bash
# 1. Verify backend is running
curl http://localhost:8000/legal/

# 2. Get analysis types
curl http://localhost:8000/legal/analysis-types

# 3. Try a single analysis request
curl -X POST http://localhost:8000/legal/analyze-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "file_uri": "gs://your-bucket/sample.pdf",
    "focus_area": "property_transfer"
  }'
```

Done! Your frontend now has a fully functional legal document analysis interface.
