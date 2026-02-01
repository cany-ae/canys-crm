<template>
  <ActivityHeader
    v-model="tabIndex"
    v-model:showWhatsappTemplates="showWhatsappTemplates"
    v-model:showFilesUploader="showFilesUploader"
    :tabs="tabs"
    :title="title"
    :doc="doc"
    :emailBox="emailBox"
    :whatsappBox="whatsappBox"
    :modalRef="modalRef"
  />
  <FadedScrollableDiv class="flex flex-col h-full overflow-y-auto">
    <div
      v-if="all_activities?.loading"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>
    <div v-else-if="title == 'Events'" class="h-full activity">
      <EventArea :doctype="doctype" :docname="docname" />
    </div>
    <div v-else-if="title == 'InvoiceTool'" class="h-full overflow-y-auto">
      <AngebotArea :leadId="docname" @angebotCreated="openEmailWithAngebot" />
    </div>
    <div
      v-else-if="
        activities?.length ||
        (whatsappMessages.data?.length && title == 'WhatsApp')
      "
      class="activities"
    >
      <div v-if="title == 'WhatsApp' && whatsappMessages.data?.length">
        <WhatsAppArea
          class="px-3 sm:px-10"
          v-model="whatsappMessages"
          v-model:reply="replyMessage"
          :messages="whatsappMessages.data"
        />
      </div>
      <div
        v-else-if="title == 'Notes'"
        class="grid grid-cols-1 gap-4 px-3 pb-3 sm:px-10 sm:pb-5 lg:grid-cols-2 xl:grid-cols-3"
      >
        <div v-for="note in activities" @click="modalRef.showNote(note)">
          <NoteArea :note="note" v-model="all_activities" />
        </div>
      </div>
      <div v-else-if="title == 'Comments'" class="pb-5">
        <div v-for="(comment, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 px-3 sm:gap-4 sm:px-10"
          >
            <div
              class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
              :class="
                i != activities.length - 1 ? 'before:h-full' : 'before:h-4'
              "
            >
              <div
                class="flex h-8 w-7 items-center justify-center bg-surface-white"
              >
                <CommentIcon class="text-ink-gray-8" />
              </div>
            </div>
            <CommentArea class="mb-4" :activity="comment" />
          </div>
        </div>
      </div>
      <div v-else-if="title == 'Tasks'" class="px-3 pb-3 sm:px-10 sm:pb-5">
        <TaskArea :modalRef="modalRef" :tasks="activities" :doctype="doctype" />
      </div>
      <div v-else-if="title == 'Calls'" class="activity">
        <div v-for="(call, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10"
          >
            <div
              class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
              :class="
                i != activities.length - 1 ? 'before:h-full' : 'before:h-4'
              "
            >
              <div
                class="flex h-8 w-7 items-center justify-center bg-surface-white text-ink-gray-8"
              >
                <MissedCallIcon
                  v-if="call.status == 'No Answer'"
                  class="text-ink-red-4"
                />
                <DeclinedCallIcon v-else-if="call.status == 'Busy'" />
                <component
                  v-else
                  :is="
                    call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon
                  "
                />
              </div>
            </div>
            <CallArea class="mb-4" :activity="call" />
          </div>
        </div>
      </div>
      <div
        v-else-if="title == 'Attachments'"
        class="px-3 pb-3 sm:px-10 sm:pb-5"
      >
        <AttachmentArea
          :attachments="activities"
          @reload="all_activities.reload() && scroll()"
        />
      </div>

      <div
        v-else
        v-for="(activity, i) in activities"
        class="activity px-3 sm:px-10"
        :class="
          ['Activity', 'Emails'].includes(title)
            ? 'grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4'
            : ''
        "
      >
        <div
          v-if="['Activity', 'Emails'].includes(title)"
          class="z-0 relative flex justify-center before:absolute before:left-[50%] before:-z-[1] before:top-0 before:border-l before:border-outline-gray-modals"
          :class="[i != activities.length - 1 ? 'before:h-full' : 'before:h-4']"
        >
          <div
            class="flex h-7 w-7 items-center justify-center bg-surface-white"
            :class="{
              'mt-2.5': ['communication'].includes(activity.activity_type),
              'bg-surface-white': ['added', 'removed', 'changed'].includes(
                activity.activity_type,
              ),
              'h-8': [
                'comment',
                'communication',
                'incoming_call',
                'outgoing_call',
              ].includes(activity.activity_type),
            }"
          >
            <UserAvatar
              v-if="activity.activity_type == 'communication'"
              :user="activity.data.sender"
              size="md"
            />
            <MissedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'No Answer'
              "
              class="text-ink-red-4"
            />
            <DeclinedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'Busy'
              "
            />
            <div
              v-else-if="activity.activity_type == 'status_change'"
              class="flex h-6 w-6 items-center justify-center rounded-full"
              :class="statusChangeIconBgClass(activity.data?.value)"
            >
              <StatusChangeIcon class="h-3 w-3 text-white" />
            </div>
            <component
              v-else
              :is="activity.icon"
              :class="
                ['added', 'removed', 'changed'].includes(activity.activity_type)
                  ? 'text-ink-gray-4'
                  : 'text-ink-gray-8'
              "
            />
          </div>
        </div>
        <div
          v-if="activity.activity_type == 'communication'"
          class="pb-5 mt-px"
        >
          <EmailArea :activity="activity" :emailBox="emailBox" />
        </div>
        <div
          class="mb-4"
          :id="activity.name"
          v-else-if="activity.activity_type == 'comment'"
        >
          <CommentArea :activity="activity" />
        </div>
        <div
          class="mb-4 flex flex-col gap-2 py-1.5"
          :id="activity.name"
          v-else-if="activity.activity_type == 'attachment_log'"
        >
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              class="inline-flex items-center flex-wrap gap-1.5 text-ink-gray-8 font-medium"
            >
              <span class="font-medium">{{ activity.owner_name }}</span>
              <span class="text-ink-gray-5">{{ __(activity.data.type) }}</span>
              <a
                v-if="activity.data.file_url"
                :href="activity.data.file_url"
                target="_blank"
              >
                <span>{{ activity.data.file_name }}</span>
              </a>
              <span v-else>{{ activity.data.file_name }}</span>
              <FeatherIcon
                v-if="activity.data.is_private"
                name="lock"
                class="size-3"
              />
            </div>
            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="formatDate(activity.creation)">
                <div class="text-sm text-ink-gray-5">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
        </div>
        <div
          v-else-if="
            activity.activity_type == 'incoming_call' ||
            activity.activity_type == 'outgoing_call'
          "
          class="mb-4"
        >
          <CallArea :activity="activity" />
        </div>
        <div v-else-if="activity.activity_type == 'status_change'"
          class="relative -mx-4 my-4"
        >
          <div
            class="relative overflow-hidden rounded-xl border-2 shadow-lg"
            :class="statusChangeBorderClass(activity.data?.value)"
          >
            <div class="h-1.5 w-full bg-gradient-to-r from-transparent via-white/40 to-transparent animate-pulse"
              :class="statusChangeIconBgClass(activity.data?.value)"
            ></div>
            <div class="relative px-5 py-4">
              <div class="absolute inset-0 opacity-[0.04]"
                :class="statusChangeIconBgClass(activity.data?.value)"
              ></div>
              <div class="relative flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <div class="flex items-center justify-center w-7 h-7 rounded-full ring-2 ring-white shadow-md"
                    :class="statusChangeIconBgClass(activity.data?.value)"
                  >
                    <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                    </svg>
                  </div>
                  <span class="text-xs font-bold uppercase tracking-widest"
                    :class="statusChangeTextClass(activity.data?.value)"
                  >
                    {{ __('Status Update') }}
                  </span>
                </div>
                <Tooltip :text="formatDate(activity.creation)">
                  <div class="text-[11px] text-gray-400 font-medium">
                    {{ __(timeAgo(activity.creation)) }}
                  </div>
                </Tooltip>
              </div>
              <div class="relative flex items-center gap-3 mb-3">
                <div class="flex-1 min-w-0">
                  <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold opacity-60 bg-gray-100 text-gray-500 ring-1 ring-gray-200 line-through decoration-1">
                    <span class="w-2 h-2 rounded-full flex-shrink-0" :class="statusDotClass(activity.data?.old_value)"></span>
                    <span class="truncate">{{ activity.data?.old_value }}</span>
                  </div>
                </div>
                <div class="flex-shrink-0 flex items-center gap-0.5">
                  <div class="w-6 h-0.5 rounded-full" :class="statusChangeIconBgClass(activity.data?.value)"></div>
                  <div class="w-8 h-0.5 rounded-full animate-pulse" :class="statusChangeIconBgClass(activity.data?.value)"></div>
                  <svg class="w-5 h-5 -ml-1" :class="statusChangeTextClass(activity.data?.value)" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold shadow-md ring-2 ring-offset-1"
                    :class="statusBadgeClass(activity.data?.value)"
                  >
                    <span class="relative flex h-2.5 w-2.5 flex-shrink-0">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :class="statusDotClass(activity.data?.value)"></span>
                      <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="statusDotClass(activity.data?.value)"></span>
                    </span>
                    <span class="truncate">{{ activity.data?.value }}</span>
                  </div>
                </div>
              </div>
              <div class="relative flex items-center gap-1 text-[10px] text-gray-400 mt-1">
                <span>{{ activity.owner_name }}</span>
              </div>
            </div>
            <div class="h-1 w-full" :class="statusChangeIconBgClass(activity.data?.value)"></div>
          </div>
        </div>
        <div v-else class="mb-4 flex flex-col gap-2 py-1.5">
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              v-if="activity.other_versions"
              class="inline-flex flex-wrap gap-1.5 text-ink-gray-8 font-medium"
            >
              <span>{{ activity.show_others ? __('Hide') : __('Show') }}</span>
              <span> +{{ activity.other_versions.length + 1 }} </span>
              <span>{{ __('changes from') }}</span>
              <span>{{ activity.owner_name }}</span>
              <Button
                class="!size-4"
                variant="ghost"
                :icon="SelectIcon"
                @click="activity.show_others = !activity.show_others"
              />
            </div>
            <div
              v-else
              class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5"
            >
              <span class="font-medium text-ink-gray-8">
                {{ activity.owner_name }}
              </span>
              <span v-if="activity.type">{{ __(activity.type) }}</span>
              <span
                v-if="activity.data?.field_label"
                class="max-w-xs truncate font-medium text-ink-gray-8"
              >
                {{ __(activity.data.field_label) }}
              </span>
              <span v-if="activity.value">{{ __(activity.value) }}</span>
              <span
                v-if="activity.data?.old_value"
                class="max-w-xs font-medium text-ink-gray-8"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.old_value" size="xs" />
                  {{ getUser(activity.data.old_value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.old_value }}
                </div>
              </span>
              <span v-if="activity.to">{{ __('to') }}</span>
              <span
                v-if="activity.data?.value"
                class="max-w-xs font-medium text-ink-gray-8"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.value" size="xs" />
                  {{ getUser(activity.data.value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.value }}
                </div>
              </span>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="formatDate(activity.creation)">
                <div class="text-sm text-ink-gray-5">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.other_versions && activity.show_others"
            class="flex flex-col gap-0.5"
          >
            <div
              v-for="activity in [activity, ...activity.other_versions]"
              class="flex items-start justify-stretch gap-2 py-1.5 text-base"
            >
              <div class="inline-flex flex-wrap gap-1 text-ink-gray-5">
                <span
                  v-if="activity.data?.field_label"
                  class="max-w-xs truncate text-ink-gray-5"
                >
                  {{ __(activity.data.field_label) }}
                </span>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-ink-gray-5"
                />
                <span v-if="activity.type">
                  {{ startCase(__(activity.type)) }}
                </span>
                <span
                  v-if="activity.data?.old_value"
                  class="max-w-xs font-medium text-ink-gray-8"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.old_value" size="xs" />
                    {{ getUser(activity.data.old_value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.old_value }}
                  </div>
                </span>
                <span v-if="activity.to">{{ __('to') }}</span>
                <span
                  v-if="activity.data?.value"
                  class="max-w-xs font-medium text-ink-gray-8"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.value" size="xs" />
                    {{ getUser(activity.data.value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.value }}
                  </div>
                </span>
              </div>

              <div class="ml-auto whitespace-nowrap">
                <Tooltip :text="formatDate(activity.creation)">
                  <div class="text-sm text-ink-gray-5">
                    {{ __(timeAgo(activity.creation)) }}
                  </div>
                </Tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="title == 'Data'" class="h-full flex flex-col px-3 sm:px-10">
      <DataFields
        :doctype="doctype"
        :docname="docname"
        @beforeSave="(data) => emit('beforeSave', data)"
        @afterSave="(data) => emit('afterSave', data)"
      />
    </div>
    <div
      v-else
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <component :is="emptyTextIcon" class="h-10 w-10" />
      <span>{{ __(emptyText) }}</span>
      <MultiActionButton v-if="title == 'Calls'" :options="callActions" />
      <Button
        v-else-if="title == 'Notes'"
        :label="__('Create Note')"
        @click="modalRef.showNote()"
      />
      <Button
        v-else-if="title == 'Emails'"
        :label="__('New Email')"
        @click="emailBox.show = true"
      />
      <Button
        v-else-if="title == 'Comments'"
        :label="__('New Comment')"
        @click="emailBox.showComment = true"
      />
      <Button
        v-else-if="title == 'Tasks'"
        :label="__('Create Task')"
        @click="modalRef.showTask()"
      />
      <Button
        v-else-if="title == 'Attachments'"
        :label="__('Upload Attachment')"
        @click="showFilesUploader = true"
      />
    </div>
  </FadedScrollableDiv>
  <div>
    <CommunicationArea
      ref="emailBox"
      v-if="['Emails', 'Comments', 'Activity'].includes(title)"
      v-model="doc"
      v-model:reload="reload_email"
      :doctype="doctype"
      @scroll="scroll"
    />
    <WhatsAppBox
      ref="whatsappBox"
      v-if="title == 'WhatsApp'"
      v-model="doc"
      v-model:reply="replyMessage"
      v-model:whatsapp="whatsappMessages"
      :doctype="doctype"
      @scroll="scroll"
    />
  </div>
  <WhatsappTemplateSelectorModal
    v-if="whatsappEnabled"
    v-model="showWhatsappTemplates"
    :doctype="doctype"
    @send="(t) => sendTemplate(t)"
  />
  <AllModals
    ref="modalRef"
    v-model="all_activities"
    v-model:events="events"
    :doctype="doctype"
    :doc="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    :doctype="doctype"
    :docname="docname"
    @after="
      () => {
        all_activities.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>
<script setup>
import ActivityHeader from '@/components/Activities/ActivityHeader.vue'
import EmailArea from '@/components/Activities/EmailArea.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import CallArea from '@/components/Activities/CallArea.vue'
import NoteArea from '@/components/Activities/NoteArea.vue'
import TaskArea from '@/components/Activities/TaskArea.vue'
import AttachmentArea from '@/components/Activities/AttachmentArea.vue'
import AngebotArea from '@/components/Activities/AngebotArea.vue'
import DataFields from '@/components/Activities/DataFields.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EventArea from '@/components/Activities/EventArea.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import WhatsAppBox from '@/components/Activities/WhatsAppBox.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import MultiActionButton from '@/components/MultiActionButton.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import StatusChangeIcon from '@/components/Icons/StatusChangeIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import SelectIcon from '@/components/Icons/SelectIcon.vue'
import MissedCallIcon from '@/components/Icons/MissedCallIcon.vue'
import DeclinedCallIcon from '@/components/Icons/DeclinedCallIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import WhatsappTemplateSelectorModal from '@/components/Modals/WhatsappTemplateSelectorModal.vue'
import AllModals from '@/components/Activities/AllModals.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import { timeAgo, formatDate, startCase } from '@/utils'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { Button, Tooltip, createResource } from 'frappe-ui'
import { useElementVisibility } from '@vueuse/core'
import {
  ref,
  computed,
  h,
  markRaw,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute } from 'vue-router'

const { makeCall, $socket } = globalStore()
const { getUser } = usersStore()

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  docname: {
    type: String,
    default: '',
  },
  tabs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['beforeSave', 'afterSave'])

const route = useRoute()

const reload = defineModel('reload')
const tabIndex = defineModel('tabIndex')

const { document: _document } = useDocument(props.doctype, props.docname)

const doc = computed(() => _document.doc || {})

const reload_email = ref(false)
const modalRef = ref(null)
const showFilesUploader = ref(false)

const title = computed(() => props.tabs?.[tabIndex.value]?.name || 'Activity')

const changeTabTo = (tabName) => {
  const tabNames = props.tabs?.map((tab) => tab.name?.toLowerCase())
  const index = tabNames?.indexOf(tabName)
  if (index == -1) return
  tabIndex.value = index
}

const all_activities = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: props.docname },
  cache: ['activity', props.docname],
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments]) => {
    return { versions, calls, notes, tasks, attachments }
  },
  onSuccess: () => nextTick(() => scroll()),
})

