import { useEffect, useState } from "react";

import {
  addRecipeToList,
  getRecipes,
  saveCartItem,
  saveRecipe,
  scanProduct,
  type Recipe,
  type ScanResult,
} from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import Icon from "../components/Icon";
import NotForLine from "../components/NotForLine";
import NutritionFacts from "../components/NutritionFacts";
import RecipeGroups from "../components/RecipeGroups";
import { StatusBadge } from "../components/StatusBadge";

const RED_CONFIRM = "This isn't recommended for anyone in your household. Add it anyway?";

export default function Scan() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");
  const [added, setAdded] = useState<number[]>([]);
  const [recipes, setRecipes] = useState<Recipe[] | null>(null);

  // Home's scanner opens /scan?code=…; look that code up straight away.
  useEffect(() => {
    const initial = new URLSearchParams(window.location.search).get("code");
    if (initial) {
      setCode(initial);
      void scan(initial);
    }
  }, []);

  async function scan(value = code) {
    if (!value.trim()) return;
    setError("");
    setAdded([]);
    setRecipes(null);
    try {
      const scanned = await scanProduct(value.trim());
      setResult(scanned);
      if (scanned.product_id) {
        getRecipes({ scanned_product_id: scanned.product_id })
          .then((found) => setRecipes(found.recipes))
          .catch(() => setRecipes([]));
      }
    } catch {
      setResult(null);
      setError("We couldn't find that product. Check the SKU and try again.");
    }
  }

  // Client choice: a Red item can still be added after one confirmation; checkout stops it.
  async function handleAddToCart(productId: number, status?: string) {
    if (status === "Restricted" && !window.confirm(RED_CONFIRM)) return;
    await saveCartItem(productId, 1);
    setAdded((ids) => [...ids, productId]);
  }

  const addButton = (productId: number, status?: string, label = "Add to cart") => (
    <button
      className={`btn btn-block ${added.includes(productId) ? "btn-done" : "btn-primary"}`}
      disabled={added.includes(productId)}
      type="button"
      onClick={() => void handleAddToCart(productId, status)}
    >
      {added.includes(productId) ? (
        <>
          <Icon name="check" /> Added to cart
        </>
      ) : (
        label
      )}
    </button>
  );

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
            <NotForLine allergy={result.allergy_match} notFor={result.not_for} />
            <h2>{result.name}</h2>
            <p className="meta tabular">SKU {result.sku}</p>
            <hr className="rule-heavy" />
            <NutritionFacts facts={result} />
            <hr className="rule-heavy" />
            <p className="why">
              <strong>Why: </strong>
              {result.explanation}
            </p>
            {result.image_url && <img alt={result.name} className="media" src={result.image_url} />}
            {result.product_id && <div style={{ marginTop: "1rem" }}>{addButton(result.product_id, result.status)}</div>}
            {result.status === "Restricted" && (
              <section aria-label="Safer swaps" className="stack" style={{ marginTop: "1rem" }}>
                <hr className="rule-mid" />
                <h3 style={{ fontSize: "1.125rem" }}>Safer swaps in stock</h3>
                {result.swaps?.length ? (
                  result.swaps.map((swap) => (
                    <div className="panel stack" key={swap.product_id} style={{ gap: "0.5rem" }}>
                      <div className="row">
                        <strong>{swap.name}</strong>
                        <StatusBadge status={swap.status} />
                      </div>
                      <NotForLine notFor={swap.not_for} />
                      <span className="location">
                        <Icon name="pin" />
                        Aisle {swap.aisle} · Shelf {swap.shelf} · Bin {swap.bin}
                      </span>
                      {addButton(swap.product_id, swap.status, `Add ${swap.name}`)}
                    </div>
                  ))
                ) : (
                  <p className="panel-sub">There's no safer swap in stock today. A volunteer can help you find one.</p>
                )}
              </section>
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

      {result?.product_id && (
        <section aria-label="Recipe ideas" style={{ marginTop: "2rem" }}>
          <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
            Recipes with {result.name}
          </h2>
          {recipes === null ? (
            <p className="empty">Finding recipes that are safe for everyone at home…</p>
          ) : recipes.length === 0 ? (
            <p className="panel empty">
              <strong>No recipes with this item are safe for everyone in your household.</strong>
            </p>
          ) : (
            <RecipeGroups
              actions={{
                onSave: saveRecipe,
                onAddToList: (recipe) => addRecipeToList(recipe, result.product_id),
              }}
              recipes={recipes}
            />
          )}
        </section>
      )}
    </main>
  );
}
