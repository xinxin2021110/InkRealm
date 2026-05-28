import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import NovelLibrary from './pages/NovelLibrary'
import NovelDetail from './pages/NovelDetail'
import UploadNovel from './pages/UploadNovel'
import ChatSessions from './pages/ChatSessions'
import ChatPage from './pages/ChatPage'
import PersonaCreator from './pages/PersonaCreator'
import OutlineConfirm from './pages/OutlineConfirm'
import ChapterReader from './pages/ChapterReader'
import MyStories from './pages/MyStories'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="library" element={<NovelLibrary />} />
        <Route path="novels/:novelId" element={<NovelDetail />} />
        <Route path="upload" element={<UploadNovel />} />

        <Route path="chat" element={<ChatSessions />} />
        <Route path="chat/:sessionId" element={<ChatPage />} />

        <Route path="stories" element={<MyStories />} />
        <Route path="stories/new/:characterId" element={<PersonaCreator />} />
        <Route path="stories/:storyId/outline" element={<OutlineConfirm />} />
        <Route path="stories/:storyId" element={<ChapterReader />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
