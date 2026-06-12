const API_BASE = import.meta.env.VITE_API_BASE

export interface Collection {
  id: number
  name: string
  is_default: boolean
  is_public: boolean
  item_count: number
  poster_url: string | null
}

export interface CollectionItem {
  media_id: string
  title: string
  cover_url: string | null
}

export interface CollectionDetail {
  collection: Collection
  items: CollectionItem[]
}

/** Build the auth headers, failing fast when no token is stored. */
function buildAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('token')
  if (!token) throw new Error('Connecte-toi pour utiliser ta bibliothèque')
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

/** Run an authenticated request and return the parsed JSON body. */
async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers: buildAuthHeaders() })
  if (response.status === 401) {
    localStorage.removeItem('token')  //* because a 401 means the token is stale; 403 is a permission error and must NOT log the user out
    throw new Error('Connecte-toi pour utiliser ta bibliothèque')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail ?? 'Une erreur est survenue')
  }
  return response.json() as Promise<T>
}

/** Fetch the caller's collections, defaults first. */
export function fetchMyCollections(): Promise<Collection[]> {
  return requestJson<Collection[]>('/collections/me')
}

/** Fetch one collection with its items. */
export function fetchCollectionItems(collectionId: number): Promise<CollectionDetail> {
  return requestJson<CollectionDetail>(`/collections/${collectionId}/items`)
}

/** Create a custom collection. */
export function createCollection(name: string, isPublic: boolean): Promise<Collection> {
  return requestJson<Collection>('/collections', { method: 'POST', body: JSON.stringify({ name, is_public: isPublic }) })
}

/** Rename a custom collection. */
export function renameCollection(collectionId: number, name: string): Promise<Collection> {
  return requestJson<Collection>(`/collections/${collectionId}`, { method: 'PATCH', body: JSON.stringify({ name }) })
}

/** Toggle a collection's public visibility. */
export function setVisibility(collectionId: number, isPublic: boolean): Promise<Collection> {
  return requestJson<Collection>(`/collections/${collectionId}`, { method: 'PATCH', body: JSON.stringify({ is_public: isPublic }) })
}

/** Delete a custom collection and its items. */
export function deleteCollection(collectionId: number): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}`, { method: 'DELETE' })
}

/** Add a media to a collection. */
export function addItem(collectionId: number, mediaId: string): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}/item/${mediaId}`, { method: 'POST' })
}

/** Remove a media from a collection. */
export function removeItem(collectionId: number, mediaId: string): Promise<{ detail: string }> {
  return requestJson<{ detail: string }>(`/collections/${collectionId}/item/${mediaId}`, { method: 'DELETE' })
}

/** Set the media's reading status (null clears it). */
export function setMediaStatus(mediaId: string, collectionId: number | null): Promise<{ collection_id: number | null }> {
  return requestJson<{ collection_id: number | null }>(`/collections/me/status/${mediaId}`, { method: 'PUT', body: JSON.stringify({ collection_id: collectionId }) })
}

/** Fetch the ids of the caller's collections containing the media. */
export function fetchMembership(mediaId: string): Promise<{ collection_ids: number[] }> {
  return requestJson<{ collection_ids: number[] }>(`/collections/me/membership/${mediaId}`)
}
