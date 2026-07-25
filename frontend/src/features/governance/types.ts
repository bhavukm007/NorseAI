export type AgentStatus = "enabled" | "disabled" | "suspended";
export type GovernanceStatus = "enabled" | "disabled" | "emergency_stopped";

export interface Agent {
  id: string;
  name: string;
  description: string;
  owner_id: string | null;
  fleet_id: string | null;
  agent_type: string;
  status: AgentStatus;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  status: GovernanceStatus;
}

export interface Fleet {
  id: string;
  organization_id: string;
  name: string;
  status: GovernanceStatus;
  created_at: string;
  updated_at: string;
}

export interface Policy {
  id: string;
  name: string;
  effect: "allow" | "deny" | "conditional";
  resource: string;
  action: string;
  conditions: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  allows_uncapped_spend: boolean;
}

export interface Permission {
  id: string;
  agent_id: string;
  policy_id: string;
}

export interface SpendLimit {
  id: string;
  agent_id?: string;
  fleet_id?: string;
  organization_id?: string;
  period: "transaction" | "daily" | "monthly";
  amount: string;
  currency: string;
}

export interface FinancialAction {
  id: string;
  request_id: string;
  agent_id: string;
  fleet_id: string;
  organization_id: string;
  action_type: "payment" | "transfer" | "refund";
  amount: string;
  currency: string;
  status: "rejected" | "settled" | "reversed";
  allowed: boolean;
  reason: string;
  timestamp: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  username: string;
  agent_reference: string | null;
  fleet_id: string | null;
  organization_id: string | null;
  action: string;
  resource: string;
  result: string;
  policy_reference: string | null;
  request_id: string | null;
  amount: string | null;
  currency: string | null;
  policy_decision: string | null;
  spend_decision: string | null;
  execution_result: string | null;
  correlation_id: string | null;
  metadata_json: Record<string, unknown>;
  decision_context: Record<string, unknown>;
  policy_version: string | null;
}

export interface Overview {
  active_agents: number;
  active_fleets: number;
  active_policies: number;
  emergency_fleets: number;
  budget_limit: string;
  settled_spend: string;
  reserved_spend: string;
  recent_decisions: FinancialAction[];
  recent_audits: AuditLog[];
}
