import JsBarcode from "jsbarcode";
import qrcode from "qrcode-generator";
import { useEffect, useRef, useState } from "react";

import { getProductLabels } from "../api/client";
import Icon from "../components/Icon";

function QrSvg({ sku }: { sku: string }) {
  const qr = qrcode(0, "M");
  qr.addData(sku);
  qr.make();
  const size = qr.getModuleCount();
  const dark: string[] = [];
  for (let row = 0; row < size; row += 1) {
    for (let col = 0; col < size; col += 1) {
      if (qr.isDark(row, col)) dark.push(`M${col} ${row}h1v1h-1z`);
    }
  }
  return (
    <svg aria-label={`QR code for ${sku}`} className="label-qr" role="img" shapeRendering="crispEdges" viewBox={`-4 -4 ${size + 8} ${size + 8}`}>
      <rect fill="#fff" height={size + 8} width={size + 8} x={-4} y={-4} />
      <path d={dark.join("")} fill="#000" />
    </svg>
  );
}

function Code128Svg({ sku }: { sku: string }) {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (ref.current) JsBarcode(ref.current, sku, { format: "CODE128", displayValue: false, margin: 10, height: 80 });
  }, [sku]);
  return <svg aria-label={`Code 128 barcode for ${sku}`} className="label-code128" preserveAspectRatio="none" ref={ref} role="img" />;
}

export default function Labels() {
  const [products, setProducts] = useState<Array<{ sku: string; name: string }> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getProductLabels().then(setProducts).catch(() => setError(true));
  }, []);

  return (
    <main>
      <header className="page-head no-print">
        <div>
          <h1>Product labels</h1>
          <p>Print these and stick one on each product. The QR code and the barcode both hold the SKU.</p>
        </div>
        <button className="btn btn-primary" type="button" onClick={() => window.print()}>
          <Icon name="reports" />
          <span>Print labels</span>
        </button>
      </header>
      {error && (
        <p className="alert alert-danger" role="alert">
          <Icon name="alert" />
          We couldn't load the products. Try again.
        </p>
      )}
      {products?.length === 0 && <p className="panel empty">There are no products yet.</p>}
      <section aria-label="Product labels" className="label-grid">
        {products?.map((product) => (
          <article className="label-card" key={product.sku}>
            <QrSvg sku={product.sku} />
            <Code128Svg sku={product.sku} />
            <h2>{product.name}</h2>
            <p className="tabular">{product.sku}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
