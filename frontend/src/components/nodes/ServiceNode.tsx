import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'

export type ServiceNodeData = {
  label: string
  role: string
  confidence: 'verified' | 'inferred' | 'unverifiable'
  selected: boolean
}

type ServiceNode = Node<ServiceNodeData>

export function ServiceNode({ data }: NodeProps<ServiceNode>) {
  const confidenceColor =
    data.confidence === 'verified' ? 'border-l-arch-green' :
    data.confidence === 'inferred' ? 'border-l-arch-yellow' :
    'border-l-arch-red'

  return (
    <div className={`bg-arch-surface border border-arch-border rounded-lg px-4 py-3 min-w-[160px] border-l-4 ${confidenceColor} ${data.selected ? 'ring-2 ring-blue-500' : ''}`}>
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      <div className="text-white text-sm font-medium">{data.label}</div>
      <div className="text-gray-400 text-xs mt-1 line-clamp-2">{data.role}</div>
      <div className="flex items-center gap-1.5 mt-2">
        <ConfidenceDot level={data.confidence} />
        <span className="text-[10px] text-gray-500 capitalize">{data.confidence}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
    </div>
  )
}

function ConfidenceDot({ level }: { level: string }) {
  const color =
    level === 'verified' ? 'bg-arch-green' :
    level === 'inferred' ? 'bg-arch-yellow' :
    'bg-arch-red'
  return <span className={`w-1.5 h-1.5 rounded-full ${color}`} />
}
