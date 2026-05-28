import { create } from 'zustand'
import type { SelectionsKey } from '../types'

/** 故事创建中跨页面的临时草稿 */
interface StoryDraftState {
  novelId: number | null
  characterId: number | null
  characterName: string
  bookTitle: string
  userName: string
  selections: Record<SelectionsKey, string>
  totalChapters: number
  setMeta: (p: {
    novelId: number
    characterId: number
    characterName: string
    bookTitle: string
  }) => void
  setUserName: (n: string) => void
  setSelection: (k: SelectionsKey, v: string) => void
  setTotalChapters: (n: number) => void
  reset: () => void
}

const initial = {
  novelId: null as number | null,
  characterId: null as number | null,
  characterName: '',
  bookTitle: '',
  userName: '',
  selections: {
    background: 'A',
    personality: 'A',
    relationship: 'A',
    ability: 'A',
  } as Record<SelectionsKey, string>,
  totalChapters: 5,
}

export const useStoryDraft = create<StoryDraftState>((set) => ({
  ...initial,
  setMeta: (p) =>
    set({
      novelId: p.novelId,
      characterId: p.characterId,
      characterName: p.characterName,
      bookTitle: p.bookTitle,
    }),
  setUserName: (userName) => set({ userName }),
  setSelection: (k, v) =>
    set((s) => ({ selections: { ...s.selections, [k]: v } })),
  setTotalChapters: (totalChapters) => set({ totalChapters }),
  reset: () => set({ ...initial }),
}))
