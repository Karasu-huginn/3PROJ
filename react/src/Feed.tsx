import { useEffect, useState } from 'react'
import './Feed.css'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Feed() {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchFeed = async () => {
      const token = localStorage.getItem("token")
      if (!token) {
        setError("Vous devez être connecté pour voir votre fil d'actualité.")
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`${API_BASE}/feed`, {
          headers: { "Authorization": `Bearer ${token}` }
        })
        const data = await res.json()

        if (res.ok) {
          setActivities(data.activities || [])
        } else {
          setError(data.detail || "Impossible de charger le fil d'actualité.")
        }
      } catch (err) {
        setError("Erreur réseau lors de la récupération du flux.")
      } finally {
        setLoading(false)
      }
    }

    fetchFeed()
  }, [])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) return <div className="feed-status">Chargement du fil d'actualité...</div>
  if (error) return <div className="feed-error">⚠️ {error}</div>

  return (
    <div className="feed-container">
      <h2>Fil d'actualité</h2>
      
      {activities.length === 0 ? (
        <p className="feed-empty">
          Votre fil d'actualité est vide. Suivez d'autres membres pour voir leurs activités !
        </p>
      ) : (
        <div className="feed-list">
          {activities.map((activity) => {
            const actorName = activity.actor.username || "Un membre"
            
            let avatarSrc = "https://api.dicebear.com/7.x/initials/svg?seed=" + actorName
            if (activity.actor.avatar_url) {
              avatarSrc = activity.actor.avatar_url.startsWith("http")
                ? activity.actor.avatar_url
                : `${API_BASE}${activity.actor.avatar_url}`
            }

            return (
              <div key={activity.id} className="feed-card">
                
                <div className="feed-card-header">
                  <img src={avatarSrc} alt={actorName} className="feed-avatar" />
                  <div className="feed-header-info">
                    <span className="feed-actor-name">{actorName}</span>
                    <span className="feed-date">{formatDate(activity.created_at)}</span>
                  </div>
                </div>

                <div className="feed-card-body">
                  {activity.activity_type === "follow" ? (
                    <div className="activity-follow">
                      <p>
                        🤝 A commencé à suivre <strong>{activity.target_pseudo || "un nouvel utilisateur"}</strong>
                      </p>
                    </div>
                  ) : (
                    <div className="activity-review">
                      <p>
                        📝 <strong>
                          {activity.rating_score 
                            ? `A publié un avis avec une note de ${activity.rating_score}/5` 
                            : "A publié un avis"}
                        </strong> sur <strong>{activity.media_title}</strong>
                      </p>
                      
                      {activity.review_title && (
                        <blockquote className="feed-review-quote">
                          "{activity.review_title}"
                        </blockquote>
                      )}

                      {activity.media_cover && (
                        <div className="feed-media-preview">
                          <img 
                            src={activity.media_cover.startsWith("http") ? activity.media_cover : `${API_BASE}${activity.media_cover}`} 
                            alt={activity.media_title} 
                            className="feed-media-cover"
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>

              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}