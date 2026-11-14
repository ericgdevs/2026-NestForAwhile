import { useState } from "react";

import { completeCheckout, validateCheckout } from "../api/client";

export default function Checkout() {
  const [token, setToken] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [receipt, setReceipt] = useState<{ checkout_id: number; total_lb: number } | null>(null);

  async function review() {
    const result = await validateCheckout(token);
    setErrors(result.errors);
    if (result.valid) setReceipt(null);
  }

  async function complete() {
    setReceipt(await completeCheckout(token));
    setErrors([]);
  }

  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-xl space-y-5">
        <h1 className="text-2xl font-semibold">Checkout</h1>
        <label className="block text-sm font-medium">
          Shopping session token
          <input
            className="mt-1 w-full rounded-lg border px-3 py-2"
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
        </label>
        <div className="flex gap-2">
          <button className="rounded-lg border px-4 py-2" onClick={() => void review()}>Review cart</button>
          <button className="rounded-lg bg-slate-900 px-4 py-2 text-white" onClick={() => void complete()}>Complete checkout</button>
        </div>
        {errors.length > 0 && (
          <div className="rounded-lg bg-red-50 p-4 text-red-900">
            <strong>Checkout needs attention</strong>
            <ul className="list-disc pl-5">{errors.map((error) => <li key={error}>{error}</li>)}</ul>
          </div>
        )}
        {receipt && (
          <div className="rounded-lg bg-emerald-50 p-4 text-emerald-900">
            Receipt #{receipt.checkout_id} · {receipt.total_lb} lb distributed
          </div>
        )}
      </div>
    </main>
  );
}
