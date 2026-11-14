import { useEffect, useState } from "react";

import { getRecommendations, saveCartItem, type Recommendation } from "../api/client";
import Icon from "../components/Icon";
import RecipeSheet from "../components/RecipeSheet";
import { StatusBadge } from "../components/StatusBadge";

export default function Home({ householdSize }: { householdSize?: number }) {
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null);
  const [addedIds, setAddedIds] = useState<number[]>([]);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(() => setRecommendations([]));
  }, []);

  async function handleAdd(item: Recommendation) {
    await saveCartItem(item.product_id, item.quantity);
    setAddedIds((prev) => [...prev, item.product_id]);
    setTimeout(() => {
      setAddedIds((prev) => prev.filter((id) => id !== item.product_id));
    }, 2000);
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Today's MTG Warehouse picks</h1>
          <p>Sized for your household and checked against your dietary choices.</p>
        </div>
        {householdSize ? (
          <div className="figure">
            <b>{householdSize}</b>
            <span>{householdSize === 1 ? "person" : "people"} in your household</span>
          </div>
        ) : (
          recommendations &&
          recommendations.length > 0 && (
            <div className="figure">
              <b>{recommendations.length}</b>
              <span>picks in stock</span>
            </div>
          )
        )}
      </header>

      {recommendations === null ? (
        <p className="empty">Finding groceries that fit you…</p>
      ) : recommendations.length === 0 ? (
        <div className="panel empty">
          <Icon name="home" />
          <strong>No recommendations yet.</strong>
          <span>Update your dietary choices in Profile, or scan a product to check it.</span>
        </div>
      ) : (
        <section aria-label="Recommended groceries" className="grid grid-2">
          {recommendations.map((item) => {
            const isAdded = addedIds.includes(item.product_id);
            return (
              <article key={item.product_id} className="label-panel">
                <StatusBadge bar status={item.status} />
                <h2>{item.name}</h2>
                <hr className="rule-heavy" />
                <div className="figure-row">
                  <span>Suggested quantity:</span> <b>{item.quantity}</b>
                </div>
                <hr className="rule-mid" />
                {item.aisle && (
                  <span className="location">
                    <Icon name="pin" />
                    Aisle {item.aisle} · Shelf {item.shelf} · Bin {item.bin}
                  </span>
                )}
                <p className="why">{item.rationale}</p>
                <button
                  className={`btn btn-block ${isAdded ? "btn-done" : "btn-primary"}`}
                  style={{ marginTop: "auto" }}
                  type="button"
                  onClick={() => void handleAdd(item)}
                >
                  {isAdded ? (
                    <>
                      <Icon name="check" /> Added to cart
                    </>
                  ) : (
                    "Add to cart"
                  )}
                </button>
              </article>
            );
          })}
        </section>
      )}

      <RecipeSheet />
    </main>
  );
}
