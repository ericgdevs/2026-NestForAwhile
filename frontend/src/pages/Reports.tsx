import { Download, FileText } from 'lucide-react'
import { useState } from 'react'

export function Reports() {
  const [type, setType] = useState('distribution')
  const [period, setPeriod] = useState('month')
  const [downloaded, setDownloaded] = useState(false)

  function downloadReport() {
    const blob = new Blob([`Nest For Awhile report: ${type}, ${period}`], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `nest-report-${period}.docx`
    anchor.click()
    URL.revokeObjectURL(url)
    setDownloaded(true)
  }

  return <div className="mx-auto max-w-3xl"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-sage-600">Manager tools</p><h1 className="mt-2 text-3xl font-bold text-sage-950">Reports</h1><p className="mt-3 text-sage-700">Create an aggregate report without exposing client details.</p><section className="mt-8 rounded-3xl border border-sage-200 bg-white p-6 shadow-sm sm:p-8"><div className="flex items-start gap-3"><FileText className="mt-1 text-sage-700" /><div><h2 className="text-xl font-bold text-sage-950">Export a report</h2><p className="mt-1 text-sm text-sage-700">Choose a report type and time period, then download a DOCX.</p></div></div><div className="mt-8 grid gap-5 sm:grid-cols-2"><label className="text-sm font-semibold text-sage-950">Report type<select className="mt-2 w-full rounded-xl border border-sage-300 px-3 py-3" value={type} onChange={(event) => { setType(event.target.value); setDownloaded(false) }}><option value="distribution">Distribution summary</option><option value="inventory">Inventory usage</option><option value="donor">Donor and grant summary</option></select></label><label className="text-sm font-semibold text-sage-950">Period<select className="mt-2 w-full rounded-xl border border-sage-300 px-3 py-3" value={period} onChange={(event) => { setPeriod(event.target.value); setDownloaded(false) }}><option value="week">This week</option><option value="month">This month</option><option value="quarter">This quarter</option></select></label></div><button className="mt-8 inline-flex items-center gap-2 rounded-xl bg-sage-700 px-4 py-3 font-semibold text-white hover:bg-sage-800" onClick={downloadReport}><Download size={17} />Download DOCX</button>{downloaded && <p role="status" className="mt-4 text-sm font-semibold text-sage-700">Your report download is ready.</p>}</section></div>
}
