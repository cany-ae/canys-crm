<template>
  <!-- Futuristischer AI Button -->
  <button 
    v-if="!isOpen" 
    @click="openSidebar" 
    class="ai-fab"
    title="KI-Assistent öffnen"
  >
    <span class="ai-fab-pulse"></span>
    <svg class="ai-fab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
      <circle cx="7.5" cy="14.5" r="1.5" fill="currentColor"/>
      <circle cx="16.5" cy="14.5" r="1.5" fill="currentColor"/>
    </svg>
  </button>

  <!-- Sidebar Overlay -->
  <Teleport to="body">
    <div 
      v-if="isOpen" 
      class="ai-sidebar-overlay"
      @click.self="closeSidebar"
    >
      <div class="ai-sidebar" :class="{ open: isOpen }">
        <div class="ai-sidebar-header">
          <div class="ai-sidebar-title">
            <div class="ai-sidebar-title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
                <circle cx="7.5" cy="14.5" r="1.5" fill="currentColor"/>
                <circle cx="16.5" cy="14.5" r="1.5" fill="currentColor"/>
              </svg>
            </div>
            <span>KI-Assistent</span>
          </div>
          <button class="ai-sidebar-close" @click="closeSidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="ai-sidebar-body">
          <div v-if="!iframeLoaded" class="ai-sidebar-loader">
            <div class="ai-loader-spinner"></div>
          </div>
          <iframe 
            v-show="iframeLoaded"
            ref="aiIframe"
            class="ai-sidebar-iframe" 
            :src="openWebUIUrl"
            @load="onIframeLoad"
          ></iframe>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const openWebUIUrl = 'https://chat.eco.canys.de'
const isOpen = ref(false)
const iframeLoaded = ref(false)
const aiIframe = ref(null)

function openSidebar() {
  isOpen.value = true
  document.addEventListener('keydown', handleEscape)
}

function closeSidebar() {
  isOpen.value = false
  document.removeEventListener('keydown', handleEscape)
}

function handleEscape(e) {
  if (e.key === 'Escape') closeSidebar()
}

function onIframeLoad() {
  iframeLoaded.value = true
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
/* Futuristischer AI Button */
.ai-fab {
  position: fixed;
  bottom: 28px;
  right: 28px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  border: none;
  cursor: pointer;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 4px 20px rgba(99, 102, 241, 0.5),
    0 0 40px rgba(139, 92, 246, 0.3),
    inset 0 1px 0 rgba(255,255,255,0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.ai-fab::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    rgba(255,255,255,0.1) 60deg,
    transparent 120deg
  );
  animation: ai-rotate 3s linear infinite;
}

.ai-fab::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
}

@keyframes ai-rotate {
  100% { transform: rotate(360deg); }
}

.ai-fab:hover {
  transform: scale(1.1);
  box-shadow: 
    0 8px 30px rgba(99, 102, 241, 0.6),
    0 0 60px rgba(139, 92, 246, 0.4),
    inset 0 1px 0 rgba(255,255,255,0.3);
}

.ai-fab:active {
  transform: scale(0.95);
}

.ai-fab-icon {
  position: relative;
  z-index: 1;
  width: 32px;
  height: 32px;
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

/* Pulsierender Ring */
.ai-fab-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid rgba(139, 92, 246, 0.6);
  animation: ai-pulse 2s ease-out infinite;
}

@keyframes ai-pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

/* Sidebar */
.ai-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 10000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.ai-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 420px;
  max-width: 100vw;
  height: 100vh;
  background: #0f0f14;
  z-index: 10001;
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 40px rgba(0,0,0,0.5);
  animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.ai-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, #1a1a24 0%, #0f0f14 100%);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.ai-sidebar-title {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.ai-sidebar-title-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-sidebar-title-icon svg {
  width: 16px;
  height: 16px;
  color: white;
}

.ai-sidebar-close {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.ai-sidebar-close:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.ai-sidebar-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.ai-sidebar-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #0f0f14;
}

.ai-sidebar-loader {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f0f14;
}

.ai-loader-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(139, 92, 246, 0.2);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: ai-spin 1s linear infinite;
}

@keyframes ai-spin {
  100% { transform: rotate(360deg); }
}

/* Mobile */
@media (max-width: 480px) {
  .ai-fab {
    width: 56px;
    height: 56px;
    bottom: 20px;
    right: 20px;
  }
  .ai-fab-icon {
    width: 26px;
    height: 26px;
  }
  .ai-sidebar {
    width: 100vw;
  }
}
</style>
