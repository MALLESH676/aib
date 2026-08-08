import { useState, useEffect, useCallback } from 'react';
import { api, type AnalysisCase } from '../api/client';

interface QueueProps {
  onCaseClick: (caseId: string) => void;
  onRefresh?: () => void;
}

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

function timeSince(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

/* ── Priority Badge ─────────────────────────────────────── */
function PriorityBadge({ score }: { score: number }) {
  if (score >= 80) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        padding: '3px 8px', borderRadius: 4,
        background: 'rgba(244,63,94,0.15)', color: 'var(--hold-color)',
        border: '1px solid rgba(244,63,94,0.3)',
        fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px',
      }}>
        🔴 P1 CRITICAL
      </span>
    );
  }
  if (score >= 60) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        padding: '3px 8px', borderRadius: 4,
        background: 'rgba(245,158,11,0.15)', color: 'var(--accent-amber)',
        border: '1px solid rgba(245,158,11,0.3)',
        fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px',
      }}>
        🟡 P2 HIGH
      </span>
    );
  }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 8px', borderRadius: 4,
      background: 'rgba(6,182,212,0.15)', color: 'var(--accent-cyan)',
      border: '1px solid rgba(6,182,212,0.3)',
      fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px',
    }}>
      🔵 P3 MEDIUM
    </span>
  );
}

/* ── Queue Card ─────────────────────────────────────────── */
function QueueCard({ c, onClick }: { c: AnalysisCase; onClick: () => void }) {
  const riskScore = c.overall_risk_score;
  const borderColor = riskScore >= 70
    ? 'rgba(244,63,94,0.35)'
    : riskScore >= 40
      ? 'rgba(245,158,11,0.25)'
      : 'var(--border)';

  return (
    <div
      className="card fade-in"
      onClick={onClick}
      style={{
        borderColor,
        cursor: 'pointer',
        transition: 'all 0.2s',
        marginBottom: 12,
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)';
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 8px 32px rgba(0,0,0,0.4)';
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
        (e.currentTarget as HTMLDivElement).style.boxShadow = 'none';
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
        {/* Left: score circle */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, flexShrink: 0 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            border: `3px solid ${scoreColor(riskScore)}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 0 16px ${scoreColor(riskScore)}44`,
            flexShrink: 0,
          }}>
            <span style={{ fontSize: 20, fontWeight: 900, color: scoreColor(riskScore) }}>
              {riskScore.toFixed(0)}
            </span>
          </div>
          <span style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>risk</span>
        </div>

        {/* Center: info */}
        <div style={{ flex: 1, minWidth: 180 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>{c.entity_id}</span>
            <PriorityBadge score={riskScore} />
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
            <span className={`badge ${decisionClass(c.decision)}`}>
              <span className="badge-dot" />
              {c.decision}
            </span>
            <span className="chip">{c.scenario_label}</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              🕐 {timeSince(c.created_at)}
            </span>
          </div>
          {c.summary && (
            <div style={{
              fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5,
              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {c.summary}
            </div>
          )}
        </div>

        {/* Right: agent scores */}
        <div style={{ display: 'flex', gap: 12, flexShrink: 0, flexWrap: 'wrap' }}>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ fontSize: 16, color: scoreColor(c.risk_agent_output.risk_score) }}>
              {c.risk_agent_output.risk_score.toFixed(0)}
            </span>
            <span className="stat-pill-label">Risk</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ fontSize: 16, color: scoreColor(c.auth_agent_output.risk_score) }}>
              {c.auth_agent_output.risk_score.toFixed(0)}
            </span>
            <span className="stat-pill-label">Auth</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ fontSize: 16, color: scoreColor(c.review_agent_output.risk_score) }}>
              {c.review_agent_output.risk_score.toFixed(0)}
            </span>
            <span className="stat-pill-label">Review</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingLeft: 8 }}>
            <span style={{ fontSize: 12, color: 'var(--accent-cyan)', fontWeight: 600 }}>
              {c.latency_ms.toFixed(0)}ms
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>latency</span>
          </div>
        </div>

        {/* Arrow */}
        <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', flexShrink: 0, alignSelf: 'center' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>
    </div>
  );
}

