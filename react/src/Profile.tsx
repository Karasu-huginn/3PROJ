import { useState, useEffect } from 'react'
import defaultAvatarUrl from './assets/default-avatar.svg'

const API_BASE = import.meta.env.VITE_API_BASE

export default function Profile({ userId }: { userId: number }) {
  const [profile, setProfile] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/users/${userId}/profile`)
      .then(res => res.json())
      .then(data => {
        setProfile(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Erreur chargement profil:", err)
        setLoading(false)
      })
  }, [userId])

  const toggleFollow = async () => {
    const token = localStorage.getItem("token")

    if (!token) {
      alert("Vous devez être connecté pour vous abonner à quelqu'un.")
      return
    }

    try {
      const res = await fetch(`${API_BASE}/users/${userId}/follow`, { 
        method: 'POST',
        headers: {
          "Authorization": `Bearer ${token}` 
        }
      })

      if (res.ok) {
        const newData = await res.json()
        setProfile((prev: any) => ({
          ...prev,
          is_followed_by_viewer: newData.following,
          follower_count: newData.follower_count
        }))
      } else {
        console.error("Erreur lors de l'abonnement :", await res.text())
      }
    } catch (err) {
      console.error("Erreur réseau :", err)
    }
  }

  if (loading) return <div>Chargement du profil...</div>
  if (!profile) return <div>Profil introuvable.</div>

  return (
    <div className="profile-container">
      <img 
        src={profile.avatar_url || defaultAvatarUrl} 
        alt={profile.pseudo}
        onError={(e) => { 
          if (e.currentTarget.src !== defaultAvatarUrl) {
            e.currentTarget.src = defaultAvatarUrl; 
          }
        }} 
      />
      <h2>{profile.pseudo}</h2>
      <p>{profile.bio}</p>
      
      <div className="stats">
        <span>{profile.follower_count} Abonnés</span>
        <span>{profile.following_count} Abonnements</span>
      </div>

      <button onClick={toggleFollow}>
        {profile.is_followed_by_viewer ? "Se désabonner" : "S'abonner"}
      </button>
    </div>
  )
}