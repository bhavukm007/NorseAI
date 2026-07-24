import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  Clock3,
  Download,
  FileJson,
  FileSpreadsheet,
  FileText,
  History,
  LoaderCircle,
  RotateCcw,
  Scale,
  ShieldCheck,
  Sparkles,
  Trash2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { z } from "zod";

import { assessSystem, pipelineStages } from "./assessment";
import { demoSystems } from "./demoSystems";
import { exportCsv, exportJson, exportPdf, loadAssessments, saveAssessments } from "./storage";
import type { Assessment, RuleStatus, Severity, SystemSubmission } from "./types";
import { riskCategories } from "./types";

const submissionSchema = z.object({
  systemName: z.string().trim().min(2, "Enter the AI system name"),
  organization: z.string().trim().min(2, "Enter the organization name"),
  industry: z.string().min(1, "Select an industry"),
  modelType: z.string().trim().min(2, "Enter the model type"),
  deploymentType: z.string().min(1, "Select a deployment type"),
  region: z.string().min(1, "Select a geographic region"),
  description: z.string().trim().min(20, "Add at least 20 characters"),
  intendedUse: z.string().trim().min(20, "Add at least 20 characters"),
  trainingDataSource: z.string().trim().min(5, "Describe the training data source"),
  dataCategories: z.string().trim().min(3, "List the data categories"),
  sensitiveData: z.enum(["Yes", "No"]),
  humanOversight: z.enum(["Yes", "No"]),
});

type View = "submission" | "pipeline" | "dashboard" | "report" | "history";
const severityOrder: Severity[] = ["Critical", "High", "Medium", "Low"];
const chartColors = ["#d75252", "#d48422", "#7967da", "#13b8a6"];

const fieldOptions = {
  industry: [
    "Healthcare",
    "Financial services",
    "Human resources",
    "Security",
    "Retail",
    "Automotive",
    "Public sector",
    "Other",
  ],
  deploymentType: [
    "Private cloud",
    "Public cloud",
    "Public cloud API",
    "SaaS",
    "On-premises",
    "Edge and public cloud",
    "Vehicle edge",
  ],
  region: ["European Union", "United States", "United Kingdom", "Asia Pacific", "Global"],
};

function StatusIcon({ status }: { status: RuleStatus }) {
  if (status === "Passed") return <CheckCircle2 size={16} />;
  if (status === "Failed") return <XCircle size={16} />;
  return <AlertTriangle size={16} />;
}

