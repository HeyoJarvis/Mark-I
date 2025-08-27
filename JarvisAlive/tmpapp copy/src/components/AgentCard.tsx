import React from 'react'

type Props = {
	name: string
	role: string
	avatar: string
	status?: 'Online' | 'Idle' | 'Busy'
	onClick?: () => void
}

export default function AgentCard({ name, role, avatar, status = 'Online', onClick }: Props) {
	const [imageOk, setImageOk] = React.useState(true)
	return (
		<button
			className="group w-full text-left rounded-2xl border border-neutral-200 bg-white shadow-sm hover:shadow-md hover:-translate-y-[1px] transition px-4 py-3 focus:outline-none focus:ring-2 ring-[--vf-accent]"
			onClick={onClick}
			aria-label={`Open ${name} agent`}
		>
			<div className="flex items-center gap-3">
				{imageOk ? (
					<img src={encodeURI(avatar)} alt={name} onError={() => setImageOk(false)} className="w-10 h-10 rounded-full object-cover" />
				) : (
					<div className="w-10 h-10 rounded-full grid place-items-center bg-neutral-100 text-neutral-600">
						{(name || '?').slice(0,1)}
					</div>
				)}
				<div className="flex-1 min-w-0">
					<div className="font-medium leading-tight truncate">{name}</div>
					<div className="text-sm text-neutral-500 truncate">{role}</div>
				</div>
				<span className="relative inline-flex items-center">
					<span className={`h-2.5 w-2.5 rounded-full ${status === 'Online' ? 'bg-green-500' : status === 'Busy' ? 'bg-amber-500' : 'bg-neutral-400'} ring-2 ring-white`} />
					<span role="tooltip" className="invisible group-hover:visible absolute -left-2 top-4 text-xs px-2 py-1 rounded bg-black/80 text-white">{status}</span>
				</span>
			</div>
		</button>
	)
} 