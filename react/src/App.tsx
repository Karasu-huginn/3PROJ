import { useState } from 'react'
import Home from './Home'
import Recherche from './Recherche'
import RechercheUsers from './RechercheUsers'
import Auth from './auth'
import Bibliotheque from './Bibliotheque'
import './App.css'

function App() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [currentTab, setCurrentTab] = useState<'accueil' | 'recherche' | 'recherche-users' | 'profil' | 'bibliotheque'>('accueil')

  return (
    <div className={`app-container ${theme}`}>
      
      <header className="main-header">
        <div className="header-left">
          <h1 className="header-logo" onClick={() => setCurrentTab('accueil')} style={{ cursor: 'pointer' }}>
            Scrum<span>TeamSite</span>
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
        {currentTab === 'recherche' && <Recherche />}
        {currentTab === 'recherche-users' && <RechercheUsers />}
        
        {currentTab === 'profil' && (
          <Auth onBackToHome={() => setCurrentTab('accueil')} />
        )}
        {currentTab === 'bibliotheque' && (
          <Bibliotheque onGoToLogin={() => setCurrentTab('profil')} />
        )}
      </main>

      <footer className="main-footer">
        <p>© 2026 ScrumTeamSite — Réseau Social Manga</p>
      </footer>
    </div>
  )
}

export default App