<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Notiz bearbeiten') : __('Notiz erstellen') }}
        </h3>
        <Button
          v-if="_note?.reference_docname"
          size="sm"
          :label="
            _note.reference_doctype == 'CRM Deal'
              ? __('Deal öffnen')
              : __('Lead öffnen')
          "
          :iconRight="ArrowUpRightIcon"
          @click="redirect()"
        />
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            ref="title"
            :label="__('Titel')"
            v-model="_note.title"
            :placeholder="__('z.B. Gespräch mit Kunde')"
            required
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ __('Inhalt') }}</div>
          <TextEditor
            variant="outline"
            ref="content"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_note.content"
            @change="(val) => (_note.content = val)"
            :placeholder="__('Notizinhalt eingeben...')"
          />
        </div>

        <!-- Optionaler Erinnerungs-Timer -->
        <div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="flex items-center gap-1.5 text-xs font-medium transition-colors"
              :class="showErinnerung ? 'text-blue-600' : 'text-ink-gray-4 hover:text-ink-gray-7'"
              @click="toggleErinnerung"
            >
              <svg
                class="h-3.5 w-3.5"
                :class="showErinnerung ? 'text-blue-600' : 'text-ink-gray-4'"
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
              {{ showErinnerung ? __('Erinnerung entfernen') : __('Erinnerung hinzufügen') }}
            </button>
          </div>

          <div v-if="showErinnerung" class="mt-2">
            <label class="mb-1 block text-xs font-medium text-ink-gray-5">
              {{ __('Erinnerung am') }}
              <span class="text-ink-gray-4 font-normal ml-1">({{ __('optional') }})</span>
            </label>
            <input
              v-model="_note.erinnerung"
              type="datetime-local"
              class="w-full rounded border border-outline-gray-2 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="editMode ? __('Aktualisieren') : __('Erstellen')"
          variant="solid"
          @click="updateNote"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { capture } from '@/telemetry'
import { TextEditor, call } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  note: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
  withTimer: {
    type: Boolean,
    default: false,
  },
})

const show = defineModel()
const notes = defineModel('reloadNotes')

const emit = defineEmits(['after'])

const router = useRouter()

const { updateOnboardingStep } = useOnboarding('frappecrm')

const error = ref(null)
const title = ref(null)
const editMode = ref(false)
const showErinnerung = ref(false)
let _note = ref({})

function toggleErinnerung() {
  showErinnerung.value = !showErinnerung.value
  if (!showErinnerung.value) {
    _note.value.erinnerung = null
  }
}

async function updateNote() {
  if (_note.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'FCRM Note',
      name: _note.value.name,
      fieldname: {
        title: _note.value.title,
        content: _note.value.content,
        erinnerung: _note.value.erinnerung || null,
      },
    })
    if (d.name) {
      notes.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call(
      'frappe.client.insert',
      {
        doc: {
          doctype: 'FCRM Note',
          title: _note.value.title,
          content: _note.value.content,
          erinnerung: _note.value.erinnerung || null,
          reference_doctype: props.doctype,
          reference_docname: props.doc || '',
        },
      },
      {
        onError: (err) => {
          if (err.error.exc_type == 'MandatoryError') {
            error.value = 'Titel ist Pflichtfeld'
          }
        },
      },
    )
    if (d.name) {
      updateOnboardingStep('create_first_note')
      capture('note_created')
      notes.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
}

function redirect() {
  if (!props.note?.reference_docname) return
  let name = props.note.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: props.note.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.note.reference_docname }
  }
  router.push({ name: name, params: params })
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    showErinnerung.value = false
    nextTick(() => {
      title.value?.el?.focus()
      _note.value = { ...props.note }
      if (_note.value.title || _note.value.content) {
        editMode.value = true
      }
      // If withTimer prop set, pre-activate the reminder field
      if (props.withTimer && !_note.value.erinnerung) {
        showErinnerung.value = true
      }
      // If existing note has erinnerung, show the field
      if (_note.value.erinnerung) {
        showErinnerung.value = true
        // Convert Frappe datetime format (YYYY-MM-DD HH:MM:SS) to datetime-local format (YYYY-MM-DDTHH:MM)
        const dt = _note.value.erinnerung
        if (dt && dt.includes(' ')) {
          _note.value.erinnerung = dt.replace(' ', 'T').substring(0, 16)
        }
      }
    })
  },
)
</script>
