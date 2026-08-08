import { useState, useEffect, useCallback } from 'react';
import { api, type AuditEntry } from '../api/client';

/* ── Actor color ────────────────────────────────────────── */
function actorColor(actor: string): string {
  if (actor.toLowerCase().includes('system') || actor.toLowerCase().includes('agent')) {
    return 'var(--accent-purple-light)';
  }
  if (actor.toLowerCase().includes('human') || actor.toLowerCase().includes('investigator')) {
    return 'var(--accent-cyan)';
  }
  return 'var(--accent-amber)';
}

/* ── Action icon ────────────────────────────────────────── */
function actionIcon(action: string): string {
  const a = action.toLowerCase();
  if (a.includes('create') || a.includes('initial')) return '🆕';
  if (a.includes('approve')) return '✅';
  if (a.includes('reject')) return '❌';
  if (a.includes('escalate')) return '⬆️';
  if (a.includes('evidence')) return '🔍';
  if (a.includes('decision')) return '⚖️';
  if (a.includes('hold')) return '🛑';
  if (a.includes('allow')) return '✅';
  if (a.includes('review')) return '🔎';
  if (a.includes('risk')) return '📊';
  if (a.includes('auth')) return '🔐';
  return '📋';
}

/* ── Format detail ──────────────────────────────────────── */
function formatDetail(detail: Record<string, unknown>): string {
  return Object.entries(detail)
    .filter(([, v]) => v !== null && v !== '' && v !== undefined)
    .map(([k, v]) => {
      const key = k.replace(/_/g, ' ');
      if (typeof v === 'number') return `${key}: ${Number.isInteger(v) ? v : (v as number).toFixed(2)}`;
      if (typeof v === 'boolean') return `${key}: ${v ? 'yes' : 'no'}`;
      return `${key}: ${String(v)}`;
    })
    .join(' · ');
}

/* ── Audit Row ──────────────────────────────────────────── */
function AuditRow({ entry }: { entry: AuditEntry }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetail = entry.detail && Object.keys(entry.detail).length > 0;

  return (
    <tr
      style={{ cursor: hasDetail ? 'pointer' : 'default' }}
      onClick={() => hasDetail && setExpanded((v) => !v)}
    >
      <td>
        <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-muted)' }}>
          #{entry.id}
        </span>
      </td>
      <td>
        <span style={{ fontSize: 18 }}>{actionIcon(entry.action)}</span>
      </td>
      <td>
        <span style={{ fontWeight: 700, color: actorColor(entry.actor) }}>
          {entry.actor}
        </span>
      </td>
      <td>
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {entry.action}
        </span>
        {expanded && hasDetail && (
          <div style={{
            marginTop: 6, fontSize: 11, color: 'var(--text-secondary)',
            padding: '8px 10px', background: 'rgba(255,255,255,0.03)',
            borderRadius: 6, lineHeight: 1.6,
          }}>
            {formatDetail(entry.detail)}
          </div>
        )}
      </td>
      <td>
        <span style={{
          fontFamily: 'monospace', fontSize: 11,
          color: 'var(--accent-purple-light)',
        }}>
          {entry.case_id.slice(0, 8)}…
        </span>
      </td>
      <td>
        {entry.confidence > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 48, height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 2,
                width: `${(entry.confidence * 100).toFixed(0)}%`,
                background: entry.confidence >= 0.8
                  ? 'var(--allow-color)'
                  : entry.confidence >= 0.6
                    ? 'var(--review-color)'
                    : 'var(--hold-color)',
              }} />
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {(entry.confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </td>
      <td>
        {entry.model_version && (
          <span className="chip" style={{ fontSize: 10 }}>{entry.model_version}</span>
        )}
      </td>
      <td style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        {new Date(entry.timestamp).toLocaleString()}
      </td>
    </tr>
  );
}

/* ── Filter Controls ────────────────────────────────────── */
interface FilterState {
  actor: string;
  action: string;
}

