import { useState, useEffect, useCallback } from 'react'
import type { Collection } from './api/collections'
import { fetchMyCollections, fetchMembership, setMediaStatus, addItem, removeItem } from './api/collections'

interface LibraryActionsProps {
  mediaId: string
}

export default function LibraryActions({ mediaId }: LibraryActionsProps) {
  const [collections, setCollections] = useState<Collection[]>([])
  const [memberIds, setMemberIds] = useState<number[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  const refreshLibraryState = useCallback(async () => {
    try {
      const [myCollections, membership] = await Promise.all([fetchMyCollections(), fetchMembership(mediaId)])
      setCollections(myCollections)
      setMemberIds(membership.collection_ids)
    } catch (err: any) {
      setErrorMessage(err.message)
    }
  }, [mediaId])

  useEffect(() => {
    refreshLibraryState()
  }, [refreshLibraryState])

  const defaultCollections = collections.filter((collection) => collection.is_default)
  const customCollections = collections.filter((collection) => !collection.is_default)
  const activeStatusId = defaultCollections.find((collection) => memberIds.includes(collection.id))?.id ?? null

  const handleStatusClick = async (collectionId: number) => {
    setIsBusy(true)
    setErrorMessage("")
    try {
      await setMediaStatus(mediaId, collectionId === activeStatusId ? null : collectionId)
      await refreshLibraryState()
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsBusy(false)
    }
  }

  const handleCustomToggle = async (collectionId: number) => {
    setIsBusy(true)
    setErrorMessage("")
    try {
      if (memberIds.includes(collectionId)) {
        await removeItem(collectionId, mediaId)
      } else {
        await addItem(collectionId, mediaId)
      }
      await refreshLibraryState()
    } catch (err: any) {
      setErrorMessage(err.message)
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="modal-action-block">
      <h4 className="modal-action-title">Ma bibliothèque :</h4>
      <div className="status-buttons-row">
        {defaultCollections.map((collection) => (
          <button
            key={collection.id}
            disabled={isBusy}
            className={`btn-status-segment ${collection.id === activeStatusId ? 'active' : ''}`}
            onClick={() => handleStatusClick(collection.id)}
          >
            {collection.name}
          </button>
        ))}
      </div>

      {customCollections.length > 0 && (
        <div className="custom-lists-block">
          <h4 className="modal-action-title">Listes personnalisées :</h4>
          {customCollections.map((collection) => (
            <label key={collection.id} className="custom-list-checkbox">
              <input
                type="checkbox"
                disabled={isBusy}
                checked={memberIds.includes(collection.id)}
                onChange={() => handleCustomToggle(collection.id)}
              />
              {collection.name}
            </label>
          ))}
        </div>
      )}

      {errorMessage && <div className="library-error-message">⚠️ {errorMessage}</div>}
    </div>
  )
}
