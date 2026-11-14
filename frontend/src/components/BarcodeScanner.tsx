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
    <div className="space-y-3">
      <video
        ref={videoRef}
        className="aspect-video w-full rounded-lg bg-slate-950"
        playsInline
        muted
        aria-label="Barcode camera preview"
      />
      {active ? (
        <button className="rounded-lg border px-4 py-2" onClick={stop} type="button">
          Stop camera
        </button>
      ) : (
        <button className="rounded-lg bg-slate-900 px-4 py-2 text-white" onClick={start} type="button">
          Scan with camera
        </button>
      )}
      {error && <p className="text-sm text-amber-800">{error}</p>}
    </div>
  );
}
