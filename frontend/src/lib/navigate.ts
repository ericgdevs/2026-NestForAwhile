import { useSyncExternalStore } from "react";

const NAVIGATE_EVENT = "app:navigate";

/** Go to another screen without reloading the page, so the session and visit stay in memory. */
export function navigate(to: string, replace = false) {
  window.history[replace ? "replaceState" : "pushState"]({}, "", to);
  window.dispatchEvent(new Event(NAVIGATE_EVENT));
  window.scrollTo(0, 0);
}

const subscribe = (notify: () => void) => {
  window.addEventListener(NAVIGATE_EVENT, notify);
  window.addEventListener("popstate", notify);
  return () => {
    window.removeEventListener(NAVIGATE_EVENT, notify);
    window.removeEventListener("popstate", notify);
  };
};

export const usePath = () => useSyncExternalStore(subscribe, () => window.location.pathname);

/** Plain left-clicks on same-site links navigate in the app; new tabs, downloads and modifier clicks stay native. */
export function onLinkClick(event: MouseEvent) {
  const link = (event.target as Element | null)?.closest?.("a[href]") as HTMLAnchorElement | null;
  const plain = event.button === 0 && !(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey);
  if (event.defaultPrevented || !link || !plain) return;
  if ((link.target && link.target !== "_self") || link.hasAttribute("download")) return;
  if (link.origin !== window.location.origin) return;
  event.preventDefault();
  navigate(link.pathname + link.search + link.hash);
}
