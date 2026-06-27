const API_BASE = '/api'

export async function extractArchitecture(repoUrl: string, signal?: AbortSignal): Promise<{ task_id: string }> {
  const res = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
    signal,
  })
  if (!res.ok) throw new Error(`Extraction failed: ${res.statusText}`)
  return res.json()
}

export async function getArchitecture(taskId: string): Promise<ArchitectureResponse> {
  const res = await fetch(`${API_BASE}/architecture/${taskId}`)
  if (!res.ok) throw new Error(`Fetch failed: ${res.statusText}`)
  return res.json()
}

export function subscribeToProgress(taskId: string, onProgress: (msg: string) => void): EventSource {
  const es = new EventSource(`${API_BASE}/extract/stream/${taskId}`)
  es.onmessage = (e) => onProgress(e.data)
  return es
}

export interface ArchitectureResponse {
  architecture: import('../types/architecture').Architecture
}
