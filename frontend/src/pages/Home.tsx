import { useEffect, useState } from "react";

import {
  getHousehold,
  getRecommendations,
  getShoppingList,
  saveCartItem,
  type ListLine,
  type Member,
  type Recommendation,
} from "../api/client";
import BarcodeScanner from "../components/BarcodeScanner";
import Icon from "../components/Icon";
import ListAdder from "../components/ListAdder";
import NotForLine from "../components/NotForLine";
import { StatusBadge } from "../components/StatusBadge";
import { ALLERGY_CHOICES } from "../lib/household";

const allergyLabel = (value: string) => ALLERGY_CHOICES.find((choice) => choice.value === value)?.label ?? value;

// Diet choices and allergies only: medical conditions stay on the Profile page.
function HouseholdSummary({ members }: { members: Member[] | null }) {
  return (
    <section aria-label="Your household" className="panel stack" style={{ flex: 1 }}>
      <div className="panel-title panel-title-row">
        <h2>Your household</h2>
        <a className="btn btn-secondary btn-compact" href="/profile">
          <Icon name="profile" /> Edit household
        </a>
      </div>
      {members === null ? (
        <p className="panel-sub">Loading your household…</p>
      ) : members.length === 0 ? (
        <p className="panel-sub">Add the people you shop for so picks fit everyone.</p>
      ) : (
        <ul className="household-list">
          {members.map((member, index) => (
            <li key={`${member.nickname}-${index}`}>
              <strong>
                {member.nickname}
                {member.age !== null && <span className="panel-sub"> · {member.age}</span>}
              </strong>
              <span className="household-tags">
                {member.restrictions.map((choice) => (
                  <span className="tag" key={choice}>
                    {choice}
                  </span>
                ))}
                {member.allergies.map((allergy) => (
                  <span className="tag tag-allergy" key={allergy}>
                    <Icon name="alert" />
                    {allergyLabel(allergy)}
                  </span>
                ))}
                {!member.restrictions.length && !member.allergies.length && <span className="panel-sub">No restrictions</span>}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// Home's scanner hands off to the Scan page, which owns the full result, swaps, and recipes.
const openScan = (code: string) => window.location.assign(`/scan?code=${encodeURIComponent(code)}`);

export default function Home({ householdSize }: { householdSize?: number }) {
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null);
  const [addedIds, setAddedIds] = useState<number[]>([]);
  const [listItems, setListItems] = useState<ListLine[] | null>(null);
  const [members, setMembers] = useState<Member[] | null>(null);

  useEffect(() => {
    getRecommendations().then(setRecommendations).catch(() => setRecommendations([]));
    getShoppingList()
      .then((list) => setListItems(list.items))
      .catch(() => setListItems(null));
    getHousehold()
      .then((household) => setMembers(household.members))
      .catch(() => setMembers([]));
  }, []);

  const listLeft = listItems?.filter((line) => !line.ticked).length ?? 0;

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
          <h1>Epic-Cure Food System</h1>
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

      <div className="grid grid-2" style={{ marginBottom: "2rem" }}>
        <section aria-label="Grocery list" className="panel stack">
          <h2 className="panel-title">Grocery list</h2>
          {listItems && (
            <p className="panel-sub">
              {listLeft} {listLeft === 1 ? "item" : "items"} left to find
            </p>
          )}
          <ListAdder onAdded={setListItems} />
          <a className="btn btn-secondary" href="/list">
            <Icon name="list" /> Open full list
          </a>
        </section>

        <div className="stack">
          <section aria-label="Scan a product" className="panel stack">
            <h2 className="panel-title">Scan a product</h2>
            <p className="panel-sub">Check whether one item fits your household.</p>
            <BarcodeScanner onDetected={openScan} />
            <form
              className="inline-form"
              onSubmit={(event) => {
                event.preventDefault();
                const code = new FormData(event.currentTarget).get("code");
                if (typeof code === "string" && code.trim()) openScan(code.trim());
              }}
            >
              <label className="sr-only" htmlFor="home-sku">
                SKU or barcode
              </label>
              <input className="input" id="home-sku" name="code" placeholder="Or type the SKU" />
              <button className="btn btn-primary" type="submit">
                Check
              </button>
            </form>
          </section>
          <HouseholdSummary members={members} />
        </div>
      </div>

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
                <NotForLine allergy={item.allergy_match} notFor={item.not_for} />
                <div className="figure-row">
                  <h2>{item.name}</h2>
                  <span className="pick-qty">
                    <span>Suggested quantity:</span> <b>{item.quantity}</b>
                  </span>
                </div>
                <hr className="rule-heavy" />
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

    </main>
  );
}
