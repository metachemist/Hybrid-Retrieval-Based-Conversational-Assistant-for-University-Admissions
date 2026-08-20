'use client'

import { useEffect, useRef, useState } from 'react'
import { api, DocumentInfo } from '@/lib/api'
import { Upload, Trash2, RefreshCw, FileText, Loader2 } from 'lucide-react'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fileRef = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState('')
  const [year, setYear] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)

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
      setUploadMsg(`✓ Uploaded "${result.title}" (${result.chunks_created} chunks created)`)
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

  const inputClass = `w-full border border-neutral-300 rounded-xl px-3.5 py-2.5 text-sm
                      text-neutral-900 placeholder-neutral-400
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                      transition-shadow bg-white`

  return (
    <div className="p-8 space-y-7">
      <div className="animate-in-down">
        <h1 className="font-display font-bold text-2xl text-neutral-900">Documents</h1>
        <p className="text-sm text-neutral-500 mt-0.5">Upload and manage admission policy PDFs</p>
      </div>

      {/* ── Upload form ─────────────────────────────────── */}
      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden animate-in-up stagger-1">
        <div className="px-6 py-4 border-b border-neutral-100 flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center">
            <Upload className="w-4 h-4 text-primary-600" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-neutral-800">Upload Document</h2>
            <p className="text-xs text-neutral-500">PDF files are automatically chunked and indexed</p>
          </div>
        </div>

        <form onSubmit={handleUpload} className="p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1">
              <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1.5">
                PDF File *
              </label>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf"
                required
                className="w-full text-sm text-neutral-600 cursor-pointer
                           file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0
                           file:text-xs file:font-semibold
                           file:bg-neutral-100 file:text-neutral-700
                           hover:file:bg-neutral-200 file:cursor-pointer file:transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1.5">
                Title (optional)
              </label>
              <input type="text" value={title} onChange={e => setTitle(e.target.value)}
                placeholder="Auto-detected from filename" className={inputClass} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1.5">
                Year (optional)
              </label>
              <input type="number" value={year} onChange={e => setYear(e.target.value)}
                placeholder="e.g. 2024" min={2000} max={2099} className={inputClass} />
            </div>
          </div>

          {uploadMsg && (
            <div className={`flex items-start gap-2 px-4 py-3 rounded-xl text-sm border ${
              uploadMsg.startsWith('Upload failed')
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-emerald-50 border-emerald-200 text-emerald-700'
            }`}>
              {uploadMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={uploading}
            className="flex items-center gap-2 px-5 py-2.5 bg-neutral-900 hover:bg-neutral-800
                       text-white rounded-full text-sm font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm
                       hover:scale-[1.02] active:scale-[0.98]"
          >
            {uploading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Upload className="w-4 h-4" />}
            {uploading ? 'Uploading…' : 'Upload Document'}
          </button>
        </form>
      </div>

      {/* ── Document list ───────────────────────────────── */}
      <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden animate-in-up stagger-2">
        <div className="px-6 py-4 border-b border-neutral-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-neutral-800">Ingested Documents</h2>
            <p className="text-xs text-neutral-500">{docs.length} document{docs.length !== 1 ? 's' : ''} indexed</p>
          </div>
          <button
            onClick={fetchDocs}
            className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg
                       transition-all hover:scale-110 active:scale-90"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-5 h-5 animate-spin text-neutral-400 mx-auto mb-2" />
            <p className="text-sm text-neutral-400">Loading documents…</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500 text-sm">{error}</div>
        ) : docs.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-neutral-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6 text-neutral-400" />
            </div>
            <p className="text-sm font-medium text-neutral-700 mb-1">No documents yet</p>
            <p className="text-xs text-neutral-400">Upload an admission policy PDF to get started.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-neutral-50/60 border-b border-neutral-100">
                <th className="px-6 py-3 text-left text-xs font-semibold text-neutral-500">Title</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-neutral-500">Year</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-neutral-500">Chunks</th>
                <th className="px-3 py-3 text-left text-xs font-semibold text-neutral-500">Ingested</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-neutral-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-50">
              {docs.map(doc => (
                <tr key={doc.id} className="hover:bg-neutral-50/70 transition-colors group">
                  <td className="px-6 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0">
                        <FileText className="w-3.5 h-3.5 text-red-500" />
                      </div>
                      <span className="font-medium text-neutral-800">{doc.title}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3.5">
                    {doc.year
                      ? <span className="px-2 py-0.5 bg-neutral-100 text-neutral-600 rounded-full text-xs font-medium">{doc.year}</span>
                      : <span className="text-neutral-400">-</span>}
                  </td>
                  <td className="px-3 py-3.5">
                    <span className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded-full text-xs font-semibold">
                      {doc.chunk_count}
                    </span>
                  </td>
                  <td className="px-3 py-3.5 text-neutral-500 text-xs">
                    {new Date(doc.ingested_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-3.5">
                    <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleReindex(doc.id)}
                        disabled={reindexing === doc.id}
                        className="p-1.5 text-neutral-400 hover:text-primary-600 hover:bg-primary-50
                                   rounded-lg transition-all hover:scale-110 active:scale-90 disabled:opacity-40"
                        title="Re-index"
                      >
                        {reindexing === doc.id
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <RefreshCw className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        disabled={deleting === doc.id}
                        className="p-1.5 text-neutral-400 hover:text-red-600 hover:bg-red-50
                                   rounded-lg transition-all hover:scale-110 active:scale-90 disabled:opacity-40"
                        title="Delete"
                      >
                        {deleting === doc.id
                          ? <Loader2 className="w-4 h-4 animate-spin" />
                          : <Trash2 className="w-4 h-4" />}
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
