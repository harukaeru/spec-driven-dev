import { useEffect, useMemo, useState } from 'react'

const API = '/api/tasks'

async function fetchJSON(url, options) {
  const res = await fetch(url, options)
  if (!res.ok) {
    let message = `リクエストに失敗しました (${res.status})`
    try {
      const body = await res.json()
      if (body?.error) message = body.error
    } catch {
      // ボディが無い / JSON でない場合はデフォルトメッセージを使う
    }
    throw new Error(message)
  }
  return res.status === 204 ? null : res.json()
}

export default function App() {
  const [tasks, setTasks] = useState([])
  const [input, setInput] = useState('')
  const [filter, setFilter] = useState('all') // all | active | completed
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 初回ロード時にサーバーからタスクを取得する
  useEffect(() => {
    fetchJSON(API)
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const addTask = async (e) => {
    e.preventDefault()
    const title = input.trim()
    if (!title) return
    try {
      const task = await fetchJSON(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      setTasks((prev) => [task, ...prev])
      setInput('')
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const toggleTask = async (task) => {
    try {
      const updated = await fetchJSON(`${API}/${task.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !task.completed }),
      })
      setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)))
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const deleteTask = async (id) => {
    try {
      await fetchJSON(`${API}/${id}`, { method: 'DELETE' })
      setTasks((prev) => prev.filter((t) => t.id !== id))
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const clearCompleted = async () => {
    try {
      await fetchJSON(`${API}/completed`, { method: 'DELETE' })
      setTasks((prev) => prev.filter((t) => !t.completed))
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const visibleTasks = useMemo(() => {
    if (filter === 'active') return tasks.filter((t) => !t.completed)
    if (filter === 'completed') return tasks.filter((t) => t.completed)
    return tasks
  }, [tasks, filter])

  const remaining = tasks.filter((t) => !t.completed).length

  return (
    <div className="app">
      <h1>タスク管理</h1>

      <form className="task-form" onSubmit={addTask}>
        <input
          className="task-input"
          type="text"
          value={input}
          placeholder="新しいタスクを入力..."
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="add-btn" type="submit">
          追加
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="filters">
        {['all', 'active', 'completed'].map((f) => (
          <button
            key={f}
            className={`filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'すべて' : f === 'active' ? '未完了' : '完了'}
          </button>
        ))}
      </div>

      <ul className="task-list">
        {loading && <li className="empty">読み込み中...</li>}
        {!loading && visibleTasks.length === 0 && (
          <li className="empty">タスクはありません</li>
        )}
        {visibleTasks.map((task) => (
          <li
            key={task.id}
            className={`task-item ${task.completed ? 'completed' : ''}`}
          >
            <label className="task-label">
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => toggleTask(task)}
              />
              <span className="task-title">{task.title}</span>
            </label>
            <button
              className="delete-btn"
              onClick={() => deleteTask(task.id)}
              aria-label="削除"
            >
              ×
            </button>
          </li>
        ))}
      </ul>

      <footer className="footer">
        <span>残り {remaining} 件</span>
        <button className="clear-btn" onClick={clearCompleted}>
          完了済みを削除
        </button>
      </footer>
    </div>
  )
}
