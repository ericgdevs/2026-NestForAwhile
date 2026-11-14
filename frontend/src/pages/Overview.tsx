import { useEffect, useState } from "react";

import { getCapacity, getInventoryLots, getReplenishment } from "../api/client";
import Icon from "../components/Icon";
import { useAuth } from "../lib/auth";
import { canVisit } from "../lib/roles";

// `one`/`many` caption the page-head figure so "1 lot" and "3 lots" both read right.
type Fact = { label: string; value: number | null; href?: string; one: string; many: string };

// The first non-zero action item leads; everything else reads as label rows.
export function leadFact(facts: Fact[]): Fact | undefined {
  return facts.find((fact) => fact.href && fact.value) ?? facts[0];
}

export default function Overview() {
  const { user } = useAuth();
  const role = user!.role;
  const seesInventory = canVisit(role, "/lots");
  // Mirrors the server's /capacity roles; Director is denied there.
  const seesCapacity = role !== "Director";
  const [shoppers, setShoppers] = useState<number | null>(null);
  const [expiring, setExpiring] = useState<number | null>(null);
  const [lowStock, setLowStock] = useState<number | null>(null);

  useEffect(() => {
    if (seesCapacity) {
      getCapacity()
        .then((capacity) => setShoppers(capacity.Active_Floor_Shoppers))
        .catch(() => setShoppers(null));
    }
    if (seesInventory) {
      getInventoryLots()
        .then((lots) => setExpiring(lots.filter((lot) => lot.expiring_soon).length))
        .catch(() => setExpiring(null));
      getReplenishment()
        .then((items) => setLowStock(items.length))
        .catch(() => setLowStock(null));
    }
  }, [seesCapacity, seesInventory]);

  const facts: Fact[] = [
    ...(seesInventory
      ? [
          { label: "Lots expiring within 7 days", value: expiring, href: "/lots", one: "lot expiring within 7 days", many: "lots expiring within 7 days" },
          { label: "Items below threshold", value: lowStock, href: "/replenishment", one: "item below threshold", many: "items below threshold" },
        ]
      : []),
    ...(seesCapacity ? [{ label: "Active shoppers on the floor", value: shoppers, one: "shopper on the floor", many: "shoppers on the floor" }] : []),
  ];
  const lead = leadFact(facts);

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Overview</h1>
          <p>Today on the warehouse floor.</p>
        </div>
        {lead && (
          <div className="figure">
            <b>{lead.value ?? "—"}</b>
            <span>{lead.value === 1 ? lead.one : lead.many}</span>
          </div>
        )}
      </header>

      {seesInventory && expiring !== null && expiring > 0 && (
        <p className="alert alert-warn" role="alert" style={{ marginBottom: "1rem" }}>
          <Icon name="alert" />
          <span>
            {expiring} {expiring === 1 ? "lot expires" : "lots expire"} within seven days. <a href="/lots">Review lots</a>
          </span>
        </p>
      )}

      {facts.length > 0 ? (
        <section className="label-panel" style={{ maxWidth: "40rem" }}>
          <h2 className="panel-title">Today</h2>
          <dl className="facts">
            {facts.map((fact) => (
              <div key={fact.label}>
                <dt>{fact.href ? <a href={fact.href}>{fact.label}</a> : fact.label}</dt>
                <dd>{fact.value ?? "—"}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : (
        <div className="panel empty">
          <Icon name="analytics" />
          <strong>Your screens are in the menu.</strong>
          <span>Open Analytics for anonymized totals or Reports to download DOCX files.</span>
        </div>
      )}
    </main>
  );
}