const showWhatsappTemplates = ref(false)

const whatsappMessages = createResource({
  url: 'crm.api.whatsapp.get_whatsapp_messages',
  cache: ['whatsapp_messages', props.docname],
  params: {
    reference_doctype: props.doctype,
    reference_name: props.docname,
  },
  auto: whatsappEnabled.value,
  transform: (data) => sortByCreation(data),
  onSuccess: () => nextTick(() => scroll()),
})

onBeforeUnmount(() => {
  $socket.off('whatsapp_message')
})

onMounted(() => {
  $socket.on('whatsapp_message', (data) => {
    if (
      data.reference_doctype === props.doctype &&
      data.reference_name === props.docname
    ) {
      whatsappMessages.reload()
    }
  })

  nextTick(() => {
    const hash = route.hash.slice(1) || null
    let tabNames = props.tabs?.map((tab) => tab.name)
    if (!tabNames?.includes(hash)) {
      scroll(hash)
    }
  })
})

function sendTemplate(template) {
  showWhatsappTemplates.value = false
  capture('send_whatsapp_template', { doctype: props.doctype })
  createResource({
    url: 'crm.api.whatsapp.send_whatsapp_template',
    params: {
      reference_doctype: props.doctype,
      reference_name: props.docname,
      to: doc.value.mobile_no,
      template,
    },
    auto: true,
  })
}

