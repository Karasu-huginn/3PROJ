import { useState, useEffect } from 'react'
import './Home.css'
import defaultAvatarUrl from './assets/default-avatar.svg'

const API_BASE = import.meta.env.VITE_API_BASE

interface AuthProps {
  onBackToHome: () => void;
}

export default function Auth({ onBackToHome }: AuthProps) {
  const [user, setUser] = useState<any>(null)
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ text: "", isError: false })

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [pseudo, setPseudo] = useState("")

  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState<'followers' | 'following'>('followers')
  const [modalUsers, setModalUsers] = useState<any[]>([])
  const [loadingModal, setLoadingModal] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (token) {
      fetchUserProfile(token)
    }
  }, [])

  const updateLiveCounters = async (userId: number, token: string) => {
    try {
      const [resFollowers, resFollowing] = await Promise.all([
        fetch(`${API_BASE}/users/${userId}/followers`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${API_BASE}/users/${userId}/following`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);
      
      let followersCount = 0;
      let followingCount = 0;

      if (resFollowers.ok) {
        const data = await resFollowers.json();
        followersCount = Array.isArray(data) ? data.length : (data.results?.length || 0);
      }
      if (resFollowing.ok) {
        const data = await resFollowing.json();
        followingCount = Array.isArray(data) ? data.length : (data.results?.length || 0);
      }

      setUser((prev: any) => prev ? { ...prev, follower_count: followersCount, following_count: followingCount } : prev);
    } catch (err) {
      console.error("Erreur lors de la mise à jour des compteurs:", err);
    }
  };

  const fetchUserProfile = (token: string) => {
    fetch(`${API_BASE}/auth/profile`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error()
        return res.json()
      })
      .then(data => {
        setUser(data);
        if (data && data.id) {
          updateLiveCounters(data.id, token);
        }
      })
      .catch(() => logout())
  }

  const openFollowModal = async (type: 'followers' | 'following') => {
    if (!user || !user.id) return;
    setModalType(type);
    setShowModal(true);
    setLoadingModal(true);
    setModalUsers([]);

    const token = localStorage.getItem("token");
    try {
      const res = await fetch(`${API_BASE}/users/${user.id}/${type}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setModalUsers(Array.isArray(data) ? data : (data.results || []));
      }
    } catch (err) {
      console.error("Erreur de récupération de la liste:", err);
    } finally {
      setLoadingModal(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage({ text: "", isError: false })

    const endpoint = isRegister ? "/auth/register" : "/auth/login"
    const payload = isRegister ? { email, password, pseudo } : { email, password }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || "Une erreur est survenue")
      }

      localStorage.setItem("token", data.access_token)
      fetchUserProfile(data.access_token)
      setMessage({ text: "Connexion réussie !", isError: false })
    } catch (err: any) {
      setMessage({ text: err.message, isError: true })
    } finally {
      setLoading(false)
    }
  };

  const logout = () => {
    localStorage.removeItem("token")
    setUser(null)
  };

  if (user) {
    return (
      <div className="search-wrapper-container" style={{ maxWidth: '850px', margin: '40px auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #333', paddingBottom: '15px' }}>
          <h3 style={{ margin: 0, color: 'white' }}>Mon Profil</h3>
          <span onClick={onBackToHome} style={{ cursor: 'pointer', color: '#3498db', fontWeight: 'bold' }}>← Retour à l'accueil</span>
        </div>

        <div style={{ 
          display: 'flex', 
          flexDirection: 'row', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          gap: '25px', 
          background: '#1a1a1a', 
          padding: '25px', 
          borderRadius: '12px',
          border: '1px solid #333',
          flexWrap: 'wrap'
        }}>
          
          <div style={{ flexShrink: 0 }}>
            <img 
              src={user.avatar_url || defaultAvatarUrl} 
              alt="Avatar" 
              style={{ width: '100px', height: '100px', borderRadius: '50%', objectFit: 'cover', border: '2px solid #3498db' }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minWidth: '180px', flex: 1 }}>
            <h2 style={{ color: '#fff', margin: 0, fontSize: '1.5rem', fontWeight: 'bold' }}>{user.pseudo}</h2>
            <p style={{ color: '#888', fontSize: '0.9rem', margin: 0 }}>{user.email}</p>
            
            <div style={{ display: 'flex', gap: '15px', marginTop: '6px', fontSize: '0.9rem' }}>
              <span 
                onClick={() => openFollowModal('followers')} 
                style={{ color: '#3498db', cursor: 'pointer', fontWeight: 'bold', textDecoration: 'underline' }}
              >
                {user.follower_count || 0} Abonnés
              </span>
              <span 
                onClick={() => openFollowModal('following')} 
                style={{ color: '#3498db', cursor: 'pointer', fontWeight: 'bold', textDecoration: 'underline' }}
              >
                {user.following_count || 0} Abonnements
              </span>
            </div>
          </div>
          
          <div style={{ background: '#252525', padding: '15px', borderRadius: '8px', flex: 2, minWidth: '220px', textAlign: 'left' }}>
            <strong style={{ color: '#fff', display: 'block', marginBottom: '5px' }}>Bio :</strong>
            <p style={{ color: '#ccc', margin: 0, fontSize: '0.9rem', lineHeight: '1.4' }}>
              {user.bio || "Aucune biographie rédigée pour le moment."}
            </p>
          </div>

          <div style={{ flexShrink: 0, minWidth: '150px' }}>
            <button 
              onClick={logout} 
              style={{ width: '100%', background: '#ff4757', color: '#fff', border: 'none', padding: '12px 20px', borderRadius: '20px', fontWeight: 'bold', cursor: 'pointer' }}
            >
              🚪 Se déconnecter
            </button>
          </div>
        </div>

        {showModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999,
            padding: '20px',
            boxSizing: 'border-box'
          }} onClick={() => setShowModal(false)}>
            
            <div style={{
              background: '#1a1a1e',
              border: '1px solid #333',
              borderRadius: '12px',
              width: '100%',
              maxWidth: '400px',
              maxHeight: '75vh',
              overflowY: 'auto',
              padding: '25px',
              position: 'relative',
              color: 'white',
              boxShadow: '0 10px 30px rgba(0,0,0,0.6)'
            }} onClick={(e) => e.stopPropagation()}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #333', paddingBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 'bold' }}>
                  {modalType === 'followers' ? 'Mes Abonnés' : 'Mes Abonnements'}
                </h3>
                <button 
                  onClick={() => setShowModal(false)}
                  style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.3rem', cursor: 'pointer', opacity: 0.7 }}
                >
                  ✕
                </button>
              </div>

              {loadingModal ? (
                <p style={{ textAlign: 'center', color: '#aaa' }}>Chargement de la liste...</p>
              ) : modalUsers.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {modalUsers.map((u: any) => (
                    <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: '15px', padding: '10px', background: '#252525', borderRadius: '8px' }}>
                      <img 
                        src={u.avatar_url || defaultAvatarUrl} 
                        alt={u.pseudo} 
                        style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover', border: '1px solid #3498db' }}
                      />
                      <span style={{ fontWeight: 'bold', fontSize: '1rem', color: '#fff' }}>{u.pseudo}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ textAlign: 'center', color: '#aaa', fontStyle: 'italic', margin: '20px 0' }}>
                  {modalType === 'followers' ? "Aucun abonné pour le moment." : "Aucun abonnement pour le moment."}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="search-wrapper-container" style={{ maxWidth: '450px', margin: '40px auto' }}>
      <div className="search-back-row">
        <h3 style={{ margin: 0 }}>{isRegister ? "Créer un compte" : "Connexion"}</h3>
        <span onClick={onBackToHome} style={{ cursor: 'pointer' }}>← Accueil</span>
      </div>

      <div className="search-component-container" style={{ padding: '25px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          
          {isRegister && (
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem', color: 'var(--text-sub)' }}>Pseudo</label>
              <input 
                type="text" 
                required
                placeholder="Votre pseudo" 
                className="search-input-field" 
                style={{ width: '100%' }}
                value={pseudo}
                onChange={(e) => setPseudo(e.target.value)}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem', color: 'var(--text-sub)' }}>Email</label>
            <input 
              type="email" 
              required
              placeholder="exemple@mail.com" 
              className="search-input-field" 
              style={{ width: '100%' }}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem', color: 'var(--text-sub)' }}>Mot de passe</label>
            <input 
              type="password" 
              required
              placeholder="••••••••" 
              className="search-input-field" 
              style={{ width: '100%' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {message.text && (
            <div style={{ color: message.isError ? '#ff4757' : '#2ed573', fontSize: '0.85rem', marginTop: '5px', fontWeight: 600 }}>
              {message.text}
            </div>
          )}

          <button 
            type="submit" 
            disabled={loading}
            className="btn-filters-trigger" 
            style={{ width: '100%', background: 'var(--accent-color)', color: '#fff', border: 'none', padding: '12px', borderRadius: '20px', fontWeight: 'bold', marginTop: '10px' }}
          >
            {loading ? "Chargement..." : isRegister ? "S'inscrire" : "Se connecter"}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          {isRegister ? "Déjà un compte ?" : "Nouveau sur ScrumTeamSite ?"} 
          <span 
            onClick={() => { setIsRegister(!isRegister); setMessage({text:"", isError:false}); }} 
            style={{ color: 'var(--accent-color)', cursor: 'pointer', marginLeft: '5px', fontWeight: 600 }}
          >
            {isRegister ? "Se connecter" : "Créer un compte"}
          </span>
        </div>
      </div>
    </div>
  )
}