/* ── AuditLog Page ──────────────────────────────────────── */
export function AuditLog() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterState>({ actor: '', action: '' });
  const [search, setSearch] = useState('');

  const fetchLog = useCallback(() => {
    setLoading(true);
    api.getAuditLog()
      .then((data) => { setEntries(data); setError(null); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchLog(); }, [fetchLog]);

  /* Derived unique values for filter dropdowns */
  const actors  = Array.from(new Set(entries.map((e) => e.actor)));
  const actions = Array.from(new Set(entries.map((e) => e.action)));

  /* Filtered entries */
  const filtered = entries.filter((e) => {
    if (filter.actor  && e.actor  !== filter.actor)  return false;
    if (filter.action && e.action !== filter.action) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        e.actor.toLowerCase().includes(q)  ||
        e.action.toLowerCase().includes(q) ||
        e.case_id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  /* Summary stats */
  const totalSystems = entries.filter((e) => e.actor.toLowerCase().includes('system') || e.actor.toLowerCase().includes('agent')).length;
  const totalHumans  = entries.length - totalSystems;

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Audit Log</h1>
          <p>Full immutable record of all system and human actions</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost btn-sm" onClick={fetchLog} disabled={loading}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Stats Row */}
      {!loading && entries.length > 0 && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ color: 'var(--accent-purple-light)' }}>{entries.length}</span>
            <span className="stat-pill-label">Total Entries</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ color: 'var(--accent-cyan)' }}>{totalSystems}</span>
            <span className="stat-pill-label">AI Actions</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ color: 'var(--accent-amber)' }}>{totalHumans}</span>
            <span className="stat-pill-label">Human Actions</span>
          </div>
          <div className="stat-pill">
            <span className="stat-pill-value" style={{ color: 'var(--allow-color)' }}>
              {Array.from(new Set(entries.map((e) => e.case_id))).length}
            </span>
            <span className="stat-pill-label">Cases</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          className="investigator-input"
          style={{ width: 200 }}
          placeholder="Search actor, action, case ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          style={{
            padding: '9px 12px', borderRadius: 8,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)', fontSize: 13,
            outline: 'none', cursor: 'pointer',
            fontFamily: 'Inter, sans-serif',
          }}
          value={filter.actor}
          onChange={(e) => setFilter((f) => ({ ...f, actor: e.target.value }))}
        >
          <option value="">All Actors</option>
          {actors.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select
          style={{
            padding: '9px 12px', borderRadius: 8,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border)',
            color: 'var(--text-secondary)', fontSize: 13,
            outline: 'none', cursor: 'pointer',
            fontFamily: 'Inter, sans-serif',
          }}
          value={filter.action}
          onChange={(e) => setFilter((f) => ({ ...f, action: e.target.value }))}
        >
          <option value="">All Actions</option>
          {actions.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        {(filter.actor || filter.action || search) && (
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => { setFilter({ actor: '', action: '' }); setSearch(''); }}
          >
            ✕ Clear
          </button>
        )}
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filtered.length} of {entries.length} entries
        </span>
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

      {/* Table */}
      {loading ? (
        <div className="loading-center">
          <div className="spinner" />
          Loading audit log…
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No entries found</div>
          <div className="empty-state-desc">
            {entries.length === 0
              ? 'The audit log is empty. Run a demo to generate entries.'
              : 'No entries match your filters.'}
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container" style={{ border: 'none' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Case</th>
                  <th>Confidence</th>
                  <th>Model</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {[...filtered].reverse().map((entry) => (
                  <AuditRow key={entry.id} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Legend */}
      {!loading && entries.length > 0 && (
        <div style={{
          marginTop: 16, padding: '12px 16px',
          background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)',
          borderRadius: 8, fontSize: 12, color: 'var(--text-muted)',
          display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center',
        }}>
          <span>💡 Click any row with details to expand</span>
          <span style={{ color: 'var(--accent-purple-light)' }}>● AI / System actor</span>
          <span style={{ color: 'var(--accent-cyan)' }}>● Human actor</span>
        </div>
      )}
    </div>
  );
}
