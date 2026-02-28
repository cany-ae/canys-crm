<template>
  <Dialog v-model="show" :options="{ title: config.title, size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-4 py-2">
        <!-- Cross-Sell context info (read-only) -->
        <div v-if="crossSellData?.cross_sell_produkt" class="rounded-lg bg-blue-50 border border-blue-200 p-3">
          <div class="flex items-center gap-2 text-sm">
            <span class="font-medium text-blue-800">Cross-Sell Weiterleitung:</span>
            <span class="text-blue-700">{{ crossSellData.cross_sell_produkt }}</span>
            <span class="text-xs text-blue-500">(Prio {{ crossSellData.cross_sell_prio }})</span>
          </div>
        </div>
        <div v-for="field in config.fields" :key="field.name" class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-ink-gray-7">
            {{ field.label }}
            <span v-if="field.required" class="text-red-500">*</span>
          </label>

          <input
            v-if="field.type === 'date'"
            type="date"
            v-model="formData[field.name]"
            style="font-size: 16px; padding: 12px 14px; height: 44px;"
            class="form-input w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
          />

          <input
            v-else-if="field.type === 'time'"
            type="time"
            step="900"
            v-model="formData[field.name]"
            style="font-size: 16px; padding: 12px 14px; height: 44px;"
            class="form-input w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
          />

          <select
            v-else-if="field.type === 'select'"
            v-model="formData[field.name]"
            style="font-size: 16px; padding: 12px 14px; height: 44px;"
            class="form-select w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
          >
            <option v-for="opt in getFieldOptions(field)" :key="typeof opt === 'object' ? opt.value : opt" :value="typeof opt === 'object' ? opt.value : opt">
              {{ typeof opt === 'object' ? opt.label : opt }}
            </option>
          </select>

          <input
            v-else-if="field.type === 'number'"
            type="number"
            step="0.01"
            v-model.number="formData[field.name]"
            style="font-size: 16px; padding: 12px 14px; height: 44px;"
            class="form-input w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
          />

          <textarea
            v-else
            v-model="formData[field.name]"
            rows="4"
            style="font-size: 16px; padding: 12px 14px; min-height: 100px;"
            class="form-textarea w-full rounded-md border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8 focus:border-outline-gray-4 focus:ring-0"
          ></textarea>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center" :class="action === 'termin_buchen' ? 'justify-between' : 'justify-end'">
        <button
          v-if="action === 'termin_buchen'"
          @click="switchToVorschlaege"
          class="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          Termin mit Vorschlägen
        </button>
        <div class="flex gap-2">
          <Button variant="subtle" @click="show = false">{{ __('Abbrechen') }}</Button>
          <Button
            variant="solid"
            :theme="actionTheme"
            :loading="loading"
            @click="submit"
          >
            {{ config.title }}
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Dialog, call } from 'frappe-ui'

const props = defineProps({
  action: { type: String, default: '' },
  crossSellData: { type: Object, default: () => null },
})

const emit = defineEmits(['submit', 'update:show', 'switchToVorschlaege'])

const show = defineModel('show', { type: Boolean, default: false })
const loading = ref(false)
const formData = ref({})
const vertriebler = ref([])
const currentUser = ref('')
const currentUserName = ref('')

// Load sales users for Berater dropdown
onMounted(async () => {
  try {
    currentUser.value = decodeURIComponent(document.cookie.match(/user_id=([^;]+)/)?.[1] || window.cur_user || '')
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_vertriebler_list'
    )
    if (result && result.length) {
      vertriebler.value = result.map(u => ({
        email: u.email,
        full_name: u.full_name || u.email
      }))
    }
    // Eingeloggten User-Namen laden (fuer Anzeige im Dropdown, auch wenn GF)
    if (currentUser.value) {
      const found = vertriebler.value.find(v => v.email === currentUser.value)
      if (found) {
        currentUserName.value = found.full_name
      } else {
        try {
          const userInfo = await call('frappe.client.get_value', {
            doctype: 'User',
            filters: { name: currentUser.value },
            fieldname: 'full_name'
          })
          if (userInfo && userInfo.full_name) {
            currentUserName.value = userInfo.full_name
          }
        } catch (e2) {
          // Fallback: use email as name
          currentUserName.value = ''
        }
      }
    }
  } catch (e) {
    console.warn('Could not load sales users for Berater dropdown', e)
  }
})

