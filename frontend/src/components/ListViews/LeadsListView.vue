<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
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
            {{ label }}
          </div>
        </template>
      </ListRowItem>
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
  <ListFooter
    v-if="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Lead" />
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
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
])

const route = useRoute()

const pageLengthCount = defineModel()
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
