<template>
  <div class="flex flex-col h-full">
    <!-- Tab Navigation -->
    <div class="flex border-b dark:border-gray-700 px-4 pt-3">
      <button
        @click="activeTab = 'erstellen'"
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px"
        :class="activeTab === 'erstellen'
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
      >
        Angebot erstellen
      </button>
      <button
        @click="activeTab = 'angebote'"
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px flex items-center gap-1.5"
        :class="activeTab === 'angebote'
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
      >
        Erstellte Angebote
        <span
          v-if="angebote.length"
          class="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-xs font-medium rounded-full"
          :class="activeTab === 'angebote'
            ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400'
            : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'"
        >
          {{ angebote.length }}
        </span>
      </button>
    </div>

    <!-- Tab: Angebot erstellen -->
    <div v-show="activeTab === 'erstellen'" class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- Mitarbeiter -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mitarbeiter</label>
        <div class="text-sm text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-800 px-3 py-2 rounded-md">
          {{ currentMitarbeiter || 'Wird geladen...' }}
        </div>
      </div>

      <!-- AMIS-PDF Upload -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">AMIS-Angebot (PDF) *</label>
        <div
          class="border-2 border-dashed rounded-md p-4 text-center cursor-pointer transition-colors"
          :class="selectedFile
            ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'"
          @click="selectFile"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <input ref="fileInput" type="file" accept=".pdf" class="hidden" @change="handleFileSelect" />
          <div v-if="!selectedFile" class="text-gray-500 dark:text-gray-400">
            <svg class="mx-auto h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-1 text-sm">PDF hierher ziehen oder klicken</p>
          </div>
          <div v-else class="text-green-600 dark:text-green-400">
            <svg class="mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="mt-1 text-sm font-medium">{{ selectedFile.name }}</p>
            <button @click.stop="clearFile" class="mt-1 text-xs text-red-500 hover:text-red-700">Entfernen</button>
          </div>
        </div>
      </div>

      <!-- Extrahierte Daten Vorschau -->
      <div v-if="extractedData" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 space-y-2">
        <h4 class="text-sm font-semibold text-blue-800 dark:text-blue-300">Erkannte Daten</h4>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">Kunde:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-100">{{ extractedData.customer_name || '–' }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Datum:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-100">{{ extractedData.created_date || '–' }}</span>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Rasse:</span>
            <span class="ml-1 text-gray-900 dark:text-gray-100">{{ extractedData.horse_breed || '–' }}</span>
          </div>
          <div class="col-span-2" v-if="extractedData.beitrag">
            <span class="text-gray-500 dark:text-gray-400">Beitrag (10% SB):</span>
            <span class="ml-1 font-medium text-gray-900 dark:text-gray-100">{{ extractedData.beitrag }}</span>
          </div>
        </div>
      </div>

      <!-- Pferdename (auto-populated from Lead) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Pferdename *</label>
        <!-- Warning when tiername is missing from Lead -->
        <div
          v-if="!props.tiername"
          class="mb-2 flex items-start gap-2 p-2.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-md"
        >
          <svg class="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
          </svg>
          <span class="text-xs text-amber-700 dark:text-amber-400">Tiername fehlt im Lead. Bitte zuerst im Lead unter "Tier-Daten" eintragen.</span>
        </div>
        <!-- Read-only display when tiername comes from Lead -->
        <div v-if="props.tiername" class="relative">
          <div class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 text-sm">
            {{ horseName }}
          </div>
          <span class="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-1.5 py-0.5 rounded">
            aus Lead
          </span>
        </div>
        <!-- Fallback: editable input if no tiername in Lead -->
        <input
          v-else
          v-model="horseName"
          type="text"
          placeholder="z.B. Luna, Blitz, Shadow..."
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Beitraege (Selbstbeteiligung) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Beiträge (optional)</label>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <span class="text-xs text-gray-500 dark:text-gray-400 block mb-1">20% SB</span>
            <input
              v-model="beitrag20"
              type="text"
              placeholder="z.B. 195,50"
              class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <span class="text-xs text-gray-500 dark:text-gray-400 block mb-1">10% SB</span>
            <input
              v-model="beitrag10"
              type="text"
              placeholder="z.B. 240,20"
              class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <span class="text-xs text-gray-500 dark:text-gray-400 block mb-1">Keine SB</span>
            <input
              v-model="beitrag0"
              type="text"
              placeholder="z.B. 310,80"
              class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <!-- KI-Rasseinfo -->
      <div v-if="extractedData && extractedData.horse_breed">
        <div class="flex items-center justify-between mb-1">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">KI-Rasseinfo</label>
          <button
            @click="fetchBreedInfo"
            :disabled="isLoadingBreed"
            class="text-xs px-2 py-1 rounded text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
          >
            <span v-if="isLoadingBreed">Wird geladen...</span>
            <span v-else>{{ breedInfo ? 'Neu generieren' : 'Generieren' }}</span>
          </button>
        </div>
        <textarea
          v-model="breedInfo"
          rows="3"
          placeholder="KI-generierter Text für das Deckblatt (optional)"
          class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p class="text-xs text-gray-400 mt-1">{{ breedInfo ? breedInfo.length + '/260 Zeichen' : '' }}</p>
      </div>

      <!-- Angebot erstellen -->
      <button
        @click="generateAngebot"
        :disabled="!canGenerate || isGenerating"
        class="w-full py-2.5 px-4 rounded-md text-white font-medium transition-colors"
        :class="canGenerate && !isGenerating ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'"
      >
        <span v-if="isGenerating" class="flex items-center justify-center">
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Wird erstellt...
        </span>
        <span v-else>Angebot erstellen</span>
      </button>

      <!-- Status -->
      <div v-if="statusMessage" :class="statusClass" class="p-3 rounded-md text-sm">
        {{ statusMessage }}
      </div>
    </div>

    <!-- Tab: Erstellte Angebote -->
    <div v-show="activeTab === 'angebote'" class="flex-1 overflow-y-auto p-4">
      <div v-if="angebote.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg class="h-12 w-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-sm">Noch keine Angebote erstellt</p>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="angebot in angebote"
          :key="angebot.name"
          class="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <svg class="h-8 w-8 text-red-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
          </svg>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{{ angebot.file_name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ formatDate(angebot.creation) }}</p>
          </div>
          <!-- Kopieren Button -->
          <button
            @click="openCopyDialog(angebot)"
            class="ml-2 p-2 text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-md transition-colors"
            title="E-Mail-Text kopieren"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
          </button>
          <!-- Download Button -->
          <a
            :href="angebot.file_url"
            download
            class="ml-2 p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-md transition-colors"
            title="Herunterladen"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- AngebotCopyDialog fuer Angebote aus der Liste -->
  <AngebotCopyDialog
    v-model="showCopyDialog"
    :lead-id="leadId"
    :file-data="selectedAngebotFile"
  />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { createResource } from 'frappe-ui'
import AngebotCopyDialog from '@/components/AngebotCopyDialog.vue'

const props = defineProps({
  leadId: { type: String, required: true },
  tiername: { type: String, default: '' }
})

const emit = defineEmits(['angebotCreated'])

const activeTab = ref('erstellen')
const horseName = ref('')
const selectedFile = ref(null)
const fileBase64 = ref('')
const currentMitarbeiter = ref('')
const isGenerating = ref(false)
const statusMessage = ref('')
const statusType = ref('')
const angebote = ref([])
const fileInput = ref(null)
const extractedData = ref(null)
const isExtracting = ref(false)
const breedInfo = ref('')
const isLoadingBreed = ref(false)
const beitrag20 = ref('')
const beitrag10 = ref('')
const beitrag0 = ref('')

// Copy dialog state
const showCopyDialog = ref(false)
const selectedAngebotFile = ref(null)

const canGenerate = computed(() => horseName.value.trim() && selectedFile.value && currentMitarbeiter.value)
const statusClass = computed(() =>
  statusType.value === 'success'
    ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
    : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
)

// Auto-populate horseName from Lead's tiername
function syncTiername(val) {
  if (val) {
    horseName.value = val
  }
}

// Watch for prop changes (e.g. if Lead data loads after component mounts)
watch(() => props.tiername, (newVal) => {
  syncTiername(newVal)
}, { immediate: true })

const mitarbeiterResource = createResource({
  url: 'pferdeversicherung.api.get_current_user_mitarbeiter',
  auto: true,
  onSuccess: (data) => { currentMitarbeiter.value = data || 'Nicht konfiguriert' }
})

const angeboteResource = createResource({
  url: 'pferdeversicherung.api.get_lead_angebote',
  makeParams: () => ({ lead_id: props.leadId }),
  auto: true,
  onSuccess: (data) => { angebote.value = data || [] }
})

function openCopyDialog(angebot) {
  selectedAngebotFile.value = {
    file_name: angebot.file_name,
    file_url: angebot.file_url,
    file_doc_name: angebot.name,
  }
  showCopyDialog.value = true
}

function selectFile() { fileInput.value?.click() }

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') processFile(file)
}

