import { useCallback, useEffect, useState, type ReactNode } from "react";

import { checkIn, getVisit, type VisitState } from "../api/client";
import AwaitingApproval from "../pages/AwaitingApproval";
import VisitComplete from "../pages/VisitComplete";
import Waiting from "../pages/Waiting";

const POLL_MS = { shopping: 15000, queued: 5000 } as const;

/** Shows clients the screen for where they are in their visit; shopping screens only while shopping. */
export default function VisitGate({ children }: { children: ReactNode }) {
  const [visit, setVisit] = useState<VisitState | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  const refresh = useCallback(
    () =>
      getVisit()
        .then(setVisit)
        .catch(() => setUnavailable(true)),
    [],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Shopping: notice when the volunteer completes checkout. Queued: notice when it's our turn.
  const status = visit?.status;
  useEffect(() => {
    const ms = status === "shopping" || status === "queued" ? POLL_MS[status] : 0;
    if (!ms) return;
    const timer = setInterval(() => void refresh(), ms);
    return () => clearInterval(timer);
  }, [status, refresh]);

  async function start() {
    const next = await checkIn();
    setVisit(next);
    return next.status === "shopping" || next.status === "queued";
  }

  // Children stay mounted (hidden) while the visit loads, so their data requests run alongside
  // the visit check instead of waiting for it.
  const blocker = unavailable ? null : visit ? screenFor(visit, start, refresh) : <p className="empty">Checking your visit…</p>;
  const showChildren = unavailable || !visit || !blocker;
  return (
    <>
      {blocker}
      {showChildren && <div style={{ display: blocker ? "none" : "contents" }}>{children}</div>}
    </>
  );
}

/** The screen that replaces the shopping screens for this visit state, or null while shopping. */
function screenFor(visit: VisitState, start: () => Promise<boolean>, refresh: () => Promise<void>) {
  switch (visit.status) {
    case "awaiting_approval":
      return <AwaitingApproval onCheckAgain={start} />;
    case "queued":
      return (
        <Waiting
          message={visit.message}
          position={visit.position}
          ready={visit.queue_status === "ready"}
          onIn={() => void refresh()}
        />
      );
    case "complete":
      return <VisitComplete receipt={visit.receipt} onStart={start} />;
    case "none":
      return <VisitComplete onStart={start} />;
    case "inactive":
      return (
        <p className="panel centered">
          This account isn't active. Please ask staff at the front desk for help.
        </p>
      );
    default:
      return null;
  }
}
