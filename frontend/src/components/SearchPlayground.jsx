import { useState } from 'react'
import { Search, Zap, BookOpen, GitCompare, SlidersHorizontal, Clock, Copy, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { searchCollection, compareSearch } from '../api/client'

export default function SearchPlayground({ collection }) {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState('hybrid')
  const [topK, setTopK] = useState(5)
  const [vectorWeight, setVectorWeight] = useState(0.7)
  const [keywordWeight, setKeywordWeight] = useState(0.3)
  const [fusionMethod, setFusionMethod] = useState('weighted_sum')
  const [highlight, setHighlight] = useState(true)
  const [filterJson, setFilterJson] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const [results, setResults] = useState(null)
  const [compareResults, setCompareResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [queryHistory, setQueryHistory] = useState([])

  const handleSearch = async () => {
    if (!collection) return toast.error('Select a collection first')
    if (!query.trim()) return toast.error('Enter a search query')

    setLoading(true)
    setCompareResults(null)

    let filters = undefined
    if (filterJson.trim()) {
      try {
        filters = JSON.parse(filterJson)
      } catch {
        setLoading(false)
        return toast.error('Invalid filter JSON')
      }
    }

    try {
      const data = await searchCollection(collection, {
        query,
        top_k: topK,
        search_type: searchType,
        filters,
        highlight,
        hybrid_config: searchType === 'hybrid' ? {
          vector_weight: vectorWeight,
          keyword_weight: keywordWeight,
          fusion_method: fusionMethod,
        } : undefined,
      })
      setResults(data)
      setQueryHistory(prev => [{ query, type: searchType, time: new Date().toLocaleTimeString(), results: data.total_results }, ...prev.slice(0, 19)])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!collection) return toast.error('Select a collection first')
    if (!query.trim()) return toast.error('Enter a search query')

    setLoading(true)
    setResults(null)

    let filters = undefined
    if (filterJson.trim()) {
      try { filters = JSON.parse(filterJson) } catch { setLoading(false); return toast.error('Invalid filter JSON') }
    }

    try {
      const data = await compareSearch(collection, {
        query,
        top_k: topK,
        filters,
        highlight: true,
        hybrid_config: {
          vector_weight: vectorWeight,
          keyword_weight: keywordWeight,
          fusion_method: fusionMethod,
        },
      })
      setCompareResults(data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Compare failed')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSearch()
  }

  if (!collection) {
    return (
      <div className="text-center py-20">
        <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-slate-300">No collection selected</h3>
        <p className="text-sm text-slate-500 mt-1">Select a collection from the Collections tab to start searching</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
        <div className="flex gap-3 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter your search query... (Ctrl+Enter to search)"
              className="w-full pl-10 pr-4 py-3 rounded-lg bg-[#0f172a] border border-[#334155] text-white placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50 flex items-center gap-2"
          >
            <Zap className="w-4 h-4" /> Search
          </button>
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-4 py-3 rounded-lg bg-[#334155] hover:bg-[#475569] text-slate-300 text-sm flex items-center gap-2"
            title="Compare all search types"
          >
            <GitCompare className="w-4 h-4" /> Compare
          </button>
        </div>

        {/* Controls Row */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Type:</label>
            <div className="flex rounded-lg overflow-hidden border border-[#334155]">
              {['vector', 'keyword', 'hybrid'].map(type => (
                <button
                  key={type}
                  onClick={() => setSearchType(type)}
                  className={`px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                    searchType === type ? 'bg-indigo-600 text-white' : 'bg-[#0f172a] text-slate-400 hover:text-white'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400">Top K:</label>
            <input
              type="number"
              value={topK}
              onChange={e => setTopK(parseInt(e.target.value) || 5)}
              min={1} max={100}
              className="w-16 px-2 py-1.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-xs text-center focus:outline-none focus:border-indigo-500"
            />
          </div>

          {searchType === 'hybrid' && (
            <>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Vector:</label>
                <input
                  type="range" min="0" max="1" step="0.1"
                  value={vectorWeight}
                  onChange={e => { setVectorWeight(parseFloat(e.target.value)); setKeywordWeight(round(1 - parseFloat(e.target.value))) }}
                  className="w-20 accent-indigo-500"
                />
                <span className="text-xs text-indigo-400 font-mono w-8">{vectorWeight}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Keyword:</label>
                <span className="text-xs text-amber-400 font-mono w-8">{keywordWeight}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Fusion:</label>
                <select
                  value={fusionMethod}
                  onChange={e => setFusionMethod(e.target.value)}
                  className="px-2 py-1.5 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="weighted_sum">Weighted Sum</option>
                  <option value="rrf">RRF</option>
                  <option value="relative_score">Relative Score</option>
                </select>
              </div>
            </>
          )}

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs ${showFilters ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'bg-[#0f172a] text-slate-400 border border-[#334155]'}`}
          >
            <SlidersHorizontal className="w-3 h-3" /> Filters
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-[#334155]">
            <label className="block text-xs text-slate-400 mb-1">Metadata Filter (JSON)</label>
            <textarea
              value={filterJson}
              onChange={e => setFilterJson(e.target.value)}
              rows={3}
              placeholder='{"category": {"$eq": "legal"}, "date": {"$gte": "2024-01-01"}}'
              className="w-full px-3 py-2 rounded-lg bg-[#0f172a] border border-[#334155] text-white text-xs font-mono focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>
        )}
      </div>

      {/* Results */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {/* Single Search Results */}
          {results && !loading && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-300">
                  {results.total_results} results · {results.search_type} · {results.processing_time_ms}ms
                </h3>
              </div>
              {results.results.map((r, i) => (
                <ResultCard key={r.id} result={r} rank={i + 1} searchType={results.search_type} />
              ))}
              {results.total_results === 0 && (
                <p className="text-center text-slate-500 py-10">No results found</p>
              )}
            </div>
          )}

          {/* Compare Results */}
          {compareResults && !loading && (
            <div className="space-y-6">
              {/* Overlap Stats */}
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(compareResults.overlap_analysis || {}).map(([key, val]) => (
                  <div key={key} className="bg-[#1e293b] border border-[#334155] rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-white">{val}</p>
                    <p className="text-xs text-slate-400">{key.replace(/_/g, ' ')}</p>
                  </div>
                ))}
              </div>

              {/* Three Column Compare */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {[
                  { label: 'Vector', color: 'indigo', data: compareResults.vector_results },
                  { label: 'Keyword', color: 'amber', data: compareResults.keyword_results },
                  { label: 'Hybrid', color: 'emerald', data: compareResults.hybrid_results },
                ].map(({ label, color, data }) => (
                  <div key={label} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className={`text-sm font-semibold text-${color}-400`}>{label}</h4>
                      <span className="text-xs text-slate-500">{data.processing_time_ms}ms</span>
                    </div>
                    {data.results.map((r, i) => (
                      <div key={r.id} className="bg-[#1e293b] border border-[#334155] rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-slate-500">#{i + 1}</span>
                          <span className={`text-xs font-mono text-${color}-400`}>{r.score?.toFixed(4)}</span>
                        </div>
                        <p className="text-xs text-slate-300 line-clamp-3">{r.text}</p>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Query History Sidebar */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" /> Query History
          </h3>
          {queryHistory.length === 0 ? (
            <p className="text-xs text-slate-500">No queries yet</p>
          ) : (
            queryHistory.map((h, i) => (
              <button
                key={i}
                onClick={() => { setQuery(h.query); setSearchType(h.type) }}
                className="w-full text-left bg-[#1e293b] border border-[#334155] rounded-lg p-3 hover:border-indigo-500/30 transition-colors"
              >
                <p className="text-xs text-slate-300 truncate">{h.query}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-slate-500">{h.type}</span>
                  <span className="text-xs text-slate-600">·</span>
                  <span className="text-xs text-slate-500">{h.results} results</span>
                  <span className="text-xs text-slate-600">·</span>
                  <span className="text-xs text-slate-500">{h.time}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function round(n) {
  return Math.round(n * 10) / 10
}

function ResultCard({ result, rank, searchType }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 hover:border-indigo-500/20 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold flex items-center justify-center">
            {rank}
          </span>
          <div className="flex gap-2">
            {result.vector_score != null && (
              <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-400">
                vec: {result.vector_score?.toFixed(4)}
              </span>
            )}
            {result.keyword_score != null && result.keyword_score > 0 && (
              <span className="px-2 py-0.5 rounded text-xs bg-amber-500/10 text-amber-400">
                kw: {result.keyword_score?.toFixed(4)}
              </span>
            )}
            {result.combined_score != null && (
              <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400">
                combined: {result.combined_score?.toFixed(4)}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-white">{result.score?.toFixed(4)}</span>
          <button
            onClick={() => { navigator.clipboard.writeText(result.text); toast.success('Copied') }}
            className="p-1 rounded text-slate-500 hover:text-white"
          >
            <Copy className="w-3 h-3" />
          </button>
        </div>
      </div>

      <div
        className={`text-sm text-slate-300 ${expanded ? '' : 'line-clamp-3'} cursor-pointer`}
        onClick={() => setExpanded(!expanded)}
        dangerouslySetInnerHTML={{
          __html: result.highlighted_text || result.text
        }}
      />

      {/* Metadata badges */}
      {result.metadata && Object.keys(result.metadata).filter(k => !k.startsWith('_')).length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-[#334155]/50">
          {Object.entries(result.metadata).filter(([k]) => !k.startsWith('_')).slice(0, 5).map(([k, v]) => (
            <span key={k} className="px-2 py-0.5 rounded text-xs bg-[#334155] text-slate-400">
              {k}: {String(v).slice(0, 30)}
            </span>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-600 mt-2 font-mono">{result.id}</p>
    </div>
  )
}
