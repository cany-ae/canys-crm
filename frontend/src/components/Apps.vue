<template>
  <a
    href="/apps"
    :class="[
      active ? 'bg-surface-gray-3' : 'text-ink-gray-6',
      'group w-full flex h-7 items-center rounded px-2 text-base hover:bg-surface-gray-2',
    ]"
  >
    <div class="flex gap-2">
      <AppsIcon class="size-4" />
      <span class="whitespace-nowrap">
        {{ __('Apps') }}
      </span>
    </div>
  </a>
</template>
<script setup>
import AppsIcon from '@/components/Icons/AppsIcon.vue'

const props = defineProps({
  active: Boolean,
})
</script>
