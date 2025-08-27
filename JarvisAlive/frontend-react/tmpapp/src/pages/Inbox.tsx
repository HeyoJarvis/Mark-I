import React from 'react'
import { Mail, MessageSquare, Instagram, Linkedin, Search as SearchIcon } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

const AGENTS = ['Marketing', 'Sales', 'Engineering', 'Orchestration'] as const
const CHANNELS = ['Email', 'Text', 'Instagram', 'LinkedIn'] as const
const STATUSES = ['Sent', 'Replied', 'Meeting scheduled'] as const

type Agent = typeof AGENTS[number]
type Channel = typeof CHANNELS[number]

type Outreach = {
  id: string
  company: string
  contact: string
  subject: string
  agent: Agent
  reason: string
  functionTag: string
  channel: Channel
  purpose: string
  status: 'Sent' | 'Replied' | 'Meeting scheduled'
  timestamp: string
}

const AGENT_META: Record<Agent, { name: string; avatar: string }> = {
  Marketing: { name: 'MJ', avatar: '/MJ copy.png' },
  Sales: { name: 'Alfred', avatar: '/Alfred copy.png' },
  Engineering: { name: 'Edith', avatar: '/Ed1th copy.png' },
  Orchestration: { name: 'Jarvis', avatar: '/Jarvis copy.png' },
}

function ChannelIcon({ channel }: { channel: Outreach['channel'] }) {
  const base = 'w-4 h-4 text-neutral-400'
  switch (channel) {
    case 'Email':
      return <span title="Email" aria-label="Email"><Mail className={base} aria-hidden="true" /></span>
    case 'Text':
      return <span title="Text" aria-label="Text"><MessageSquare className={base} aria-hidden="true" /></span>
    case 'Instagram':
      return <span title="Instagram" aria-label="Instagram"><Instagram className={base} aria-hidden="true" /></span>
    case 'LinkedIn':
      return <span title="LinkedIn" aria-label="LinkedIn"><Linkedin className={base} aria-hidden="true" /></span>
    default:
      return <Mail className={base} aria-hidden="true" />
  }
}

const SAMPLE_OUTREACH: Outreach[] = [
  { id: '1', company: 'RoasterCo', contact: 'hello@roaster.co', subject: 'Partner beans for launch', agent: 'Sales', functionTag: 'Lead Generation', reason: 'sourcing wholesale beans and pricing.', channel: 'Email', purpose: 'Requesting wholesale pricing and samples', status: 'Replied', timestamp: 'Today 9:12 AM' },
  { id: '2', company: 'Millwork Inc', contact: 'ops@millwork.com', subject: 'Bar buildout timeline', agent: 'Engineering', functionTag: 'System Architecture', reason: 'confirming lead times for bar and cabinetry.', channel: 'Email', purpose: 'Get timeline to coordinate grand opening', status: 'Sent', timestamp: 'Yesterday 4:05 PM' },
  { id: '3', company: 'LocalPaper', contact: 'ads@localpaper.com', subject: 'Grand opening promo slots', agent: 'Marketing', functionTag: 'Campaign Design', reason: 'lining up local promo for launch week.', channel: 'Email', purpose: 'Reserve ad inventory and request media kit', status: 'Meeting scheduled', timestamp: 'Mon 2:40 PM' },
  { id: '4', company: 'Neighborhood Assoc.', contact: '@neighassoc', subject: 'Community feature request', agent: 'Marketing', functionTag: 'Brand Strategy', reason: 'building neighborhood buzz.', channel: 'Instagram', purpose: 'Ask for a featured post about new shop', status: 'Sent', timestamp: 'Sun 7:18 PM' },
  { id: '5', company: 'BeanExpress', contact: '(212) 555-0199', subject: 'Delivery window confirmation', agent: 'Sales', functionTag: 'Deal Closing', reason: 'locking in supplier logistics.', channel: 'Text', purpose: 'Confirm first-week delivery timing', status: 'Replied', timestamp: 'Sun 4:11 PM' },
  { id: '6', company: 'CivicPermits', contact: 'licensing@city.gov', subject: 'Sidewalk sign permit', agent: 'Orchestration', functionTag: 'Team Coordination', reason: 'unblocking launch dependencies.', channel: 'Email', purpose: 'Clarify signage permit requirements', status: 'Sent', timestamp: 'Sat 9:02 AM' },
  { id: '7', company: 'CoffeeJobs NYC', contact: 'hiring@coffeejobs.nyc', subject: 'Hiring 2 baristas', agent: 'Orchestration', functionTag: 'Workflow Automation', reason: 'kickstarting hiring funnel.', channel: 'LinkedIn', purpose: 'Post JD and gather applicants', status: 'Sent', timestamp: 'Fri 5:36 PM' },
]

