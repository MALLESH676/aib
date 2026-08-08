import { useState, useEffect, useCallback } from 'react';
import {
  api,
  type AnalysisCase,
  type AgentSignal,
  type SuspiciousAttribute,
  type AuditEntry,
} from '../api/client';

interface InvestigateProps {
  caseId: string;
  onBack: () => void;
  onActionSuccess: () => void;
}

/* ── Helpers ────────────────────────────────────────────── */
function severityClass(s: string): string {
  switch (s.toUpperCase()) {
    case 'CRITICAL': return 'critical';
    case 'HIGH':     return 'high';
    case 'MEDIUM':   return 'medium';
    default:         return 'low';
  }
}

function severityColor(s: string): string {
  switch (s.toUpperCase()) {
    case 'CRITICAL': return 'var(--hold-color)';
    case 'HIGH':     return 'var(--accent-amber)';
    case 'MEDIUM':   return 'var(--accent-cyan)';
    default:         return 'var(--text-muted)';
  }
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

/* ── Score Circle (SVG) ─────────────────────────────────── */
interface ScoreCircleProps {
  score: number;
  size?: number;
  label?: string;
}

function ScoreCircle({ score, size = 72, label }: ScoreCircleProps) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = scoreColor(score);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} style={{ filter: `drop-shadow(0 0 8px ${color}88)` }}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.07)"
          strokeWidth="5"
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />
        <text
          x={size / 2}
          y={size / 2 + 5}
          textAnchor="middle"
          fill={color}
          fontSize={size * 0.22}
          fontWeight="800"
          fontFamily="Inter, sans-serif"
        >
          {Math.round(score)}
        </text>
      </svg>
      {label && <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{label}</span>}
    </div>
  );
}

