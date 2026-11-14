import { useEffect, useState } from "react";
import { getInventoryLots } from "../api/client";

export default function Lots() {
  const [lots, setLots] = useState<Awaited<ReturnType<typeof getInventoryLots>>>([]);
  useEffect(() => { getInventoryLots().then(setLots); }, []);
  const expiring = lots.some((lot) => lot.expiring_soon);
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">FIFO lots</h1>{expiring && <p role="alert" className="rounded bg-amber-100 p-3">Some lots expire within seven days.</p>}<ul>{lots.map((lot) => <li key={lot.lot_id}>{lot.product_id} · {lot.quantity} · {lot.expiration_date}{lot.expiring_soon ? " · expiring soon" : ""}</li>)}</ul></main>;
}
