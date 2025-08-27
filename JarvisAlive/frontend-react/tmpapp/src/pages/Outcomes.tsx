import React, { useMemo, useState } from 'react'
import { Search as SearchIcon } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

export default function OutcomesPage() {
  const AGENTS = ['Marketing', 'Sales', 'Engineering', 'Orchestration'] as const
  type Agent = typeof AGENTS[number]
  type Status = 'Done' | 'In progress' | 'Pending' | 'Blocked'

  type Task = {
    id: string
    agent: Agent
    title: string
    description: string
    status: Status
    date: string
    // Visual preview fields
    progressPct?: number
    colors?: string[]
    checklist?: { done: number; total: number }
    skeletonLines?: number
  }

  // Avatars to mirror Inbox style
  const AGENT_META: Record<Agent, { name: string; avatar: string }> = {
    Marketing: { name: 'MJ', avatar: '/MJ copy.png' },
    Sales: { name: 'Alfred', avatar: '/Alfred copy.png' },
    Engineering: { name: 'Edith', avatar: '/Ed1th copy.png' },
    Orchestration: { name: 'Jarvis', avatar: '/Jarvis copy.png' },
  }

  const TASKS: Task[] = [
    { id: 't1', agent: 'Marketing', title: 'Brand kit v1', description: 'Logo, palette, typography for Copper & Crumb.', status: 'Done', date: 'Today', colors: ['#1F2937', '#6B7280', '#F59E0B', '#FFFFFF'] },
    { id: 't2', agent: 'Engineering', title: 'Website demo', description: 'Landing page draft with CTA and menu stub.', status: 'Done', date: 'Today', skeletonLines: 3, progressPct: 100 },
    { id: 't3', agent: 'Sales', title: 'Shortlist 5 roasters', description: 'Quality/price matrix and initial outreach.', status: 'In progress', date: 'Yesterday', checklist: { done: 3, total: 5 } },
    { id: 't4', agent: 'Marketing', title: 'Menu v1 copy', description: 'Draft hero, subcopy and CTA variants.', status: 'In progress', date: 'Today', progressPct: 45 },
    { id: 't5', agent: 'Engineering', title: 'Custom domain setup', description: 'Point Copper&Crumb.co to the demo site.', status: 'Pending', date: 'Today', skeletonLines: 2 },
    { id: 't6', agent: 'Orchestration', title: 'Grand opening runbook', description: 'Cross-team timeline and owners.', status: 'Pending', date: 'Today', checklist: { done: 1, total: 6 } },
    { id: 't7', agent: 'Sales', title: 'Sample tasting', description: 'Schedule roaster sampling session.', status: 'Blocked', date: 'This week' },
  ]

  const done = TASKS.filter(t => t.status === 'Done').length
  const inProgress = TASKS.filter(t => t.status === 'In progress').length
  const pending = TASKS.filter(t => t.status === 'Pending').length
  const blocked = TASKS.filter(t => t.status === 'Blocked').length

  const METRICS: { label: string; value: number }[] = [
    { label: 'Completed', value: done },
    { label: 'In progress', value: inProgress },
    { label: 'Pending', value: pending },
    { label: 'Blocked', value: blocked },
  ]

  const byAgent = AGENTS.map(a => {
    const total = TASKS.filter(t => t.agent === a).length
    const completed = TASKS.filter(t => t.agent === a && t.status === 'Done').length
    const pct = total ? Math.round((completed / total) * 100) : 0
    return { agent: a, total, completed, pct }
  })

  const STATUSES: Status[] = ['Done', 'In progress', 'Pending', 'Blocked']

  const [query, setQuery] = useState('')
  const [agentFilter, setAgentFilter] = useState<Set<Agent>>(new Set())
  const [statusFilter, setStatusFilter] = useState<Set<Status>>(new Set())

  function toggle<T>(set: React.Dispatch<React.SetStateAction<Set<T>>>, v: T) {
    set((prev) => {
      const next = new Set(prev)
      next.has(v) ? next.delete(v) : next.add(v)
      return next
    })
  }

  const filtered = useMemo(() => {
    return TASKS
      .filter(t => agentFilter.size ? agentFilter.has(t.agent) : true)
      .filter(t => statusFilter.size ? statusFilter.has(t.status) : true)
      .filter(t => {
        if (!query.trim()) return true
        const q = query.toLowerCase()
        return (
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q) ||
          t.agent.toLowerCase().includes(q)
        )
      })
  }, [agentFilter, statusFilter, query])

  const { pathname } = useLocation()

  return (
    <div className="absolute inset-0 pt-[56px] pb-[16px] overflow-y-auto">
      <div className="max-w-7xl mx-auto px-8 py-6 space-y-6">
        {/* Elegant Header & persistent tabs */}
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <div className="text-xl font-semibold tracking-tight">Outcomes</div>
            <div className="text-xs text-neutral-500">Progress across teams and workstreams</div>
          </div>
          <div className="ml-auto inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1 shadow-sm">
            <Link to="/inbox" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/inbox') ? 'bg-neutral-900 text-white' : ''}`}>Inbox</Link>
            <Link to="/outcomes" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/outcomes') ? 'bg-neutral-900 text-white' : ''}`}>Outcomes</Link>
            <Link to="/suggestions" className={`px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50 ${pathname.startsWith('/suggestions') ? 'bg-neutral-900 text-white' : ''}`}>Suggestions</Link>
          </div>
          <div className="w-full sm:w-auto">
            <div className="relative">
              <SearchIcon className="w-4 h-4 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                className="w-full sm:w-[320px] pl-9 pr-3 py-2.5 rounded-xl border border-neutral-200 outline-none bg-white placeholder:text-neutral-400"
                placeholder="Search outcomes"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Metric cards */}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {METRICS.map((m) => (
            <div key={m.label} className="rounded-2xl border border-neutral-200 bg-white p-5">
              <div className="text-xs text-neutral-500">{m.label}</div>
              <div className="text-3xl font-semibold tracking-tight">{m.value}</div>
            </div>
          ))}
        </div>

        {/* Agent progress */}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {byAgent.map(a => (
            <div key={a.agent} className="rounded-2xl border border-neutral-200 bg-white p-5">
              <div className="text-sm font-medium mb-2">{a.agent}</div>
              <div className="h-2 rounded bg-neutral-100 overflow-hidden">
                <div className="h-full bg-indigo-600" style={{ width: `${a.pct}%` }} />
              </div>
              <div className="text-xs text-neutral-500 mt-2">{a.completed} of {a.total} complete • {a.pct}%</div>
            </div>
          ))}
        </div>

        {/* Sticky Filters - chips */}
        <div className="sticky top-[56px] z-10 bg-white/85 backdrop-blur rounded-2xl border border-neutral-200 p-3">
          <div className="grid sm:grid-cols-2 gap-2">
            <div className="inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1">
              <button className="px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50" onClick={() => setAgentFilter(new Set())}>All teams</button>
              {AGENTS.map(a => (
                <button key={a} onClick={() => toggle(setAgentFilter, a)} className={`px-3 py-1.5 text-xs rounded-full ${agentFilter.has(a) ? 'bg-neutral-900 text-white' : 'hover:bg-neutral-50'}`}>{a}</button>
              ))}
            </div>
            <div className="inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white px-1 py-1">
              <button className="px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50" onClick={() => setStatusFilter(new Set())}>All status</button>
              {STATUSES.map(s => (
                <button key={s} onClick={() => toggle(setStatusFilter, s)} className={`px-3 py-1.5 text-xs rounded-full ${statusFilter.has(s) ? 'bg-neutral-900 text-white' : 'hover:bg-neutral-50'}`}>{s}</button>
              ))}
            </div>
          </div>
        </div>

        {/* List with visual previews and avatars */}
        <div className="rounded-2xl border border-neutral-200 bg-white overflow-hidden">
          {filtered.map(t => (
            <div
              key={t.id}
              className={`grid grid-cols-[8px_auto_1fr_auto] items-start gap-4 px-5 py-4 border-b last:border-b-0 border-neutral-100 hover:bg-neutral-50`}
            >
              <div className={`${t.status === 'Done' ? 'bg-emerald-500' : t.status === 'In progress' ? 'bg-indigo-500' : t.status === 'Pending' ? 'bg-amber-500' : 'bg-rose-500'} rounded-full`} />
              <img src={AGENT_META[t.agent].avatar} alt={AGENT_META[t.agent].name} className="w-8 h-8 rounded-full border border-neutral-200 object-cover" />
              <div className="min-w-0">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="font-medium truncate">{t.title}</div>
                  <span className="text-xs text-neutral-500 truncate">{t.agent}</span>
                </div>
                <div className="text-sm text-neutral-700 truncate">{t.description}</div>
                {/* Visual preview row */}
                <div className="mt-2 flex items-center gap-3">
                  {/* Colors preview */}
                  {t.colors && (
                    <div className="flex items-center gap-1">
                      {t.colors.slice(0,4).map((c) => (
                        <span key={c} className="w-4 h-4 rounded-full ring-1 ring-neutral-200" style={{ backgroundColor: c }} />
                      ))}
                    </div>
                  )}
                  {/* Progress preview */}
                  {typeof t.progressPct === 'number' && (
                    <div className="flex items-center gap-2 min-w-[160px]">
                      <div className="h-1.5 w-28 bg-neutral-100 rounded overflow-hidden">
                        <div className="h-full bg-indigo-600" style={{ width: `${t.progressPct}%` }} />
                      </div>
                      <span className="text-xs text-neutral-500">{t.progressPct}%</span>
                    </div>
                  )}
                  {/* Checklist preview */}
                  {t.checklist && (
                    <div className="text-xs text-neutral-600">
                      {t.checklist.done}/{t.checklist.total} items
                    </div>
                  )}
                  {/* Website skeleton preview */}
                  {t.skeletonLines && (
                    <div className="hidden sm:flex flex-col gap-1.5 w-40">
                      {[...Array(t.skeletonLines)].map((_,i) => (
                        <div key={i} className="h-2 rounded bg-neutral-100" />
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-xs text-neutral-400 mt-1">{t.date}</div>
              </div>
              <div className="self-start">
                <span className={`text-[11px] px-2 py-0.5 rounded-full whitespace-nowrap border ${t.status === 'Done' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : t.status === 'In progress' ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : t.status === 'Pending' ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-rose-50 border-rose-200 text-rose-700'}`}>{t.status}</span>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="p-8 text-center text-neutral-500 text-sm">No tasks match the current filters.</div>
          )}
        </div>
      </div>
    </div>
  )
} 