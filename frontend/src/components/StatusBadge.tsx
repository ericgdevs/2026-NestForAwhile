import type { components } from "../api/generated";
import Icon, { type IconName } from "./Icon";

type SafetyStatus = components["schemas"]["SafetyStatus"];

const statusDetails: Record<SafetyStatus, { label: string; icon: IconName }> = {
  Approved: { label: "Good match", icon: "check" },
  Capped: { label: "Please check", icon: "alert" },
  Restricted: { label: "Not recommended", icon: "stop" },
};

// `bar` renders the status as the top bar of a product label panel.
export function StatusBadge({ status, bar = false }: { status: SafetyStatus; bar?: boolean }) {
  const detail = statusDetails[status];
  return (
    <span
      className={`status-badge status-badge-${status.toLowerCase()} ${bar ? "status-bar" : ""}`}
      role="status"
      aria-label={`${detail.label}: ${status}`}
    >
      <Icon name={detail.icon} />
      <span>{detail.label}</span>
    </span>
  );
}
