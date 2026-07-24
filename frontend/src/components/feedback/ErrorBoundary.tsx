import { CircleAlert, RefreshCw } from "lucide-react";
import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children?: ReactNode;
}

interface ErrorBoundaryState {
  failed: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch() {
    // The production UI intentionally avoids exposing exception details.
  }

  render() {
    if (!this.state.failed) return this.props.children;

    return (
      <main className="recovery-page" id="main-content">
        <span className="feature-icon" aria-hidden="true">
          <CircleAlert size={24} />
        </span>
        <span className="eyebrow">Workspace recovery</span>
        <h1>Something interrupted this view</h1>
        <p>
          Your locally saved assessments are safe. Reload the workspace to return to a stable state.
        </p>
        <button className="primary-button" onClick={() => window.location.reload()}>
          <RefreshCw size={16} /> Reload workspace
        </button>
      </main>
    );
  }
}
