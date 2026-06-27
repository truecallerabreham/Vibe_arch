import { useState } from 'react'

function App() {
  const [repo1, setRepo1] = useState('')
  const [repo2, setRepo2] = useState('')

  return (
    <div className="min-h-screen bg-arch-bg">
      <header className="border-b border-arch-border px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Vibe Arch
            </h1>
            <p className="text-sm text-gray-400 mt-0.5">
              Compare open-source architectures. Choose deliberately.
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4 tracking-tight">
            Stop vibe-coding.<br />
            <span className="text-gray-400">Build with real architecture.</span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Paste two GitHub repository URLs and see their architectures
            side-by-side. Compare component by component. Choose what fits
            your project — with understanding, not guesses.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div>
            <label className="block text-sm text-gray-400 mb-2 font-medium">
              Repository 1
            </label>
            <input
              type="text"
              value={repo1}
              onChange={(e) => setRepo1(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full px-4 py-3 bg-arch-surface border border-arch-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2 font-medium">
              Repository 2
            </label>
            <input
              type="text"
              value={repo2}
              onChange={(e) => setRepo2(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="w-full px-4 py-3 bg-arch-surface border border-arch-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </div>
        </div>

        <div className="text-center">
          <button
            disabled={!repo1 || !repo2}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
          >
            Compare Architectures
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
