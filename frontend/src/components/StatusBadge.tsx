import type { components } from "../api/generated";

type SafetyStatus = components["schemas"]["SafetyStatus"];

const statusDetails: Record<
  SafetyStatus,
  { label: string; icon: string; classes: string }
> = {
  Approved: {
    label: "Good match",
    icon: "✓",
    classes: "bg-emerald-100 text-emerald-900",
  },
  Capped: {
    label: "Please check",
    icon: "!",
    classes: "bg-amber-100 text-amber-950",
  },
  Restricted: {
    label: "Not recommended",
    icon: "×",
    classes: "bg-red-100 text-red-900",
  },
};

export function StatusBadge({ status }: { status: SafetyStatus }) {
  const detail = statusDetails[status];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${detail.classes}`}
      role="status"
      aria-label={`${detail.label}: ${status}`}
    >
      <span aria-hidden="true">{detail.icon}</span>
      <span>{detail.label}</span>
    </span>
  );
}
