export default function Reports() {
  async function download(type: "donor" | "grant") {
    const response = await fetch(`/reports/${type}`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (!response.ok) throw new Error("Report generation failed");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${type}-report.docx`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return <main className="space-y-4 p-6"><h1 className="text-2xl font-semibold">Reports</h1><button className="mr-2 rounded bg-slate-900 px-3 py-2 text-white" onClick={() => download("donor")}>Download donor report</button><button className="rounded bg-slate-900 px-3 py-2 text-white" onClick={() => download("grant")}>Download grant report</button></main>;
}
