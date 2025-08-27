import React from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { SendHorizonal, Plus, SlidersHorizontal, Search, ChevronDown } from 'lucide-react'
import WorkflowForm from '../components/WorkflowForm'

type DashboardData = {
	businessName: string;
	track: string;
	completedAt: string;
	totalFields: number;
	paymentTotal: number;
}

const AGENTS: Record<string, { name: string; role: string; avatar: string; greeting: string; accent: string }> = {
	mj: { name: 'MJ', role: 'Marketing', avatar: '/MJ copy.png', greeting: 'Hey! Want help with branding or launch campaigns?', accent: 'bg-rose-100 text-rose-700' },
	alfred: { name: 'Alfred', role: 'Sales', avatar: '/Alfred copy.png', greeting: 'Ready to source suppliers or close deals?', accent: 'bg-amber-100 text-amber-700' },
	edith: { name: 'Edith', role: 'Engineering', avatar: '/Ed1th copy.png', greeting: 'Hi! I can spin up sites, automate flows, and ship.', accent: 'bg-indigo-100 text-indigo-700' },
	jarvis: { name: 'Jarvis', role: 'Orchestration', avatar: '/Jarvis copy.png', greeting: 'I’ll coordinate the crew. What should we tackle first?', accent: 'bg-sky-100 text-sky-700' },
	lincoln: { name: 'Lincoln', role: 'Legal', avatar: '/lincolnn.png', greeting: 'I’ve drafted the legal setup plan. Want me to walk you through it?', accent: 'bg-emerald-100 text-emerald-700' },
	wolf: { name: 'Wolf', role: 'Strategy', avatar: '/wolf.png', greeting: 'I can help with market analysis, business plans, funding, and growth.', accent: 'bg-purple-100 text-purple-700' },
}

const EXACT_TRIGGER = 'HeyJarvis I want to create a Coffee Shop'

