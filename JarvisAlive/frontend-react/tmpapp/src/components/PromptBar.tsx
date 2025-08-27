import React from 'react'

export default function PromptBar({ onSubmit }: { onSubmit: (v: string) => Promise<void> | void }) {
	const [value, setValue] = React.useState('')
	const [loading, setLoading] = React.useState(false)
	const textareaRef = React.useRef<HTMLTextAreaElement>(null)

	React.useEffect(() => {
		function onKey(e: KeyboardEvent) {
			if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
				e.preventDefault()
				textareaRef.current?.focus()
			}
		}
		window.addEventListener('keydown', onKey)
		return () => window.removeEventListener('keydown', onKey)
	}, [])

	async function submit() {
		const v = value.trim()
		if (!v) return
		try {
			setLoading(true)
			await onSubmit(v)
			console.log('track','prompt_submitted',{ length: v.length })
			setValue('')
		} finally {
			setLoading(false)
		}
	}

	return (
		<div className="sticky top-0 z-10 bg-gradient-to-b from-white/70 to-transparent backdrop-blur pb-3">
			<label htmlFor="prompt" className="sr-only">Type your request</label>
			<div className="flex items-center gap-2 rounded-2xl border border-white/15 bg-white/80 backdrop-blur px-4 py-3 focus-within:ring-2 ring-[--vf-accent]">
				<textarea
					id="prompt"
					ref={textareaRef}
					value={value}
					onChange={(e) => setValue(e.target.value)}
					placeholder="Type here…"
					rows={1}
					className="w-full bg-transparent resize-none outline-none text-base leading-6 placeholder:opacity-60"
					onKeyDown={(e) => {
						if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
					}}
				/>
				<button aria-label="Record voice" className="p-2 rounded-lg hover:bg-white/10 focus:outline-none focus:ring-2 ring-[--vf-accent]">
					<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1v11"/><path d="M5 8a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
				</button>
				<button onClick={submit} disabled={loading} className="inline-flex items-center gap-2 rounded-xl px-3 py-2 bg-[--vf-accent] text-white disabled:opacity-50 focus:outline-none focus:ring-2 ring-[--vf-accent]" aria-label="Send message">
					{loading ? <span className="animate-spin w-4 h-4 border-2 border-white/50 border-t-transparent rounded-full"/> : (
						<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
					)}
				</button>
			</div>
			<p className="mt-1 text-xs opacity-60">Enter to send • Shift+Enter for newline • Cmd/Ctrl+K to focus</p>
			{value.length > 800 && (
				<p className="mt-1 text-xs opacity-60">Tip: Keep prompts under 200 words</p>
			)}
		</div>
	)
} 