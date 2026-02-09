import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [question, setQuestion] = useState('');
  const [scenario, setScenario] = useState('');
  const [templateType, setTemplateType] = useState('own_funds_cr1');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('template');

  // Download report as JSON
  const handleDownload = () => {
    if (!result) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "corep_report.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/api/query`, {
        question,
        scenario: scenario || null,
        template_type: templateType
      });

      setResult(response.data);
      setActiveTab('template');
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while processing your query');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    {
      question: "What items should be included in Common Equity Tier 1 capital?",
      scenario: "A UK bank preparing its quarterly COREP submission",
      template: "own_funds_cr1"
    },
    {
      question: "How do I calculate regulatory adjustments to CET1?",
      scenario: "Institution has intangible assets of £50m and deferred tax assets of £30m",
      template: "own_funds_cr1"
    },
    {
      question: "What are the minimum capital requirements for credit risk?",
      scenario: "Bank using standardised approach for credit risk",
      template: "capital_requirements_cr2"
    }
  ];

  const loadExample = (example) => {
    setQuestion(example.question);
    setScenario(example.scenario);
    setTemplateType(example.template);
  };

  return (
    <div className="App">
      <header className="header">
        <div className="container">
          <h1>🏦 PRA COREP Reporting Assistant</h1>
          <p className="subtitle">LLM-assisted regulatory reporting for UK banks</p>
        </div>
      </header>

      <main className="container">
        <div className="layout">
          {/* Left Panel - Query Form */}
          <div className="query-panel">
            <div className="card">
              <h2>Query Regulatory Guidance</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="question">
                    Question <span className="required">*</span>
                  </label>
                  <textarea
                    id="question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., What items should be included in Common Equity Tier 1 capital?"
                    required
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="scenario">
                    Reporting Scenario <span className="optional">(optional)</span>
                  </label>
                  <textarea
                    id="scenario"
                    value={scenario}
                    onChange={(e) => setScenario(e.target.value)}
                    placeholder="Describe your specific reporting scenario..."
                    rows={2}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="template">Template Type</label>
                  <select
                    id="template"
                    value={templateType}
                    onChange={(e) => setTemplateType(e.target.value)}
                  >
                    <option value="own_funds_cr1">CR1 - Own Funds</option>
                    <option value="capital_requirements_cr2">CR2 - Capital Requirements</option>
                  </select>
                </div>

                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={loading || !question}
                >
                  {loading ? 'Processing...' : 'Generate Report'}
                </button>
              </form>

              <div className="examples">
                <h3>Example Queries</h3>
                {exampleQueries.map((example, idx) => (
                  <div 
                    key={idx}
                    className="example-card"
                    onClick={() => loadExample(example)}
                  >
                    <div className="example-question">{example.question}</div>
                    <div className="example-scenario">{example.scenario}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Panel - Results */}
          <div className="results-panel">
            {error && (
              <div className="card error-card">
                <h3>❌ Error</h3>
                <p>{error}</p>
              </div>
            )}

            {loading && (
              <div className="card loading-card">
                <div className="spinner"></div>
                <p>Processing your query...</p>
                <p className="loading-subtext">Retrieving regulatory documents and generating structured output</p>
              </div>
            )}

            {result && (
              <div className="card results-card">
                <div className="results-header">
                  <h2>📊 Results</h2>
                  <div className="meta-info">
                    <span>⏱️ {result.processing_time_seconds.toFixed(2)}s</span>
                    <span>🤖 {result.llm_model}</span>
                  </div>
                </div>

                {/* Download Button */}
                <button 
                  className="btn btn-secondary"
                  onClick={handleDownload}
                  style={{ marginBottom: '1rem' }}
                >
                  Download Report (JSON)
                </button>

                {/* Tabs */}
                <div className="tabs">
                  <button 
                    className={`tab ${activeTab === 'template' ? 'active' : ''}`}
                    onClick={() => setActiveTab('template')}
                  >
                    Template Output
                  </button>
                  <button 
                    className={`tab ${activeTab === 'references' ? 'active' : ''}`}
                    onClick={() => setActiveTab('references')}
                  >
                    Regulatory References
                  </button>
                  <button 
                    className={`tab ${activeTab === 'validation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('validation')}
                  >
                    Validation ({result.template_output.validation_issues.length})
                  </button>
                  <button 
                    className={`tab ${activeTab === 'audit' ? 'active' : ''}`}
                    onClick={() => setActiveTab('audit')}
                  >
                    Audit Log
                  </button>
                </div>

                {/* Tab Content */}
                <div className="tab-content">
                  {activeTab === 'template' && (
                    <TemplateOutputView data={result.template_output} />
                  )}
                  {activeTab === 'references' && (
                    <ReferencesView references={result.regulatory_references} />
                  )}
                  {activeTab === 'validation' && (
                    <ValidationView 
                      issues={result.template_output.validation_issues}
                      summary={result.template_output.metadata.validation_summary}
                    />
                  )}
                  {activeTab === 'audit' && (
                    <AuditLogView log={result.template_output.audit_log} />
                  )}
                </div>
              </div>
            )}

            {!result && !loading && !error && (
              <div className="card placeholder-card">
                <h3>👈 Start by entering a query</h3>
                <p>Ask a question about regulatory requirements, and we'll retrieve relevant guidance and generate structured output for your COREP template.</p>
                <div className="features">
                  <div className="feature">
                    <span className="icon">📚</span>
                    <div>
                      <strong>Regulatory Retrieval</strong>
                      <p>Searches PRA Rulebook and COREP instructions</p>
                    </div>
                  </div>
                  <div className="feature">
                    <span className="icon">🤖</span>
                    <div>
                      <strong>LLM Generation</strong>
                      <p>Generates structured output with justifications</p>
                    </div>
                  </div>
                  <div className="feature">
                    <span className="icon">✅</span>
                    <div>
                      <strong>Validation</strong>
                      <p>Checks data consistency and business rules</p>
                    </div>
                  </div>
                  <div className="feature">
                    <span className="icon">📝</span>
                    <div>
                      <strong>Audit Trail</strong>
                      <p>Logs all regulatory references used</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// Template Output Component
function TemplateOutputView({ data }) {
  const { fields, metadata } = data;

  return (
    <div className="template-output">
      {metadata.summary && (
        <div className="summary-box">
          <h4>Summary</h4>
          <p>{metadata.summary}</p>
        </div>
      )}

      <div className="fields-table">
        <table>
          <thead>
            <tr>
              <th>Field ID</th>
              <th>Field Name</th>
              <th>Value</th>
              <th>Confidence</th>
              <th>Justification</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field, idx) => (
              <tr key={idx}>
                <td className="field-id">{field.field_id}</td>
                <td>{field.field_name}</td>
                <td className="field-value">
                  {field.value !== null ? field.value : <span className="na">N/A</span>}
                </td>
                <td>
                  <ConfidenceBadge score={field.confidence_score} />
                </td>
                <td className="justification">{field.justification}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {metadata.key_considerations && metadata.key_considerations.length > 0 && (
        <div className="considerations-box">
          <h4>Key Considerations</h4>
          <ul>
            {metadata.key_considerations.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// References Component
function ReferencesView({ references }) {
  return (
    <div className="references">
      {references.map((ref, idx) => (
        <div key={idx} className="reference-card">
          <div className="reference-header">
            <span className="document-name">{ref.document}</span>
            <span className="relevance-badge">
              {(ref.relevance_score * 100).toFixed(0)}% relevant
            </span>
          </div>
          <div className="section-name">{ref.section}</div>
          <div className="content">{ref.content}</div>
        </div>
      ))}
    </div>
  );
}

// Validation Component
function ValidationView({ issues, summary }) {
  const errorIssues = issues.filter(i => i.severity === 'error');
  const warningIssues = issues.filter(i => i.severity === 'warning');
  const infoIssues = issues.filter(i => i.severity === 'info');

  return (
    <div className="validation">
      <div className="validation-summary">
        <div className={`status-badge ${summary.is_valid ? 'valid' : 'invalid'}`}>
          {summary.is_valid ? '✅ Valid' : '❌ Invalid'}
        </div>
        <div className="counts">
          <span className="error-count">{summary.errors} errors</span>
          <span className="warning-count">{summary.warnings} warnings</span>
          <span className="info-count">{summary.info} info</span>
        </div>
      </div>

      {errorIssues.length > 0 && (
        <div className="issue-section">
          <h4>🚫 Errors</h4>
          {errorIssues.map((issue, idx) => (
            <IssueCard key={idx} issue={issue} />
          ))}
        </div>
      )}

      {warningIssues.length > 0 && (
        <div className="issue-section">
          <h4>⚠️ Warnings</h4>
          {warningIssues.map((issue, idx) => (
            <IssueCard key={idx} issue={issue} />
          ))}
        </div>
      )}

      {infoIssues.length > 0 && (
        <div className="issue-section">
          <h4>ℹ️ Information</h4>
          {infoIssues.map((issue, idx) => (
            <IssueCard key={idx} issue={issue} />
          ))}
        </div>
      )}

      {issues.length === 0 && (
        <div className="no-issues">
          <p>✅ No validation issues found</p>
        </div>
      )}
    </div>
  );
}

// Audit Log Component
function AuditLogView({ log }) {
  return (
    <div className="audit-log">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Field ID</th>
            <th>Regulatory Reference</th>
            <th>Justification</th>
          </tr>
        </thead>
        <tbody>
          {log.map((entry, idx) => (
            <tr key={idx}>
              <td>{new Date(entry.timestamp).toLocaleString()}</td>
              <td className="field-id">{entry.field_id}</td>
              <td className="reference">{entry.regulatory_reference}</td>
              <td className="justification">{entry.justification}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Helper Components
function ConfidenceBadge({ score }) {
  let className = 'confidence-badge ';
  if (score >= 0.8) className += 'high';
  else if (score >= 0.5) className += 'medium';
  else className += 'low';

  return (
    <span className={className}>
      {(score * 100).toFixed(0)}%
    </span>
  );
}

function IssueCard({ issue }) {
  return (
    <div className={`issue-card ${issue.severity}`}>
      <div className="issue-header">
        {issue.field_id && <span className="field-id">{issue.field_id}</span>}
        <span className="rule">{issue.rule}</span>
      </div>
      <div className="issue-message">{issue.message}</div>
    </div>
  );
}

export default App;
