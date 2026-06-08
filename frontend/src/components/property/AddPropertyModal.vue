<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal">
            <div class="modal-header">
              <h2 class="text-lg font-semibold">{{ isEdit ? 'Edit Property Details' : 'Add Property' }}</h2>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="form-group">
                <label class="form-label" for="prop-name">Property Name *</label>
                <input id="prop-name" v-model="form.name" type="text" class="form-input" placeholder="e.g. Main Home" />
              </div>

              <div class="form-group">
                <label class="form-label" for="prop-address">Address</label>
                <input id="prop-address" v-model="form.property_address" type="text" class="form-input" placeholder="e.g. 123 London Rd" />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="prop-purchase-date">Purchase Date</label>
                  <input id="prop-purchase-date" v-model="form.purchase_date" type="date" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label" for="prop-original">Original Purchase Price (£)</label>
                  <input id="prop-original" v-model.number="form.original_price" type="number" min="0" step="1" class="form-input" placeholder="e.g. 280000" />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="prop-value">Current Estimated Value (£) *</label>
                <input id="prop-value" v-model.number="form.property_value" type="number" min="0" step="1" class="form-input" placeholder="e.g. 300000" :disabled="isEdit" />
                <p v-if="isEdit" class="text-xs text-muted mt-1">Value changes are tracked via the "Update Value" button on the card.</p>
              </div>

              <div class="form-group">
                <label class="form-label" for="prop-ownership">Ownership Share (%) *</label>
                <input id="prop-ownership" v-model.number="form.ownership_percent" type="number" min="1" max="100" step="1" class="form-input" />
                <p class="text-xs text-muted mt-1">Used to compute your portion of property value, debt, and equity.</p>
              </div>

              <div class="form-group">
                <label class="form-label" for="prop-notes">Notes</label>
                <textarea id="prop-notes" v-model="form.notes" class="form-textarea" rows="2" placeholder="Optional notes…" />
              </div>
            </div>

            <div class="modal-footer">
              <button v-if="isEdit" class="btn btn-danger mr-auto" @click="$emit('delete')">Delete Property</button>
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button class="btn btn-primary" :disabled="!isValid || saving" @click="save">
                {{ saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Property' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Property } from '@/api/client'

const props = defineProps<{
  modelValue: boolean
  property?: Property | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: [form: any]
  delete: []
}>()

const isEdit = computed(() => !!props.property)
const saving = ref(false)

const defaultForm = () => ({
  name: '',
  property_address: '',
  purchase_date: '',
  original_price: null as number | null,
  property_value: 0,
  ownership_percent: 100,
  notes: '',
})

const form = ref(defaultForm())

watch(() => props.property, (p) => {
  if (p) {
    form.value = {
      name: p.name,
      property_address: p.property_address ?? '',
      purchase_date: p.purchase_date ? p.purchase_date.split('T')[0] : '',
      original_price: p.original_price ?? null,
      property_value: p.property_value,
      ownership_percent: p.ownership_percent,
      notes: p.notes ?? '',
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

const isValid = computed(() =>
  form.value.name.trim().length > 0 &&
  form.value.property_value >= 0 &&
  form.value.ownership_percent > 0 &&
  form.value.ownership_percent <= 100
)

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (!isValid.value) return
  saving.value = true
  try {
    emit('saved', {
      ...form.value,
      property_address: form.value.property_address || undefined,
      notes: form.value.notes || undefined,
      original_price: form.value.original_price ?? undefined,
      purchase_date: form.value.purchase_date || undefined,
    })
    close()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}
.form-textarea {
  resize: vertical;
  min-height: 60px;
}
.mr-auto {
  margin-right: auto;
}
.mt-1 {
  margin-top: 4px;
}
@media (max-width: 520px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
