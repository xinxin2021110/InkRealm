import { api } from './client'
import type { CharacterDetail, NovelDetail, NovelOut } from '../types'

export const novelsApi = {
  list: async () => (await api.get<NovelOut[]>('/novels')).data,
  detail: async (id: number) => (await api.get<NovelDetail>(`/novels/${id}`)).data,
  remove: async (id: number) => (await api.delete(`/novels/${id}`)).data,
  upload: async (form: FormData) =>
    (
      await api.post<NovelDetail>('/novels', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    ).data,
  characterDetail: async (id: number) =>
    (await api.get<CharacterDetail>(`/characters/${id}`)).data,
}
