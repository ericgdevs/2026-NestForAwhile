import { useState } from 'react'
import { Check, Save } from 'lucide-react'

const choices = [
  'Low Sugar',
  'Low Sodium',
  'Heart Healthy',
  'Kidney Friendly',
  'Vegetarian',
  'Vegan',
  'Gluten Free',
  'Nut Allergy',
  'Dairy Free',
]

export function Profile() {
  const [selected, setSelected] = useState<string[]>([])
  const [saved, setSaved] = useState(false)

  function toggleChoice(choice: string) {
    setSaved(false)
    setSelected((current) => current.includes(choice) ? current.filter((item) => item !== choice) : [...current, choice])
  }

  function saveProfile() {
    setSaved(true)
  }

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Your preferences</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-sage-950">Dietary Restrictions &amp; Preferences</h1>
      <p className="mt-3 max-w-2xl text-sage-700">Choose anything that helps us make recommendations feel right for you. You can update these choices any time.</p>
      <section className="mt-8 rounded-3xl border border-sage-200 bg-white p-6 shadow-sm sm:p-8">
        <fieldset>
          <legend className="text-lg font-bold text-sage-950">What should we keep in mind?</legend>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {choices.map((choice) => {
              const isSelected = selected.includes(choice)
              return (
                <label key={choice} className={`flex cursor-pointer items-center gap-3 rounded-2xl border p-4 transition-colors ${isSelected ? 'border-sage-500 bg-sage-50' : 'border-sage-200 hover:bg-sage-50/60'}`}>
                  <input className="sr-only" type="checkbox" checked={isSelected} onChange={() => toggleChoice(choice)} />
                  <span aria-hidden="true" className={`grid size-6 place-items-center rounded-lg border ${isSelected ? 'border-sage-700 bg-sage-700 text-white' : 'border-sage-300 bg-white'}`}>{isSelected && <Check size={16} />}</span>
                  <span className="font-semibold text-sage-900">{choice}</span>
                </label>
              )
            })}
          </div>
        </fieldset>
        <div className="mt-8 flex flex-col gap-3 border-t border-sage-100 pt-6 sm:flex-row sm:items-center">
          <button type="button" onClick={saveProfile} className="inline-flex items-center justify-center gap-2 rounded-xl bg-sage-700 px-5 py-3 font-semibold text-white hover:bg-sage-800"><Save size={17} />Save preferences</button>
          {saved && <p role="status" className="text-sm font-semibold text-sage-700">Saved. We’ll use this to guide your recommendations.</p>}
        </div>
      </section>
    </div>
  )
}
