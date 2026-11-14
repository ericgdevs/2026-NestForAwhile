import { useEffect, useState } from "react";

import { apiRequest, getMe } from "../api/client";
import Icon from "../components/Icon";

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
      <header className="page-head">
        <div>
          <h1>Dietary Restrictions &amp; Preferences</h1>
          <p>Pick anything that helps us find food that works for you. You can change these any time.</p>
        </div>
      </header>

      <section className="panel stack" style={{ maxWidth: "860px" }}>
        <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="field-label" style={{ marginBottom: "0.75rem" }}>
            Choose all that apply
          </legend>
          <div className="choices">
            {choices.map((choice) => (
              <label className="choice" key={choice}>
                <input checked={selected.includes(choice)} type="checkbox" onChange={() => toggle(choice)} />
                <span>{choice}</span>
              </label>
            ))}
          </div>
        </fieldset>

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
      </section>
    </main>
  );
}