export default function AgentChatPage() {
	const { agentId = '' } = useParams()
	const navigate = useNavigate()
	const meta = AGENTS[agentId.toLowerCase()]
	const [input, setInput] = React.useState('')
	const [messages, setMessages] = React.useState<{ from: 'agent' | 'user'; text: string; dashboardData?: DashboardData }[]>([])
	const scrollerRef = React.useRef<HTMLDivElement>(null)
	const storageKey = React.useMemo(() => `vf:chat:${agentId.toLowerCase()}`, [agentId])
	const [showWorkflowForm, setShowWorkflowForm] = React.useState(false)
	const [showDashboard, setShowDashboard] = React.useState(false)
	const [showComplianceBubble, setShowComplianceBubble] = React.useState(false)

	// Lincoln guided stepper state
	type StepKey = 'entity'|'permits'|'compliance'|'insurance'|'filings'
	type Status = 'pending'|'running'|'done'|'blocked'
	type Item = { id: string; title: string; status: Status; kind: 'auto'|'upload'|'choice'; options?: string[]; hint?: string }
	type Step = { key: StepKey; title: string; cta: string; status: Status; items: Item[] }
	// const ORDER: StepKey[] = ['entity','permits','compliance','insurance','filings']
	const defaultSteps: Step[] = [
		{ key:'entity', title:'Legal entity', cta:'Start filings', status:'pending', items:[
			{ id:'entity-type', title:'Choose entity type', status:'pending', kind:'choice', options:['LLC','S‑Corp','C‑Corp','Not sure'], hint:'Most SMBs pick LLC for flexibility and pass-through taxes.' },
			{ id:'name', title:'Check & Reserve Business Name', status:'pending', kind:'auto', hint:'Search state registry; reserve if available.' },
			{ id:'formation', title:'File Formation Documents', status:'pending', kind:'auto', hint:'Articles of Organization/Incorporation with the state.' },
			{ id:'ein', title:'Obtain Federal EIN', status:'pending', kind:'auto', hint:'IRS tax ID for banking and employees.' },
			{ id:'operating', title:'Generate Operating Agreement', status:'pending', kind:'auto', hint:'Governing rules; often required by banks/landlords.' },
		]},
		{ key:'permits', title:'Licenses & permits', cta:'Check local permits', status:'pending', items:[
			{ id:'business-license', title:'Local business license', status:'pending', kind:'auto' },
			{ id:'resale', title:'Resale certificate / seller’s permit', status:'pending', kind:'auto' },
			{ id:'zoning', title:'Zoning / occupancy clearance', status:'pending', kind:'auto' },
			{ id:'warehouse', title:'Warehouse permit (if required)', status:'pending', kind:'auto' },
			{ id:'importer', title:'Importer of Record / Customs bond', status:'pending', kind:'auto' },
		]},
		{ key:'compliance', title:'Compliance & documentation', cta:'Generate plan', status:'pending', items:[
			{ id:'cpsia', title:'CPSIA applicability check', status:'pending', kind:'auto' },
			{ id:'astm', title:'ASTM D4236 labeling (if art materials)', status:'pending', kind:'auto' },
			{ id:'prop65', title:'California Proposition 65 labeling plan', status:'pending', kind:'auto' },
			{ id:'warnings', title:'Product safety & choking hazard warnings', status:'pending', kind:'auto' },
			{ id:'sds', title:'Collect SDS & lab test results', status:'pending', kind:'upload' },
			{ id:'package', title:'Compile compliance documentation', status:'pending', kind:'auto' },
		]},
		{ key:'insurance', title:'Insurance recommendations', cta:'Get quotes', status:'pending', items:[
			{ id:'gl', title:'General & Product Liability (1M/2M)', status:'pending', kind:'auto' },
			{ id:'property', title:'Property / warehouse coverage', status:'pending', kind:'auto' },
			{ id:'workers', title:'Workers’ comp (as needed)', status:'pending', kind:'auto' },
			{ id:'cyber', title:'Cyber liability', status:'pending', kind:'auto' },
		]},
		{ key:'filings', title:'Regulatory filings', cta:'Prepare filing packet', status:'pending', items:[
			{ id:'ein', title:'Upload IRS CP 575 EIN letter', status:'pending', kind:'upload' },
			{ id:'state-receipt', title:'State registration receipt', status:'pending', kind:'upload' },
			{ id:'resale-onfile', title:'Resale certificate on file', status:'pending', kind:'upload' },
			{ id:'fda', title:'FDA importer facility registration (if needed)', status:'pending', kind:'auto' },
			{ id:'bond', title:'Customs bond confirmation (if importing)', status:'pending', kind:'auto' },
		]},
	]
	const legalKey = React.useMemo(()=>`vf:legal:${agentId.toLowerCase()}`,[agentId])
	const [steps, setSteps] = React.useState<Step[]>(defaultSteps)
	const [active, setActive] = React.useState<StepKey>('entity')
	const [log, setLog] = React.useState<{ id:string; text:string; ts:number }[]>([])

	// Load legal workflow when Lincoln is open
	React.useEffect(() => {
		if (agentId.toLowerCase() !== 'lincoln') return
		try {
			const raw = localStorage.getItem(legalKey)
			if (raw) {
				const parsed = JSON.parse(raw) as { steps: Step[]; active: StepKey; log:{id:string;text:string;ts:number}[] }
				if (parsed?.steps) setSteps(parsed.steps)
				if (parsed?.active) setActive(parsed.active)
				if (parsed?.log) setLog(parsed.log)
			} else {
				setSteps(defaultSteps)
				setActive('entity')
			}
		} catch { /* no-op */ }
	}, [agentId, legalKey])

	// Persist legal workflow
	React.useEffect(() => {
		if (agentId.toLowerCase() !== 'lincoln') return
		try { localStorage.setItem(legalKey, JSON.stringify({ steps, active, log })) } catch { /* no-op */ }
	}, [steps, active, log, legalKey, agentId])

	// Legacy stepper helpers retained for future use; not needed when using the new inline workflows

	// Load persisted chat on mount or agent change
	React.useEffect(() => {
		if (!meta) return
		try {
			const raw = localStorage.getItem(storageKey)
			if (raw) {
				const parsed = JSON.parse(raw) as Array<{ from: 'agent' | 'user'; text: string }>
				if (Array.isArray(parsed)) {
					setMessages(parsed)
				} else {
					setMessages([{ from: 'agent', text: meta.greeting }])
				}
			} else {
				setMessages([{ from: 'agent', text: meta.greeting }])
			}
		} catch {
			setMessages([{ from: 'agent', text: meta.greeting }])
		}
		// Do not clear jarvis-demo flag here; it drives dashboard persistence
	}, [agentId, meta, storageKey])

	// Persist on change
	React.useEffect(() => {
		try { localStorage.setItem(storageKey, JSON.stringify(messages)) } catch { /* no-op */ }
	}, [messages, storageKey])

	// Auto-scroll
	React.useEffect(() => {
		if (scrollerRef.current) scrollerRef.current.scrollTo({ top: scrollerRef.current.scrollHeight })
	}, [messages])

	if (!meta) {
		return (
			<div className="absolute inset-0 grid place-items-center">
				<div className="text-center space-y-2">
					<div className="text-lg font-semibold">Unknown agent</div>
					<Link to="/" className="text-sm text-indigo-600 underline">Go back</Link>
				</div>
			</div>
		)
	}

	function send() {
		const v = input.trim()
		if (!v) return
		// Special: Jarvis demo trigger (keeps demo in main flow)
		if (agentId.toLowerCase() === 'jarvis') {
			if (v === EXACT_TRIGGER) {
				sessionStorage.setItem('jarvis-demo', '1')
			}
			setInput('')
			navigate('/')
			return
		}
		const next: { from: 'agent' | 'user'; text: string }[] = [...messages, { from: 'user' as const, text: v }]
		setMessages(next)
		setInput('')
		setTimeout(() => {
			setMessages((m) => [...m, { from: 'agent', text: `Got it. I’ll take “${v}” and get moving.` }])
		}, 500)
	}

	const handleDashboardComplete = () => {
		// Show the compliance bubble instead of adding a chat message
		setShowComplianceBubble(true)
	}





	return (
		<div className="absolute inset-0 flex flex-col bg-white">
			{/* Header */}
			<header className="shrink-0 border-b border-neutral-200 px-6 py-5 bg-white/90 backdrop-blur">
				<div className="flex items-center gap-4">
					<div className="inline-flex items-center gap-3">
						<img src={meta.avatar} alt={meta.name} className="w-12 h-12 rounded-full object-cover" />
						<div>
							<div className="font-semibold text-base leading-tight">{meta.name}</div>
							<div className="text-[11px] text-neutral-500 -mt-0.5">{meta.role} • Online</div>
						</div>
					</div>

					{/* Slim tabs (shadcn expandable-tabs stand-in) */}
					<div className="ml-auto inline-flex items-center gap-1 rounded-full border border-neutral-200 bg-white/80 backdrop-blur px-1 py-1 shadow-sm">
						<button onClick={() => navigate('/inbox')} className="px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50">Inbox</button>
						<button onClick={() => navigate('/outcomes')} className="px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50">Outcomes</button>
						<button onClick={() => navigate('/suggestions')} className="px-3 py-1.5 text-xs rounded-full hover:bg-neutral-50">Suggestions</button>
					</div>

					{agentId.toLowerCase()==='lincoln' && (
						<button className="text-xs px-3 py-1.5 ml-2 rounded-lg border border-neutral-200 hover:bg-neutral-50" onClick={()=>setShowWorkflowForm(true)}>Open workflows</button>
					)}

				</div>
			</header>

			{/* Messages */}
			<div ref={scrollerRef} className="flex-1 overflow-y-auto">
				<div className="px-6 py-6 space-y-3">
					{messages.map((m, i) => (
						<div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
							<div className={`${m.from === 'user' ? 'bg-indigo-600 text-white' : 'bg-neutral-100 text-neutral-800'} px-3 py-2 rounded-2xl max-w-[75%]`}>
								{m.text}
								{m.dashboardData && (
										<div className="mt-3 pt-3 border-t border-neutral-300">
											<div className="rounded-xl border border-neutral-200 bg-white p-3 flex items-center justify-between gap-3">
												<div className="text-sm text-neutral-700">Welcome. I see you want to create a Coffee Shop.</div>
												<button 
													className="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
													onClick={() => setShowDashboard(true)}
												>
													Open business setup dashboard
												</button>
											</div>
										</div>
									)}
							</div>
						</div>
					))}

					{/* Lincoln workflows inline suggestion instead of large CTA */}
					{agentId.toLowerCase() === 'lincoln' && sessionStorage.getItem('jarvis-demo') === '1' && !showComplianceBubble && (
						<div className="mt-6">
							<div className="rounded-xl border border-neutral-200 bg-white p-4 flex items-center justify-between gap-3">
								<div className="text-sm text-neutral-700">Welcome. I see you want to create a Coffee Shop.</div>
								<button 
									className="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
									onClick={() => setShowWorkflowForm(true)}
								>
									Open business setup dashboard
								</button>
							</div>
						</div>
					)}
				</div>
			</div>

			{/* Bottom input - Redesigned to match reference */}
			<footer className="shrink-0 border-t border-neutral-200 bg-white/95 backdrop-blur px-6 py-6">
				<div className="">
					<div className="rounded-3xl border border-neutral-200 bg-white shadow-sm">
						{/* Top textarea row */}
						<div className="px-5 pt-5 pb-2">
							<textarea
								className="w-full min-h-[120px] py-3 outline-none text-[17px] placeholder:text-neutral-400 resize-none"
								placeholder={agentId.toLowerCase()==='jarvis' ? EXACT_TRIGGER : `How can I help you today?`}
								value={input}
								onChange={(e) => setInput(e.target.value)}
								onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
							/>
						</div>
						{/* Controls row */}
						<div className="flex items-center justify-between px-4 pb-4 pt-3">
							<div className="flex items-center gap-2">
								<button className="w-10 h-10 grid place-items-center rounded-xl border border-neutral-200 hover:bg-neutral-50" aria-label="Add">
									<Plus className="w-4 h-4 text-neutral-700" />
								</button>
								<button className="w-10 h-10 grid place-items-center rounded-xl border border-neutral-200 hover:bg-neutral-50" aria-label="Settings">
									<SlidersHorizontal className="w-4 h-4 text-neutral-700" />
								</button>
								<button className="h-10 px-3 rounded-xl border border-neutral-200 hover:bg-neutral-50 inline-flex items-center gap-2" aria-label="Research">
									<Search className="w-4 h-4 text-neutral-700" />
									<span className="text-sm text-neutral-800">Research</span>
								</button>
							</div>
							<div className="flex items-center gap-2">
								<button className="h-10 px-3 rounded-xl border border-neutral-200 hover:bg-neutral-50 inline-flex items-center gap-1" aria-label="Model selector">
									<span className="text-sm text-neutral-800 hidden sm:inline">Claude Opus 4</span>
									<ChevronDown className="w-4 h-4 text-neutral-500" />
								</button>
								<button className="w-11 h-11 grid place-items-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700" onClick={send} aria-label="Send message">
									<SendHorizonal className="w-5 h-5" />
								</button>
							</div>
						</div>
					</div>
				</div>
			</footer>
			<WorkflowForm 
				isOpen={showWorkflowForm} 
				onClose={() => setShowWorkflowForm(false)} 
				onDashboardComplete={handleDashboardComplete}
			/>
			{showDashboard && (
				<WorkflowForm 
					isOpen={showDashboard} 
					onClose={() => setShowDashboard(false)}
					onDashboardComplete={handleDashboardComplete}
				/>
			)}
			
			{/* Compliance Dashboard Bubble */}
			{showComplianceBubble && (
				<div className="fixed top-30 right-4 z-50">
					<button
						onClick={() => setShowDashboard(true)}
						className="flex items-center space-x-3 bg-blue-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
					>
						<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<span className="font-medium">Compliance Dashboard</span>
					</button>
				</div>
			)}

		</div>
	)
} 