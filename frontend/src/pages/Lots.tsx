import { useEffect, useState } from "react";

import { getInventoryLots } from "../api/client";
import Icon from "../components/Icon";

export default function Lots() {
  const [lots, setLots] = useState<Awaited<ReturnType<typeof getInventoryLots>>>([]);

  useEffect(() => {
    getInventoryLots().then(setLots).catch(() => setLots([]));
  }, []);

  const expiringCount = lots.filter((lot) => lot.expiring_soon).length;

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Lots, oldest first</h1>
          <p>Use the top lot first. Lots expiring within seven days are flagged.</p>
        </div>
        {expiringCount > 0 && (
          <div className="figure">
            <b>{expiringCount}</b>
            <span>expiring soon</span>
          </div>
        )}
      </header>

      {expiringCount > 0 && (
        <p className="alert alert-warn" role="alert" style={{ marginBottom: "1rem" }}>
          <Icon name="alert" />
          Some lots expire within seven days.
        </p>
      )}

      <section className="panel">
        {lots.length === 0 ? (
          <div className="empty">
            <Icon name="lots" />
            <strong>No inventory lots recorded.</strong>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Lot</th>
                  <th scope="col">Product</th>
                  <th scope="col">Expires</th>
                  <th className="num" scope="col">Units</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((lot) => (
                  <tr className={lot.expiring_soon ? "row-warn" : undefined} key={lot.lot_id}>
                    <td data-label="Lot">
                      <strong>#{lot.lot_id}</strong>
                    </td>
                    <td data-label="Product">Product #{lot.product_id}</td>
                    <td data-label="Expires">{lot.expiration_date}</td>
                    <td data-label="Units" className="num">{lot.quantity}</td>
                    <td data-label="Status">
                      {lot.expiring_soon ? (
                        <span className="status-badge status-badge-capped">
                          <Icon name="alert" /> Expiring soon
                        </span>
                      ) : (
                        <span className="location">OK</span>
                      )}
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
