import { useEffect, useState, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { extractArchitecture, subscribeToProgress, getArchitecture } from '../api/client'
import { ArchitectureCanvas } from '../components/ArchitectureCanvas'
import type { Architecture } from '../types/architecture'

interface ExtractionState {
  status: 'idle' | 'queued' | 'running' | 'complete' | 'error'
  progress: string[]
  architecture: Architecture | null
  error: string | null
}

function ProgressBar({ state }: { state: ExtractionState }) {
  if (state.status === 'error') {
    return <div className="text-red-400 text-sm">Error: {state.error}</div>
  }

  const lastMsg = state.progress[state.progress.length - 1] || ''

  return (
    <div className="space-y-1">
      <div className="h-2 bg-arch-surface rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            state.status === 'complete' ? 'bg-green-500 w-full' :
            state.status === 'running' ? 'bg-blue-500 w-2/3 animate-pulse' :
            'bg-blue-500 w-1/4'
          }`}
        />
      </div>
      <p className="text-gray-400 text-xs">{lastMsg || 'Queued...'}</p>
    </div>
  )
}

export default function ComparisonPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const leftUrl = searchParams.get('left') || ''
  const rightUrl = searchParams.get('right') || ''

  const [leftState, setLeftState] = useState<ExtractionState>({
    status: 'queued', progress: [], architecture: null, error: null,
  })
  const [rightState, setRightState] = useState<ExtractionState>({
    status: 'queued', progress: [], architecture: null, error: null,
  })
  const [selectedLeft, setSelectedLeft] = useState<Set<string>>(new Set())
  const [selectedRight, setSelectedRight] = useState<Set<string>>(new Set())

  const extractOne = useCallback(async (repoUrl: string, side: 'left' | 'right') => {
    const setState = side === 'left' ? setLeftState : setRightState
    setState({ status: 'queued', progress: [], architecture: null, error: null })

    try {
      const { task_id } = await extractArchitecture(repoUrl)
      setState(prev => ({ ...prev, status: 'running' }))

      const es = subscribeToProgress(task_id, (msg) => {
        setState(prev => ({ ...prev, progress: [...prev.progress, msg] }))
      })

      const pollInterval = setInterval(async () => {
        try {
          const result = await getArchitecture(task_id)
          if (result.architecture) {
            clearInterval(pollInterval)
            es.close()
            setState(prev => ({
              ...prev,
              architecture: result.architecture,
              status: 'complete',
              progress: [...prev.progress, 'Architecture ready!'],
            }))
          }
        } catch {
          // Not ready yet, keep polling
        }
      }, 1000)

      setTimeout(() => {
        clearInterval(pollInterval)
        es.close()
        setState(prev => {
          if (prev.status !== 'complete') {
            return { ...prev, status: 'error', error: 'Extraction timed out' }
          }
          return prev
        })
      }, 60000)
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Extraction failed',
      }))
    }
  }, [])

  useEffect(() => {
    if (leftUrl) extractOne(leftUrl, 'left')
    if (rightUrl) extractOne(rightUrl, 'right')
  }, [leftUrl, rightUrl, extractOne])

  const toggleSelection = (side: 'left' | 'right', componentId: string) => {
    if (side === 'left') {
      setSelectedLeft(prev => {
        const next = new Set(prev)
        if (next.has(componentId)) next.delete(componentId)
        else next.add(componentId)
        return next
      })
    } else {
      setSelectedRight(prev => {
        const next = new Set(prev)
        if (next.has(componentId)) next.delete(componentId)
        else next.add(componentId)
        return next
      })
    }
  }

  const isComplete = leftState.status === 'complete' && rightState.status === 'complete'

  const leftRepoPath = leftUrl ? new URL(leftUrl).pathname.slice(1) : ''
  const rightRepoPath = rightUrl ? new URL(rightUrl).pathname.slice(1) : ''

  return (
    <div className="min-h-screen bg-arch-bg flex flex-col">
      <header className="border-b border-arch-border px-6 py-3 flex items-center justify-between shrink-0">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white transition-colors text-sm">
          &larr; Back
        </button>
        <h1 className="text-lg font-bold text-white">Architecture Comparison</h1>
        <div className="w-16" />
      </header>

      {!isComplete && (
        <div className="flex-1 flex items-center justify-center">
          <div className="max-w-lg w-full space-y-6 px-6">
            <div className="space-y-2">
              <h3 className="text-white font-medium">Left: {leftRepoPath}</h3>
              <ProgressBar state={leftState} />
            </div>
            <div className="space-y-2">
              <h3 className="text-white font-medium">Right: {rightRepoPath}</h3>
              <ProgressBar state={rightState} />
            </div>
            <p className="text-gray-500 text-sm text-center">Architectures are extracted via AST analysis + LLM interpretation. This may take 30-60 seconds.</p>
          </div>
        </div>
      )}

      {isComplete && leftState.architecture && rightState.architecture && (
        <div className="flex-1 flex">
          <div className="flex-1 border-r border-arch-border relative">
            <div className="absolute top-2 left-2 z-10 bg-arch-surface/80 px-2 py-1 rounded text-xs text-gray-300">
              {leftRepoPath}
            </div>
            <ArchitectureCanvas
              architecture={leftState.architecture}
              selected={selectedLeft}
              onToggle={(id) => toggleSelection('left', id)}
              side="left"
            />
          </div>
          <div className="flex-1 relative">
            <div className="absolute top-2 left-2 z-10 bg-arch-surface/80 px-2 py-1 rounded text-xs text-gray-300">
              {rightRepoPath}
            </div>
            <ArchitectureCanvas
              architecture={rightState.architecture}
              selected={selectedRight}
              onToggle={(id) => toggleSelection('right', id)}
              side="right"
            />
          </div>
        </div>
      )}
    </div>
  )
}
