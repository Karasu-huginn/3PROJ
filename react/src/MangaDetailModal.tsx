import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE

interface MangaDetailModalProps {
  mangaId: string
  onClose: () => void
}

export default function MangaDetailModal({ mangaId, onClose }: MangaDetailModalProps) {
  const [mangaDetail, setMangaDetail] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState("")

  const [userScore, setUserScore] = useState<number>(5)
  const [reviewTitle, setReviewTitle] = useState("")
  const [reviewContent, setReviewContent] = useState("")
  const [reviewSpoiler, setReviewSpoiler] = useState(false)
  const [submittingAction, setSubmittingAction] = useState(false)

  const loadMangaDetail = useCallback(async () => {
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
  }, [mangaId])

  useEffect(() => {
    loadMangaDetail()
  }, [loadMangaDetail])

  const handleRate = async () => {
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour noter !")

    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}/rating`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ score: userScore })
      })
      if (res.ok) {
        alert("Note enregistrée ! ⭐")
        loadMangaDetail()
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
      const res = await fetch(`${API_BASE}/media/${mangaId}/reviews`, {
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
        loadMangaDetail()
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
    <div className="modal-overlay">
      <div className="search-component-container modal-content-box">

        <button onClick={onClose} className="modal-close-btn">✕</button>

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
  )
}
