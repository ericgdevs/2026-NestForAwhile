import { useEffect, useState } from "react";

import { approveClient, getPendingClients, type PendingClient } from "../api/client";
import Icon from "../components/Icon";

// Warehouse Manager only: the one screen that shows a client's real name, to verify who is approved.
export default function Approvals() {
  const [clients, setClients] = useState<PendingClient[] | null>(null);
  const [approved, setApproved] = useState<number[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getPendingClients()
      .then(setClients)
      .catch(() => setError("We couldn't load pending accounts."));
  }, []);

  async function approve(client: PendingClient) {
    setError("");
    try {
      await approveClient(client.client_id);
      setApproved((ids) => [...ids, client.client_id]);
    } catch {
      setError(`We couldn't approve client #${client.client_id}. Please try again.`);
    }
  }

  const waiting = clients?.filter((client) => !approved.includes(client.client_id)) ?? [];

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Approvals</h1>
          <p>New accounts can shop right away but can't check out until you approve them. Check their ID at the desk.</p>
        </div>
        {clients && (
          <div className="figure">
            <b>{waiting.length}</b>
            <span>waiting</span>
          </div>
        )}
      </header>

      {error && (
        <p className="alert alert-danger" role="alert" style={{ marginBottom: "1rem" }}>
          <Icon name="alert" />
          {error}
        </p>
      )}
      {approved.length > 0 && (
        <p className="alert alert-ok" role="status" style={{ marginBottom: "1rem" }}>
          <Icon name="check" />
          Approved {approved.length} {approved.length === 1 ? "account" : "accounts"}.
        </p>
      )}

      <section className="panel">
        {clients === null ? (
          <p className="empty">Loading pending accounts…</p>
        ) : waiting.length === 0 ? (
          <div className="empty">
            <Icon name="check" />
            <strong>No accounts are waiting.</strong>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Client</th>
                  <th scope="col">Name</th>
                  <th className="num" scope="col">Household</th>
                  <th scope="col">Signed up</th>
                  <th scope="col">
                    <span className="sr-only">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {waiting.map((client) => (
                  <tr key={client.client_id}>
                    <td data-label="Client">
                      <strong>#{client.client_id}</strong>
                    </td>
                    <td data-label="Name">{client.name}</td>
                    <td data-label="Household" className="num">
                      {client.Household_Size}
                    </td>
                    <td data-label="Signed up">{new Date(client.created_at).toLocaleString()}</td>
                    <td data-label="Action">
                      <button className="btn btn-primary" type="button" onClick={() => void approve(client)}>
                        Approve #{client.client_id}
                      </button>
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
