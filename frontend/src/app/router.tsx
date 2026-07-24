import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { FeaturePage } from "../pages/FeaturePage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "chat", element: <FeaturePage feature="Chat" /> },
      { path: "simulator", element: <FeaturePage feature="Simulator" /> },
      { path: "governance", element: <FeaturePage feature="Governance" /> },
      { path: "analytics", element: <FeaturePage feature="Analytics" /> },
      { path: "history", element: <FeaturePage feature="History" /> },
      { path: "settings", element: <FeaturePage feature="Settings" /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
