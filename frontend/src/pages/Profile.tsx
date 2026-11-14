import { useEffect, useState } from "react";

import { apiRequest, getMe } from "../api/client";

const choices = [
  "Low Sugar",
  "Low Sodium",
  "Heart Healthy",
  "Kidney Friendly",
  "Vegetarian",
  "Vegan",
  "Gluten Free",
  "Nut Allergy",
  "Dairy Free",
] as const;

export default function Profile() {
  const [selected, setSelected] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMe()
      .then((profile) => setSelected(profile.profile?.restrictions ?? []))
      .catch(() => undefined);
  }, []);

  function toggle(choice: string) {
    setSelected((current) =>
      current.includes(choice) ? current.filter((item) => item !== choice) : [...current, choice],
    );
    setSaved(false);
  }

  async function save() {
    setError("");
    setSaving(true);
    try {
      await apiRequest("/me/profile", {
        method: "PUT",
        body: { restrictions: selected, allergies: [], preferences: [] },
      });
      setSaved(true);
    } catch {
      setError("We couldn't save your choices. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main>
      <div className="hero-banner">
        <div>
          <span className="eyebrow-chip">Dietary profile</span>
          <h1 className="page-title">
            Dietary Restrictions &amp; Preferences
          </h1>
          <p className="page-subtitle">
            Choose any options that help us find a better grocery match. You can edit these anytime.
          </p>
        </div>
      </div>

      <section className="ui-card" style={{ maxWidth: "800px" }}>
        <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
          <legend className="stat-label" style={{ marginBottom: "1.25rem" }}>
            Dietary choices
          </legend>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.85rem", marginBottom: "1.75rem" }}>
            {choices.map((choice) => {
              const isChecked = selected.includes(choice);
              return (
                <label
                  key={choice}
                  className={`choice-pill ${isChecked ? "choice-pill-selected" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggle(choice)}
                  />
                  <span>{choice}</span>
                </label>
              );
            })}
          </div>
        </fieldset>

        {saved && (
          <div
            style={{
              background: "var(--pastel-green-bg)",
              border: "1px solid var(--pastel-green-border)",
              color: "var(--pastel-green-text)",
              padding: "0.75rem 1.25rem",
              borderRadius: "var(--radius-md)",
              marginBottom: "1.25rem",
              fontSize: "0.9rem",
              fontWeight: 600,
            }}
          >
            Your choices were saved.
          </div>
        )}

        {error && (
          <div
            style={{
              background: "var(--pastel-rose-bg)",
              border: "1px solid var(--pastel-rose-border)",
              color: "var(--pastel-rose-text)",
              padding: "0.75rem 1.25rem",
              borderRadius: "var(--radius-md)",
              marginBottom: "1.25rem",
              fontSize: "0.9rem",
            }}
          >
            {error}
          </div>
        )}

        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save choices"}
        </button>
      </section>
    </main>
  );
}
