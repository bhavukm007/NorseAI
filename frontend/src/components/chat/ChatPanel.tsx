import { LockKeyhole, Sparkles } from "lucide-react";

export function ChatPanel() {
  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="panel-header">
        <div className="chat-heading">
          <span className="assistant-mark">
            <Sparkles size={17} aria-hidden="true" />
          </span>
          <div>
            <h2 id="chat-title">Norse assistant</h2>
            <span>Backend integration unavailable</span>
          </div>
        </div>
        <span className="phase-chip">Phase 04</span>
      </div>
      <div className="chat-unavailable" role="status">
        <span className="empty-icon">
          <LockKeyhole size={20} aria-hidden="true" />
        </span>
        <strong>AI chat is not connected</strong>
        <p>
          Conversation history and messaging will become available when the Phase 04 backend
          endpoint is implemented.
        </p>
      </div>
      <div className="chat-composer">
        <label className="sr-only" htmlFor="chat-message">
          Message Norse assistant
        </label>
        <input id="chat-message" disabled placeholder="Coming in Phase 04" />
        <button className="send-button" disabled type="button">
          Send
        </button>
      </div>
    </section>
  );
}
