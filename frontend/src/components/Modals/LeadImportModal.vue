<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Leads importieren') }}
          </h3>
          <Button variant="ghost" class="w-7" @click="show = false" icon="x" />
        </div>

        <!-- Step 1: File Upload -->
        <div v-if="step === 'upload'">
          <div
            class="border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors"
            :class="isDragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-outline-gray-3 hover:border-outline-gray-4'"
            @click="$refs.fileInput.click()"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <FeatherIcon name="upload" class="h-10 w-10 mx-auto mb-3 text-ink-gray-4" />
            <p class="text-lg font-medium text-ink-gray-7 mb-1">
              {{ __('CSV-Datei hierher ziehen') }}
            </p>
            <p class="text-sm text-ink-gray-4 mb-3">
              {{ __('oder klicken zum Auswählen') }}
            </p>
            <p class="text-xs text-ink-gray-4">
              {{ __('Unterstuetzte Formate: .csv') }}
            </p>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept=".csv"
            class="hidden"
            @change="handleFileSelect"
          />

          <!-- Template Download -->
          <div class="mt-4 flex items-center gap-2">
            <Button variant="subtle" size="sm" @click="downloadTemplate">
              <template #prefix>
                <FeatherIcon name="download" class="h-3.5 w-3.5" />
              </template>
              {{ __('Vorlage herunterladen') }}
            </Button>
            <span class="text-xs text-ink-gray-4">
              {{ __('CSV-Vorlage mit allen Spalten') }}
            </span>
          </div>
        </div>

        <!-- Step 2: Preview -->
        <div v-else-if="step === 'preview'">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-ink-gray-7">
                {{ fileName }}
              </p>
              <p class="text-xs text-ink-gray-4">
                {{ parsedRows.length }} {{ __('Zeilen gefunden') }}
              </p>
            </div>
            <Button variant="subtle" size="sm" @click="resetUpload">
              {{ __('Andere Datei') }}
            </Button>
          </div>

          <!-- Column Mapping -->
          <div class="mb-4 rounded-lg border border-outline-gray-2 p-3">
            <p class="text-sm font-medium text-ink-gray-7 mb-2">
              {{ __('Spaltenzuordnung') }}
            </p>
            <div class="flex flex-wrap gap-2">
              <div
                v-for="(mapping, idx) in columnMappings"
                :key="idx"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs"
                :class="mapping.field ? 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400' : 'bg-gray-100 text-ink-gray-4 dark:bg-gray-800'"
              >
                <span class="font-medium">{{ mapping.header }}</span>
                <span v-if="mapping.field">→ {{ mapping.fieldLabel }}</span>
                <span v-else>{{ __('(ignoriert)') }}</span>
              </div>
            </div>
          </div>

          <!-- Preview Table -->
          <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-surface-gray-2">
                  <th class="px-3 py-2 text-left text-xs font-medium text-ink-gray-5">#</th>
                  <th
                    v-for="(mapping, idx) in columnMappings"
                    :key="idx"
                    class="px-3 py-2 text-left text-xs font-medium"
                    :class="mapping.field ? 'text-ink-gray-7' : 'text-ink-gray-3'"
                  >
                    {{ mapping.field ? mapping.fieldLabel : mapping.header }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, rowIdx) in previewRows"
                  :key="rowIdx"
                  class="border-t border-outline-gray-1"
                >
                  <td class="px-3 py-2 text-xs text-ink-gray-4">{{ rowIdx + 1 }}</td>
                  <td
                    v-for="(cell, cellIdx) in row"
                    :key="cellIdx"
                    class="px-3 py-2 text-xs"
                    :class="columnMappings[cellIdx]?.field ? 'text-ink-gray-7' : 'text-ink-gray-3'"
                  >
                    {{ cell || '-' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="parsedRows.length > 5" class="mt-2 text-xs text-ink-gray-4 text-center">
            {{ __('Vorschau zeigt die ersten 5 von {0} Zeilen', [parsedRows.length]) }}
          </p>
        </div>

        <!-- Step 3: Importing -->
        <div v-else-if="step === 'importing'">
          <div class="text-center py-10">
            <div class="inline-flex items-center gap-3">
              <LoadingIndicator class="h-6 w-6" />
              <span class="text-lg text-ink-gray-7">
                {{ __('Importiere {0} Leads...', [parsedRows.length]) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Step 4: Results -->
        <div v-else-if="step === 'results'">
          <div class="text-center py-6">
            <FeatherIcon
              :name="importResult.failed === 0 ? 'check-circle' : 'alert-circle'"
              class="h-12 w-12 mx-auto mb-3"
              :class="importResult.failed === 0 ? 'text-green-500' : 'text-yellow-500'"
            />
            <p class="text-lg font-medium text-ink-gray-9 mb-1">
              {{ __('Import abgeschlossen') }}
            </p>
            <div class="flex items-center justify-center gap-4 mt-3">
              <div class="text-center">
                <p class="text-2xl font-bold text-green-600">{{ importResult.success }}</p>
                <p class="text-xs text-ink-gray-4">{{ __('Erfolgreich') }}</p>
              </div>
              <div v-if="importResult.failed > 0" class="text-center">
                <p class="text-2xl font-bold text-red-600">{{ importResult.failed }}</p>
                <p class="text-xs text-ink-gray-4">{{ __('Fehlgeschlagen') }}</p>
              </div>
            </div>
          </div>

          <!-- Distribution Details -->
          <div v-if="importResult.distribution && Object.keys(importResult.distribution).length > 0" class="mt-4">
            <p class="text-sm font-medium text-ink-gray-7 mb-2">{{ __('Verteilung an Vertriebler') }}</p>
            <div class="rounded-lg border border-outline-gray-2 overflow-hidden">
              <div
                v-for="(count, name) in importResult.distribution"
                :key="name"
                class="flex items-center justify-between px-3 py-2 text-sm border-b border-outline-gray-1 last:border-0"
              >
                <span class="text-ink-gray-7">{{ name }}</span>
                <span class="font-medium text-ink-gray-9">{{ count }} {{ __('Leads') }}</span>
              </div>
            </div>
          </div>

          <!-- Error Details -->
          <div v-if="importResult.errors && importResult.errors.length > 0" class="mt-4">
            <p class="text-sm font-medium text-ink-gray-7 mb-2">{{ __('Fehlerdetails') }}</p>
            <div class="rounded-lg border border-red-200 dark:border-red-800 overflow-hidden max-h-48 overflow-y-auto">
              <div
                v-for="(err, idx) in importResult.errors"
                :key="idx"
                class="px-3 py-2 text-xs border-b border-red-100 dark:border-red-900 last:border-0"
              >
                <span class="font-medium text-red-600">{{ __('Zeile') }} {{ err.row }}:</span>
                <span class="text-ink-gray-6 ml-1">{{ err.error }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Error -->
        <ErrorMessage class="mt-4" v-if="errorMsg" :message="errorMsg" />
      </div>

      <!-- Actions -->
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            v-if="step === 'preview'"
            variant="solid"
            :label="__('Importieren')"
            @click="startImport"
          >
            <template #prefix>
              <FeatherIcon name="upload" class="h-4 w-4" />
            </template>
          </Button>
          <Button
            v-if="step === 'results'"
            variant="solid"
            :label="__('Schließen')"
            @click="closeAndRefresh"
          />
          <Button
            v-if="step === 'results' && importResult.failed > 0"
            variant="subtle"
            :label="__('Erneut versuchen')"
            @click="resetUpload"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { call, LoadingIndicator } from 'frappe-ui'

const show = defineModel()
const emit = defineEmits(['imported'])

const step = ref('upload')
const isDragging = ref(false)
const fileName = ref('')
const parsedHeaders = ref([])
const parsedRows = ref([])
const errorMsg = ref(null)
const importResult = ref({ success: 0, failed: 0, errors: [] })

const FIELD_LABELS = {
  first_name: 'Vorname',
  last_name: 'Nachname',
  email: 'E-Mail',
  mobile_no: 'Mobilfunknummer',
  organization: 'Organisation',
  status: 'Status',
  custom_liste: 'Liste',
}

const COLUMN_MAP = {
  'vorname': 'first_name',
  'nachname': 'last_name',
  'e-mail': 'email',
  'e mail': 'email',
  'email': 'email',
  'mobilfunknummer': 'mobile_no',
  'telefon': 'mobile_no',
  'mobil': 'mobile_no',
  'organisation': 'organization',
  'firma': 'organization',
  'unternehmen': 'organization',
  'status': 'status',
  'liste': 'custom_liste',
  'first_name': 'first_name',
  'first name': 'first_name',
  'last_name': 'last_name',
  'last name': 'last_name',
  'mobile_no': 'mobile_no',
  'mobile': 'mobile_no',
  'phone': 'mobile_no',
  'organization': 'organization',
  'company': 'organization',
  'custom_liste': 'custom_liste',
}

const columnMappings = computed(() => {
  return parsedHeaders.value.map((header) => {
    const norm = header.trim().toLowerCase().replace(/_/g, ' ').replace(/-/g, ' ').trim()
    const field = COLUMN_MAP[norm] || COLUMN_MAP[norm.replace(/ /g, '_')] || null
    return {
      header,
      field,
      fieldLabel: field ? FIELD_LABELS[field] || field : null,
    }
  })
})

const previewRows = computed(() => {
  return parsedRows.value.slice(0, 5)
})

function parseCSV(text) {
  const lines = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (char === '"') {
      if (inQuotes && text[i + 1] === '"') {
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
    } else if ((char === ',' || char === ';') && !inQuotes) {
      lines.push(current)
      current = ''
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && text[i + 1] === '\n') i++
      lines.push(current)
      current = ''
      // End of row marker
      lines.push('\n')
    } else {
      current += char
    }
  }
  if (current) lines.push(current)

  // Reconstruct rows from tokens
  const rows = []
  let row = []
  for (const token of lines) {
    if (token === '\n') {
      if (row.length > 0) rows.push(row)
      row = []
    } else {
      row.push(token.trim())
    }
  }
  if (row.length > 0) rows.push(row)

  return rows
}

function detectDelimiter(text) {
  const firstLine = text.split('\n')[0]
  const semicolons = (firstLine.match(/;/g) || []).length
  const commas = (firstLine.match(/,/g) || []).length
  return semicolons > commas ? ';' : ','
}

function parseCSVAdvanced(text) {
  const delimiter = detectDelimiter(text)
  const lines = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    if (char === '"') {
      if (inQuotes && text[i + 1] === '"') {
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === delimiter && !inQuotes) {
      lines.push(current)
      current = ''
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && text[i + 1] === '\n') i++
      lines.push(current)
      current = ''
      lines.push('\n')
    } else {
      current += char
    }
  }
  if (current) lines.push(current)

  const rows = []
  let row = []
  for (const token of lines) {
    if (token === '\n') {
      if (row.length > 0) rows.push(row)
      row = []
    } else {
      row.push(token.trim())
    }
  }
  if (row.length > 0) rows.push(row)

  return rows
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) processFile(file)
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) processFile(file)
}

function processFile(file) {
  errorMsg.value = null

  if (!file.name.endsWith('.csv')) {
    errorMsg.value = 'Bitte eine CSV-Datei auswählen (.csv)'
    return
  }

  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const text = e.target.result
      const allRows = parseCSVAdvanced(text)

      if (allRows.length < 2) {
        errorMsg.value = 'Die Datei enthaelt keine Daten (mindestens Header + 1 Zeile erforderlich)'
        return
      }

      parsedHeaders.value = allRows[0]
      parsedRows.value = allRows.slice(1).filter((row) => row.some((cell) => cell))

      if (parsedRows.value.length === 0) {
        errorMsg.value = 'Die Datei enthaelt keine Datenzeilen'
        return
      }

      // Check if at least one column maps to a field
      const hasMappedColumn = columnMappings.value.some((m) => m.field)
      if (!hasMappedColumn) {
        errorMsg.value = 'Keine Spalten konnten zugeordnet werden. Bitte pruefen Sie die Spaltenkoepfe (z.B. Vorname, Nachname, E-Mail)'
        return
      }

      // Check if first_name is mapped
      const hasFirstName = columnMappings.value.some((m) => m.field === 'first_name')
      if (!hasFirstName) {
        errorMsg.value = 'Pflichtfeld "Vorname" / "first_name" fehlt in den Spaltenkoepfen'
        return
      }

      step.value = 'preview'
    } catch (err) {
      errorMsg.value = 'Fehler beim Lesen der Datei: ' + err.message
    }
  }
  reader.readAsText(file, 'UTF-8')
}

async function startImport() {
  step.value = 'importing'
  errorMsg.value = null

  try {
    const result = await call('crm.api.lead_import.import_leads', {
      rows: JSON.stringify(parsedRows.value),
      headers: JSON.stringify(parsedHeaders.value),
    })
    importResult.value = result
    step.value = 'results'
  } catch (err) {
    errorMsg.value = err.message || 'Import fehlgeschlagen'
    step.value = 'preview'
  }
}

function resetUpload() {
  step.value = 'upload'
  fileName.value = ''
  parsedHeaders.value = []
  parsedRows.value = []
  errorMsg.value = null
  importResult.value = { success: 0, failed: 0, errors: [] }
}

function closeAndRefresh() {
  if (importResult.value.success > 0) {
    emit('imported')
  }
  show.value = false
}

function downloadTemplate() {
  const headers = ['Vorname', 'Nachname', 'E-Mail', 'Mobilfunknummer', 'Organisation', 'Status', 'Liste']
  const example = ['Max', 'Mustermann', 'max@beispiel.de', '+49 170 1234567', 'Musterfirma GmbH', '', '10 - Neu ohne Termin']
  const csv = headers.join(';') + '\n' + example.join(';') + '\n'
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'leads_import_vorlage.csv'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
