import { useState } from 'react'
import { Office3D } from './Office3D'

type Agent = {
  name: string
  role: string
  avatar: string
  dept: 'Marketing' | 'Sales' | 'Engineering' | 'Orchestration'
}

type Props = {
  isOpen: boolean
  onClose: () => void
  agents: Agent[]
  coordination: Array<[Agent['dept'], Agent['dept']]>
}

const desks: Array<{ dept: Agent['dept']; x: number; y: number; label: string }> = [
  { dept: 'Marketing', x: 0, y: 0, label: 'Marketing' },
  { dept: 'Sales', x: 1, y: 0, label: 'Sales' },
  { dept: 'Engineering', x: 0, y: 1, label: 'Engineering' },
  { dept: 'Orchestration', x: 1, y: 1, label: 'Orchestration' },
]

export function OfficeView({ isOpen, onClose, agents, coordination }: Props) {
  const [mode, setMode] = useState<'2d' | '3d'>('2d')
  if (!isOpen) return null

  const coordinatingMap = new Map<string, Set<string>>()
  coordination.forEach(([a, b]) => {
    if (!coordinatingMap.has(a)) coordinatingMap.set(a, new Set())
    if (!coordinatingMap.has(b)) coordinatingMap.set(b, new Set())
    coordinatingMap.get(a)!.add(b)
    coordinatingMap.get(b)!.add(a)
  })

  const byDept = (dept: Agent['dept']) => agents.filter((a) => a.dept === dept)

  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="absolute inset-y-8 inset-x-10 bg-white/90 backdrop-blur rounded-3xl border border-neutral-200 shadow-xl overflow-hidden">
        <div className="flex h-full">
          {/* Floor */}
          <div className="flex-1 relative p-0">
            <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
              <div className="rounded-xl border border-neutral-300 bg-white shadow-sm overflow-hidden">
                <button onClick={() => setMode('2d')} className={`px-3 py-1.5 text-sm ${mode==='2d'?'bg-neutral-100':''}`}>2D</button>
                <button onClick={() => setMode('3d')} className={`px-3 py-1.5 text-sm ${mode==='3d'?'bg-neutral-100':''}`}>3D</button>
              </div>
              <button onClick={onClose} className="px-3 py-1.5 text-sm rounded-lg border border-neutral-300 bg-white hover:bg-neutral-50" aria-label="Close office view" title="Close">
                Close
              </button>
            </div>

            {mode === '3d' ? (
              <div className="absolute inset-0">
                <Office3D agents={agents} />
              </div>
            ) : (
              <div className="p-8 bg-[radial-gradient(circle_at_30%_20%,#f3f6fd,transparent_50%),radial-gradient(circle_at_80%_0,#fff7f8,transparent_40%)] h-full">
                <div className="grid grid-cols-2 grid-rows-2 gap-10 h-full">
                  {desks.map((desk) => {
                    const deptAgents = byDept(desk.dept)
                    const isCoordinating = coordinatingMap.get(desk.dept)?.size
                    return (
                      <div key={desk.dept} className="relative rounded-2xl bg-white border border-neutral-200 shadow-sm p-5 flex flex-col">
                        <div className="text-sm text-neutral-500 mb-3">{desk.label}</div>
                        <div className="relative flex-1 rounded-xl border border-neutral-100 bg-neutral-50/70">
                          <div className="absolute inset-3 rounded-lg bg-white grid place-items-center border border-neutral-200">
                            <div className="flex items-center gap-4">
                              {deptAgents.map((a, idx) => (
                                <div key={a.name} className={`relative w-16 h-16 rounded-full ring-1 ring-neutral-200 overflow-hidden shadow ${idx === 0 ? 'animate-float-slow' : 'animate-float-slower'}`}>
                                  <img src={a.avatar} alt={a.name} className="w-full h-full object-cover" />
                                  <span className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full bg-green-500 ring-2 ring-white" />
                                </div>
                              ))}
                              {deptAgents.length === 0 && (
                                <div className="text-xs text-neutral-400">No one at the desk</div>
                              )}
                            </div>
                          </div>
                        </div>
                        {!!isCoordinating && (
                          <div className="mt-3 text-[12px] text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg px-2 py-1 inline-flex items-center gap-2">Coordinating with {Array.from(coordinatingMap.get(desk.dept)!).join(', ')}</div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right panel */}
          <aside className="w-80 border-l border-neutral-200 bg-white p-5">
            <div className="font-semibold tracking-tight">Office</div>
            <div className="text-sm text-neutral-500">Click any desk to drill in (coming soon)</div>
            <div className="mt-5 space-y-4 text-sm">
              <div className="p-3 rounded-xl bg-neutral-50 border border-neutral-200">
                The office view is a live glance at which agents are working and who is coordinating with who.
              </div>
              <ul className="list-disc list-inside text-neutral-600 space-y-2">
                <li>Green dot indicates active</li>
                <li>Multiple avatars at one desk means coordination</li>
                <li>Switch between 2D and 3D view</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
} 