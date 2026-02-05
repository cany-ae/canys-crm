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
      <ListRowItem v-else :item="item" :align="column.align">
        <template #prefix>
          <div v-if="column.key === 'status'" class="flex items-center">
            <span
              class="inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-semibold"
              :class="getStatusBadgeClass(item)"
            >
              <span class="inline-block h-1.5 w-1.5 rounded-full" :class="getStatusDotClass(item)"></span>
            </span>
          </div>
          <div v-else-if="column.key === 'lead_name'">
            <Avatar
              v-if="item.label"
              class="flex items-center"
              :image="item.image"
              :label="item.image_label"
              size="sm"
            />
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
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
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
import { ref, computed, watch } from 'vue'
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


const STATUS_COLOR_MAP = {
  'Nicht kontaktiert': 'gray',
  'Kontaktiert': 'blue',
  'Kontaktiert aber nicht erreicht': 'orange',
  'Nicht erreicht': 'orange',
  'Rückruf geplant': 'yellow',
  'Rueckruf geplant': 'yellow',
  'Termin vereinbart': 'green',
  'Kein Interesse': 'red',
}

function getStatusColor(item) {
  const statusName = item?.label || ''
  return STATUS_COLOR_MAP[statusName] || 'gray'
}

function getStatusBadgeClass(item) {
  const color = getStatusColor(item)
  const map = {
    gray: 'bg-gray-100 text-gray-700',
    blue: 'bg-blue-100 text-blue-700',
    orange: 'bg-orange-100 text-orange-700',
    yellow: 'bg-yellow-100 text-yellow-800',
    green: 'bg-green-100 text-green-700',
    red: 'bg-red-100 text-red-700',
  }
  return map[color] || map.gray
}

function getStatusDotClass(item) {
  const color = getStatusColor(item)
  const map = {
    gray: 'bg-gray-500',
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
  }
  return map[color] || map.gray
}

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
