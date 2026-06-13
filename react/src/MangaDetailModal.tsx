import { useState, useEffect, useCallback } from 'react'
import LibraryActions from './LibraryActions'
import defaultCoverUrl from './assets/default-cover.svg'

const API_BASE = import.meta.env.VITE_API_BASE

interface MangaDetailModalProps {
  mangaId: string
  onClose: () => void
  currentUserRole?: string
  currentUserId?: number
}

const FLAG_REASONS = [
  "Spoiler non marqué",
  "Insultes / langage inapproprié",
  "Contenu hors-sujet",
  "Autre",
]

export default function MangaDetailModal({ mangaId, onClose, currentUserRole, currentUserId }: MangaDetailModalProps) {
  const [mangaDetail, setMangaDetail] = useState<any>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState("")

  const [userScore, setUserScore] = useState<number>(5)
  const [reviewTitle, setReviewTitle] = useState("")
  const [reviewContent, setReviewContent] = useState("")
  const [reviewSpoiler, setReviewSpoiler] = useState(false)
  const [submittingAction, setSubmittingAction] = useState(false)

  const [flagTarget, setFlagTarget] = useState<number | null>(null)
  const [flagReason, setFlagReason] = useState(FLAG_REASONS[0])
  const [flagCustom, setFlagCustom] = useState("")
  const [flagSubmitting, setFlagSubmitting] = useState(false)

  const isAdmin = currentUserRole === "admin"

  const loadMangaDetail = useCallback(async () => {
    setLoadingDetail(true)
    setDetailError("")
    setMangaDetail(null)

    const token = localStorage.getItem("token")
    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`

    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}`, { headers })
      if (!res.ok) throw new Error("Impossible de charger les détails du manga.")
      const data = await res.json()
      setMangaDetail(data)
      if (data.media?.user_rating) setUserScore(data.media.user_rating)
    } catch (err: any) {
      setDetailError(err.message || "Erreur de chargement.")
    } finally {
      setLoadingDetail(false)
    }
  }, [mangaId])

  useEffect(() => { loadMangaDetail() }, [loadMangaDetail])

  const handleRate = async () => {
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour noter !")
    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}/rating`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ score: userScore }),
      })
      if (res.ok) { alert("Note enregistrée ! ⭐"); loadMangaDetail() }
      else alert("Erreur lors de l'enregistrement de la note.")
    } catch (err) { console.error(err) }
    finally { setSubmittingAction(false) }
  }

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour écrire une critique !")
    setSubmittingAction(true)
    try {
      const res = await fetch(`${API_BASE}/media/${mangaId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ title: reviewTitle, content: reviewContent, spoiler_flag: reviewSpoiler }),
      })
      if (res.ok) {
        alert("Critique publiée !")
        setReviewTitle(""); setReviewContent("")
        loadMangaDetail()
      } else alert("Erreur lors de la publication.")
    } catch (err) { console.error(err) }
    finally { setSubmittingAction(false) }
  }

  const handleFlagSubmit = async () => {
    if (!flagTarget) return
    const token = localStorage.getItem("token")
    if (!token) return alert("Tu dois être connecté pour signaler.")
    const reason = flagReason === "Autre" ? flagCustom.trim() : flagReason
    if (!reason) return alert("Merci de préciser la raison du signalement.")
    setFlagSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/media/reviews/${flagTarget}/flag`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ reason }),
      })
      if (res.ok) {
        alert("Signalement envoyé. Un modérateur va examiner la critique.")
        setFlagTarget(null); setFlagReason(FLAG_REASONS[0]); setFlagCustom("")
      } else {
        const data = await res.json()
        alert(data.detail || "Erreur lors du signalement.")
      }
    } catch (err) { console.error(err) }
    finally { setFlagSubmitting(false) }
  }

  const handleAdminDeleteReview = async (reviewId: number) => {
    if (!confirm("Supprimer définitivement cette critique ?")) return
    const token = localStorage.getItem("token")
    try {
      await fetch(`${API_BASE}/admin/reviews/${reviewId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
      })
      loadMangaDetail()
    } catch (err) { console.error(err) }
  }

  const handleAdminToggleFeature = async (reviewId: number) => {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(`${API_BASE}/admin/reviews/${reviewId}/feature`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
      })
      if (res.ok) loadMangaDetail()
    } catch (err) { console.error(err) }
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
              <img src={mangaDetail.media.cover_url || defaultCoverUrl} alt="" className="modal-media-cover" />
              <div>
                <h2 className="modal-media-title">{mangaDetail.media.title}</h2>
                <p className="modal-media-status">Statut : {mangaDetail.media.status || "Inconnu"}</p>
                <p className="modal-media-description">{mangaDetail.media.description || "Pas de description disponible."}</p>
                <h3 className="modal-community-rating">
                  ⭐ Note : {mangaDetail.community_rating?.average
                    ? `${mangaDetail.community_rating.average.toFixed(1)}/5 (${mangaDetail.community_rating.count || 0} avis)`
                    : "Pas encore noté"}
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

            {localStorage.getItem("token") && <LibraryActions mediaId={mangaId} />}

            {/* Coup de cœur mis en avant */}
            {mangaDetail.featured_review && (
              <div className="featured-review-block">
                <span className="featured-badge">💖 Coup de cœur</span>
                <strong className="review-title-text">{mangaDetail.featured_review.title}</strong>
                <span className="review-item-author"> par {mangaDetail.featured_review.author?.username || "Anonyme"}</span>
                <p className="review-item-body">{mangaDetail.featured_review.content}</p>
              </div>
            )}

            <h3 className="reviews-section-title">Critiques de la communauté</h3>
            <div className="reviews-scroll-container">
              {!mangaDetail.reviews || mangaDetail.reviews.length === 0 ? (
                <p>Aucun avis pour le moment.</p>
              ) : (
                mangaDetail.reviews.map((rev: any) => (
                  <div key={rev.id} className={`review-item-card ${rev.is_featured ? "review-featured" : ""} ${rev.is_flagged ? "review-flagged" : ""}`}>
                    <div className="review-item-header">
                      <div>
                        {rev.is_featured && <span className="featured-badge-small">💖 Coup de cœur</span>}
                        <strong className="review-title-text">{rev.title}</strong>
                        <span className="review-item-author"> par {rev.author?.username || "Anonyme"}</span>
                        {(rev.contains_spoiler || rev.spoiler_flag) && (
                          <span className="review-item-spoiler-tag">⚠️ SPOILER</span>
                        )}
                        {rev.is_flagged && <span className="review-flagged-tag">🚩 Signalé</span>}
                      </div>

                      <div className="review-item-actions">
                        {/* Bouton Signaler — visible si connecté et pas l'auteur */}
                        {localStorage.getItem("token") && currentUserId !== rev.author?.id && (
                          <button
                            className="btn-flag-review"
                            onClick={() => setFlagTarget(rev.id)}
                            title="Signaler cette critique"
                          >
                            🚩 Signaler
                          </button>
                        )}

                        {/* Contrôles admin */}
                        {isAdmin && (
                          <>
                            <button
                              className="btn-admin-feature"
                              onClick={() => handleAdminToggleFeature(rev.id)}
                              title={rev.is_featured ? "Retirer le coup de cœur" : "Mettre en avant"}
                            >
                              {rev.is_featured ? "💔 Retirer" : "💖 Coup de cœur"}
                            </button>
                            <button
                              className="btn-admin-delete"
                              onClick={() => handleAdminDeleteReview(rev.id)}
                              title="Supprimer la critique"
                            >
                              🗑 Supprimer
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    <p className="review-item-body">{rev.content || rev.body}</p>
                  </div>
                ))
              )}
            </div>

            {localStorage.getItem("token") && (
              <form onSubmit={handleReviewSubmit} className="review-creation-form">
                <h4 className="modal-action-title">Rédiger une critique</h4>
                <input
                  type="text"
                  placeholder="Titre de votre critique"
                  value={reviewTitle}
                  onChange={(e) => setReviewTitle(e.target.value)}
                  required disabled={submittingAction}
                  className="review-form-input"
                />
                <textarea
                  placeholder="Donnez votre avis détaillé..."
                  value={reviewContent}
                  onChange={(e) => setReviewContent(e.target.value)}
                  required disabled={submittingAction}
                  className="review-form-textarea"
                />
                <label className="review-form-checkbox-label">
                  <input type="checkbox" checked={reviewSpoiler} onChange={(e) => setReviewSpoiler(e.target.checked)} disabled={submittingAction} />
                  {" "}Signaler comme spoiler
                </label>
                <button type="submit" disabled={submittingAction} className="btn-review-publish">
                  {submittingAction ? "Publication..." : "Publier"}
                </button>
              </form>
            )}
          </div>
        )}
      </div>

      {/* Modale de signalement */}
      {flagTarget !== null && (
        <div className="modal-overlay flag-modal-overlay">
          <div className="flag-modal">
            <h3>Signaler une critique</h3>
            <p>Sélectionne la raison du signalement :</p>
            <select
              className="flag-reason-select"
              value={flagReason}
              onChange={(e) => setFlagReason(e.target.value)}
            >
              {FLAG_REASONS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            {flagReason === "Autre" && (
              <textarea
                className="flag-custom-reason"
                placeholder="Précise la raison..."
                value={flagCustom}
                onChange={(e) => setFlagCustom(e.target.value)}
                maxLength={512}
              />
            )}
            <div className="flag-modal-actions">
              <button className="btn-flag-cancel" onClick={() => setFlagTarget(null)} disabled={flagSubmitting}>
                Annuler
              </button>
              <button className="btn-flag-submit" onClick={handleFlagSubmit} disabled={flagSubmitting}>
                {flagSubmitting ? "Envoi..." : "Envoyer le signalement"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
