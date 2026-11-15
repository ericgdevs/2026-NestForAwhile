import { useEffect, useState } from "react";

import { getAnalytics, getCapacity, getInventoryLots, getPendingClients, getReplenishment } from "../api/client";
import Icon from "../components/Icon";
import StatGrid, { type Stat } from "../components/StatGrid";
import { useAuth } from "../lib/auth";
import { canVisit } from "../lib/roles";

// `one`/`many` caption the page-head figure so "1 lot" and "3 lots" both read right.
type Fact = Stat & { value: number | null; one: string; many: string };

// The first non-zero action item leads; everything else reads as label rows.
export function leadFact(facts: Fact[]): Fact | undefined {
  return facts.find((fact) => fact.href && fact.value) ?? facts[0];
}

export default function Overview() {
  const { user } = useAuth();
  const role = user!.role;
  const seesInventory = canVisit(role, "/lots");
  const seesApprovals = canVisit(role, "/approvals");
  // Mirrors the server's /capacity roles; Director is denied there.
  const seesCapacity = role !== "Director";
  // Directors can't read floor or stock; their overview is the anonymized totals they can read.
  const isDirector = role === "Director";
  const [totals, setTotals] = useState<Awaited<ReturnType<typeof getAnalytics>> | null>(null);
  const [shoppers, setShoppers] = useState<number | null>(null);
  const [expiring, setExpiring] = useState<number | null>(null);
  const [lowStock, setLowStock] = useState<number | null>(null);
  const [pending, setPending] = useState<number | null>(null);

  useEffect(() => {
    if (isDirector) {
      getAnalytics()
        .then(setTotals)
        .catch(() => setTotals(null));
    }
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
    if (seesApprovals) {
      getPendingClients()
        .then((clients) => setPending(clients.length))
        .catch(() => setPending(null));
    }
  }, [isDirector, seesApprovals, seesCapacity, seesInventory]);

  const facts: Fact[] = [
    ...(seesApprovals
      ? [{ label: "Waiting for approval", value: pending, href: "/approvals", one: "account waiting for approval", many: "accounts waiting for approval", icon: "profile" as const, tone: "blue" as const }]
      : []),
    ...(seesInventory
      ? [
          { label: "Lots expiring within 7 days", value: expiring, href: "/lots", one: "lot expiring within 7 days", many: "lots expiring within 7 days", icon: "alert" as const, tone: "warn" as const },
          { label: "Items below threshold", value: lowStock, href: "/replenishment", one: "item below threshold", many: "items below threshold", icon: "restock" as const, tone: "stop" as const },
        ]
      : []),
    ...(isDirector
      ? [
          { label: "Families served", value: totals?.families_served ?? null, one: "family served to date", many: "families served to date", icon: "home" as const, tone: "blue" as const },
          { label: "Visits completed", value: totals?.visits_completed ?? null, one: "visit completed", many: "visits completed", icon: "checkout" as const, tone: "ok" as const },
          { label: "Pounds distributed", value: totals?.pounds_distributed ?? null, one: "pound distributed", many: "pounds distributed", icon: "cart" as const, tone: "blue" as const },
          { label: "Units given out", value: totals?.inventory_usage ?? null, one: "unit given out", many: "units given out", icon: "lots" as const, tone: "ok" as const },
          { label: "Lots expiring within 7 days", value: totals?.waste_reduction.expiring_soon_lots ?? null, one: "lot expiring within 7 days", many: "lots expiring within 7 days", icon: "alert" as const, tone: "warn" as const },
        ]
      : []),
    ...(seesCapacity ? [{ label: "Active shoppers on the floor", value: shoppers, one: "shopper on the floor", many: "shoppers on the floor", icon: "queue" as const, tone: "blue" as const }] : []),
  ];
  const lead = leadFact(facts);

  return (
    <main>
      <header className="page-head page-head-plain">
        <div>
          <h1>Overview</h1>
          <p>{isDirector ? "Anonymized totals to date. Open Analytics for the full breakdown." : "Today on the warehouse floor."}</p>
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
        <section aria-label={isDirector ? "Totals to date" : "Today"}>
          <h2 className="panel-title" style={{ marginBottom: "1rem" }}>
            {isDirector ? "Totals to date" : "Today"}
          </h2>
          <StatGrid stats={facts} />
        </section>
      ) : (
        <div className="panel empty">
          <Icon name="analytics" />
          <strong>Your screens are in the menu.</strong>
          <span>Open Analytics for anonymized totals.</span>
        </div>
      )}
    </main>
  );
}
