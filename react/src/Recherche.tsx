import { useState, useEffect, useRef, useCallback } from 'react'
import './Recherche.css'

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
  const [mangaDetail, setMangaDetail] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState("")
  
  const [userScore, setUserScore] = useState<number>(5)
  const [reviewTitle, setReviewTitle] = useState("")
  const [reviewContent, setReviewContent] = useState("")
  const [reviewSpoiler, setReviewSpoiler] = useState(false)
  const [submittingAction, setSubmittingAction] = useState(false)

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

  const openMangaDetail = async (mangaId: string) => {
    setSelectedMangaId(mangaId)
    setLoadingDetail(true)
    setDetailError("")
    setMangaDetail(null)
    
    const token = localStorage.getItem("token")
    const headers: any = {}
    if (token) headers["Authorization"] = `Bearer ${token}`

    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}`, { headers })
      if (!res.ok) throw new Error("Impossible de charger les détails du manga.")
      
      const data = await res.json()
      setMangaDetail(data)
      
      if (data.media?.user_rating) {
        setUserScore(data.media.user_rating)
      }
    } catch (err: any) {
      setDetailError(err.message || "Erreur de chargement.")
    } finally { 
      setLoadingDetail(false)
    }
  }

  const handleRate = async () => {
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour noter !")

    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${selectedMangaId}/rating`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ score: userScore })
      })
      if (res.ok) {
        alert("Note enregistrée ! ⭐")
        openMangaDetail(selectedMangaId!)
      } else {
        alert("Erreur lors de l'enregistrement de la note.")
      }
    } catch (err) { 
      console.error(err) 
    } finally {
      setSubmittingAction(false)
    }
  }

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour écrire une critique !")

    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${selectedMangaId}/reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          title: reviewTitle,
          content: reviewContent,
          spoiler_flag: reviewSpoiler
        })
      })
      if (res.ok) {
        alert("Critique publiée !")
        setReviewTitle("")
        setReviewContent("")
        openMangaDetail(selectedMangaId!)
      } else {
        alert("Erreur lors de la publication.")
      }
    } catch (err) { 
      console.error(err) 
    } finally {
      setSubmittingAction(false)
    }
  }

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
              onClick={() => openMangaDetail(manga.id)}
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
        <div className="modal-overlay">
          <div className="search-component-container modal-content-box">
            
            <button onClick={() => { setSelectedMangaId(null); setMangaDetail(null); setDetailError(""); }} className="modal-close-btn">✕</button>

            {loadingDetail && <div className="status-message-centered">⏳ Chargement de la fiche...</div>}
            {detailError && <div className="status-message-centered">⚠️ {detailError}</div>}

            {mangaDetail && mangaDetail.media && !loadingDetail && (
              <div>
                <div className="modal-media-header">
                  <img src={mangaDetail.media.cover_url || "https://via.placeholder.com/120x180?text=No+Cover"} alt="" className="modal-media-cover" />
                  <div>
                    <h2 className="modal-media-title">{mangaDetail.media.title}</h2>
                    <p className="modal-media-status">Statut : {mangaDetail.media.status || "Inconnu"}</p>
                    <p className="modal-media-description">{mangaDetail.media.description || "Pas de description disponible."}</p>
                    
                    <h3 className="modal-community-rating">
                      ⭐ Note : {mangaDetail.community_rating?.average ? `${mangaDetail.community_rating.average.toFixed(1)}/5 (${mangaDetail.community_rating.count || 0} avis)` : "Pas encore noté"}
                    </h3>
                  </div>
                </div>

                {localStorage.getItem("token") && (
                  <div className="modal-action-block">
                    <h4 className="modal-action-title">Attribuer une note :</h4>
                    <select disabled={submittingAction} value={userScore} onChange={(e) => setUserScore(parseFloat(e.target.value))} className="rating-select-dropdown">
                      {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].map(v => <option key={v} value={v}>{v} ⭐</option>)}
                    </select>
                    <button onClick={handleRate} disabled={submittingAction} className="btn-action-submit">
                      {submittingAction ? "Envoi..." : "Noter"}
                    </button>
                  </div>
                )}

                <h3 className="reviews-section-title">Critiques de la communauté</h3>
                <div className="reviews-scroll-container">
                  {!mangaDetail.reviews || mangaDetail.reviews.length === 0 ? (
                    <p>Aucun avis pour le moment.</p>
                  ) : (
                    mangaDetail.reviews.map((rev: any) => (
                      <div key={rev.id} className="review-item-card">
                        <strong className="review-title-text">{rev.title}</strong> 
                        <span className="review-item-author"> par {rev.author?.username || "Anonyme"}</span>
                        {(rev.contains_spoiler || rev.spoiler_tag || rev.spoiler_flag) && <span className="review-item-spoiler-tag">⚠️ SPOILER</span>}
                        <p className="review-item-body">{rev.content || rev.body}</p>
                      </div>
                    ))
                  )}
                </div>

                {localStorage.getItem("token") && (
                  <form onSubmit={handleReviewSubmit} className="review-creation-form">
                    <h4 className="modal-action-title">Rédiger une critique</h4>
                    <input type="text" placeholder="Titre de votre critique" value={reviewTitle} onChange={(e) => setReviewTitle(e.target.value)} required disabled={submittingAction} className="review-form-input" />
                    <textarea placeholder="Donnez votre avis détaillé..." value={reviewContent} onChange={(e) => setReviewContent(e.target.value)} required disabled={submittingAction} className="review-form-textarea" />
                    <label className="review-form-checkbox-label">
                      <input type="checkbox" checked={reviewSpoiler} onChange={(e) => setReviewSpoiler(e.target.checked)} disabled={submittingAction} /> Signaler comme spoiler
                    </label>
                    <button type="submit" disabled={submittingAction} className="btn-review-publish">
                      {submittingAction ? "Publication..." : "Publier"}
                    </button>
                  </form>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}