const replyMessage = ref({})

function get_activities() {
  if (!all_activities.data?.versions) return []
  if (!all_activities.data?.calls.length)
    return all_activities.data.versions || []
  return [...all_activities.data.versions, ...all_activities.data.calls]
}

const activities = computed(() => {
  let _activities = []
  if (title.value == 'Activity') {
    _activities = get_activities()
  } else if (title.value == 'Emails') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'communication',
    )
  } else if (title.value == 'StatusUpdates') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'status_change',
    )
  } else if (title.value == 'Comments') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'comment',
    )
  } else if (title.value == 'Calls') {
    if (!all_activities.data?.calls) return []
    return sortByCreation(all_activities.data.calls)
  } else if (title.value == 'Tasks') {
    if (!all_activities.data?.tasks) return []
    return sortByModified(all_activities.data.tasks)
  } else if (title.value == 'Notes') {
    if (!all_activities.data?.notes) return []
    return sortByModified(all_activities.data.notes)
  } else if (title.value == 'Attachments') {
    if (!all_activities.data?.attachments) return []
    return sortByModified(all_activities.data.attachments)
  }

  _activities.forEach((activity) => {
    activity.icon = timelineIcon(activity.activity_type, activity.is_lead)

    if (
      activity.activity_type == 'incoming_call' ||
      activity.activity_type == 'outgoing_call' ||
      activity.activity_type == 'communication'
    )
      return

    update_activities_details(activity)

    if (activity.other_versions) {
      activity.show_others = false
      activity.other_versions.forEach((other_version) => {
        update_activities_details(other_version)
      })
    }
  })
  return sortByCreation(_activities)
})

