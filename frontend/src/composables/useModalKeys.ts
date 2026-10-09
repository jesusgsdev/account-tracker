import { watch, onUnmounted, type Ref } from 'vue'

// Stack of open modals so only the topmost reacts to keys (e.g. ConfirmModal over a form modal).
const stack: symbol[] = []

/**
 * Esc closes the modal; Enter submits (ignored in textareas/buttons/links).
 * @param isOpen  reactive open flag
 * @param close   called on Escape
 * @param submit  called on Enter; return false/omit to ignore. Should check validity itself.
 */
export function useModalKeys(isOpen: Ref<boolean>, close: () => void, submit?: () => void) {
  const id = Symbol('modal')

  function onKey(e: KeyboardEvent) {
    if (stack[stack.length - 1] !== id) return
    if (e.key === 'Escape') {
      e.preventDefault()
      close()
    } else if (e.key === 'Enter' && submit && !e.isComposing) {
      const t = e.target as HTMLElement | null
      const tag = t?.tagName
      if (tag === 'TEXTAREA' || tag === 'BUTTON' || tag === 'A' || tag === 'SELECT') return
      e.preventDefault()
      submit()
    }
  }

  function detach() {
    const i = stack.indexOf(id)
    if (i !== -1) stack.splice(i, 1)
    window.removeEventListener('keydown', onKey)
  }

  watch(isOpen, (open) => {
    detach()
    if (open) {
      stack.push(id)
      window.addEventListener('keydown', onKey)
    }
  }, { immediate: true })

  onUnmounted(detach)
}
