<template>
  <div class="shares-panel">
    <HoldingsSummary
      :holdings="holdings"
      :display-holdings="displayHoldings"
      :portfolio="portfolio"
      :now="now"
      @manage="showModal = true"
      @add="openManageAndAdd"
    />

    <ManageHoldingsModal
      v-model="showModal"
      v-model:show-add-form="showAddForm"
      :account-name="accountName"
      :holdings="holdings"
      :display-holdings="displayHoldings"
      :portfolio="portfolio"
      :is-loading="isLoading"
      :syncing="syncing"
      :adding="adding"
      :add-error="addError"
      :local-error="localError"
      :editing-id="editingId"
      :edit-form="editForm"
      :form="form"
      :refreshed-at="refreshedAt"
      @refresh="handleRefresh"
      @sync="syncAccountValue"
      @add="addHolding"
      @edit="startEdit"
      @save="saveEdit"
      @cancel-edit="editingId = null"
      @remove="removeHolding"
    />

    <ConfirmModal
      v-model="showDeleteConfirm"
      title="Remove Holding"
      message="Are you sure you want to remove this stock holding?"
      confirmText="Remove"
      @confirm="executeDeleteHolding"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useHoldingsManager } from '@/composables/useHoldingsManager'
import { useNow } from '@/composables/useNow'
import { formatRefreshedLabel } from '@/utils/holdings'
import ConfirmModal from '@/components/layout/ConfirmModal.vue'
import HoldingsSummary from './shares/HoldingsSummary.vue'
import ManageHoldingsModal from './shares/ManageHoldingsModal.vue'

const props = defineProps<{
  accountId: number
  accountName?: string
}>()
const emit = defineEmits<{ synced: [newValue: number] }>()

const {
  holdings, syncing, showAddForm, adding, addError, localError, editingId, editForm, form,
  showModal, showDeleteConfirm, portfolio, isLoading, displayHoldings, lastRefreshedAt,
  handleRefresh, addHolding, startEdit, saveEdit, removeHolding, executeDeleteHolding,
  syncAccountValue, openManageAndAdd,
} = useHoldingsManager(() => props.accountId, (v) => emit('synced', v))

const now = useNow()
const refreshedAt = computed(() => formatRefreshedLabel(lastRefreshedAt.value, now.value))
</script>

<style scoped>
.shares-panel {
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-3);
  margin-top: var(--space-2);
}
</style>
