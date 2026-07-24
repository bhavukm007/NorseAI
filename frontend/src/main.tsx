import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { router } from "./app/router";
import { ErrorBoundary } from "./components/feedback/ErrorBoundary";
import { ThemeProvider } from "./providers/ThemeProvider";
import { ToastProvider } from "./providers/ToastProvider";
import "./styles/global.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("Application root element was not found.");
}

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <ThemeProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </ThemeProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  </StrictMode>,
);
