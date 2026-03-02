<template>
  <Dialog v-model="show" :options="{ title: 'Angebot per E-Mail versenden', size: '2xl' }">
    <template #body-content>
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500"></div>
        <span class="ml-3 text-sm text-gray-500">Vorlage wird geladen...</span>
      </div>
      <div v-else-if="loadError" class="p-4">
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          <p class="font-medium mb-1">Vorlage konnte nicht geladen werden</p>
          <p>{{ loadError }}</p>
          <button @click="loadTemplate" class="mt-3 px-3 py-1.5 bg-red-600 text-white rounded-md text-xs font-medium hover:bg-red-700 transition-colors">
            Erneut versuchen
          </button>
        </div>
      </div>
      <div v-else class="space-y-5 p-2">

        <!-- Empfänger -->
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Empfänger</label>
          <div class="relative">
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 pr-10 text-sm font-medium text-gray-800 select-all">
              {{ emailData.empfaenger || 'Keine E-Mail hinterlegt' }}
            </div>
            <button
              @click.stop="copyField(emailData.empfaenger, 'empfaenger')"
              :disabled="!emailData.empfaenger"
              class="absolute top-2.5 right-2.5 p-1.5 rounded-md transition-colors"
              :class="!emailData.empfaenger
                ? 'text-gray-300 cursor-not-allowed'
                : copyStatus.empfaenger === 'ok'
                  ? 'text-green-500'
                  : copyStatus.empfaenger === 'fail'
                    ? 'text-red-500'
                    : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'"
              :title="copyTitle('empfaenger')"
            >
              <FeatherIcon
                :name="copyStatus.empfaenger === 'ok' ? 'check' : copyStatus.empfaenger === 'fail' ? 'x' : 'clipboard'"
                class="h-4 w-4"
              />
            </button>
          </div>
        </div>

        <!-- Betreff -->
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Betreff</label>
          <div class="relative">
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 pr-10 text-sm font-medium text-gray-800 select-all">
              {{ emailData.betreff }}
            </div>
            <button
              @click.stop="copyField(emailData.betreff, 'betreff')"
              :disabled="!emailData.betreff"
              class="absolute top-2.5 right-2.5 p-1.5 rounded-md transition-colors"
              :class="!emailData.betreff
                ? 'text-gray-300 cursor-not-allowed'
                : copyStatus.betreff === 'ok'
                  ? 'text-green-500'
                  : copyStatus.betreff === 'fail'
                    ? 'text-red-500'
                    : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'"
              :title="copyTitle('betreff')"
            >
              <FeatherIcon
                :name="copyStatus.betreff === 'ok' ? 'check' : copyStatus.betreff === 'fail' ? 'x' : 'clipboard'"
                class="h-4 w-4"
              />
            </button>
          </div>
        </div>

        <!-- E-Mail Text -->
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">E-Mail Text</label>
          <div class="relative">
            <div class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-4 pr-10 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap select-all overflow-y-auto" style="min-height: 200px; max-height: 350px;">{{ emailData.inhalt_plain }}</div>
            <button
              @click.stop="copyField(emailData.inhalt_plain, 'inhalt')"
              :disabled="!emailData.inhalt_plain"
              class="absolute top-2.5 right-2.5 p-1.5 rounded-md transition-colors"
              :class="!emailData.inhalt_plain
                ? 'text-gray-300 cursor-not-allowed'
                : copyStatus.inhalt === 'ok'
                  ? 'text-green-500'
                  : copyStatus.inhalt === 'fail'
                    ? 'text-red-500'
                    : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'"
              :title="copyTitle('inhalt')"
            >
              <FeatherIcon
                :name="copyStatus.inhalt === 'ok' ? 'check' : copyStatus.inhalt === 'fail' ? 'x' : 'clipboard'"
                class="h-4 w-4"
              />
            </button>
          </div>
        </div>

        <!-- Angebot Datei -->
        <div>
          <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Angebot (Anhang)</label>
          <div class="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
            <svg class="h-8 w-8 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
            </svg>
            <span class="flex-1 text-sm font-medium text-gray-800 truncate">{{ fileData?.file_name || 'Angebot.pdf' }}</span>
            <div class="flex items-center gap-2">
              <!-- Herunterladen -->
              <a
                v-if="fileData?.file_url"
                :href="fileData.file_url"
                download
                class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                <FeatherIcon name="download" class="h-4 w-4" />
                Herunterladen
              </a>
            </div>
          </div>
        </div>

        <!-- Aktionen -->
        <div class="pt-2 space-y-2">
          <!-- Alles kopieren (Betreff + Text) -->
          <button
            @click="copyAll"
            :disabled="!emailData.betreff && !emailData.inhalt_plain"
            class="w-full flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-semibold transition-colors"
            :class="allStatus === 'ok'
              ? 'bg-green-600 text-white'
              : allStatus === 'fail'
                ? 'bg-red-600 text-white'
                : (!emailData.betreff && !emailData.inhalt_plain)
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'"
          >
            <FeatherIcon :name="allStatus === 'ok' ? 'check' : allStatus === 'fail' ? 'x' : 'clipboard'" class="h-4 w-4" />
            {{ allStatus === 'ok' ? 'Betreff + Text kopiert!' : allStatus === 'fail' ? 'Kopieren fehlgeschlagen' : 'Betreff + Text kopieren' }}
          </button>
          <p class="text-center text-xs text-gray-400">
            Kopiere die Daten in dein E-Mail-Programm und hänge das Angebot als Datei an.
          </p>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Dialog, FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  leadId: { type: String, required: true },
  fileData: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])

