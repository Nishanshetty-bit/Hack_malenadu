import { useState, useEffect, useCallback, useRef } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts'
import './App.css'

const API = 'http://localhost:8000'

// ─── Toast Notification System ────────────────────────────────
function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`} onClick={() => onDismiss(t.id)}>
          <span>{t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : 'ℹ️'}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Quality Score Gauge ──────────────────────────────────────
function QualityGauge({ score }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#f43f5e';

  return (
    <div className="score-gauge">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <circle cx="70" cy="70" r={radius} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="score-gauge-label">
        <div className="score-gauge-value" style={{ color }}>{score}%</div>
        <div className="score-gauge-text">Quality</div>
      </div>
    </div>
  )
}

// ─── Language Bar Chart ───────────────────────────────────────
const LANG_NAMES = {
  en: 'English', hi: 'Hindi', kn: 'Kannada', ta: 'Tamil', te: 'Telugu',
  es: 'Spanish', fr: 'French', de: 'German', zh: 'Chinese', ja: 'Japanese',
  ko: 'Korean', ar: 'Arabic', ru: 'Russian', pt: 'Portuguese', it: 'Italian',
  mr: 'Marathi', bn: 'Bengali', unknown: 'Unknown'
}

function getLanguageName(code) {
  if (code.toLowerCase() === 'unknown') return 'Unknown';
  try {
    const name = new Intl.DisplayNames(['en'], { type: 'language' }).of(code);
    return name ? name.charAt(0).toUpperCase() + name.slice(1) : code;
  } catch (e) {
    return LANG_NAMES[code] || code.toUpperCase();
  }
}

function LanguageChart({ data }) {
  if (!data || Object.keys(data).length === 0) return <div className="empty-state"><p>No language data</p></div>
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 8)

  return (
    <div className="lang-bar-chart">
      {sorted.map(([lang, count]) => (
        <div key={lang} className="lang-bar-row">
          <span className="lang-bar-label">{getLanguageName(lang)}</span>
          <div className="lang-bar-track">
            <div className={`lang-bar-fill ${lang}`}
              style={{ width: `${Math.max((count / total) * 100, 8)}%` }}>
              {count}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Product Health Radar Map ───────────────────────────────
function ProductHealthRadar({ trends }) {
  if (!trends || Object.keys(trends).length === 0) return <div className="empty-state">No trend data</div>
  
  const data = Object.entries(trends).map(([feat, stats]) => {
    const recentTotal = stats.recent_positive_pct + stats.recent_negative_pct;
    const histTotal = stats.hist_positive_pct + stats.hist_negative_pct;
    
    const recentScore = recentTotal > 0 ? (stats.recent_positive_pct / recentTotal) * 100 : 50;
    const histScore = histTotal > 0 ? (stats.hist_positive_pct / histTotal) * 100 : 50;
      
    return {
      feature: feat.charAt(0).toUpperCase() + feat.slice(1).replace('_', ' '),
      historical: Math.round(histScore),
      recent: Math.round(recentScore),
      fullMark: 100
    };
  }).slice(0, 7);

  return (
    <div style={{ width: '100%', height: 350, marginTop: '20px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis dataKey="feature" tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--text-tertiary)', fontSize: 10 }} />
          <Radar name="Historical" dataKey="historical" stroke="var(--accent-indigo)" fill="var(--accent-indigo)" fillOpacity={0.2} />
          <Radar name="Recent" dataKey="recent" stroke="var(--accent-rose)" fill="var(--accent-rose)" fillOpacity={0.4} />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-medium)', borderRadius: '8px' }}
            itemStyle={{ fontSize: '12px' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─── Fake Score Visual ────────────────────────────────────────
function FakeScore({ score }) {
  const level = score >= 0.55 ? 'high' : score >= 0.3 ? 'medium' : 'low'
  return (
    <span>
      <span className="fake-score-bar">
        <span className={`fake-score-fill ${level}`} style={{ width: `${score * 100}%` }} />
      </span>
      <span style={{ fontSize: '12px', color: level === 'high' ? '#fb7185' : level === 'medium' ? '#fbbf24' : '#34d399' }}>
        {(score * 100).toFixed(0)}%
      </span>
    </span>
  )
}

// ─── Pipeline Visualization ───────────────────────────────────
function PipelineViz({ step, totalSteps }) {
  const steps = [
    { icon: '🧹', label: 'Clean & Normalize' },
    { icon: '🌐', label: 'Detect Language' },
    { icon: '🔄', label: 'Translate' },
    { icon: '🔍', label: 'Deduplicate' },
    { icon: '🤖', label: 'Detect Bots' },
    { icon: '🎯', label: 'Detect Sentiment' },
    { icon: '💾', label: 'Store Results' },
  ]

  return (
    <div>
      <div className="pipeline-container">
        {steps.map((s, i) => (
          <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className={`pipeline-step ${i < step ? 'done' : i === step ? 'active' : ''}`}>
              <span className="pipeline-step-icon">{i < step ? '✅' : s.icon}</span>
              <span className="pipeline-step-label">{s.label}</span>
            </div>
            {i < steps.length - 1 && <span className="pipeline-arrow">→</span>}
          </span>
        ))}
      </div>
      <div className="progress-bar" style={{ marginTop: '20px' }}>
        <div className="progress-fill" style={{ width: `${(step / totalSteps) * 100}%` }} />
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  MAIN APP COMPONENT
// ═══════════════════════════════════════════════════════════════
function App() {
  const [activeTab, setActiveTab] = useState('pulse')
  const [toasts, setToasts] = useState([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [reviews, setReviews] = useState([])
  const [clusters, setClusters] = useState([])
  const [featureInsights, setFeatureInsights] = useState([])
  const [ambiguousReviews, setAmbiguousReviews] = useState([])
  const [pipelineStep, setPipelineStep] = useState(-1)
  const [lastResult, setLastResult] = useState(null)
  const [filter, setFilter] = useState('all')
  const [pasteText, setPasteText] = useState('')
  const [dragOver, setDragOver] = useState(false)
  
  // Drill-down Filters
  const [explorerFeatureFilter, setExplorerFeatureFilter] = useState(null)
  const [explorerSentimentFilter, setExplorerSentimentFilter] = useState(null)
  
  // Date Filters
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // Trends
  const [trendCategory, setTrendCategory] = useState('Smartwatch')
  const [trendsData, setTrendsData] = useState(null)

  const fileInputRef = useRef(null)

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      let url = `${API}/stats`
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (params.toString()) url += `?${params.toString()}`
      const res = await fetch(url)
      if (res.ok) setStats(await res.json())
    } catch (e) {}
  }, [startDate, endDate])

  const fetchTrends = useCallback(async () => {
    try {
      const res = await fetch(`${API}/trends?category=${trendCategory}`)
      if (res.ok) setTrendsData(await res.json())
    } catch (e) {}
  }, [trendCategory])

  const fetchReviews = useCallback(async () => {
    try {
      let url = `${API}/reviews?limit=200`
      if (filter === 'suspicious') url += '&suspicious=true'
      else if (filter === 'duplicate') url += '&duplicate=true'
      else if (filter === 'clean') url += '&suspicious=false&duplicate=false'
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setReviews(data.reviews || [])
      }
    } catch (e) {}
  }, [filter])

  const fetchClusters = useCallback(async () => {
    try {
      const res = await fetch(`${API}/clusters`)
      if (res.ok) {
        const data = await res.json()
        setClusters(data.clusters || [])
      }
    } catch (e) {}
  }, [])

  const fetchFeatureInsights = useCallback(async () => {
    try {
      const res = await fetch(`${API}/feature-insights`)
      if (res.ok) {
        const data = await res.json()
        setFeatureInsights(data.features || [])
      }
    } catch (e) {}
  }, [])

  const fetchAmbiguousReviews = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ambiguous-reviews?limit=50`)
      if (res.ok) {
        const data = await res.json()
        setAmbiguousReviews(data.reviews || [])
      }
    } catch (e) {}
  }, [])

  useEffect(() => { 
    fetchStats(); fetchReviews(); fetchClusters(); fetchFeatureInsights(); fetchAmbiguousReviews(); fetchTrends() 
  }, [fetchStats, fetchReviews, fetchClusters, fetchFeatureInsights, fetchAmbiguousReviews, fetchTrends])

  const animatePipeline = useCallback(async (result) => {
    setActiveTab('pulse') 
    setPipelineStep(0)
    for (let i = 0; i <= 7; i++) {
      setPipelineStep(i)
      await new Promise(r => setTimeout(r, 600))
    }
    setLastResult(result)
    setPipelineStep(7)
    fetchStats(); fetchReviews(); fetchClusters(); fetchFeatureInsights(); fetchAmbiguousReviews(); fetchTrends()
    setTimeout(() => setPipelineStep(-1), 3000)
  }, [fetchStats, fetchReviews, fetchClusters, fetchFeatureInsights, fetchAmbiguousReviews, fetchTrends])

  const handleFileUpload = async (file) => {
    if (!file) return
    setLoading(true)
    addToast(`Uploading ${file.name}...`, 'info')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API}/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      if (res.ok) {
        addToast(`✅ Processed ${data.total_processed} reviews`, 'success')
        await animatePipeline(data)
      } else {
        addToast(data.detail || 'Upload failed', 'error')
      }
    } catch (e) {
      addToast('Failed to connect to backend', 'error')
    }
    setLoading(false)
  }

  const handlePaste = async () => {
    if (!pasteText.trim()) return
    setLoading(true)
    addToast('Processing pasted reviews...', 'info')
    try {
      const res = await fetch(`${API}/paste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pasteText }),
      })
      const data = await res.json()
      if (res.ok) {
        addToast(`✅ Processed ${data.total_processed} reviews`, 'success')
        setPasteText('')
        await animatePipeline(data)
      } else {
        addToast(data.detail || 'Processing failed', 'error')
      }
    } catch (e) {
      addToast('Failed to connect to backend', 'error')
    }
    setLoading(false)
  }

  const handleLoadSamples = async () => {
    setLoading(true)
    addToast('Loading sample reviews...', 'info')
    try {
      const res = await fetch(`${API}/load-samples`, { method: 'POST' })
      const data = await res.json()
      if (res.ok) {
        addToast(`✅ Loaded sample data`, 'success')
        await animatePipeline(data)
      }
    } catch (e) {}
    setLoading(false)
  }

  const handleApiFeed = async () => {
    setLoading(true)
    addToast('Simulating API feed...', 'info')
    const sampleFeed = [
      { text: "Phone is great but battery could be better", rating: 4 },
      { text: "Terrible experience, phone crashed multiple times", rating: 1 },
      { text: "ye phone mast hai bhai 👍🔥", rating: 5 },
      { text: "BEST PHONE EVER BUY NOW AMAZING DEAL!!!", rating: 5 },
      { text: "Camera quality in daylight is phenomenal. Night mode needs work.", rating: 4 },
    ]
    try {
      const res = await fetch(`${API}/api-feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviews: sampleFeed }),
      })
      if (res.ok) await animatePipeline(await res.json())
    } catch (e) {}
    setLoading(false)
  }

  const handleReset = async () => {
    try {
      await fetch(`${API}/reset`, { method: 'POST' })
      addToast('Database reset', 'info')
      setLastResult(null); setPipelineStep(-1)
      fetchStats(); fetchReviews(); fetchClusters(); fetchTrends()
    } catch (e) {}
  }

  const drillDownToReviews = (feature, sentiment = null) => {
    setExplorerFeatureFilter(feature);
    setExplorerSentimentFilter(sentiment);
    setActiveTab('explorer');
    addToast(`🔍 Filtering for ${feature}${sentiment ? ` (${sentiment})` : ''}`, 'info');
  };

  const tabs = [
    { id: 'pulse', icon: '⚡', label: 'Pulse Overview' },
    { id: 'explorer', icon: '🗃️', label: 'Data Explorer' },
    { id: 'ingest', icon: '📥', label: 'Ingestion Engine' },
  ]

  return (
    <>
      <div className="app-bg" />
      <div className="app-container">
        <ToastContainer toasts={toasts} onDismiss={id => setToasts(prev => prev.filter(t => t.id !== id))} />

        <aside className="sidebar">
          <div className="logo">
            <div className="logo-icon">IQ</div>
            <div>
              <div className="logo-text">InsightIQ</div>
              <div className="logo-version">v2.1 Premium</div>
            </div>
          </div>
          
          <nav className="sidebar-nav">
            {tabs.map(tab => (
              <button key={tab.id}
                className={`sidebar-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}>
                <span className="sidebar-nav-icon">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>

          <div style={{ marginTop: 'auto' }}>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center' }} onClick={handleReset}>
              🗑️ Reset Pipeline
            </button>
          </div>
        </aside>

        <main className="main-content">
          {/* PIPELINE OVERLAY */}
          {pipelineStep >= 0 && (
            <div className="pipeline-overlay fade-in">
              <div className="card pipeline-card">
                <div className="card-header">
                  <div className="card-title">🚀 Intelligence Pipeline active...</div>
                </div>
                <PipelineViz step={pipelineStep} totalSteps={7} />
                {pipelineStep >= 7 && (
                   <div style={{ textAlign: 'center', marginTop: '20px' }}>
                     <button className="btn btn-primary" onClick={() => setPipelineStep(-1)}>Continue to Insights</button>
                   </div>
                )}
              </div>
            </div>
          )}

          {/* ════════ PULSE TAB ════════ */}
          {activeTab === 'pulse' && (
            <div className="fade-in">
              <div className="section-header">
                <div>
                  <h1 className="section-title">Dashboard Overview</h1>
                  <p className="section-desc">Executive metrics and emerging trend detection</p>
                </div>
              </div>

              {!stats || stats.total_reviews === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📊</div>
                  <h3>Waiting for Data</h3>
                  <button className="btn btn-primary" onClick={() => setActiveTab('ingest')}>📥 Start Ingesting</button>
                </div>
              ) : (
                <>
                  <div className="stats-grid">
                    <div className="stat-card indigo">
                      <div className="stat-label">Total Reviews</div>
                      <div className="stat-value">{stats.total_reviews}</div>
                    </div>
                    <div className="stat-card emerald">
                      <div className="stat-label">Health Score</div>
                      <div className="stat-value">{stats.quality_score}%</div>
                    </div>
                    <div className="stat-card rose">
                      <div className="stat-label">Suspicious</div>
                      <div className="stat-value">{stats.suspicious_count}</div>
                    </div>
                    <div className="stat-card violet">
                      <div className="stat-label">Ambiguous</div>
                      <div className="stat-value">{stats.ambiguous_count || 0}</div>
                    </div>
                  </div>

                  {/* TRENDS RADAR */}
                  {trendsData && trendsData.status !== 'insufficient_data' && (
                    <div className="grid-2" style={{ marginTop: '24px' }}>
                      <div className="card">
                        <div className="card-header">
                          <div style={{ display:'flex', justifyContent:'space-between', width:'100%', alignItems:'center' }}>
                            <div className="card-title">🎯 Product Health Radar</div>
                            <select className="trend-select" value={trendCategory} onChange={(e) => setTrendCategory(e.target.value)}>
                              <option value="Smartwatch">Smartwatch</option>
                              <option value="Smartphone">Smartphone</option>
                              <option value="Headphones">Headphones</option>
                            </select>
                          </div>
                        </div>
                        <ProductHealthRadar trends={trendsData.trends} />
                      </div>

                      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                         <div className="card-header"><div className="card-title">⚠️ Priority Alerts</div></div>
                         {trendsData.alerts.length > 0 ? (
                            trendsData.alerts.map((alert, i) => (
                              <div key={i} className={`trend-alert trend-alert-${alert.severity}`} onClick={() => drillDownToReviews(alert.feature, alert.severity === 'critical' ? 'negative' : null)} style={{ cursor: 'pointer' }}>
                                <div className="trend-alert-icon">{alert.severity === 'critical' ? '🚨' : '⚠️'}</div>
                                <div className="trend-alert-body">
                                  <strong>{alert.feature}</strong>: {alert.message}
                                </div>
                              </div>
                            ))
                         ) : <div className="empty-state">No critical anomalies.</div>}
                      </div>
                    </div>
                  )}

                  {/* FEATURE INSIGHTS & AMBIGUITY */}
                  <div className="grid-2" style={{ marginTop: '24px' }}>
                     <div className="card">
                        <div className="card-header"><div className="card-title">🏷️ Feature Sentiment</div></div>
                        <div className="feature-bars">
                          {featureInsights.slice(0, 6).map((feat, i) => (
                            <div key={i} className="feature-bar-container">
                              <div className="feature-bar-label">{feat.feature}</div>
                              <div className="feature-bar-track-wrap">
                                <div className="feature-bar-track">
                                  <div className="feature-segment positive" style={{ width: `${(feat.positive/feat.mentions)*100}%` }}></div>
                                  <div className="feature-segment negative" style={{ width: `${(feat.negative/feat.mentions)*100}%` }}></div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                     </div>
                     <div className="card">
                        <div className="card-header"><div className="card-title">🤷 Ambiguity Queue</div></div>
                        <div className="ambiguous-grid" style={{ maxHeight: '300px', overflowY:'auto' }}>
                          {ambiguousReviews.slice(0, 5).map((rev, i) => (
                             <div key={i} className="ambiguous-card">
                               <div className="ambiguous-header">
                                 <span className="badge badge-warning">{rev.ambiguity_flags[0]}</span>
                               </div>
                               <div className="ambiguous-text">"{rev.original_text}"</div>
                             </div>
                          ))}
                        </div>
                     </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ════════ EXPLORER TAB ════════ */}
          {activeTab === 'explorer' && (
            <div className="fade-in">
              <div className="section-header">
                <div>
                  <h1 className="section-title">Data Explorer</h1>
                  <p className="section-desc">Search, filter, and drill into granular processing data</p>
                </div>
              </div>

              {/* REVIEWS TABLE */}
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="filter-bar">
                  <div style={{ display: 'flex', gap: '8px', alignItems:'center' }}>
                    {['all', 'clean', 'suspicious', 'duplicate'].map(f => (
                      <button key={f} className={`filter-chip ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>{f}</button>
                    ))}
                  </div>
                  { (explorerFeatureFilter || explorerSentimentFilter) && (
                    <div className="drilldown-active-badge">
                      <span className="badge badge-translated">{explorerFeatureFilter} {explorerSentimentFilter}</span>
                      <button className="btn-close" onClick={() => { setExplorerFeatureFilter(null); setExplorerSentimentFilter(null); }}>×</button>
                    </div>
                  )}
                </div>

                <div className="review-table-wrapper">
                  <table className="review-table">
                    <thead>
                      <tr><th>#</th><th>Review</th><th>Lang</th><th>Quality</th><th>Status</th><th>Stars</th></tr>
                    </thead>
                    <tbody>
                      {reviews.filter(r => {
                         if (explorerFeatureFilter) {
                           return (r.features || []).some(f => f.feature === explorerFeatureFilter && (!explorerSentimentFilter || f.sentiment === explorerSentimentFilter));
                         }
                         return true;
                      }).map((rev, i) => (
                        <ReviewRow key={rev.id || i} review={rev} index={i} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* CLUSTERS */}
              <div className="section-header"><h3>Semantic Clusters</h3></div>
              <div className="cluster-list">
                {clusters.map((cluster, i) => (
                  <div key={i} className="cluster-item">
                    <div className="cluster-header">
                      <strong>Cluster #{i+1}</strong> ({cluster.review_count} docs)
                      <span>Similarity: {(cluster.similarity_score*100).toFixed(1)}%</span>
                    </div>
                    <div className="cluster-reviews">
                      <div className="cluster-review-item representative">⭐ {cluster.representative_text}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ════════ INGEST TAB ════════ */}
          {activeTab === 'ingest' && (
            <div className="fade-in">
              <div className="section-header"><h1 className="section-title">Ingestion Engine</h1></div>
              <div className="ingest-methods">
                <div className="card">
                  <div className="card-header"><div className="card-title">📁 File / 📝 Paste</div></div>
                  <textarea value={pasteText} onChange={e => setPasteText(e.target.value)} placeholder="Paste JSON or raw text..." style={{ minHeight:'150px' }} />
                  <div style={{ display:'flex', gap:'12px', marginTop:'12px' }}>
                    <button className="btn btn-primary" onClick={handlePaste} disabled={loading}>Process Data</button>
                    <button className="btn btn-success" onClick={handleLoadSamples} disabled={loading}>Load Samples</button>
                    <button className="btn btn-secondary" onClick={handleApiFeed} disabled={loading}>Simulate API</button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  )
}

function ReviewRow({ review, index }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <tr onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>
      <td>{index + 1}</td>
      <td>
        <div className={expanded ? '' : 'review-text-cell'}>{review.original_text}</div>
        {expanded && (
          <div className="expanded-review-details">
            {review.translated_text && <div className="translated-box"><strong>Translated:</strong> {review.translated_text}</div>}
            <div className="aspect-pills">
               {(review.features || []).map((f, idx) => (
                 <div key={idx} className={`aspect-pill ${f.sentiment}`}>
                    {f.feature} {f.sentiment === 'positive' ? '👍' : '👎'}
                 </div>
               ))}
            </div>
          </div>
        )}
      </td>
      <td><span className="badge badge-lang">{review.detected_language}</span></td>
      <td><FakeScore score={review.fake_score || 0} /></td>
      <td>{review.is_suspicious ? '🤖 Bot' : review.is_duplicate ? '🔁 Dup' : '✅ Ok'}</td>
      <td>{review.rating ? '⭐'.repeat(review.rating) : '—'}</td>
    </tr>
  )
}

export default App