function sortByCreation(list) {
  return list.sort((a, b) => new Date(a.creation) - new Date(b.creation))
}
function sortByModified(list) {
  return list.sort((b, a) => new Date(a.modified) - new Date(b.modified))
}

function update_activities_details(activity) {
  activity.owner_name = getUser(activity.owner).full_name
  activity.type = ''
  activity.value = ''
  activity.to = ''

  if (activity.activity_type == 'creation') {
    activity.type = activity.data
  } else if (activity.activity_type == 'status_change') {
    activity.type = 'changed'
    activity.value = 'from'
    activity.to = 'to'
  } else if (activity.activity_type == 'added') {
    activity.type = 'added'
    activity.value = 'as'
  } else if (activity.activity_type == 'removed') {
    activity.type = 'removed'
    activity.value = 'value'
  } else if (activity.activity_type == 'changed') {
    activity.type = 'changed'
    activity.value = 'from'
    activity.to = 'to'
  }
}

const emptyText = computed(() => {
  let text = 'No Activities'
  if (title.value == 'StatusUpdates') {
    text = 'No Status Updates'
  } else if (title.value == 'Emails') {
    text = 'No Email Communications'
  } else if (title.value == 'Comments') {
    text = 'No Comments'
  } else if (title.value == 'Data') {
    text = 'No Data'
  } else if (title.value == 'Calls') {
    text = 'No Call Logs'
  } else if (title.value == 'Notes') {
    text = 'No Notes'
  } else if (title.value == 'Tasks') {
    text = 'No Tasks'
  } else if (title.value == 'Attachments') {
    text = 'No Attachments'
  } else if (title.value == 'WhatsApp') {
    text = 'No WhatsApp Messages'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon
  if (title.value == 'StatusUpdates') {
    icon = ActivityIcon
  } else if (title.value == 'Emails') {
    icon = Email2Icon
  } else if (title.value == 'Comments') {
    icon = CommentIcon
  } else if (title.value == 'Data') {
    icon = DetailsIcon
  } else if (title.value == 'Calls') {
    icon = PhoneIcon
  } else if (title.value == 'Notes') {
    icon = NoteIcon
  } else if (title.value == 'Tasks') {
    icon = TaskIcon
  } else if (title.value == 'Attachments') {
    icon = AttachmentIcon
  } else if (title.value == 'WhatsApp') {
    icon = WhatsAppIcon
  }
  return h(icon, { class: 'text-ink-gray-4' })
})

function timelineIcon(activity_type, is_lead) {
  let icon
  switch (activity_type) {
    case 'creation':
      icon = is_lead ? LeadsIcon : DealsIcon
      break
    case 'deal':
      icon = DealsIcon
      break
    case 'comment':
      icon = CommentIcon
      break
    case 'event':
      icon = CalendarIcon
      break
    case 'incoming_call':
      icon = InboundCallIcon
      break
    case 'outgoing_call':
      icon = OutboundCallIcon
      break
    case 'attachment_log':
      icon = AttachmentIcon
      break
    case 'status_change':
      icon = StatusChangeIcon
      break
    default:
      icon = DotIcon
  }

  return markRaw(icon)
}

const emailBox = ref(null)
const whatsappBox = ref(null)

watch([reload, reload_email], ([reload_value, reload_email_value]) => {
  if (reload_value || reload_email_value) {
    all_activities.reload()
    _document.reload()
    reload.value = false
    reload_email.value = false
  }
})

function scroll(hash) {
  if (['tasks', 'notes', 'events'].includes(route.hash?.slice(1))) return
  setTimeout(() => {
    let el
    if (!hash) {
      let e = document.getElementsByClassName('activity')
      el = e[e.length - 1]
    } else {
      el = document.getElementById(hash)
    }
    if (el && !useElementVisibility(el).value) {
      el.scrollIntoView({ behavior: 'smooth' })
      el.focus()
    }
  }, 500)
}

const callActions = computed(() => {
  let actions = [
    {
      label: __('Log a Call'),
      onClick: () => modalRef.value.createCallLog(),
    },
    {
      label: __('Make a Call'),
      onClick: () => makeCall(doc.value.mobile_no),
      condition: () => callEnabled.value,
    },
  ]

  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})


const STATUS_COLORS = {
  'Nicht kontaktiert': 'gray',
  'Kontaktiert': 'blue',
  'Nicht erreicht': 'orange',
  'Kontaktiert aber nicht erreicht': 'orange',
  'Rueckruf geplant': 'yellow',
  'Rückruf geplant': 'yellow',
  'Termin vereinbart': 'green',
  'Kein Interesse': 'red',
}

function getStatusColor(status) {
  return STATUS_COLORS[status] || 'gray'
}

function statusChangeBorderClass(status) {
  const colorMap = {
    gray: 'border-gray-400 bg-gray-50',
    blue: 'border-blue-500 bg-blue-50',
    orange: 'border-orange-500 bg-orange-50',
    yellow: 'border-yellow-500 bg-yellow-50',
    green: 'border-green-500 bg-green-50',
    red: 'border-red-500 bg-red-50',
  }
  return colorMap[getStatusColor(status)] || colorMap.gray
}

function statusChangeIconBgClass(status) {
  const colorMap = {
    gray: 'bg-gray-500',
    blue: 'bg-blue-600',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-600',
    red: 'bg-red-500',
  }
  return colorMap[getStatusColor(status)] || colorMap.gray
}

function statusChangeTextClass(status) {
  const colorMap = {
    gray: 'text-gray-800',
    blue: 'text-blue-800',
    orange: 'text-orange-800',
    yellow: 'text-yellow-800',
    green: 'text-green-800',
    red: 'text-red-800',
  }
  return colorMap[getStatusColor(status)] || colorMap.gray
}

function statusBadgeClass(status) {
  const colorMap = {
    gray: 'bg-gray-100 text-gray-700 ring-1 ring-gray-300',
    blue: 'bg-blue-100 text-blue-700 ring-1 ring-blue-300',
    orange: 'bg-orange-100 text-orange-700 ring-1 ring-orange-300',
    yellow: 'bg-yellow-100 text-yellow-800 ring-1 ring-yellow-300',
    green: 'bg-green-100 text-green-700 ring-1 ring-green-300',
    red: 'bg-red-100 text-red-700 ring-1 ring-red-300',
  }
  return colorMap[getStatusColor(status)] || colorMap.gray
}

function statusDotClass(status) {
  const colorMap = {
    gray: 'bg-gray-500',
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
  }
  return colorMap[getStatusColor(status)] || colorMap.gray
}

function openEmailWithAngebot(fileData) {
  changeTabTo('emails')
  nextTick(() => {
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('open-email-with-angebot', {
        detail: {
          fileData,
          lead: doc.value,
        },
      }))
    }, 300)
  })
}

defineExpose({ emailBox, all_activities, changeTabTo })
</script>
