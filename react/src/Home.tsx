import { useEffect, useState } from 'react'
import './Home.css'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Home() {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [popularMangas, setPopularMangas] = useState<any[]>([])
  const [loadingPopular, setLoadingPopular] = useState(true)
  
  const [selectedUser, setSelectedUser] = useState<any | null>(null)
  const [activeChat, setActiveChat] = useState<any | null>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [newMessage, setNewMessage] = useState("")

  useEffect(() => {
    const fetchFeed = async () => {
      const token = localStorage.getItem("token")
      if (!token) { setLoading(false); return }
      try {
        const res = await fetch(`${API_BASE}/feed`, { headers: { "Authorization": `Bearer ${token}` } })
        if (res.ok) {
          const data = await res.json()
          setActivities(data?.activities || [])
        }
      } catch (err) {
        console.error("Erreur feed :", err)
      } finally {
        setLoading(false)
      }
    }
    fetchFeed()
  }, [])

  useEffect(() => {
    fetch(`${API_BASE}/media/search?limit=4`)
      .then(res => { if (!res.ok) throw new Error("Erreur serveur"); return res.json() })
      .then(data => {
        const items = data.results || data
        if (Array.isArray(items)) setPopularMangas(items.slice(0, 4))
      })
      .catch(err => console.error("Erreur populaires:", err))
      .finally(() => setLoadingPopular(false))
  }, [])

  const fetchDiscussion = async (userId: string) => {
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(`${API_BASE}/messages/${userId}`, { headers: { "Authorization": `Bearer ${token}` } })
      if (res.ok) setMessages(await res.json() || [])
    } catch (err) { console.error("Erreur historique messages :", err) }
  }

  const handleOpenChat = (user: any) => {
    setActiveChat(user)
    setSelectedUser(null)
    fetchDiscussion(user.id)
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !activeChat) return
    const token = localStorage.getItem("token")
    try {
      const res = await fetch(`${API_BASE}/messages/${activeChat.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ content: newMessage })
      })
      if (res.ok) { setNewMessage(""); fetchDiscussion(activeChat.id) }
    } catch (err) { console.error("Erreur envoi message :", err) }
  }

  const getAvatarUrl = (user: any) => {
    if (user?.avatar_url) return user.avatar_url.startsWith("http") ? user.avatar_url : `${API_BASE}${user.avatar_url}`
    return `https://api.dicebear.com/7.x/initials/svg?seed=${user?.username || 'User'}`
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return ""
    return new Date(dateString).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="home-container">
      
      <div className="home-main-content">
        
        <div className="share-card">
          <div className="share-input-container">
            <span className="share-icon">👤</span>
            <input type="text" placeholder="Partagez votre lecture actuelle..." />
          </div>
          <div className="share-actions">

          </div>
        </div>

        <div className="feed-section">
          {loading ? (
            <p className="feed-loading">Chargement du fil d'actualité...</p>
          ) : activities.length === 0 ? (
            <p className="feed-empty">Aucune activité récente dans le fil d'actualité.</p>
          ) : (
            <div className="activity-list">
              {activities.map((activity) => {
                if (!activity) return null
                const actor = activity?.actor || { username: "Un membre" }
                return (
                  <div key={activity.id || Math.random()} className="activity-card">
                    <div className="activity-header">
                      <img src={getAvatarUrl(actor)} alt={actor.username} className="activity-avatar clickable"
                        onClick={() => setSelectedUser(actor)}
                        onError={(e) => { e.currentTarget.src = `https://api.dicebear.com/7.x/initials/svg?seed=${actor.username}` }}
                      />
                      <div className="activity-meta">
                        <span className="activity-author clickable" onClick={() => setSelectedUser(actor)}>{actor.username}</span>
                        <span className="activity-date">{formatDate(activity.created_at)}</span>
                      </div>
                    </div>
                    <div className="activity-body">
                      {activity.activity_type === "follow" ? (
                        <p className="activity-text-follow">🤝 A commencé à suivre <strong className="highlight-link">{activity.target_pseudo || "un membre"}</strong></p>
                      ) : (
                        <div className="activity-review-content">
                          <p className="activity-text-review">⭐ A donné une note de <strong>{activity.rating_score}/5</strong> à <strong>{activity.media_title}</strong></p>
                          {activity.review_title && <blockquote className="activity-quote">"{activity.review_title}"</blockquote>}
                          
                          {(activity.review_content || activity.content) && (
                            <p className="feed-review-body" style={{ color: '#bbbbbb', background: '#141416', padding: '12px', borderRadius: '8px', margin: '10px 0', fontSize: '0.92rem', borderLeft: '3px solid #3498db', lineHeight: '1.5' }}>
                              {activity.review_content || activity.content}
                            </p>
                          )}

                          {activity.media_cover && (
                            <img src={activity.media_cover.startsWith("http") ? activity.media_cover : `${API_BASE}${activity.media_cover}`}
                              alt={activity.media_title} className="activity-media-cover" />
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
      </div>

      <div className="home-sidebar">
        <div className="sidebar-card">
          <h3>Qui suivre</h3>
          <p className="sidebar-placeholder-text">Aucune suggestion pour le moment.</p>
        </div>

        <div className="sidebar-card">
          <h3>Populaires cette semaine</h3>
          {loadingPopular ? (
            <p className="sidebar-placeholder-text">Chargement...</p>
          ) : popularMangas.length > 0 ? (
            <div className="popular-list">
              {popularMangas.map((m: any, i: number) => (
                <div key={m.id || i} className="popular-item">
                  <img
                    src={m.cover_url || m.coverUrl || "https://via.placeholder.com/36x50?text=?"}
                    alt={m.title}
                    className="manga-cover"
                  />
                  <div className="manga-info">
                    <h4>{m.title}</h4>
                    <span>{m.genres?.slice(0, 2).join(', ') || m.status || ''}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="sidebar-placeholder-text">Aucun manga trouvé.</p>
          )}
        </div>
      </div>

      {selectedUser && (
        <div className="profile-popover-overlay" onClick={() => setSelectedUser(null)}>
          <div className="profile-popover-card" onClick={(e) => e.stopPropagation()}>
            <div className="profile-popover-avatar-wrapper">
              <img src={getAvatarUrl(selectedUser)} alt={selectedUser.username} className="profile-popover-avatar"
                onError={(e) => { e.currentTarget.src = `https://api.dicebear.com/7.x/initials/svg?seed=${selectedUser.username}` }}
              />
            </div>
            <h4 className="profile-popover-username">{selectedUser.username}</h4>
            <div className="profile-popover-actions">
              <button className="popover-btn-profile">Voir profil</button>
              <button className="popover-btn-message" onClick={() => handleOpenChat(selectedUser)}>💬 Message</button>
            </div>
          </div>
        </div>
      )}

      {activeChat && (
        <div className="chat-modal-overlay">
          <div className="chat-modal-card">
            <div className="chat-modal-header">
              <div className="chat-modal-userinfo">
                <img src={getAvatarUrl(activeChat)} alt={activeChat.username} className="chat-modal-avatar"
                  onError={(e) => { e.currentTarget.src = `https://api.dicebear.com/7.x/initials/svg?seed=${activeChat.username}` }}
                />
                <h3>Discussion avec {activeChat.username}</h3>
              </div>
              <button className="chat-modal-close" onClick={() => setActiveChat(null)}>✕</button>
            </div>
            <div className="chat-modal-body">
              {messages.length === 0 ? (
                <p className="chat-empty-msg">Aucun message dans cette discussion.</p>
              ) : (
                <div className="chat-messages-list">
                  {messages.map((msg: any, index: number) => (
                    <div key={index} className={`chat-bubble-wrapper ${msg.sender_id === activeChat.id ? 'incoming' : 'outgoing'}`}>
                      <div className="chat-bubble">
                        <p>{msg.content}</p>
                        <span className="chat-bubble-time">{formatDate(msg.created_at)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <form className="chat-modal-footer" onSubmit={handleSendMessage}>
              <input type="text" placeholder="Écrire un message..." value={newMessage} onChange={(e) => setNewMessage(e.target.value)} />
              <button type="submit" className="chat-send-btn">Envoyer</button>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}