import { useState } from "react";

import { ALLERGY_CHOICES, CONDITIONS, DIET_CHOICES, emptyMember, toggle, type MemberDraft } from "../lib/household";
import Icon from "./Icon";

type Props = {
  members: MemberDraft[];
  onChange: (members: MemberDraft[]) => void;
  showConditions?: boolean;
};

type ListKey = "restrictions" | "allergies" | "conditions";

function ChoiceSet({
  legend,
  options,
  selected,
  onToggle,
}: {
  legend: string;
  options: readonly { value: string; label: string }[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <fieldset className="choice-set">
      <legend className="field-label">{legend}</legend>
      <div className="choices">
        {options.map((option) => (
          <label className="choice" key={option.value}>
            <input checked={selected.includes(option.value)} type="checkbox" onChange={() => onToggle(option.value)} />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

const asOptions = (values: readonly string[]) => values.map((value) => ({ value, label: value }));

// Sign-up and Profile both edit the household here: one card per person, or shared choices.
export default function HouseholdEditor({ members, onChange, showConditions = false }: Props) {
  const [shared, setShared] = useState(false);

  function setSharedChoices(on: boolean) {
    setShared(on);
    if (on) {
      const { restrictions, allergies } = members[0];
      onChange(members.map((member) => ({ ...member, restrictions, allergies })));
    }
  }

  function update(index: number, change: Partial<MemberDraft>) {
    onChange(members.map((member, i) => (i === index ? { ...member, ...change } : member)));
  }

  function toggleFor(index: number, key: ListKey, value: string) {
    if (shared && key !== "conditions") {
      const next = toggle(members[0][key], value);
      onChange(members.map((member) => ({ ...member, [key]: next })));
    } else {
      update(index, { [key]: toggle(members[index][key], value) });
    }
  }

  return (
    <div className="stack">
      {members.length > 1 && (
        <label className="choice" style={{ alignSelf: "flex-start" }}>
          <input checked={shared} type="checkbox" onChange={(event) => setSharedChoices(event.target.checked)} />
          <span>Use the same diet choices and allergies for everyone</span>
        </label>
      )}
      {members.map((member, index) => (
        <section className="panel stack" key={index} aria-label={member.nickname || `Person ${index + 1}`}>
          <div className="row" style={{ alignItems: "flex-end", flexWrap: "wrap" }}>
            <label className="field" style={{ flex: "1 1 12rem" }}>
              <span className="field-label">Nickname</span>
              <input
                className="input"
                maxLength={40}
                placeholder={`Person ${index + 1}`}
                value={member.nickname}
                onChange={(event) => update(index, { nickname: event.target.value })}
              />
            </label>
            <label className="field" style={{ flex: "0 1 7rem" }}>
              <span className="field-label">Age</span>
              <input
                className="input"
                inputMode="numeric"
                max={120}
                min={0}
                type="number"
                value={member.age}
                onChange={(event) => update(index, { age: event.target.value })}
              />
            </label>
            {members.length > 1 && (
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => onChange(members.filter((_, i) => i !== index))}
              >
                Remove
              </button>
            )}
          </div>
          {(!shared || index === 0) && (
            <>
              <ChoiceSet
                legend={shared ? "Diet choices for everyone" : "Diet choices"}
                options={asOptions(DIET_CHOICES)}
                selected={member.restrictions}
                onToggle={(value) => toggleFor(index, "restrictions", value)}
              />
              <ChoiceSet
                legend={shared ? "Allergies for everyone" : "Allergies"}
                options={ALLERGY_CHOICES}
                selected={member.allergies}
                onToggle={(value) => toggleFor(index, "allergies", value)}
              />
            </>
          )}
          {showConditions && (
            <ChoiceSet
              legend="Health conditions (optional)"
              options={CONDITIONS}
              selected={member.conditions}
              onToggle={(value) => toggleFor(index, "conditions", value)}
            />
          )}
        </section>
      ))}
      <button
        className="btn btn-secondary"
        style={{ alignSelf: "flex-start" }}
        type="button"
        onClick={() => onChange([...members, shared ? { ...emptyMember(), restrictions: members[0].restrictions, allergies: members[0].allergies } : emptyMember()])}
      >
        <Icon name="profile" /> Add a person
      </button>
    </div>
  );
}
