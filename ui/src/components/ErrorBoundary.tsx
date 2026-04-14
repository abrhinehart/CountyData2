import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="page-stack" style={{ maxWidth: 760, margin: "80px auto", padding: "0 24px" }}>
          <div className="hero-band">
            <div className="page-kicker" style={{ color: "rgba(191,219,254,0.88)" }}>
              Frontend Recovery
            </div>
            <h1 className="page-title" style={{ color: "#f8fafc", marginTop: 8 }}>
              Something went wrong in the workspace
            </h1>
            <p className="page-subtitle" style={{ color: "rgba(226,232,240,0.82)" }}>
              The UI hit an unexpected rendering error. You can retry without leaving the current thread.
            </p>
          </div>
          <div className="surface-strong panel-pad page-stack">
            <div className="section-head" style={{ marginBottom: 0 }}>
              <div>
                <div className="section-title">Error Message</div>
                <div className="section-caption">Captured by the global React error boundary.</div>
              </div>
              <span className="badge badge-danger">Render Failure</span>
            </div>
            <pre className="code-block">{this.state.error.message}</pre>
            <div className="button-row">
              <button
                onClick={() => this.setState({ error: null })}
                className="button-primary"
              >
                Retry Render
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
