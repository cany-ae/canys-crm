<template>
  <div v-show="false" class="flex justify-between gap-3 border-t px-4 py-2.5 sm:px-10">
    <div class="flex gap-1.5">
      <Button
        ref="sendEmailRef"
        variant="ghost"
        :class="[
          showEmailBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        :label="__('Reply')"
        :iconLeft="Email2Icon"
        @click="toggleEmailBox()"
      />
      <Button
        variant="ghost"
        :label="__('Comment')"
        :class="[
          showCommentBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        :iconLeft="CommentIcon"
        @click="toggleCommentBox()"
      />
    </div>
  </div>
  <div
    v-show="showEmailBox"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discardButtonProps="{
        onClick: discardEmail,
      }"
      :editable="showEmailBox"
      v-model="doc"
      v-model:attachments="attachments"
      :doctype="doctype"
      :subject="subject"
      :placeholder="
        __('Hi John, \n\nCan you please provide more details on this...')
      "
    />
  </div>
  <div v-show="showCommentBox">
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discardButtonProps="{
        onClick: async () => {
          await deleteAttachedFiles()
          showCommentBox = false
          newComment = ''
        },
      }"
      :editable="showCommentBox"
      v-model="doc"
      v-model:attachments="attachments"
      :doctype="doctype"
      :placeholder="__('@John, can you please check this?')"
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import { capture } from '@/telemetry'
import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'
import { useDebounceFn } from '@vueuse/core'
import { call, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const doc = defineModel()
const reload = defineModel('reload')

const emit = defineEmits(['scroll'])

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const showEmailBox = ref(false)
const showCommentBox = ref(false)
const newEmail = useStorage(
  `emailBoxContent-${getUser().email}-${props.doctype}-${doc.value.name}`,
  '',
)
const newComment = useStorage(
  `commentBoxContent-${getUser().email}-${props.doctype}-${doc.value.name}`,
  '',
)
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)
const sendEmailRef = ref(null)
const isAngebotFlow = ref(false)
const skipSignature = ref(false)

// --- Draft System ---
const draftsKey = `emailDrafts-${getUser().email}-${props.doctype}-${doc.value.name}`
const drafts = useStorage(draftsKey, [], localStorage, {
  serializer: {
    read: (v) => v ? JSON.parse(v) : [],
    write: (v) => JSON.stringify(v),
  },
})

// ID des aktuell bearbeiteten Drafts (null = kein aktiver Draft)
const currentDraftId = ref(null)

// Flag: Draft-Save unterdruecken (z.B. nach Send/Reset)
const suppressDraftSave = ref(false)

const attachments = useStorage(
  `attachments-${getUser().email}-${props.doctype}-${doc.value.name}`,
  [],
  localStorage,
  {
    serializer: {
      read: (v) => v ? JSON.parse(v) : [],
      write: (v) => JSON.stringify(v)
    }
  }
)

const subject = computed(() => {
  let prefix = ''
  if (doc.value?.lead_name) {
    prefix = doc.value.lead_name
  } else if (doc.value?.organization) {
    prefix = doc.value.organization
  }
  return `${prefix} (#${doc.value.name})`
})

const signature = createResource({
  url: 'crm.api.get_user_signature',
  cache: 'user-email-signature',
  auto: true,
})

function setSignature(editor) {
  if (!signature.data) return
  signature.data = signature.data.replace(/\n/g, '<br>')
  let emailContent = editor.getHTML()
  emailContent = emailContent.startsWith('<p></p>')
    ? emailContent.slice(7)
    : emailContent
  editor.commands.setContent(signature.data + emailContent)
  editor.commands.focus('start')
}

// --- Signature-Watcher ---
watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      let editor = newEmailEditor.value.editor
      editor.commands.focus()
      if (!skipSignature.value) {
        setSignature(editor)
      }
      skipSignature.value = false
    }
  },
)

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      newCommentEditor.value.editor.commands.focus()
    }
  },
)

// --- Computed ---
const commentEmpty = computed(() => {
  return !newComment.value || newComment.value === '<p></p>'
})

const emailEmpty = computed(() => {
  return (
    !newEmail.value ||
    newEmail.value === '<p></p>' ||
    !newEmailEditor.value?.toEmails?.length
  )
})

// Prueft ob der Compose tatsaechlich User-Content hat (nicht nur Signatur)
function hasComposableContent() {
  const hasContent = newEmail.value && newEmail.value !== '<p></p>'
  const hasAttachments = attachments.value && attachments.value.length > 0
  const editorRef = newEmailEditor.value
  const hasCustomSubject = editorRef?.subject && editorRef.subject !== subject.value
  return hasContent || hasAttachments || hasCustomSubject
}

