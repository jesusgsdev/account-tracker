<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay confirm-modal-overlay" @click.self="cancel">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal confirm-modal">
            <div class="modal-header">
              <h2 class="text-lg font-semibold">{{ title }}</h2>
              <button class="btn btn-icon btn-ghost" @click="cancel">✕</button>
            </div>

            <div class="modal-body">
              <p class="text-sm text-muted confirm-message">{{ message }}</p>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="cancel">{{ cancelText }}</button>
              <button
                class="btn"
                :class="isDanger ? 'btn-danger' : 'btn-primary'"
                @click="confirm"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  isDanger?: boolean
}>(), {
  title: 'Confirm Action',
  message: 'Are you sure you want to proceed?',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  isDanger: true
})

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  confirm: []
  cancel: []
}>()

function cancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function confirm() {
  emit('confirm')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.confirm-modal-overlay {
  z-index: 20000;
}
.confirm-modal {
  max-width: 400px;
  width: 90%;
}
.confirm-message {
  line-height: 1.5;
  white-space: pre-wrap;
}
.btn-danger {
  background: var(--negative);
  color: #fff;
  border: none;
}
.btn-danger:hover {
  background: var(--negative-hover, #dc2626);
}
</style>
