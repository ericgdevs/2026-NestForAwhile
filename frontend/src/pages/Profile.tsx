import { useEffect, useState } from "react";

import { getHousehold, saveHousehold } from "../api/client";
import HouseholdEditor from "../components/HouseholdEditor";
import Icon from "../components/Icon";
import { fromMember, toMemberInput, type MemberDraft } from "../lib/household";

export default function Profile() {
  const [members, setMembers] = useState<MemberDraft[] | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getHousehold()
      .then((household) => setMembers(household.members.map(fromMember)))
      .catch(() => setError("We couldn't load your household. Please try again."));
  }, []);

  function change(next: MemberDraft[]) {
    setMembers(next);
    setSaved(false);
  }

  async function save() {
    if (!members) return;
    setError("");
    setSaving(true);
    try {
      const household = await saveHousehold(members.map(toMemberInput));
      setMembers(household.members.map(fromMember));
      setSaved(true);
    } catch {
      setError("We couldn't save your choices. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main>
      <header className="page-head">
        <div>
          <h1>Your household</h1>
          <p>Everyone you shop for, and what works for each of them. You can change these any time.</p>
        </div>
        {members && (
          <div className="figure">
            <b>{members.length}</b>
            <span>{members.length === 1 ? "person" : "people"}</span>
          </div>
        )}
      </header>

      {members === null ? (
        error ? (
          <p className="alert alert-danger" role="alert">
            <Icon name="alert" />
            {error}
          </p>
        ) : (
          <p className="empty">Loading your household…</p>
        )
      ) : (
        <div className="stack" style={{ maxWidth: "860px" }}>
          <HouseholdEditor members={members} onChange={change} />
          {saved && (
            <p className="alert alert-ok" role="status">
              <Icon name="check" />
              Your choices were saved.
            </p>
          )}
          {error && (
            <p className="alert alert-danger" role="alert">
              <Icon name="alert" />
              {error}
            </p>
          )}
          <button className="btn btn-primary" disabled={saving} style={{ alignSelf: "flex-start" }} type="button" onClick={save}>
            {saving ? "Saving…" : "Save choices"}
          </button>
        </div>
      )}
    </main>
  );
}
