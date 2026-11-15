// One authored 24px stroke icon set so every icon shares weight and style.
const paths = {
  home: "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  scan: "M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M8 8v8M11 8v8M14 8v8M17 8v8",
  cart: "M3 4h2l2.4 11.2a1 1 0 0 0 1 .8h9.2a1 1 0 0 0 1-.8L20 8H6.2M9 20.5h.01M17 20.5h.01",
  recipes: "M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11M9 8h6",
  profile: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0",
  checkout: "M9 11l3 3 8-8M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9",
  audit: "M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1zM8 5H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2M9 12h6M9 16h4",
  restock: "M12 3v12M7 10l5 5 5-5M4 21h16",
  upload: "M12 15V3M7 8l5-5 5 5M4 21h16",
  lots: "M3 7l9-4 9 4-9 4zM3 12l9 4 9-4M3 17l9 4 9-4",
  analytics: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  reports: "M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5M9 13h6M9 17h6",
  queue: "M12 7v5l3 2M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z",
  logout: "M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4M10 17l-5-5 5-5M5 12h11",
  camera: "M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  check: "M5 12.5l4.5 4.5L19 7.5",
  alert: "M12 8v5M12 16.5h.01M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
  stop: "M7 7l10 10M17 7 7 17",
  pin: "M12 21s-7-6.1-7-11.5a7 7 0 0 1 14 0C19 14.9 12 21 12 21zM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  chevron: "M6 15l6-6 6 6",
  list: "M9 6h11M9 12h11M9 18h11M4.5 6l.01 0M4.5 12l.01 0M4.5 18l.01 0",
  eye: "M2.2 12C3.3 9.5 6.8 5 12 5s8.7 4.5 9.8 7c-1.1 2.5-4.6 7-9.8 7s-8.7-4.5-9.8-7zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  eyeOff: "M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.2A10.7 10.7 0 0 1 12 5c5.2 0 8.7 4.5 9.8 7a11.8 11.8 0 0 1-3.1 4.2M6.2 6.2C3.9 7.8 2.7 10.1 2.2 12c.5 1.4 1.9 4.2 5.4 6.1A10.7 10.7 0 0 0 12 19c1.1 0 2.1-.2 3-.5",
  // Cuisine tabs (RecipeGroups maps cuisine names to these).
  all: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
  american: "M4 11a8 6 0 0 1 16 0zM3 14h18M5 17h14v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2z",
  mexican: "M3 18a9 9 0 0 1 18 0zM7 13l1.5-1.5L10 13l2-2 2 2 1.5-1.5L17 13",
  italian: "M4 5c5-2 11-2 16 0L12 21zM9.5 9h.01M14 10h.01M11.5 13.5h.01",
  chinese: "M4 9h16l-2 11H6zM9 9V6a3 3 0 0 1 6 0v3",
  japanese: "M12 4 3 19h18zM8.5 13h7v6h-7z",
  korean: "M5 11h14v2a7 7 0 0 1-14 0zM3 11h18M9 7c1-1 1-2 0-3M15 7c1-1 1-2 0-3",
  thai: "M5 19c6 0 13-5 13-12a2 2 0 0 0-4 0c0 5-4 9-9 9a1.5 1.5 0 0 0 0 3zM16 5c0-1.5 1-2.5 2.5-2.5",
  vietnamese: "M3 12h18a9 9 0 0 1-18 0zM14 3l-3 9M20 4l-6 8",
  indian: "M4 11h16v2a7 7 0 0 1-7 7h-2a7 7 0 0 1-7-7zM2 11h20M9 4c-1 1 1 2 0 4M13 4c-1 1 1 2 0 4",
  mediterranean: "M5 20C9 15 13 10 19 4M8 16c-3 0-4-2-4-4 2 0 4 1 4 4zM11 12.5c0-3 2-4 4-4 0 2-1 4-4 4zM14 9c-3 0-4-2-4-4 2 0 4 1 4 4z",
  middleEastern: "M4 20 20 4M6.5 13.5l4 4M10 10l4 4M13.5 6.5l4 4",
  greek: "M4 5h16M6 8h12M8 8v10M12 8v10M16 8v10M5 21h14M6 18h12",
  french: "M3 15c3-6 15-6 18 0-3 2-6 1-9-2-3 3-6 4-9 2zM9 11l1 4M15 11l-1 4",
  southern: "M15 3a6 6 0 0 1 6 6c0 4-4 6-7 5l-3 3a2 2 0 1 1-3 3 2 2 0 1 1-3-3 2 2 0 1 1 3-3l3-3c-1-3 1-8 4-8z",
  caribbean: "M12 21c0-5 0-8-1-12M11 9C9 6 5 6 3 8M11 9c2-3 6-3 8-1M11 9C10 6 7 4 4 5M11 9c1-3 4-5 7-4M7 21h10",
  african: "M3 19h18M5 19a7 7 0 0 1 14 0M12 6v6M10 6h4",
} as const;

export type IconName = keyof typeof paths;

export default function Icon({ name }: { name: IconName }) {
  return (
    <svg aria-hidden="true" className="icon" viewBox="0 0 24 24">
      <path d={paths[name]} />
    </svg>
  );
}