function getFieldOptions(field) {
  if (field.name === 'berater_user' && vertriebler.value.length) {
    const options = vertriebler.value.map(v => ({
      value: v.email,
      label: v.full_name ? `${v.full_name} (${v.email})` : v.email
    }))
    // Eingeloggten User immer anzeigen (auch wenn GF, nicht Vertriebler)
    if (currentUser.value && !options.find(o => o.value === currentUser.value)) {
      options.unshift({
        value: currentUser.value,
        label: currentUserName.value ? `${currentUserName.value} (${currentUser.value})` : currentUser.value
      })
    }
    return options
  }
  return field.options || []
}

/** Helper: next 15-min interval as HH:MM string (24h format) */
function nextQuarterHour() {
  const now = new Date()
  let h = now.getHours()
  let m = now.getMinutes()
  // Round up to next 15-min boundary
  const remainder = m % 15
  if (remainder > 0) {
    m += (15 - remainder)
  } else {
    // Already on a 15-min boundary, add 15 min so it's in the future
    m += 15
  }
  if (m >= 60) { h += 1; m -= 60 }
  if (h >= 24) h = 9  // wrap to 09:00 if past midnight
  return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0')
}

/** Helper: add minutes to a HH:MM string, return HH:MM (snapped to 15-min) */
function addMinutesToTime(timeStr, minutes) {
  if (!timeStr || !minutes) return ''
  const parts = timeStr.split(':')
  if (parts.length < 2) return ''
  let h = parseInt(parts[0], 10)
  let m = parseInt(parts[1], 10)
  m += parseInt(minutes, 10)
  while (m >= 60) { h += 1; m -= 60 }
  if (h >= 24) h -= 24
  // Snap to nearest 15-min boundary
  const remainder = m % 15
  if (remainder > 0) m += (15 - remainder)
  if (m >= 60) { h += 1; m -= 60 }
  return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0')
}

