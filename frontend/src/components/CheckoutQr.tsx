import qrcode from "qrcode-generator";
import { useEffect, useState } from "react";

import { getMySession } from "../api/client";

/** The QR shows only the session token (never personal data); the ID is the typed fallback. */
export default function CheckoutQr() {
  const [session, setSession] = useState<{ Shopping_Session_Token: string; client_id: number } | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getMySession()
      .then(setSession)
      .catch(() => setError(true));
  }, []);

  if (error) return <p className="panel-sub">Your visit isn't active. Ask a volunteer for help.</p>;
  if (!session) return <p className="empty">Getting your checkout code…</p>;

  const qr = qrcode(0, "M");
  qr.addData(session.Shopping_Session_Token);
  qr.make();
  const size = qr.getModuleCount();
  const dark: string[] = [];
  for (let row = 0; row < size; row += 1) {
    for (let col = 0; col < size; col += 1) {
      if (qr.isDark(row, col)) dark.push(`M${col} ${row}h1v1h-1z`);
    }
  }

  return (
    <figure className="checkout-qr">
      <svg aria-label="Checkout QR code" role="img" shapeRendering="crispEdges" viewBox={`-2 -2 ${size + 4} ${size + 4}`}>
        <rect fill="#fff" height={size + 4} width={size + 4} x={-2} y={-2} />
        <path d={dark.join("")} fill="#0b1b33" />
      </svg>
      <figcaption>
        Client ID <b className="tabular">{session.client_id}</b>
      </figcaption>
    </figure>
  );
}
