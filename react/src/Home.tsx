import { useState, useEffect } from 'react'
import './Home.css'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Home() {
  const [feed] = useState([])
  
  const [popularManga, setPopularManga] = useState<any[]>([])
  const [loadingPopular, setLoadingPopular] = useState(true)

  useEffect(() => {
  fetch(`${API_BASE}/media/search?limit=4`) 
    .then((res) => {
      if (!res.ok) throw new Error("Erreur serveur")
      return res.json()
    })
    .then((data) => {
      const items = data.results || data
      if (Array.isArray(items)) {
        setPopularManga(items.slice(0, 4))
      }
    })
    .catch((err) => {
      console.error("Erreur populaires:", err)
    })
    .finally(() => {
      setLoadingPopular(false)
    })
}, [])

  return (
    <div className="home-container">
      
      <div className="feed-column">
        
        <div className="share-box">
          <div className="share-box-input-row">
            <div className="share-box-avatar">👤</div>
            <input 
              type="text" 
              placeholder="Partagez votre lecture actuelle..." 
              className="share-box-input"
            />
          </div>
          <div className="share-box-actions">
            <span className="share-action-item">📝 Écrire un avis</span>
            <span className="share-action-item">⭐ Noter un manga</span>
            <span className="share-action-item">➕ Créer une liste</span>
          </div>
        </div>

        {feed.length > 0 ? (
          feed.map((item: any) => (
            <div key={item.id} className="feed-card">
              <div className="feed-user-row">
                <div className="feed-avatar">{item.username[0].toUpperCase()}</div>
                <div>
                  <span className="feed-username">{item.username}</span>{' '}
                  <span className="feed-action">{item.action}</span>
                  <div className="feed-time">{item.time}</div>
                </div>
              </div>

              <div className="feed-manga-box">
                <img src={item.manga.coverUrl} alt={item.manga.title} className="feed-manga-cover" />
                <div className="feed-manga-info">
                  <h4 className="feed-manga-title">{item.manga.title}</h4>
                  <p className="feed-manga-meta">{item.manga.author} · {item.manga.year}</p>
                  <div className="feed-stars">
                    {'★'.repeat(item.rating)}{'☆'.repeat(5 - item.rating)}
                  </div>
                  {item.text && <p className="feed-review-text">"{item.text}"</p>}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-feed-message">
            <p>Aucune activité récente dans le fil d'actualité.</p>
          </div>
        )}
      </div>

      <div className="sidebar-column">
        
        <div className="sidebar-card">
          <h4 className="sidebar-title empty-title">Qui suivre</h4>
          <p className="sidebar-empty-text">Aucune suggestion pour le moment.</p>
        </div>

        <div className="sidebar-card">
          <h4 className="sidebar-title">Populaires cette semaine</h4>
          
          {loadingPopular ? (
            <p className="sidebar-empty-text">Chargement des tendances...</p>
          ) : popularManga.length > 0 ? (
            <>
              <div className="sidebar-list">
                {popularManga.map((m: any, i: number) => (
                  <div key={m.id || i} className="manga-popular-item">
                    <img 
                      src={m.cover_url || m.coverUrl || "https://via.placeholder.com/150x220?text=No+Cover"} 
                      alt={m.title} 
                      className="manga-popular-cover" 
                    />
                    <div className="manga-popular-details">
                      <div className="manga-popular-title">{m.title}</div>
                      <div className="manga-popular-author">
                        {m.genres ? m.genres.slice(0, 2).join(', ') : (m.status || 'Manga')}
                      </div>
                      {m.average_rating && (
                        <div className="manga-popular-rating">⭐ {m.average_rating.toFixed(1)}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="see-more-link">Voir plus →</div>
            </>
          ) : (
            <p className="sidebar-empty-text">Aucun manga populaire trouvé en base de données.</p>
          )}
        </div>

      </div>
    </div>
  )
}