/* ── Queue Stats Bar ────────────────────────────────────── */
function QueueStatsBar({ cases }: { cases: AnalysisCase[] }) {
  const critical = cases.filter((c) => c.overall_risk_score >= 80).length;
  const high     = cases.filter((c) => c.overall_risk_score >= 60 && c.overall_risk_score < 80).length;
  const medium   = cases.filter((c) => c.overall_risk_score < 60).length;
  const hold     = cases.filter((c) => c.decision === 'HOLD').length;
  const review   = cases.filter((c) => c.decision === 'REVIEW').length;

  return (
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
      <div className="stat-pill">
        <span className="stat-pill-value" style={{ color: 'var(--hold-color)' }}>{critical}</span>
        <span className="stat-pill-label">P1 Critical</span>
      </div>
      <div className="stat-pill">
        <span className="stat-pill-value" style={{ color: 'var(--accent-amber)' }}>{high}</span>
        <span className="stat-pill-label">P2 High</span>
      </div>
      <div className="stat-pill">
        <span className="stat-pill-value" style={{ color: 'var(--accent-cyan)' }}>{medium}</span>
        <span className="stat-pill-label">P3 Medium</span>
      </div>
      <div style={{ width: 1, background: 'var(--border)', margin: '0 4px' }} />
      <div className="stat-pill">
        <span className="stat-pill-value" style={{ color: 'var(--hold-color)' }}>{hold}</span>
        <span className="stat-pill-label">HOLD</span>
      </div>
      <div className="stat-pill">
        <span className="stat-pill-value" style={{ color: 'var(--review-color)' }}>{review}</span>
        <span className="stat-pill-label">REVIEW</span>
      </div>
    </div>
  );
}

/* ── Queue Page ─────────────────────────────────────────── */
export function Queue({ onCaseClick, onRefresh }: QueueProps) {
  const [cases, setCases] = useState<AnalysisCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'risk' | 'time'>('risk');

  const fetchQueue = useCallback(() => {
    setLoading(true);
    api.getQueue()
      .then((data) => { setCases(data); setError(null); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const handleRefresh = () => {
    fetchQueue();
    onRefresh?.();
  };

  const sorted = [...cases].sort((a, b) => {
    if (sortBy === 'risk') return b.overall_risk_score - a.overall_risk_score;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Review Queue</h1>
          <p>
            {loading ? 'Loading…' : `${cases.length} case${cases.length !== 1 ? 's' : ''} pending human review`}
          </p>
        </div>
        <div className="page-header-actions">
          <button
            className={`btn btn-sm ${sortBy === 'risk' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setSortBy('risk')}
          >
            Sort: Risk ↓
          </button>
          <button
            className={`btn btn-sm ${sortBy === 'time' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setSortBy('time')}
          >
            Sort: Newest
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handleRefresh} disabled={loading}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '12px 16px', marginBottom: 16,
          background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)',
          borderRadius: 8, fontSize: 13, color: 'var(--hold-color)',
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="loading-center">
          <div className="spinner" />
          Loading queue…
        </div>
      ) : cases.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <div className="empty-state-title">Queue is clear</div>
          <div className="empty-state-desc">
            All cases have been reviewed. Run a demo scenario to generate new cases.
          </div>
        </div>
      ) : (
        <>
          {/* Stats */}
          <QueueStatsBar cases={cases} />

          {/* Alert banner for critical cases */}
          {cases.some((c) => c.overall_risk_score >= 80) && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 16px', marginBottom: 16,
              background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.3)',
              borderRadius: 8, animation: 'pulse-ring 2s infinite',
            }}>
              <span style={{ fontSize: 18 }}>🚨</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--hold-color)' }}>
                  Critical Cases Pending
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {cases.filter((c) => c.overall_risk_score >= 80).length} high-risk case(s) require immediate attention.
                </div>
              </div>
            </div>
          )}

          {/* Case Cards */}
          <div>
            {sorted.map((c) => (
              <QueueCard key={c.id} c={c} onClick={() => onCaseClick(c.id)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
