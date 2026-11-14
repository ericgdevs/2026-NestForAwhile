import { useEffect, useState } from "react";

import { getReplenishment } from "../api/client";
import Icon from "../components/Icon";

export default function Replenishment() {
  const [items, setItems] = useState<Awaited<ReturnType<typeof getReplenishment>>>([]);
  const [sort, setSort] = useState("priority");

  useEffect(() => {
    getReplenishment(sort).then(setItems).catch(() => setItems([]));
  }, [sort]);

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Restock</h1>
          <p>Items below their threshold, with where to put them.</p>
        </div>
        <div className="field" style={{ flexDirection: "row", alignItems: "center", gap: "0.5rem" }}>
          <label className="field-label" htmlFor="restock-sort">
            Sort by
          </label>
          <select className="input" id="restock-sort" value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="priority">Priority</option>
            <option value="location">Location</option>
            <option value="name">Name</option>
          </select>
        </div>
      </header>

      <section className="panel">
        {items.length === 0 ? (
          <div className="empty">
            <Icon name="check" />
            <strong>Everything is stocked.</strong>
            <span>All items are above their threshold.</span>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Item</th>
                  <th className="num" scope="col">On hand</th>
                  <th className="num" scope="col">Threshold</th>
                  <th scope="col">Location</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${item.product_id}-${item.aisle}-${item.bin}`}>
                    <td data-label="Item">
                      <strong>{item.name}</strong>
                    </td>
                    <td data-label="On hand" className="num">{item.quantity}</td>
                    <td data-label="Threshold" className="num">{item.reorder_threshold}</td>
                    <td data-label="Location">
                      <span className="location">
                        <Icon name="pin" />
                        Aisle {item.aisle} · Shelf {item.shelf} · Bin {item.bin}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
