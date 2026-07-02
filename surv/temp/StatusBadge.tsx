interface Props {
  online: boolean
  size?:  'sm' | 'md'
}

export default function StatusBadge({ online, size = 'sm' }: Props) {
  const dotSize  = size === 'sm' ? 'size-1.5' : 'size-2'
  const textSize = size === 'sm' ? 'text-[10px]' : 'text-xs'

  return (
    <span className="flex items-center gap-1.5">
      <span className={`${dotSize} rounded-full shrink-0 ${online ? 'bg-online animate-[pulse-dot_2s_ease-in-out_infinite]' : 'bg-dim'}`} />
      <span className={`font-mono ${textSize} ${online ? 'text-online' : 'text-muted'}`}>
        {online ? 'ONLINE' : 'OFFLINE'}
      </span>
    </span>
  )
}
