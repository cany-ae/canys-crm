<template>
  <div
    ref="popupEl"
    class="lead-hover-popup"
    :style="popupStyle"
  >
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-4">
      <div class="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500"></div>
      <span class="ml-2 text-xs text-gray-400">Laden...</span>
    </div>

    <!-- Content -->
    <div v-else-if="lead">
      <!-- 1. Header: Name + Organization + Leadtyp -->
      <div class="mb-2 flex items-start justify-between gap-2">
        <div class="min-w-0">
          <div class="text-sm font-bold text-gray-900 leading-tight truncate">
            {{ lead.lead_name || lead.name }}
          </div>
          <div v-if="lead.organization" class="text-[11px] text-gray-500 truncate">
            {{ lead.organization }}
          </div>
        </div>
        <span
          v-if="lead.custom_leadtyp"
          class="flex-shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-50 text-indigo-700"
        >{{ lead.custom_leadtyp }}</span>
      </div>

      <!-- 2. Badges row: Phase + Status -->
      <div class="mb-2 flex flex-wrap items-center gap-1">
        <!-- Phase badge -->
        <span
          v-if="lead.custom_liste"
          class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold"
          :class="phaseBadgeClass"
        >
          <span class="h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: phaseHex }"></span>
          {{ lead.custom_liste }}
        </span>


      </div>

      <!-- 3. TERMIN section (most prominent, light blue background) -->
      <div
        v-if="lead.termin_datum && lead.termin_datum !== 'None' && lead.termin_datum !== ''"
        class="mb-2 rounded-md bg-blue-50 border-l-2 border-blue-400 px-2.5 py-2"
      >
        <div class="flex items-center gap-1.5 mb-1">
          <FeatherIcon name="calendar" class="h-3.5 w-3.5 text-blue-600" />
          <span class="text-[11px] font-semibold text-blue-800">Nächster Termin</span>
          <span
            v-if="isTerminToday"
            class="ml-auto rounded bg-red-100 px-1 py-0.5 text-[9px] font-bold text-red-700"
          >HEUTE</span>
          <span
            v-else-if="isTerminTomorrow"
            class="ml-auto rounded bg-orange-100 px-1 py-0.5 text-[9px] font-bold text-orange-700"
          >MORGEN</span>
        </div>
        <div class="text-xs text-blue-900 font-medium">
          {{ formatDate(lead.termin_datum) }}
          <span v-if="lead.termin_zeit_von" class="text-blue-700"> · {{ formatTime(lead.termin_zeit_von) }}</span>
        </div>
        <div class="mt-1 flex flex-wrap items-center gap-1 text-[10px]">
          <span v-if="lead.termin_typ" class="rounded bg-blue-100 px-1 py-0.5 text-blue-700">{{ lead.termin_typ }}</span>
          <span v-if="lead.termin_status" class="rounded px-1 py-0.5" :class="terminStatusClass">{{ lead.termin_status }}</span>
          <span v-if="lead.termin_berater" class="text-blue-600">· {{ lead.termin_berater }}</span>
        </div>
      </div>

      <!-- 4. Kontakt-Infos (compact) -->
      <div class="space-y-1 text-xs">
        <div v-if="lead.mobile_no || lead.phone" class="flex items-center gap-2">
          <FeatherIcon name="phone" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="font-medium text-gray-700">{{ lead.mobile_no || lead.phone }}</span>
        </div>
        <div v-if="lead.email" class="flex items-center gap-2">
          <FeatherIcon name="mail" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="text-gray-700 truncate">{{ lead.email }}</span>
        </div>
        <div v-if="lead.erreichbarkeit" class="flex items-center gap-2">
          <FeatherIcon name="clock" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="text-gray-600">{{ lead.erreichbarkeit }}</span>
        </div>
        <div v-if="lead.owner_name" class="flex items-center gap-2">
          <FeatherIcon name="user" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="text-gray-600">{{ lead.owner_name }}</span>
        </div>
      </div>

      <!-- 5. Follow-up section -->
      <div
        v-if="hasFollowup"
        class="mt-2 border-t border-gray-100 pt-2 space-y-1 text-xs"
      >
        <div v-if="lead.naechster_kontakt && lead.naechster_kontakt !== 'None'" class="flex items-center gap-2">
          <FeatherIcon name="bell" class="h-3 w-3 flex-shrink-0" :class="isOverdue ? 'text-red-500' : 'text-gray-400'" />
          <span :class="isOverdue ? 'text-red-600 font-semibold' : 'text-gray-600'">{{ formatDate(lead.naechster_kontakt) }}</span>
          <span v-if="isOverdue" class="rounded bg-red-100 px-1 py-0.5 text-[9px] font-bold text-red-700">Überfällig</span>
        </div>
        <div v-if="lead.followup_grund" class="flex items-center gap-2">
          <FeatherIcon name="info" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="text-gray-600">{{ lead.followup_grund }}</span>
        </div>
        <div v-if="lead.kontaktversuche > 0" class="flex items-center gap-2">
          <FeatherIcon name="repeat" class="h-3 w-3 text-gray-400 flex-shrink-0" />
          <span class="text-gray-600">{{ lead.kontaktversuche }}× versucht</span>
        </div>
      </div>

      <!-- 6. Cross-Sell section -->
      <div v-if="hasCrossSell" class="mt-2 border-t border-gray-100 pt-2">
        <div class="flex items-center gap-1.5 mb-1">
          <FeatherIcon name="gift" class="h-3 w-3 text-purple-500" />
          <span class="text-[10px] font-semibold text-purple-700">Cross-Sell</span>
        </div>
        <div class="space-y-0.5">
          <div v-for="cs in crossSellItems" :key="cs.prio" class="flex items-center gap-1.5 text-[11px]">
            <span class="font-medium text-gray-500 w-3">{{ cs.prio }}.</span>
            <span class="font-medium text-gray-800">{{ cs.produkt }}</span>
            <span
              v-if="cs.status"
              class="rounded px-1 py-0.5 text-[9px]"
              :class="crossSellStatusClass(cs.status)"
            >{{ cs.status }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error / no data -->
    <div v-else class="py-3 text-center text-xs text-gray-400">
      Keine Daten
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { call, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  leadName: { type: String, required: true },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
})

