<template>
  <ListView
    :class="$attrs.class"
    :columns="computedColumns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Lead',
        params: { leadId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      :rows="rows"
      v-slot="{ idx, column, item, row }"
      doctype="CRM Lead"
    >
      <div v-if="column.key === '_assign'" class="flex items-center">
        <MultipleAvatar
          :avatars="item"
          size="sm"
          @click="
            (event) =>
              emit('applyFilter', {
                event,
                idx,
                column,
                item,
                firstColumn: columns[0],
              })
          "
        />
      </div>
      <div v-else-if="column.key === 'custom_termin_datum'" class="truncate text-base">
        <span v-if="item.label" class="inline-flex items-center gap-1 text-xs">
          <svg class="h-3.5 w-3.5 text-ink-gray-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>{{ item.label }}</span>
        </span>
        <span v-else class="text-xs text-ink-gray-4">–</span>
      </div>
      <ListRowItem v-else :item="item" :align="column.align">
        <template #prefix>
          <div v-if="column.key === 'lead_name'" class="relative">
            <Avatar
              v-if="item.label"
              class="flex items-center"
              :image="item.image"
              :label="item.image_label"
              size="sm"
            />
            <span
              v-if="isOverdue(row)"
              class="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-500 ring-2 ring-white"
              :title="__('Überfällig')"
            >
              <span class="text-[6px] font-bold text-white leading-none">!</span>
            </span>
          </div>
          <div v-else-if="column.key === 'lead_owner'">
            <Avatar
              v-if="item.full_name"
              class="flex items-center"
              :image="item.user_image"
              :label="item.full_name"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'mobile_no'" class="flex items-center gap-1">
            <PhoneIcon class="h-4 w-4" />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="
              [
                'modified',
                'creation',
                'first_response_time',
                'first_responded_on',
                'response_by',
              ].includes(column.key)
            "
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              v-if="column.key == '_liked_by'"
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="
                () =>
                  emit('likeDoc', {
                    name: row.name,
                    liked: isLiked(item),
                  })
              "
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div
            v-else-if="column.key === 'lead_name'"
            class="truncate text-base"
          >
            <span class="inline-flex items-center gap-1.5">
              <span class="truncate">{{ item.label }}</span>
              <Tooltip v-if="isOverdue(row)" :text="__('Überfälliger Follow-up')">
                <span class="inline-flex items-center gap-0.5 rounded px-1 py-px text-[10px] font-semibold leading-tight bg-red-100 text-red-700 whitespace-nowrap flex-shrink-0">
                  <svg class="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M12 2l10 18H2L12 2z" />
                  </svg>
                  Überfällig
                </span>
              </Tooltip>
            </span>
          </div>
          <div
            v-else-if="column.key === 'custom_liste' && item.phase_color"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <span
              class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold whitespace-nowrap"
              :class="getListeBadgeClass(item.phase_color)"
            >
              {{ item.label }}
            </span>
          </div>
          <div
            v-else-if="column.key === 'custom_leadtyp' && item.label"
            class="truncate text-base"
          >
            <span
              class="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium bg-surface-gray-2 text-ink-gray-7"
            >
              {{ item.label }}
            </span>
          </div>
          <div
            v-else-if="column.key === 'sla_status'"
            class="truncate text-base"
          >
            <Badge
              v-if="item.value"
              :variant="'subtle'"
              :theme="item.color"
              size="md"
              :label="item.value"
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            />
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div
            v-else
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ __(label) }}
          </div>
        </template>
      </ListRowItem>
      <div v-if="column.key === '_actions'" class="flex items-center justify-end gap-1">
        <Tooltip :text="__('Anrufen')">
          <Button
            variant="ghost"
            size="sm"
            @click.stop.prevent="emit('quickCall', row)"
          >
            <PhoneIcon class="h-3.5 w-3.5 text-ink-gray-5 hover:text-ink-gray-9" />
          </Button>
        </Tooltip>
        <Tooltip :text="__('E-Mail')">
          <Button
            variant="ghost"
            size="sm"
            @click.stop.prevent="emit('quickMail', row)"
          >
            <Email2Icon class="h-3.5 w-3.5 text-ink-gray-5 hover:text-ink-gray-9" />
          </Button>
        </Tooltip>
        <Tooltip :text="__('Notiz')">
          <Button
            variant="ghost"
            size="sm"
            @click.stop.prevent="emit('quickNote', row)"
          >
            <NoteIcon class="h-3.5 w-3.5 text-ink-gray-5 hover:text-ink-gray-9" />
          </Button>
        </Tooltip>
      </div>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <div class="flex items-center justify-between border-t px-5 py-2">
    <span class="text-sm text-ink-gray-5">
      {{ paginationStart }}–{{ paginationEnd }} {{ __('von') }} {{ options.totalCount || rows.length }}
    </span>
    <div class="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        :disabled="currentPage <= 1"
        @click="emit('prevPage')"
      >
        <FeatherIcon name="chevron-left" class="h-4 w-4" />
      </Button>
      <span class="text-sm text-ink-gray-5 px-2">
        {{ __('Seite') }} {{ currentPage }} {{ __('von') }} {{ totalPages }}
      </span>
      <Button
        variant="ghost"
        size="sm"
        :disabled="currentPage >= totalPages"
        @click="emit('nextPage')"
      >
        <FeatherIcon name="chevron-right" class="h-4 w-4" />
      </Button>
    </div>
  </div>
  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Lead" />
  <Teleport to="body">
    <LeadHoverPopup
      v-if="hoveredLead"
      :lead-name="hoveredLead"
      :x="hoverPos.x"
      :y="hoverPos.y"
    />
  </Teleport>
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import LeadHoverPopup from '@/components/LeadHoverPopup.vue'
import {
  Avatar,
  Button,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  Dropdown,
  Tooltip,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { usePipelinePhases } from '@/composables/usePipelinePhases'
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})
const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
  'quickCall',
  'quickMail',
  'quickNote',
  'prevPage',
  'nextPage',
])

