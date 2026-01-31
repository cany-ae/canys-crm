<template>
  <div class="flex flex-col h-full p-4">
    <!-- Header -->
    <div class="mb-4">
      <h3 class="text-lg font-semibold text-gray-900">Invoice Tool</h3>
      <p class="text-sm text-gray-500">Create horse insurance invoices</p>
    </div>

    <!-- Form -->
    <div class="space-y-4 flex-1">
      <!-- Employee -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Employee
        </label>
        <div class="text-sm text-gray-900 bg-gray-100 px-3 py-2 rounded-md">
          {{ currentMitarbeiter || 'Loading...' }}
        </div>
      </div>

      <!-- Horse Name -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Horse Name *
        </label>
        <input
          v-model="horseName"
          type="text"
          placeholder="e.g. Blitz, Luna, Shadow..."
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <!-- AMIS-PDF Upload -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          AMIS Invoice (PDF) *
        </label>
        <div 
          class="border-2 border-dashed border-gray-300 rounded-md p-4 text-center cursor-pointer hover:border-blue-400 transition-colors"
          @click="selectFile"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".pdf"
            class="hidden"
            @change="handleFileSelect"
          />
          <div v-if="!selectedFile" class="text-gray-500">
            <svg class="mx-auto h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-1 text-sm">Drop PDF here or click to select</p>
          </div>
          <div v-else class="text-green-600">
            <svg class="mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="mt-1 text-sm font-medium">{{ selectedFile.name }}</p>
            <button 
              @click.stop="clearFile"
              class="mt-1 text-xs text-red-500 hover:text-red-700"
            >
              Remove
            </button>
          </div>
        </div>
      </div>

      <!-- Generate Button -->
      <button
        @click="generateAngebot"
        :disabled="!canGenerate || isGenerating"
        class="w-full py-2 px-4 rounded-md text-white font-medium transition-colors"
        :class="canGenerate && !isGenerating ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'"
      >
        <span v-if="isGenerating" class="flex items-center justify-center">
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Creating...
        </span>
        <span v-else>Create Invoice</span>
      </button>

      <!-- Status Message -->
      <div v-if="statusMessage" :class="statusClass" class="p-3 rounded-md text-sm">
        {{ statusMessage }}
      </div>
    </div>

    <!-- Created Invoices -->
    <div class="mt-6 border-t pt-4">
      <h4 class="text-sm font-medium text-gray-700 mb-2">Created Invoices</h4>
      <div v-if="angebote.length === 0" class="text-sm text-gray-500">
        No invoices created yet
      </div>
      <div v-else class="space-y-2 max-h-48 overflow-y-auto">
        <a
          v-for="angebot in angebote"
          :key="angebot.name"
          :href="angebot.file_url"
          target="_blank"
          class="flex items-center p-2 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
        >
          <svg class="h-5 w-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
          </svg>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ angebot.file_name }}</p>
            <p class="text-xs text-gray-500">{{ formatDate(angebot.creation) }}</p>
          </div>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  leadId: {
    type: String,
    required: true
  }
})

const horseName = ref('')
const selectedFile = ref(null)
const fileBase64 = ref('')
const currentMitarbeiter = ref('')
const isGenerating = ref(false)
const statusMessage = ref('')
const statusType = ref('')
const angebote = ref([])
const fileInput = ref(null)

const canGenerate = computed(() => {
  return horseName.value.trim() && selectedFile.value && currentMitarbeiter.value
})

const statusClass = computed(() => {
  return statusType.value === 'success' 
    ? 'bg-green-100 text-green-800' 
    : 'bg-red-100 text-red-800'
})

// Load employee
const mitarbeiterResource = createResource({
  url: 'pferdeversicherung.api.get_current_user_mitarbeiter',
  auto: true,
  onSuccess: (data) => {
    currentMitarbeiter.value = data || 'Not configured'
  }
})

// Load invoices
const angeboteResource = createResource({
  url: 'pferdeversicherung.api.get_lead_angebote',
  makeParams: () => ({ lead_id: props.leadId }),
  auto: true,
  onSuccess: (data) => {
    angebote.value = data || []
  }
})

function selectFile() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    processFile(file)
  }
}

function handleDrop(event) {
  const file = event.dataTransfer.files[0]
  if (file && file.type === 'application/pdf') {
    processFile(file)
  }
}

function processFile(file) {
  selectedFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    fileBase64.value = e.target.result.split(',')[1]
  }
  reader.readAsDataURL(file)
}

function clearFile() {
  selectedFile.value = null
  fileBase64.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function generateAngebot() {
  if (!canGenerate.value) return
  
  isGenerating.value = true
  statusMessage.value = ''
  
  try {
    const response = await createResource({
      url: 'pferdeversicherung.api.generate_angebot',
      params: {
        lead_id: props.leadId,
        horse_name: horseName.value,
        amis_pdf_base64: fileBase64.value,
        mitarbeiter: currentMitarbeiter.value
      }
    }).fetch()
    
    if (response.success) {
      statusType.value = 'success'
      statusMessage.value = response.message
      // Reload invoices
      angeboteResource.reload()
      // Reset form
      horseName.value = ''
      clearFile()
    } else {
      statusType.value = 'error'
      statusMessage.value = response.message || 'An error occurred'
    }
  } catch (error) {
    statusType.value = 'error'
    statusMessage.value = error.message || 'An error occurred'
  } finally {
    isGenerating.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  mitarbeiterResource.fetch()
  angeboteResource.fetch()
})
</script>
