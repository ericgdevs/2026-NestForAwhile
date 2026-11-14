import { useState } from "react";

import { saveCartItem, scanProduct, type ScanResult } from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import { StatusBadge } from "../components/StatusBadge";

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
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Instant scan</span>
          <h1 className="page-title">
            Decode<br />your food.
          </h1>
          <p className="page-subtitle">
            Scan a barcode or enter a SKU to get a clear, calm read on nutrition and dietary fit.
          </p>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
          alignItems: "start",
        }}
      >
        {/* Scanner & Lookup Card */}
        <section className="ui-card" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 0.25rem" }}>Barcode Scanner</h2>
            <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", margin: 0 }}>
              Use your device camera to scan items directly on the shelf.
            </p>
          </div>

          <BarcodeScanner
            onDetected={(value) => {
              setCode(value);
              void scan(value);
            }}
          />

          <div
            style={{
              position: "relative",
              textAlign: "center",
              margin: "0.5rem 0",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: 0,
                right: 0,
                height: "1px",
                background: "var(--border-subtle)",
              }}
            />
            <span
              style={{
                position: "relative",
                background: "#ffffff",
                padding: "0 0.75rem",
                fontSize: "0.78rem",
                fontWeight: 600,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Or enter manually
            </span>
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              void scan();
            }}
            style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}
          >
            <label htmlFor="sku" className="form-label">
              SKU or barcode
            </label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                id="sku"
                className="form-input"
                placeholder="Enter SKU or barcode"
                value={code}
                onChange={(event) => setCode(event.target.value)}
              />
              <button type="submit" className="btn btn-primary" style={{ flexShrink: 0 }}>
                Check
              </button>
            </div>
          </form>

          {error && (
            <p
              style={{
                margin: 0,
                fontSize: "0.88rem",
                color: "var(--pastel-rose-text)",
                background: "var(--pastel-rose-bg)",
                border: "1px solid var(--pastel-rose-border)",
                padding: "0.75rem 1rem",
                borderRadius: "var(--radius-md)",
              }}
            >
              {error}
            </p>
          )}
        </section>

        {/* Scan Result Card */}
        {result ? (
          <article className="ui-card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.5rem" }}>
              <div>
                <span className="stat-label">Product match</span>
                <h2 style={{ fontSize: "1.45rem", fontWeight: 700, margin: "0.2rem 0", color: "var(--text-dark)" }}>
                  {result.name}
                </h2>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", margin: 0 }}>SKU: {result.sku}</p>
              </div>
              <StatusBadge status={result.status} />
            </div>

            <p style={{ fontSize: "0.92rem", lineHeight: 1.5, color: "var(--text-body)", margin: 0 }}>
              {result.explanation}
            </p>

            <dl className="nutrition-grid">
              <div className="nutrition-item">
                <dt className="nutrition-label">Sodium</dt>
                <dd className="nutrition-value">{result.sodium_mg ?? "Unknown"} mg</dd>
              </div>
              <div className="nutrition-item">
                <dt className="nutrition-label">Sugar</dt>
                <dd className="nutrition-value">{result.sugar_g ?? "Unknown"} g</dd>
              </div>
              <div className="nutrition-item">
                <dt className="nutrition-label">Sat. fat</dt>
                <dd className="nutrition-value">{result.sat_fat_g ?? "Unknown"} g</dd>
              </div>
              <div className="nutrition-item">
                <dt className="nutrition-label">Potassium</dt>
                <dd className="nutrition-value">{result.potassium_mg ?? "Unknown"} mg</dd>
              </div>
            </dl>

            {result.image_url && (
              <div
                style={{
                  width: "100%",
                  height: "180px",
                  borderRadius: "var(--radius-md)",
                  overflow: "hidden",
                  border: "1px solid var(--border-card)",
                }}
              >
                <img
                  alt=""
                  src={result.image_url}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              </div>
            )}

            {result.product_id && (
              <button
                className={`btn ${added ? "btn-secondary" : "btn-primary"}`}
                style={{ width: "100%", marginTop: "0.5rem" }}
                onClick={() => void handleAddToCart(result.product_id!)}
              >
                {added ? "Added to cart ✓" : "Add to cart"}
              </button>
            )}
          </article>
        ) : (
          <div
            className="ui-card"
            style={{
              padding: "3rem 1.5rem",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              minHeight: "280px",
              color: "var(--text-muted)",
            }}
          >
            <span style={{ fontSize: "2.5rem", marginBottom: "0.75rem", opacity: 0.5 }}>▣</span>
            <p style={{ margin: 0, fontWeight: 500 }}>Scan an item or enter a SKU to view safety details.</p>
          </div>
        )}
      </div>
    </main>
  );
}
