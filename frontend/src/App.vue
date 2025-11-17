<template>
  <div id="app">
    <header class="app-header">
      <h1>🚀 Business OS</h1>
      <p>LLM 기반 이벤트 드리븐 온톨로지 시스템</p>
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
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f0f2f5;
}

#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
}

.app-header p {
  opacity: 0.9;
  font-size: 0.95rem;
}

.app-main {
  flex: 1;
  overflow: hidden;
}

.app-footer {
  background: white;
  padding: 1rem 2rem;
  text-align: center;
  color: #666;
  font-size: 0.85rem;
  border-top: 1px solid #ddd;
}
</style>
