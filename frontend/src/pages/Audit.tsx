import { useState } from "react";
import { apiRequest } from "../api/client";

export default function Audit() {
  const [code, setCode] = useState("");
  const [current, setCurrent] = useState<{ product_id: number; name: string; current_qty: number } | null>(null);
  const [count, setCount] = useState("");
  const [message, setMessage] = useState("");
  async function lookup() {
    const result = await apiRequest<typeof current>(`/inventory/audit/${encodeURIComponent(code)}`);
    setCurrent(result);
    setMessage("");
  }
  async function submit() {
    if (!current) return;
    const result = await apiRequest<{ variance: number }>("/inventory/audit", { method: "POST", body: { product_id: current.product_id, counted_qty: Number(count) } });
    setMessage(`Variance: ${result.variance}`);
  }
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">Inventory audit</h1><input className="rounded border p-2" value={code} onChange={(event) => setCode(event.target.value)} placeholder="SKU or barcode" /><button className="ml-2 rounded bg-slate-900 px-3 py-2 text-white" onClick={lookup}>Scan item</button>{current && <section className="rounded bg-white p-4 shadow"><p>{current.name}</p><p>Current count: {current.current_qty}</p><input className="rounded border p-2" type="number" min="0" value={count} onChange={(event) => setCount(event.target.value)} placeholder="Actual count" /><button className="ml-2 rounded bg-emerald-700 px-3 py-2 text-white" onClick={submit}>Confirm</button></section>}{message && <p role="status">{message}</p>}</main>;
}
