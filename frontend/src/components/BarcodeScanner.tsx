import { BrowserMultiFormatReader, type IScannerControls } from "@zxing/browser";
import { BarcodeFormat, DecodeHintType } from "@zxing/library";
import { useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";

import Icon from "./Icon";

type Props = {
  onDetected: (code: string) => void;
};

type Camera = { deviceId: string; label: string };

const HINTS = new Map<DecodeHintType, unknown>([
  [DecodeHintType.POSSIBLE_FORMATS, [BarcodeFormat.QR_CODE, BarcodeFormat.CODE_128, BarcodeFormat.EAN_13, BarcodeFormat.UPC_A]],
  [DecodeHintType.TRY_HARDER, true],
]);

const SIZE = { width: { ideal: 1280 }, height: { ideal: 720 } };

function cameraErrorMessage(error: unknown): string {
  const name = error instanceof DOMException ? error.name : "";
  if (name === "NotAllowedError" || name === "SecurityError") {
    return "Camera permission was denied. Allow camera access in your browser settings, or type the code below.";
  }
  if (name === "NotFoundError" || name === "OverconstrainedError") {
    return "No camera was found on this device. Type the code below instead.";
  }
  return "The camera couldn't start. Type the code below instead.";
}

export default function BarcodeScanner({ onDetected }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const [active, setActive] = useState(false);
  const [mirrored, setMirrored] = useState(false);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [error, setError] = useState("");

  function stop() {
    controlsRef.current?.stop();
    controlsRef.current = null;
    setActive(false);
  }

  // Preferring (not requiring) the back camera lets laptops fall back to their only camera.
  async function start(chosenId = "") {
    if (!videoRef.current) return;
    controlsRef.current?.stop();
    setError("");
    // The video must be visible before streaming: iOS Safari won't play a display:none video.
    flushSync(() => setActive(true));
    let finished = false;
    try {
      const video: MediaTrackConstraints = chosenId
        ? { deviceId: { exact: chosenId }, ...SIZE }
        : { facingMode: { ideal: "environment" }, ...SIZE };
      const reader = new BrowserMultiFormatReader(HINTS);
      const controls = await reader.decodeFromConstraints({ audio: false, video }, videoRef.current, (result) => {
        if (!result || finished) return;
        finished = true;
        stop();
        onDetected(result.getText().trim());
      });
      controlsRef.current = controls;
      if (finished) return stop();
      await describeCamera(videoRef.current);
    } catch (caught) {
      stop();
      setError(cameraErrorMessage(caught));
    }
  }

  // Labels only appear after permission is granted, so list cameras once the stream runs.
  async function describeCamera(video: HTMLVideoElement) {
    const track = (video.srcObject as MediaStream | null)?.getVideoTracks()[0];
    const current = track?.getSettings();
    setDeviceId(current?.deviceId ?? "");
    setMirrored(current?.facingMode === "user");
    const devices = (await navigator.mediaDevices?.enumerateDevices?.()) ?? [];
    setCameras(devices.filter((d) => d.kind === "videoinput").map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Camera ${i + 1}` })));
  }

  useEffect(() => {
    window.addEventListener("pagehide", stop);
    return () => {
      window.removeEventListener("pagehide", stop);
      controlsRef.current?.stop();
    };
  }, []);

  return (
    <div className="stack">
      <video
        aria-label="Barcode camera preview"
        className="camera"
        hidden={!active}
        muted
        playsInline
        ref={videoRef}
        style={mirrored ? { transform: "scaleX(-1)" } : undefined}
      />
      {active && (
        <p className="alert" role="status">
          <Icon name="camera" />
          Camera on. Hold a QR code or barcode steady in view.
        </p>
      )}
      {active && cameras.length > 1 && (
        <label className="field">
          <span className="field-label">Camera</span>
          <select className="input" value={deviceId} onChange={(event) => void start(event.target.value)}>
            {cameras.map((camera) => (
              <option key={camera.deviceId} value={camera.deviceId}>
                {camera.label}
              </option>
            ))}
          </select>
        </label>
      )}
      {active ? (
        <button className="btn btn-secondary btn-block" type="button" onClick={stop}>
          <Icon name="stop" />
          <span>Stop camera</span>
        </button>
      ) : (
        <button className="btn btn-primary btn-block" type="button" onClick={() => void start()}>
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