/* ── Signal List ────────────────────────────────────────── */
function SignalList({ signals }: { signals: AgentSignal[] }) {
  if (!signals?.length) return <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No signals detected.</div>;
  return (
    <div className="signal-list">
      {signals.map((sig, i) => (
        <div key={i} className={`signal-item ${severityClass(sig.severity)}`}>
          <div className="signal-body">
            <div className="signal-name">{sig.signal}</div>
            <div className="signal-detail">{sig.detail}</div>
            {typeof sig.value !== 'undefined' && (
              <div className="signal-detail" style={{ color: 'var(--text-muted)', marginTop: 2 }}>
                value: <strong style={{ color: 'var(--text-secondary)' }}>{String(sig.value)}</strong>
              </div>
            )}
          </div>
          <div className="signal-right">
            <span className={`signal-severity severity-${severityClass(sig.severity)}`}>{sig.severity}</span>
            <span className="signal-weight">w={sig.weight.toFixed(2)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Suspicious Attributes ──────────────────────────────── */
function AttrList({ attrs }: { attrs: SuspiciousAttribute[] }) {
  if (!attrs?.length) return <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>No suspicious attributes.</div>;
  return (
    <div className="attr-list">
      {attrs.map((a, i) => (
        <div key={i} className="attr-item">
          <div className="attr-dot" style={{ background: severityColor(a.severity) }} />
          <div className="attr-body">
            <div className="attr-name">{a.attribute}</div>
            <div className="attr-detail">{a.detail}</div>
          </div>
          <span
            className="signal-severity"
            style={{ color: severityColor(a.severity), marginLeft: 'auto', flexShrink: 0, fontSize: 10, fontWeight: 700 }}
          >
            {a.severity}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── Confidence Bar ─────────────────────────────────────── */
function ConfidenceBar({ value, label }: { value: number; label?: string }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? 'var(--allow-color)' : pct >= 60 ? 'var(--review-color)' : 'var(--hold-color)';
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>{label ?? 'Confidence'}</span>
        <span style={{ fontSize: 14, fontWeight: 800, color }}>{pct}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

/* ── Risk Agent Card ────────────────────────────────────── */
function RiskAgentCard({ data }: { data: AnalysisCase['risk_agent_output'] }) {
  const cls =
    data.risk_score >= 70 ? 'risk-high' :
    data.risk_score >= 40 ? 'risk-medium' : 'risk-low';

  return (
    <div className="agent-card">
      <div className="agent-card-header">
        <div>
          <div className="agent-name">Risk Agent</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Behavioural Analysis</div>
        </div>
        <span className="agent-tag">{data.model_version}</span>
      </div>

      <div className="agent-score-block">
        <ScoreCircle score={data.risk_score} size={80} label="risk" />
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>CATEGORY</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{data.risk_category}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{data.latency_ms.toFixed(0)}ms</div>
        </div>
      </div>

      <ConfidenceBar value={data.confidence} />

      <div>
        <div className="section-title">Signals ({data.signals?.length ?? 0})</div>
        <SignalList signals={data.signals ?? []} />
      </div>

      <div>
        <div className="section-title">Recommendation</div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '6px 12px', borderRadius: 8,
          background: `rgba(${data.risk_score >= 70 ? '244,63,94' : data.risk_score >= 40 ? '245,158,11' : '16,185,129'},0.1)`,
          border: `1px solid rgba(${data.risk_score >= 70 ? '244,63,94' : data.risk_score >= 40 ? '245,158,11' : '16,185,129'},0.3)`,
          fontSize: 12, fontWeight: 700, color: scoreColor(data.risk_score),
        }}>
          {data.recommendation}
        </div>
      </div>

      <div>
        <div className="section-title">Analysis</div>
        <div className="explanation-box">{data.explanation}</div>
      </div>
    </div>
  );
}

/* ── Auth Agent Card ────────────────────────────────────── */
function AuthAgentCard({ data }: { data: AnalysisCase['auth_agent_output'] }) {
  const img = data.image_analysis;
  return (
    <div className="agent-card">
      <div className="agent-card-header">
        <div>
          <div className="agent-name">Authenticity Agent</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Counterfeit Detection</div>
        </div>
        <span className="agent-tag">{data.model_version}</span>
      </div>

      <div className="agent-score-block">
        <ScoreCircle score={data.risk_score} size={80} label="risk" />
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>COUNTERFEIT PROB.</div>
          <div style={{
            fontSize: 22, fontWeight: 800,
            color: scoreColor(data.counterfeit_probability * 100),
          }}>
            {(data.counterfeit_probability * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{data.latency_ms.toFixed(0)}ms</div>
        </div>
      </div>

      <ConfidenceBar value={data.confidence} />

      {img && (
        <div>
          <div className="section-title">Image Analysis</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div className="stat-pill">
              <span className="stat-pill-value" style={{ fontSize: 15, fontWeight: 700 }}>{img.logo_consistency}</span>
              <span className="stat-pill-label">Logo Consistency</span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-value">{(img.image_quality_score * 100).toFixed(0)}%</span>
              <span className="stat-pill-label">Image Quality</span>
            </div>
            <div className="stat-pill" style={{ gridColumn: '1/-1' }}>
              <span className="stat-pill-value" style={{ color: img.similar_known_counterfeits > 0 ? 'var(--hold-color)' : 'var(--allow-color)' }}>
                {img.similar_known_counterfeits}
              </span>
              <span className="stat-pill-label">Known Counterfeits Matched</span>
            </div>
          </div>
          {img.notes && (
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {img.notes}
            </div>
          )}
        </div>
      )}

      <div>
        <div className="section-title">Suspicious Attributes ({data.suspicious_attributes?.length ?? 0})</div>
        <AttrList attrs={data.suspicious_attributes ?? []} />
      </div>

      <div>
        <div className="section-title">Analysis</div>
        <div className="explanation-box">{data.explanation}</div>
      </div>
    </div>
  );
}

/* ── Review Agent Card ──────────────────────────────────── */
function ReviewAgentCard({ data }: { data: AnalysisCase['review_agent_output'] }) {
  const ca = data.cluster_analysis;
  const rs = data.rating_stats;
  return (
    <div className="agent-card">
      <div className="agent-card-header">
        <div>
          <div className="agent-name">Review Agent</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Manipulation Detection</div>
        </div>
        <span className="agent-tag">{data.model_version}</span>
      </div>

      <div className="agent-score-block">
        <ScoreCircle score={data.risk_score} size={80} label="risk" />
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>MANIPULATION PROB.</div>
          <div style={{
            fontSize: 22, fontWeight: 800,
            color: scoreColor(data.manipulation_probability * 100),
          }}>
            {(data.manipulation_probability * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{data.latency_ms.toFixed(0)}ms</div>
        </div>
      </div>

      <ConfidenceBar value={data.confidence} />

      {rs && (
        <div>
          <div className="section-title">Rating Stats</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div className="stat-pill">
              <span className="stat-pill-value">⭐ {rs.avg_rating.toFixed(1)}</span>
              <span className="stat-pill-label">Avg Rating</span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-value" style={{ color: rs.five_star_rate > 0.8 ? 'var(--hold-color)' : 'var(--allow-color)' }}>
                {(rs.five_star_rate * 100).toFixed(0)}%
              </span>
              <span className="stat-pill-label">5-Star Rate</span>
            </div>
            <div className="stat-pill" style={{ gridColumn: '1/-1' }}>
              <span className="stat-pill-value" style={{ color: rs.review_velocity > 10 ? 'var(--hold-color)' : 'var(--text-primary)' }}>
                {rs.review_velocity.toFixed(1)}/min
              </span>
              <span className="stat-pill-label">Review Velocity ({rs.velocity_window_minutes}min window)</span>
            </div>
          </div>
        </div>
      )}

      {ca && (
        <div>
          <div className="section-title">Cluster Analysis</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
            <div className="stat-pill">
              <span className="stat-pill-value" style={{ color: ca.suspicious_clusters > 0 ? 'var(--hold-color)' : 'var(--allow-color)' }}>
                {ca.suspicious_clusters}
              </span>
              <span className="stat-pill-label">Suspicious Clusters</span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill-value">{ca.cluster_size}</span>
              <span className="stat-pill-label">Cluster Size</span>
            </div>
            <div className="stat-pill" style={{ gridColumn: '1/-1' }}>
              <span className="stat-pill-value" style={{ color: ca.network_density > 0.7 ? 'var(--hold-color)' : 'var(--allow-color)' }}>
                {(ca.network_density * 100).toFixed(0)}%
              </span>
              <span className="stat-pill-label">Network Density</span>
            </div>
          </div>
          {ca.linked_accounts?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 600 }}>LINKED ACCOUNTS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {ca.linked_accounts.map((acc, i) => (
                  <span key={i} className="chip" style={{
                    background: 'rgba(244,63,94,0.1)', color: 'var(--hold-color)',
                    borderColor: 'rgba(244,63,94,0.2)',
                  }}>
                    {acc}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div>
        <div className="section-title">Signals ({data.signals?.length ?? 0})</div>
        <SignalList signals={data.signals ?? []} />
      </div>

      <div>
        <div className="section-title">Analysis</div>
        <div className="explanation-box">{data.explanation}</div>
      </div>
    </div>
  );
}

/* ── Fusion Section ─────────────────────────────────────── */
function FusionSection({ c }: { c: AnalysisCase }) {
  const bars = [
    { label: 'Risk Agent',          score: c.risk_agent_output.risk_score,    weight: 0.45, color: 'var(--hold-color)' },
    { label: 'Auth Agent',          score: c.auth_agent_output.risk_score,    weight: 0.30, color: 'var(--accent-amber)' },
    { label: 'Review Agent',        score: c.review_agent_output.risk_score,  weight: 0.25, color: 'var(--accent-purple)' },
  ];

  return (
    <div className="card mb-24">
      <div className="section-title">Fusion Score Breakdown</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>FUSION SCORE</div>
          <div style={{ fontSize: 48, fontWeight: 900, color: scoreColor(c.fusion_score), lineHeight: 1 }}>
            {c.fusion_score.toFixed(2)}
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          {bars.map((b) => (
            <div key={b.label} className="fusion-bar-row">
              <div className="fusion-bar-label">{b.label}</div>
              <div className="fusion-bar-container">
                <div className="fusion-bar-track">
                  <div className="fusion-bar-fill" style={{ width: `${b.score}%`, background: b.color }} />
                </div>
                <div className="fusion-bar-weight" style={{ color: b.color }}>weight: {(b.weight * 100).toFixed(0)}%</div>
              </div>
              <div className="fusion-bar-score" style={{ color: b.color }}>{b.score.toFixed(0)}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div className="stat-pill">
          <span className="stat-pill-value" style={{ color: 'var(--allow-color)' }}>
            {c.overall_trust_score.toFixed(0)}
          </span>
          <span className="stat-pill-label">Trust Score</span>
        </div>
        <div className="stat-pill">
          <span className="stat-pill-value" style={{ color: scoreColor(c.overall_risk_score) }}>
            {c.overall_risk_score.toFixed(0)}
          </span>
          <span className="stat-pill-label">Risk Score</span>
        </div>
        <div className="stat-pill">
          <span className="stat-pill-value">{(c.confidence * 100).toFixed(0)}%</span>
          <span className="stat-pill-label">Confidence</span>
        </div>
        <div className="stat-pill">
          <span className="stat-pill-value" style={{ color: 'var(--accent-cyan)' }}>
            {c.latency_ms.toFixed(0)}ms
          </span>
          <span className="stat-pill-label">Total Latency</span>
        </div>
      </div>
    </div>
  );
}

/* ── Policy Decision Box ────────────────────────────────── */
function PolicyDecisionBox({ c }: { c: AnalysisCase }) {
  const isHold = c.decision === 'HOLD';
  return (
    <div className={`card mb-24 ${isHold ? 'pulse-hold' : ''}`} style={{
      borderColor: isHold
        ? 'rgba(244,63,94,0.4)'
        : c.decision === 'REVIEW'
          ? 'rgba(245,158,11,0.3)'
          : 'rgba(16,185,129,0.3)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>POLICY DECISION</div>
          <span className={`badge badge-lg ${decisionClass(c.decision)}`}>
            <span className="badge-dot" />
            {c.decision}
          </span>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6 }}>REASON</div>
          <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>{c.decision_reason}</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 6 }}>HUMAN STATUS</div>
          <div style={{
            fontSize: 13, fontWeight: 700,
            color: c.human_status === 'pending'
              ? 'var(--review-color)'
              : c.human_status === 'actioned'
                ? 'var(--allow-color)'
                : 'var(--text-muted)',
          }}>
            {c.human_status?.toUpperCase() ?? 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Human Action Panel ─────────────────────────────────── */
interface ActionPanelProps {
  c: AnalysisCase;
  onActionSuccess: () => void;
  onRefreshCase: () => void;
}

function HumanActionPanel({ c, onActionSuccess, onRefreshCase }: ActionPanelProps) {
  const [notes, setNotes] = useState('');
  const [investigator, setInvestigator] = useState('');
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const takeAction = async (action: string) => {
    if (!investigator.trim()) { setSubmitError('Please enter your investigator name.'); return; }
    setSubmitting(action);
    setSubmitError(null);
    try {
      await api.takeAction(c.id, action, notes, investigator);
      onActionSuccess();
      onRefreshCase();
    } catch (e) {
      setSubmitError(String(e));
    } finally {
      setSubmitting(null);
    }
  };

  /* Already actioned */
  if (c.human_status === 'actioned' && c.human_action) {
    return (
      <div className="action-panel">
        <div className="action-panel-header">
          <span style={{ fontSize: 18 }}>✅</span>
          <div>
            <div className="action-panel-title">Action Recorded</div>
            <div className="action-panel-subtitle">Investigated by {c.human_investigator || 'Unknown'}</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div className="detail-item">
            <div className="detail-item-label">Action Taken</div>
            <div className="detail-item-value" style={{ color: 'var(--allow-color)', fontWeight: 700, fontSize: 16 }}>
              {c.human_action}
            </div>
          </div>
          {c.human_notes && (
            <div className="detail-item">
              <div className="detail-item-label">Notes</div>
              <div className="detail-item-value">{c.human_notes}</div>
            </div>
          )}
          {c.human_timestamp && (
            <div className="detail-item">
              <div className="detail-item-label">Timestamp</div>
              <div className="detail-item-value">{new Date(c.human_timestamp).toLocaleString()}</div>
            </div>
          )}
        </div>
      </div>
    );
  }

  /* Not pending — no action required */
  if (c.human_status !== 'pending') {
    return null;
  }

  return (
    <div className="action-panel">
      <div className="action-panel-header">
        <span style={{ fontSize: 22 }}>🔎</span>
        <div>
          <div className="action-panel-title">Human Review Required</div>
          <div className="action-panel-subtitle">
            This case requires investigator review. Choose an action below.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div className="input-group">
          <label className="input-label">Investigator Name *</label>
          <input
            className="investigator-input"
            placeholder="Enter your name"
            value={investigator}
            onChange={(e) => setInvestigator(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label className="input-label">Case Severity</label>
          <div style={{ display: 'flex', alignItems: 'center', height: 38 }}>
            <span className={`badge badge-lg ${decisionClass(c.decision)}`}>
              <span className="badge-dot" />
              {c.decision}
            </span>
          </div>
        </div>
      </div>

      <div className="input-group mb-12">
        <label className="input-label">Investigation Notes</label>
        <textarea
          className="notes-input"
          placeholder="Enter your findings, observations, or rationale…"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {submitError && (
        <div style={{
          padding: '10px 14px', marginBottom: 12,
          background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)',
          borderRadius: 8, fontSize: 13, color: 'var(--hold-color)',
        }}>
          {submitError}
        </div>
      )}

      <div className="action-buttons">
        <button
          className="btn btn-success"
          onClick={() => takeAction('approve')}
          disabled={submitting !== null}
        >
          {submitting === 'approve' ? <span className="spinner spinner-sm" /> : '✅'}
          Approve
        </button>
        <button
          className="btn btn-danger"
          onClick={() => takeAction('reject')}
          disabled={submitting !== null}
        >
          {submitting === 'reject' ? <span className="spinner spinner-sm" /> : '❌'}
          Reject
        </button>
        <button
          className="btn btn-amber"
          onClick={() => takeAction('escalate')}
          disabled={submitting !== null}
        >
          {submitting === 'escalate' ? <span className="spinner spinner-sm" /> : '⬆️'}
          Escalate
        </button>
        <button
          className="btn btn-cyan"
          onClick={() => takeAction('request_evidence')}
          disabled={submitting !== null}
        >
          {submitting === 'request_evidence' ? <span className="spinner spinner-sm" /> : '🔍'}
          Request Evidence
        </button>
      </div>
    </div>
  );
}

/* ── Audit Log Timeline ──────────────────────────────────── */
function AuditTimeline({ entries }: { entries: AuditEntry[] }) {
  if (!entries?.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <div className="empty-state-title">No audit entries</div>
      </div>
    );
  }

  return (
    <div className="audit-timeline">
      {[...entries].reverse().map((entry) => (
        <div key={entry.id} className="audit-item">
          <div className="audit-header">
            <div>
              <div className="audit-actor">{entry.actor}</div>
              <div className="audit-action">{entry.action}</div>
            </div>
            <div className="audit-time">{new Date(entry.timestamp).toLocaleString()}</div>
          </div>
          {entry.detail && Object.keys(entry.detail).length > 0 && (
            <div className="audit-detail">
              {Object.entries(entry.detail)
                .filter(([, v]) => v !== null && v !== '')
                .map(([k, v]) => `${k}: ${String(v)}`)
                .join(' · ')}
            </div>
          )}
          <div className="audit-confidence">
            {entry.model_version && (
              <span style={{ color: 'var(--accent-purple-light)', marginRight: 8 }}>{entry.model_version}</span>
            )}
            {entry.confidence > 0 && `Confidence: ${(entry.confidence * 100).toFixed(0)}%`}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Investigate Page ───────────────────────────────────── */
export function Investigate({ caseId, onBack, onActionSuccess }: InvestigateProps) {
  const [caseData, setCaseData] = useState<AnalysisCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCase = useCallback(() => {
    setLoading(true);
    api.getCase(caseId)
      .then(setCaseData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [caseId]);

  useEffect(() => { fetchCase(); }, [fetchCase]);

  if (loading) {
    return (
      <div className="loading-center" style={{ minHeight: '60vh' }}>
        <div className="spinner" />
        Loading case {caseId.slice(0, 8)}…
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="error-state" style={{ minHeight: '60vh' }}>
        <div className="error-state-icon">⚠</div>
        <div className="error-state-title">Failed to load case</div>
        <div className="error-state-desc">{error}</div>
        <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={onBack}>
          ← Back
        </button>
      </div>
    );
  }

  const c = caseData;

  return (
    <div className="fade-in">
      {/* Back button */}
      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-ghost btn-sm" onClick={onBack}>
          ← Back to Cases
        </button>
      </div>

      {/* ── Case Hero ── */}
      <div className="case-hero">
        <div className="case-hero-left">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <span className="chip">{c.scenario_label}</span>
            <span className="chip" style={{ background: 'rgba(6,182,212,0.1)', color: 'var(--accent-cyan)', borderColor: 'rgba(6,182,212,0.2)' }}>
              {c.case_type}
            </span>
          </div>
          <div className="case-hero-entity">{c.entity_id}</div>
          <div className="case-hero-meta" style={{ marginTop: 8 }}>
            <span className={`badge badge-lg ${decisionClass(c.decision)}`}>
              <span className="badge-dot" />
              {c.decision}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {new Date(c.created_at).toLocaleString()}
            </span>
            <span style={{ fontSize: 12, color: 'var(--accent-cyan)' }}>
              {c.latency_ms.toFixed(0)}ms total
            </span>
          </div>
          {c.summary && (
            <div style={{ marginTop: 14, fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, maxWidth: 560 }}>
              {c.summary}
            </div>
          )}
        </div>

        <div className="case-hero-right">
          <div className="case-hero-stat">
            <div
              className="case-hero-stat-value"
              style={{ color: scoreColor(c.overall_risk_score) }}
            >
              {c.overall_risk_score.toFixed(0)}
            </div>
            <div className="case-hero-stat-label">Risk Score</div>
          </div>

          <div style={{ width: 1, height: 60, background: 'var(--border)' }} />

          <div className="case-hero-stat">
            <div
              className="case-hero-stat-value"
              style={{ color: 'var(--allow-color)' }}
            >
              {c.overall_trust_score.toFixed(0)}
            </div>
            <div className="case-hero-stat-label">Trust Score</div>
          </div>

          <div style={{ width: 1, height: 60, background: 'var(--border)' }} />

          <div className="case-hero-stat">
            <div className="case-hero-stat-value" style={{ fontSize: 28, color: 'var(--text-primary)' }}>
              {(c.confidence * 100).toFixed(0)}%
            </div>
            <div className="case-hero-stat-label">Confidence</div>
          </div>
        </div>
      </div>

      {/* ── Policy Decision ── */}
      <PolicyDecisionBox c={c} />

      {/* ── Agent Cards ── */}
      <div className="section-title" style={{ marginBottom: 16 }}>Agent Analysis</div>
      <div className="agent-grid mb-24">
        <RiskAgentCard data={c.risk_agent_output} />
        <AuthAgentCard data={c.auth_agent_output} />
        <ReviewAgentCard data={c.review_agent_output} />
      </div>

      {/* ── Fusion ── */}
      <FusionSection c={c} />

      {/* ── Human Action ── */}
      <div className="mb-24">
        <div className="section-title" style={{ marginBottom: 16 }}>Human Review</div>
        <HumanActionPanel
          c={c}
          onActionSuccess={onActionSuccess}
          onRefreshCase={fetchCase}
        />
      </div>

      {/* ── Audit Log ── */}
      <div className="card">
        <div className="section-title">Audit Trail ({c.audit_log?.length ?? 0} entries)</div>
        <AuditTimeline entries={c.audit_log ?? []} />
      </div>

      {/* Bottom spacer */}
      <div style={{ height: 40 }} />
    </div>
  );
}