// --- Draft Save/Update ---
function saveOrUpdateDraft() {
  if (suppressDraftSave.value) return
  if (!showEmailBox.value) return
  if (!hasComposableContent()) return

  const editorRef = newEmailEditor.value
  const draftData = {
    subject: editorRef?.subject || '',
    content: newEmail.value || '',
    toEmails: editorRef?.toEmails || [],
    ccEmails: editorRef?.ccEmails || [],
    bccEmails: editorRef?.bccEmails || [],
    attachmentsList: [...(attachments.value || [])],
    updated_at: new Date().toISOString(),
  }

  if (currentDraftId.value) {
    // Bestehenden Draft aktualisieren
    const idx = drafts.value.findIndex(d => d.id === currentDraftId.value)
    if (idx !== -1) {
      const updated = { ...drafts.value[idx], ...draftData }
      const newDrafts = [...drafts.value]
      newDrafts[idx] = updated
      drafts.value = newDrafts
      return
    }
  }

  // Neuen Draft erstellen
  const newId = Date.now()
  const draft = {
    id: newId,
    ...draftData,
    created_at: new Date().toISOString(),
  }
  const currentDrafts = [...drafts.value]
  currentDrafts.unshift(draft)
  if (currentDrafts.length > 10) currentDrafts.pop()
  drafts.value = currentDrafts
  currentDraftId.value = newId
}

// Debounced Auto-Save: 1.5 Sekunden nach letzter Aenderung
const debouncedSaveDraft = useDebounceFn(() => {
  saveOrUpdateDraft()
}, 1500)

// --- Auto-Save Watcher: Content ---
watch(
  () => newEmail.value,
  (val, oldVal) => {
    if (suppressDraftSave.value) return
    if (!showEmailBox.value) return
    if (val !== oldVal) {
      debouncedSaveDraft()
    }
  },
)

// --- Auto-Save Watcher: Attachments ---
watch(
  () => attachments.value,
  () => {
    if (suppressDraftSave.value) return
    if (!showEmailBox.value) return
    debouncedSaveDraft()
  },
  { deep: true }
)

// --- Mail senden ---
async function sendMail() {
  let recipients = newEmailEditor.value.toEmails
  let subject = newEmailEditor.value.subject
  let cc = newEmailEditor.value.ccEmails || []
  let bcc = newEmailEditor.value.bccEmails || []

  if (attachments.value.length) {
    capture('email_attachments_added')
  }
  await call('frappe.core.doctype.communication.email.make', {
    recipients: recipients.join(', '),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(', '),
    bcc: bcc.join(', '),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.name,
    send_email: 1,
    sender: getUser().email,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function sendComment() {
  let comment = await call('frappe.desk.form.utils.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    content: newComment.value,
    comment_email: getUser().email,
    comment_by: getUser()?.full_name || undefined,
  })
  if (comment && attachments.value.length) {
    capture('comment_attachments_added')
    await call('crm.api.comment.add_attachments', {
      name: comment.name,
      attachments: attachments.value.map((x) => x.name),
    })
  }
}

async function deleteAttachedFiles() {
  if (!attachments.value || attachments.value.length === 0) return

  const deletePromises = attachments.value.map(async (file) => {
    try {
      await call('frappe.client.delete', {
        doctype: 'File',
        name: file.name,
      })
    } catch (error) {
      console.warn(`Failed to delete file ${file.name}:`, error)
    }
  })

  await Promise.all(deletePromises)
  attachments.value = []
}

async function submitEmail() {
  if (emailEmpty.value) return

  // Draft loeschen nach Senden
  suppressDraftSave.value = true
  if (currentDraftId.value) {
    drafts.value = drafts.value.filter(d => d.id !== currentDraftId.value)
    currentDraftId.value = null
  }

  showEmailBox.value = false
  await sendMail()
  newEmail.value = ''
  attachments.value = []
  isAngebotFlow.value = false
  suppressDraftSave.value = false
  reload.value = true
  emit('scroll')
  capture('email_sent', { doctype: props.doctype })
  updateOnboardingStep('send_first_email')
}

async function submitComment() {
  if (commentEmpty.value) return
  showCommentBox.value = false
  await sendComment()
  newComment.value = ''
  attachments.value = []
  reload.value = true
  emit('scroll')
  capture('comment_sent', { doctype: props.doctype })
  updateOnboardingStep('add_first_comment')
}

// --- Ablegen (Discard) ---
async function discardEmail() {
  // Draft speichern bevor Inhalt geloescht wird
  saveOrUpdateDraft()
  suppressDraftSave.value = true
  currentDraftId.value = null
  await deleteAttachedFiles()
  showEmailBox.value = false
  if (newEmailEditor.value) {
    newEmailEditor.value.subject = subject.value
    newEmailEditor.value.toEmails = doc.value.email ? [doc.value.email] : []
    newEmailEditor.value.ccEmails = []
    newEmailEditor.value.bccEmails = []
    newEmailEditor.value.cc = false
    newEmailEditor.value.bcc = false
  }
  newEmail.value = ''
  attachments.value = []
  suppressDraftSave.value = false
}

// --- Neue E-Mail (immer leer) ---
function openNewEmail() {
  if (showCommentBox.value) {
    showCommentBox.value = false
  }
  // Aktuellen Compose als Draft speichern
  saveOrUpdateDraft()

  // Reset
  suppressDraftSave.value = true
  currentDraftId.value = null
  newEmail.value = ''
  attachments.value = []
  isAngebotFlow.value = false
  skipSignature.value = true
  showEmailBox.value = true
  suppressDraftSave.value = false

  nextTick(() => {
    const editorRef = newEmailEditor.value
    if (editorRef) {
      editorRef.subject = subject.value
      editorRef.toEmails = doc.value.email ? [doc.value.email] : []
      editorRef.ccEmails = []
      editorRef.bccEmails = []
      editorRef.cc = false
      editorRef.bcc = false
      const editor = editorRef.editor
      if (editor) {
        editor.commands.setContent('')
        setSignature(editor)
        editor.commands.focus('start')
      }
    }
  })
}

// --- Toggle (Reply-Button) ---
function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false
  }
  if (!showEmailBox.value) {
    // Beim Oeffnen: Wenn nicht vom Angebot-Flow, frisch starten
    if (!isAngebotFlow.value) {
      saveOrUpdateDraft()
      suppressDraftSave.value = true
      currentDraftId.value = null
      newEmail.value = ''
      attachments.value = []
      suppressDraftSave.value = false
      nextTick(() => {
        const editor = newEmailEditor.value
        if (editor) {
          editor.subject = subject.value
          editor.toEmails = doc.value.email ? [doc.value.email] : []
          editor.ccEmails = []
          editor.bccEmails = []
          editor.cc = false
          editor.bcc = false
        }
      })
    }
    isAngebotFlow.value = false
  } else {
    // Beim Schliessen: Draft speichern
    saveOrUpdateDraft()
    currentDraftId.value = null
  }
  showEmailBox.value = !showEmailBox.value
}

