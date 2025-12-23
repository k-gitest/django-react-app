import { http, HttpResponse } from 'msw'

export const todoHandlers = [
  // Todo一覧
  http.get(`**/todos/`, () => {
    return HttpResponse.json([
      { id: 1, todo_title: "テストタスク1", priority: "HIGH", progress: 50, updated_at: new Date().toISOString() },
      { id: 2, todo_title: "テストタスク2", priority: "MEDIUM", progress: 100, updated_at: new Date().toISOString() },
      { id: 3, todo_title: "テストタスク3", priority: "LOW", progress: 0, updated_at: new Date().toISOString() },
      { id: 4, todo_title: "制限で見えないはずのタスク", priority: "LOW", progress: 0, updated_at: new Date().toISOString() },
    ])
  }),

  // 優先度別統計
  http.get(`**/todos/stats/`, () => {
    return HttpResponse.json([
      { priority: 'high', count: 1 },
      { priority: 'medium', count: 1 },
      { priority: 'low', count: 2 },
    ])
  }),

  // 進捗分布統計
  http.get(`**/todos/progress-stats/`, () => {
    return HttpResponse.json([
      { range: '0-20', count: 1 },
      { range: '40-60', count: 1 },
      { range: '80-100', count: 1 },
    ])
  }),
]