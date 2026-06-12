import { useState, useEffect, useCallback } from 'react'
import type { Collection } from './api/collections'
import { fetchMyCollections, createCollection, renameCollection, deleteCollection } from './api/collections'
import ListeDetail from './ListeDetail'
import './Bibliotheque.css'

interface BibliothequeProps {
  onGoToLogin: () => void
}

interface ListeCardProps {
  collection: Collection
  onOpen: () => void
  onRename: () => void
  onDelete: () => void
}

function ListeCard({ collection, onOpen, onRename, onDelete }: ListeCardProps) {
  return (
    <div className="search-component-container liste-card" onClick={onOpen}>
      <img
        src={collection.poster_url || "https://via.placeholder.com/200x300?text=Liste"}
        alt={collection.name}
        className="liste-card-poster"
      />
      <h3 className="liste-card-name">{collection.name}</h3>
      <p className="liste-card-count">
        {collection.item_count} manga{collection.item_count > 1 ? "s" : ""}
        {!collection.is_default && (collection.is_public ? " · 🌐 publique" : " · 🔒 privée")}
      </p>
      {!collection.is_default && (
        <div className="liste-card-actions">
          <button className="btn-liste-action" onClick={(event) => { event.stopPropagation(); onRename(); }}>✏️</button>
          <button className="btn-liste-action" onClick={(event) => { event.stopPropagation(); onDelete(); }}>🗑️</button>
        </div>
      )}
    </div>
  )
}

export default function Bibliotheque({ onGoToLogin }: BibliothequeProps) {
  const isLoggedIn = Boolean(localStorage.getItem('token'))
  const [collections, setCollections] = useState<Collection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newListName, setNewListName] = useState("")
  const [newListIsPublic, setNewListIsPublic] = useState(true)

  const refreshCollections = useCallback(async () => {
    if (!isLoggedIn) return
    setIsLoading(true)
    setErrorMessage("")
    try {
      setCollections(await fetchMyCollections())
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsLoading(false)
    }
  }, [isLoggedIn])

  useEffect(() => {
    refreshCollections()
  }, [refreshCollections])

  const handleCreateSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    try {
      await createCollection(newListName, newListIsPublic)
      setNewListName("")
      setNewListIsPublic(true)
      setShowCreateForm(false)
      refreshCollections()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    }
  }

  const handleRename = async (collection: Collection) => {
    const newName = window.prompt("Nouveau nom :", collection.name)
    if (!newName || newName === collection.name) return
    try {
      await renameCollection(collection.id, newName)
      refreshCollections()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    }
  }

  const handleDelete = async (collection: Collection) => {
    const isConfirmed = window.confirm(`Supprimer "${collection.name}" et tout son contenu ?`)
    if (!isConfirmed) return
    try {
      await deleteCollection(collection.id)
      refreshCollections()
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Une erreur est survenue')
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="search-wrapper-container bibliotheque-login-prompt">
        <h2>Ma Bibliothèque</h2>
        <p>Connecte-toi pour gérer tes listes de lecture.</p>
        <button className="btn-filters-trigger" onClick={onGoToLogin}>Se connecter</button>
      </div>
    )
  }

  if (selectedCollection) {
    return (
      <ListeDetail
        collectionId={selectedCollection.id}
        onBack={() => { setSelectedCollection(null); refreshCollections(); }}
      />
    )
  }

  const defaultCollections = collections.filter((collection) => collection.is_default)
  const customCollections = collections.filter((collection) => !collection.is_default)

  return (
    <div className="search-wrapper-container">
      <div className="bibliotheque-header">
        <h2>Ma Bibliothèque</h2>
        <button className="btn-filters-trigger" onClick={() => setShowCreateForm(!showCreateForm)}>
          ➕ Nouvelle liste
        </button>
      </div>

      {showCreateForm && (
        <form className="search-component-container create-liste-form" onSubmit={handleCreateSubmit}>
          <input
            type="text"
            required
            className="search-input-field"
            placeholder="Nom de la liste"
            value={newListName}
            onChange={(event) => setNewListName(event.target.value)}
          />
          <label className="create-liste-public-label">
            <input
              type="checkbox"
              checked={newListIsPublic}
              onChange={(event) => setNewListIsPublic(event.target.checked)}
            />
            Liste publique
          </label>
          <button type="submit" className="btn-filters-trigger">Créer</button>
        </form>
      )}

      {errorMessage && <div className="status-message-centered">⚠️ {errorMessage}</div>}
      {isLoading && <div className="status-message-centered">🔄 Chargement...</div>}

      <h3 className="bibliotheque-section-title">Mes statuts</h3>
      <div className="manga-results-grid">
        {defaultCollections.map((collection) => (
          <ListeCard
            key={collection.id}
            collection={collection}
            onOpen={() => setSelectedCollection(collection)}
            onRename={() => handleRename(collection)}
            onDelete={() => handleDelete(collection)}
          />
        ))}
      </div>

      <h3 className="bibliotheque-section-title">Mes listes</h3>
      {customCollections.length === 0 && !isLoading && (
        <p className="status-message-centered">Aucune liste personnalisée pour le moment.</p>
      )}
      <div className="manga-results-grid">
        {customCollections.map((collection) => (
          <ListeCard
            key={collection.id}
            collection={collection}
            onOpen={() => setSelectedCollection(collection)}
            onRename={() => handleRename(collection)}
            onDelete={() => handleDelete(collection)}
          />
        ))}
      </div>
    </div>
  )
}
