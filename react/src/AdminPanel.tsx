import { useState, useEffect, useCallback } from 'react'
import './AdminPanel.css'

const API_BASE = import.meta.env.VITE_API_BASE

type AdminTab = 'reports' | 'users'

interface FlaggedReview {
  id: number
  media_id: string
  title: string
  content: string
  flag_reason: string
  spoiler_flag: boolean
  is_featured: boolean
  created_at: string
  author: {
    id: number
    username: string
    avatar_url: string | null
    is_active: boolean
  }
}

interface AdminUser {
  id: number
  pseudo: string
  email: string
  role: string
  is_active: boolean
  created_at: string
  avatar_url: string | null
}

export default function AdminPanel() {
  const [tab, setTab] = useState<AdminTab>('reports')

  const [reports, setReports] = useState<FlaggedReview[]>([])
  const [reportTotal, setReportTotal] = useState(0)
  const [loadingReports, setLoadingReports] = useState(false)

  const [users, setUsers] = useState<AdminUser[]>([])
  const [userTotal, setUserTotal] = useState(0)
  const [userSearch, setUserSearch] = useState("")
  const [loadingUsers, setLoadingUsers] = useState(false)

  const authHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem("token")}`,
    "Content-Type": "application/json",
  })

  const loadReports = useCallback(async () => {
    setLoadingReports(true)
    try {
      const res = await fetch(`${API_BASE}/admin/flagged-reviews?limit=50`, { headers: authHeaders() })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setReports(data.reviews)
      setReportTotal(data.total)
    } catch {
      setReports([])
    } finally {
      setLoadingReports(false)
    }
  }, [])

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true)
    try {
      const url = userSearch
        ? `${API_BASE}/admin/users?q=${encodeURIComponent(userSearch)}&limit=50`
        : `${API_BASE}/admin/users?limit=50`
      const res = await fetch(url, { headers: authHeaders() })
      if (!res.ok) throw new Error()
      const data = await res.json()
      setUsers(data.users)
      setUserTotal(data.total)
    } catch {
      setUsers([])
    } finally {
      setLoadingUsers(false)
    }
  }, [userSearch])

  useEffect(() => { if (tab === 'reports') loadReports() }, [tab, loadReports])
  useEffect(() => { if (tab === 'users') loadUsers() }, [tab, loadUsers])

  const handleUnflag = async (reviewId: number) => {
    await fetch(`${API_BASE}/admin/reviews/${reviewId}/unflag`, { method: "POST", headers: authHeaders() })
    loadReports()
  }

  const handleDeleteReview = async (reviewId: number) => {
    if (!confirm("Supprimer définitivement cette critique ?")) return
    await fetch(`${API_BASE}/admin/reviews/${reviewId}`, { method: "DELETE", headers: authHeaders() })
    loadReports()
  }

  const handleToggleFeature = async (reviewId: number) => {
    await fetch(`${API_BASE}/admin/reviews/${reviewId}/feature`, { method: "POST", headers: authHeaders() })
    loadReports()
  }

  const handleBanToggle = async (user: AdminUser) => {
    const action = user.is_active ? "ban" : "unban"
    const label = user.is_active ? "bannir" : "réactiver"
    if (!confirm(`Voulez-vous ${label} « ${user.pseudo} » ?`)) return
    await fetch(`${API_BASE}/admin/users/${user.id}/${action}`, { method: "POST", headers: authHeaders() })
    loadUsers()
  }

  return (
    <div className="admin-panel">
      <h2 className="admin-title">Panneau d'administration</h2>

      <div className="admin-tabs">
        <button
          className={`admin-tab-btn ${tab === 'reports' ? 'active' : ''}`}
          onClick={() => setTab('reports')}
        >
           Signalements {reportTotal > 0 && <span className="admin-badge">{reportTotal}</span>}
        </button>
        <button
          className={`admin-tab-btn ${tab === 'users' ? 'active' : ''}`}
          onClick={() => setTab('users')}
        >
           Utilisateurs {userTotal > 0 && <span className="admin-badge-muted">{userTotal}</span>}
        </button>
      </div>

      {/* ── Onglet Signalements ── */}
      {tab === 'reports' && (
        <div className="admin-section">
          {loadingReports && <p className="admin-loading">Chargement...</p>}
          {!loadingReports && reports.length === 0 && (
            <p className="admin-empty">Aucune critique signalée.</p>
          )}
          {reports.map(rev => (
            <div key={rev.id} className="admin-report-card">
              <div className="admin-report-meta">
                <span className="admin-report-author">
                  {rev.author.avatar_url && (
                    <img src={rev.author.avatar_url} alt="" className="admin-avatar-sm" />
                  )}
                  <strong>{rev.author.username}</strong>
                  {!rev.author.is_active && <span className="admin-banned-tag">banni</span>}
                </span>
                <span className="admin-report-date">{new Date(rev.created_at).toLocaleDateString('fr-FR')}</span>
              </div>

              <p className="admin-report-title">{rev.title || "(sans titre)"}</p>
              <p className="admin-report-content">{rev.content}</p>

              <div className="admin-report-reason">
                <strong>Raison du signalement :</strong> {rev.flag_reason || "Non précisée"}
                {rev.spoiler_flag && <span className="admin-spoiler-tag"> · ⚠️ Spoiler</span>}
              </div>

              <div className="admin-report-actions">
                <button className="btn-admin-sm btn-unflag" onClick={() => handleUnflag(rev.id)}>
                  ✅ Retirer le signalement
                </button>
                <button
                  className="btn-admin-sm btn-feature"
                  onClick={() => handleToggleFeature(rev.id)}
                >
                  {rev.is_featured ? "💔 Retirer coup de cœur" : "💖 Mettre en avant"}
                </button>
                <button className="btn-admin-sm btn-delete" onClick={() => handleDeleteReview(rev.id)}>
                  🗑 Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Onglet Utilisateurs ── */}
      {tab === 'users' && (
        <div className="admin-section">
          <div className="admin-user-search">
            <input
              type="text"
              placeholder="Rechercher par pseudo..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              className="admin-search-input"
            />
          </div>

          {loadingUsers && <p className="admin-loading">Chargement...</p>}
          {!loadingUsers && users.length === 0 && <p className="admin-empty">Aucun utilisateur trouvé.</p>}

          <table className="admin-users-table">
            <thead>
              <tr>
                <th>Pseudo</th>
                <th>Email</th>
                <th>Rôle</th>
                <th>Statut</th>
                <th>Membre depuis</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className={!u.is_active ? "admin-user-banned" : ""}>
                  <td>
                    <div className="admin-user-name">
                      {u.avatar_url && <img src={u.avatar_url} alt="" className="admin-avatar-sm" />}
                      {u.pseudo}
                    </div>
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`admin-role-tag role-${u.role}`}>{u.role}</span>
                  </td>
                  <td>
                    {u.is_active
                      ? <span className="admin-status-active">Actif</span>
                      : <span className="admin-status-banned">Banni</span>}
                  </td>
                  <td>{new Date(u.created_at).toLocaleDateString('fr-FR')}</td>
                  <td>
                    {u.role !== 'admin' && (
                      <button
                        className={`btn-admin-sm ${u.is_active ? 'btn-ban' : 'btn-unban'}`}
                        onClick={() => handleBanToggle(u)}
                      >
                        {u.is_active ? "🚫 Bannir" : "✅ Réactiver"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
