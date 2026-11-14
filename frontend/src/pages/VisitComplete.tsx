import { useEffect, useState } from "react";

import { getSavedRecipes, type Recipe } from "../api/client";
import Icon from "../components/Icon";
import RecipeGroups from "../components/RecipeGroups";

type Props = {
  receipt?: { checkout_id: number; total_lb: number };
  onStart: () => Promise<boolean>;
};

// After checkout (or before a visit starts): the receipt, saved recipes for home, and a way back in.
export default function VisitComplete({ receipt, onStart }: Props) {
  const [saved, setSaved] = useState<Recipe[] | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    getSavedRecipes()
      .then(setSaved)
      .catch(() => setSaved([]));
  }, []);

  async function start() {
    setStarting(true);
    await onStart();
    setStarting(false);
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>{receipt ? "Visit complete" : "Ready to shop?"}</h1>
          <p>{receipt ? "Thanks for shopping with Epic-Cure. Your recipes are saved for home." : "Start your visit when you're at the warehouse."}</p>
        </div>
        {receipt && (
          <div className="figure">
            <b>{receipt.total_lb}</b>
            <span>lb of groceries</span>
          </div>
        )}
      </header>

      {receipt && (
        <p className="alert alert-ok" role="status" style={{ marginBottom: "1rem", maxWidth: "40rem" }}>
          <Icon name="check" />
          Checked out. Receipt #{receipt.checkout_id}.
        </p>
      )}

      <button className="btn btn-primary" disabled={starting} style={{ marginBottom: "2rem" }} type="button" onClick={() => void start()}>
        {starting ? "Starting…" : receipt ? "Start a new visit" : "Start shopping"}
      </button>

      <section aria-label="Your saved recipes">
        <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
          Your saved recipes
        </h2>
        {saved === null ? (
          <p className="empty">Loading your recipes…</p>
        ) : saved.length === 0 ? (
          <p className="panel empty">
            <span>Recipes you save while scanning show up here to cook at home.</span>
          </p>
        ) : (
          <RecipeGroups recipes={saved} />
        )}
      </section>
    </main>
  );
}