function handleDrop(event) {
  const file = event.dataTransfer.files[0]
  if (file && file.type === 'application/pdf') processFile(file)
}

function processFile(file) {
  selectedFile.value = file
  extractedData.value = null
  breedInfo.value = ''
  const reader = new FileReader()
  reader.onload = (e) => {
    fileBase64.value = e.target.result.split(',')[1]
    extractPreview()
  }
  reader.readAsDataURL(file)
}

function clearFile() {
  selectedFile.value = null
  fileBase64.value = ''
  extractedData.value = null
  breedInfo.value = ''
  beitrag10.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function extractPreview() {
  if (!fileBase64.value) return
  isExtracting.value = true
  try {
    const res = await createResource({
      url: 'pferdeversicherung.api.preview_amis_pdf',
      params: { amis_pdf_base64: fileBase64.value }
    }).fetch()
    if (res.success && res.data) {
      extractedData.value = res.data
      if (res.data.beitrag) {
        beitrag10.value = res.data.beitrag.replace(' EUR', '').replace(' €', '')
      }
    }
  } catch (e) {
    console.error('Vorschau-Extraktion fehlgeschlagen:', e)
  } finally {
    isExtracting.value = false
  }
}

async function fetchBreedInfo() {
  const breed = extractedData.value?.horse_breed
  if (!breed) return
  isLoadingBreed.value = true
  try {
    const res = await createResource({
      url: 'pferdeversicherung.api.get_breed_info',
      params: { breed_name: breed, horse_name: horseName.value || '' }
    }).fetch()
    if (res.success && res.breed_info) {
      breedInfo.value = res.breed_info
    }
  } catch (e) {
    console.error('Rasseinfo fehlgeschlagen:', e)
  } finally {
    isLoadingBreed.value = false
  }
}

async function generateAngebot() {
  if (!canGenerate.value) return
  isGenerating.value = true
  statusMessage.value = ''
  try {
    const res = await createResource({
      url: 'pferdeversicherung.api.generate_angebot',
      params: {
        lead_id: props.leadId,
        horse_name: horseName.value,
        amis_pdf_base64: fileBase64.value,
        mitarbeiter: currentMitarbeiter.value,
        beitrag_20: beitrag20.value,
        beitrag_10: beitrag10.value,
        beitrag_0: beitrag0.value,
        breed_info: breedInfo.value,
      }
    }).fetch()
    if (res.success) {
      statusType.value = 'success'
      statusMessage.value = res.message
      angeboteResource.reload()
      // Emit event to open email with attachment
      emit('angebotCreated', {
        file_name: res.file_name,
        file_url: res.file_url,
        file_doc_name: res.file_doc_name,
      })
      // Only reset horseName if it was manually entered (not from Lead)
      if (!props.tiername) {
        horseName.value = ''
      }
      beitrag20.value = ''
      beitrag10.value = ''
      beitrag0.value = ''
      breedInfo.value = ''
      clearFile()
    } else {
      statusType.value = 'error'
      statusMessage.value = res.message || 'Fehler aufgetreten'
    }
  } catch (error) {
    statusType.value = 'error'
    statusMessage.value = error.message || 'Fehler aufgetreten'
  } finally {
    isGenerating.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

watch(horseName, (newVal) => {
  if (newVal && newVal.trim().length >= 2 && extractedData.value?.horse_breed && !breedInfo.value) {
    fetchBreedInfo()
  }
})

onMounted(() => {
  mitarbeiterResource.fetch()
  angeboteResource.fetch()
})
</script>
