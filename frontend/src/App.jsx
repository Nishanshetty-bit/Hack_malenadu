import { useState, useEffect, useCallback, useRef } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
  BarChart, Bar, Cell
} from 'recharts'
import {
  Zap, TrendingUp, Database, Upload, Download, FileJson, RefreshCw, Trash2,
  Shield, Bot, Copy, ThumbsUp, ThumbsDown, Scale, Globe, BarChart3,
  AlertTriangle, AlertCircle, CheckCircle, ChevronRight, Star,
  FileText, Languages, Layers, Activity, Search, Filter, PieChart,
  ArrowUpRight, ArrowDownRight, Minus, Eye, MessageSquare, Award,
  CircleDot, Clock, Users, Settings, BookOpen, Sparkles, Target, Heart,
  HelpCircle, Bell, Package, Save, Calendar, Inbox
} from 'lucide-react'
import './App.css'

const API = 'http://localhost:8000'

// ─── Toast Notification System ────────────────────────────────
function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`} onClick={() => onDismiss(t.id)}>
          <span>{t.type === 'success' ? <CheckCircle size={16} /> : t.type === 'error' ? <AlertCircle size={16} /> : <Activity size={16} />}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Animated Counter ─────────────────────────────────────────
function AnimatedNumber({ value, suffix = '' }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    const start = Date.now()
    const duration = 800
    const from = 0
    const to = Number(value) || 0
    const animate = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(from + (to - from) * eased))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [value])
  return <span>{display}{suffix}</span>
}

// ─── Quality Score Gauge ──────────────────────────────────────
function QualityGauge({ score }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#f43f5e'
  const label = score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : score >= 40 ? 'Fair' : 'Poor'

  return (
    <div className="score-gauge">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
        <circle cx="70" cy="70" r={radius} fill="none" stroke="url(#gaugeGrad)" strokeWidth="12"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }} />
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor={color + 'aa'} />
          </linearGradient>
        </defs>
      </svg>
      <div className="score-gauge-label">
        <div className="score-gauge-value" style={{ color }}>{score}%</div>
        <div className="score-gauge-text">{label}</div>
      </div>
    </div>
  )
}

// ─── Language Display Names ───────────────────────────────────
const LANG_NAMES = {
  en: 'English', hi: 'Hindi', kn: 'Kannada', ta: 'Tamil', te: 'Telugu',
  es: 'Spanish', fr: 'French', de: 'German', zh: 'Chinese', ja: 'Japanese',
  ko: 'Korean', ar: 'Arabic', ru: 'Russian', pt: 'Portuguese', it: 'Italian',
  mr: 'Marathi', bn: 'Bengali', hinglish: 'Hinglish', kanglish: 'Kanglish', unknown: 'Unknown'
}
function getLangName(code) {
  if (!code) return 'Unknown'
  if (LANG_NAMES[code]) return LANG_NAMES[code]
  try { return new Intl.DisplayNames(['en'], { type: 'language' }).of(code) || code.toUpperCase() }
  catch { return code.toUpperCase() }
}

// ─── Language Distribution Chart ────────────────────────────
const LANG_COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#f43f5e','#3b82f6','#a855f7']
function LanguageChart({ data }) {
  if (!data || Object.keys(data).length === 0) return (
    <div className="empty-mini">No language data yet</div>
  )
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 8)
  return (
    <div className="lang-chart">
      {sorted.map(([lang, count], i) => (
        <div key={lang} className="lang-row">
          <div className="lang-row-label">
            <span className="lang-dot" style={{ background: LANG_COLORS[i % LANG_COLORS.length] }} />
            <span>{getLangName(lang)}</span>
            {(lang === 'hinglish' || lang === 'kanglish') && (
              <span className="badge badge-translated" style={{ fontSize: '9px', padding: '1px 6px' }}>Mixed</span>
            )}
          </div>
          <div className="lang-bar-outer">
            <div className="lang-bar-inner" style={{
              width: `${(count / total) * 100}%`,
              background: LANG_COLORS[i % LANG_COLORS.length]
            }} />
          </div>
          <span className="lang-count">{count}</span>
        </div>
      ))}
    </div>
  )
}

// ─── Product Health Radar ────────────────────────────────────
const CUSTOM_RADAR_TICK = (props) => {
  const { x, y, textAnchor, payload } = props
  return (
    <text x={x} y={y} textAnchor={textAnchor} fill="var(--text-tertiary)" fontSize={11} fontWeight={500}>
      {payload.value.charAt(0).toUpperCase() + payload.value.slice(1).replace('_', ' ')}
    </text>
  )
}

function ProductHealthRadar({ trends }) {
  if (!trends || Object.keys(trends).length === 0) return (
    <div className="empty-mini">Insufficient data for radar analysis</div>
  )
  const data = Object.entries(trends).map(([feat, stats]) => {
    const rT = stats.recent_positive_pct + stats.recent_negative_pct
    const hT = stats.hist_positive_pct + stats.hist_negative_pct
    const recent = rT > 0 ? Math.round((stats.recent_positive_pct / rT) * 100) : 50
    const historical = hT > 0 ? Math.round((stats.hist_positive_pct / hT) * 100) : 50
    return { feature: feat.replace('_', ' '), recent, historical, fullMark: 100 }
  }).slice(0, 8)

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="72%" data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.07)" />
          <PolarAngleAxis dataKey="feature" tick={CUSTOM_RADAR_TICK} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--text-tertiary)', fontSize: 9 }} />
          <Radar name="Historical Avg" dataKey="historical" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} strokeWidth={2} />
          <Radar name="Recent (Last 50)" dataKey="recent" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.3} strokeWidth={2} />
          <Tooltip contentStyle={{ background: 'rgba(18,18,26,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', fontSize: '13px' }} />
          <Legend iconType="circle" wrapperStyle={{ paddingTop: '16px', fontSize: '12px' }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─── Fake Score Bar ───────────────────────────────────────────
function FakeScore({ score }) {
  const level = score >= 0.55 ? 'high' : score >= 0.3 ? 'medium' : 'low'
  const colors = { high: '#f43f5e', medium: '#f59e0b', low: '#10b981' }
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <span style={{ width: '60px', height: '5px', background: 'rgba(255,255,255,0.08)', borderRadius: '99px', overflow: 'hidden', display: 'inline-block' }}>
        <span style={{ display: 'block', width: `${score * 100}%`, height: '100%', background: colors[level], borderRadius: '99px', transition: 'width 0.4s ease' }} />
      </span>
      <span style={{ fontSize: '12px', color: colors[level], fontWeight: 600 }}>{(score * 100).toFixed(0)}%</span>
    </span>
  )
}

// ─── Feature Insight Bar ──────────────────────────────────────
function FeatureBar({ feat, onClick }) {
  const total = Math.max(feat.mentions, 1)
  const posPct = Math.round((feat.positive / total) * 100)
  const negPct = Math.round((feat.negative / total) * 100)
  const mixPct = Math.round(((feat.mixed || 0) / total) * 100)
  const label = feat.feature.replace('_', ' ').charAt(0).toUpperCase() + feat.feature.replace('_', ' ').slice(1)
  return (
    <div className="feat-bar-row" onClick={onClick} title={`Click to drill into ${label} reviews`}>
      <div className="feat-bar-header">
        <span className="feat-bar-label">{label}</span>
        <div className="feat-bar-stats">
          <span className="feat-stat positive">▲ {posPct}%</span>
          <span className="feat-stat negative">▼ {negPct}%</span>
          <span className="feat-count">{feat.mentions} reviews</span>
        </div>
      </div>
      <div className="feat-bar-track">
        <div className="feat-bar-seg pos" style={{ width: `${posPct}%` }} />
        <div className="feat-bar-seg mix" style={{ width: `${mixPct}%` }} />
        <div className="feat-bar-seg neg" style={{ width: `${negPct}%` }} />
      </div>
    </div>
  )
}

// ─── Trend Alert Card ─────────────────────────────────────────
function TrendAlertCard({ alert, onDrillDown }) {
  const configs = {
    critical: {
      icon: <AlertCircle size={20}/>,
      badge: 'CRITICAL',
      borderColor: '#f43f5e',
      bgGlow: 'rgba(244,63,94,0.06)',
      badgeBg: 'rgba(244,63,94,0.15)',
      badgeColor: '#fb7185',
    },
    warning: {
      icon: <AlertTriangle size={20}/>,
      badge: 'WARNING',
      borderColor: '#f59e0b',
      bgGlow: 'rgba(245,158,11,0.06)',
      badgeBg: 'rgba(245,158,11,0.15)',
      badgeColor: '#fbbf24',
    },
    success: {
      icon: <Sparkles size={20}/>,
      badge: 'PRAISE TREND',
      borderColor: '#10b981',
      bgGlow: 'rgba(16,185,129,0.06)',
      badgeBg: 'rgba(16,185,129,0.15)',
      badgeColor: '#34d399',
    }
  }
  const cfg = configs[alert.severity] || configs.warning
  const isSystemic = alert.is_systemic
  const featureLabel = (alert.feature || '').replace('_', ' ')

  return (
    <div className="alert-card" style={{ borderLeftColor: cfg.borderColor, background: `linear-gradient(90deg, ${cfg.bgGlow} 0%, transparent 80%)` }}
      onClick={() => onDrillDown(alert.feature, alert.severity === 'critical' ? 'negative' : null)}
    >
      <div className="alert-card-top">
        <span className="alert-icon">{cfg.icon}</span>
        <div className="alert-content">
          <div className="alert-header-row">
            <span className="alert-feature-name">{featureLabel}</span>
            <div className="alert-badges">
              <span className="alert-badge" style={{ background: cfg.badgeBg, color: cfg.badgeColor }}>{cfg.badge}</span>
              {isSystemic
                ? <span className="alert-badge systemic"><RefreshCw size={12} style={{marginRight: 4, display: 'inline', verticalAlign: 'text-bottom'}} /> SYSTEMIC</span>
                : <span className="alert-badge isolated"><Target size={12} style={{marginRight: 4, display: 'inline', verticalAlign: 'text-bottom'}} /> ISOLATED</span>
              }
              {alert.assigned_team && (
                <span className="alert-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                  <Upload size={12} style={{marginRight: 4, display: 'inline', verticalAlign: 'text-bottom'}}/> Routing to: {alert.assigned_team}
                </span>
              )}
            </div>
          </div>
          <p className="alert-message">{alert.message}</p>
          {(alert.recent_pct !== undefined && alert.hist_pct !== undefined) && (
            <div className="alert-deltas">
              <div className="delta-chip">
                <span className="delta-label">Recent</span>
                <span className="delta-val" style={{ color: cfg.badgeColor }}>{alert.recent_pct}%</span>
              </div>
              <div className="delta-arrow">→</div>
              <div className="delta-chip">
                <span className="delta-label">Historical</span>
                <span className="delta-val">{alert.hist_pct}%</span>
              </div>
              <div className="delta-chip change">
                <span className="delta-label">Δ Change</span>
                <span className="delta-val" style={{ color: cfg.badgeColor }}>
                  {alert.recent_pct > alert.hist_pct ? '+' : ''}{(alert.recent_pct - alert.hist_pct).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
          {alert.unique_users > 0 && (
            <div className="alert-footer">
              <span className="alert-meta" style={{display: 'flex', alignItems: 'center', gap: 4}}><Users size={14} /> {alert.unique_users} unique reviewers affected</span>
              {alert.review_count > 0 && <span className="alert-meta" style={{display: 'flex', alignItems: 'center', gap: 4}}><FileText size={14} /> {alert.review_count} total reviews</span>}
            </div>
          )}
        </div>
      </div>
      <div className="alert-drilldown-hint">Click to investigate →</div>
    </div>
  )
}

// ─── Ambiguity Card ───────────────────────────────────────────
function AmbiguityCard({ rev }) {
  const [exp, setExp] = useState(false)
  const flag = (rev.ambiguity_flags || [])[0] || 'Ambiguous'
  const isSarcastic = flag.toLowerCase().includes('sarcasm')
  return (
    <div className="ambig-card" onClick={() => setExp(!exp)}>
      <div className="ambig-header">
        <span className={`badge ${isSarcastic ? 'badge-sarcastic' : 'badge-mixed'}`}>
          {isSarcastic ? <><Eye size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'text-bottom'}}/> Sarcasm</> : <><HelpCircle size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'text-bottom'}}/> Mixed</>}
        </span>
        {rev.rating && <span className="ambig-rating" style={{display: 'flex', gap: 2}}>{Array.from({length: Math.round(rev.rating)}).map((_, i) => <Star key={i} size={14} fill="currentColor" />)}</span>}
      </div>
      <div className="ambig-text">&ldquo;{rev.original_text?.slice(0, 120)}{rev.original_text?.length > 120 ? '…' : ''}&rdquo;</div>
      <div className="ambig-flag">{flag}</div>
      {exp && (
        <div className="ambig-aspects">
          {(rev.features || []).map((f, i) => (
            <span key={i} className={`aspect-pill ${f.sentiment}`}>{f.feature} <span className="pill-conf">{(f.confidence * 100).toFixed(0)}%</span></span>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Pipeline Stepper ─────────────────────────────────────────
function PipelineViz({ step }) {
  const steps = [
    { icon: <Trash2 size={16} />, label: 'Clean & Normalize' },
    { icon: <Globe size={16} />, label: 'Detect Language' },
    { icon: <RefreshCw size={16} />, label: 'Translate' },
    { icon: <Search size={16} />, label: 'Deduplicate' },
    { icon: <Bot size={16} />, label: 'Bot Detection' },
    { icon: <Target size={16} />, label: 'Sentiment Analysis' },
    { icon: <Save size={16} />, label: 'Store Results' },
  ]
  return (
    <div>
      <div className="pipeline-grid">
        {steps.map((s, i) => (
          <div key={i} className={`pipeline-step ${i < step ? 'done' : i === step ? 'active' : ''}`}>
            <span className="pipeline-step-icon">{i < step ? <CheckCircle size={16} /> : s.icon}</span>
            <span className="pipeline-step-label">{s.label}</span>
            {i === step && <div className="pipeline-pulse" />}
          </div>
        ))}
      </div>
      <div className="progress-bar" style={{ marginTop: '24px' }}>
        <div className="progress-fill" style={{ width: `${(step / 7) * 100}%` }} />
      </div>
      <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '13px', marginTop: '8px' }}>
        Step {step} of 7 — {steps[Math.min(step, 6)]?.label}
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
//  MAIN APP
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
  const [explorerFeatureFilter, setExplorerFeatureFilter] = useState(null)
  const [explorerSentimentFilter, setExplorerSentimentFilter] = useState(null)
  const [trendCategory, setTrendCategory] = useState('General')
  const [trendsData, setTrendsData] = useState(null)
  const [trendStartDate, setTrendStartDate] = useState('')
  const [trendEndDate, setTrendEndDate] = useState('')
  const [activeAlertTab, setActiveAlertTab] = useState('critical')
  const [persistentAlerts, setPersistentAlerts] = useState([])
  const [alertTeamFilter, setAlertTeamFilter] = useState('All Teams')
  const [activePreset, setActivePreset] = useState('all')
  const [categoryComparison, setCategoryComparison] = useState([])
  const [explorerSearch, setExplorerSearch] = useState('')
  const [explorerCategoryFilter, setExplorerCategoryFilter] = useState('All')
  const fileInputRef = useRef(null)

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4500)
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API}/stats`)
      if (res.ok) setStats(await res.json())
    } catch { }
  }, [])

  const fetchTrends = useCallback(async () => {
    try {
      let url = `${API}/trends?category=${trendCategory}`
      if (trendStartDate) url += `&start_date=${trendStartDate}`
      if (trendEndDate) url += `&end_date=${trendEndDate}`
      const res = await fetch(url)
      if (res.ok) setTrendsData(await res.json())
    } catch { }
  }, [trendCategory, trendStartDate, trendEndDate])

  const fetchPersistentAlerts = useCallback(async () => {
    try {
      let url = `${API}/alerts?status=open`
      if (alertTeamFilter !== 'All Teams') url += `&team=${alertTeamFilter}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setPersistentAlerts(data.alerts || [])
      }
    } catch { }
  }, [alertTeamFilter])

  const fetchReviews = useCallback(async () => {
    try {
      let url = `${API}/reviews?limit=200`
      if (filter === 'suspicious') url += '&suspicious=true'
      else if (filter === 'duplicate') url += '&duplicate=true'
      else if (filter === 'clean') url += '&suspicious=false&duplicate=false'
      const res = await fetch(url)
      if (res.ok) setReviews((await res.json()).reviews || [])
    } catch { }
  }, [filter])

  const fetchClusters = useCallback(async () => {
    try {
      const res = await fetch(`${API}/clusters`)
      if (res.ok) setClusters((await res.json()).clusters || [])
    } catch { }
  }, [])

  const fetchFeatureInsights = useCallback(async () => {
    try {
      const res = await fetch(`${API}/feature-insights`)
      if (res.ok) setFeatureInsights((await res.json()).features || [])
    } catch { }
  }, [])

  const fetchAmbiguousReviews = useCallback(async () => {
    try {
      const res = await fetch(`${API}/ambiguous-reviews?limit=20`)
      if (res.ok) setAmbiguousReviews((await res.json()).reviews || [])
    } catch { }
  }, [])

  const fetchCategoryComparison = useCallback(async () => {
    try {
      const res = await fetch(`${API}/category-comparison`)
      if (res.ok) setCategoryComparison((await res.json()).categories || [])
    } catch { }
  }, [])

  const refreshAll = useCallback(() => {
    fetchStats(); fetchReviews(); fetchClusters(); fetchFeatureInsights(); fetchAmbiguousReviews(); fetchTrends(); fetchPersistentAlerts(); fetchCategoryComparison()
  }, [fetchStats, fetchReviews, fetchClusters, fetchFeatureInsights, fetchAmbiguousReviews, fetchTrends, fetchPersistentAlerts, fetchCategoryComparison])

  useEffect(() => { refreshAll() }, [refreshAll])

  const setDatePreset = (preset) => {
    setActivePreset(preset)
    const end = new Date().toISOString().split('T')[0]
    let start = ''
    
    if (preset === '7d') {
      const d = new Date()
      d.setDate(d.getDate() - 7)
      start = d.toISOString().split('T')[0]
    } else if (preset === '30d') {
      const d = new Date()
      d.setDate(d.getDate() - 30)
      start = d.toISOString().split('T')[0]
    } else if (preset === '90d') {
      const d = new Date()
      d.setDate(d.getDate() - 90)
      start = d.toISOString().split('T')[0]
    }
    
    setTrendStartDate(start)
    setTrendEndDate(end)
    addToast(`Filter applied: ${preset === 'all' ? 'All Time' : preset}`, 'info')
  }

  const handleResolveAlert = async (id) => {
    try {
      const res = await fetch(`${API}/alerts/resolve/${id}`, { method: 'POST' })
      if (res.ok) {
        addToast(<><CheckCircle size={14} /> Alert resolved and routed to archive</>, "success")
        fetchPersistentAlerts()
      }
    } catch { addToast("Failed to resolve alert", "error") }
  }

  const animatePipeline = useCallback(async (result) => {
    setPipelineStep(0)
    for (let i = 0; i <= 7; i++) {
      setPipelineStep(i)
      await new Promise(r => setTimeout(r, 550))
    }
    setLastResult(result)
    refreshAll()
    setTimeout(() => setPipelineStep(-1), 2500)
  }, [refreshAll])

  const handleFileUpload = async (file) => {
    if (!file) return
    setLoading(true)
    addToast(`Uploading ${file.name}…`, 'info')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API}/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      if (res.ok) {
        addToast(`Processed ${data.total_processed} reviews`, 'success')
        await animatePipeline(data)
      } else addToast(data.detail || 'Upload failed', 'error')
    } catch { addToast('Cannot reach backend', 'error') }
    setLoading(false)
  }

  const handlePaste = async () => {
    if (!pasteText.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/paste`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: pasteText }),
      })
      const data = await res.json()
      if (res.ok) {
        addToast(`Processed ${data.total_processed} reviews`, 'success')
        setPasteText('')
        await animatePipeline(data)
      } else addToast(data.detail || 'Processing failed', 'error')
    } catch { addToast('Cannot reach backend', 'error') }
    setLoading(false)
  }

  const handleLoadSamples = async () => {
    setLoading(true)
    addToast('Loading sample data…', 'info')
    try {
      const res = await fetch(`${API}/load-samples`, { method: 'POST' })
      if (res.ok) { addToast('Samples loaded', 'success'); await animatePipeline(await res.json()) }
    } catch { }
    setLoading(false)
  }

  const handleApiFeed = async () => {
    setLoading(true)
    addToast('Simulating API ingestion…', 'info')
    const feed = [
      { review: "Phone is great but battery could be better", rating: 4, product: "Smartphone", id: "f-001" },
      { review: "Camera quality absolutely stunning!", rating: 5, product: "Smartphone", id: "f-002" },
      { review: "Terrible experience, phone crashed repeatedly", rating: 1, product: "Smartphone", id: "f-003" },
      { review: "ye phone mast hai bhai 👍🔥 battery super badhiya", rating: 5, product: "Smartphone", id: "f-004" },
      { review: "Packaging was damaged on arrival. Very disappointed", rating: 2, product: "Smartwatch", id: "f-005" },
      { review: "BEST PHONE EVER BUY NOW AMAZING DEAL!!!", rating: 5, product: "Smartphone", id: "f-006" },
      { review: "Screen display is vibrant and sharp", rating: 4, product: "Smartwatch", id: "f-007" },
      { review: "Delivery was super fast, box was crushed though", rating: 3, product: "Headphones", id: "f-008" },
    ]
    try {
      const res = await fetch(`${API}/api-feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviews: feed }),
      })
      if (res.ok) await animatePipeline(await res.json())
    } catch { }
    setLoading(false)
  }

  const handleReset = async () => {
    if (!confirm('Reset all data?')) return
    await fetch(`${API}/reset`, { method: 'POST' })
    addToast('Database cleared', 'info')
    setStats(null); setReviews([]); setClusters([]); setFeatureInsights([]); setAmbiguousReviews([]); setTrendsData(null); setLastResult(null); setCategoryComparison([])
  }

  const handleDownloadReport = async (format = 'json') => {
    addToast(`Generating ${format.toUpperCase()} report…`, 'info')
    try {
      const res = await fetch(`${API}/export-report?format=${format}`)
      if (!res.ok) { addToast('Report generation failed', 'error'); return }
      const data = await res.json()

      let blob, filename
      if (format === 'csv') {
        blob = new Blob([data.content], { type: 'text/csv;charset=utf-8;' })
        filename = data.filename || 'insightiq_report.csv'
      } else {
        blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        filename = data.filename || 'insightiq_report.json'
      }

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      addToast(`Report downloaded: ${filename}`, 'success')
    } catch { addToast('Cannot generate report', 'error') }
  }

  const drillDownToReviews = (feature, sentiment = null) => {
    setExplorerFeatureFilter(feature)
    setExplorerSentimentFilter(sentiment)
    setActiveTab('explorer')
    addToast(`Drilling into: ${(feature || '').replace('_', ' ')}`, 'info')
  }

  // ─── Computed Stats ──────────────────────────────────────────
  const positiveRate = stats ? Math.round((stats.positive_count / Math.max(stats.total_reviews, 1)) * 100) : 0
  const negativeRate = stats ? Math.round((stats.negative_count / Math.max(stats.total_reviews, 1)) * 100) : 0
  const uniqueLangs = stats?.language_distribution ? Object.keys(stats.language_distribution).length : 0

  // ─── Alert Grouping ──────────────────────────────────────────
  const allAlerts = trendsData?.alerts || []
  const criticalAlerts = allAlerts.filter(a => a.severity === 'critical')
  const warningAlerts = allAlerts.filter(a => a.severity === 'warning')
  const successAlerts = allAlerts.filter(a => a.severity === 'success')

  const tabs = [
    { id: 'pulse', icon: <Zap size={20} />, label: 'Pulse Overview' },
    { id: 'trends', icon: <TrendingUp size={20} />, label: 'Trend Intelligence' },
    { id: 'explorer', icon: <Database size={20} />, label: 'Data Explorer' },
    { id: 'ingest', icon: <Upload size={20} />, label: 'Ingestion Engine' },
  ]

  const hasData = stats && stats.total_reviews > 0

  return (
    <>
      <div className="app-bg" />
      <div className="app-container">
        <ToastContainer toasts={toasts} onDismiss={id => setToasts(prev => prev.filter(t => t.id !== id))} />

        {/* ── SIDEBAR ── */}
        <aside className="sidebar">
          <div className="logo" style={{ marginBottom: '32px' }}>
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
                {tab.id === 'trends' && criticalAlerts.length > 0 && (
                  <span className="sidebar-alert-dot">{criticalAlerts.length}</span>
                )}
              </button>
            ))}
          </nav>

          {hasData && (
            <div className="sidebar-data-pill">
              <div className="sdp-row">
                <span>Reviews</span><strong>{stats.total_reviews}</strong>
              </div>
              <div className="sdp-row">
                <span>Languages</span><strong>{uniqueLangs}</strong>
              </div>
              <div className="sdp-row">
                <span>Bot Flagged</span><strong style={{ color: 'var(--accent-rose)' }}>{stats.suspicious_count}</strong>
              </div>
            </div>
          )}

          <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {hasData && (
              <div className="download-dropdown">
                <button className="btn btn-success" style={{ width: '100%', justifyContent: 'center', fontSize: '13px' }}
                  onClick={() => handleDownloadReport('csv')}><Download size={14} /> Download CSV</button>
                <button className="btn" style={{ width: '100%', justifyContent: 'center', fontSize: '13px', background: 'rgba(99,102,241,0.1)', color: 'var(--accent-indigo)', border: '1px solid rgba(99,102,241,0.2)' }}
                  onClick={() => handleDownloadReport('json')}><FileJson size={14} /> Download JSON</button>
              </div>
            )}
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center', fontSize: '13px' }}
              onClick={refreshAll}><RefreshCw size={14} /> Refresh</button>
            <button className="btn" style={{ width: '100%', justifyContent: 'center', fontSize: '13px', background: 'rgba(244,63,94,0.1)', color: 'var(--accent-rose)', border: '1px solid rgba(244,63,94,0.2)' }}
              onClick={handleReset}><Trash2 size={14} /> Reset Data</button>
          </div>
        </aside>

        <main className="main-content">
          {/* ── PIPELINE OVERLAY ── */}
          {pipelineStep >= 0 && (
            <div className="pipeline-overlay">
              <div className="card" style={{ width: '90%', maxWidth: '820px', padding: '40px', boxShadow: '0 0 60px rgba(99,102,241,0.25)' }}>
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                  <div style={{ fontSize: '13px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>AI Intelligence Pipeline</div>
                  <div style={{ fontSize: '22px', fontWeight: '800', background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    Processing Reviews…
                  </div>
                </div>
                <PipelineViz step={pipelineStep} />
                {pipelineStep >= 7 && (
                  <div style={{ textAlign: 'center', marginTop: '28px' }}>
                    <button className="btn btn-primary btn-lg" onClick={() => { setPipelineStep(-1); setActiveTab('pulse') }}>
                      View Insights →
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ════════ PULSE TAB ════════ */}
          {activeTab === 'pulse' && (
            <div className="fade-in">
              <div className="page-header">
                <div>
                  <h1 className="page-title">Pulse Overview</h1>
                  <p className="page-desc">Real-time intelligence dashboard — executive analytics at a glance</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <div className="live-indicator"><span className="live-dot" />Live</div>
                </div>
              </div>

              {!hasData ? (
                <div className="empty-hero">
                  <div className="empty-hero-icon"><BarChart3 size={48} /></div>
                  <h2>No Data Yet</h2>
                  <p>Ingest your first batch of reviews to see intelligence insights</p>
                  <button className="btn btn-primary btn-lg" onClick={() => setActiveTab('ingest')}><Download size={18} style={{marginRight: 8}} /> Start Ingesting</button>
                </div>
              ) : (
                <>
                  {/* ── KPI GRID ── */}
                  <div className="kpi-grid">
                    <div className="kpi-card indigo">
                      <div className="kpi-icon"><BarChart3 size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Total Reviews</div>
                        <div className="kpi-value"><AnimatedNumber value={stats.total_reviews} /></div>
                        <div className="kpi-sub">{uniqueLangs} languages detected</div>
                      </div>
                    </div>
                    <div className="kpi-card emerald">
                      <div className="kpi-icon"><ThumbsUp size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Positive Sentiment</div>
                        <div className="kpi-value"><AnimatedNumber value={positiveRate} suffix="%" /></div>
                        <div className="kpi-sub">{stats.positive_count || 0} reviews</div>
                      </div>
                    </div>
                    <div className="kpi-card rose">
                      <div className="kpi-icon"><Bot size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Bot / Suspicious</div>
                        <div className="kpi-value"><AnimatedNumber value={stats.suspicious_count} /></div>
                        <div className="kpi-sub">{Math.round((stats.suspicious_count / Math.max(stats.total_reviews, 1)) * 100)}% of total</div>
                      </div>
                    </div>
                    <div className="kpi-card amber">
                      <div className="kpi-icon"><Copy size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Duplicates</div>
                        <div className="kpi-value"><AnimatedNumber value={stats.duplicate_count} /></div>
                        <div className="kpi-sub">{stats.cluster_count || 0} semantic clusters</div>
                      </div>
                    </div>
                    <div className="kpi-card violet">
                      <div className="kpi-icon"><HelpCircle size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Ambiguous / Sarcastic</div>
                        <div className="kpi-value"><AnimatedNumber value={stats.ambiguous_count || 0} /></div>
                        <div className="kpi-sub">Require human review</div>
                      </div>
                    </div>
                    <div className="kpi-card cyan">
                      <div className="kpi-icon"><Star size={24} /></div>
                      <div className="kpi-body">
                        <div className="kpi-label">Data Quality Score</div>
                        <div className="kpi-value"><AnimatedNumber value={stats.quality_score || 0} suffix="%" /></div>
                        <div className="kpi-sub">{stats.quality_score >= 80 ? 'Excellent' : stats.quality_score >= 60 ? 'Good' : 'Needs attention'}</div>
                      </div>
                    </div>
                  </div>

                  {/* ── TWO COLUMN SECTION ── */}
                  <div className="two-col" style={{ marginTop: '28px' }}>

                    {/* Feature Sentiment Deep Dive */}
                    <div className="card">
                      <div className="card-header">
                        <div className="card-title">
                          <Target size={18} className="card-title-icon" />
                          Feature Sentiment Breakdown
                        </div>
                        <span className="card-badge">{featureInsights.length} features</span>
                      </div>
                      {featureInsights.length === 0 ? (
                        <div className="empty-mini">No feature data yet</div>
                      ) : (
                        <div className="feat-bars-list">
                          {featureInsights.slice(0, 8).map((feat, i) => (
                            <FeatureBar key={i} feat={feat} onClick={() => drillDownToReviews(feat.feature)} />
                          ))}
                        </div>
                      )}
                      <div className="feat-legend">
                        <span><span className="legend-dot" style={{ background: '#10b981' }} />Positive</span>
                        <span><span className="legend-dot" style={{ background: '#f59e0b' }} />Mixed</span>
                        <span><span className="legend-dot" style={{ background: '#f43f5e' }} />Negative</span>
                      </div>
                    </div>

                    {/* Right column */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      {/* Quality Gauge + Language */}
                      <div className="card">
                        <div className="card-header">
                          <div className="card-title"><Globe size={18} className="card-title-icon"/> Language Mix</div>
                        </div>
                        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                          <QualityGauge score={stats.quality_score || 0} />
                          <div style={{ flex: 1 }}>
                            <LanguageChart data={stats.language_distribution} />
                          </div>
                        </div>
                      </div>

                      {/* Ambiguity Queue mini */}
                      <div className="card" style={{ flex: 1 }}>
                        <div className="card-header">
                          <div className="card-title"><HelpCircle size={18} className="card-title-icon"/> Sarcastic Reviews</div>
                          <span className="card-badge">{ambiguousReviews.length}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '220px', overflowY: 'auto' }}>
                          {ambiguousReviews.length === 0
                            ? <div className="empty-mini">No ambiguous reviews</div>
                            : ambiguousReviews.slice(0, 5).map((rev, i) => (
                              <AmbiguityCard key={i} rev={rev} />
                            ))
                          }
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* ── MINI TREND ALERT PREVIEW ── */}
                  {allAlerts.length > 0 && (
                    <div className="card" style={{ marginTop: '24px' }}>
                      <div className="card-header">
                        <div className="card-title"><AlertCircle size={18} className="card-title-icon"/> Active Anomalies</div>
                        <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('trends')}>
                          Full Report →
                        </button>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {allAlerts.slice(0, 3).map((alert, i) => (
                          <TrendAlertCard key={i} alert={alert} onDrillDown={drillDownToReviews} />
                        ))}
                        {allAlerts.length > 3 && (
                          <button className="btn btn-secondary" style={{ alignSelf: 'flex-start' }} onClick={() => setActiveTab('trends')}>
                            +{allAlerts.length - 3} more alerts →
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* ── CATEGORY CROSS-COMPARISON ── */}
                  {categoryComparison.length >= 2 && (
                    <div className="card" style={{ marginTop: '24px' }}>
                      <div className="card-header">
                        <div className="card-title"><Award size={18} className="card-title-icon"/> Category Cross-Comparison</div>
                        <span className="card-badge">{categoryComparison.length} categories</span>
                      </div>

                      {/* Comparison Bar Chart */}
                      <div style={{ width: '100%', height: 280, marginBottom: '20px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={categoryComparison} barCategoryGap="20%">
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="category" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                            <YAxis tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }} />
                            <Tooltip
                              contentStyle={{ background: 'rgba(18,18,26,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', fontSize: '13px' }}
                              formatter={(val, name) => [`${val}%`, name]}
                            />
                            <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                            <Bar dataKey="positive_pct" name="Positive %" fill="#10b981" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="neutral_pct" name="Neutral %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="negative_pct" name="Negative %" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Comparison Cards Grid */}
                      <div className="comparison-grid">
                        {categoryComparison.map((cat, i) => {
                          const scoreColor = cat.sentiment_score >= 20 ? '#10b981' : cat.sentiment_score >= 0 ? '#f59e0b' : '#f43f5e'
                          const posPct = cat.positive_pct;
                          const negPct = cat.negative_pct;
                          return (
                            <div key={i} className="comparison-card">
                              <div className="comp-card-header">
                                <span className="comp-cat-name">{cat.category}</span>
                                <span className="comp-review-count">{cat.total_reviews} reviews</span>
                              </div>
                              <div className="comp-score" style={{ color: scoreColor }}>
                                {cat.sentiment_score > 0 ? '+' : ''}{cat.sentiment_score}%
                                <span className="comp-score-label">Net Sentiment</span>
                              </div>
                              <div className="comp-rating">
                                <span style={{ color: 'var(--accent-amber)' }}>{'★'.repeat(Math.round(cat.avg_rating))}</span>
                                <span className="comp-rating-val">{cat.avg_rating.toFixed(1)}</span>
                              </div>
                              <div className="comp-bars">
                                <div className="comp-bar-row">
                                  <span className="comp-bar-label"><ThumbsUp size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'middle'}}/> Positive</span>
                                  <div className="comp-bar mix" style={{ background: 'var(--accent-emerald)', width: `${posPct}%` }} />
                                  <span className="comp-bar-pct">{posPct}%</span>
                                </div>
                                <div className="comp-bar-row">
                                  <span className="comp-bar-label"><ThumbsDown size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'middle'}}/> Negative</span>
                                  <div className="comp-bar mix" style={{ background: 'var(--accent-rose)', width: `${negPct}%` }} />
                                  <span className="comp-bar-pct">{negPct}%</span>
                                </div>
                              </div>
                              <div className="comp-insights-list mt-3">
                                {cat.top_praise && <div className="comp-insight good"><Sparkles size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'middle'}}/> Top: <strong>{cat.top_praise.replace('_', ' ')}</strong></div>}
                                {cat.top_complaint && <div className="comp-insight bad"><AlertTriangle size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'middle'}}/> Pain: <strong>{cat.top_complaint.replace('_', ' ')}</strong></div>}
                                {cat.suspicious_count > 0 && <div className="comp-insight warn"><Bot size={14} style={{marginRight: 4, display: 'inline', verticalAlign: 'middle'}}/> {cat.suspicious_count} bot flagged</div>}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* ════════ TREND INTELLIGENCE TAB ════════ */}
          {activeTab === 'trends' && (
            <div className="fade-in">
              <div className="page-header">
                <div>
                  <h1 className="page-title">Trend Intelligence</h1>
                  <p className="page-desc">Layer 3 — Temporal anomaly detection, systemic vs isolated issue classification</p>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div className="preset-group">
                    <button className={`preset-btn ${activePreset === 'all' ? 'active' : ''}`} onClick={() => setDatePreset('all')}><Activity size={14} /> All Time</button>
                    {['7d', '30d', '90d'].map(p => (
                      <button key={p} className={`preset-btn ${activePreset === p ? 'active' : ''}`} onClick={() => setDatePreset(p)}>
                        {p.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <div className="v-divider" />
                  <input type="date" className="trend-select" value={trendStartDate} onChange={e => { setTrendStartDate(e.target.value); setActivePreset('custom') }} title="From Date" style={{ colorScheme: 'dark' }} />
                  <span style={{ color: 'var(--text-tertiary)' }}>to</span>
                  <input type="date" className="trend-select" value={trendEndDate} onChange={e => { setTrendEndDate(e.target.value); setActivePreset('custom') }} title="To Date" style={{ colorScheme: 'dark' }} />
                  <select className="trend-select" value={trendCategory} onChange={e => { setTrendCategory(e.target.value) }}>
                    <option value="General">All Categories</option>
                    <option value="Smartphone">Smartphone</option>
                    <option value="Smartwatch">Smartwatch</option>
                    <option value="Headphones">Headphones</option>
                    <option value="Wireless Mouse">Wireless Mouse</option>
                  </select>
                </div>
              </div>

              {!trendsData || trendsData.status === 'insufficient_data' ? (
                <div className="empty-hero">
                  <div className="empty-hero-icon"><TrendingUp size={48} /></div>
                  <h2>Need More Data</h2>
                  <p>Trend analysis requires at least 20 reviews. Load sample data to see this in action.</p>
                  <button className="btn btn-primary" onClick={handleLoadSamples} disabled={loading}>Load Sample Reviews</button>
                </div>
              ) : (
                <>



                  <div className="two-col" style={{ marginTop: '24px' }}>
                    {/* Radar Chart */}
                    <div className="card">
                      <div className="card-header">
                        <div className="card-title" style={{ justifyContent: 'space-between' }}>
                          <span><Target size={18} className="card-title-icon" /> Feature Radar</span>
                          <span className="badge badge-info">{stats.feature_mentions?.length || 0} extracted</span>
                        </div>
                        <div className="card-badge-grp">
                          <span className="card-badge" style={{ background: 'rgba(99,102,241,0.15)', color: 'var(--accent-indigo)' }}>■ Historical</span>
                          <span className="card-badge" style={{ background: 'rgba(244,63,94,0.15)', color: 'var(--accent-rose)' }}>■ Recent</span>
                        </div>
                      </div>
                      <ProductHealthRadar trends={trendsData.trends} />
                      <div className="radar-note">
                        Higher score = more positive sentiment. Drop between layers signals a systemic shift.
                      </div>
                    </div>

                    {/* Feature Trend Table */}
                    <div className="card">
                      <div className="card-header">
                        <div className="card-title"><BarChart3 size={18} className="card-title-icon"/> Feature Trend Table</div>
                      </div>
                      <div className="trend-table-scroll">
                        <table className="trend-table">
                          <thead>
                            <tr>
                              <th>Feature</th>
                              <th>Recent Neg%</th>
                              <th>Hist Neg%</th>
                              <th>Δ Shift</th>
                              <th>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(trendsData.trends || {}).map(([feat, stats]) => {
                              const delta = stats.recent_negative_pct - stats.hist_negative_pct
                              const isWorse = delta > 5
                              const isBetter = delta < -5
                              return (
                                <tr key={feat} onClick={() => drillDownToReviews(feat, 'negative')} className="trend-table-row">
                                  <td className="trend-feat-name">{feat.replace('_', ' ')}</td>
                                  <td style={{ color: stats.recent_negative_pct > 20 ? 'var(--accent-rose)' : 'var(--text-secondary)' }}>
                                    {stats.recent_negative_pct}%
                                  </td>
                                  <td>{stats.hist_negative_pct}%</td>
                                  <td>
                                    <span className={`delta-tag ${isWorse ? 'worse' : isBetter ? 'better' : 'neutral'}`}>
                                      {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
                                    </span>
                                  </td>
                                  <td>
                                    {isWorse
                                      ? <span className="status-pill critical">↑ Degrading</span>
                                      : isBetter
                                      ? <span className="status-pill good">↓ Improving</span>
                                      : <span className="status-pill stable">→ Stable</span>
                                    }
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>

                  {/* ── ALERTS SECTION ── */}
                  <div className="card" style={{ marginTop: '24px' }}>
                    <div className="card-header">
                      <div className="card-title"><Bell size={18} className="card-title-icon"/> Anomaly Intelligence Feed</div>
                      <div className="alert-tabs">
                        {[['critical', <AlertCircle size={16}/>, criticalAlerts.length], ['warning', <AlertTriangle size={16}/>, warningAlerts.length], ['success', <Sparkles size={16}/>, successAlerts.length]].map(([type, icon, count]) => (
                          <button key={type} className={`alert-tab-btn ${activeAlertTab === type ? 'active-' + type : ''}`}
                            onClick={() => setActiveAlertTab(type)}>
                            {icon} {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Context box */}
                    <div className="alert-context-box">
                      <div className="alert-context-banner">
                        <span className="acb-icon"><BookOpen size={16} /></span>
                        <div>
                          <strong>How to read this:</strong> <em>Systemic</em> issues appear across multiple unique reviewers and are likely linked to a product or batch defect.
                          <em> Isolated</em> issues appear in 1–2 reviews and may be anecdotal or outliers.
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
                      {(activeAlertTab === 'critical' ? criticalAlerts : activeAlertTab === 'warning' ? warningAlerts : successAlerts).length === 0
                        ? <div className="empty-mini">No anomalies detected in this batch.</div>
                        : (activeAlertTab === 'critical' ? criticalAlerts : activeAlertTab === 'warning' ? warningAlerts : successAlerts).map((alert, i) => (
                          <TrendAlertCard key={i} alert={alert} onDrillDown={drillDownToReviews} />
                        ))
                      }
                    </div>
                  </div>

                  {/* ── PERSISTENT ACTION CENTER ── */}
                  <div className="card" style={{ marginTop: '24px', background: 'rgba(99, 102, 241, 0.03)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                    <div className="card-header">
                      <div className="card-title">
                        <Inbox size={18} className="card-title-icon" />
                        Business Action Center
                        <span className="live-pill">OPEN ALERTS</span>
                      </div>
                      <div className="team-filter-grp">
                        {['All Teams', 'Engineering Team', 'Logistics Team', 'Management Team', 'Customer Support'].map(team => (
                          <button key={team} className={`team-filter-btn ${alertTeamFilter === team ? 'active' : ''}`}
                            onClick={() => setAlertTeamFilter(team)}>
                            {team}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="action-center-grid">
                      {persistentAlerts.length === 0 ? (
                        <div className="empty-mini" style={{ padding: '40px' }}>
                         <div className="pai-empty"><CheckCircle size={16} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}}/> All quiet. No pending actions for {alertTeamFilter}.</div>
                        </div>
                      ) : (
                        persistentAlerts.map((alert) => (
                          <div key={alert.id} className="persistent-alert-item">
                            <div className="pai-severity" style={{ background: alert.severity === 'critical' ? 'var(--accent-rose)' : alert.severity === 'warning' ? 'var(--accent-amber)' : 'var(--accent-emerald)' }} />
                            <div className="pai-content">
                              <div className="pai-header">
                                <span className="pai-feature">{alert.feature}</span>
                                <span className="pai-type">{alert.alert_type}</span>
                                <span className="pai-team">⤿ {alert.assigned_team}</span>
                                <span className="pai-date">{new Date(alert.detected_at).toLocaleString()}</span>
                              </div>
                              <p className="pai-msg">{alert.message}</p>
                            </div>
                            <button className="pai-resolve-btn" onClick={() => handleResolveAlert(alert.id)}>
                              Resolve
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ════════ EXPLORER TAB ════════ */}
          {activeTab === 'explorer' && (() => {
            // Centralized filter logic — applied once, used everywhere
            const filteredReviews = reviews.filter(r => {
              // 1. Status filter (clean / suspicious / duplicate)
              if (filter === 'clean' && (r.is_suspicious || r.is_duplicate)) return false
              if (filter === 'suspicious' && !r.is_suspicious) return false
              if (filter === 'duplicate' && !r.is_duplicate) return false
              if (filter === 'positive' && !['positive', 'very_positive'].includes(r.sentiment_label)) return false
              if (filter === 'negative' && !['negative', 'very_negative'].includes(r.sentiment_label)) return false
              if (filter === 'mixed' && r.sentiment_label !== 'mixed') return false
              if (filter === 'neutral' && r.sentiment_label !== 'neutral') return false

              // 2. Feature drill-down filter
              if (explorerFeatureFilter) {
                const match = (r.features || []).some(f =>
                  f.feature === explorerFeatureFilter && (!explorerSentimentFilter || f.sentiment === explorerSentimentFilter)
                )
                if (!match) return false
              }

              // 3. Category filter
              if (explorerCategoryFilter && explorerCategoryFilter !== 'All') {
                if (r.product_category !== explorerCategoryFilter) return false
              }

              // 4. Text search
              if (explorerSearch.trim()) {
                const q = explorerSearch.toLowerCase()
                const inText = (r.original_text || '').toLowerCase().includes(q)
                const inClean = (r.cleaned_text || '').toLowerCase().includes(q)
                const inLang = (r.detected_language || '').toLowerCase().includes(q)
                const inCat = (r.product_category || '').toLowerCase().includes(q)
                if (!inText && !inClean && !inLang && !inCat) return false
              }

              return true
            })

            // Count stats for each filter type
            const countClean = reviews.filter(r => !r.is_suspicious && !r.is_duplicate).length
            const countSus = reviews.filter(r => r.is_suspicious).length
            const countDup = reviews.filter(r => r.is_duplicate).length
            const countPos = reviews.filter(r => ['positive', 'very_positive'].includes(r.sentiment_label)).length
            const countNeg = reviews.filter(r => ['negative', 'very_negative'].includes(r.sentiment_label)).length
            const countMixed = reviews.filter(r => r.sentiment_label === 'mixed').length
            const countNeutral = reviews.filter(r => r.sentiment_label === 'neutral').length

            // Get unique categories
            const categories = [...new Set(reviews.map(r => r.product_category).filter(Boolean))]

            return (
            <div className="fade-in">
              <div className="page-header">
                <div>
                  <h1 className="page-title">Data Explorer</h1>
                  <p className="page-desc">Search, filter, and drill into granular review intelligence</p>
                </div>
                {(explorerFeatureFilter || explorerSentimentFilter) && (
                  <div className="drilldown-active-badge">
                      <span style={{display:"flex", alignItems:"center", gap: 6}}><Search size={16}/> {explorerFeatureFilter} {explorerSentimentFilter && `(${explorerSentimentFilter})`}</span>
                    <button className="btn-close" onClick={() => { setExplorerFeatureFilter(null); setExplorerSentimentFilter(null) }}>×</button>
                  </div>
                )}
              </div>

              {/* ── QUALITY BREAKDOWN ── */}
              <div className="explorer-stats-row">
                <div className="explorer-stat-chip good" onClick={() => setFilter('clean')}>
                  <span className="esc-icon"><CheckCircle size={16}/></span>
                  <div><div className="esc-val">{countClean}</div><div className="esc-label">Verified Clean</div></div>
                </div>
                <div className="explorer-stat-chip bad" onClick={() => setFilter('suspicious')}>
                  <span className="esc-icon"><Bot size={16}/></span>
                  <div><div className="esc-val">{countSus}</div><div className="esc-label">Bot / Fake</div></div>
                </div>
                <div className="explorer-stat-chip warn" onClick={() => setFilter('duplicate')}>
                  <span className="esc-icon"><Copy size={16}/></span>
                  <div><div className="esc-val">{countDup}</div><div className="esc-label">Duplicates</div></div>
                </div>
                <div className="explorer-stat-chip pos" onClick={() => setFilter('positive')}>
                  <span className="esc-icon"><ThumbsUp size={16}/></span>
                  <div><div className="esc-val">{countPos}</div><div className="esc-label">Positive</div></div>
                </div>
                <div className="explorer-stat-chip neg" onClick={() => setFilter('negative')}>
                  <span className="esc-icon"><ThumbsDown size={16}/></span>
                  <div><div className="esc-val">{countNeg}</div><div className="esc-label">Negative</div></div>
                </div>
                <div className="explorer-stat-chip mix" onClick={() => setFilter('mixed')}>
                  <span className="esc-icon"><HelpCircle size={16}/></span>
                  <div><div className="esc-val">{countMixed + countNeutral}</div><div className="esc-label">Neutral / Mixed</div></div>
                </div>
              </div>

              {/* ── QUALITY PIE + SENTIMENT SPLIT ── */}
              <div className="grid-2" style={{ marginBottom: '24px' }}>
                <div className="card">
                  <div className="card-header">
                    <div className="card-title"><Shield size={18} className="card-title-icon"/> Review Quality Breakdown</div>
                  </div>
                  <div className="quality-bars">
                    {[
                      { label: 'Clean Reviews', count: countClean, pct: Math.round((countClean / Math.max(reviews.length, 1)) * 100), color: '#10b981' },
                      { label: 'Bot / Fake', count: countSus, pct: Math.round((countSus / Math.max(reviews.length, 1)) * 100), color: '#ef4444' },
                      { label: 'Duplicates', count: countDup, pct: Math.round((countDup / Math.max(reviews.length, 1)) * 100), color: '#f59e0b' },
                    ].map(b => (
                      <div key={b.label} className="quality-bar-item">
                        <div className="quality-bar-header">
                          <span className="quality-bar-label">{b.label}</span>
                          <span className="quality-bar-val">{b.count} <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>({b.pct}%)</span></span>
                        </div>
                        <div className="quality-bar-track">
                          <div className="quality-bar-fill" style={{ width: `${b.pct}%`, background: b.color }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: '16px', padding: '12px 16px', background: countClean > countSus * 3 ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)', borderRadius: 'var(--radius-sm)', fontSize: '13px', fontWeight: 600, color: countClean > countSus * 3 ? '#059669' : '#dc2626' }}>
                    {countClean > countSus * 3 ? 'Good data quality — majority of reviews are clean and trustworthy' : 'High bot/fake rate — review ingestion filters may need adjustment'}
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <div className="card-title"><MessageSquare size={18} className="card-title-icon"/> Sentiment Distribution</div>
                  </div>
                  <div className="quality-bars">
                    {[
                      { label: 'Positive', count: countPos, pct: Math.round((countPos / Math.max(reviews.length, 1)) * 100), color: '#10b981' },
                      { label: 'Negative', count: countNeg, pct: Math.round((countNeg / Math.max(reviews.length, 1)) * 100), color: '#ef4444' },
                      { label: 'Mixed', count: countMixed, pct: Math.round((countMixed / Math.max(reviews.length, 1)) * 100), color: '#f59e0b' },
                      { label: 'Neutral', count: countNeutral, pct: Math.round((countNeutral / Math.max(reviews.length, 1)) * 100), color: '#8b8da3' },
                    ].map(b => (
                      <div key={b.label} className="quality-bar-item">
                        <div className="quality-bar-header">
                          <span className="quality-bar-label">{b.label}</span>
                          <span className="quality-bar-val">{b.count} <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>({b.pct}%)</span></span>
                        </div>
                        <div className="quality-bar-track">
                          <div className="quality-bar-fill" style={{ width: `${b.pct}%`, background: b.color }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ── LANGUAGE BREAKDOWN ── */}
              {reviews.length > 0 && (() => {
                const langCounts = {}
                reviews.forEach(r => {
                  const lang = (r.detected_language || 'unknown').toUpperCase()
                  langCounts[lang] = (langCounts[lang] || 0) + 1
                })
                const sorted = Object.entries(langCounts).sort((a, b) => b[1] - a[1])
                const maxLang = sorted[0]?.[1] || 1
                return (
                  <div className="card" style={{ marginBottom: '24px' }}>
                    <div className="card-header">
                      <div className="card-title"><Globe size={18} className="card-title-icon"/> Language Distribution</div>
                      <span className="card-badge">{sorted.length} languages</span>
                    </div>
                    <div className="lang-bar-chart">
                      {sorted.slice(0, 8).map(([lang, count]) => (
                        <div key={lang} className="lang-bar-row">
                          <span className="lang-bar-label">{lang}</span>
                          <div className="lang-bar-track">
                            <div className={`lang-bar-fill ${lang.toLowerCase()}`} style={{ width: `${(count / maxLang) * 100}%` }}>
                              {count}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })()}

              {/* ── CATEGORY BREAKDOWN ── */}
              {categories.length > 1 && (() => {
                const catStats = {}
                reviews.forEach(r => {
                  const cat = r.product_category || 'Unknown'
                  if (!catStats[cat]) catStats[cat] = { total: 0, clean: 0, sus: 0, pos: 0, neg: 0 }
                  catStats[cat].total++
                  if (!r.is_suspicious && !r.is_duplicate) catStats[cat].clean++
                  if (r.is_suspicious) catStats[cat].sus++
                  if (['positive', 'very_positive'].includes(r.sentiment_label)) catStats[cat].pos++
                  if (['negative', 'very_negative'].includes(r.sentiment_label)) catStats[cat].neg++
                })
                return (
                  <div className="card" style={{ marginBottom: '24px' }}>
                    <div className="card-header">
                      <div className="card-title"><BarChart3 size={18} className="card-title-icon"/> Category Breakdown</div>
                    </div>
                    <div className="comparison-grid">
                      {Object.entries(catStats).map(([cat, st]) => (
                        <div key={cat} className="comparison-card" style={{ padding: '20px' }}>
                          <div className="comp-card-header">
                            <span className="comp-cat-name" style={{ fontSize: '16px' }}>{cat}</span>
                            <span className="comp-review-count">{st.total} reviews</span>
                          </div>
                          <div className="comp-bars" style={{ marginBottom: '8px' }}>
                            <div className="comp-bar-item">
                              <span className="comp-bar-label">Clean</span>
                              <div className="comp-bar-track">
                                <div className="comp-bar-fill pos" style={{ width: `${(st.clean / Math.max(st.total, 1)) * 100}%` }} />
                              </div>
                              <span className="comp-bar-val">{Math.round((st.clean / Math.max(st.total, 1)) * 100)}%</span>
                            </div>
                            <div className="comp-bar-item">
                              <span className="comp-bar-label">Bot Flagged</span>
                              <div className="comp-bar-track">
                                <div className="comp-bar-fill neg" style={{ width: `${(st.sus / Math.max(st.total, 1)) * 100}%` }} />
                              </div>
                              <span className="comp-bar-val">{Math.round((st.sus / Math.max(st.total, 1)) * 100)}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })()}

              {/* ── DUPLICATE CLUSTERS ── */}
              {clusters.length > 0 && (
                <>
                  <div className="card" style={{ marginBottom: '24px' }}>
                    <div className="card-header">
                      <div className="card-title"><Layers size={18} className="card-title-icon"/> Semantic Duplicate Clusters</div>
                      <span className="card-badge">{clusters.length} clusters</span>
                    </div>
                    <div className="cluster-grid">
                      {clusters.map((cluster, i) => (
                        <div key={i} className="cluster-card">
                          <div className="cluster-card-header">
                            <span className="cluster-num">Cluster #{i + 1}</span>
                            <span className="cluster-count">{cluster.review_count} docs</span>
                            <span className="cluster-sim">{((cluster.similarity_score || 0) * 100).toFixed(0)}% similar</span>
                          </div>
                          <div className="cluster-rep">&ldquo;{cluster.representative_text}&rdquo;</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )})()}

          {/* ════════ INGEST TAB ════════ */}
          {activeTab === 'ingest' && (
            <div className="fade-in">
              <div className="page-header">
                <h1 className="page-title">Ingestion Engine</h1>
                <p className="page-desc">Multi-source review ingestion with full AI preprocessing pipeline</p>
              </div>

              <div className="ingest-grid">
                {/* Paste / JSON */}
                <div className="card">
                  <div className="card-header">
                    <div className="card-title"><FileText size={18} className="card-title-icon"/> Paste Reviews</div>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', marginBottom: '12px' }}>
                    Paste raw text (one per line) or paste a JSON array of review objects.
                  </p>
                  <textarea
                    value={pasteText}
                    onChange={e => setPasteText(e.target.value)}
                    placeholder={'[\n  {"id":"rev-001","review":"Great product!","product":"Wireless Mouse","rating":5},\n  {"id":"rev-002","review":"yeh product boht accha hai","product":"Wireless Mouse"}\n]'}
                    style={{ minHeight: '200px', fontFamily: 'monospace', fontSize: '13px' }}
                  />
                  <button className="btn btn-primary" style={{ marginTop: '12px', width: '100%' }}
                    onClick={handlePaste} disabled={loading || !pasteText.trim()}>
                    {loading ? 'Processing…' : 'Run Pipeline'}
                  </button>
                </div>

                {/* Quick Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* File Upload */}
                  <div className="card upload-zone"
                    style={{ minHeight: '140px', cursor: 'pointer', border: dragOver ? '2px dashed var(--accent-indigo)' : undefined }}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={e => { e.preventDefault(); setDragOver(false); handleFileUpload(e.dataTransfer.files[0]) }}>
                    <input ref={fileInputRef} type="file" accept=".csv,.json" style={{ display: 'none' }}
                      onChange={e => handleFileUpload(e.target.files[0])} />
                      <div className="upload-icon"><Upload size={32} /></div>
                    <div className="upload-text">Drop CSV or JSON file</div>
                    <div className="upload-hint">or click to browse</div>
                  </div>

                  {/* Quick Ingest */}
                  <div className="card">
                    <div className="card-header">
                      <div className="card-title"><Upload size={18} className="card-title-icon"/> Action Center</div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <button className="btn btn-success" onClick={handleLoadSamples} disabled={loading}>
                        <Database size={16} style={{marginRight: 8}}/> Load Sample Dataset
                      </button>
                      <button className="btn btn-secondary" onClick={handleApiFeed} disabled={loading}>
                        <Globe size={16} style={{marginRight: 8}}/> Simulate API Feed (Mixed Languages)
                      </button>
                    </div>
                  </div>

                  {/* Pipeline Legend */}
                  <div className="card" style={{ background: 'rgba(99,102,241,0.05)', borderColor: 'rgba(99,102,241,0.2)' }}>
                    <div className="card-title" style={{ marginBottom: '12px' }}><Target size={18} className="card-title-icon" /> Pipeline Stages</div>
                    {[
                      [<Trash2 size={16}/>, 'Text Cleaning', 'Emojis, slang, noise removal'],
                      [<Globe size={16}/>, 'Language Detection', 'Hinglish, Kanglish, 20+ languages'],
                      [<RefreshCw size={16}/>, 'Translation', 'MarianMT → normalize to English'],
                      [<Search size={16}/>, 'Deduplication', 'TF-IDF + cosine near-duplicate clustering'],
                      [<Bot size={16}/>, 'Bot Detection', '10-signal heuristic scoring'],
                      [<Target size={16}/>, 'Feature Sentiment', 'Aspect-level extraction + confidence'],
                    ].map(([icon, name, desc]) => (
                      <div key={name} style={{ display: 'flex', gap: '10px', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '13px' }}>
                        <span style={{ fontSize: '16px' }}>{icon}</span>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{name}</div>
                          <div style={{ color: 'var(--text-tertiary)' }}>{desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Last Ingestion Result */}
              {lastResult && (
                <div className="card" style={{ marginTop: '24px', borderColor: 'rgba(16,185,129,0.3)' }}>
                  <div className="card-header">
                    <div className="card-title" style={{ color: 'var(--accent-emerald)' }}><CheckCircle size={18} className="card-title-icon"/> Last Ingestion Summary</div>
                  </div>
                  <div className="result-grid">
                    {[
                      ['Processed', lastResult.total_processed],
                      ['Duplicates', lastResult.duplicates_found],
                      ['Bot Flagged', lastResult.suspicious_flagged],
                      ['Ambiguous', lastResult.ambiguous_flagged],
                      ['Clusters', lastResult.clusters_created],
                    ].map(([label, val]) => (
                      <div key={label} className="result-stat">
                        <div className="result-val">{val ?? 0}</div>
                        <div className="result-label">{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </>
  )
}

// ─── Review Table Row ─────────────────────────────────────────
function ReviewRow({ review, index }) {
  const [expanded, setExpanded] = useState(false)
  const sentColor = {
    very_positive: '#10b981', positive: '#34d399',
    neutral: 'var(--text-tertiary)',
    negative: '#fb7185', very_negative: '#f43f5e',
    mixed: '#fbbf24'
  }
  return (
    <>
      <tr onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>
        <td style={{ color: 'var(--text-tertiary)', fontSize: '12px' }}>{index + 1}</td>
        <td>
          <div className="review-text-cell" style={{ maxWidth: '340px', whiteSpace: expanded ? 'normal' : 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {review.original_text}
          </div>
        </td>
        <td><span className="badge badge-lang" style={{ fontSize: '10px' }}>{review.product_category || '—'}</span></td>
        <td><span className="badge badge-lang">{review.detected_language?.toUpperCase()}</span></td>
        <td>
          <span style={{ fontSize: '12px', fontWeight: 600, color: sentColor[review.sentiment_label] || 'var(--text-secondary)' }}>
            {review.sentiment_label?.replace('_', ' ') || '—'}
          </span>
        </td>
        <td><FakeScore score={review.fake_score || 0} /></td>
        <td>
          {review.bot_probability > 0.5
            ? <span className="badge badge-bot"><Bot size={12} style={{marginRight: 4}}/> Bot</span>
            : review.is_duplicate
              ? <span className="badge badge-duplicate"><Copy size={12} style={{marginRight: 4}}/> Dup</span>
              : <span className="badge badge-clean"><CheckCircle size={12} style={{marginRight: 4}}/> Clean</span>
          }
        </td>
        <td style={{ color: 'var(--accent-amber)' }}>{review.rating ? '★'.repeat(Math.round(review.rating)) : '—'}</td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={8}>
            <div className="expanded-review-details">
              {review.translated_text && (
                <div className="translated-box">
                  <strong>Translated:</strong> {review.translated_text}
                </div>
              )}
              {(review.preprocessing_notes || []).length > 0 && (
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '10px' }}>
                  {(review.preprocessing_notes || []).map((n, i) => (
                    <span key={i} className="badge badge-lang" style={{ fontSize: '10px' }}>{n}</span>
                  ))}
                </div>
              )}
              <div className="aspect-pills">
                {(review.features || []).map((f, idx) => (
                  <span key={idx} className={`aspect-pill ${f.sentiment}`}>
                    {f.feature.replace('_', ' ')}
                    <span className="pill-conf"> {(f.confidence * 100).toFixed(0)}%</span>
                    {f.sentiment === 'positive' ? <ThumbsUp size={14} style={{marginLeft: 4, display: 'inline', verticalAlign: 'middle'}}/> : f.sentiment === 'negative' ? <ThumbsDown size={14} style={{marginLeft: 4, display: 'inline', verticalAlign: 'middle'}}/> : <Minus size={14} style={{marginLeft: 4, display: 'inline', verticalAlign: 'middle'}}/>}
                  </span>
                ))}
              </div>
              {(review.fake_flags || []).length > 0 && (
                <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(review.fake_flags || []).map((flag, i) => (
                    <span key={i} className="badge badge-bot" style={{ fontSize: '10px' }}>{flag}</span>
                  ))}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default App
