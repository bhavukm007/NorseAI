import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { LoginPage } from "../features/auth/LoginPage";
import { ProtectedRoute } from "../features/auth/ProtectedRoute";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { AgentsPage } from "../features/governance/AgentsPage";
import { AuditPage } from "../features/governance/AuditPage";
import { BudgetsPage } from "../features/governance/BudgetsPage";
import { EmergencyPage } from "../features/governance/EmergencyPage";
import { FinancialActionsPage } from "../features/governance/FinancialActionsPage";
import { FleetsPage } from "../features/governance/FleetsPage";
import { OrganizationsPage } from "../features/governance/OrganizationsPage";
import { PoliciesPage } from "../features/governance/PoliciesPage";
import { NotFoundPage } from "../pages/NotFoundPage";

const SimulatorPage = lazy(() =>
  import("../features/simulator/SimulatorPage").then((module) => ({
    default: module.SimulatorPage,
  })),
);

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/",
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "organizations", element: <OrganizationsPage /> },
          { path: "agents", element: <AgentsPage /> },
          { path: "fleets", element: <FleetsPage /> },
          { path: "policies", element: <PoliciesPage /> },
          { path: "budgets", element: <BudgetsPage /> },
          { path: "financial-actions", element: <FinancialActionsPage /> },
          { path: "audit", element: <AuditPage /> },
          { path: "emergency", element: <EmergencyPage /> },
          {
            path: "assessment-lab",
            element: (
              <Suspense
                fallback={<div className="page-skeleton" aria-label="Loading AI Assessment Lab" />}
              >
                <SimulatorPage />
              </Suspense>
            ),
          },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