function SubmissionForm({
  onSubmit,
  historyCount,
  onHistory,
}: {
  onSubmit: (value: SystemSubmission) => void;
  historyCount: number;
  onHistory: () => void;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SystemSubmission>({
    resolver: zodResolver(submissionSchema),
    defaultValues: { sensitiveData: "No", humanOversight: "Yes" },
  });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <section className="simulator-hero">
        <div>
          <span className="eyebrow">AI governance simulator</span>
          <h1>Assess an AI system end to end</h1>
          <p>
            Classify risk, evaluate controls, and produce an audit-ready governance decision in one
            guided assessment.
          </p>
        </div>
        <button className="secondary-button" type="button" onClick={onHistory}>
          <History size={16} /> Assessment history <span>{historyCount}</span>
        </button>
      </section>

      <section className="sim-card demo-picker">
        <div className="section-heading">
          <div>
            <span className="section-label">Demo library</span>
            <h2>Start with a representative system</h2>
          </div>
          <Sparkles size={19} />
        </div>
        <div className="demo-grid">
          {demoSystems.map((demo) => (
            <button key={demo.systemName} type="button" onClick={() => reset(demo)}>
              <span>{demo.industry}</span>
              <strong>{demo.systemName}</strong>
              <ChevronRight size={15} />
            </button>
          ))}
        </div>
      </section>

      <form className="sim-card assessment-form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="section-heading">
          <div>
            <span className="section-label">System profile</span>
            <h2>Assessment submission</h2>
          </div>
          <span className="required-note">All fields required</span>
        </div>
        <div className="form-grid">
          <label>
            AI system name
            <input {...register("systemName")} aria-invalid={Boolean(errors.systemName)} />
            {errors.systemName && <small>{errors.systemName.message}</small>}
          </label>
          <label>
            Organization name
            <input {...register("organization")} aria-invalid={Boolean(errors.organization)} />
            {errors.organization && <small>{errors.organization.message}</small>}
          </label>
          {Object.entries(fieldOptions).map(([name, options]) => (
            <label key={name}>
              {name === "deploymentType"
                ? "Deployment type"
                : name === "region"
                  ? "Geographic region"
                  : "Industry"}
              <select {...register(name as keyof SystemSubmission)}>
                <option value="">Select an option</option>
                {options.map((option) => (
                  <option key={option}>{option}</option>
                ))}
              </select>
              {errors[name as keyof SystemSubmission] && (
                <small>{errors[name as keyof SystemSubmission]?.message}</small>
              )}
            </label>
          ))}
          <label>
            AI model type
            <input {...register("modelType")} placeholder="e.g. Large language model" />
            {errors.modelType && <small>{errors.modelType.message}</small>}
          </label>
          <label className="form-span">
            Description
            <textarea {...register("description")} rows={3} />
            {errors.description && <small>{errors.description.message}</small>}
          </label>
          <label className="form-span">
            Intended use
            <textarea {...register("intendedUse")} rows={3} />
            {errors.intendedUse && <small>{errors.intendedUse.message}</small>}
          </label>
          <label>
            Training data source
            <input {...register("trainingDataSource")} />
            {errors.trainingDataSource && <small>{errors.trainingDataSource.message}</small>}
          </label>
          <label>
            Data categories used
            <input {...register("dataCategories")} placeholder="Identity, financial, behavioral…" />
            {errors.dataCategories && <small>{errors.dataCategories.message}</small>}
          </label>
          <fieldset>
            <legend>Sensitive data</legend>
            <div className="segmented-control">
              {(["No", "Yes"] as const).map((value) => (
                <label key={value}>
                  <input type="radio" value={value} {...register("sensitiveData")} />
                  <span>{value}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Human oversight</legend>
            <div className="segmented-control">
              {(["Yes", "No"] as const).map((value) => (
                <label key={value}>
                  <input type="radio" value={value} {...register("humanOversight")} />
                  <span>{value}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>
        <div className="form-actions">
          <p>
            <ShieldCheck size={16} /> Submitted information remains in this browser.
          </p>
          <button className="primary-button" disabled={isSubmitting}>
            Run assessment <ArrowRight size={16} />
          </button>
        </div>
      </form>
    </motion.div>
  );
}

function Pipeline({ activeStage, name }: { activeStage: number; name: string }) {
  const progress = Math.round(((activeStage + 1) / pipelineStages.length) * 100);
  return (
    <motion.section className="pipeline-view" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="pipeline-orb">
        <LoaderCircle size={35} />
        <span>{progress}%</span>
      </div>
      <span className="eyebrow">Assessment in progress</span>
      <h1>Evaluating {name}</h1>
      <p>Applying NorseAI governance controls and assembling decision evidence.</p>
      <div className="pipeline-progress" aria-label={`${progress}% complete`}>
        <motion.span animate={{ width: `${progress}%` }} />
      </div>
      <div className="pipeline-list">
        {pipelineStages.map((stage, index) => {
          const complete = index < activeStage;
          const active = index === activeStage;
          return (
            <div className={active ? "active" : complete ? "complete" : ""} key={stage}>
              <span>
                {complete ? (
                  <Check size={15} />
                ) : active ? (
                  <LoaderCircle size={15} />
                ) : (
                  <Circle size={11} />
                )}
              </span>
              <div>
                <strong>{stage}</strong>
                <small>{complete ? "Completed" : active ? "Processing…" : "Queued"}</small>
              </div>
            </div>
          );
        })}
      </div>
    </motion.section>
  );
}

function Ring({ value, label }: { value: number; label: string }) {
  return (
    <div className="score-ring" style={{ "--score": `${value * 3.6}deg` } as React.CSSProperties}>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

function AssessmentDashboard({
  assessment,
  onReport,
  onReset,
}: {
  assessment: Assessment;
  onReport: () => void;
  onReset: () => void;
}) {
  const counts = {
    passed: assessment.rules.filter((rule) => rule.status === "Passed").length,
    warning: assessment.rules.filter((rule) => rule.status === "Warning").length,
    failed: assessment.rules.filter((rule) => rule.status === "Failed").length,
    critical: assessment.rules.filter((rule) => rule.severity === "Critical").length,
  };
  const categoryData = riskCategories.map((category) => ({
    category: category === "Regulatory Compliance" ? "Regulatory" : category,
    risk: assessment.categories[category],
    safety: 100 - assessment.categories[category],
  }));
  const severityData = severityOrder.map((severity) => ({
    severity,
    count: assessment.rules.filter((rule) => rule.severity === severity).length,
  }));
  const trendData = [38, 45, 41, 52, 47, assessment.riskScore].map((risk, index) => ({
    assessment: `A${index + 1}`,
    risk,
  }));

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="results-view">
      <section className="results-header">
        <div>
          <span className="eyebrow">Assessment complete</span>
          <h1>{assessment.submission.systemName}</h1>
          <p>
            {assessment.submission.organization} · {assessment.submission.industry} ·{" "}
            {assessment.submission.region}
          </p>
        </div>
        <div className="results-actions">
          <button className="secondary-button" onClick={onReset}>
            <RotateCcw size={15} /> New assessment
          </button>
          <button className="primary-button" onClick={onReport}>
            <FileText size={15} /> Executive report
          </button>
        </div>
      </section>

      <section className="risk-overview">
        <div className="sim-card risk-score-card">
          <span className="section-label">Overall risk score</span>
          <Ring value={assessment.riskScore} label="/ 100" />
          <span className={`tone-badge severity-${assessment.riskLevel.toLowerCase()}`}>
            {assessment.riskLevel} risk
          </span>
          <small>{assessment.confidence}% assessment confidence</small>
        </div>
        <div className="sim-card risk-categories">
          <div className="section-heading">
            <div>
              <span className="section-label">Control domains</span>
              <h2>Category breakdown</h2>
            </div>
            <BarChart3 size={18} />
          </div>
          {riskCategories.map((category) => (
            <div className="risk-row" key={category}>
              <span>{category}</span>
              <div>
                <motion.span
                  initial={{ width: 0 }}
                  animate={{ width: `${assessment.categories[category]}%` }}
                />
              </div>
              <strong>{assessment.categories[category]}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="kpi-grid">
        <div>
          <span>Compliance</span>
          <strong>{assessment.compliance}%</strong>
          <small>Weighted control score</small>
        </div>
        <div>
          <span>Passed rules</span>
          <strong>{counts.passed}</strong>
          <small>Verified controls</small>
        </div>
        <div>
          <span>Warnings</span>
          <strong>{counts.warning}</strong>
          <small>Needs evidence</small>
        </div>
        <div>
          <span>Failed rules</span>
          <strong>{counts.failed}</strong>
          <small>Remediation required</small>
        </div>
        <div>
          <span>Critical issues</span>
          <strong>{counts.critical}</strong>
          <small>Immediate action</small>
        </div>
      </section>

      <section className="charts-grid">
        <div className="sim-card chart-card">
          <div className="section-heading">
            <div>
              <span className="section-label">Risk posture</span>
              <h2>Domain radar</h2>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={270}>
            <RadarChart data={categoryData}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis
                dataKey="category"
                tick={{ fill: "var(--text-soft)", fontSize: 11 }}
              />
              <Radar
                dataKey="risk"
                stroke="#13b8a6"
                fill="#13b8a6"
                fillOpacity={0.25}
                animationDuration={800}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="sim-card chart-card donut-card">
          <div className="section-heading">
            <div>
              <span className="section-label">Compliance posture</span>
              <h2>Control completion</h2>
            </div>
          </div>
          <div
            className="compliance-donut"
            style={{ "--compliance": `${assessment.compliance * 3.6}deg` } as React.CSSProperties}
          >
            <div>
              <strong>{assessment.compliance}%</strong>
              <span>compliant</span>
            </div>
          </div>
          <div className="donut-legend">
            <span>
              <i className="passed" /> Passed
            </span>
            <span>
              <i className="warning" /> Warning
            </span>
            <span>
              <i className="failed" /> Failed
            </span>
          </div>
        </div>
        <div className="sim-card chart-card">
          <div className="section-heading">
            <div>
              <span className="section-label">Findings</span>
              <h2>Severity distribution</h2>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={severityData}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis dataKey="severity" tick={{ fill: "var(--text-soft)", fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fill: "var(--text-soft)", fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[5, 5, 0, 0]}>
                {severityData.map((_, index) => (
                  <Cell key={severityOrder[index]} fill={chartColors[index]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="sim-card chart-card">
          <div className="section-heading">
            <div>
              <span className="section-label">Portfolio context</span>
              <h2>Assessment trend</h2>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis dataKey="assessment" tick={{ fill: "var(--text-soft)", fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: "var(--text-soft)", fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="risk"
                stroke="#7967da"
                strokeWidth={2.5}
                dot={{ r: 3 }}
                animationDuration={900}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="sim-card chart-card chart-wide">
          <div className="section-heading">
            <div>
              <span className="section-label">Domain comparison</span>
              <h2>Risk category profile</h2>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={categoryData} layout="vertical">
              <CartesianGrid horizontal={false} stroke="var(--border)" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fill: "var(--text-soft)", fontSize: 11 }}
              />
              <YAxis
                type="category"
                dataKey="category"
                width={92}
                tick={{ fill: "var(--text-soft)", fontSize: 11 }}
              />
              <Tooltip />
              <Bar dataKey="risk" fill="#13b8a6" radius={[0, 5, 5, 0]} animationDuration={900} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="sim-card rules-section">
        <div className="section-heading">
          <div>
            <span className="section-label">Governance controls</span>
            <h2>Rule evaluation</h2>
          </div>
          <span>{assessment.rules.length} rules</span>
        </div>
        <div className="rules-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Rule name</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {assessment.rules.map((rule) => (
                <tr key={rule.name}>
                  <td>
                    <strong>{rule.name}</strong>
                  </td>
                  <td>
                    <span className={`status-badge status-${rule.status.toLowerCase()}`}>
                      <StatusIcon status={rule.status} />
                      {rule.status}
                    </span>
                  </td>
                  <td>
                    <span className={`severity-label severity-${rule.severity.toLowerCase()}`}>
                      {rule.severity}
                    </span>
                  </td>
                  <td>{rule.description}</td>
                  <td>{rule.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="sim-card recommendations">
        <div className="section-heading">
          <div>
            <span className="section-label">Remediation plan</span>
            <h2>Actionable recommendations</h2>
          </div>
          <Scale size={18} />
        </div>
        {severityOrder.map((priority) => {
          const items = assessment.recommendations.filter((item) => item.priority === priority);
          return items.length ? (
            <div className="recommendation-group" key={priority}>
              <span className={`severity-label severity-${priority.toLowerCase()}`}>
                {priority}
              </span>
              <div>
                {items.map((item) => (
                  <article key={item.title}>
                    <strong>{item.title}</strong>
                    <p>{item.detail}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : null;
        })}
      </section>
    </motion.div>
  );
}

function ExecutiveReport({ assessment, onBack }: { assessment: Assessment; onBack: () => void }) {
  const failed = assessment.rules.filter((rule) => rule.status === "Failed");
  return (
    <motion.div
      className="report-view"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="report-toolbar">
        <button className="secondary-button" onClick={onBack}>
          <ChevronRight className="back-icon" size={15} /> Back to results
        </button>
        <div>
          <button title="Export PDF" onClick={() => exportPdf(assessment)}>
            <Download size={15} /> PDF
          </button>
          <button title="Export JSON" onClick={() => exportJson(assessment)}>
            <FileJson size={15} /> JSON
          </button>
          <button title="Export CSV" onClick={() => exportCsv(assessment)}>
            <FileSpreadsheet size={15} /> CSV
          </button>
        </div>
      </div>
      <article className="executive-report">
        <header>
          <div>
            <span className="brand-mark">
              <ShieldCheck size={19} />
            </span>
            <strong>NorseAI</strong>
          </div>
          <span>Governance assessment · {new Date(assessment.createdAt).toLocaleDateString()}</span>
          <h1>{assessment.submission.systemName}</h1>
          <p>{assessment.submission.organization}</p>
          <span
            className={`decision decision-${assessment.decision.toLowerCase().replaceAll(" ", "-")}`}
          >
            {assessment.decision}
          </span>
        </header>
        <section>
          <h2>Executive Summary</h2>
          <p>
            {assessment.submission.systemName} received an overall risk score of{" "}
            <strong>{assessment.riskScore}/100</strong> with {assessment.compliance}% compliance.
            NorseAI recommends <strong>{assessment.decision.toLowerCase()}</strong> based on{" "}
            {failed.length} failed controls and{" "}
            {assessment.rules.filter((rule) => rule.status === "Warning").length} warnings.
          </p>
        </section>
        <section>
          <h2>AI System Overview</h2>
          <dl>
            <div>
              <dt>Industry</dt>
              <dd>{assessment.submission.industry}</dd>
            </div>
            <div>
              <dt>Model</dt>
              <dd>{assessment.submission.modelType}</dd>
            </div>
            <div>
              <dt>Deployment</dt>
              <dd>{assessment.submission.deploymentType}</dd>
            </div>
            <div>
              <dt>Region</dt>
              <dd>{assessment.submission.region}</dd>
            </div>
            <div>
              <dt>Intended use</dt>
              <dd>{assessment.submission.intendedUse}</dd>
            </div>
            <div>
              <dt>Training data</dt>
              <dd>{assessment.submission.trainingDataSource}</dd>
            </div>
          </dl>
        </section>
        <section>
          <h2>Risk Assessment</h2>
          <div className="report-risk-grid">
            {riskCategories.map((category) => (
              <div key={category}>
                <span>{category}</span>
                <strong>{assessment.categories[category]}</strong>
              </div>
            ))}
          </div>
        </section>
        <section>
          <h2>Compliance Findings</h2>
          <p>
            {assessment.rules.filter((rule) => rule.status === "Passed").length} of{" "}
            {assessment.rules.length} controls passed without qualification. The weighted compliance
            score is {assessment.compliance}%.
          </p>
        </section>
        <section>
          <h2>Rule Violations</h2>
          {failed.length ? (
            failed.map((rule) => (
              <div className="report-finding" key={rule.name}>
                <strong>{rule.name}</strong>
                <p>{rule.description}</p>
              </div>
            ))
          ) : (
            <p>No failed rules were detected.</p>
          )}
        </section>
        <section>
          <h2>Recommendations</h2>
          <ol>
            {assessment.recommendations.map((item) => (
              <li key={`${item.priority}-${item.title}`}>
                <span className={`severity-label severity-${item.priority.toLowerCase()}`}>
                  {item.priority}
                </span>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </li>
            ))}
          </ol>
        </section>
        <footer>
          <div>
            <span>Final decision</span>
            <strong>{assessment.decision}</strong>
          </div>
          <p>Generated by NorseAI · Assessment ID {assessment.id}</p>
        </footer>
      </article>
    </motion.div>
  );
}

function HistoryView({
  items,
  onOpen,
  onDelete,
  onBack,
}: {
  items: Assessment[];
  onOpen: (item: Assessment) => void;
  onDelete: (id: string) => void;
  onBack: () => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const compared = items.filter((item) => selected.includes(item.id));
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <section className="results-header">
        <div>
          <span className="eyebrow">Local workspace</span>
          <h1>Assessment history</h1>
          <p>Reopen, compare, or remove reports stored in this browser.</p>
        </div>
        <button className="secondary-button" onClick={onBack}>
          <ChevronRight className="back-icon" size={15} /> Back to simulator
        </button>
      </section>
      {compared.length === 2 && (
        <section className="sim-card comparison">
          <div className="section-heading">
            <div>
              <span className="section-label">Side-by-side</span>
              <h2>Assessment comparison</h2>
            </div>
          </div>
          <div>
            {compared.map((item) => (
              <article key={item.id}>
                <strong>{item.submission.systemName}</strong>
                <span>{item.decision}</span>
                <dl>
                  <div>
                    <dt>Risk</dt>
                    <dd>{item.riskScore}</dd>
                  </div>
                  <div>
                    <dt>Compliance</dt>
                    <dd>{item.compliance}%</dd>
                  </div>
                  <div>
                    <dt>Failed</dt>
                    <dd>{item.rules.filter((rule) => rule.status === "Failed").length}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </section>
      )}
      <section className="history-grid">
        {items.length ? (
          items.map((item) => (
            <article className="sim-card history-card" key={item.id}>
              <label className="compare-check">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  disabled={!selected.includes(item.id) && selected.length >= 2}
                  onChange={() =>
                    setSelected((current) =>
                      current.includes(item.id)
                        ? current.filter((id) => id !== item.id)
                        : [...current, item.id],
                    )
                  }
                />{" "}
                Compare
              </label>
              <span className="section-label">{new Date(item.createdAt).toLocaleString()}</span>
              <h2>{item.submission.systemName}</h2>
              <p>
                {item.submission.organization} · {item.submission.industry}
              </p>
              <div className="history-metrics">
                <span>
                  Risk <strong>{item.riskScore}</strong>
                </span>
                <span>
                  Compliance <strong>{item.compliance}%</strong>
                </span>
              </div>
              <span
                className={`decision decision-${item.decision.toLowerCase().replaceAll(" ", "-")}`}
              >
                {item.decision}
              </span>
              <div className="history-actions">
                <button onClick={() => onOpen(item)}>
                  <FileText size={15} /> Open report
                </button>
                <button
                  aria-label={`Delete ${item.submission.systemName}`}
                  onClick={() => onDelete(item.id)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="empty-history">
            <Clock3 size={30} />
            <h2>No assessments yet</h2>
            <p>Completed assessments will appear here.</p>
          </div>
        )}
      </section>
    </motion.div>
  );
}

export function SimulatorPage() {
  const [view, setView] = useState<View>("submission");
  const [activeStage, setActiveStage] = useState(0);
  const [pending, setPending] = useState<SystemSubmission | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [history, setHistory] = useState(loadAssessments);

  useEffect(() => {
    if (view !== "pipeline" || !pending) return;
    if (activeStage >= pipelineStages.length - 1) {
      const timeout = window.setTimeout(() => {
        const result = assessSystem(pending);
        setAssessment(result);
        setHistory((current) => {
          const next = [result, ...current];
          saveAssessments(next);
          return next;
        });
        setView("dashboard");
      }, 650);
      return () => window.clearTimeout(timeout);
    }
    const timeout = window.setTimeout(() => setActiveStage((stage) => stage + 1), 520);
    return () => window.clearTimeout(timeout);
  }, [activeStage, pending, view]);

  const content = useMemo(() => {
    if (view === "pipeline" && pending)
      return <Pipeline activeStage={activeStage} name={pending.systemName} />;
    if (view === "dashboard" && assessment)
      return (
        <AssessmentDashboard
          assessment={assessment}
          onReport={() => setView("report")}
          onReset={() => setView("submission")}
        />
      );
    if (view === "report" && assessment)
      return <ExecutiveReport assessment={assessment} onBack={() => setView("dashboard")} />;
    if (view === "history")
      return (
        <HistoryView
          items={history}
          onBack={() => setView("submission")}
          onOpen={(item) => {
            setAssessment(item);
            setView("report");
          }}
          onDelete={(id) => {
            const next = history.filter((item) => item.id !== id);
            setHistory(next);
            saveAssessments(next);
          }}
        />
      );
    return (
      <SubmissionForm
        historyCount={history.length}
        onHistory={() => setView("history")}
        onSubmit={(submission) => {
          setPending(submission);
          setActiveStage(0);
          setView("pipeline");
        }}
      />
    );
  }, [activeStage, assessment, history, pending, view]);

  return (
    <div className="simulator-page">
      <AnimatePresence mode="wait">{content}</AnimatePresence>
    </div>
  );
}
