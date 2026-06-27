import { useMemo, useCallback } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { ServiceNode, type ServiceNodeData } from './nodes/ServiceNode'
import { StorageNode, type StorageNodeData } from './nodes/StorageNode'
import { QueueNode, type QueueNodeData } from './nodes/QueueNode'
import { CLINode, type CLINodeData } from './nodes/CLINode'
import { ConfidenceEdge, type ConfidenceEdgeData } from './edges/ConfidenceEdge'
import type { Architecture } from '../types/architecture'

const nodeTypes: NodeTypes = {
  service: ServiceNode,
  storage: StorageNode,
  queue: QueueNode,
  cli: CLINode,
}

const edgeTypes: EdgeTypes = {
  confidence: ConfidenceEdge,
}

interface ArchitectureCanvasProps {
  architecture: Architecture
  selected: Set<string>
  onToggle: (componentId: string) => void
  side: 'left' | 'right'
}

export function ArchitectureCanvas({ architecture, selected, onToggle, side }: ArchitectureCanvasProps) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    const nodes: Node[] = architecture.components.map((comp, i) => {
      const cols = 3
      const col = i % cols
      const row = Math.floor(i / cols)
      return {
        id: comp.id,
        type: inferNodeType(comp.name, comp.path),
        position: { x: col * 220 + 50, y: row * 140 + 50 },
        data: {
          label: comp.name,
          role: comp.role,
          confidence: comp.confidence,
          selected: selected.has(comp.id),
        },
        draggable: true,
      }
    })

    const edges: Edge[] = architecture.relationships.map((rel, i) => ({
      id: `${rel.source_id}-${rel.target_id}-${i}`,
      source: rel.source_id,
      target: rel.target_id,
      type: 'confidence',
      data: { confidence: rel.confidence },
      animated: rel.confidence === 'verified',
    }))

    return { nodes, edges }
  }, [architecture, selected])

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    onToggle(node.id)
  }, [onToggle])

  return (
    <div className="w-full h-full">
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          colorMode="dark"
          minZoom={0.3}
          maxZoom={2}
        >
          <Controls showInteractive={false} className="!bg-arch-surface !border-arch-border" />
          <MiniMap
            className="!bg-arch-surface !border-arch-border"
            maskColor="rgba(3,7,18,0.7)"
            nodeColor="#1f2937"
          />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1f2937" />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}

function inferNodeType(name: string, path: string): string {
  const lower = `${name} ${path}`.toLowerCase()
  if (/db|database|redis|mongo|postgres|mysql|sqlite|cache|storage|disk|s3|blob/i.test(lower)) return 'storage'
  if (/queue|bus|kafka|rabbit|pub.sub|event|message|stream|mq/i.test(lower)) return 'queue'
  if (/cli|bin|cmd|entrypoint|main|runner/i.test(lower)) return 'cli'
  return 'service'
}
