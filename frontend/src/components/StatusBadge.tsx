import type { components } from "../api/generated";

type SafetyStatus = components["schemas"]["SafetyStatus"];

const statusDetails: Record<
  SafetyStatus,
  { label: string; icon: string }
> = {
  Approved: {
    label: "Good match",
    icon: "✓",
  },
  Capped: {
    label: "Please check",
    icon: "!",
  },
  Restricted: {
    label: "Not recommended",
    icon: "×",
  },
};

export function StatusBadge({ status }: { status: SafetyStatus }) {
  const detail = statusDetails[status];
  return (
    <span
      className={`status-badge status-badge-${status.toLowerCase()}`}
      role="status"
      aria-label={`${detail.label}: ${status}`}
    >
      <span aria-hidden="true">{detail.icon}</span>
      <span>{detail.label}</span>
    </span>
  );
}
