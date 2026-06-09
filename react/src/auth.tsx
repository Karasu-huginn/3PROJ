import { useState, useEffect } from 'react'
import './Home.css'

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

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (token) {
      fetchUserProfile(token)
    }
  }, [])

  const fetchUserProfile = (token: string) => {
    fetch(`${API_BASE}/auth/profile`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error()
        return res.json()
      })
      .then(data => setUser(data))
      .catch(() => logout())
  }

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
      <div className="search-wrapper-container" style={{ maxWidth: '600px', margin: '40px auto' }}>
        <div className="search-back-row">
          <h3 style={{ margin: 0 }}>Mon Profil</h3>
          <span onClick={onBackToHome} style={{ cursor: 'pointer' }}>← Retour à l'accueil</span>
        </div>

        <div className="search-component-container" style={{ textAlign: 'center', padding: '30px' }}>
          <div style={{ marginBottom: '20px' }}>
            <img 
              src={user.avatar_url || "https://via.placeholder.com/100?text=👤"} 
              alt="Avatar" 
              style={{ width: '100px', height: '100px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--accent-color)' }}
            />
          </div>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '5px' }}>{user.pseudo}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '15px' }}>{user.email}</p>
          
          <div style={{ background: 'var(--bg-inner)', padding: '15px', borderRadius: '8px', marginBottom: '20px', textAlign: 'left' }}>
            <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '5px' }}>Bio :</strong>
            <p style={{ color: 'var(--text-sub)', margin: 0, fontSize: '0.95rem' }}>
              {user.bio || "Aucune biographie rédigée pour le moment."}
            </p>
          </div>

          <button 
            onClick={logout} 
            className="btn-filters-trigger" 
            style={{ width: '100%', background: '#ff4757', color: '#fff', border: 'none', padding: '12px', borderRadius: '20px' }}
          >
            🚪 Se déconnecter
          </button>
        </div>
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