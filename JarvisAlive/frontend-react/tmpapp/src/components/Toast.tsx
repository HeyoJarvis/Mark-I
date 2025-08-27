import React from 'react'

const ToastContext = React.createContext<{ success: (m: string) => void; error: (m: string) => void } | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
	const [toasts, setToasts] = React.useState<{ id: number; type: 'success' | 'error'; message: string }[]>([])
	const idRef = React.useRef(1)

	function push(type: 'success' | 'error', message: string) {
		const id = idRef.current++
		setToasts((t) => [...t, { id, type, message }])
		setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2500)
	}

	const api = React.useMemo(() => ({ success: (m: string) => push('success', m), error: (m: string) => push('error', m) }), [])

	return (
		<ToastContext.Provider value={api}>
			{children}
			<div className="pointer-events-none fixed top-4 right-4 z-[100] space-y-2">
				{toasts.map((t) => (
					<div key={t.id} className={`pointer-events-auto rounded-xl border px-4 py-2 shadow bg-white ${t.type === 'success' ? 'border-emerald-200 text-emerald-700' : 'border-rose-200 text-rose-700'}`}>{t.message}</div>
				))}
			</div>
		</ToastContext.Provider>
	)
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
	const ctx = React.useContext(ToastContext)
	if (!ctx) throw new Error('useToast must be used within ToastProvider')
	return ctx
} 