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
  <ViewControls
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Contact"
  />
  <ContactsListView
    ref="contactsListView"
    v-if="contacts.data && filteredRows.length"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :rows="filteredRows"
    :columns="contacts.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
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
import { ref, computed, onMounted, nextTick } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()

const showContactModal = ref(false)
const contactsListView = ref(null)

// Tab state
const activeTab = ref('kunden')
const contactTabs = [
  { key: 'kunden', label: 'Kunden' },
  { key: 'intern', label: 'Intern' },
]

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
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

// Force-Reload beim Navigieren zurueck zur Liste (Cache-Bypass)
onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      if (viewControls.value?.reload) {
        viewControls.value.reload()
      }
    }, 300)
  })
})

// Frontend-Filter nach Tab
const filteredRows = computed(() => {
  if (activeTab.value === 'intern') {
    return rows.value.filter(r => r._contact_type === 'Intern')
  }
  // Kunden: alles was nicht Intern ist (inkl. leer/Kunde)
  return rows.value.filter(r => r._contact_type !== 'Intern')
})
</script>