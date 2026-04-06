'use client'

import { useEffect, useRef, useState } from 'react'
import { api, DocumentInfo } from '@/lib/api'
import { Upload, Trash2, RefreshCw, FileText, Loader2 } from 'lucide-react'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Upload form state
  const fileRef = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)

  // Per-document action states
  const [deleting, setDeleting] = useState<string | null>(null)
  const [reindexing, setReindexing] = useState<string | null>(null)

  const fetchDocs = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.listDocuments()
      setDocs(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDocs() }, [])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    const file = fileRef.current?.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadMsg(null)
    try {
      const result = await api.uploadDocument(file, title || undefined, year ? parseInt(year) : undefined)
      setUploadMsg(`Uploaded "${result.title}" — ${result.chunks_created} chunks created`)
      setTitle('')
      setYear('')
      if (fileRef.current) fileRef.current.value = ''
      await fetchDocs()
    } catch (err: any) {
      setUploadMsg(`Upload failed: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: string, docTitle: string) => {
    if (!confirm(`Delete "${docTitle}"? This will remove all associated chunks.`)) return
    setDeleting(id)
    try {
      await api.deleteDocument(id)
      setDocs(prev => prev.filter(d => d.id !== id))
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`)
    } finally {
      setDeleting(null)
    }
  }

  const handleReindex = async (id: string) => {
    setReindexing(id)
    try {
      const result = await api.reindexDocument(id)
      alert(`Re-indexed ${result.chunks_reindexed} chunks.`)
    } catch (err: any) {
      alert(`Re-index failed: ${err.message}`)
    } finally {
      setReindexing(null)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">Document Management</h1>
        <p className="text-sm text-gray-500">Upload and manage admission policy PDFs</p>
      </div>

      {/* Upload form */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Upload New Document</h2>
        <form onSubmit={handleUpload} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">PDF File *</label>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                required
                className="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3
                           file:rounded-lg file:border-0 file:text-sm file:font-medium
                           file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Title (optional)</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Auto-detected from filename"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Year (optional)</label>
              <input
                type="number"
                value={year}
                onChange={e => setYear(e.target.value)}
                placeholder="e.g. 2024"
                min={2000}
                max={2099}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {uploadMsg && (
            <p className={`text-sm px-3 py-2 rounded-lg ${
              uploadMsg.startsWith('Upload failed')
                ? 'bg-red-50 text-red-600'
                : 'bg-green-50 text-green-700'
            }`}>
              {uploadMsg}
            </p>
          )}

          <button
            type="submit"
            disabled={uploading}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg
                       text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {uploading ? 'Uploading…' : 'Upload Document'}
          </button>
        </form>
      </div>

      {/* Document list */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Ingested Documents</h2>
          <button
            onClick={fetchDocs}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading documents…</div>
        ) : error ? (
          <div className="p-8 text-center text-red-500 text-sm">{error}</div>
        ) : docs.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <FileText className="w-10 h-10 mx-auto mb-2 opacity-40" />
            <p className="text-sm">No documents ingested yet. Upload a PDF to get started.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                <th className="px-5 py-3 font-medium">Title</th>
                <th className="px-3 py-3 font-medium">Year</th>
                <th className="px-3 py-3 font-medium">Chunks</th>
                <th className="px-3 py-3 font-medium">Ingested</th>
                <th className="px-3 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {docs.map(doc => (
                <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-800">{doc.title}</td>
                  <td className="px-3 py-3 text-gray-500">{doc.year ?? '—'}</td>
                  <td className="px-3 py-3 text-gray-500">{doc.chunk_count}</td>
                  <td className="px-3 py-3 text-gray-500">
                    {new Date(doc.ingested_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: 'numeric',
                    })}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleReindex(doc.id)}
                        disabled={reindexing === doc.id}
                        className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50
                                   rounded-lg transition-colors disabled:opacity-50"
                        title="Re-index"
                      >
                        {reindexing === doc.id
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <RefreshCw className="w-4 h-4" />
                        }
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        disabled={deleting === doc.id}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50
                                   rounded-lg transition-colors disabled:opacity-50"
                        title="Delete"
                      >
                        {deleting === doc.id
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <Trash2 className="w-4 h-4" />
                        }
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
