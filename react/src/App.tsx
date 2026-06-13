import { useState, useEffect } from 'react'
import Home from './Home'
import Recherche from './Recherche'
import RechercheUsers from './RechercheUsers'
import Auth from './auth'
import Bibliotheque from './Bibliotheque'
import AdminPanel from './AdminPanel'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE

type Tab = 'accueil' | 'recherche' | 'recherche-users' | 'profil' | 'bibliotheque' | 'admin'

interface CurrentUser {
  id: number
  pseudo: string
  role: string
}

function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [currentTab, setCurrentTab] = useState<Tab>('accueil')
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null)

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem("token")
    if (!token) { setCurrentUser(null); return }
    try {
      const res = await fetch(`${API_BASE}/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) { setCurrentUser(null); return }
      const data = await res.json()
      setCurrentUser({ id: data.id, pseudo: data.pseudo, role: data.role })
    } catch {
      setCurrentUser(null)
    }
  }

  useEffect(() => {
    fetchCurrentUser()
    // Re-sync après connexion / déconnexion en écoutant les changements de localStorage
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") fetchCurrentUser()
    }
    window.addEventListener("storage", onStorage)
    return () => window.removeEventListener("storage", onStorage)
  }, [])

  const isAdmin = currentUser?.role === "admin"

  return (
    <div className={`app-container ${theme}`}>
      <header className="main-header">
        <div className="header-left">
          <h1 className="header-logo" onClick={() => setCurrentTab('accueil')} style={{ cursor: 'pointer' }}>
            Scru<span>manga</span>
          </h1>
          <nav className="header-nav">
            <span
              className={`nav-link ${currentTab === 'accueil' ? 'active' : 'muted'}`}
              onClick={() => setCurrentTab('accueil')}
            >
              Accueil
            </span>
            <span
              className={`nav-link ${currentTab === 'recherche' ? 'active' : 'muted'}`}
              onClick={() => setCurrentTab('recherche')}
            >
              Découvrir
            </span>
            <span
              className={`nav-link ${currentTab === 'bibliotheque' ? 'active' : 'muted'}`}
              onClick={() => setCurrentTab('bibliotheque')}
            >
              Bibliothèque
            </span>
            {isAdmin && (
              <span
                className={`nav-link nav-link-admin ${currentTab === 'admin' ? 'active' : 'muted'}`}
                onClick={() => setCurrentTab('admin')}
              >
                Admin
              </span>
            )}
          </nav>
        </div>

        <div className="header-right-actions" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={() => setCurrentTab('recherche-users')}
            className="theme-toggle-btn"
            style={currentTab === 'recherche-users' ? { borderColor: 'var(--accent-color)', color: 'var(--accent-color)' } : {}}
          >
            🔍
          </button>

          <button
            onClick={() => console.log("Voir les favoris")}
            className="theme-toggle-btn"
          >
            ❤️
          </button>

          <button
            onClick={() => setCurrentTab('profil')}
            className="theme-toggle-btn"
            style={currentTab === 'profil' ? { borderColor: 'var(--accent-color)', color: 'var(--accent-color)' } : {}}
          >
            👤
          </button>

          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="theme-toggle-btn"
          >
            {theme === 'dark' ? '☀️ Mode Clair' : '🌙 Mode Sombre'}
          </button>
        </div>
      </header>

      <main className="main-content-wrapper">
        {currentTab === 'accueil' && <Home />}
        {currentTab === 'recherche' && (
          <Recherche
            currentUserRole={currentUser?.role}
            currentUserId={currentUser?.id}
          />
        )}
        {currentTab === 'recherche-users' && <RechercheUsers />}
        {currentTab === 'profil' && (
          <Auth
            onBackToHome={() => setCurrentTab('accueil')}
            onAuthChange={fetchCurrentUser}
          />
        )}
        {currentTab === 'bibliotheque' && (
          <Bibliotheque
            onGoToLogin={() => setCurrentTab('profil')}
            currentUserRole={currentUser?.role}
            currentUserId={currentUser?.id}
          />
        )}
        {currentTab === 'admin' && isAdmin && <AdminPanel />}
      </main>

      <footer className="main-footer">
        <p>© 2026 Scrumanga — Réseau Social Manga</p>
      </footer>
    </div>
  )
}

export default App
