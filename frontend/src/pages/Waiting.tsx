import { useState } from "react";

import { claimQueue } from "../api/client";
import Icon from "../components/Icon";

type Props = {
  position: number | null;
  ready: boolean;
  message: string;
  onIn: () => void; // called once the client has a shopping session
};

// Shown when the floor is full; the visit gate refreshes it every few seconds.
export default function Waiting({ position, ready, message, onIn }: Props) {
  const [error, setError] = useState("");

  async function comeIn() {
    setError("");
    try {
      await claimQueue();
      onIn();
    } catch {
      setError("Your turn timed out. You're back in line; we'll call you again.");
    }
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Waiting to shop</h1>
          <p>The floor is full right now. We'll let you in as soon as a shopper finishes.</p>
        </div>
      </header>

      <section className="label-panel" style={{ maxWidth: "32rem" }} aria-live="polite">
        <p className={`status-badge status-bar ${ready ? "status-badge-approved" : "status-badge-capped"}`}>
          <Icon name={ready ? "check" : "queue"} />
          {ready ? "Your turn" : "Please wait"}
        </p>
        {!ready && position && (
          <div className="figure">
            <b>Position: {position}</b>
          </div>
        )}
        <hr className="rule-heavy" />
        <p className="why">{message}</p>
        {ready && (
          <button className="btn btn-primary btn-block" style={{ marginTop: "1rem" }} type="button" onClick={() => void comeIn()}>
            Come in
          </button>
        )}
        {error && (
          <p className="alert alert-warn" role="alert" style={{ marginTop: "1rem" }}>
            <Icon name="alert" />
            {error}
          </p>
        )}
      </section>
    </main>
  );
}
