import { api } from './client'
import type { ChatMessageOut, ChatSessionDetail, ChatSessionOut } from '../types'

export type StreamEvent =
  | { type: 'user_message'; message: ChatMessageOut }
  | { type: 'chunk'; delta: string }
  | { type: 'done'; character_message: ChatMessageOut }
  | { type: 'error'; message: string }

/** 把"非流式整段回复"伪装成 stream 事件序列，分批 emit 出去，
 *  这样 ChatPage 的渲染逻辑无需做任何分支。
 */
async function fallbackToNonStream(
  id: number,
  content: string,
  onEvent: (e: StreamEvent) => void,
): Promise<void> {
  const data = await chatApi.send(id, content)
  onEvent({ type: 'user_message', message: data.user_message })

  // 把整段回复按字符分片小批发出，制造类似流的视觉
  const text = data.character_message.content || ''
  const step = Math.max(1, Math.ceil(text.length / 60))
  for (let i = 0; i < text.length; i += step) {
    onEvent({ type: 'chunk', delta: text.slice(i, i + step) })
    // 每片 ≈16ms 节奏，比"瞬时整段"舒服
    await new Promise((r) => setTimeout(r, 16))
  }
  onEvent({ type: 'done', character_message: data.character_message })
}

export const chatApi = {
  listSessions: async () => (await api.get<ChatSessionOut[]>('/chat/sessions')).data,
  createSession: async (params: {
    novel_id: number
    character_id: number
    user_name?: string
  }) => (await api.post<ChatSessionOut>('/chat/sessions', params)).data,
  getSession: async (id: number) =>
    (await api.get<ChatSessionDetail>(`/chat/sessions/${id}`)).data,
  deleteSession: async (id: number) =>
    (await api.delete(`/chat/sessions/${id}`)).data,
  send: async (id: number, content: string) =>
    (
      await api.post<{
        user_message: ChatMessageOut
        character_message: ChatMessageOut
      }>(`/chat/sessions/${id}/messages`, { content })
    ).data,

  /**
   * 真流式发送：用 fetch + ReadableStream 解析 SSE。
   * - 若 backend 暂未注册 /messages/stream 端点（404），自动降级走普通 POST，
   *   把结果切片后伪装成 stream 事件，保证 UX 不间断。
   * - 若网络异常 / 400 / 500，则照常抛错由 UI 提示。
   */
  sendStream: async (
    id: number,
    content: string,
    onEvent: (e: StreamEvent) => void,
    signal?: AbortSignal,
  ) => {
    let resp: Response
    try {
      resp = await fetch(`/api/v1/chat/sessions/${id}/messages/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
        signal,
      })
    } catch (e) {
      // 网络层失败（fetch 抛错） —— 走降级
      console.warn('[chat] 流式 fetch 异常，降级到非流式:', e)
      return await fallbackToNonStream(id, content, onEvent)
    }

    // 后端未升级（缺路由）或 SPA fallback 命中 —— 自动降级
    if (resp.status === 404 || resp.status === 405) {
      console.warn('[chat] /messages/stream 不可用 (HTTP', resp.status, ')，降级到非流式')
      return await fallbackToNonStream(id, content, onEvent)
    }

    if (!resp.ok || !resp.body) {
      const detail = await resp.text().catch(() => resp.statusText)
      throw new Error(`流式请求失败: ${detail || resp.status}`)
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      // SSE 事件以 \n\n 分隔
      const parts = buf.split('\n\n')
      buf = parts.pop() || ''
      for (const raw of parts) {
        const line = raw.trim()
        if (!line.startsWith('data:')) continue
        const data = line.slice(5).trim()
        if (!data) continue
        try {
          const evt = JSON.parse(data) as StreamEvent
          onEvent(evt)
        } catch (e) {
          // 容错：跳过坏行
        }
      }
    }
  },

  exportUrl: (id: number) => `/api/v1/chat/sessions/${id}/export`,
}
