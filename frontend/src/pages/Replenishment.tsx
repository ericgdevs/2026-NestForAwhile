import { useEffect, useState } from "react";
import { getReplenishment } from "../api/client";

export default function Replenishment() {
  const [items, setItems] = useState<Awaited<ReturnType<typeof getReplenishment>>>([]);
  const [sort, setSort] = useState("priority");
  useEffect(() => { getReplenishment(sort).then(setItems); }, [sort]);
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">Replenishment</h1><select className="rounded border p-2" value={sort} onChange={(event) => setSort(event.target.value)}><option value="priority">Priority</option><option value="location">Location</option><option value="name">Name</option></select><ul className="space-y-2">{items.map((item) => <li className="rounded bg-white p-3 shadow" key={`${item.product_id}-${item.aisle}-${item.bin}`}>{item.name}: {item.quantity}/{item.reorder_threshold} · {item.aisle}/{item.shelf}/{item.bin}</li>)}</ul></main>;
}
