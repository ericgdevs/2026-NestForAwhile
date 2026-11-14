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
    <main className="space-y-6">
      <div className="space-y-3">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-stone-500">Instant scan</p>
        <div>
          <h1 className="display-title">Decode<br />your food.</h1>
          <p className="mt-3 max-w-md text-stone-500">Scan a barcode to get a clear, calm read on nutrition and dietary fit.</p>
        </div>
      </div>
      <div className="soft-card overflow-hidden p-3 sm:p-4">
        <BarcodeScanner
          onDetected={(value) => {
            setCode(value);
            void scan(value);
          }}
        />
      </div>
        <form
          className="flex flex-col gap-2 sm:flex-row"
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
            className="soft-input min-w-0 flex-1 px-4 py-3"
            placeholder="Enter SKU or barcode"
            value={code}
            onChange={(event) => setCode(event.target.value)}
          />
          <button className="accent-button px-5 py-3 sm:min-w-24" type="submit">
            Check
          </button>
        </form>
        {error && <p className="text-sm text-red-800">{error}</p>}
        {result && (
          <article className="soft-card space-y-4 p-5 sm:p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">{result.name}</h2>
                <p className="text-sm text-slate-600">SKU: {result.sku}</p>
              </div>
              <StatusBadge status={result.status} />
            </div>
            <p>{result.explanation}</p>
            <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <div className="rounded-2xl bg-[#edf5fc] p-3"><dt className="text-slate-500">Sodium</dt><dd className="mt-1 font-semibold">{result.sodium_mg ?? "Unknown"} mg</dd></div>
              <div className="rounded-2xl bg-[#edf5fc] p-3"><dt className="text-slate-500">Sugar</dt><dd className="mt-1 font-semibold">{result.sugar_g ?? "Unknown"} g</dd></div>
              <div className="rounded-2xl bg-[#edf5fc] p-3"><dt className="text-slate-500">Sat. fat</dt><dd className="mt-1 font-semibold">{result.sat_fat_g ?? "Unknown"} g</dd></div>
              <div className="rounded-2xl bg-[#edf5fc] p-3"><dt className="text-slate-500">Potassium</dt><dd className="mt-1 font-semibold">{result.potassium_mg ?? "Unknown"} mg</dd></div>
            </dl>
            {result.image_url && <img alt="" className="max-h-48 rounded-lg" src={result.image_url} />}
            {result.product_id && (
              <button
                className="accent-button px-4 py-2 text-sm"
                onClick={() => void saveCartItem(result.product_id!, 1)}
              >
                Add to cart
              </button>
            )}
          </article>
        )}
    </main>
  );
}
