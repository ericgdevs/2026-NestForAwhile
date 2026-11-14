import { useEffect, useState } from "react";
import { getAnalytics } from "../api/client";

export default function Analytics() {
  const [metrics, setMetrics] = useState<Awaited<ReturnType<typeof getAnalytics>> | null>(null);
  useEffect(() => { getAnalytics().then(setMetrics); }, []);
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">Analytics</h1>{metrics && <dl className="grid gap-3 md:grid-cols-3">{Object.entries(metrics).filter(([key]) => key !== "waste_reduction").map(([key, value]) => <div className="rounded bg-white p-3 shadow" key={key}><dt>{key.replaceAll("_", " ")}</dt><dd className="text-xl font-semibold">{String(value)}</dd></div>)}</dl>}</main>;
}