const loading = ref(true)
const lead = ref(null)
const popupEl = ref(null)
const popupWidth = ref(320)
const popupHeight = ref(200)

// ─── Phase / Status maps ────────────────────────────────────────────────────

const LEAD_PHASES = {
  '10 - Neu ohne Termin': { color: 'gray', hex: '#6B7280' },
  '20 - Termin gebucht': { color: 'blue', hex: '#3B82F6' },
  '30 - Reaktivierung': { color: 'amber', hex: '#F59E0B' },
  '50 - Closer-Termin': { color: 'purple', hex: '#8B5CF6' },
  '70 - Follow-up': { color: 'orange', hex: '#F97316' },
  '80 - Abschluss gewonnen': { color: 'green', hex: '#10B981' },
  '90 - Abschluss verloren': { color: 'red', hex: '#EF4444' },
}

const BADGE_CLASSES = {
  gray: 'bg-gray-100 text-gray-700',
  blue: 'bg-blue-100 text-blue-700',
  amber: 'bg-amber-100 text-amber-700',
  purple: 'bg-purple-100 text-purple-700',
  orange: 'bg-orange-100 text-orange-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
}

// ─── Phase computed ─────────────────────────────────────────────────────────

const currentPhase = computed(() => {
  if (!lead.value?.custom_liste) return null
  return LEAD_PHASES[lead.value.custom_liste] || null
})

const phaseHex = computed(() => currentPhase.value?.hex || '#6B7280')

const phaseBadgeClass = computed(() => {
  const color = currentPhase.value?.color || 'gray'
  return BADGE_CLASSES[color] || BADGE_CLASSES.gray
})

// ─── Status computed ────────────────────────────────────────────────────────

// ─── Termin computed ────────────────────────────────────────────────────────

const isTerminToday = computed(() => isToday(lead.value?.termin_datum))
const isTerminTomorrow = computed(() => isTomorrow(lead.value?.termin_datum))

const terminStatusClass = computed(() => {
  const s = lead.value?.termin_status || ''
  if (s === 'Bestätigt') return 'bg-green-100 text-green-700'
  if (s === 'Geplant') return 'bg-yellow-100 text-yellow-800'
  if (s === 'Verschoben') return 'bg-orange-100 text-orange-700'
  return 'bg-gray-100 text-gray-600'
})

