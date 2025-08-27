import { TeamMemberCard } from './TeamMemberCard'
import { useNavigate, useLocation } from 'react-router-dom'

export function Sidebar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const currentAgent = pathname.startsWith('/chat/') ? pathname.split('/')[2] : ''
  const hasLegalFlag = typeof window !== 'undefined' && sessionStorage.getItem('jarvis-demo') === '1'
  return (
    <aside className="h-full bg-white/90 backdrop-blur border-r border-neutral-200 flex flex-col">
      <div className="p-4 border-b border-neutral-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-indigo-600 text-white grid place-items-center text-xs font-bold shadow-sm">J</div>
          <div className="flex-1">
            <div className="font-semibold tracking-tight text-sm">Your AI Team</div>
            <div className="text-[11px] text-neutral-500">7 active</div>
          </div>
          <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_0_2px_#EAFBE7]" aria-label="Online" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2.5 p-3 pt-6">
        <button className={`w-full text-left rounded-2xl ${currentAgent==='jarvis' ? 'ring-2 ring-indigo-500/50' : ''}`} onClick={() => navigate('/')} aria-label="Open Jarvis">
          <TeamMemberCard name="Jarvis" role="Orchestration" skills={["Workflow Automation", "Team Coordination"]} avatar="/Jarvis copy.png" />
        </button>
        <button className={`w-full text-left rounded-2xl ${currentAgent==='mj' ? 'ring-2 ring-indigo-500/50' : ''}`} onClick={() => navigate('/chat/mj')} aria-label="Open MJ chat">
        <TeamMemberCard name="MJ" role="Marketing" skills={["Brand Strategy", "Campaign Design"]} avatar="/MJ copy.png" />
        </button>
        <button className={`w-full text-left rounded-2xl ${currentAgent==='alfred' ? 'ring-2 ring-indigo-500/50' : ''}`} onClick={() => navigate('/chat/alfred')} aria-label="Open Alfred chat">
        <TeamMemberCard name="Alfred" role="Sales" skills={["Lead Generation", "Deal Closing"]} avatar="/Alfred copy.png" />
        </button>
        <button className={`w-full text-left rounded-2xl ${currentAgent==='edith' ? 'ring-2 ring-indigo-500/50' : ''}`} onClick={() => navigate('/chat/edith')} aria-label="Open Edith chat">
        <TeamMemberCard name="Edith" role="Engineering" skills={["System Architecture", "Code Review"]} avatar="/Ed1th copy.png" />
        </button>
        <div className={`relative ${currentAgent==='lincoln' ? 'ring-2 ring-indigo-500/50 rounded-2xl' : ''}`}>
          {hasLegalFlag && (
            <span className="absolute -top-2 -right-2 z-10 text-[11px] px-2 py-0.5 rounded-full bg-indigo-600 text-white shadow">New</span>
          )}
          			<button className="w-full text-left" onClick={() => navigate('/chat/lincoln')} aria-label="Open Lincoln chat">
				<TeamMemberCard name="Lincoln" role="Legal" skills={["Compliance", "Contracts"]} avatar="/lincolnn.png" />
			</button>
		</div>

		{/* Wolf Agent below Legal */}
		<button className={`w-full text-left rounded-2xl ${currentAgent==='wolf' ? 'ring-2 ring-indigo-500/50' : ''}`} onClick={() => navigate('/chat/wolf')} aria-label="Open Wolf chat">
			<TeamMemberCard name="Wolf" role="Strategy" skills={["Market Analysis", "Growth"]} avatar="/wolf.png" />
		</button>
	</div>

    </aside>
  )
} 