// --- Draft laden ---
function loadDraft(draft) {
  showCommentBox.value = false
  skipSignature.value = true
  isAngebotFlow.value = true
  suppressDraftSave.value = true
  showEmailBox.value = true

  // Draft aus Liste entfernen und als aktiv setzen
  currentDraftId.value = draft.id

  nextTick(() => {
    const editorRef = newEmailEditor.value
    if (editorRef) {
      editorRef.subject = draft.subject || subject.value
      editorRef.toEmails = draft.toEmails || []
      editorRef.ccEmails = draft.ccEmails || []
      editorRef.bccEmails = draft.bccEmails || []
      const editor = editorRef.editor
      if (editor) {
        editor.commands.setContent(draft.content || '')
      }
    }
    newEmail.value = draft.content || ''
    attachments.value = draft.attachmentsList || []
    isAngebotFlow.value = false
    suppressDraftSave.value = false
  })
}

// --- Draft loeschen ---
function deleteDraft(draftId) {
  drafts.value = drafts.value.filter(d => d.id !== draftId)
  if (currentDraftId.value === draftId) {
    currentDraftId.value = null
  }
}

// --- Toggle Comment ---
function toggleCommentBox() {
  if (showEmailBox.value) {
    // E-Mail Box schliessen → Draft speichern
    saveOrUpdateDraft()
    currentDraftId.value = null
    showEmailBox.value = false
  }
  showCommentBox.value = !showCommentBox.value
}

// --- Angebot-Flow: Mail vorbefuellen + sofort Draft ---
function handleAngebotEmail(e) {
  const { fileData, lead } = e.detail

  // Vorhandenen Compose speichern
  saveOrUpdateDraft()

  suppressDraftSave.value = true
  currentDraftId.value = null
  isAngebotFlow.value = true
  showCommentBox.value = false
  newEmail.value = ''
  attachments.value = []
  showEmailBox.value = true
  suppressDraftSave.value = false

  nextTick(() => {
    const editor = newEmailEditor.value
    if (editor) {
      editor.subject = 'Ihr Angebot - ' + (lead.lead_name || lead.first_name || '')
      if (lead.email) {
        editor.toEmails = [lead.email]
      }
    }
    attachments.value = [{
      name: fileData.file_doc_name,
      file_name: fileData.file_name,
      file_url: fileData.file_url,
    }]

    // Sofort als Draft speichern (Offer-Flow)
    nextTick(() => {
      saveOrUpdateDraft()
    })
  })
}

// --- Lifecycle ---
onMounted(() => {
  window.addEventListener('open-email-with-angebot', handleAngebotEmail)
  // beforeunload: Draft speichern wenn Browser/Tab geschlossen wird
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('open-email-with-angebot', handleAngebotEmail)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  // Component wird unmounted (Tab-Wechsel, Route-Wechsel) → Draft speichern
  if (showEmailBox.value) {
    saveOrUpdateDraft()
  }
})

function handleBeforeUnload() {
  if (showEmailBox.value) {
    saveOrUpdateDraft()
  }
}

defineExpose({
  attachments,
  show: showEmailBox,
  showComment: showCommentBox,
  editor: newEmailEditor,
  drafts,
  loadDraft,
  deleteDraft,
  openNewEmail,
})
</script>
