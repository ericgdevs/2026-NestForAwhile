import { useEffect, useState } from "react";

import { claimQueue, getQueue } from "../api/client";
import Icon from "../components/Icon";

export default function Waiting() {
  const [queue, setQueue] = useState<{ status: string; position: number | null; message: string } | null>(null);

  useEffect(() => {
    getQueue().then(setQueue).catch(() => setQueue(null));
  }, []);

  const ready = queue?.status === "ready";

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Waiting to shop</h1>
          <p>The floor is full right now. We'll let you in as soon as a shopper finishes.</p>
        </div>
      </header>

      <section className="label-panel" style={{ maxWidth: "32rem" }} aria-live="polite">
        {queue ? (
          <>
            <p className={`status-badge status-bar ${ready ? "status-badge-approved" : "status-badge-capped"}`}>
              <Icon name={ready ? "check" : "queue"} />
              {ready ? "Your turn" : "Please wait"}
            </p>
            {queue.position && (
              <div className="figure">
                <b>Position: {queue.position}</b>
              </div>
            )}
            <hr className="rule-heavy" />
            <p className="why">{queue.message}</p>
            {ready && (
              <button className="btn btn-primary btn-block" style={{ marginTop: "1rem" }} type="button" onClick={() => claimQueue()}>
                Come in
              </button>
            )}
          </>
        ) : (
          <p className="empty">Checking the line…</p>
        )}
      </section>
    </main>
  );
}
