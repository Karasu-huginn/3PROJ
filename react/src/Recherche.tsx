import { useState, useEffect, useRef, useCallback } from 'react'
import './Recherche.css'
import MangaDetailModal from './MangaDetailModal'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Recherche() {
  const [mangas, setMangas] = useState<any[]>([])
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const [genres, setGenres] = useState<any[]>([])
  const [selectedGenre, setSelectedGenre] = useState("")
  const [showFilters, setShowFilters] = useState(false)

  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  const [selectedMangaId, setSelectedMangaId] = useState<string | null>(null)

  const observer = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/media/tags`)
      .then(res => {
        if (!res.ok) throw new Error("Impossible de récupérer les filtres.")
        return res.json()
      })
      .then(data => {
        if (data.genres) setGenres(data.genres)
      })
      .catch(err => console.error("Erreur tags:", err))
  }, [])

  useEffect(() => {
    setMangas([])
    setPage(1)
    setHasMore(true)
  }, [query, selectedGenre])


  useEffect(() => {
    executeSearch(page)
  }, [page, query, selectedGenre])

  const executeSearch = async (pageNumber: number) => {
    if (loading || (!hasMore && pageNumber > 1)) return

    setLoading(true)
    setError("")

    try {
      const params = new URLSearchParams()
      if (query.trim() !== "") params.append("title", query)
      if (selectedGenre !== "") params.append("genre", selectedGenre)


       params.append("limit", "20")
       params.append("offset", ((pageNumber - 1) * 20).toString())

      const response = await fetch(`${API_BASE}/media/search?${params.toString()}`)
      if (!response.ok) throw new Error("Erreur serveur lors de la recherche.")

      const data = await response.json()
      const results = data.results || data || []

      if (results.length === 0) {
        setHasMore(false)
      }

      setMangas(prev => pageNumber === 1 ? results : [...prev, ...results])

    } catch (err: any) {
      setError(err.message || "Une erreur est survenue lors de la recherche.")
    } finally {
      setLoading(false)
    }
  }

  const lastMangaElementRef = useCallback((node: HTMLDivElement) => {
    if (loading) return
    if (observer.current) observer.current.disconnect()

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1)
      }
    })

    if (node) observer.current.observe(node)
  }, [loading, hasMore])

  return (
    <div className="search-wrapper-container">

      <div className="search-component-container">
        <form onSubmit={(e) => { e.preventDefault(); setPage(1); executeSearch(1); }}>
          <input
            type="text"
            className="search-input-field"
            placeholder="Rechercher un manga..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit" className="btn-filters-trigger btn-search-submit">Rechercher</button>
          <button type="button" className="btn-filters-trigger btn-filters-toggle" onClick={() => setShowFilters(!showFilters)}>
            {showFilters ? "🔹 Masquer Filtres" : "🔸 Filtrer par Genre"}
          </button>
        </form>
      </div>

      {showFilters && (
        <div className="search-component-container filters-section">
          <h4 className="filters-title">Genres :</h4>
          <div className="tags-list-container tags-list-container-genres">
            <span
              onClick={() => setSelectedGenre("")}
              className={`tag-item ${selectedGenre === "" ? "active" : ""}`}
            >
              Tous
            </span>
            {genres.map(g => (
              <span
                key={g.id}
                onClick={() => setSelectedGenre(g.id)}
                className={`tag-item ${selectedGenre === g.id ? "active" : ""}`}
              >
                {g.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="manga-results-grid">
        {mangas.map((manga: any, index: number) => {
          const currentCover = manga.coverUrl || manga.cover_url || "https://via.placeholder.com/200x300?text=No+Cover"

          const isLastElement = mangas.length === index + 1

          return (
            <div
              key={`${manga.id}-${index}`}
              ref={isLastElement ? lastMangaElementRef : null}
              className="search-component-container manga-card-clickable"
              onClick={() => setSelectedMangaId(manga.id)}
            >
              <img src={currentCover} alt={manga.title} className="manga-card-cover" />
              <h3 className="manga-card-title">{manga.title}</h3>
            </div>
          )
        })}
      </div>

      {loading && <div className="status-message-centered">🔄 Chargement des mangas...</div>}
      {error && <div className="status-message-centered">⚠️ {error}</div>}
      {!hasMore && mangas.length > 0 && <div className="status-message-centered" style={{opacity: 0.5}}>Fin de la collection. ✨</div>}

      {selectedMangaId && (
        <MangaDetailModal key={selectedMangaId} mangaId={selectedMangaId} onClose={() => setSelectedMangaId(null)} />
      )}
    </div>
  )
}
