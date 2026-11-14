import type { NotFor } from "../api/client";
import Icon from "./Icon";

// Under a product's status bar: who in the household it isn't for, and why (nicknames only).
export default function NotForLine({ notFor, allergy = false }: { notFor?: NotFor[]; allergy?: boolean }) {
  if (!notFor?.length) return null;
  return (
    <p className={`not-for ${allergy ? "not-for-allergy" : ""}`}>
      <Icon name={allergy ? "alert" : "profile"} />
      <span>
        {notFor.map((who, index) => (
          <span key={who.nickname}>
            {index > 0 && "; "}
            Not for <strong>{who.nickname}</strong>: {who.reason}
          </span>
        ))}
        {allergy && " (allergy)"}
      </span>
    </p>
  );
}
