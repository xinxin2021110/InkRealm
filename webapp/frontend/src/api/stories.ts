import { api } from './client'
import type {
  ChapterOut,
  PersonaOptionsOut,
  PersonaOption,
  StoryBrief,
  StoryDetail,
} from '../types'

export interface CreateStoryParams {
  novel_id: number
  character_id: number
  user_name: string
  selections: {
    background: string
    personality: string
    relationship: string
    ability: string
  }
  total_chapters: number
}

export const storiesApi = {
  personaOptions: async (novelId: number, characterId: number) =>
    (
      await api.get<PersonaOptionsOut>(
        `/stories/persona-options/${novelId}/${characterId}`,
      )
    ).data,

  create: async (params: CreateStoryParams) =>
    (await api.post<StoryDetail>('/stories', params)).data,

  list: async () => (await api.get<StoryBrief[]>('/stories')).data,

  detail: async (id: number) => (await api.get<StoryDetail>(`/stories/${id}`)).data,

  remove: async (id: number) => (await api.delete(`/stories/${id}`)).data,

  choose: async (storyId: number, chapterNumber: number, optionId: string) =>
    (
      await api.post<{
        chapter: ChapterOut
        relationship_meter: Record<string, number>
        user_power_level: string
      }>(
        `/stories/${storyId}/chapters/${chapterNumber}/choose`,
        { option_id: optionId },
      )
    ).data,

  regenerate: async (storyId: number, chapterNumber: number) =>
    (
      await api.post<ChapterOut>(
        `/stories/${storyId}/chapters/${chapterNumber}/regenerate`,
      )
    ).data,

  exportUrl: (id: number) => `/api/v1/stories/${id}/export`,
}

export type { PersonaOption }
