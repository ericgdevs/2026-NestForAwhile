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
    try {
      await apiRequest("/me/profile", {
        method: "PUT",
        body: { restrictions: selected, allergies: [], preferences: [] },
      });
      setSaved(true);
    } catch {
      setError("We couldn't save your choices. Please try again.");
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 p-6 text-slate-900">
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Dietary Restrictions &amp; Preferences</h1>
          <p className="mt-2 text-slate-600">
            Choose any options that help us find a better grocery match. You can edit these anytime.
          </p>
        </div>
        <fieldset className="grid gap-3 sm:grid-cols-2">
          <legend className="sr-only">Dietary choices</legend>
          {choices.map((choice) => (
            <label key={choice} className="flex items-center gap-3 rounded-lg bg-white p-4 shadow-sm">
              <input
                type="checkbox"
                checked={selected.includes(choice)}
                onChange={() => toggle(choice)}
              />
              <span>{choice}</span>
            </label>
          ))}
        </fieldset>
        {saved && <p className="text-sm text-emerald-800">Your choices were saved.</p>}
        {error && <p className="text-sm text-red-800">{error}</p>}
        <button className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white" onClick={save}>
          Save choices
        </button>
      </div>
    </main>
  );
}