const route = useRoute()
const { getListeBadgeClass: _getListeBadgeClass } = usePipelinePhases()

const pageLengthCount = defineModel()

const computedColumns = computed(() => {
  return [
    ...props.columns,
    { label: '', key: '_actions', width: '7rem' },
  ]
})
const list = defineModel('list')

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

const PAGE_SIZE = 50

const currentPage = computed(() => {
  return props.options.currentPage || 1
})

const totalPages = computed(() => {
  return props.options.totalPages || Math.max(1, Math.ceil((props.options.totalCount || 0) / PAGE_SIZE))
})

const paginationStart = computed(() => {
  const total = props.options.totalCount || 0
  return total ? ((currentPage.value - 1) * PAGE_SIZE) + 1 : 0
})

const paginationEnd = computed(() => {
  return Math.min(currentPage.value * PAGE_SIZE, props.options.totalCount || 0)
})

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

// Hover popup state
const hoveredLead = ref(null)
const hoverPos = ref({ x: 0, y: 0 })
const hoverTimer = ref(null)

function onRowMouseLeave() {
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value)
    hoverTimer.value = null
  }
  hoveredLead.value = null
}

function formatTerminZeit(zeit) {
  if (!zeit || zeit === 'None' || zeit === 'null') return ''
  // zeit can be "HH:MM:SS" or "HH:MM" or timedelta string
  const str = String(zeit).trim()
  // Extract HH:MM from various formats
  const match = str.match(/^(\d{1,2}):(\d{2})/)
  if (!match) return ''
  const hh = match[1].padStart(2, '0')
  const mm = match[2]
  return hh + ':' + mm
}

// Badge classes loaded from composable
function getListeBadgeClass(color) {
  return _getListeBadgeClass(color)
}



// Overdue detection: check if custom_naechster_kontakt is in the past
// and lead is not in closed phases (80/90)
function isOverdue(row) {
  const nk = row.custom_naechster_kontakt
  if (!nk || nk === 'None' || nk === 'null') return false
  // Exclude closed phases (80 = Abschluss gewonnen, 90 = Abschluss verloren)
  const liste = row.custom_liste
  if (liste && typeof liste === 'object') {
    const phase = liste.phase_short
    if (phase === '80' || phase === '90') return false
  }
  // nk is raw ISO-ish value from API e.g. "2026-02-25" or "2026-02-25 00:00:00"
  const nkDate = new Date(nk)
  if (isNaN(nkDate.getTime())) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return nkDate < today
}

// Hover delegation via document-level event bubbling
onMounted(() => {
  document.addEventListener('mouseover', handleHoverDelegate)
  document.addEventListener('mouseout', handleHoverOutDelegate)
  document.addEventListener('click', handleClickDismissPopup, true)
})

onBeforeUnmount(() => {
  if (hoverTimer.value) clearTimeout(hoverTimer.value)
  document.removeEventListener('mouseover', handleHoverDelegate)
  document.removeEventListener('mouseout', handleHoverOutDelegate)
  document.removeEventListener('click', handleClickDismissPopup, true)
})

function handleClickDismissPopup() {
  // Instantly hide popup on any click so it never blocks navigation
  if (hoverTimer.value) {
    clearTimeout(hoverTimer.value)
    hoverTimer.value = null
  }
  hoveredLead.value = null
}

function handleHoverDelegate(event) {
  // frappe-ui ListRow renders as <a> (router-link) with href containing /leads/CRM-LEAD-XXXXX
  const link = event.target.closest('a[href]')
  if (!link) return

  const href = link.getAttribute('href') || ''
  // Match /leads/CRM-LEAD-XXXXX pattern
  const match = href.match(/\/leads\/(CRM-LEAD-[^?/]+)/)
  if (!match) return

  const leadName = decodeURIComponent(match[1])

  // Update position on every mouseover
  hoverPos.value = { x: event.clientX, y: event.clientY }

  // If same lead, just update position
  if (hoveredLead.value === leadName) return

  // Debounce new lead
  if (hoverTimer.value) clearTimeout(hoverTimer.value)
  hoverTimer.value = setTimeout(() => {
    hoveredLead.value = leadName
    hoverPos.value = { x: event.clientX, y: event.clientY }
  }, 300)
}

function handleHoverOutDelegate(event) {
  const link = event.target.closest('a[href]')
  if (!link) return

  // Check if we're moving to a child element (still in the same row link)
  const related = event.relatedTarget
  if (related && link.contains(related)) return

  onRowMouseLeave()
}

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
