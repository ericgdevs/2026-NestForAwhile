import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader, type IScannerControls } from "@zxing/browser";

type Props = {
  onDetected: (code: string) => void;
};

export default function BarcodeScanner({ onDetected }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    if (!videoRef.current) return;
    setError("");
    try {
      const reader = new BrowserMultiFormatReader();
      controlsRef.current = await reader.decodeFromConstraints(
        { audio: false, video: { facingMode: { ideal: "environment" } } },
        videoRef.current,
        (result) => {
          if (result) onDetected(result.getText());
        },
      );
      setActive(true);
    } catch {
      setError("Camera access is unavailable. You can enter a SKU manually.");
    }
  }

  function stop() {
    controlsRef.current?.stop();
    controlsRef.current = null;
    setActive(false);
  }

  useEffect(() => stop, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          height: active ? "240px" : "0px",
          overflow: "hidden",
          borderRadius: "var(--radius-lg)",
          background: "#000000",
          transition: "height 0.3s ease",
          display: active ? "block" : "none",
          position: "relative",
          boxShadow: "var(--shadow-card)",
          border: "2px solid #38bdf8",
        }}
      >
        <video
          ref={videoRef}
          playsInline
          muted
          aria-label="Barcode camera preview"
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>

      {active ? (
        <button onClick={stop} type="button" className="btn btn-secondary">
          Stop camera
        </button>
      ) : (
        <button onClick={start} type="button" className="btn btn-primary">
          <span aria-hidden="true">📷</span>
          <span>Scan with camera</span>
        </button>
      )}

      {error && (
        <p
          style={{
            margin: 0,
            fontSize: "0.88rem",
            color: "var(--pastel-rose-text)",
            background: "var(--pastel-rose-bg)",
            border: "1px solid var(--pastel-rose-border)",
            padding: "0.5rem 1rem",
            borderRadius: "var(--radius-pill)",
          }}
        >
          {error}
        </p>
      )}
    </div>
  );
}
