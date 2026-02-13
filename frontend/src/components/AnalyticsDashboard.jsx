import { useState, useEffect } from 'react'
import { HardDrive, Database, FileText, RefreshCw, Server, Cpu } from 'lucide-react'
import toast from 'react-hot-toast'
import { getStorageHealth, getHealth, getCollections } from '../api/client'

export default function AnalyticsDashboard() {
  const [storageHealth, setStorageHealth] = useState(null)
  const [health, setHealth] = useState(null)
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [sh, h, c] = await Promise.all([
        getStorageHealth().catch(() => null),
        getHealth().catch(() => null),
        getCollections().catch(() => ({ collections: [] })),
      ])
      setStorageHealth(sh)
      setHealth(h)
      setCollections(c.collections || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAll() }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
      </div>
    )
  }

  const totalDocs = collections.reduce((sum, c) => sum + (c.document_count || 0), 0)
  const diskPercent = storageHealth?.disk_usage_percent || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Analytics</h2>
          <p className="text-sm text-slate-400 mt-1">Storage health and system metrics</p>
        </div>
        <button onClick={fetchAll} className="p-2.5 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-400 hover:text-white">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Database}
          label="Collections"
          value={collections.length}
          sub={`Max ${health?.collections_count || 50}`}
          color="indigo"
        />
        <StatCard
          icon={FileText}
          label="Total Documents"
          value={totalDocs}
          sub="Across all collections"
          color="emerald"
        />
        <StatCard
          icon={HardDrive}
          label="Storage Used"
          value={`${storageHealth?.storage_size_mb || 0} MB`}
          sub={`${storageHealth?.disk_free_gb || 0} GB free`}
          color="amber"
        />
        <StatCard
          icon={Server}
          label="Status"
          value={health?.status === 'healthy' ? 'Healthy' : 'Offline'}
          sub={`v${health?.version || '?'}`}
          color={health?.status === 'healthy' ? 'green' : 'red'}
        />
      </div>

      {/* Disk Usage Bar */}
      {storageHealth && (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-3">Disk Usage</h3>
          <div className="w-full h-4 bg-[#0f172a] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${diskPercent > 80 ? 'bg-red-500' : diskPercent > 60 ? 'bg-amber-500' : 'bg-indigo-500'}`}
              style={{ width: `${Math.min(diskPercent, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-slate-400">{storageHealth.disk_used_gb} GB used</span>
            <span className="text-xs text-slate-400">{diskPercent}%</span>
            <span className="text-xs text-slate-400">{storageHealth.disk_total_gb} GB total</span>
          </div>
        </div>
      )}

      {/* Collections Breakdown */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
        <h3 className="text-sm font-medium text-slate-300 mb-4">Collections Breakdown</h3>
        {collections.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-6">No collections yet</p>
        ) : (
          <div className="space-y-3">
            {collections.map(coll => {
              const pct = totalDocs > 0 ? ((coll.document_count || 0) / totalDocs * 100) : 0
              return (
                <div key={coll.name} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${coll.backend === 'chroma' ? 'bg-emerald-400' : 'bg-blue-400'}`} />
                      <span className="text-sm text-slate-300">{coll.name}</span>
                      <span className="text-xs text-slate-500">{coll.backend}</span>
                    </div>
                    <span className="text-sm font-medium text-white">{coll.document_count || 0} docs</span>
                  </div>
                  <div className="w-full h-2 bg-[#0f172a] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${coll.backend === 'chroma' ? 'bg-emerald-500' : 'bg-blue-500'}`}
                      style={{ width: `${Math.max(pct, 1)}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Backend Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {storageHealth?.backends && Object.entries(storageHealth.backends).map(([name, info]) => (
          <div key={name} className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-medium text-slate-300">{name.toUpperCase()} Backend</h3>
              <span className={`ml-auto px-2 py-0.5 rounded text-xs ${info.exists ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                {info.exists ? 'Active' : 'Not initialized'}
              </span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-xs text-slate-500">Directory</span>
                <span className="text-xs text-slate-400 font-mono">{info.persist_directory}</span>
              </div>
              {info.index_type && (
                <div className="flex justify-between">
                  <span className="text-xs text-slate-500">Index Type</span>
                  <span className="text-xs text-slate-400">{info.index_type}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Embedding Models */}
      {health?.available_models && (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-300 mb-4">Available Embedding Models</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {health.available_models.map(model => (
              <div key={model.name} className="bg-[#0f172a] rounded-lg p-3 border border-[#334155]">
                <p className="text-sm font-mono text-indigo-400">{model.name}</p>
                <p className="text-xs text-slate-500 mt-1">{model.description}</p>
                <p className="text-xs text-slate-600 mt-1">{model.dimension}d</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, sub, color }) {
  const colorMap = {
    indigo: 'bg-indigo-500/10 text-indigo-400',
    emerald: 'bg-emerald-500/10 text-emerald-400',
    amber: 'bg-amber-500/10 text-amber-400',
    green: 'bg-green-500/10 text-green-400',
    red: 'bg-red-500/10 text-red-400',
  }

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colorMap[color]}`}>
          <Icon className="w-4.5 h-4.5" />
        </div>
        <span className="text-sm text-slate-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  )
}
