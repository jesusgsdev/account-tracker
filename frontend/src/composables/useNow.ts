import { ref, onMounted, onUnmounted } from 'vue'

/** A `now` ref refreshed every `intervalMs` while the component is mounted. */
export function useNow(intervalMs = 10000) {
  const now = ref(new Date())
  let timer: ReturnType<typeof setInterval> | null = null
  onMounted(() => {
    timer = setInterval(() => { now.value = new Date() }, intervalMs)
  })
  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })
  return now
}
