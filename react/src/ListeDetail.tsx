import { useState, useEffect, useCallback } from 'react'
import type { CollectionDetail } from './api/collections'
import { fetchCollectionItems, removeItem } from './api/collections'

interface ListeDetailProps {
  collectionId: number
  onBack: () => void
  onOpenManga: (mediaId: string) => void
}

export default function ListeDetail({ collectionId, onBack, onOpenManga }: ListeDetailProps) {
  const [detail, setDetail] = useState<CollectionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [isBusy, setIsBusy] = useState(false)

  const refreshItems = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage("")
    try {
      setDetail(await fetchCollectionItems(collectionId))
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsLoading(false)
    }
  }, [collectionId])

  useEffect(() => {
    refreshItems()
  }, [refreshItems])

  const handleRemoveItem = async (mediaId: string) => {
    setIsBusy(true)
    try {
      await removeItem(collectionId, mediaId)
      await refreshItems()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="search-wrapper-container">
      <div className="search-back-row">
        <h3 style={{ margin: 0 }}>{detail ? detail.collection.name : "Chargement..."}</h3>
        <span onClick={onBack} style={{ cursor: 'pointer' }}>← Retour à la bibliothèque</span>
      </div>

      {isLoading && <div className="status-message-centered">🔄 Chargement...</div>}
      {errorMessage && <div className="status-message-centered">⚠️ {errorMessage}</div>}
      {detail && detail.items.length === 0 && !isLoading && (
        <div className="status-message-centered">Cette liste est vide pour le moment.</div>
      )}

      <div className="manga-results-grid">
        {detail?.items.map((item) => (
          <div key={item.media_id} className="search-component-container manga-card-clickable">
            <img
              src={item.cover_url || "https://via.placeholder.com/200x300?text=No+Cover"}
              alt={item.title}
              className="manga-card-cover"
              onClick={() => onOpenManga(item.media_id)}
            />
            <h3 className="manga-card-title" onClick={() => onOpenManga(item.media_id)}>{item.title}</h3>
            <button
              className="btn-filters-trigger btn-retirer"
              disabled={isBusy}
              onClick={() => handleRemoveItem(item.media_id)}
            >
              Retirer
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
