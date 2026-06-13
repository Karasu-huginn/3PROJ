import { useState } from 'react'
import Profile from './Profile' 
import './RechercheUsers.css'

const API_BASE = import.meta.env.VITE_API_BASE

export default function RechercheUsers() {
  const [query, setQuery] = useState("")
  const [users, setUsers] = useState<any[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const [activeChatUser, setActiveChatUser] = useState<any | null>(null)
  const [chatMessages, setChatMessages] = useState<any[]>([])
  const [newMessage, setNewMessage] = useState("")
  const [loadingChat, setLoadingChat] = useState(false)
  const [chatError, setChatError] = useState("")

  const searchUsers = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/users/search?username=${query}`)
      const data = await res.json()
      setUsers(Array.isArray(data) ? data : (data.results || []))
    } catch (err) {
      console.error("Erreur recherche:", err)
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  // --- Charger l'historique de la conversation ---
  const openChat = async (targetUser: any) => {
    setActiveChatUser(targetUser)
    setChatError("")
    setChatMessages([])
    setLoadingChat(true)
    
    const token = localStorage.getItem("token")
    if (!token) {
      setChatError("Vous devez être connecté pour envoyer un message.")
      setLoadingChat(false)
      return
    }

    try {
      const res = await fetch(`${API_BASE}/messages/${targetUser.id}`, {
        headers: { "Authorization": `Bearer ${token}` }
      })
      const data = await res.json()
      
      if (res.ok) {
        if (Array.isArray(data)) {
          if (data.length === 2 && Array.isArray(data[0])) {
            setChatMessages(data[0])
          } else {
            setChatMessages(data)
          }
        } else if (data.messages) {
          setChatMessages(data.messages)
        } else if (data.results) {
          setChatMessages(data.results)
        }
      } else {
        setChatError(data.detail || "Impossible de charger la conversation.")
      }
    } catch (err) {
      setChatError("Erreur réseau lors du chargement des messages.")
    } finally {
      setLoadingChat(false)
    }
  }

  // --- Envoyer un nouveau message ---
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !activeChatUser) return

    const token = localStorage.getItem("token")
    try {
      const res = await fetch(`${API_BASE}/messages/${activeChatUser.id}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ content: newMessage })
      })
      const data = await res.json()
      
      if (res.ok) {
        setChatMessages(prev => [...prev, data])
        setNewMessage("")
        setChatError("")
      } else {
        setChatError(data.detail || "Erreur lors de l'envoi.")
      }
    } catch (err) {
      setChatError("Erreur réseau lors de l'envoi du message.")
    }
  }

  return (
    <div className="search-wrapper-container">
      <h2>Trouver des membres</h2>
      
      <form onSubmit={searchUsers} className="search-component-container">
        <input 
          type="text" 
          placeholder="Pseudo de l'utilisateur..." 
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
        />
        <button type="submit" disabled={loading}>
          {loading ? "Recherche..." : "🔍 Rechercher"}
        </button>
      </form>
      
      <div className="user-results-grid">
        {users.length > 0 ? (
          users.map(user => {
            const displayName = user.pseudo || user.username || "Membre";
            let avatarSrc = "https://api.dicebear.com/7.x/initials/svg?seed=" + displayName;
            if (user.avatar_url) {
              avatarSrc = user.avatar_url.startsWith("http") 
                ? user.avatar_url 
                : `${API_BASE}${user.avatar_url}`;
            }

            return (
              <div key={user.id} className="user-card">
                <img src={avatarSrc} alt={displayName} />
                <h3>{displayName}</h3>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '10px' }}>
                  <button onClick={() => setSelectedUserId(user.id)}>
                    Voir profil
                  </button>
                  <button 
                    onClick={() => openChat(user)}
                    style={{ background: '#3498db', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    💬 Message
                  </button>
                </div>
              </div>
            )
          })
        ) : (
          <p>Aucun utilisateur trouvé.</p>
        )}
      </div>

      {selectedUserId && (
        <div className="profile-overlay">
          <button onClick={() => setSelectedUserId(null)}>Fermer le profil</button>
          <Profile userId={selectedUserId} />
        </div>
      )}

      {activeChatUser && (() => {
        const chatDisplayName = activeChatUser.pseudo || activeChatUser.username || "Membre";
        let chatAvatarSrc = "https://api.dicebear.com/7.x/initials/svg?seed=" + chatDisplayName;
        if (activeChatUser.avatar_url) {
          chatAvatarSrc = activeChatUser.avatar_url.startsWith("http") 
            ? activeChatUser.avatar_url 
            : `${API_BASE}${activeChatUser.avatar_url}`;
        }

        return (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 10000,
            padding: '20px',
            boxSizing: 'border-box'
          }} onClick={() => setActiveChatUser(null)}>
            
            <div style={{
              background: '#1a1a1e',
              border: '1px solid #333',
              borderRadius: '12px',
              width: '100%',
              maxWidth: '450px',
              height: '75vh',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              color: 'white',
              boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
            }} onClick={(e) => e.stopPropagation()}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '15px 20px', borderBottom: '1px solid #333' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <img 
                    src={chatAvatarSrc} 
                    alt={chatDisplayName} 
                    style={{ width: '35px', height: '35px', borderRadius: '50%', objectFit: 'cover' }}
                  />
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 'bold' }}>{chatDisplayName}</h3>
                </div>
                <button 
                  onClick={() => setActiveChatUser(null)}
                  style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.2rem', cursor: 'pointer', opacity: 0.7 }}
                >
                  ✕
                </button>
              </div>

              <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', background: '#121214' }}>
                {loadingChat ? (
                  <p style={{ textAlign: 'center', color: '#aaa' }}>Chargement de la discussion...</p>
                ) : chatError ? (
                  <div style={{ padding: '15px', background: 'rgba(255, 71, 87, 0.1)', border: '1px solid #ff4757', borderRadius: '8px', color: '#ff4757', textAlign: 'center', fontSize: '0.9rem', fontWeight: '500' }}>
                    ⚠️ {chatError}
                  </div>
                ) : chatMessages.length > 0 ? (
                  chatMessages.map((msg: any) => {
                    const isMe = msg.sender?.id !== activeChatUser.id
                    return (
                      <div key={msg.id} style={{ display: 'flex', justifyContent: isMe ? 'flex-end' : 'flex-start', width: '100%' }}>
                        <div style={{
                          background: isMe ? '#3498db' : '#2d2d30',
                          color: '#fff',
                          padding: '10px 14px',
                          borderRadius: isMe ? '14px 14px 0 14px' : '14px 14px 14px 0',
                          maxWidth: '75%',
                          wordBreak: 'break-word',
                          fontSize: '0.95rem'
                        }}>
                          {msg.content}
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <p style={{ textAlign: 'center', color: '#666', fontStyle: 'italic', marginTop: '20px' }}>
                    Aucun message dans cette discussion. Lancez la conversation !
                  </p>
                )}
              </div>

              {!chatError.includes("suivre mutuellement") && (
                <form onSubmit={handleSendMessage} style={{ padding: '15px', borderTop: '1px solid #333', display: 'flex', gap: '10px', background: '#1a1a1e', borderRadius: '0 0 12px 12px' }}>
                  <input 
                    type="text"
                    placeholder="Écrivez votre message..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    style={{
                      flex: 1,
                      background: '#252529',
                      border: '1px solid #444',
                      borderRadius: '20px',
                      padding: '10px 15px',
                      color: 'white',
                      outline: 'none'
                    }}
                  />
                  <button 
                    type="submit"
                    disabled={!newMessage.trim()}
                    style={{
                      background: newMessage.trim() ? '#2ed573' : '#444',
                      color: 'white',
                      border: 'none',
                      padding: '10px 18px',
                      borderRadius: '20px',
                      cursor: newMessage.trim() ? 'pointer' : 'default',
                      fontWeight: 'bold'
                    }}
                  >
                    Envoyer
                  </button>
                </form>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}