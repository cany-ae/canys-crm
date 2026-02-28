<template>
  <div
    class="activity group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-md bg-surface-gray-1 px-4 py-3 hover:bg-surface-gray-2"
  >
    <div class="flex items-center justify-between">
      <div class="truncate text-lg font-medium text-ink-gray-8">
        {{ note.title }}
      </div>
      <Dropdown
        :options="[
          {
            label: __('Löschen'),
            icon: 'trash-2',
            onClick: () => deleteNote(note.name),
          },
        ]"
        @click.stop
        class="h-6 w-6"
      >
        <Button
          icon="more-horizontal"
          variant="ghosted"
          class="!h-6 !w-6 hover:bg-surface-gray-2"
        />
      </Dropdown>
    </div>
    <TextEditor
      v-if="note.content"
      :content="note.content"
      :editable="false"
      editor-class="prose-sm text-p-sm max-w-none text-ink-gray-5 focus:outline-none"
      class="flex-1 overflow-hidden"
    />
    <div class="mt-1 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2 truncate">
        <UserAvatar :user="note.owner" size="xs" />
        <div
          class="truncate text-sm text-ink-gray-8"
          :title="getUser(note.owner).full_name"
        >
          {{ getUser(note.owner).full_name }}
        </div>
      </div>
      <div class="flex items-center gap-2">
        <!-- Erinnerungs-Badge -->
        <Tooltip v-if="note.erinnerung" :text="__('Erinnerung: ') + formatErinnerung(note.erinnerung)">
          <div
            class="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium"
            :class="isOverdue(note.erinnerung) ? 'bg-red-100 text-red-700' : 'bg-blue-50 text-blue-600'"
          >
            <svg
              class="h-3 w-3"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ formatErinnerung(note.erinnerung) }}
          </div>
        </Tooltip>
        <Tooltip :text="formatDate(note.modified)">
          <div class="truncate text-sm text-ink-gray-7">
            {{ __(timeAgo(note.modified)) }}
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { timeAgo, formatDate } from '@/utils'
import { Tooltip, Dropdown, TextEditor, call } from 'frappe-ui'
import { usersStore } from '@/stores/users'

const props = defineProps({
  note: Object,
})

const notes = defineModel()

const { getUser } = usersStore()

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'FCRM Note',
    name,
  })
  notes.value?.reload()
}

function formatErinnerung(dt) {
  if (!dt) return ''
  try {
    // Frappe returns datetime as "YYYY-MM-DD HH:MM:SS"
    const dateStr = dt.includes('T') ? dt : dt.replace(' ', 'T')
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dt
    return d.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dt
  }
}

function isOverdue(dt) {
  if (!dt) return false
  try {
    const dateStr = dt.includes('T') ? dt : dt.replace(' ', 'T')
    return new Date(dateStr) < new Date()
  } catch {
    return false
  }
}
</script>
