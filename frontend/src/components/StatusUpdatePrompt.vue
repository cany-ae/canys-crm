<template>
  <Dialog
    v-model="dialogVisible"
    :options="{ title: __('Status aktualisieren?'), size: 'md' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-base text-ink-gray-5">
          {{ triggerMessage }}
        </p>

        <div class="flex items-center gap-2">
          <span class="text-sm font-medium text-ink-gray-7">
            {{ __('Aktueller Status:') }}
          </span>
          <div class="flex items-center gap-1.5">
            <IndicatorIcon
              v-if="currentStatusData"
              :class="currentStatusData.color"
            />
            <span class="text-sm text-ink-gray-9 font-medium">
              {{ currentStatus }}
            </span>
          </div>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink-gray-7">
            {{ __('Neuer Status') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="status in availableStatuses"
              :key="status.name"
              class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-all"
              :class="
                selectedStatus === status.name
                  ? 'border-ink-gray-9 bg-ink-gray-9 text-white shadow-sm'
                  : 'border-outline-gray-2 bg-surface-white text-ink-gray-7 hover:border-outline-gray-3 hover:bg-surface-gray-2'
              "
              @click="selectedStatus = status.name"
            >
              <IndicatorIcon
                :class="
                  selectedStatus === status.name
                    ? 'text-white'
                    : status.color
                "
              />
              <span>{{ status.name }}</span>
            </button>
          </div>
        </div>

        <div>
          <label class="mb-1.5 block text-sm font-medium text-ink-gray-7">
            {{ __('Notiz (optional)') }}
          </label>
          <textarea
            v-model="note"
            :placeholder="__('z.B. Kunde hat Interesse gezeigt...')"
            class="form-input w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:border-outline-gray-4 focus:ring-0"
            rows="3"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full flex-row-reverse gap-2">
        <Button
          variant="solid"
          :label="__('Status aendern')"
          :disabled="!selectedStatus || selectedStatus === currentStatus"
          @click="handleStatusChange"
        />
        <Button
          variant="ghost"
          :label="__('Status beibehalten')"
          @click="handleClose"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { statusesStore } from '@/stores/statuses'
import { Dialog, Button } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  leadName: {
    type: String,
    default: '',
  },
  currentStatus: {
    type: String,
    default: '',
  },
  triggerAction: {
    type: String,
    default: 'call',
    validator: (value) => ['call', 'email', 'task', 'event'].includes(value),
  },
})

const emit = defineEmits(['update:show', 'statusChanged'])

const { getLeadStatus, leadStatuses } = statusesStore()

const selectedStatus = ref('')
const note = ref('')

const dialogVisible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      selectedStatus.value = ''
      note.value = ''
    }
  },
)

const triggerMessage = computed(() => {
  const labels = {
    call: 'einem Anruf',
    email: 'einer E-Mail',
    task: 'einer abgeschlossenen Aufgabe',
    event: 'einem Termin',
  }
  const actionLabel = labels[props.triggerAction] || props.triggerAction
  return __('Nach {0}: Moechten Sie den Lead-Status aktualisieren?', [actionLabel])
})

const currentStatusData = computed(() => {
  if (!props.currentStatus) return null
  return getLeadStatus(props.currentStatus)
})

const availableStatuses = computed(() => {
  if (!leadStatuses.data) return []
  return leadStatuses.data.filter((s) => s.name !== props.currentStatus)
})

function handleStatusChange() {
  if (selectedStatus.value && selectedStatus.value !== props.currentStatus) {
    emit('statusChanged', selectedStatus.value, note.value)
    dialogVisible.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
}
</script>
