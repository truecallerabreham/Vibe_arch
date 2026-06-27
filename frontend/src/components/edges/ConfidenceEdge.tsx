import { BaseEdge, getBezierPath, type EdgeProps, type Edge } from '@xyflow/react'

export type ConfidenceEdgeData = {
  confidence: 'verified' | 'inferred' | 'unverifiable'
}

type ConfidenceEdge = Edge<ConfidenceEdgeData>

export function ConfidenceEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps<ConfidenceEdge>) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  const strokeColor =
    data?.confidence === 'verified' ? '#22c55e' :
    data?.confidence === 'inferred' ? '#eab308' :
    '#ef4444'

  const strokeDash = data?.confidence === 'inferred' ? '8 4' :
    data?.confidence === 'unverifiable' ? '4 4' :
    undefined

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        stroke: strokeColor,
        strokeWidth: 2,
        strokeDasharray: strokeDash,
      }}
    />
  )
}
