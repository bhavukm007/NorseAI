import type {
  Assessment,
  GovernanceRule,
  Recommendation,
  RiskCategory,
  Severity,
  SystemSubmission,
} from "./types";
import { riskCategories } from "./types";

export const pipelineStages = [
  "Collecting metadata",
  "Classifying AI system",
  "Identifying applicable regulations",
  "Running governance rules",
  "Calculating risk",
  "Detecting violations",
  "Generating recommendations",
  "Preparing executive report",
] as const;

const categoryBase: Record<RiskCategory, number> = {
  Privacy: 30,
  Security: 25,
  Fairness: 30,
  Transparency: 28,
  Accountability: 24,
  "Regulatory Compliance": 26,
};

function bound(value: number) {
  return Math.max(5, Math.min(96, Math.round(value)));
}

function makeRule(
  name: string,
  status: GovernanceRule["status"],
  severity: Severity,
  description: string,
  recommendation: string,
): GovernanceRule {
  return { name, status, severity, description, recommendation };
}

export function assessSystem(submission: SystemSubmission): Assessment {
  const text =
    `${submission.description} ${submission.intendedUse} ${submission.dataCategories}`.toLowerCase();
  const sensitive = submission.sensitiveData === "Yes";
  const oversight = submission.humanOversight === "Yes";
  const biometric = /facial|biometric|health|medical/.test(text);
  const consequential = /credit|hiring|vehicle|diagnos|employment/.test(text);
  const publicDeployment = /public|cloud|edge/.test(submission.deploymentType.toLowerCase());

  const categories = Object.fromEntries(
    riskCategories.map((category) => {
      let score = categoryBase[category];
      if (sensitive && category === "Privacy") score += 34;
      if (publicDeployment && category === "Security") score += 24;
      if (consequential && category === "Fairness") score += 28;
      if (!oversight && category === "Accountability") score += 38;
      if (/black box|deep learning|neural/.test(text) && category === "Transparency") score += 27;
      if ((biometric || consequential) && category === "Regulatory Compliance") score += 32;
      return [category, bound(score)];
    }),
  ) as Record<RiskCategory, number>;

  const rules: GovernanceRule[] = [
    makeRule(
      "Sensitive data safeguards",
      sensitive ? "Warning" : "Passed",
      sensitive ? "High" : "Low",
      sensitive
        ? "The system processes sensitive or regulated information."
        : "No sensitive data processing was declared.",
      sensitive
        ? "Encrypt sensitive information at rest and in transit."
        : "Retain current controls.",
    ),
    makeRule(
      "Meaningful human oversight",
      oversight ? "Passed" : "Failed",
      oversight ? "Low" : "Critical",
      oversight
        ? "A human review path is included in the operating model."
        : "No human review or intervention path was declared.",
      oversight
        ? "Test escalation procedures quarterly."
        : "Add qualified human review before consequential decisions.",
    ),
    makeRule(
      "Bias and fairness evaluation",
      consequential ? "Warning" : "Passed",
      consequential ? "High" : "Low",
      consequential
        ? "The intended use may materially affect individuals or protected groups."
        : "The declared use has limited direct impact on individual rights.",
      consequential
        ? "Benchmark outcomes across demographic cohorts and improve dataset diversity."
        : "Continue periodic fairness testing.",
    ),
    makeRule(
      "Explainability documentation",
      /deep learning|neural|facial/.test(text) ? "Failed" : "Warning",
      /deep learning|neural|facial/.test(text) ? "High" : "Medium",
      "Model cards, decision rationale, and user-facing explanations require verification.",
      "Document model limitations and provide explanations appropriate to affected users.",
    ),
    makeRule(
      "Security monitoring",
      publicDeployment ? "Warning" : "Passed",
      publicDeployment ? "Medium" : "Low",
      publicDeployment
        ? "Externally reachable deployment increases the attack surface."
        : "The deployment boundary limits external exposure.",
      "Enable immutable audit logging and continuous anomaly monitoring.",
    ),
    makeRule(
      "Post-deployment monitoring",
      "Warning",
      "Medium",
      "Continuous performance and drift controls were not evidenced in the submission.",
      "Add monitoring after deployment with incident thresholds and named owners.",
    ),
  ];

  const failed = rules.filter((rule) => rule.status === "Failed").length;
  const warnings = rules.filter((rule) => rule.status === "Warning").length;
  const compliance = Math.round(((rules.length - failed - warnings * 0.45) / rules.length) * 100);
  const riskScore = Math.round(
    riskCategories.reduce((total, category) => total + categories[category], 0) /
      riskCategories.length,
  );
  const riskLevel =
    riskScore >= 75 ? "Critical" : riskScore >= 55 ? "High" : riskScore >= 35 ? "Moderate" : "Low";
  const decision: Assessment["decision"] =
    riskScore >= 78 || failed >= 3
      ? "Rejected"
      : riskScore >= 63
        ? "High Risk"
        : failed || warnings >= 2
          ? "Approved with Conditions"
          : "Approved";

  const recommendations: Recommendation[] = rules
    .filter((rule) => rule.status !== "Passed")
    .map((rule) => ({
      priority: rule.severity,
      title: rule.recommendation.split(".")[0],
      detail: `${rule.name}: ${rule.description}`,
    }));
  recommendations.push({
    priority: "Low",
    title: "Document the governance process",
    detail: "Maintain an accountable decision log, control owners, evidence, and review cadence.",
  });

  return {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    submission,
    riskScore,
    riskLevel,
    confidence: 92,
    categories,
    rules,
    recommendations,
    compliance,
    decision,
  };
}