export default function InboxPage() {
  const { pathname } = useLocation()
  const [agentFilter, setAgentFilter] = React.useState<Agent | 'All'>('All')
  const [channelFilter, setChannelFilter] = React.useState<typeof CHANNELS[number]>('All')
  const [selectedStatuses, setSelectedStatuses] = React.useState<Set<string>>(new Set())
  const items = SAMPLE_OUTREACH
    .filter((o) => (agentFilter === 'All' ? true : o.agent === agentFilter))
    .filter((o) => (channelFilter === 'All' ? true : o.channel === channelFilter))

  return (
    <div className="absolute inset-0 pt-[56px] pb-[16px] overflow-y-auto">
      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Header with persistent tabs */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="text-xl font-semibold tracking-tight">Inbox</div>
          <div className="ml-auto inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1 shadow-sm">
            <Link to="/inbox" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/inbox') ? 'bg-neutral-900 text-white' : ''}`}>Inbox</Link>
            <Link to="/outcomes" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/outcomes') ? 'bg-neutral-900 text-white' : ''}`}>Outcomes</Link>
            <Link to="/suggestions" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/suggestions') ? 'bg-neutral-900 text-white' : ''}`}>Suggestions</Link>
          </div>
          <div className="w-full sm:w-auto">
            <div className="relative">
              <SearchIcon className="w-4 h-4 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                className="w-full sm:w-[360px] pl-9 pr-3 py-2.5 rounded-xl border border-neutral-200 outline-none bg-white placeholder:text-neutral-400"
                placeholder="Search company, subject, purpose"
              />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1">
            {["All", ...AGENTS].map((a) => (
              <button
                key={a}
                onClick={() => setAgentFilter(a as Agent | 'All')}
                className={`px-3 py-1.5 text-xs rounded-full transition ${agentFilter === a ? 'bg-neutral-900 text-white' : 'hover:bg-neutral-50'}`}
              >
                {a}
              </button>
            ))}
          </div>
          <div className="inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1">
            {["All", ...CHANNELS].map((c) => (
              <button
                key={c}
                onClick={() => setChannelFilter(c as Channel | 'All')}
                className={`px-3 py-1.5 text-xs rounded-full transition ${channelFilter === c ? 'bg-neutral-900 text-white' : 'hover:bg-neutral-50'}`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="rounded-2xl border border-neutral-200 bg-white overflow-hidden">
          {items.map((o) => {
            const meta = AGENT_META[o.agent]
            return (
              <div key={o.id} className="group grid grid-cols-[auto_auto_1fr_auto] items-start gap-3 px-4 py-3 border-b last:border-b-0 border-neutral-100 hover:bg-neutral-50">
                <img src={meta.avatar} alt={meta.name} className="w-8 h-8 rounded-full border border-neutral-200 object-cover" />
                <div className="mt-1.5"><ChannelIcon channel={o.channel} /></div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="font-medium truncate">{o.company}</div>
                    <span className="text-xs text-neutral-500 truncate">{o.contact}</span>
                  </div>
                  <div className="text-sm text-neutral-800 truncate">{o.subject}</div>
                  <div className="text-xs text-neutral-500 truncate">From {meta.name} — {o.functionTag}: {o.reason}</div>
                  <div className="text-xs text-neutral-400 mt-0.5">{o.timestamp}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className="inline-flex items-center gap-1">
                    <span className="text-[11px] px-2 py-0.5 rounded-full border border-neutral-200 bg-white text-neutral-600 whitespace-nowrap">{o.agent}</span>
                    <span className="text-[11px] px-2 py-0.5 rounded-full border border-neutral-200 bg-white text-neutral-600 whitespace-nowrap">{o.functionTag}</span>
                  </div>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full whitespace-nowrap ${o.status === 'Replied' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : o.status === 'Meeting scheduled' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100' : 'bg-neutral-100 text-neutral-700 border border-neutral-200'}`}>{o.status}</span>
                </div>
              </div>
            )
          })}
          {items.length === 0 && (
            <div className="p-8 text-center text-neutral-500 text-sm">No outreach yet for this filter.</div>
          )}
        </div>
      </div>
    </div>
  )
} 