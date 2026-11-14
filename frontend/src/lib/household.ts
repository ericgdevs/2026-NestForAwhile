import type { Member, MemberInput } from "../api/client";

// Values must match the backend vocabulary (rules/tiers.py DIETARY_TIER_IDS).
export const DIET_CHOICES = [
  "Low Sugar",
  "Low Sodium",
  "Heart Healthy",
  "Kidney Friendly",
  "Vegetarian",
  "Vegan",
  "Gluten Free",
  "Dairy Free",
] as const;

export const ALLERGY_CHOICES = [
  { value: "Nut Allergy", label: "Nut allergy" },
  { value: "Dairy Free", label: "Dairy allergy" },
  { value: "Gluten Free", label: "Gluten allergy" },
] as const;

// Optional ICD-10 codes (Epic 2): stored encrypted in Client_Medical_Profile and mapped to diet
// choices by the rules matrix (backend clinical_rules_matrix.json).
export const CONDITIONS = [
  { value: "E11", label: "Type 2 diabetes" },
  { value: "I10", label: "High blood pressure" },
  { value: "I25", label: "Heart disease" },
  { value: "N18", label: "Chronic kidney disease" },
  { value: "K90.0", label: "Celiac disease" },
] as const;

export type MemberDraft = {
  nickname: string;
  age: string;
  restrictions: string[];
  allergies: string[];
  conditions: string[];
};

export const emptyMember = (): MemberDraft => ({
  nickname: "",
  age: "",
  restrictions: [],
  allergies: [],
  conditions: [],
});

export const fromMember = (member: Member): MemberDraft => ({
  nickname: member.nickname,
  age: member.age === null ? "" : String(member.age),
  restrictions: member.restrictions,
  allergies: member.allergies,
  conditions: member.conditions ?? [],
});

export function toMemberInput(draft: MemberDraft): MemberInput {
  const age = draft.age.trim() === "" ? null : Number(draft.age);
  return {
    nickname: draft.nickname.trim() || undefined,
    age: age !== null && Number.isFinite(age) ? age : null,
    restrictions: draft.restrictions,
    allergies: draft.allergies,
    conditions: draft.conditions,
  };
}

export const toggle = (list: string[], value: string) =>
  list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
