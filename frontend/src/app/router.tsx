import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPlaceholder } from "../features/dashboard/DashboardPlaceholder";
import { NotFoundPage } from "../pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPlaceholder /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
