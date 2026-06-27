import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'

export type CLINodeData = {
  label: string
  role: string
  confidence: 'verified' | 'inferred' | 'unverifiable'
  selected: boolean
}

type CLINode = Node<CLINodeData>

export function CLINode({ data }: NodeProps<CLINode>) {
  return (
    <div className={`bg-arch-surface border border-arch-border rounded-lg px-4 py-3 min-w-[160px] border-l-4 border-l-blue-500 ${data.selected ? 'ring-2 ring-blue-500' : ''}`}>
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      <div className="flex items-center gap-2">
        <span className="text-lg">⌨️</span>
        <div>
          <div className="text-white text-sm font-medium">{data.label}</div>
          <div className="text-gray-400 text-xs mt-0.5">{data.role}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
    </div>
  )
}
