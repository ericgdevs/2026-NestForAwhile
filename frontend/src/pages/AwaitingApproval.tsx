import Icon from "../components/Icon";

// Epic 1: no shopping session until a Warehouse Manager approves a new (Pending) account.
export default function AwaitingApproval() {
  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Almost ready</h1>
          <p>Your account is waiting for staff approval.</p>
        </div>
      </header>
      <section className="label-panel stack" style={{ maxWidth: "36rem" }}>
        <p className="status-badge status-badge-capped status-bar">
          <Icon name="queue" /> Waiting for staff approval
        </p>
        <ol className="steps">
          <li>Show a staff member your ID at the front desk.</li>
          <li>Once they approve your account, sign out and sign in again to start shopping.</li>
        </ol>
        <a className="btn btn-secondary" href="/profile">
          <Icon name="profile" /> Review your household
        </a>
      </section>
    </main>
  );
}
