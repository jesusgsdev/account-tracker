import { watch } from 'vue'
import { useDocumentVisibility } from '@vueuse/core'

/**
 * Call `fn` when the tab becomes visible again, at most once per `minIntervalMs`
 * (measured from the last time it ran, or from setup). Cleans up with the component.
 */
export function useRefetchOnFocus(fn: () => unknown, minIntervalMs = 3 * 60_000) {
  const visibility = useDocumentVisibility()
  let last = Date.now()
  watch(visibility, (v) => {
    if (v !== 'visible') return
    if (Date.now() - last < minIntervalMs) return
    last = Date.now()
    void fn()
  })
  /** Mark data as just refreshed (e.g. after a manual refresh). */
  return { touch: () => { last = Date.now() } }
}
