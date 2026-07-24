import type { Assessment } from "./types";

const STORAGE_KEY = "norseai.assessments.v1";
const MAX_SAVED_ASSESSMENTS = 50;

function isAssessment(value: unknown): value is Assessment {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<Assessment>;
  return (
    typeof item.id === "string" &&
    typeof item.createdAt === "string" &&
    typeof item.riskScore === "number" &&
    typeof item.compliance === "number" &&
    Array.isArray(item.rules) &&
    Array.isArray(item.recommendations) &&
    typeof item.submission?.systemName === "string"
  );
}

export function loadAssessments(): Assessment[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(value) ? value.filter(isAssessment).slice(0, MAX_SAVED_ASSESSMENTS) : [];
  } catch {
    return [];
  }
}

export function saveAssessments(items: Assessment[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_SAVED_ASSESSMENTS)));
    return true;
  } catch {
    return false;
  }
}

function download(name: string, content: BlobPart, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.rel = "noopener";
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function exportJson(assessment: Assessment) {
  download(
    `${assessment.submission.systemName}-assessment.json`,
    JSON.stringify(assessment, null, 2),
    "application/json",
  );
}

export function exportCsv(assessment: Assessment) {
  const rows = [
    ["Rule", "Status", "Severity", "Description", "Recommendation"],
    ...assessment.rules.map((rule) => [
      rule.name,
      rule.status,
      rule.severity,
      rule.description,
      rule.recommendation,
    ]),
  ];
  const csv = rows
    .map((row) => row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(","))
    .join("\n");
  download(`${assessment.submission.systemName}-findings.csv`, csv, "text/csv;charset=utf-8");
}

export async function exportPdf(assessment: Assessment) {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF();
  const lines = [
    "NorseAI Governance Assessment",
    assessment.submission.systemName,
    "",
    `Organization: ${assessment.submission.organization}`,
    `Assessment date: ${new Date(assessment.createdAt).toLocaleString()}`,
    `Final decision: ${assessment.decision}`,
    `Risk score: ${assessment.riskScore}/100 (${assessment.riskLevel})`,
    `Compliance: ${assessment.compliance}%`,
    "",
    "Executive summary",
    `${assessment.submission.systemName} was assessed against privacy, security, fairness, transparency, accountability, and regulatory controls.`,
    "",
    "Findings",
    ...assessment.rules.map((rule) => `${rule.status} · ${rule.name}: ${rule.description}`),
    "",
    "Recommendations",
    ...assessment.recommendations.map((item) => `${item.priority} · ${item.title}`),
  ];
  const wrapped = lines.flatMap((line) => pdf.splitTextToSize(line, 175) as string[]);
  let y = 18;
  wrapped.forEach((line, index) => {
    if (y > 278) {
      pdf.addPage();
      y = 18;
    }
    pdf.setFont("helvetica", index < 2 ? "bold" : "normal");
    pdf.setFontSize(index === 0 ? 16 : index === 1 ? 13 : 9.5);
    pdf.text(line, 18, y);
    y += index < 2 ? 8 : 5.5;
  });
  pdf.save(`${assessment.submission.systemName}-assessment.pdf`);
}
