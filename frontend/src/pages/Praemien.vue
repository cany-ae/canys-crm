<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Prämien'), route: { name: 'Praemien' } }]" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Dropdown :options="periodOptions">
            <template #default="{ open }">
              <Button
                :label="activePeriodLabel"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
                variant="outline"
                size="sm"
              />
            </template>
          </Dropdown>
          <Button
            :label="__('Aktualisieren')"
            variant="outline"
            size="sm"
            @click="reload"
            :loading="loading"
          >
            <template #prefix>
              <FeatherIcon name="refresh-cw" class="h-3.5 w-3.5" />
            </template>
          </Button>
          <Button
            v-if="isAdmin"
            :label="__('CSV Export')"
            variant="outline"
            size="sm"
            @click="exportCSV"
            :loading="exporting"
          >
            <template #prefix>
              <FeatherIcon name="download" class="h-3.5 w-3.5" />
            </template>
          </Button>
        </div>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-5 space-y-5">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-blue-50 text-blue-600 border border-blue-100">
              <FeatherIcon name="dollar-sign" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Gesamt Prämien') }}</span>
          </div>
          <div class="text-2xl font-bold text-ink-gray-9 mt-1">{{ formatCurrency(summary.total_berechnet + summary.total_ausgezahlt) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ summary.count_berechnet + summary.count_ausgezahlt }} {{ __('Leads') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-green-50 text-green-600 border border-green-100">
              <FeatherIcon name="check-circle" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Ausgezahlt') }}</span>
          </div>
          <div class="text-2xl font-bold text-green-700 mt-1">{{ formatCurrency(summary.total_ausgezahlt) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ summary.count_ausgezahlt }} {{ __('Leads') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-orange-50 text-orange-600 border border-orange-100">
              <FeatherIcon name="clock" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Ausstehend') }}</span>
          </div>
          <div class="text-2xl font-bold text-orange-700 mt-1">{{ formatCurrency(summary.total_offen) }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ summary.count_berechnet }} {{ __('offen') }}</div>
        </div>
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 flex flex-col gap-1">
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center justify-center w-8 h-8 rounded-md text-sm bg-purple-50 text-purple-600 border border-purple-100">
              <FeatherIcon name="users" class="h-4 w-4" />
            </span>
            <span class="text-sm font-medium text-ink-gray-5">{{ __('Anzahl Leads') }}</span>
          </div>
          <div class="text-2xl font-bold text-ink-gray-9 mt-1">{{ summary.count_berechnet + summary.count_ausgezahlt }}</div>
          <div class="text-xs text-ink-gray-4 mt-0.5">{{ __('mit Prämie') }}</div>
        </div>
      </div>

      <!-- Main Content: Table + Sidebar -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Prämien per User Table -->
        <div class="lg:col-span-2 rounded-lg border border-outline-gray-2 bg-surface-white">
          <div class="px-4 py-3 border-b border-outline-gray-2">
            <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Prämien pro Mitarbeiter') }}</h3>
          </div>
          <div v-if="byUser.length === 0" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm">
            {{ __('Keine Prämien im gewählten Zeitraum') }}
          </div>
          <div v-else class="divide-y divide-outline-gray-1">
            <div v-for="(userRow, idx) in byUser" :key="userRow.user">
              <!-- User row (clickable) -->
              <div
                class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-surface-gray-1 transition-colors"
                @click="toggleExpand(idx)"
              >
                <FeatherIcon
                  name="chevron-right"
                  class="h-4 w-4 text-ink-gray-5 transition-transform duration-200 flex-shrink-0"
                  :class="{ 'rotate-90': expandedRows[idx] }"
                />
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-medium text-ink-gray-9 truncate">{{ userRow.full_name || userRow.user }}</div>
                  <div class="text-xs text-ink-gray-4">{{ userRow.user }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-16">
                  <div class="text-xs text-ink-gray-5">{{ __('Anzahl') }}</div>
                  <div class="text-sm font-semibold text-ink-gray-9">{{ userRow.count }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Berechnet') }}</div>
                  <div class="text-sm font-semibold text-orange-600">{{ formatCurrency(userRow.berechnet) }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Ausgezahlt') }}</div>
                  <div class="text-sm font-semibold text-green-600">{{ formatCurrency(userRow.ausgezahlt) }}</div>
                </div>
                <div class="text-right flex-shrink-0 w-24">
                  <div class="text-xs text-ink-gray-5">{{ __('Gesamt') }}</div>
                  <div class="text-sm font-bold text-ink-gray-9">{{ formatCurrency(userRow.total) }}</div>
                </div>
              </div>
              <!-- Expanded: Lead details -->
              <div v-if="expandedRows[idx]" class="bg-surface-gray-1 px-4 py-2">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="text-ink-gray-5 border-b border-outline-gray-2">
                      <th class="text-left py-1.5 font-medium">{{ __('Lead') }}</th>
                      <th class="text-left py-1.5 font-medium">{{ __('Typ') }}</th>
                      <th class="text-right py-1.5 font-medium">{{ __('Prämie') }}</th>
                      <th class="text-center py-1.5 font-medium">{{ __('Status') }}</th>
                      <th class="text-right py-1.5 font-medium">{{ __('Datum') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="lead in userRow.leads"
                      :key="lead.lead"
                      class="border-b border-outline-gray-1 last:border-0 hover:bg-surface-white transition-colors cursor-pointer"
                      @click.stop="openLead(lead.lead)"
                    >
                      <td class="py-1.5 text-ink-gray-8">
                        <span class="font-medium">{{ lead.lead_name || lead.lead }}</span>
                        <span class="text-ink-gray-4 ml-1">({{ lead.lead }})</span>
                      </td>
                      <td class="py-1.5 text-ink-gray-7">{{ lead.spezialist_typ }}</td>
                      <td class="py-1.5 text-right font-semibold text-ink-gray-9">{{ formatCurrency(lead.praemie) }}</td>
                      <td class="py-1.5 text-center">
                        <span
                          class="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold"
                          :class="statusBadgeClass(lead.status)"
                        >
                          {{ lead.status }}
                        </span>
                      </td>
                      <td class="py-1.5 text-right text-ink-gray-6">{{ formatDate(lead.datum) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar: By Type -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-white">
          <div class="px-4 py-3 border-b border-outline-gray-2">
            <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Prämien pro Produkttyp') }}</h3>
          </div>
          <div v-if="byTyp.length === 0" class="flex items-center justify-center h-32 text-ink-gray-4 text-sm">
            {{ __('Keine Daten') }}
          </div>
          <div v-else class="divide-y divide-outline-gray-1">
            <div
              v-for="typRow in byTyp"
              :key="typRow.typ"
              class="px-4 py-3"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-ink-gray-8">{{ typRow.typ }}</span>
                <span class="text-sm font-bold text-ink-gray-9">{{ formatCurrency(typRow.total) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex-1 mr-3">
                  <div class="h-2 bg-surface-gray-2 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-blue-500 rounded-full transition-all duration-500"
                      :style="{ width: typBarWidth(typRow.total) + '%' }"
                    ></div>
                  </div>
                </div>
                <span class="text-xs text-ink-gray-5 flex-shrink-0">{{ typRow.count }} {{ __('Leads') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Dropdown, FeatherIcon, call } from 'frappe-ui'
import { usePageMeta } from 'frappe-ui'
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// --- Period ---
const periods = [
  { label: 'Diesen Monat', value: 'month' },
  { label: 'Dieses Quartal', value: 'quarter' },
  { label: 'Dieses Jahr', value: 'year' },
  { label: 'Alle', value: 'all' },
]

const activePeriod = ref('month')

const activePeriodLabel = computed(() => {
  const p = periods.find((p) => p.value === activePeriod.value)
  return p ? __(p.label) : __('Diesen Monat')
})

const periodOptions = computed(() =>
  periods.map((p) => ({
    label: __(p.label),
    onClick: () => {
      activePeriod.value = p.value
      reload()
    },
  }))
)

// --- Admin Check ---
const isAdmin = computed(() => {
  const roles = window.frappe?.boot?.user?.roles || []
  return roles.includes('System Manager') || roles.includes('Administrator')
})

// --- Data ---
const loading = ref(false)
const exporting = ref(false)
const summary = ref({
  total_berechnet: 0,
  total_ausgezahlt: 0,
  total_offen: 0,
  count_berechnet: 0,
  count_ausgezahlt: 0,
})
const byUser = ref([])
const byTyp = ref([])
const expandedRows = reactive({})

async function fetchData() {
  loading.value = true
  try {
    const result = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.get_praemien_uebersicht',
      { period: activePeriod.value }
    )
    if (result) {
      summary.value = result.summary || summary.value
      byUser.value = result.by_user || []
      byTyp.value = result.by_typ || []
    }
  } catch (e) {
    console.error('Error fetching Praemien data:', e)
  } finally {
    loading.value = false
  }
}

function reload() {
  Object.keys(expandedRows).forEach((k) => delete expandedRows[k])
  fetchData()
}

onMounted(() => fetchData())

// --- Export ---
async function exportCSV() {
  exporting.value = true
  try {
    const url = `/api/method/crm.fcrm.doctype.crm_lead.crm_lead.export_praemien_csv?period=${activePeriod.value}`
    window.open(url, '_blank')
  } catch (e) {
    console.error('Export error:', e)
  } finally {
    exporting.value = false
  }
}

// --- Row Expand ---
function toggleExpand(idx) {
  if (expandedRows[idx]) {
    delete expandedRows[idx]
  } else {
    expandedRows[idx] = true
  }
}

// --- Navigate to Lead ---
function openLead(leadId) {
  router.push({ name: 'Lead', params: { leadId } })
}

// --- Formatting ---
function formatCurrency(val) {
  if (!val || val === 0) return '0,00 \u20AC'
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(val)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function statusBadgeClass(status) {
  switch (status) {
    case 'Ausgezahlt':
      return 'bg-green-100 text-green-700'
    case 'Berechnet':
      return 'bg-orange-100 text-orange-700'
    case 'Offen':
      return 'bg-gray-100 text-gray-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

// --- Type bar width ---
const maxTypTotal = computed(() => {
  if (byTyp.value.length === 0) return 1
  return Math.max(...byTyp.value.map((t) => t.total), 1)
})

function typBarWidth(total) {
  return Math.max((total / maxTypTotal.value) * 100, 2)
}

usePageMeta(() => ({ title: __('Prämien') }))
</script>
