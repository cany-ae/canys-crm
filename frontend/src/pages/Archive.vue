<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: __('Archiv'), route: { name: 'Archive' } }]" />
    </template>
  </LayoutHeader>
  <div class="flex items-center gap-2 sm:px-5 px-3 py-2 border-b border-outline-gray-1">
    <div class="flex items-center gap-0.5">
      <button
        class="px-3 py-1 text-xs font-medium rounded-md transition-all duration-150"
        :class="activeTab === 'leads'
          ? 'bg-amber-100 text-amber-900 dark:bg-amber-800 dark:text-amber-100'
          : 'text-ink-gray-5 hover:text-ink-gray-7'"
        @click="activeTab = 'leads'"
      >
        {{ __('Leads') }}
      </button>
      <button
        class="px-3 py-1 text-xs font-medium rounded-md transition-all duration-150"
        :class="activeTab === 'deals'
          ? 'bg-amber-100 text-amber-900 dark:bg-amber-800 dark:text-amber-100'
          : 'text-ink-gray-5 hover:text-ink-gray-7'"
        @click="activeTab = 'deals'"
      >
        {{ __('Deals') }}
      </button>
    </div>
    <div class="flex items-center gap-1.5 text-xs text-amber-600">
      <FeatherIcon name="archive" class="h-3 w-3" />
      <span v-if="activeTab === 'leads'">{{ totalLeads }} Leads im Archiv</span>
      <span v-else>{{ totalDeals }} Deals im Archiv</span>
    </div>
  </div>
  
  <!-- Leads Tab -->
  <div v-if="activeTab === 'leads'" class="flex-1 overflow-y-auto">
    <div v-if="leadsLoading" class="flex h-full items-center justify-center">
      <div class="text-ink-gray-4">Laden...</div>
    </div>
    <table v-else-if="leadRows.length" class="w-full text-sm">
      <thead class="sticky top-0 bg-surface-white z-10 border-b">
        <tr>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[11rem]">Name</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[10rem]">Leadtyp</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[12rem]">Mobilfunknummer</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[11rem]">Zugewiesen zu</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[13rem]">Phase</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[10rem]">Ergebnis</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[9rem]">Datum</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="lead in leadRows"
          :key="lead.name"
          class="border-b hover:bg-surface-gray-1 cursor-pointer transition-colors"
          @click="openLead(lead.name)"
        >
          <td class="px-4 py-2.5 truncate">
            <div class="flex items-center gap-2">
              <Avatar :label="lead.first_name || lead.lead_name" size="sm" />
              <span class="truncate font-medium text-ink-gray-9">{{ lead.lead_name }}</span>
            </div>
          </td>
          <td class="px-4 py-2.5 truncate text-ink-gray-7">{{ lead.custom_leadtyp || '-' }}</td>
          <td class="px-4 py-2.5 truncate text-ink-gray-7">{{ lead.mobile_no || '-' }}</td>
          <td class="px-4 py-2.5 truncate">
            <div v-if="getAssignee(lead._assign)" class="flex items-center gap-1.5">
              <Avatar :image="getUser(getAssignee(lead._assign)).user_image" :label="getUser(getAssignee(lead._assign)).full_name" size="xs" />
              <span class="truncate text-ink-gray-7">{{ getUser(getAssignee(lead._assign)).full_name }}</span>
            </div>
            <span v-else class="text-ink-gray-4">-</span>
          </td>
          <td class="px-4 py-2.5">
            <span
              v-if="lead.custom_liste"
              class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium"
              :style="{ backgroundColor: getPhaseHex(lead.custom_liste) + '20', color: getPhaseHex(lead.custom_liste) }"
            >
              <span class="inline-block h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: getPhaseHex(lead.custom_liste) }"></span>
              {{ lead.custom_liste.replace(/^\d+\s*-\s*/, '') }}
            </span>
          </td>
          <td class="px-4 py-2.5">
            <Badge
              v-if="lead.converted"
              variant="subtle"
              theme="blue"
              size="sm"
              label="In Deal umgewandelt"
            />
            <Badge
              v-else-if="lead.custom_liste && lead.custom_liste.startsWith('80')"
              variant="subtle"
              theme="green"
              size="sm"
              label="Gewonnen"
            />
            <Badge
              v-else-if="lead.custom_liste && lead.custom_liste.startsWith('90')"
              variant="subtle"
              theme="red"
              size="sm"
              label="Verloren"
            />
          </td>
          <td class="px-4 py-2.5 text-ink-gray-5 text-xs">{{ formatDate(lead.modified) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="flex h-full items-center justify-center">
      <div class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4">
        <FeatherIcon name="archive" class="h-10 w-10" />
        <span>{{ __('Keine archivierten Leads') }}</span>
      </div>
    </div>
  </div>

  <!-- Deals Tab -->
  <div v-if="activeTab === 'deals'" class="flex-1 overflow-y-auto">
    <div v-if="dealsLoading" class="flex h-full items-center justify-center">
      <div class="text-ink-gray-4">Laden...</div>
    </div>
    <table v-else-if="dealRows.length" class="w-full text-sm">
      <thead class="sticky top-0 bg-surface-white z-10 border-b">
        <tr>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[14rem]">Organisation</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[10rem]">Status</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[11rem]">Zugewiesen zu</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[12rem]">Betrag</th>
          <th class="px-4 py-2 text-left text-xs font-medium text-ink-gray-5 w-[9rem]">Datum</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="deal in dealRows"
          :key="deal.name"
          class="border-b hover:bg-surface-gray-1 cursor-pointer transition-colors"
          @click="openDeal(deal.name)"
        >
          <td class="px-4 py-2.5 truncate font-medium text-ink-gray-9">{{ deal.organization || deal.lead_name || deal.name }}</td>
          <td class="px-4 py-2.5">
            <Badge
              :variant="'subtle'"
              :theme="deal.status === 'Won' ? 'green' : deal.status === 'Lost' ? 'red' : 'gray'"
              size="sm"
              :label="deal.status === 'Won' ? 'Gewonnen' : deal.status === 'Lost' ? 'Verloren' : deal.status"
            />
          </td>
          <td class="px-4 py-2.5 truncate">
            <div v-if="getAssignee(deal._assign)" class="flex items-center gap-1.5">
              <Avatar :image="getUser(getAssignee(deal._assign)).user_image" :label="getUser(getAssignee(deal._assign)).full_name" size="xs" />
              <span class="truncate text-ink-gray-7">{{ getUser(getAssignee(deal._assign)).full_name }}</span>
            </div>
            <span v-else class="text-ink-gray-4">-</span>
          </td>
          <td class="px-4 py-2.5 text-ink-gray-7">{{ deal.annual_revenue ? formatCurrency(deal.annual_revenue) : '-' }}</td>
          <td class="px-4 py-2.5 text-ink-gray-5 text-xs">{{ formatDate(deal.modified) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="flex h-full items-center justify-center">
      <div class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4">
        <FeatherIcon name="archive" class="h-10 w-10" />
        <span>{{ __('Keine archivierten Deals') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { usePipelinePhases } from '@/composables/usePipelinePhases'
import { formatDate } from '@/utils'
import { Avatar, Badge, FeatherIcon, call } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { ref, computed, onMounted, watch } from 'vue'

const router = useRouter()
const { getUser } = usersStore()
const { getPhaseHex } = usePipelinePhases()

const activeTab = ref('leads')

// Leads data
const leadRows = ref([])
const leadsLoading = ref(true)
const totalLeads = computed(() => leadRows.value.length)

// Deals data
const dealRows = ref([])
const dealsLoading = ref(true)
const totalDeals = computed(() => dealRows.value.length)

function getAssignee(assignStr) {
  if (!assignStr) return null
  try {
    const arr = JSON.parse(assignStr)
    return arr.length ? arr[0] : null
  } catch {
    return null
  }
}

function formatCurrency(val) {
  if (!val) return '-'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(val)
}

function openLead(name) {
  router.push({ name: 'Lead', params: { leadId: name } })
}

function openDeal(name) {
  router.push({ name: 'Deal', params: { dealId: name } })
}

async function fetchLeads() {
  leadsLoading.value = true
  try {
    const result = await call('frappe.client.get_list', {
      doctype: 'CRM Lead',
      filters: [
        ['custom_liste', 'IN', ['80 - Abschluss gewonnen', '90 - Abschluss verloren']],
      ],
      or_filters: [
        ['converted', '=', 1],
      ],
      fields: ['name', 'lead_name', 'first_name', 'mobile_no', 'custom_leadtyp', 'custom_liste', '_assign', 'modified', 'converted', 'image'],
      order_by: 'modified desc',
      limit_page_length: 500,
    })
    leadRows.value = result || []
  } catch (e) {
    // Fallback: fetch with simple OR logic
    try {
      // Fetch closed leads
      const closed = await call('frappe.client.get_list', {
        doctype: 'CRM Lead',
        filters: { custom_liste: ['IN', ['80 - Abschluss gewonnen', '90 - Abschluss verloren']] },
        fields: ['name', 'lead_name', 'first_name', 'mobile_no', 'custom_leadtyp', 'custom_liste', '_assign', 'modified', 'converted', 'image'],
        order_by: 'modified desc',
        limit_page_length: 500,
      })
      // Fetch converted leads
      const converted = await call('frappe.client.get_list', {
        doctype: 'CRM Lead',
        filters: { converted: 1 },
        fields: ['name', 'lead_name', 'first_name', 'mobile_no', 'custom_leadtyp', 'custom_liste', '_assign', 'modified', 'converted', 'image'],
        order_by: 'modified desc',
        limit_page_length: 500,
      })
      // Merge and deduplicate
      const seen = new Set()
      const all = []
      for (const row of [...(closed || []), ...(converted || [])]) {
        if (!seen.has(row.name)) {
          seen.add(row.name)
          all.push(row)
        }
      }
      all.sort((a, b) => new Date(b.modified) - new Date(a.modified))
      leadRows.value = all
    } catch (e2) {
      console.error('Failed to load archive leads:', e2)
      leadRows.value = []
    }
  }
  leadsLoading.value = false
}

async function fetchDeals() {
  dealsLoading.value = true
  try {
    const result = await call('frappe.client.get_list', {
      doctype: 'CRM Deal',
      filters: { status: ['IN', ['Won', 'Lost']] },
      fields: ['name', 'organization', 'lead_name', 'status', '_assign', 'annual_revenue', 'modified'],
      order_by: 'modified desc',
      limit_page_length: 500,
    })
    dealRows.value = result || []
  } catch (e) {
    console.error('Failed to load archive deals:', e)
    dealRows.value = []
  }
  dealsLoading.value = false
}

onMounted(() => {
  fetchLeads()
  fetchDeals()
})
</script>