const actionConfigs = {
  termin_buchen: {
    title: 'Termin buchen',
    theme: 'blue',
    fields: [
      { name: 'termin_datum', label: 'Termin-Datum', type: 'date', required: true },
      { name: 'termin_zeit_von', label: 'Uhrzeit von', type: 'time', required: true },
      { name: 'termin_zeit_bis', label: 'Uhrzeit bis', type: 'time' },
      { name: 'termin_typ', label: 'Termin-Typ', type: 'select',
        options: ['Ersttermin', 'Closer-Termin', 'Follow-up Termin', 'Reaktivierung', 'Spezialist'] },
      { name: 'termin_dauer', label: 'Dauer (Minuten)', type: 'select', options: [15, 30, 45, 60, 75, 90, 120] },
      { name: 'berater_user', label: 'Berater', type: 'select', options: [] },
      { name: 'termin_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  followup_setzen: {
    title: 'Follow-up setzen',
    theme: 'orange',
    fields: [
      { name: 'naechster_kontakt', label: 'Nächster Kontakt', type: 'date', required: true },
      { name: 'followup_grund', label: 'Grund', type: 'select',
        options: ['Erstkontakt', 'Rückruf vereinbart', 'Terminerinnerung', 'Nachfass nach Termin', 'Reaktivierung', 'Cross-Selling', 'Dokumente ausstehend', 'Sonstiges'] },
      { name: 'kontaktart', label: 'Kontaktart', type: 'select',
        options: ['Anruf', 'WhatsApp', 'SMS', 'E-Mail', 'Termin', 'Sonstiges'] },
      { name: 'followup_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  abschluss_gewonnen: {
    title: 'Abschluss gewonnen',
    theme: 'green',
    fields: [
      { name: 'abschluss_produkt', label: 'Produkt', type: 'text', required: true },
      { name: 'abschluss_beitrag', label: 'Monatsbeitrag (EUR)', type: 'number' },
      { name: 'abschluss_provision', label: 'Provision (EUR)', type: 'number' },
      { name: 'abschluss_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  abschluss_verloren: {
    title: 'Abschluss verloren',
    theme: 'red',
    fields: [
      { name: 'verloren_grund', label: 'Grund', type: 'select',
        options: ['Kein Interesse', 'Preis zu hoch', 'Anderem Anbieter zugesagt', 'Nicht erreicht', 'Falsche Zielgruppe', 'Sonstiges'] },
      { name: 'abschluss_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  an_spezialist_weiterleiten: {
    title: 'An Spezialist weiterleiten',
    theme: 'blue',
    fields: [
      { name: 'spezialist_typ', label: 'Spezialisten-Typ', type: 'select',
        options: ['KV Mensch', 'bAV', 'Finanz', 'Sach', 'Sonstiges'] },
      { name: 'spezialist_user', label: 'Spezialist (E-Mail)', type: 'text' },
    ],
  },
  termin_absagen: {
    title: 'Termin absagen',
    theme: 'red',
    fields: [
      { name: 'absage_grund', label: 'Absagegrund', type: 'select',
        options: ['Vom Kunden abgesagt', 'Berater nicht verfügbar', 'Termin verlegt', 'Sonstiges'] },
      { name: 'termin_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  termin_verschieben: {
    title: 'Termin verschieben',
    theme: 'purple',
    fields: [
      { name: 'neues_datum', label: 'Neues Datum', type: 'date', required: true },
      { name: 'termin_notiz', label: 'Notiz', type: 'text' },
    ],
  },
  spezialist_qualifiziert: {
    title: 'Lead qualifiziert',
    theme: 'green',
    fields: [
      { name: 'qualif_notiz', label: 'Qualifizierungs-Notiz', type: 'text' },
    ],
  },
  spezialist_nicht_qualifiziert: {
    title: 'Lead nicht qualifiziert',
    theme: 'red',
    fields: [
      { name: 'nicht_qualif_grund', label: 'Grund', type: 'select',
        options: ['Kein Bedarf', 'Bereits versichert', 'Gesundheitliche Ablehnungsgruende', 'Nicht erreichbar', 'Sonstiges'] },
      { name: 'nicht_qualif_notiz', label: 'Notiz', type: 'text' },
    ],
  },
}

const config = computed(() => {
  return actionConfigs[props.action] || { title: '', theme: 'blue', fields: [] }
})

const actionTheme = computed(() => config.value.theme || 'blue')

// Reset form when action changes or dialog opens
watch([() => props.action, show], () => {
  if (show.value) {
    const defaults = {}
    config.value.fields.forEach(f => {
      if (f.name === 'berater_user') {
        // Default to current user
        defaults[f.name] = currentUser.value
      } else if (f.name === 'termin_dauer') {
        // Default duration 60 minutes
        defaults[f.name] = 60
      } else if (f.name === 'termin_zeit_von') {
        // Default to next full hour
        defaults[f.name] = nextQuarterHour()
      } else if (f.name === 'termin_zeit_bis') {
        // Auto-calculated from termin_zeit_von + duration, set initial
        const startTime = defaults['termin_zeit_von'] || nextQuarterHour()
        const duration = defaults['termin_dauer'] || 60
        defaults[f.name] = addMinutesToTime(startTime, duration)
      } else if (f.type === 'select' && f.options?.length) {
        defaults[f.name] = f.options[0]
      } else if (f.type === 'date') {
        const d = new Date()
        if (props.action === 'followup_setzen') d.setDate(d.getDate() + 1)
        defaults[f.name] = d.toISOString().split('T')[0]
      } else if (f.type === 'number') {
        defaults[f.name] = 0
      } else {
        defaults[f.name] = ''
      }
    })
    formData.value = defaults
  }
})

// Auto-recalculate termin_zeit_bis when termin_zeit_von or termin_dauer changes
watch(
  () => [formData.value.termin_zeit_von, formData.value.termin_dauer],
  ([zeitVon, dauer]) => {
    if (props.action === 'termin_buchen' && zeitVon && dauer) {
      formData.value.termin_zeit_bis = addMinutesToTime(zeitVon, dauer)
    }
  }
)

function switchToVorschlaege() {
  show.value = false
  emit('switchToVorschlaege')
}

function submit() {
  // Validate required fields
  for (const field of config.value.fields) {
    if (field.required && !formData.value[field.name]) {
      return
    }
  }
  loading.value = true
  // Merge cross-sell data into submission if present
  const submitData = { ...formData.value }
  if (props.crossSellData) {
    submitData.cross_sell_prio = props.crossSellData.cross_sell_prio || ''
    submitData.cross_sell_produkt = props.crossSellData.cross_sell_produkt || ''
  }
  emit('submit', props.action, submitData)
  // Parent will close dialog after action completes
  setTimeout(() => {
    loading.value = false
    show.value = false
  }, 500)
}
</script>
