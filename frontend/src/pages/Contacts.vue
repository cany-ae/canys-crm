<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>
  <!-- Tab Navigation -->
  <div class="flex border-b px-5">
    <button
      v-for="tab in contactTabs"
      :key="tab.key"
      @click="activeTab = tab.key"
      class="px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px"
      :class="activeTab === tab.key
        ? 'border-surface-gray-7 text-ink-gray-9'
        : 'border-transparent text-ink-gray-5 hover:text-ink-gray-7'"
    >
      {{ tab.label }}
    </button>
  </div>
  <!-- Search bar -->
  <div class="px-5 pt-3 pb-1">
    <div class="relative">
      <FeatherIcon name="search" class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-gray-4" />
      <input
        v-model="searchQuery"
        type="text"
        :placeholder="__('Suche nach Name oder Nummer...')"
        class="w-full rounded-md border border-outline-gray-2 bg-surface-gray-1 py-1.5 pl-9 pr-3 text-sm text-ink-gray-8 placeholder:text-ink-gray-4 focus:border-outline-gray-3 focus:outline-none focus:ring-1 focus:ring-outline-gray-3"
      />
      <button
        v-if="searchQuery"
        @click="searchQuery = ''"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-ink-gray-4 hover:text-ink-gray-6"
      >
        <FeatherIcon name="x" class="h-4 w-4" />
      </button>
    </div>
  </div>
  <ViewControls
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
    :options="{
      lockView: true,
      hideColumnsButton: true,
    }"
  />
  <ContactsListView
    ref="contactsListView"
    v-if="contacts.data && filteredRows.length"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="paginatedRows"
    :columns="contacts.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: paginatedRows.length,
      totalCount: filteredRows.length,
      currentPage: contactPage,
      totalPages: contactTotalPages,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"

    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
    @prevPage="contactPrevPage"
    @nextPage="contactNextPage"
  />
  <div
    v-else-if="contacts.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <ContactsIcon class="h-10 w-10" />
      <span>{{ activeTab === 'intern' ? __('Keine internen Kontakte vorhanden') : __('Keine Kundenkontakte vorhanden') }}</span>
      <Button
        :label="__('Create')"
        iconLeft="plus"
        @click="showContactModal = true"
      />
    </div>
  </div>
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{}"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed, onMounted, nextTick, watch } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()

const showContactModal = ref(false)
const searchQuery = ref('')
const contactPage = ref(1)
const contactsListView = ref(null)

// Tab state
const activeTab = ref('kunden')
const contactTabs = computed(() => {
  const kundenCount = rows.value.filter(r => r._contact_type !== 'Intern').length
  const internCount = rows.value.filter(r => r._contact_type === 'Intern').length
  return [
    { key: 'kunden', label: 'Kunden (' + kundenCount + ')' },
    { key: 'intern', label: 'Intern (' + internCount + ')' },
  ]
})

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(999)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    // Store raw contact_type for filtering
    _rows._contact_type = contact.custom_contact_type || 'Kunde'
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(contact[row]),
          timeAgo: __(timeAgo(contact[row])),
        }
      }
    })
    return _rows
  })
})

// Force-Reload beim Navigieren zurueck zur Liste.
// frappe-ui createResource gibt bei gleichem Cache-Key das gecachte
// Resource-Objekt mit alten Daten zurueck (ohne auto-reload).
// Wir setzen fetched=false damit der naechste reload() nicht uebersprungen
// wird, und erzwingen dann einen frischen Server-Fetch.
onMounted(() => {
  nextTick(() => {
    if (contacts.value) {
      contacts.value.fetched = false
      contacts.value.previousData = null
      if (contacts.value.reload) {
        contacts.value.reload()
      }
    }
  })
})

// Smart Tab Switch: Wenn nach einem Data-Update der aktive Tab leer ist
// aber der andere Tab Eintraege hat, automatisch zum gefuellten Tab wechseln.
// Das loest das Problem, dass nach Typ-Aenderung der Kontakt "verschwindet",
// weil der User auf dem nun leeren Tab bleibt.
watch(rows, (newRows) => {
  if (!newRows.length) return
  const kundenRows = newRows.filter(r => r._contact_type !== 'Intern')
  const internRows = newRows.filter(r => r._contact_type === 'Intern')

  if (activeTab.value === 'kunden' && kundenRows.length === 0 && internRows.length > 0) {
    activeTab.value = 'intern'
  } else if (activeTab.value === 'intern' && internRows.length === 0 && kundenRows.length > 0) {
    activeTab.value = 'kunden'
  }
}, { immediate: true })

// Frontend-Filter nach Tab
const filteredRows = computed(() => {
  let result = rows.value
  // Tab filter
  if (activeTab.value === 'intern') {
    result = result.filter(r => r._contact_type === 'Intern')
  } else {
    result = result.filter(r => r._contact_type !== 'Intern')
  }
  // Search filter
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(r => {
      const firstName = (r.first_name || r.full_name?.label || '').toLowerCase()
      const lastName = (r.last_name || '').toLowerCase()
      const fullName = (r.full_name?.label || '').toLowerCase()
      const mobile = (r.mobile_no || '').toLowerCase()
      const email = (r.email_id || '').toLowerCase()
      return firstName.includes(q) || lastName.includes(q) || fullName.includes(q) || mobile.includes(q) || email.includes(q)
    })
  }
  return result
})

const CONTACTS_PAGE_SIZE = 50

const paginatedRows = computed(() => {
  const start = (contactPage.value - 1) * CONTACTS_PAGE_SIZE
  return filteredRows.value.slice(start, start + CONTACTS_PAGE_SIZE)
})

const contactTotalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredRows.value.length / CONTACTS_PAGE_SIZE))
})

// Reset page when filter/search/tab changes
watch([activeTab, searchQuery], () => {
  contactPage.value = 1
})

function contactPrevPage() {
  if (contactPage.value > 1) contactPage.value--
}

function contactNextPage() {
  if (contactPage.value < contactTotalPages.value) contactPage.value++
}
</script>
