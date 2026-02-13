import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { Database, Search, FolderOpen, BarChart3, Heart } from 'lucide-react'
import CollectionManager from './components/CollectionManager'
import DocumentBrowser from './components/DocumentBrowser'
import SearchPlayground from './components/SearchPlayground'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import { getHealth } from './api/client'

const TABS = [
  { id: 'collections', label: 'Collections', icon: Database },
  { id: 'documents', label: 'Documents', icon: FolderOpen },
  { id: 'search', label: 'Search', icon: Search },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('collections')
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {})
  }, [])

  const handleSelectCollection = (name) => {
    setSelectedCollection(name)
    setActiveTab('documents')
  }

  return (
    <div className="min-h-screen bg-[#0f172a]">
      <Toaster position="top-right" toastOptions={{
        style: { background: '#1e293b', color: '#f1f5f9', border: '1px solid #334155' },
      }} />

      {/* Header */}
      <header className="border-b border-[#334155] bg-[#1e293b]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Database className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Local Vector Store</h1>
              <p className="text-xs text-slate-400">Chroma / FAISS · Hybrid Search · Metadata Filtering</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {selectedCollection && (
              <div className="px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                <span className="text-xs text-indigo-400">Active: </span>
                <span className="text-sm font-medium text-indigo-300">{selectedCollection}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <Heart className={`w-3.5 h-3.5 ${health ? 'text-green-400' : 'text-red-400'}`} fill="currentColor" />
              <span className="text-xs text-slate-400">{health ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex gap-1">
            {TABS.map(tab => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors
                    ${isActive
                      ? 'bg-[#0f172a] text-indigo-400 border-t-2 border-indigo-500'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#0f172a]/50'
                    }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'collections' && (
          <CollectionManager onSelectCollection={handleSelectCollection} />
        )}
        {activeTab === 'documents' && (
          <DocumentBrowser collection={selectedCollection} onBack={() => setActiveTab('collections')} />
        )}
        {activeTab === 'search' && (
          <SearchPlayground collection={selectedCollection} />
        )}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard />
        )}
      </main>
    </div>
  )
}
