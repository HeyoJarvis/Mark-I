import { Lightbulb } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

const SUGGESTIONS = [
  {
    id: '1',
    title: 'Run a 3‑question sidewalk survey',
    rationale: 'Foot traffic is up 18%; validate demand for iced drinks vs hot during afternoons.',
    action: 'Generate 50 QR flyers and a Typeform link',
  },
  {
    id: '2',
    title: 'Email 5 local roasters for wholesale pricing',
    rationale: 'We identified 5 suitable roasters; request sample packs and wholesale terms.',
    action: 'Draft outreach emails via Sales agent',
  },
  {
    id: '3',
    title: 'Test two hero headlines on the website',
    rationale: 'Early site visitors can A/B test “Small-batch coffee, fresh-baked joy.” vs a price-led variant.',
    action: 'Spin up A/B test and track conversions',
  },
] as const

export default function SuggestionsPage() {
  const { pathname } = useLocation()
  return (
    <div className="absolute inset-0 pt-[56px] pb-[16px] overflow-y-auto">
      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Header with persistent tabs */}
        <div className="flex items-center gap-3">
          <div className="text-xl font-semibold tracking-tight flex items-center gap-2"><Lightbulb className="w-5 h-5" /> Suggestions</div>
          <div className="ml-auto inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1 shadow-sm">
            <Link to="/inbox" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/inbox') ? 'bg-neutral-900 text-white' : ''}`}>Inbox</Link>
            <Link to="/outcomes" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/outcomes') ? 'bg-neutral-900 text-white' : ''}`}>Outcomes</Link>
            <Link to="/suggestions" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/suggestions') ? 'bg-neutral-900 text-white' : ''}`}>Suggestions</Link>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {SUGGESTIONS.map((s) => (
            <div key={s.id} className="rounded-2xl border border-neutral-200 bg-white p-5 flex flex-col gap-3">
              <div className="font-medium leading-snug">{s.title}</div>
              <div className="text-sm text-neutral-700">{s.rationale}</div>
              <button className="self-start text-sm px-3 py-1.5 rounded-lg border border-neutral-200 hover:bg-neutral-50">{s.action}</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
} 