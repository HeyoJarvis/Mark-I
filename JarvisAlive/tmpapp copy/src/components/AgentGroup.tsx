import React from 'react'

type Props = {
	title: string
	count: number
	children: React.ReactNode
}

export default function AgentGroup({ title, count, children }: Props) {
	const key = React.useMemo(() => `agent-group:${title}`, [title])
	const [open, setOpen] = React.useState<boolean>(true)

	React.useEffect(() => {
		const saved = localStorage.getItem(key)
		if (saved != null) setOpen(saved === '1')
	}, [key])

	function onToggle(e: React.SyntheticEvent<HTMLDetailsElement, Event>) {
		const next = (e.currentTarget as HTMLDetailsElement).open
		setOpen(next)
		localStorage.setItem(key, next ? '1' : '0')
	}

	return (
		<details open={open} onToggle={onToggle} className="group rounded-2xl border border-neutral-200 bg-white overflow-hidden">
			<summary className="list-none cursor-pointer sticky top-0 z-[1] px-4 py-3 bg-white/70 backdrop-blur flex items-center justify-between">
				<span className="text-sm font-medium">{title}</span>
				<span className="text-xs text-neutral-500">{count}</span>
			</summary>
			<div className="p-3 space-y-3">
				{children}
			</div>
		</details>
	)
} 