// ─── Follow-up computed ─────────────────────────────────────────────────────

const isOverdue = computed(() => {
  if (!lead.value?.naechster_kontakt || lead.value.naechster_kontakt === 'None') return false
  return new Date(lead.value.naechster_kontakt) < new Date()
})

const hasFollowup = computed(() => {
  if (!lead.value) return false
  const nk = lead.value.naechster_kontakt
  const fg = lead.value.followup_grund
  const kv = lead.value.kontaktversuche
  return (nk && nk !== 'None' && nk !== '') || (fg && fg !== '') || (kv && kv > 0)
})

// ─── Cross-Sell computed ────────────────────────────────────────────────────

const hasCrossSell = computed(() => {
  if (!lead.value) return false
  return lead.value.cross_sell_prio1_produkt || lead.value.cross_sell_prio2_produkt || lead.value.cross_sell_prio3_produkt
})

const crossSellItems = computed(() => {
  if (!lead.value) return []
  const items = []
  if (lead.value.cross_sell_prio1_produkt) items.push({ prio: 1, produkt: lead.value.cross_sell_prio1_produkt, status: lead.value.cross_sell_prio1_status })
  if (lead.value.cross_sell_prio2_produkt) items.push({ prio: 2, produkt: lead.value.cross_sell_prio2_produkt, status: lead.value.cross_sell_prio2_status })
  if (lead.value.cross_sell_prio3_produkt) items.push({ prio: 3, produkt: lead.value.cross_sell_prio3_produkt, status: lead.value.cross_sell_prio3_status })
  return items
})

function crossSellStatusClass(status) {
  if (status === 'Angesprochen') return 'bg-green-100 text-green-700'
  if (status === 'Weiterleitung erstellt') return 'bg-blue-100 text-blue-700'
  if (status === 'Bewusst nicht angesprochen') return 'bg-gray-100 text-gray-600'
  return 'bg-yellow-50 text-yellow-700'
}

// ─── Popup position ─────────────────────────────────────────────────────────

const popupStyle = computed(() => {
  const m = 12
  const vw = typeof window !== 'undefined' ? window.innerWidth : 1200
  const vh = typeof window !== 'undefined' ? window.innerHeight : 800

  let left = props.x + m
  let top = props.y + m

  if (left + popupWidth.value > vw - m) left = props.x - popupWidth.value - m
  if (top + popupHeight.value > vh - m) top = vh - popupHeight.value - m
  if (left < m) left = m
  if (top < m) top = m

  return {
    position: 'fixed',
    left: left + 'px',
    top: top + 'px',
    zIndex: 9999,
    maxWidth: '320px',
    width: 'max-content',
  }
})

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr || dateStr === 'None') return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return dateStr
  }
}

function formatTime(timeStr) {
  if (!timeStr || timeStr === 'None') return ''
  const parts = timeStr.split(':')
  if (parts.length >= 2) {
    return parts[0].padStart(2, '0') + ':' + parts[1].padStart(2, '0') + ' Uhr'
  }
  return timeStr
}

function isToday(dateStr) {
  if (!dateStr || dateStr === 'None') return false
  return new Date(dateStr).toDateString() === new Date().toDateString()
}

function isTomorrow(dateStr) {
  if (!dateStr || dateStr === 'None') return false
  const t = new Date()
  t.setDate(t.getDate() + 1)
  return new Date(dateStr).toDateString() === t.toDateString()
}

// ─── Data fetch ─────────────────────────────────────────────────────────────

onMounted(async () => {
  loading.value = true
  try {
    const data = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_lead_preview',
      { lead_name: props.leadName }
    )
    if (data && data.name) {
      lead.value = data
    }
  } catch (err) {
    console.error('LeadHoverPopup: failed', err)
    lead.value = null
  } finally {
    loading.value = false
    await nextTick()
    if (popupEl.value) {
      popupHeight.value = popupEl.value.offsetHeight
      popupWidth.value = popupEl.value.offsetWidth
    }
  }
})
</script>

<style scoped>
.lead-hover-popup {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.75rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  pointer-events: none;
  min-width: 200px;
}
</style>
