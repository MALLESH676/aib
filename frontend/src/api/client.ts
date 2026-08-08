const BASE_URL = 'http://localhost:8000/api/v1';

export interface AgentSignal {
  signal: string;
  value: number | string;
  weight: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  detail: string;
}

export interface SuspiciousAttribute {
  attribute: string;
  detail: string;
  severity: string;
}

export interface ClusterAnalysis {
  suspicious_clusters: number;
  cluster_size: number;
  network_density: number;
  linked_accounts: string[];
}

export interface RatingStats {
  avg_rating: number;
  five_star_rate: number;
  review_velocity: number;
  velocity_window_minutes: number;
}

export interface ImageAnalysis {
  logo_consistency: string;
  image_quality_score: number;
  similar_known_counterfeits: number;
  notes: string;
}

export interface RiskAgentOutput {
  agent: string;
  risk_score: number;
  risk_category: string;
  signals: AgentSignal[];
  recommendation: string;
  confidence: number;
  explanation: string;
  model_version: string;
  latency_ms: number;
}

export interface AuthAgentOutput {
  agent: string;
  risk_score: number;
  counterfeit_probability: number;
  suspicious_attributes: SuspiciousAttribute[];
  image_analysis: ImageAnalysis;
  recommendation: string;
  confidence: number;
  explanation: string;
  model_version: string;
  latency_ms: number;
}

export interface ReviewAgentOutput {
  agent: string;
  risk_score: number;
  manipulation_probability: number;
  signals: AgentSignal[];
  cluster_analysis: ClusterAnalysis;
  rating_stats: RatingStats;
  recommendation: string;
  confidence: number;
  explanation: string;
  model_version: string;
  latency_ms: number;
}

export interface AnalysisCase {
  id: string;
  case_type: string;
  entity_id: string;
  decision: 'ALLOW' | 'REVIEW' | 'HOLD' | 'PENDING';
  fusion_score: number;
  overall_trust_score: number;
  overall_risk_score: number;
  created_at: string;
  human_status: string;
  scenario_label: string;
  latency_ms: number;
  summary: string;
  risk_agent_output: RiskAgentOutput;
  auth_agent_output: AuthAgentOutput;
  review_agent_output: ReviewAgentOutput;
  decision_reason: string;
  confidence: number;
  human_action: string;
  human_notes: string;
  human_investigator: string;
  human_timestamp: string | null;
  audit_log: AuditEntry[];
}

export interface AuditEntry {
  id: number;
  case_id: string;
  timestamp: string;
  actor: string;
  action: string;
  detail: Record<string, unknown>;
  model_version: string;
  confidence: number;
}

export interface DashboardStats {
  total_cases: number;
  allowed: number;
  under_review: number;
  held: number;
  human_review_queue: number;
  avg_risk_score: number;
  avg_latency_ms: number;
  detection_rate: number;
  automation_rate: number;
  recent_decisions: Array<{ decision: string; score: number; label: string }>;
}

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetchJSON<{ status: string; version: string }>('/health'),
  getDashboardStats: () => fetchJSON<DashboardStats>('/dashboard/stats'),
  listCases: (decision?: string) =>
    fetchJSON<AnalysisCase[]>(`/cases${decision ? `?decision=${decision}` : ''}`),
  getCase: (id: string) => fetchJSON<AnalysisCase>(`/cases/${id}`),
  getQueue: () => fetchJSON<AnalysisCase[]>('/queue'),
  getAuditLog: (caseId?: string) =>
    fetchJSON<AuditEntry[]>(`/audit-log${caseId ? `?case_id=${caseId}` : ''}`),
  runDemo: (scenario: 'A' | 'B' | 'C') =>
    fetchJSON<AnalysisCase>(`/demo/${scenario}`, { method: 'POST' }),
  analyze: (payload: any) =>
    fetchJSON<AnalysisCase>('/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  takeAction: (
    caseId: string,
    action: string,
    notes: string,
    investigator: string
  ) =>
    fetchJSON(`/cases/${caseId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, notes, investigator }),
    }),
};
