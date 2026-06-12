import { useState } from 'react'
import './Recherche.css'
import defaultAvatarUrl from './assets/default-avatar.svg'

const API_BASE = import.meta.env.VITE_API_BASE

export default function RechercheUsers() {
  const [query, setQuery] = useState("")
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const searchUsers = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/users/search?username=${query}`)
      const data = await res.json()
      setUsers(data.results || data)
    } catch (err) {
      console.error("Erreur recherche utilisateur:", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-wrapper-container">
      <h2>Rechercher des utilisateurs</h2>
      <form onSubmit={searchUsers} className="search-component-container">
        <input 
          type="text" 
          placeholder="Pseudo de l'utilisateur..." 
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
        />
        <button type="submit" disabled={loading}>
          {loading ? "Recherche..." : "Rechercher"}
        </button>
      </form>
      
      <div className="user-results-grid">
        {users.map(user => (
          <div key={user.id} className="user-card">
            <img src={user.avatar || defaultAvatarUrl} alt={user.username} />
            <h3>{user.username}</h3>
            <button onClick={() => alert(`Ouvrir profil de ${user.username}`)}>
              Voir profil
            </button>
          </div>
        ))}
      </div>
      
    </div>
  )
}