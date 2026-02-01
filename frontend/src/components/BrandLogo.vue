<template>
  <div>
    <img :src="logoUrl" class="h-full w-full object-contain" />
  </div>
</template>

<script setup>
const brand = defineModel()
const logoUrl = '/files/allianz_logo.png'
</script>
