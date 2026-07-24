import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { FeaturePage } from "../pages/FeaturePage";
import { ThemeProvider } from "../providers/ThemeProvider";
import { ToastProvider } from "../providers/ToastProvider";

export function renderApp(path = "/dashboard") {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppLayout />,
        children: [
          { path: "dashboard", element: <DashboardPage /> },
          { path: "chat", element: <FeaturePage feature="Chat" /> },
        ],
      },
    ],
    { initialEntries: [path] },
  );

  return {
    router,
    ...render(
      <ThemeProvider>
        <ToastProvider>
          <RouterProvider router={router} />
        </ToastProvider>
      </ThemeProvider>,
    ),
  };
}
