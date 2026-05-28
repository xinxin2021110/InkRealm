import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, ChevronLeft } from 'lucide-react'
import { novelsApi } from '../api/novels'
import PageTitle from '../components/PageTitle'

export default function UploadNovel() {
  const nav = useNavigate()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [description, setDescription] = useState('')
  const [errMsg, setErrMsg] = useState('')

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('请先选择 .jsonl 文件')
      const fd = new FormData()
      fd.append('file', file)
      if (title) fd.append('title', title)
      if (author) fd.append('author', author)
      if (description) fd.append('description', description)
      return novelsApi.upload(fd)
    },
    onSuccess: (n) => {
      qc.invalidateQueries({ queryKey: ['novels'] })
      nav(`/novels/${n.id}`)
    },
    onError: (e: any) => setErrMsg(e?.message || '上传失败'),
  })

  const onPick = (f: File) => {
    if (!f.name.toLowerCase().endsWith('.jsonl')) {
      setErrMsg('文件必须为 .jsonl 格式')
      return
    }
    if (f.size > 50 * 1024 * 1024) {
      setErrMsg('文件大小不能超过 50MB')
      return
    }
    setErrMsg('')
    setFile(f)
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <button onClick={() => nav(-1)} className="inline-flex items-center gap-1.5 text-sm text-ink-light hover:text-ink mb-4">
        <ChevronLeft className="w-4 h-4" /> 返回
      </button>
      <PageTitle title="上传小说" subtitle="支持 JSONL 角色信息库 — 系统将自动解析并提取所有可玩角色" />

      <div className="ancient-page rounded-md p-8">
        <label
          htmlFor="file"
          className={`block w-full rounded-md border-2 border-dashed transition cursor-pointer
            ${file ? 'border-cinnabar bg-cinnabar/5' : 'border-ink/25 hover:border-cinnabar/60 hover:bg-cream/40'}
            p-10 text-center`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const f = e.dataTransfer.files?.[0]
            if (f) onPick(f)
          }}
        >
          <input
            ref={fileRef}
            id="file"
            type="file"
            accept=".jsonl"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) onPick(f)
            }}
          />
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="w-8 h-8 text-cinnabar" />
              <div className="text-left">
                <div className="font-title text-ink">{file.name}</div>
                <div className="text-xs text-ink-light">
                  {(file.size / 1024).toFixed(1)} KB · 点击重新选择
                </div>
              </div>
            </div>
          ) : (
            <div>
              <Upload className="w-10 h-10 mx-auto text-ink-light mb-3" />
              <div className="font-title text-ink tracking-wider">将 .jsonl 文件拖拽到这里</div>
              <div className="text-xs text-ink-light mt-1">或点击选择文件 (单文件 ≤ 50MB)</div>
            </div>
          )}
        </label>

        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-title text-ink mb-1.5">小说名称(留空则自动从文件取)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="bamboo-input"
              placeholder="如:斗破苍穹"
              maxLength={120}
            />
          </div>
          <div>
            <label className="block text-sm font-title text-ink mb-1.5">作者(可选)</label>
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              className="bamboo-input"
              placeholder="如:天蚕土豆"
              maxLength={60}
            />
          </div>
          <div>
            <label className="block text-sm font-title text-ink mb-1.5">简介(可选)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="bamboo-input"
              rows={3}
              placeholder="一句话介绍这本书……"
              maxLength={500}
            />
          </div>
        </div>

        {errMsg && (
          <div className="mt-4 px-4 py-2 rounded bg-cinnabar/10 border border-cinnabar/30 text-cinnabar text-sm">
            {errMsg}
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button onClick={() => nav('/library')} className="btn-ghost">
            取消
          </button>
          <button
            onClick={() => upload.mutate()}
            disabled={!file || upload.isPending}
            className="btn-primary"
          >
            {upload.isPending ? '正在解析…' : '上传并解析'}
          </button>
        </div>
      </div>

      <div className="mt-8 text-xs text-ink-light/80 leading-relaxed">
        <div className="font-title text-ink mb-2">JSONL 格式参考</div>
        <pre className="bg-cream/60 rounded p-3 overflow-x-auto text-[11px]">
{`{"book_title":"...","target_character":"林动","chapter_order":1,"chapter_title":"第1章",
 "summary":"...","memory_points":[...],"personality_traits":[...],
 "speech_style":[...],"evidence_quotes":[...],"relationships":[...],"key_motivations":[...]}`}
        </pre>
      </div>
    </div>
  )
}
