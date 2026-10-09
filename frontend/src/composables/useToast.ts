import { reactive, readonly } from 'vue'

export type ToastKind = 'success' | 'error' | 'info'
export interface Toast { id: number; kind: ToastKind; message: string }

const toasts = reactive<Toast[]>([])
let nextId = 1

function dismiss(id: number) {
  const i = toasts.findIndex(t => t.id === id)
  if (i !== -1) toasts.splice(i, 1)
}

function push(kind: ToastKind, message: string, timeout?: number) {
  const id = nextId++
  toasts.push({ id, kind, message })
  const ms = timeout ?? (kind === 'error' ? 7000 : 3500)
  if (ms > 0) setTimeout(() => dismiss(id), ms)
  return id
}

/** Lightweight global toast API (module-level state, no provider needed). */
export function useToast() {
  return {
    toasts: readonly(toasts) as readonly Toast[],
    dismiss,
    success: (m: string, timeout?: number) => push('success', m, timeout),
    error: (m: string, timeout?: number) => push('error', m, timeout),
    info: (m: string, timeout?: number) => push('info', m, timeout),
  }
}
