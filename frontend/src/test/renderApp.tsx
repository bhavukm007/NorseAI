import { render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { AuthProvider } from "../features/auth/AuthProvider";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { ThemeProvider } from "../providers/ThemeProvider";
import { ToastProvider } from "../providers/ToastProvider";

export function renderApp(path = "/dashboard") {
  sessionStorage.setItem(
    "norseai.operator.session",
    JSON.stringify({
      accessToken: "test-token",
      refreshToken: "test-refresh-token-that-is-long-enough-for-tests",
      expiresAt: new Date(Date.now() + 60_000).toISOString(),
      username: "admin",
      role: "admin",
    }),
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppLayout />,
        children: [
          { path: "dashboard", element: <DashboardPage /> },
          { path: "agents", element: <div>Agents</div> },
        ],
      },
    ],
    { initialEntries: [path] },
  );

  return {
    router,
    ...render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ThemeProvider>
            <ToastProvider>
              <RouterProvider router={router} />
            </ToastProvider>
          </ThemeProvider>
        </AuthProvider>
      </QueryClientProvider>,
    ),
  };
}
