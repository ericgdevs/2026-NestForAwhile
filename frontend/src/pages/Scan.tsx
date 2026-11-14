import { useState } from "react";

import { saveCartItem, scanProduct, type ScanResult } from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import { StatusBadge } from "../components/StatusBadge";

export default function Scan() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");

  async function scan(value = code) {
    if (!value.trim()) return;
    setError("");
    try {
      setResult(await scanProduct(value.trim()));
    } catch {
      setResult(null);
      setError("We couldn't find that product. Check the SKU and try again.");
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Scan a product</h1>
          <p className="mt-2 text-slate-600">Scan a barcode or enter a SKU to check its match.</p>
        </div>
        <BarcodeScanner
          onDetected={(value) => {
            setCode(value);
            void scan(value);
          }}
        />
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void scan();
          }}
        >
          <label className="sr-only" htmlFor="sku">
            SKU or barcode
          </label>
          <input
            id="sku"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2"
            placeholder="Enter SKU or barcode"
            value={code}
            onChange={(event) => setCode(event.target.value)}
          />
          <button className="rounded-lg bg-slate-900 px-4 py-2 text-white" type="submit">
            Check
          </button>
        </form>
        {error && <p className="text-sm text-red-800">{error}</p>}
        {result && (
          <article className="space-y-4 rounded-xl bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">{result.name}</h2>
                <p className="text-sm text-slate-600">SKU: {result.sku}</p>
              </div>
              <StatusBadge status={result.status} />
            </div>
            <p>{result.explanation}</p>
            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <div><dt className="text-slate-500">Sodium</dt><dd>{result.sodium_mg ?? "Unknown"} mg</dd></div>
              <div><dt className="text-slate-500">Sugar</dt><dd>{result.sugar_g ?? "Unknown"} g</dd></div>
              <div><dt className="text-slate-500">Sat. fat</dt><dd>{result.sat_fat_g ?? "Unknown"} g</dd></div>
              <div><dt className="text-slate-500">Potassium</dt><dd>{result.potassium_mg ?? "Unknown"} mg</dd></div>
            </dl>
            {result.image_url && <img alt="" className="max-h-48 rounded-lg" src={result.image_url} />}
            {result.product_id && (
              <button
                className="rounded-lg border px-3 py-2"
                onClick={() => void saveCartItem(result.product_id!, 1)}
              >
                Add to cart
              </button>
            )}
          </article>
        )}
      </div>
    </main>
  );
}
