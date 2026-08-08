import { useState, useEffect, useRef, useCallback } from 'react';
import { api, type DashboardStats, type AnalysisCase } from '../api/client';

interface DashboardProps {
  onRunDemo: (caseId: string) => void;
  onCaseClick: (caseId: string) => void;
}

/* ── Animated counter hook ─────────────────────────────── */
function useCountUp(target: number, duration = 900, decimals = 0): string {
  const [current, setCurrent] = useState(0);
  const rafRef = useRef<number>();
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    startRef.current = null;
    const start = 0;
    const step = (timestamp: number) => {
      if (!startRef.current) startRef.current = timestamp;
      const progress = Math.min((timestamp - startRef.current) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      setCurrent(start + (target - start) * ease);
      if (progress < 1) rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return decimals > 0 ? current.toFixed(decimals) : Math.round(current).toString();
}

/* ── Score color helper ─────────────────────────────────── */
function scoreColor(score: number): string {
  if (score >= 70) return 'var(--hold-color)';
  if (score >= 40) return 'var(--review-color)';
  return 'var(--allow-color)';
}

function decisionClass(d: string): string {
  switch (d) {
    case 'ALLOW':  return 'badge-allow';
    case 'REVIEW': return 'badge-review';
    case 'HOLD':   return 'badge-hold';
    default:       return 'badge-pending';
  }
}

/* ── Metric Card ───────────────────────────────────────── */
interface MetricCardProps {
  label: string;
  value: number;
  suffix?: string;
  color?: string;
  decimals?: number;
  sub?: string;
  icon: string;
  iconBg: string;
}

function MetricCard({ label, value, suffix = '', color, decimals = 0, sub, icon, iconBg }: MetricCardProps) {
  const display = useCountUp(value, 900, decimals);
  return (
    <div className="metric-card">
      <div className="metric-card-icon" style={{ background: iconBg }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
      </div>
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={color ? { color } : {}}>
        {display}{suffix}
      </div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

/* ── Demo Scenario Buttons ──────────────────────────────── */
interface DemoButtonsProps {
  onRun: (caseId: string) => void;
}

function DemoButtons({ onRun }: DemoButtonsProps) {
  const [running, setRunning] = useState<'A' | 'B' | 'C' | null>(null);
  const [error, setError] = useState<string | null>(null);

  const scenarios: { key: 'A' | 'B' | 'C'; title: string; desc: string; label: string; labelClass: string }[] = [
    {
      key: 'A',
      title: 'Trusted Seller',
      desc: 'Legitimate merchant with clean history, authentic products, and organic reviews.',
      label: 'Scenario A — ALLOW',
      labelClass: 'demo-label-a',
    },
    {
      key: 'B',
      title: 'Fraudulent Seller',
      desc: 'Counterfeit goods, botnet reviews, account cluster fraud. High-confidence HOLD.',
      label: 'Scenario B — HOLD',
      labelClass: 'demo-label-b',
    },
    {
      key: 'C',
      title: 'Suspicious Seller',
      desc: 'Mixed signals: some review anomalies, minor pricing inconsistencies. Needs human review.',
      label: 'Scenario C — REVIEW',
      labelClass: 'demo-label-c',
    },
  ];

  const run = async (scenario: 'A' | 'B' | 'C') => {
    setRunning(scenario);
    setError(null);
    try {
      const result = await api.runDemo(scenario);
      onRun(result.id);
    } catch (e) {
      setError(`Failed to run scenario ${scenario}: ${String(e)}`);
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="mb-24">
      <div className="section-title">Live Demo Scenarios</div>
      <div className="demo-grid">
        {scenarios.map((s) => (
          <button
            key={s.key}
            className="demo-btn"
            onClick={() => run(s.key)}
            disabled={running !== null}
          >
            <div className="demo-btn-inner">
              <div className={`demo-btn-label ${s.labelClass}`}>
                {running === s.key ? '⏳ Running…' : s.label}
              </div>
              <div className="demo-btn-title">{s.title}</div>
              <div className="demo-btn-desc">{s.desc}</div>
            </div>
          </button>
        ))}
      </div>
      {error && (
        <div style={{
          padding: '12px 16px',
          background: 'rgba(244,63,94,0.1)',
          border: '1px solid rgba(244,63,94,0.3)',
          borderRadius: 8,
          fontSize: 13,
          color: 'var(--hold-color)',
        }}>
          {error}
        </div>
      )}
    </div>
  );
}

/* ── Custom Case Form ───────────────────────────────────── */
function CustomCaseForm({ onRun }: { onRun: (caseId: string) => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states (with reasonable default values)
  const [amount, setAmount] = useState(2500);
  const [paymentMethod, setPaymentMethod] = useState<'COD' | 'card' | 'wallet'>('card');
  const [returnRate, setReturnRate] = useState(0.05);
  const [codRefusalRate, setCodRefusalRate] = useState(0.02);
  const [linkedAccounts, setLinkedAccounts] = useState(1);
  const [vpn, setVpn] = useState(false);
  const [emulator, setEmulator] = useState(false);
  
  const [sellerAge, setSellerAge] = useState(365);
  const [sellerSales, setSellerSales] = useState(150);
  const [disputeRate, setDisputeRate] = useState(0.02);
  const [authorized, setAuthorized] = useState(true);
  
  const [productTitle, setProductTitle] = useState('Premium Sneakers');
  const [productBrand, setProductBrand] = useState('Nike');
  const [price, setPrice] = useState(5000);
  const [msrp, setMsrp] = useState(5000);
  const [reviewCount, setReviewCount] = useState(0);
  const [reviewsSimilarity, setReviewsSimilarity] = useState<'low' | 'high'>('low');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Prepare Pydantic-compatible payload structure
    const payload = {
      event_id: `evt_custom_${Date.now()}`,
      case_type: 'transaction',
      customer: {
        id: `cust_${Math.random().toString(36).substring(2, 11)}`,
        account_age_days: 90,
        total_orders: 10,
        total_returns: Math.round(10 * returnRate),
        return_rate: returnRate,
        cod_refusal_rate: codRefusalRate,
        linked_device_count: linkedAccounts,
        linked_account_count: linkedAccounts,
      },
      transaction: {
        id: `txn_${Math.random().toString(36).substring(2, 11)}`,
        amount: amount,
        payment_method: paymentMethod,
        is_first_time_buyer: false,
        orders_last_24h: 1,
        orders_last_7d: 3,
        status: 'completed',
      },
      seller: {
        id: `seller_${Math.random().toString(36).substring(2, 11)}`,
        name: 'Custom Marketplace Seller',
        account_age_days: sellerAge,
        total_sales: sellerSales,
        avg_rating: 4.2,
        dispute_rate: disputeRate,
        is_new_seller: sellerAge < 30,
        brand_authorized: authorized,
      },
      product: {
        id: `prod_${Math.random().toString(36).substring(2, 11)}`,
        title: productTitle,
        description: 'Custom product listing created from dashboard.',
        brand: productBrand,
        category: 'apparel',
        price: price,
        msrp: msrp,
        image_url: '',
        listing_age_days: 10,
      },
      device: {
        id: `dev_${Math.random().toString(36).substring(2, 11)}`,
        linked_accounts: linkedAccounts,
        vpn_detected: vpn,
        emulator_detected: emulator,
      },
      reviews: reviewCount > 0 ? Array.from({ length: reviewCount }).map((_, i) => ({
        id: `rev_custom_${i}`,
        customer_id: `cust_rev_${i}`,
        rating: 5,
        text: reviewsSimilarity === 'high' ? 'Amazing product! Best seller recommend!' : `Good item number ${i}, shipping was fine.`,
        timestamp: new Date().toISOString(),
        verified_purchase: true,
      })) : [],
      review_window_hours: 24,
      scenario_label: 'Custom',
    };

    try {
      const res = await api.analyze(payload);
      onRun(res.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card mb-24" style={{ border: '1px solid var(--border-bright)' }}>
      <div className="section-title">✨ Create Custom Case Analysis</div>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        {/* Customer & Transaction */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-purple-light)' }}>CUSTOMER & TXN</div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Amount (₹)</label>
            <input className="notes-input" type="number" value={amount} onChange={e => setAmount(Number(e.target.value))} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Payment Method</label>
            <select className="notes-input" style={{ width: '100%' }} value={paymentMethod} onChange={e => setPaymentMethod(e.target.value as any)}>
              <option value="card">Card</option>
              <option value="wallet">Wallet</option>
              <option value="COD">COD (Cash on Delivery)</option>
            </select>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Return Rate</label>
              <input className="notes-input" type="number" step="0.05" min="0" max="1" value={returnRate} onChange={e => setReturnRate(Number(e.target.value))} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>COD Refusal</label>
              <input className="notes-input" type="number" step="0.05" min="0" max="1" value={codRefusalRate} onChange={e => setCodRefusalRate(Number(e.target.value))} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <input type="checkbox" checked={vpn} onChange={e => setVpn(e.target.checked)} /> VPN
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <input type="checkbox" checked={emulator} onChange={e => setEmulator(e.target.checked)} /> Emulator
            </label>
          </div>
        </div>

        {/* Product & Authenticity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-cyan)' }}>PRODUCT & SELLER</div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Brand Name</label>
            <input className="notes-input" type="text" value={productBrand} onChange={e => setProductBrand(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Price (₹)</label>
              <input className="notes-input" type="number" value={price} onChange={e => setPrice(Number(e.target.value))} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>MSRP (₹)</label>
              <input className="notes-input" type="number" value={msrp} onChange={e => setMsrp(Number(e.target.value))} />
            </div>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Seller Account Age (Days)</label>
            <input className="notes-input" type="number" value={sellerAge} onChange={e => setSellerAge(Number(e.target.value))} />
          </div>
          <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
              <input type="checkbox" checked={authorized} onChange={e => setAuthorized(e.target.checked)} /> Authorized Seller
            </label>
          </div>
        </div>

        {/* Reviews & Submission */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-amber)' }}>REVIEWS & TRIGGER</div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Reviews to analyze</label>
            <input className="notes-input" type="number" min="0" max="20" value={reviewCount} onChange={e => setReviewCount(Number(e.target.value))} />
          </div>
          {reviewCount > 0 && (
            <div>
              <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>Review text similarity</label>
              <select className="notes-input" style={{ width: '100%' }} value={reviewsSimilarity} onChange={e => setReviewsSimilarity(e.target.value as any)}>
                <option value="low">Organic/Low similarity</option>
                <option value="high">Coordinated/High similarity</option>
              </select>
            </div>
          )}
          <div style={{ flexGrow: 1 }} />
          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', justifyContent: 'center' }}
            disabled={loading}
            type="submit"
          >
            {loading ? 'Analyzing Custom Case...' : '⚡ Run custom analysis'}
          </button>
        </div>
      </form>
      {error && (
        <div style={{
          marginTop: 12, padding: '10px 12px',
          background: 'rgba(244,63,94,0.08)',
          border: '1px solid rgba(244,63,94,0.2)',
          borderRadius: 8, fontSize: 12, color: 'var(--hold-color)',
        }}>
          {error}
        </div>
      )}
    </div>
  );
}

/* ── Recent Cases Table ─────────────────────────────────── */
interface RecentCasesProps {
  cases: AnalysisCase[];
  onCaseClick: (id: string) => void;
}

function RecentCasesTable({ cases, onCaseClick }: RecentCasesProps) {
  if (cases.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <div className="empty-state-title">No recent cases</div>
        <div className="empty-state-desc">Run a demo scenario above to generate your first case analysis.</div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Entity ID</th>
            <th>Decision</th>
            <th>Risk Score</th>
            <th>Fusion Score</th>
            <th>Latency</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr key={c.id} onClick={() => onCaseClick(c.id)}>
              <td>
                <span className="chip">{c.scenario_label}</span>
              </td>
              <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                {c.entity_id}
              </td>
              <td>
                <span className={`badge ${decisionClass(c.decision)}`}>
                  <span className="badge-dot" />
                  {c.decision}
                </span>
              </td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: scoreColor(c.overall_risk_score), fontWeight: 800, fontSize: 15 }}>
                    {c.overall_risk_score.toFixed(0)}
                  </span>
                  <div style={{ flex: 1, minWidth: 60 }}>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${c.overall_risk_score}%`,
                          background: scoreColor(c.overall_risk_score),
                        }}
                      />
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {c.fusion_score.toFixed(2)}
                </span>
              </td>
              <td>
                <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                  {c.latency_ms.toFixed(0)}ms
                </span>
              </td>
              <td style={{ fontSize: 12 }}>
                {new Date(c.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Decision Distribution Bar ──────────────────────────── */
function DecisionBar({ stats }: { stats: DashboardStats }) {
  const total = stats.total_cases || 1;
  const segments = [
    { label: 'ALLOW',  count: stats.allowed,      color: 'var(--allow-color)',  pct: (stats.allowed / total) * 100 },
    { label: 'REVIEW', count: stats.under_review,  color: 'var(--review-color)', pct: (stats.under_review / total) * 100 },
    { label: 'HOLD',   count: stats.held,          color: 'var(--hold-color)',   pct: (stats.held / total) * 100 },
  ];

  return (
    <div>
      <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', gap: 2, marginBottom: 10 }}>
        {segments.map((s) => (
          <div
            key={s.label}
            style={{
              width: `${s.pct}%`,
              background: s.color,
              borderRadius: 5,
              transition: 'width 0.8s ease',
              minWidth: s.count > 0 ? 4 : 0,
            }}
          />
        ))}
      </div>
      <div style={{ display: 'flex', gap: 16, justifyContent: 'space-between' }}>
        {segments.map((s) => (
          <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: s.color }} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>{s.label}</span>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 700 }}>{s.count}</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>({s.pct.toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Dashboard Page ─────────────────────────────────────── */
export function Dashboard({ onRunDemo, onCaseClick }: DashboardProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [cases, setCases] = useState<AnalysisCase[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingCases, setLoadingCases] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchStats = useCallback(() => {
    api.getDashboardStats()
      .then((s) => { setStats(s); setStatsError(null); })
      .catch((e) => setStatsError(String(e)))
      .finally(() => setLoadingStats(false));
  }, []);

  const fetchCases = useCallback(() => {
    api.listCases()
      .then((c) => setCases(c.slice(0, 10)))
      .catch(() => {})
      .finally(() => setLoadingCases(false));
  }, []);

  useEffect(() => {
    fetchStats();
    fetchCases();
  }, [fetchStats, fetchCases]);

  /* Auto-refresh every 30 s */
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStats();
      fetchCases();
      setLastRefresh(new Date());
    }, 30_000);
    return () => clearInterval(interval);
  }, [fetchStats, fetchCases]);

  const handleDemoRun = (caseId: string) => {
    /* Re-fetch immediately after demo */
    setTimeout(() => {
      fetchStats();
      fetchCases();
    }, 500);
    onRunDemo(caseId);
  };

  return (
    <div className="fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Dashboard</h1>
          <p>Real-time trust &amp; safety intelligence • Last updated {lastRefresh.toLocaleTimeString()}</p>
        </div>
        <div className="page-header-actions">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => { fetchStats(); fetchCases(); setLastRefresh(new Date()); }}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Demo Buttons */}
      <DemoButtons onRun={handleDemoRun} />

      {/* Custom Case Form */}
      <CustomCaseForm onRun={handleDemoRun} />

      {/* Stats Error */}
      {statsError && (
        <div style={{
          padding: '12px 16px', marginBottom: 16,
          background: 'rgba(244,63,94,0.08)',
          border: '1px solid rgba(244,63,94,0.2)',
          borderRadius: 8, fontSize: 13, color: 'var(--hold-color)',
        }}>
          ⚠ Could not fetch dashboard stats: {statsError}
        </div>
      )}

      {/* Metrics Grid */}
      {loadingStats ? (
        <div className="loading-center" style={{ minHeight: 120 }}>
          <div className="spinner" />
          Loading metrics…
        </div>
      ) : stats ? (
        <>
          <div className="metrics-grid">
            <MetricCard
              label="Total Cases"
              value={stats.total_cases}
              icon="📊"
              iconBg="rgba(139,92,246,0.15)"
              color="var(--accent-purple-light)"
              sub="all-time"
            />
            <MetricCard
              label="Allowed"
              value={stats.allowed}
              icon="✅"
              iconBg="rgba(16,185,129,0.15)"
              color="var(--allow-color)"
              sub="auto-approved"
            />
            <MetricCard
              label="Under Review"
              value={stats.under_review}
              icon="🔍"
              iconBg="rgba(245,158,11,0.15)"
              color="var(--review-color)"
              sub="pending human"
            />
            <MetricCard
              label="Held"
              value={stats.held}
              icon="🛑"
              iconBg="rgba(244,63,94,0.15)"
              color="var(--hold-color)"
              sub="blocked"
            />
            <MetricCard
              label="Queue Size"
              value={stats.human_review_queue}
              icon="⏳"
              iconBg="rgba(6,182,212,0.15)"
              color="var(--accent-cyan)"
              sub="awaiting action"
            />
            <MetricCard
              label="Avg Risk Score"
              value={stats.avg_risk_score}
              icon="📈"
              iconBg="rgba(245,158,11,0.12)"
              color={scoreColor(stats.avg_risk_score)}
              decimals={1}
              sub="out of 100"
            />
            <MetricCard
              label="Detection Rate"
              value={stats.detection_rate * 100}
              suffix="%"
              icon="🎯"
              iconBg="rgba(16,185,129,0.12)"
              color="var(--accent-green)"
              decimals={1}
              sub="fraud caught"
            />
            <MetricCard
              label="Automation"
              value={stats.automation_rate * 100}
              suffix="%"
              icon="⚡"
              iconBg="rgba(139,92,246,0.12)"
              color="var(--accent-purple-light)"
              decimals={1}
              sub="no human needed"
            />
          </div>

          {/* Decision Distribution */}
          <div className="card mb-24">
            <div className="section-title">Decision Distribution</div>
            <DecisionBar stats={stats} />
            <div className="divider" />
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>AVG LATENCY</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {stats.avg_latency_ms.toFixed(0)}ms
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>ANALYSIS ENGINE</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>3-Agent Fusion v1</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Risk · Auth · Review</div>
              </div>
            </div>
          </div>
        </>
      ) : null}

      {/* Recent Cases */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div className="section-title" style={{ margin: 0, flex: 1 }}>Recent Cases</div>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Click any row to investigate</span>
        </div>
        {loadingCases ? (
          <div className="loading-center">
            <div className="spinner" />
            Loading cases…
          </div>
        ) : (
          <RecentCasesTable cases={cases} onCaseClick={onCaseClick} />
        )}
      </div>
    </div>
  );
}
