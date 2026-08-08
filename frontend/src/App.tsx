import { useState, useEffect, useCallback } from 'react';
import './index.css';
import { Dashboard } from './pages/Dashboard';
import { Investigate } from './pages/Investigate';
import { Queue } from './pages/Queue';
import { AuditLog } from './pages/AuditLog';
import { api } from './api/client';

type Page = 'dashboard' | 'cases' | 'queue' | 'audit';

/* ── Inline SVG Icons ──────────────────────────────────── */
function IconGrid() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function IconList() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="9" y1="6" x2="20" y2="6" />
      <line x1="9" y1="12" x2="20" y2="12" />
      <line x1="9" y1="18" x2="20" y2="18" />
      <circle cx="4" cy="6" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="4" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="4" cy="18" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconClock() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 15.5 14.5" />
    </svg>
  );
}

function IconFile() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="16" y2="17" />
    </svg>
  );
}

function IconShield() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L4 5v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V5L12 2z" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

/* ── Toast ─────────────────────────────────────────────── */
interface ToastState {
  message: string;
  type: 'success' | 'error' | 'info';
}

/* ── App ───────────────────────────────────────────────── */
export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [queueCount, setQueueCount] = useState<number>(0);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  /* Check API health */
  useEffect(() => {
    api.health()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false));
  }, []);

  /* Fetch queue count for badge */
  const refreshQueueCount = useCallback(() => {
    api.getQueue()
      .then((cases) => setQueueCount(cases.length))
      .catch(() => {});
  }, []);

  useEffect(() => {
    refreshQueueCount();
    const interval = setInterval(refreshQueueCount, 30_000);
    return () => clearInterval(interval);
  }, [refreshQueueCount]);

  /* Toast helper */
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  /* Navigation helpers */
  const navigateToCase = useCallback((caseId: string) => {
    setActiveCaseId(caseId);
    setPage('cases');
  }, []);

  const navigateTo = useCallback((p: Page) => {
    setPage(p);
    if (p !== 'cases') setActiveCaseId(null);
  }, []);

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-inner">
            <div className="sidebar-logo-icon">
              <IconShield />
            </div>
            <h1>TrustShield</h1>
          </div>
          <p>Trust &amp; Safety Platform</p>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">Main</div>

          <button
            className={`nav-item ${page === 'dashboard' ? 'active' : ''}`}
            onClick={() => navigateTo('dashboard')}
          >
            <IconGrid />
            <span>Dashboard</span>
          </button>

          <button
            className={`nav-item ${page === 'cases' ? 'active' : ''}`}
            onClick={() => navigateTo('cases')}
          >
            <IconList />
            <span>All Cases</span>
          </button>

          <div className="nav-section-label" style={{ marginTop: 8 }}>Operations</div>

          <button
            className={`nav-item ${page === 'queue' ? 'active' : ''}`}
            onClick={() => navigateTo('queue')}
          >
            <IconClock />
            <span>Review Queue</span>
            {queueCount > 0 && (
              <span className="nav-badge">{queueCount}</span>
            )}
          </button>

          <button
            className={`nav-item ${page === 'audit' ? 'active' : ''}`}
            onClick={() => navigateTo('audit')}
          >
            <IconFile />
            <span>Audit Log</span>
          </button>
        </nav>

        {/* Footer / status */}
        <div className="sidebar-footer">
          <div className="status-dot-row">
            <div
              className="status-dot"
              style={{
                background: apiOnline === null
                  ? 'var(--accent-amber)'
                  : apiOnline
                    ? 'var(--accent-green)'
                    : 'var(--hold-color)',
              }}
            />
            <span>
              {apiOnline === null ? 'Connecting…' : apiOnline ? 'API Online' : 'API Offline'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="main-content">
        {page === 'dashboard' && (
          <Dashboard
            onRunDemo={(caseId) => {
              navigateToCase(caseId);
              refreshQueueCount();
              showToast('Demo scenario executed — viewing case.', 'success');
            }}
            onCaseClick={navigateToCase}
          />
        )}

        {page === 'cases' && !activeCaseId && (
          <AllCasesBrowser onCaseClick={navigateToCase} />
        )}

        {page === 'cases' && activeCaseId && (
          <Investigate
            caseId={activeCaseId}
            onBack={() => setActiveCaseId(null)}
            onActionSuccess={() => {
              refreshQueueCount();
              showToast('Action recorded successfully.', 'success');
            }}
          />
        )}

        {page === 'queue' && (
          <Queue
            onCaseClick={navigateToCase}
            onRefresh={refreshQueueCount}
          />
        )}

        {page === 'audit' && <AuditLog />}
      </main>

      {/* ── Toast ── */}
      {toast && (
        <div
          className={`toast ${
            toast.type === 'success'
              ? 'toast-success'
              : toast.type === 'error'
                ? 'toast-error'
                : ''
          }`}
        >
          <span style={{ fontSize: 16 }}>
            {toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : 'ℹ️'}
          </span>
          {toast.message}
        </div>
      )}
    </div>
  );
}

/* ── All Cases Browser (inline) ────────────────────────── */
interface AllCasesBrowserProps {
  onCaseClick: (id: string) => void;
}

function AllCasesBrowser({ onCaseClick }: AllCasesBrowserProps) {
  const [cases, setCases] = useState<import('./api/client').AnalysisCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    api.listCases()
      .then(setCases)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const decisionClass = (d: string) => {
    switch (d) {
      case 'ALLOW':  return 'badge-allow';
      case 'REVIEW': return 'badge-review';
      case 'HOLD':   return 'badge-hold';
      default:       return 'badge-pending';
    }
  };

  const scoreColor = (s: number) =>
    s >= 70 ? 'var(--hold-color)' : s >= 40 ? 'var(--review-color)' : 'var(--allow-color)';

  const filtered = filter
    ? cases.filter((c) => c.decision === filter)
    : cases;

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-header-left">
          <h1>All Cases</h1>
          <p>Complete history of analysed entities</p>
        </div>
        <div className="page-header-actions">
          {(['', 'ALLOW', 'REVIEW', 'HOLD'] as const).map((f) => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilter(f)}
            >
              {f || 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-center">
            <div className="spinner" />
            Loading cases…
          </div>
        ) : error ? (
          <div className="error-state">
            <div className="error-state-icon">⚠</div>
            <div className="error-state-title">Failed to load cases</div>
            <div className="error-state-desc">{error}</div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📂</div>
            <div className="empty-state-title">No cases found</div>
            <div className="empty-state-desc">Run a demo scenario to generate your first case.</div>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Scenario</th>
                  <th>Entity</th>
                  <th>Decision</th>
                  <th>Risk Score</th>
                  <th>Confidence</th>
                  <th>Latency</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id} onClick={() => onCaseClick(c.id)}>
                    <td style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--accent-purple-light)' }}>
                      {c.id.slice(0, 8)}…
                    </td>
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
                      <span style={{ color: scoreColor(c.overall_risk_score), fontWeight: 700, fontSize: 14 }}>
                        {c.overall_risk_score.toFixed(0)}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>/100</span>
                    </td>
                    <td>{(c.confidence * 100).toFixed(0)}%</td>
                    <td>{c.latency_ms.toFixed(0)}ms</td>
                    <td>{new Date(c.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
