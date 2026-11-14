import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader, type IScannerControls } from "@zxing/browser";

import Icon from "./Icon";

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
    <div className="stack">
      <video
        aria-label="Barcode camera preview"
        className="camera"
        hidden={!active}
        muted
        playsInline
        ref={videoRef}
      />
      {active ? (
        <button className="btn btn-secondary btn-block" type="button" onClick={stop}>
          Stop camera
        </button>
      ) : (
        <button className="btn btn-primary btn-block" type="button" onClick={start}>
          <Icon name="camera" />
          <span>Scan with camera</span>
        </button>
      )}
      {error && (
        <p className="alert alert-warn" role="alert">
          <Icon name="alert" />
          {error}
        </p>
      )}
    </div>
  );
}
