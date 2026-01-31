<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="doc.status"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getLeadStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button
        :label="__('In Deal umwandeln')"
        variant="solid"
        theme="green"
        size="md"
        @click="showConvertToDealModal = true"
      >
        <template #prefix>
          <FeatherIcon name="arrow-right-circle" class="h-4 w-4" />
        </template>
      </Button>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
    >
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="saveChanges"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(leadId)"
      >
        {{ __(leadId) }}
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateIsImageFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="title"
                :image="doc.image"
              />
              <component
                :is="doc.image ? Dropdown : 'div'"
                v-bind="
                  doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: doc.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="doc.lead_name || __('Set first name')">
                <div class="truncate text-2xl font-medium text-ink-gray-9">
                  {{ title }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled"
                  :tooltip="__('Make a call')"
                  :icon="PhoneIcon"
                  @click="
                    () => {
                      if (doc.mobile_no) {
                        makeCall(doc.mobile_no)
                        setTimeout(() => triggerStatusPrompt('call'), 2000)
                      } else {
                        toast.error(__('No phone number set'))
                      }
                    }
                  "
                />

                <Button
                  :tooltip="__('Send an email')"
                  :icon="Email2Icon"
                  @click="
                    doc.email ? openEmailBoxWithPrompt() : toast.error(__('No email set'))
                  "
                />
                <Button
                  :tooltip="__('Go to website')"
                  :icon="LinkIcon"
                  @click="
                    doc.website
                      ? openWebsite(doc.website)
                      : toast.error(__('No website set'))
                  "
                />

                <Button
                  :tooltip="__('Attach a file')"
                  :icon="AttachmentIcon"
                  @click="showFilesUploader = true"
                />

                <Button
                  v-if="canDelete"
                  :tooltip="__('Delete')"
                  variant="subtle"
                  theme="red"
                  icon="trash-2"
                  @click="deleteLead"
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <!-- Current Status Box -->
      <div class="sticky top-0 z-10 border-b bg-surface-white px-5 py-3">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">Aktueller Status</span>
        </div>
        <div class="flex items-center gap-2 mb-2">
          <Dropdown :options="statuses" placement="right">
            <template #default="{ open }">
              <button
                class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold transition-all duration-150 w-full"
                :class="statusBoxBadgeClass"
              >
                <span class="relative flex h-3 w-3 flex-shrink-0">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :class="statusDotClass"></span>
                  <span class="relative inline-flex rounded-full h-3 w-3" :class="statusDotClass"></span>
                </span>
                {{ doc.status }}
                <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="ml-auto h-3.5 w-3.5" />
              </button>
            </template>
          </Dropdown>
        </div>
        <div class="flex flex-col gap-1 text-xs text-ink-gray-5">
          <div class="flex items-center gap-1.5" v-if="lastStatusChange">
            <FeatherIcon name="clock" class="h-3 w-3" />
            <span>{{ __('Letzte Änderung') }}: {{ lastStatusChange }}</span>
          </div>
          <div class="flex items-center gap-1.5" v-if="lastActivity">
            <FeatherIcon name="activity" class="h-3 w-3" />
            <span>{{ __('Letzte Aktivität') }}: {{ lastActivity }}</span>
          </div>
        </div>
      </div>
      <SLASection
        v-if="doc.sla_status"
        v-model="doc"
        @updateField="updateField"
      />
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Lead"
          :docname="leadId"
          @reload="sections.reload"
          @afterFieldChange="reloadAssignees"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    name="Leads"
  />
  <StatusUpdatePrompt
    v-if="showStatusPrompt"
    v-model:show="showStatusPrompt"
    :leadName="doc.lead_name"
    :currentStatus="doc.status"
    :triggerAction="statusPromptAction"
    @statusChanged="handleStatusPromptChange"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import StatusUpdatePrompt from '@/components/StatusUpdatePrompt.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  timeAgo,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  FeatherIcon,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)
const showStatusPrompt = ref(false)
const statusPromptAction = ref('call')

const { triggerOnChange, assignees, permissions, document, scripts, error } =
  useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: props.leadId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Lead']?.title_field || 'name'
  return doc.value?.[t] || props.leadId
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('lead', customStatuses, triggerStatusChange)
})

