import { useState, useEffect, useRef } from 'react'
import { Upload, Trash2, FileText, ChevronLeft, ChevronRight, RefreshCw, Eye, X, File, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { getDocuments, uploadFile, ingestDocuments, deleteDocument, bulkDeleteDocuments } from '../api/client'

export default function DocumentBrowser({ collection, onBack }) {
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(20)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(new Set())
  const [inspecting, setInspecting] = useState(null)
  const [showUpload, setShowUpload] = useState(false)
  const [showIngest, setShowIngest] = useState(false)
  const fileRef = useRef()

  // Ingest form
  const [ingestText, setIngestText] = useState('')
  const [ingestMeta, setIngestMeta] = useState('{}')

  const fetchDocs = async () => {
    if (!collection) return
    setLoading(true)
    try {
      const data = await getDocuments(collection, { page, limit })
      setDocuments(data.documents || [])
      setTotal(data.total || 0)
    } catch {
      toast.error('Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [collection, page])

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('chunk_strategy', 'recursive')
    formData.append('chunk_size', '1000')
    formData.append('chunk_overlap', '200')

    try {
      const result = await uploadFile(collection, formData)
      toast.success(`${result.chunks_created} chunks created from "${file.name}"`)
      setShowUpload(false)
      fetchDocs()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed')
    }
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleIngest = async () => {
    if (!ingestText.trim()) return toast.error('Text is required')
    let meta = {}
    try {
      meta = JSON.parse(ingestMeta)
    } catch {
      return toast.error('Invalid metadata JSON')
    }

    try {
      const result = await ingestDocuments(collection, {
        documents: [{ text: ingestText, metadata: meta }],
        on_conflict: 'error',
      })
      toast.success(`${result.ingested} document(s) ingested`)
      setShowIngest(false)
      setIngestText('')
      setIngestMeta('{}')
      fetchDocs()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Ingestion failed')
    }
  }

  const handleDelete = async (docId) => {
    try {
      await deleteDocument(collection, docId)
      toast.success('Document deleted')
      fetchDocs()
    } catch {
      toast.error('Delete failed')
    }
  }

  const handleBulkDelete = async () => {
    if (selected.size === 0) return
    if (!confirm(`Delete ${selected.size} documents?`)) return
    try {
      await bulkDeleteDocuments(collection, [...selected])
      toast.success(`${selected.size} documents deleted`)
      setSelected(new Set())
      fetchDocs()
    } catch {
      toast.error('Bulk delete failed')
    }
  }

  const totalPages = Math.ceil(total / limit)

  if (!collection) {
    return (
      <div className="text-center py-20">
        <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-slate-300">No collection selected</h3>
        <p className="text-sm text-slate-500 mt-1">Select a collection from the Collections tab first</p>
        <button onClick={onBack} className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm">
          Go to Collections
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-400 hover:text-white">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-white">{collection}</h2>
            <p className="text-sm text-slate-400">{total} documents</p>
          </div>
        </div>
        <div className="flex gap-2">
          {selected.size > 0 && (
            <button onClick={handleBulkDelete} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20">
              <Trash2 className="w-3.5 h-3.5" /> Delete ({selected.size})
            </button>
          )}
          <button onClick={fetchDocs} className="p-2.5 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-400 hover:text-white">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => setShowIngest(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#1e293b] border border-[#334155] text-slate-300 text-sm hover:border-indigo-500/40">
            <Plus className="w-4 h-4" /> Add Text
          </button>
          <button onClick={() => setShowUpload(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium">
            <Upload className="w-4 h-4" /> Upload File
          </button>
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowUpload(false)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">Upload File</h3>
            <p className="text-sm text-slate-400 mb-4">Supported: PDF, DOCX, TXT, MD. Auto-chunked and embedded.</p>
            <div
              className="border-2 border-dashed border-[#334155] rounded-xl p-8 text-center hover:border-indigo-500/40 transition-colors cursor-pointer"
              onClick={() => fileRef.current?.click()}
            >
              <File className="w-10 h-10 text-slate-500 mx-auto mb-3" />
              <p className="text-sm text-slate-300">Click to select a file</p>
              <p className="text-xs text-slate-500 mt-1">Max 50MB</p>
            </div>
            <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" className="hidden" onChange={handleFileUpload} />
            <button onClick={() => setShowUpload(false)} className="w-full mt-4 px-4 py-2.5 rounded-lg border border-[#334155] text-slate-300 text-sm hover:bg-[#334155]">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Ingest Text Modal */}
      {showIngest && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setShowIngest(false)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-white mb-4">Add Document</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Text *</label>
                <textarea
                  value={ingestText}
                  onChange={e => setIngestText(e.target.value)}
                  rows={6}
                  placeholder="Enter document text..."
                  className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Metadata (JSON)</label>
                <textarea
                  value={ingestMeta}
                  onChange={e => setIngestMeta(e.target.value)}
                  rows={3}
                  placeholder='{"category": "legal", "source": "contract.pdf"}'
                  className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-sm font-mono focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setShowIngest(false)} className="flex-1 px-4 py-2.5 rounded-lg border border-[#334155] text-slate-300 text-sm hover:bg-[#334155]">Cancel</button>
                <button onClick={handleIngest} className="flex-1 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium">Ingest</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document Inspector */}
      {inspecting && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setInspecting(null)}>
          <div className="bg-[#1e293b] border border-[#334155] rounded-2xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Document Inspector</h3>
              <button onClick={() => setInspecting(null)} className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-[#334155]">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-1">ID</p>
                <p className="text-sm font-mono text-slate-300 bg-[#0f172a] px-3 py-2 rounded-lg break-all">{inspecting.id}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Text ({inspecting.char_count || inspecting.text?.length || 0} chars)</p>
                <div className="text-sm text-slate-300 bg-[#0f172a] px-3 py-2 rounded-lg max-h-48 overflow-y-auto whitespace-pre-wrap">{inspecting.text}</div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Metadata</p>
                <pre className="text-sm text-slate-300 bg-[#0f172a] px-3 py-2 rounded-lg overflow-x-auto">{JSON.stringify(inspecting.metadata, null, 2)}</pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-20">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-300">No documents</h3>
          <p className="text-sm text-slate-500 mt-1">Upload a file or add text to get started</p>
        </div>
      ) : (
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#334155]">
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selected.size === documents.length && documents.length > 0}
                    onChange={e => {
                      if (e.target.checked) setSelected(new Set(documents.map(d => d.id)))
                      else setSelected(new Set())
                    }}
                    className="rounded border-[#334155]"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Text Preview</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Chars</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">Metadata</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map(doc => (
                <tr key={doc.id} className="border-b border-[#334155]/50 hover:bg-[#334155]/20">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(doc.id)}
                      onChange={e => {
                        const next = new Set(selected)
                        if (e.target.checked) next.add(doc.id)
                        else next.delete(doc.id)
                        setSelected(next)
                      }}
                      className="rounded border-[#334155]"
                    />
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-slate-400 max-w-[120px] truncate">{doc.id}</td>
                  <td className="px-4 py-3 text-sm text-slate-300 max-w-[300px] truncate">{doc.text}</td>
                  <td className="px-4 py-3 text-xs text-slate-400">{doc.char_count || doc.text?.length || 0}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(doc.metadata || {}).filter(([k]) => !k.startsWith('_')).slice(0, 3).map(([k, v]) => (
                        <span key={k} className="px-1.5 py-0.5 rounded text-xs bg-[#334155] text-slate-300">
                          {k}: {String(v).slice(0, 20)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => setInspecting(doc)} className="p-1.5 rounded-md text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10">
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(doc.id)} className="p-1.5 rounded-md text-slate-400 hover:text-red-400 hover:bg-red-500/10">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-[#334155]">
              <p className="text-xs text-slate-400">Page {page} of {totalPages} ({total} total)</p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-md bg-[#334155] text-slate-300 disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded-md bg-[#334155] text-slate-300 disabled:opacity-30"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
