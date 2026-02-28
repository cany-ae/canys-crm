<template>
  <div
    v-if="history.data || history.loading"
    class="rounded-lg border border-outline-gray-modals bg-surface-white"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 border-b border-outline-gray-modals px-4 py-2.5">
      <svg
        class="h-4 w-4 text-ink-gray-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <span class="text-sm font-semibold text-ink-gray-8">Kontakt-Historie</span>
    </div>

    <!-- Loading state -->
    <div v-if="history.loading" class="flex items-center justify-center py-6">
      <div class="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600"></div>
    </div>

    <!-- Content -->
    <div v-else-if="summary" class="flex flex-col gap-3 px-4 py-3">
      <!-- Leads Section -->
      <div>
        <div class="mb-1.5 flex items-center gap-2">
          <span class="text-sm font-medium text-ink-gray-7">
            Leads ({{ summary.leads_total }})
          </span>
        </div>
        <div v-if="summary.leads_total > 0" class="flex flex-wrap gap-1.5">
          <span
            v-for="(count, status) in summary.leads_by_status"
            :key="status"
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
            :class="getLeadBadgeClass(status)"
          >
            <span
              class="inline-block h-1.5 w-1.5 rounded-full"
              :class="getLeadDotClass(status)"
            ></span>
            {{ truncateStatus(status) }}
            <span class="font-semibold">{{ count }}</span>
          </span>
        </div>
        <span v-else class="text-xs text-ink-gray-4">
          Keine bisherigen Leads
        </span>
      </div>

      <!-- Deals Section -->
      <div>
        <div class="mb-1.5 flex items-center gap-2">
          <span class="text-sm font-medium text-ink-gray-7">
            Deals ({{ summary.deals_total }})
          </span>
          <span
            v-if="summary.deals_total_revenue > 0"
            class="text-xs text-ink-gray-5"
          >
            &middot; Volumen: {{ formatCurrency(summary.deals_total_revenue) }}
          </span>
        </div>
        <div v-if="summary.deals_total > 0" class="flex flex-wrap gap-1.5">
          <span
            v-for="(count, status) in summary.deals_by_status"
            :key="status"
            class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
            :class="getDealBadgeClass(status)"
          >
            <span
              class="inline-block h-1.5 w-1.5 rounded-full"
              :class="getDealDotClass(status)"
            ></span>
            {{ status }}
            <span class="font-semibold">{{ count }}</span>
          </span>
        </div>
        <span v-else class="text-xs text-ink-gray-4">
          Keine bisherigen Deals
        </span>
      </div>

      <!-- Date Footer -->
      <div
        v-if="summary.first_lead_date || summary.last_activity_date"
        class="flex flex-wrap items-center gap-1 border-t border-outline-gray-modals pt-2 text-xs text-ink-gray-5"
      >
        <span v-if="summary.first_lead_date">
          Erster Kontakt: {{ formatDateShort(summary.first_lead_date) }}
        </span>
        <span v-if="summary.first_lead_date && summary.last_activity_date">
          &middot;
        </span>
        <span v-if="summary.last_activity_date">
          Letzte Aktivität: {{ formatDateShort(summary.last_activity_date) }}
        </span>
      </div>
    </div>

    <!-- No data at all -->
    <div
      v-else-if="!history.loading"
      class="px-4 py-4 text-center text-xs text-ink-gray-4"
    >
      Keine Historie vorhanden
    </div>
  </div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const history = createResource({
  url: 'crm.api.contact.get_contact_history',
  params: { contact: props.contactId },
  cache: ['contactHistory', props.contactId],
  auto: true,
})

const summary = computed(() => history.data?.summary || null)

// -- Pipeline Phase (Liste) color mapping --

const listePhaseColorMap = {
  '10 - Neu ohne Termin': 'gray',
  '20 - Termin gebucht': 'blue',
  '30 - Reaktivierung': 'orange',
  '50 - Closer-Termin': 'cyan',
  '70 - Follow-up': 'yellow',
  '80 - Abschluss gewonnen': 'green',
  '90 - Abschluss verloren': 'red',
}

const badgeClassMap = {
  gray: 'bg-gray-100 text-gray-700',
  blue: 'bg-blue-100 text-blue-700',
  orange: 'bg-orange-100 text-orange-700',
  yellow: 'bg-yellow-100 text-yellow-800',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
  cyan: 'bg-cyan-100 text-cyan-700',
}

const dotClassMap = {
  gray: 'bg-gray-500',
  blue: 'bg-blue-500',
  orange: 'bg-orange-500',
  yellow: 'bg-yellow-500',
  green: 'bg-green-500',
  red: 'bg-red-500',
  cyan: 'bg-cyan-500',
}

function getLeadColor(phase) {
  return listePhaseColorMap[phase] || 'gray'
}

function getLeadBadgeClass(phase) {
  return badgeClassMap[getLeadColor(phase)] || badgeClassMap.gray
}

function getLeadDotClass(phase) {
  return dotClassMap[getLeadColor(phase)] || dotClassMap.gray
}

// -- Deal status color mapping --

const dealStatusColorMap = {
  'Qualification': 'blue',
  'Demo/Making': 'cyan',
  'Proposal/Quotation': 'orange',
  'Negotiation': 'yellow',
  'Ready to Close': 'green',
  'Won': 'green',
  'Lost': 'red',
}

function getDealColor(status) {
  return dealStatusColorMap[status] || 'gray'
}

function getDealBadgeClass(status) {
  return badgeClassMap[getDealColor(status)] || badgeClassMap.gray
}

function getDealDotClass(status) {
  return dotClassMap[getDealColor(status)] || dotClassMap.gray
}

// -- Helpers --

function truncateStatus(phase) {
  if (!phase) return 'Unbekannt'
  const match = phase.match(/^(\d+)\s*-\s*(.+)/)
  if (match) {
    const code = match[1]
    const label = match[2]
    if (label.length > 12) return code + ' ' + label.substring(0, 10) + '...'
    return code + ' ' + label
  }
  return phase
}

function formatCurrency(value) {
  if (!value && value !== 0) return ''
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}
</script>
