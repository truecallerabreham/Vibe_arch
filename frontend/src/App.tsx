import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import ComparisonPage from './pages/ComparisonPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/compare" element={<ComparisonPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
