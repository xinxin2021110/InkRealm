// 与后端 schemas 一一对应的类型定义

export interface NovelOut {
  id: number
  title: string
  author: string
  cover_emoji: string
  description: string
  characters_count: number
  created_at: string
}

export interface CharacterBrief {
  id: number
  novel_id: number
  name: string
  aliases: string[]
  is_protagonist: boolean
  profile_summary: string
  avatar_emoji: string
  memory_count: number
  quote_count: number
  analyzed: boolean
}

export interface NovelDetail extends NovelOut {
  characters: CharacterBrief[]
}

export interface CharacterDetail extends CharacterBrief {
  book_title: string
  personality_traits: string[]
  speech_style: string[]
  emotional_states: string[]
  key_motivations: string[]
  relationships: { name: string; relation: string; interaction: string; attitude: string }[]
  sample_quotes: string[]
}

// —— 聊天 ——
export interface ChatMessageOut {
  id: number
  role: 'user' | 'assistant'
  content: string
  retrieved_memories: number
  retrieved_quotes: number
  created_at: string
}

export interface ChatSessionOut {
  id: number
  novel_id: number
  character_id: number
  character_name: string
  novel_title: string
  user_name: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview: string
}

export interface ChatSessionDetail extends ChatSessionOut {
  messages: ChatMessageOut[]
}

// —— 故事 ——
export interface PersonaOption {
  id: string
  title: string
  description: string
  implications: string
}

export interface PersonaDimension {
  description: string
  options: PersonaOption[]
}

export interface PersonaOptionsOut {
  background: PersonaDimension
  personality: PersonaDimension
  relationship: PersonaDimension
  ability: PersonaDimension
}

export interface UserPersonaOut {
  name: string
  background: string
  personality: string
  relationship_to_protagonist: string
  initial_ability: string
  background_detail: string
  personality_detail: string
  relationship_detail: string
  ability_detail: string
  story_goal: string
}

export interface ChapterOutlineOut {
  chapter_number: number
  title: string
  core_conflict: string
  scene_setting: string
  character_interaction: string
  plot_function: string
  branch_points: string[]
}

export interface StoryOutlineOut {
  total_chapters: number
  title: string
  theme: string
  chapters: ChapterOutlineOut[]
}

export interface ChoiceOptionOut {
  option_id: string
  text: string
  description: string
  impact: string
  risk: string
  relationship_change: Record<string, number>
  flags_set: string[]
}

export interface ChapterChoicesOut {
  chapter_number: number
  situation_summary: string
  options: ChoiceOptionOut[]
}

export interface ChapterOut {
  chapter_number: number
  title: string
  content: string
  summary: string
  key_events: string[]
  choices: ChapterChoicesOut | null
  user_choice: string
  is_last: boolean
}

export interface StoryBrief {
  id: number
  novel_id: number
  character_id: number
  novel_title: string
  target_character: string
  title: string
  theme: string
  user_persona_name: string
  total_chapters: number
  current_chapter: number
  user_power_level: string
  relationship_meter: Record<string, number>
  status: 'ongoing' | 'finished' | 'abandoned'
  created_at: string
  updated_at: string
}

export interface StoryDetail extends StoryBrief {
  user_persona: UserPersonaOut
  outline: StoryOutlineOut
  flags: Record<string, any>
  chapters: ChapterOut[]
}

export type SelectionsKey = 'background' | 'personality' | 'relationship' | 'ability'
