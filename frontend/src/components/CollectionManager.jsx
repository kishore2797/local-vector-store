import { useState, useEffect } from 'react'
import { Plus, Trash2, Database, HardDrive, RefreshCw, Search, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { getCollections, createCollection, deleteCollection } from '../api/client'

export default function CollectionManager({ onSelectCollection }) {
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [form, setForm] = useState({
    name: '',
    description: '',
    backend: 'chroma',
    embedding_model: 'all-MiniLM-L6-v2',
  })

  const fetchCollections = async () => {
    setLoading(true)
    try {
      const data = await getCollections({ search: searchQuery || undefined })
      setCollections(data.collections || [])
    } catch (err) {
      toast.error('Failed to load collections')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCollections() }, [searchQuery])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) return toast.error('Collection name is required')

    try {
      await createCollection(form)
      toast.success(`Collection "${form.name}" created`)
      setShowCreate(false)
      setForm({ name: '', description: '', backend: 'chroma', embedding_model: 'all-MiniLM-L6-v2' })
      fetchCollections()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create collection')
    }
  }

  const handleDelete = async (name) => {
    if (!confirm(`Delete collection "${name}"? This cannot be undone.`)) return
    try {
      await deleteCollection(name)
      toast.success(`Collection "${name}" deleted`)
      fetchCollections()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete collection')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Collections</h2>
          <p className="text-sm text-slate-400 mt-1">Manage your vector store collections</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchCollections} className="p-2.5 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-400 hover:text-white transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors">
            <Plus className="w-4 h-4" /> New Collection
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search collections..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[#1e293b] border border-[#334155] text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
        />
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">Create Collection</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="my-documents"
                  pattern="^[a-zA-Z0-9_-]+$"
                  className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:outline-none focus:border-indigo-500"
                />
                <p className="text-xs text-slate-500 mt-1">Letters, numbers, hyphens, underscores only</p>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Description</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  placeholder="Optional description..."
                  className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Backend</label>
                  <select
                    value={form.backend}
                    onChange={e => setForm({ ...form, backend: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="chroma">ChromaDB</option>
                    <option value="faiss">FAISS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Embedding Model</label>
                  <select
                    value={form.embedding_model}
                    onChange={e => setForm({ ...form, embedding_model: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384d)</option>
                    <option value="all-MiniLM-L12-v2">all-MiniLM-L12-v2 (384d)</option>
                    <option value="all-mpnet-base-v2">all-mpnet-base-v2 (768d)</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreate(false)} className="flex-1 px-4 py-2.5 rounded-lg border border-[#334155] text-slate-300 text-sm hover:bg-[#334155] transition-colors">
                  Cancel
                </button>
                <button type="submit" className="flex-1 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Collection Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : collections.length === 0 ? (
        <div className="text-center py-20">
          <Database className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300">No collections yet</h3>
          <p className="text-sm text-slate-500 mt-1">Create your first vector collection to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {collections.map(coll => (
            <div
              key={coll.name}
              className="group bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-indigo-500/40 transition-all cursor-pointer"
              onClick={() => onSelectCollection(coll.name)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${coll.backend === 'chroma' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>
                    {coll.backend === 'chroma' ? <Database className="w-4 h-4" /> : <HardDrive className="w-4 h-4" />}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white text-sm">{coll.name}</h3>
                    <span className="text-xs text-slate-500">{coll.backend.toUpperCase()}</span>
                  </div>
                </div>
                <button
                  onClick={e => { e.stopPropagation(); handleDelete(coll.name) }}
                  className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {coll.description && (
                <p className="text-xs text-slate-400 mb-3 line-clamp-2">{coll.description}</p>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-[#334155]">
                <div className="flex gap-4">
                  <div>
                    <p className="text-lg font-bold text-white">{coll.document_count || 0}</p>
                    <p className="text-xs text-slate-500">Documents</p>
                  </div>
                  <div>
                    <p className="text-xs font-mono text-slate-400 mt-1">{coll.embedding_model}</p>
                    <p className="text-xs text-slate-500">Model</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
