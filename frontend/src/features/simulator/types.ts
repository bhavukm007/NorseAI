export const riskCategories = [
  "Privacy",
  "Security",
  "Fairness",
  "Transparency",
  "Accountability",
  "Regulatory Compliance",
] as const;

export type RiskCategory = (typeof riskCategories)[number];
export type RuleStatus = "Passed" | "Warning" | "Failed";
export type Severity = "Critical" | "High" | "Medium" | "Low";
export type Decision = "Approved" | "Approved with Conditions" | "High Risk" | "Rejected";

export interface SystemSubmission {
  systemName: string;
  organization: string;
  industry: string;
  modelType: string;
  deploymentType: string;
  region: string;
  description: string;
  intendedUse: string;
  trainingDataSource: string;
  dataCategories: string;
  sensitiveData: "Yes" | "No";
  humanOversight: "Yes" | "No";
}

export interface GovernanceRule {
  name: string;
  status: RuleStatus;
  severity: Severity;
  description: string;
  recommendation: string;
}

export interface Recommendation {
  priority: Severity;
  title: string;
  detail: string;
}

export interface Assessment {
  id: string;
  createdAt: string;
  submission: SystemSubmission;
  riskScore: number;
  riskLevel: string;
  confidence: number;
  categories: Record<RiskCategory, number>;
  rules: GovernanceRule[];
  recommendations: Recommendation[];
  compliance: number;
  decision: Decision;
}
