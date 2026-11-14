import { BrowserMultiFormatReader } from '@zxing/browser'
import type { IScannerControls } from '@zxing/browser'
import { Camera, ScanLine, Square } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'

type BarcodeScannerProps = {
  onDetected: (code: string) => void
}

export function BarcodeScanner({ onDetected }: BarcodeScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const controlsRef = useRef<IScannerControls | undefined>(undefined)
  const [manualCode, setManualCode] = useState('')
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => () => controlsRef.current?.stop(), [])

  async function startCamera() {
    if (!videoRef.current) return
    setError('')
    try {
      const reader = new BrowserMultiFormatReader()
      controlsRef.current = await reader.decodeFromVideoDevice(undefined, videoRef.current, (result) => {
        if (result) {
          onDetected(result.getText())
          controlsRef.current?.stop()
          setScanning(false)
        }
      })
      setScanning(true)
    } catch {
      setError('We could not access your camera. You can enter the SKU below instead.')
      setScanning(false)
    }
  }

  function stopCamera() {
    controlsRef.current?.stop()
    setScanning(false)
  }

  function submitManualCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const code = manualCode.trim()
    if (code) onDetected(code)
  }

  return (
    <section className="rounded-3xl border border-sage-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex items-start gap-3"><ScanLine className="mt-1 text-sage-700" /><div><h2 className="text-lg font-bold text-sage-950">Check an item</h2><p className="mt-1 text-sm text-sage-700">Scan the barcode, or enter the product code manually.</p></div></div>
      <div className="mt-5 overflow-hidden rounded-2xl bg-sage-950">
        <video ref={videoRef} className="aspect-video w-full object-cover" muted playsInline aria-label="Barcode camera preview" />
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        {!scanning ? <button type="button" onClick={startCamera} className="inline-flex items-center gap-2 rounded-xl bg-sage-700 px-4 py-3 text-sm font-semibold text-white hover:bg-sage-800"><Camera size={17} />Use camera</button> : <button type="button" onClick={stopCamera} className="inline-flex items-center gap-2 rounded-xl border border-sage-300 px-4 py-3 text-sm font-semibold text-sage-800"><Square size={15} />Stop camera</button>}
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p>}
      <form className="mt-5 flex flex-col gap-3 sm:flex-row" onSubmit={submitManualCode}>
        <label className="sr-only" htmlFor="manual-sku">Product code</label>
        <input id="manual-sku" className="min-w-0 flex-1 rounded-xl border border-sage-300 px-3 py-3 text-sage-950" value={manualCode} onChange={(event) => setManualCode(event.target.value)} placeholder="Enter SKU or barcode" />
        <button type="submit" className="rounded-xl border border-sage-300 px-4 py-3 text-sm font-semibold text-sage-800 hover:bg-sage-50">Check code</button>
      </form>
    </section>
  )
}
