import { useEffect, useRef, useState } from "react";

import Icon, { type IconName } from "./Icon";

// blue/ok for plain counts; warn/stop only for things that need action.
export type StatTone = "blue" | "ok" | "warn" | "stop";
export type Stat = { label: string; value: number | string | null; href?: string; icon: IconName; tone: StatTone };

const COUNT_MS = 900;

/** Counts up from 0 the first time the figure scrolls into view ("50%" counts too). */
function CountUp({ value }: { value: number | string | null }) {
  const ref = useRef<HTMLElement>(null);
  const parsed = typeof value === "string" ? /^(\d+(?:\.\d+)?)(\D*)$/.exec(value) : null;
  const target = typeof value === "number" ? value : parsed ? Number(parsed[1]) : null;
  const suffix = parsed?.[2] ?? "";
  const canAnimate =
    typeof IntersectionObserver !== "undefined" && !window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const [shown, setShown] = useState(canAnimate ? 0 : target);

  useEffect(() => {
    if (target === null || !canAnimate || !ref.current) return setShown(target);
    setShown(0);
    let frame = 0;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      const start = performance.now();
      const tick = (now: number) => {
        const progress = Math.min((now - start) / COUNT_MS, 1);
        setShown(target * (1 - (1 - progress) ** 3)); // ease-out
        if (progress < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    });
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [target, canAnimate]);

  const places = target === null ? 0 : (String(target).split(".")[1]?.length ?? 0);
  const text =
    target === null || shown === null
      ? (value ?? "—")
      : shown.toLocaleString(undefined, { minimumFractionDigits: places, maximumFractionDigits: places }) + suffix;
  return <dd ref={ref}>{text}</dd>;
}

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
          <CountUp value={stat.value} />
        </div>
      ))}
    </dl>
  );
}
