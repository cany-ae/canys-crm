<template>
  <TaskModal
    v-model="showTaskModal"
    v-model:reloadTasks="activities"
    :task="task"
    :doctype="doctype"
    :doc="doc?.name"
    @after="redirect('tasks')"
  />
  <NoteModal
    v-model="showNoteModal"
    v-model:reloadNotes="activities"
    :note="note"
    :doctype="doctype"
    :doc="doc?.name"
    :withTimer="noteWithTimer"
    @after="redirect('notes')"
  />
  <CallLogModal
    v-if="showCallLogModal"
    v-model="showCallLogModal"
    :data="callLog"
    :referenceDoc="referenceDoc"
    :options="{ afterInsert: () => activities.reload() }"
  />
  <EventModal
    v-if="showEventModal"
    v-model="showEventModal"
    :event="activeEvent"
    :doctype="doctype"
    :docname="doc?.name"
    :lockedParticipantEmails="lockedParticipantEmails"
  />
</template>
<script setup>
import TaskModal from '@/components/Modals/TaskModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
import EventModal from '@/components/Modals/EventModal.vue'
import { showEventModal, activeEvent, lockedParticipantEmails } from '@/composables/event'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: String,
  doc: Object,
})

const activities = defineModel()

// Event
async function showEvent(e) {
  const eventData = e || {}

  // When creating a new event (no existing event name) from a Lead/Deal context,
  // automatically add the lead/deal contact as a locked, non-removable participant.
  if (!eventData.name && props.doctype && props.doc?.name) {
    try {
      const data = await call('frappe.client.get_value', {
        doctype: props.doctype,
        filters: { name: props.doc.name },
        fieldname: ['email', 'first_name', 'last_name'],
      })
      if (data?.email) {
        // Find the Contact record for this email (required by Event Participants)
        try {
          const contact = await call('frappe.client.get_value', {
            doctype: 'Contact',
            filters: { email_id: data.email },
            fieldname: ['name'],
          })
          if (contact?.name) {
            eventData.event_participants = [
              {
                email: data.email,
                reference_doctype: 'Contact',
                reference_docname: contact.name,
              },
            ]
            // Mark this email as locked (non-removable)
            lockedParticipantEmails.value = [data.email]
          }
        } catch (contactErr) {
          // No Contact found - skip auto-participant
          lockedParticipantEmails.value = []
        }
      } else {
        lockedParticipantEmails.value = []
      }
    } catch (err) {
      // Silently continue - participant can be added manually
      lockedParticipantEmails.value = []
    }
  } else if (!eventData.name) {
    // Not in lead/deal context, clear locked participants
    lockedParticipantEmails.value = []
  }
  // When editing an existing event, don't change locked participants
  // (they were already set or not relevant)
  if (eventData.name && !lockedParticipantEmails.value?.length) {
    lockedParticipantEmails.value = []
  }

  showEventModal.value = true
  activeEvent.value = eventData
}

// Tasks
const showTaskModal = ref(false)
const task = ref({})

function showTask(t) {
  task.value = t || {
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    priority: 'Low',
    status: 'Backlog',
  }
  showTaskModal.value = true
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  activities.value.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    activities.value.reload()
  })
}

// Notes
const showNoteModal = ref(false)
const note = ref({})
const noteWithTimer = ref(false)

function showNote(n) {
  noteWithTimer.value = false
  note.value = n || {
    title: '',
    content: '',
  }
  showNoteModal.value = true
}

function showNoteWithTimer() {
  noteWithTimer.value = true
  note.value = {
    title: '',
    content: '',
  }
  showNoteModal.value = true
}

// Call Logs
const showCallLogModal = ref(false)
const callLog = ref({})
const referenceDoc = ref({})

function createCallLog() {
  let doctype = props.doctype
  let docname = props.doc?.name
  referenceDoc.value = { ...props.doc }
  callLog.value = {
    reference_doctype: doctype,
    reference_docname: docname,
  }
  showCallLogModal.value = true
}

// common
const route = useRoute()
const router = useRouter()

function redirect(tabName) {
  if (route.name == 'Lead' || route.name == 'Deal') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showEvent,
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  showNoteWithTimer,
  createCallLog,
})
</script>
