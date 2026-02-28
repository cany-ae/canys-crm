<template>
  <LayoutHeader v-if="contact.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="contact._actions?.length"
        :actions="contact._actions"
      />
    </template>
  </LayoutHeader>
  <div v-if="contact.doc" ref="parentRef" class="flex h-full">
    <Resizer
      v-if="contact.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          @success="changeContactImage"
          :validateFile="validateIsImageFile"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
                    :label="contact.doc.full_name"
                    :image="contact.doc.image"
                  />
                  <component
                    :is="contact.doc.image ? Dropdown : 'div'"
                    v-bind="
                      contact.doc.image
                        ? {
                            options: [
                              {
                                icon: 'upload',
                                label: contact.doc.image
                                  ? __('Change image')
                                  : __('Upload image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'trash-2',
                                label: __('Remove image'),
                                onClick: () => changeContactImage(''),
                              },
                            ],
                          }
                        : { onClick: openFileSelector }
                    "
                    class="!absolute bottom-0 left-0 right-0"
                  >
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-2 truncate text-ink-gray-9">
                  <div class="truncate text-2xl font-medium">
                    <span v-if="contact.doc.salutation">
                      {{ contact.doc.salutation + '. ' }}
                    </span>
                    <span>{{ contact.doc.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.doc.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    <Avatar
                      size="xs"
                      :label="contact.doc.company_name"
                      :image="
                        getOrganization(contact.doc.company_name)
                          ?.organization_logo
                      "
                    />
                    <span class="">{{ contact.doc.company_name }}</span>
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled && contact.doc.mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  @click="callEnabled && makeCall(contact.doc.mobile_no)"
                />
                <Button
                  v-if="canDelete"
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  iconLeft="trash-2"
                  @click="deleteContact()"
                />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>
    <div v-if="contact.doc.custom_contact_type !== 'Intern'" class="flex flex-1 flex-col overflow-y-auto">
      <!-- Historie Header -->
      <div class="flex items-center gap-2 border-b px-5 py-3">
        <svg class="h-5 w-5 text-ink-gray-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-lg font-semibold text-ink-gray-9">Historie</span>
      </div>

      <!-- Summary -->
      <div class="px-5 py-4">
        <ContactHistory :contactId="props.contactId" />
      </div>

      <!-- Leads Section -->
      <div v-if="historyData.data?.leads?.length" class="border-t px-5 py-4">
        <div class="mb-3 flex items-center gap-2">
          <LeadsIcon class="h-4 w-4 text-ink-gray-5" />
          <span class="text-sm font-semibold text-ink-gray-8">Leads</span>
        </div>
        <div class="flex flex-col gap-2">
          <router-link
            v-for="lead in historyData.data.leads"
            :key="lead.name"
            :to="{ name: 'Lead', params: { leadId: lead.name } }"
            class="flex items-center justify-between rounded-lg border border-outline-gray-modals px-3 py-2 transition-colors hover:bg-surface-gray-2"
          >
            <div class="flex flex-col gap-0.5">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-ink-gray-9">{{ lead.lead_name || lead.name }}</span>
                <span
                  v-if="lead.custom_leadtyp"
                  class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-violet-100 text-violet-700"
                >
                  {{ lead.custom_leadtyp }}
                </span>
              </div>
              <span class="text-xs text-ink-gray-5">{{ lead.email }} &middot; {{ formatDateShort(lead.creation) }}</span>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span
                v-if="lead.custom_liste"
                class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
                :class="getListeBadgeClass(lead.custom_liste)"
              >
                {{ lead.custom_liste }}
              </span>
              <span
                class="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium"
                :class="getLeadBadgeClass(lead.status)"
              >
                <span class="inline-block h-1.5 w-1.5 rounded-full" :class="getLeadDotClass(lead.status)"></span>
                {{ lead.status }}
              </span>
            </div>
          </router-link>
        </div>
      </div>

      <!-- Deals Section -->
      <div v-if="rows.length" class="border-t px-5 py-4">
        <div class="mb-3 flex items-center gap-2">
          <DealsIcon class="h-4 w-4 text-ink-gray-5" />
          <span class="text-sm font-semibold text-ink-gray-8">Deals</span>
        </div>
        <DealsListView
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
      </div>

      <!-- Empty State -->
      <div
        v-if="!historyData.loading && !historyData.data?.leads?.length && !rows.length"
        class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
      >
        <div class="flex flex-col items-center justify-center space-y-3">
          <svg class="h-10 w-10 text-ink-gray-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>Keine Historie vorhanden</div>
        </div>
      </div>
    </div>
    <!-- Interne Kontakte: Nur Deals anzeigen -->
    <div v-else class="flex flex-1 flex-col overflow-y-auto">
      <div class="flex items-center gap-2 border-b px-5 py-3">
        <DealsIcon class="h-5 w-5 text-ink-gray-5" />
        <span class="text-lg font-semibold text-ink-gray-9">Deals</span>
        <Badge v-if="rows.length" variant="solid" theme="gray" size="sm">
          {{ rows.length }}
        </Badge>
      </div>
      <DealsListView
        v-if="rows.length"
        class="mt-4 px-5"
        :rows="rows"
        :columns="columns"
        :options="{ selectable: false, showTooltip: false }"
      />
      <div
        v-else
        class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
      >
        <div class="flex flex-col items-center justify-center space-y-3">
          <DealsIcon class="!h-10 !w-10" />
          <div>Keine Deals vorhanden</div>
        </div>
      </div>
    </div>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'Contact'"
    :docname="contact.doc.name"
    name="Contacts"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import ContactHistory from '@/components/ContactHistory.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  formatDate,
  timeAgo,
  validateIsImageFile,
  setupCustomizations,
} from '@/utils'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { showAddressModal, addressProps } from '@/composables/modals'
import { callEnabled } from '@/composables/settings'
import {
  Badge,
  Breadcrumbs,
  Avatar,
  FileUploader,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
} from 'frappe-ui'
import { ref, computed, h, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const {
  document: contact,
  permissions,
  scripts,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['Contact']?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})
const showDeleteLinkedDocModal = ref(false)

async function deleteContact() {
  showDeleteLinkedDocModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}



const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const historyData = createResource({
  url: 'crm.api.contact.get_contact_history',
  cache: ['contactHistory', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

// Lead status badge helpers
const leadBadgeClasses = {
  'Nicht kontaktiert': { badge: 'bg-gray-100 text-gray-700', dot: 'bg-gray-500' },
  'Kontaktiert': { badge: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500' },
  'Kontaktiert aber nicht erreicht': { badge: 'bg-orange-100 text-orange-700', dot: 'bg-orange-500' },
  'Rückruf geplant': { badge: 'bg-yellow-100 text-yellow-800', dot: 'bg-yellow-500' },
  'Rückruf geplant': { badge: 'bg-yellow-100 text-yellow-800', dot: 'bg-yellow-500' },
  'Termin vereinbart': { badge: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  'Kein Interesse': { badge: 'bg-red-100 text-red-700', dot: 'bg-red-500' },
}
function getLeadBadgeClass(status) {
  return leadBadgeClasses[status]?.badge || 'bg-gray-100 text-gray-700'
}
function getLeadDotClass(status) {
  return leadBadgeClasses[status]?.dot || 'bg-gray-500'
}
function formatDateShort(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// Liste/Phase badge styling
const listeBadgeClasses = {
  '10 - Neu ohne Termin': 'bg-blue-100 text-blue-800',
  '20 - Termin gebucht': 'bg-cyan-100 text-cyan-800',
  '30 - Reaktivierung': 'bg-amber-100 text-amber-800',
  '50 - Closer-Termin': 'bg-indigo-100 text-indigo-800',
  '70 - Follow-up': 'bg-orange-100 text-orange-800',
  '80 - Abschluss gewonnen': 'bg-green-100 text-green-800',
  '90 - Abschluss verloren': 'bg-red-100 text-red-800',
}
function getListeBadgeClass(liste) {
  return listeBadgeClasses[liste] || 'bg-gray-100 text-gray-700'
}

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        if (field.fieldname === 'email_id') {
          return {
            ...field,
            read_only: false,
            fieldtype: 'Dropdown',
            options: (contact.doc?.email_ids || []).map((email) => ({
              name: email.name,
              value: email.email_id,
              selected: email.email_id === contact.doc.email_id,
              placeholder: 'john@doe.com',
              onClick: () => setAsPrimary('email', email.email_id),
              onSave: (option, isNew) =>
                isNew
                  ? createNew('email', option.value)
                  : editOption(
                      'Contact Email',
                      option.name,
                      'email_id',
                      option.value,
                    ),
              onDelete: async (option, isNew) => {
                contact.doc.email_ids = contact.doc.email_ids.filter(
                  (e) => e.name !== option.name,
                )
                if (!isNew) await deleteOption('Contact Email', option.name)
              },
            })),
            create: () => {
              // Add a temporary new option locally (mirrors original behavior)
              contact.doc.email_ids = [
                ...(contact.doc.email_ids || []),
                {
                  name: 'new-1',
                  value: '',
                  selected: false,
                  isNew: true,
                },
              ]
            },
          }
        }
        if (field.fieldname === 'mobile_no') {
          return {
            ...field,
            read_only: false,
            fieldtype: 'Dropdown',
            options: (contact.doc?.phone_nos || []).map((phone) => ({
              name: phone.name,
              value: phone.phone,
              selected: phone.phone === contact.doc.mobile_no,
              onClick: () => setAsPrimary('mobile_no', phone.phone),
              onSave: (option, isNew) =>
                isNew
                  ? createNew('phone', option.value)
                  : editOption(
                      'Contact Phone',
                      option.name,
                      'phone',
                      option.value,
                    ),
              onDelete: async (option, isNew) => {
                contact.doc.phone_nos = contact.doc.phone_nos.filter(
                  (p) => p.name !== option.name,
                )
                if (!isNew) await deleteOption('Contact Phone', option.name)
              },
            })),
            create: () => {
              contact.doc.phone_nos = [
                ...(contact.doc.phone_nos || []),
                {
                  name: 'new-1',
                  value: '',
                  selected: false,
                  isNew: true,
                },
              ]
            },
          }
        }
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (_value, close) => {
              openAddressModal()
              close && close()
            },
            edit: (address) => openAddressModal(address),
          }
        }
        return field
      }),
    })),
  }))
})

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: contact.doc.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact updated'))
  }
}

async function createNew(field, value) {
  if (!value) return
  let d = await call('crm.api.contact.create_new', {
    contact: contact.doc.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact updated'))
  }
}

async function editOption(doctype, name, fieldname, value) {
  let d = await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact updated'))
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  toast.success(__('Contact updated'))
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    annual_revenue: getFormattedCurrency('annual_revenue', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: {
      label: formatDate(deal.modified),
      timeAgo: __(timeAgo(deal.modified)),
    },
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'annual_revenue',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile no'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]

function openAddressModal(_address) {
  showAddressModal.value = true
  addressProps.value = {
    doctype: 'Address',
    address: _address,
  }
}

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField: contact.setValue.submit,
        createToast: toast.create,
        deleteDoc: deleteContact,
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
