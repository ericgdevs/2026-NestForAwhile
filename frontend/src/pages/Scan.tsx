import { useState } from "react";

import { saveCartItem, scanProduct, type ScanResult } from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import Icon from "../components/Icon";
import { StatusBadge } from "../components/StatusBadge";

function amount(value: number | null, unit: string) {
  return value === null ? "Not available" : `${value} ${unit}`;
}

export default function Scan() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");
  const [added, setAdded] = useState(false);

  async function scan(value = code) {
    if (!value.trim()) return;
    setError("");
    setAdded(false);
    try {
      setResult(await scanProduct(value.trim()));
    } catch {
      setResult(null);
      setError("We couldn't find that product. Check the SKU and try again.");
    }
  }

  async function handleAddToCart(productId: number) {
    await saveCartItem(productId, 1);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Scan a product</h1>
          <p>Point your camera at the barcode or type the SKU to see if it fits your diet.</p>
        </div>
      </header>

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        <section className="panel stack" aria-label="Find a product">
          <BarcodeScanner
            onDetected={(value) => {
              setCode(value);
              void scan(value);
            }}
          />
          <p className="divider-text">or type it</p>
          <form
            className="field"
            onSubmit={(event) => {
              event.preventDefault();
              void scan();
            }}
          >
            <label className="field-label" htmlFor="sku">
              SKU or barcode
            </label>
            <div className="inline-form">
              <input
                className="input"
                id="sku"
                inputMode="text"
                placeholder="e.g. SYN-OATS-001"
                value={code}
                onChange={(event) => setCode(event.target.value)}
              />
              <button className="btn btn-primary" type="submit">
                Check
              </button>
            </div>
          </form>
          {error && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {error}
            </p>
          )}
        </section>

        {result ? (
          <article className="label-panel" aria-live="polite">
            <StatusBadge bar status={result.status} />
            <h2>{result.name}</h2>
            <p className="meta tabular">SKU {result.sku}</p>
            <hr className="rule-heavy" />
            <dl className="facts">
              <div>
                <dt>Sodium</dt>
                <dd>{amount(result.sodium_mg, "mg")}</dd>
              </div>
              <div>
                <dt>Sugar</dt>
                <dd>{amount(result.sugar_g, "g")}</dd>
              </div>
              <div>
                <dt>Saturated fat</dt>
                <dd>{amount(result.sat_fat_g, "g")}</dd>
              </div>
              <div>
                <dt>Potassium</dt>
                <dd>{amount(result.potassium_mg, "mg")}</dd>
              </div>
            </dl>
            <hr className="rule-heavy" />
            <p className="why">
              <strong>Why: </strong>
              {result.explanation}
            </p>
            {result.image_url && <img alt={result.name} className="media" src={result.image_url} />}
            {result.product_id && (
              <button
                className={`btn btn-block ${added ? "btn-done" : "btn-primary"}`}
                style={{ marginTop: "1rem" }}
                type="button"
                onClick={() => void handleAddToCart(result.product_id!)}
              >
                {added ? (
                  <>
                    <Icon name="check" /> Added to cart
                  </>
                ) : (
                  "Add to cart"
                )}
              </button>
            )}
          </article>
        ) : (
          <div className="panel empty">
            <Icon name="scan" />
            <strong>Nothing scanned yet</strong>
            <span>Your result shows here with nutrition facts and whether it fits your diet.</span>
          </div>
        )}
      </div>
    </main>
  );
}
