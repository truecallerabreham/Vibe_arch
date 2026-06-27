import { useState, useCallback, useRef, useEffect } from 'react'
import { extractArchitecture, subscribeToProgress, getArchitecture } from '../api/client'
import type { Architecture } from '../types/architecture'

interface ExtractionState {
  status: 'idle' | 'queued' | 'running' | 'complete' | 'error'
  progress: string[]
  architecture: Architecture | null
  error: string | null
}

export function useArchitecture() {
  const [state, setState] = useState<ExtractionState>({
    status: 'idle',
    progress: [],
    architecture: null,
    error: null,
  })
  const eventSourceRef = useRef<EventSource | null>(null)

  const startExtraction = useCallback(async (repoUrl: string) => {
    setState({ status: 'queued', progress: [], architecture: null, error: null })

    try {
      const { task_id } = await extractArchitecture(repoUrl)
      setState(prev => ({ ...prev, status: 'running' }))

      const es = subscribeToProgress(task_id, (msg) => {
        setState(prev => ({
          ...prev,
          progress: [...prev.progress, msg],
          status: msg === 'Done!' ? 'complete' : prev.status,
        }))
      })

      eventSourceRef.current = es

      // Poll for result
      const pollInterval = setInterval(async () => {
        try {
          const result = await getArchitecture(task_id)
          if (result.architecture) {
            clearInterval(pollInterval)
            es.close()
            eventSourceRef.current = null
            setState(prev => ({
              ...prev,
              architecture: result.architecture,
              status: 'complete',
              progress: [...prev.progress, 'Architecture ready!'],
            }))
          }
        } catch {
          // Not ready yet
        }
      }, 1000)

      es.onerror = () => {
        es.close()
        eventSourceRef.current = null
      }

      // Timeout after 60 seconds
      setTimeout(() => {
        clearInterval(pollInterval)
        if (eventSourceRef.current) {
          eventSourceRef.current.close()
          eventSourceRef.current = null
        }
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

  const reset = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setState({ status: 'idle', progress: [], architecture: null, error: null })
  }, [])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return { ...state, startExtraction, reset }
}
