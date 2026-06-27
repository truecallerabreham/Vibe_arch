export type Confidence = 'verified' | 'inferred' | 'unverifiable'

export interface Component {
  id: string
  name: string
  role: string
  path: string
  confidence: Confidence
  children: string[]
}

export interface Relationship {
  source_id: string
  target_id: string
  type: string
  confidence: Confidence
}

export interface Architecture {
  repo_url: string
  components: Component[]
  relationships: Relationship[]
}
