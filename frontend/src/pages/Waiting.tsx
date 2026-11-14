import { useEffect, useState } from "react";
import { claimQueue, getQueue } from "../api/client";

export default function Waiting() {
  const [queue, setQueue] = useState<{ status: string; position: number | null; message: string } | null>(null);
  useEffect(() => { getQueue().then(setQueue); }, []);
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">Queue</h1>{queue && <><p>{queue.message}</p>{queue.position && <p>Position: {queue.position}</p>}{queue.status === "ready" && <button className="rounded bg-emerald-700 px-3 py-2 text-white" onClick={() => claimQueue()}>Come in</button>}</>}</main>;
}