const statusColorMap = {
  'gray': { badge: 'bg-gray-100 text-gray-700 hover:bg-gray-200', dot: 'bg-gray-500' },
  'blue': { badge: 'bg-blue-100 text-blue-700 hover:bg-blue-200', dot: 'bg-blue-500' },
  'orange': { badge: 'bg-orange-100 text-orange-700 hover:bg-orange-200', dot: 'bg-orange-500' },
  'yellow': { badge: 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200', dot: 'bg-yellow-500' },
  'green': { badge: 'bg-green-100 text-green-700 hover:bg-green-200', dot: 'bg-green-500' },
  'red': { badge: 'bg-red-100 text-red-700 hover:bg-red-200', dot: 'bg-red-500' },
  'purple': { badge: 'bg-purple-100 text-purple-700 hover:bg-purple-200', dot: 'bg-purple-500' },
}

const statusBadgeClass = computed(() => {
  let s = getLeadStatus(doc.value.status)
  let colorName = (s?.color || 'gray').replace('text-', '')
  return statusColorMap[colorName]?.badge || statusColorMap['gray'].badge
})

const statusDotClass = computed(() => {
  let s = getLeadStatus(doc.value.status)
  let colorName = (s?.color || 'gray').replace('text-', '')
  return statusColorMap[colorName]?.dot || statusColorMap['gray'].dot
})

const statusBoxBadgeClass = computed(() => {
  let s = getLeadStatus(doc.value.status)
  let colorName = (s?.color || 'gray').replace('text-', '')
  const map = {
    'gray': 'bg-gray-100 text-gray-800 hover:bg-gray-200',
    'blue': 'bg-blue-100 text-blue-800 hover:bg-blue-200',
    'orange': 'bg-orange-100 text-orange-800 hover:bg-orange-200',
    'yellow': 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    'green': 'bg-green-100 text-green-800 hover:bg-green-200',
    'red': 'bg-red-100 text-red-800 hover:bg-red-200',
    'purple': 'bg-purple-100 text-purple-800 hover:bg-purple-200',
  }
  return map[colorName] || map['gray']
})

const lastStatusChange = computed(() => {
  if (!activities.value?.all_activities?.data?.versions) return null
  const statusChanges = activities.value.all_activities.data.versions.filter(
    a => a.activity_type === 'status_change'
  )
  if (statusChanges.length) {
    const last = statusChanges[statusChanges.length - 1]
    return timeAgo(last.creation)
  }
  return null
})

const lastActivity = computed(() => {
  if (!activities.value?.all_activities?.data?.versions) return null
  const versions = activities.value.all_activities.data.versions
  if (versions.length) {
    const last = versions[versions.length - 1]
    if (last.activity_type === 'communication') return 'E-Mail'
    if (last.activity_type === 'comment') return 'Kommentar'
    if (last.activity_type === 'status_change') return 'Status Update'
    if (last.activity_type === 'incoming_call' || last.activity_type === 'outgoing_call') return 'Anruf'
    return timeAgo(last.creation)
  }
  return null
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  return [
    {
      name: 'Activity',
      label: __('Alle Aktivitäten'),
      icon: ActivityIcon,
    },
    {
      name: 'StatusUpdates',
      label: __('Status Updates'),
      icon: ActivityIcon,
    },
    {
      name: 'Calls',
      label: __('Anrufe'),
      icon: PhoneIcon,
    },
    {
      name: 'Emails',
      label: __('E-Mails'),
      icon: EmailIcon,
    },
    {
      name: 'Attachments',
      label: __('Anhänge'),
      icon: AttachmentIcon,
    },
    {
      name: 'Events',
      label: __('Veranstaltungen'),
      icon: EventIcon,
    },
    {
      name: 'Notes',
      label: __('Notizen'),
      icon: NoteIcon,
    },
    {
      name: 'InvoiceTool',
      label: __('Angebotstool'),
      icon: DetailsIcon,
    },
    {
      name: 'Data',
      label: __('Daten'),
      icon: DetailsIcon,
    },
  ]
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  document.save.submit()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

function openEmailBoxWithPrompt() {
  openEmailBox()
  // Watch for email reload (indicates email was sent)
  const unwatch = watch(
    () => reload.value,
    (newVal) => {
      if (newVal) {
        unwatch()
        setTimeout(() => triggerStatusPrompt('email'), 1000)
      }
    },
  )
  // Auto-cleanup after 5 minutes
  setTimeout(() => unwatch(), 300000)
}

function saveChanges(data) {
  document.save.submit(null, {
    onSuccess: () => reloadAssignees(data),
  })
}

function reloadAssignees(data) {
  if (data?.hasOwnProperty('lead_owner')) {
    assignees.reload()
  }
}

// Status Update Prompt - nach Anruf, E-Mail, Task, Event
onMounted(() => {
  // Listen for call events
  $socket.on('crm_call_completed', (data) => {
    if (data.reference_name === props.leadId) {
      statusPromptAction.value = 'call'
      showStatusPrompt.value = true
    }
  })
})

onBeforeUnmount(() => {
  $socket.off('crm_call_completed')
})

// Trigger status prompt after email send
const originalOpenEmailBox = openEmailBox
watch(
  () => reload.value,
  (newVal) => {
    if (newVal) {
      // Check if latest activity was an email send or call
      // The reload trigger fires after saves including email sends
    }
  },
)

function triggerStatusPrompt(action) {
  statusPromptAction.value = action
  showStatusPrompt.value = true
}

async function handleStatusPromptChange(newStatus, note) {
  // Update the lead status
  await triggerOnChange('status', newStatus)
  document.save.submit(null, {
    onSuccess: () => {
      reload.value = true
      // Add note as comment if provided
      if (note && note.trim()) {
        call('frappe.client.insert', {
          doc: {
            doctype: 'Comment',
            comment_type: 'Comment',
            reference_doctype: 'CRM Lead',
            reference_name: props.leadId,
            content: note,
          },
        }).then(() => {
          reload.value = true
        })
      }
      toast.success(__('Status aktualisiert'))
    },
    onError: (err) => {
      toast.error(err.messages?.[0] || __('Fehler beim Status-Update'))
    },
  })
}

// Expose triggerStatusPrompt for child components
defineExpose({ triggerStatusPrompt })
</script>