const show = ref(props.modelValue)
const loading = ref(false)
const loadError = ref('')
const emailData = ref({ betreff: '', inhalt_plain: '', inhalt_html: '', empfaenger: '' })

// Track copy status per field: '' = idle, 'ok' = success, 'fail' = failed
const copyStatus = ref({ empfaenger: '', betreff: '', inhalt: '' })
const allStatus = ref('')

function copyTitle(field) {
  if (copyStatus.value[field] === 'ok') return 'Kopiert!'
  if (copyStatus.value[field] === 'fail') return 'Kopieren fehlgeschlagen'
  return 'Kopieren'
}

watch(() => props.modelValue, (val) => {
  show.value = val
  if (val) loadTemplate()
})
watch(show, (val) => emit('update:modelValue', val))

async function loadTemplate() {
  loading.value = true
  loadError.value = ''
  copyStatus.value = { empfaenger: '', betreff: '', inhalt: '' }
  allStatus.value = ''
  try {
    const data = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_angebot_email_vorlage',
      { lead_name: props.leadId }
    )
    if (data && (data.betreff || data.inhalt_plain)) {
      emailData.value = data
    } else {
      // API returned but with no meaningful data - use fallback
      console.warn('AngebotCopyDialog: API returned empty data, using fallback', data)
      emailData.value = {
        betreff: 'Ihr persönliches Angebot',
        inhalt_plain: 'Sehr geehrte Damen und Herren,\n\nanbei finden Sie Ihr persönliches Angebot.\n\nBei Fragen stehe ich Ihnen gerne zur Verfügung.\n\nMit freundlichen Grüßen',
        inhalt_html: '',
        empfaenger: data?.empfaenger || '',
      }
    }
  } catch (err) {
    console.error('AngebotCopyDialog: Failed to load template:', err)
    loadError.value = err.message || 'Unbekannter Fehler beim Laden der Vorlage'
  } finally {
    loading.value = false
  }
}

/**
 * Robust clipboard write with multiple fallback strategies.
 * Returns true on success, false on failure.
 */
async function writeToClipboard(text) {
  if (!text) return false

  // Strategy 1: Modern Clipboard API
  if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (e) {
      console.warn('AngebotCopyDialog: navigator.clipboard.writeText failed:', e)
    }
  }

  // Strategy 2: execCommand fallback with textarea
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0;'
    document.body.appendChild(ta)

    // iOS needs special handling
    const range = document.createRange()
    const selection = window.getSelection()
    selection.removeAllRanges()
    ta.select()
    ta.setSelectionRange(0, text.length)
    range.selectNodeContents(ta)
    selection.addRange(range)

    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    selection.removeAllRanges()

    if (ok) return true
    console.warn('AngebotCopyDialog: execCommand("copy") returned false')
  } catch (e) {
    console.warn('AngebotCopyDialog: execCommand fallback failed:', e)
  }

  return false
}

async function copyField(text, field) {
  if (!text) return
  const success = await writeToClipboard(text)
  copyStatus.value[field] = success ? 'ok' : 'fail'
  setTimeout(() => { copyStatus.value[field] = '' }, 2500)
}

async function copyAll() {
  const parts = []
  if (emailData.value.betreff) {
    parts.push('Betreff: ' + emailData.value.betreff)
  }
  if (emailData.value.inhalt_plain) {
    parts.push(emailData.value.inhalt_plain)
  }
  if (parts.length === 0) return

  const text = parts.join('\n\n')
  const success = await writeToClipboard(text)
  allStatus.value = success ? 'ok' : 'fail'
  setTimeout(() => { allStatus.value = '' }, 3000)
}

</script>
