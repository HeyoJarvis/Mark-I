type Props = {
  name: string
  role: string
  skills: string[]
  avatar: string
}

export function TeamMemberCard({ name, role, skills, avatar }: Props) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-white shadow-sm hover:shadow-md transition w-full overflow-hidden">
      {/* Header */}
      <div className="px-3 pt-3 pb-2 flex items-center justify-between">
        <div className="min-w-0">
          <div className="font-medium leading-tight truncate">{name}</div>
          <div className="text-xs text-neutral-500 truncate">{role}</div>
        </div>
        <span className="w-2 h-2 rounded-full bg-green-500" />
      </div>
      {/* Body */}
      <div className="px-3 pb-2 flex items-start gap-2.5">
        <img
          src={encodeURI(avatar)}
          alt={name}
          className="w-9 h-9 rounded-full object-cover ring-1 ring-neutral-200 flex-shrink-0"
        />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap gap-1">
            {skills.slice(0, 2).map((skill) => (
              <span key={skill} className="text-[10px] px-1.5 py-0.5 rounded-full bg-neutral-50 text-neutral-700 border border-neutral-200">{skill}</span>
            ))}
            {skills.length > 2 && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-neutral-50 text-neutral-700 border border-neutral-200">+{skills.length - 2}</span>
            )}
          </div>
        </div>
      </div>
      {/* Footer */}
      <div className="border-t border-neutral-100 px-3 py-2 flex items-center justify-between text-[11px] text-neutral-500">
        <div className="flex items-center gap-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
          <span>0 chats</span>
        </div>
        <span>Just now</span>
      </div>
    </div>
  )
} 