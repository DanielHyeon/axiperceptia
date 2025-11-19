<template>
  <div id="app">
    <header class="app-header glass">
      <div class="header-content">
        <div class="logo-section">
          <h1>🚀 Business OS</h1>
          <span class="badge">Beta</span>
        </div>
        <p>LLM 기반 이벤트 드리븐 온톨로지 시스템</p>
      </div>
    </header>
    
    <main class="app-main">
      <EventStormCanvas />
    </main>
    
    <footer class="app-footer">
      <p>Palantir 스타일 3-Layer 온톨로지 + Given-When-Then 룰 엔진</p>
    </footer>
  </div>
</template>

<script setup>
import EventStormCanvas from './components/EventStormCanvas.vue'
</script>

<style>
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
}

.app-header {
  background: var(--header-gradient);
  color: white;
  padding: 1rem 2rem;
  box-shadow: var(--shadow-md);
  z-index: 10;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-header h1 {
  font-size: 1.5rem;
  color: white;
  margin: 0;
}

.app-header p {
  opacity: 0.9;
  font-size: 0.9rem;
  margin: 0;
}

.badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.app-main {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.app-footer {
  background: var(--surface-color);
  padding: 0.75rem 2rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.8rem;
  border-top: 1px solid var(--border-color);
}
</style>
