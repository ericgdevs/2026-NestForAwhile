import Icon, { type IconName } from "./Icon";

// blue/ok for plain counts; warn/stop only for things that need action.
export type StatTone = "blue" | "ok" | "warn" | "stop";
export type Stat = { label: string; value: number | string | null; href?: string; icon: IconName; tone: StatTone };

/** One card per number (icon, label, big coloured value); shared by Overview and Analytics. */
export default function StatGrid({ stats }: { stats: Stat[] }) {
  return (
    <dl className="stat-grid">
      {stats.map((stat) => (
        // A warning colour on a zero would cry wolf, so zero reads as fine.
        <div className={`stat-card stat-${stat.value === 0 && stat.tone !== "blue" ? "ok" : stat.tone}`} key={stat.label}>
          <dt>
            <span className="stat-icon">
              <Icon name={stat.icon} />
            </span>
            {stat.href ? <a href={stat.href}>{stat.label}</a> : stat.label}
          </dt>
          <dd>{stat.value === null ? "—" : stat.value.toLocaleString()}</dd>
        </div>
      ))}
    </dl>
  );
}
