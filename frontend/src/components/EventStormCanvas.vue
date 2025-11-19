<template>
  <div class="event-storm-container">
    <!-- Left Sidebar: Input & Controls -->
    <div class="sidebar-panel card glass">
      <div class="panel-header">
        <h2>🚀 비즈니스 설명</h2>
        <div class="header-actions">
          <button @click="showVersionList = !showVersionList" class="btn-icon" title="버전 목록">
            📂
          </button>
          <button @click="showSaveDialog = true" class="btn-icon" :disabled="!businessDescription.trim()" title="저장">
            💾
          </button>
        </div>
      </div>

      <div v-if="currentVersion" class="version-badge-display">
        <span class="badge-primary">{{ currentVersion.name }} v{{ currentVersion.version }}</span>
        <button @click="clearCurrentVersion" class="btn-text-xs">새로 시작</button>
      </div>

      <div class="input-area">
        <textarea
          v-model="businessDescription"
          placeholder="비즈니스 시나리오를 입력하세요...
예: 고객이 주문하면 결제가 처리되고 배송이 시작됩니다."
          rows="12"
          class="premium-input"
        />
      </div>

      <div class="action-buttons">
        <button
          @click="analyze"
          :disabled="isAnalyzing || !businessDescription.trim()"
          class="btn btn-primary btn-block"
        >
          <span v-if="isAnalyzing" class="spinner"></span>
          {{ isAnalyzing ? '분석 중...' : '✨ 이벤트 스토밍 분석' }}
        </button>

        <button
          @click="showOntologyVersionList = true"
          class="btn btn-secondary btn-block"
        >
          🗄️ Neo4j에서 불러오기
        </button>
      </div>

      <div v-if="error" class="error-message animate-fade-in">
        ⚠️ {{ error }}
      </div>
      
      <div class="divider"></div>
      
      <div class="sidebar-footer">
         <div v-if="eventStormResult" class="result-actions">
            <button @click="openSaveChangesDialog" class="btn btn-sm btn-info">
              💾 변경사항 저장
            </button>
            <button @click="buildOntology" class="btn btn-sm btn-success">
              ✅ 온톨로지 생성
            </button>
            <button @click="exportJSON" class="btn btn-sm btn-secondary">
              📥 JSON
            </button>
         </div>
      </div>
    </div>

    <!-- Main Visualization Area -->
    <div class="visualization-wrapper">
      <VueFlow
        class="event-storm-flow"
        v-model:nodes="nodes"
        v-model:edges="edges"
        @node-click="onNodeClick"
        @edge-click="onEdgeClick"
        @connect="onConnect"
        @nodes-change="onNodesChange"
        @edges-change="onEdgesChange"
        :default-viewport="{ zoom: 1 }"
        :min-zoom="0.2"
        :max-zoom="4"
        :connection-mode="ConnectionMode.Loose"
        :snap-to-grid="true"
        :snap-grid="[20, 20]"
        fit-view-on-init
        :nodes-draggable="true"
        :nodes-connectable="true"
        :edges-updatable="true"
        :delete-key-code="'Delete'"
      >
        <Background pattern-color="#e2e8f0" :gap="20" />
        <Controls />
        <MiniMap />

        <template #node-aggregate="{ data, selected }">
          <div class="aggregate-node card" :class="{ selected }">
            <Handle type="target" :position="Position.Left" class="node-handle" />
            <div class="node-header">
              <h3>📦 {{ data.label }}</h3>
            </div>

            <div class="node-body">
              <div class="node-section commands">
                <h4>⚡ Commands</h4>
                <ul>
                  <li v-for="cmd in data.commands" :key="cmd.name">
                    {{ cmd.name }}
                  </li>
                </ul>
              </div>

              <div class="node-section events">
                <h4>📢 Events</h4>
                <ul>
                  <li v-for="evt in data.events" :key="evt.name">
                    {{ evt.name }}
                  </li>
                </ul>
              </div>
            </div>
            <Handle type="source" :position="Position.Right" class="node-handle" />
          </div>
        </template>
      </VueFlow>
      
      <!-- Right Inspector Panel -->
      <div v-if="selectedNode || selectedEdge" class="inspector-panel card glass animate-fade-in">
        <div class="panel-header">
          <h3>{{ selectedNode ? '📦 Aggregate 편집' : '🔗 Policy 편집' }}</h3>
          <button @click="selectedNode ? deleteSelectedNode() : deleteSelectedEdge()" class="btn-icon-danger">🗑️</button>
        </div>
        
        <div v-if="selectedNode" class="inspector-content">
           <div class="form-group">
            <label>이름</label>
            <input v-model="editNodeName" @blur="updateNodeName" class="premium-input" />
          </div>
          
          <div class="list-editor">
            <label>Commands</label>
            <div v-for="(cmd, idx) in selectedNode.data.commands" :key="idx" class="list-item">
              <input
                :value="cmd.name"
                @blur="updateCommandName(idx, $event.target.value)"
                @keyup.enter="$event.target.blur()"
                class="premium-input sm"
              />
              <button @click="removeCommand(idx)" class="btn-icon-sm">×</button>
            </div>
            <div class="add-item">
              <input v-model="newCommandName" placeholder="New Command" @keyup.enter="addCommand" class="premium-input sm" />
              <button @click="addCommand" class="btn-icon-add">+</button>
            </div>
          </div>

          <div class="list-editor">
            <label>Events</label>
            <div v-for="(evt, idx) in selectedNode.data.events" :key="idx" class="list-item">
              <input
                :value="evt.name"
                @blur="updateEventName(idx, $event.target.value)"
                @keyup.enter="$event.target.blur()"
                class="premium-input sm"
              />
              <button @click="removeEvent(idx)" class="btn-icon-sm">×</button>
            </div>
            <div class="add-item">
              <input v-model="newEventName" placeholder="New Event" @keyup.enter="addEvent" class="premium-input sm" />
              <button @click="addEvent" class="btn-icon-add">+</button>
            </div>
          </div>
        </div>

        <div v-if="selectedEdge" class="inspector-content">
           <div class="form-group">
            <label>Policy 이름</label>
            <input v-model="editEdgeLabel" @blur="updateEdgeLabel" class="premium-input" />
          </div>
          <div class="edge-info text-sm text-muted">
            <p>From: {{ selectedEdge.source }}</p>
            <p>To: {{ selectedEdge.target }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals (Version List, Save, etc.) -->
    <!-- Reusing existing logic but styling them -->
    <div v-if="showVersionList" class="modal-overlay glass" @click.self="showVersionList = false">
      <div class="modal-content card animate-fade-in">
        <div class="modal-header">
          <h3>📂 저장된 버전</h3>
          <button @click="showVersionList = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
           <div v-if="versions.length === 0" class="empty-state">
            저장된 버전이 없습니다.
          </div>
          <div v-else class="version-list">
            <div v-for="version in versions" :key="version.id" class="version-item card">
              <div class="version-info">
                <h4>{{ version.name }} <span class="badge-sm">v{{ version.version }}</span></h4>
                <p>{{ version.description }}</p>
                <div class="version-meta text-xs text-muted">
                  <span>{{ formatDate(version.created_at) }}</span>
                </div>
              </div>
              <div class="version-actions">
                <button @click="loadVersion(version.id)" class="btn btn-sm btn-primary">Load</button>
                <button @click="deleteVersion(version.id)" class="btn btn-sm btn-danger">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showSaveDialog" class="modal-overlay glass" @click.self="showSaveDialog = false">
      <div class="modal-content card animate-fade-in">
        <div class="modal-header">
          <h3>💾 버전 저장</h3>
          <button @click="showSaveDialog = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>버전 이름</label>
            <input v-model="saveVersionName" placeholder="예: 온라인 쇼핑몰 v1" class="premium-input" />
          </div>
          <div class="form-group">
            <label>설명</label>
            <textarea v-model="saveVersionDescription" rows="3" class="premium-input" />
          </div>
          <div class="form-group checkbox">
             <label>
              <input type="checkbox" v-model="saveAsNewVersion" :disabled="!currentVersion" />
              새 버전으로 저장
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showSaveDialog = false" class="btn btn-secondary">취소</button>
          <button @click="saveVersion" class="btn btn-success" :disabled="!saveVersionName.trim()">저장</button>
        </div>
      </div>
    </div>
    
    <!-- Similar styling for other modals... -->
    <div v-if="showSaveChangesDialog" class="modal-overlay glass" @click.self="showSaveChangesDialog = false">
      <div class="modal-content card animate-fade-in">
        <div class="modal-header">
          <h3>💾 변경사항 저장</h3>
          <button @click="showSaveChangesDialog = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
           <div class="save-options">
              <label class="radio-card" :class="{ active: saveChangesMode === 'update' }" @click="saveChangesMode = 'update'">
                <input type="radio" v-model="saveChangesMode" value="update" />
                <div class="radio-content">
                  <strong>업데이트</strong>
                  <p>현재 버전을 덮어씁니다.</p>
                </div>
              </label>
              <label class="radio-card" :class="{ active: saveChangesMode === 'new' }" @click="saveChangesMode = 'new'">
                <input type="radio" v-model="saveChangesMode" value="new" />
                <div class="radio-content">
                  <strong>새 버전</strong>
                  <p>새로운 버전을 생성합니다.</p>
                </div>
              </label>
           </div>
           
           <div v-if="saveChangesMode === 'new' || !currentVersion" class="new-version-inputs animate-fade-in">
              <input v-model="saveChangesVersionName" placeholder="버전 이름" class="premium-input" />
              <textarea v-model="saveChangesVersionDescription" placeholder="설명" class="premium-input" />
           </div>
        </div>
        <div class="modal-footer">
          <button @click="showSaveChangesDialog = false" class="btn btn-secondary">취소</button>
          <button @click="saveChanges" class="btn btn-success">저장</button>
        </div>
      </div>
    </div>

    <div v-if="showOntologyVersionList" class="modal-overlay glass" @click.self="showOntologyVersionList = false">
       <div class="modal-content card animate-fade-in">
        <div class="modal-header">
          <h3>🗄️ 온톨로지 불러오기</h3>
          <button @click="showOntologyVersionList = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
           <button @click="loadCurrentOntology" class="btn btn-primary btn-block mb-4">
              📦 현재 Neo4j 온톨로지 전체
            </button>
            <div class="divider"><span>OR</span></div>
            <div class="version-list">
               <div v-for="version in ontologyVersions" :key="version.id" class="version-item card">
                  <h4>{{ version.name }}</h4>
                  <button @click="loadVersionOntology(version.id)" class="btn btn-sm btn-info">Load</button>
               </div>
            </div>
        </div>
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, markRaw, watch } from 'vue'
import { VueFlow, useVueFlow, ConnectionMode, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import axios from 'axios'
import dagre from 'dagre'

const businessDescription = ref('')
const isAnalyzing = ref(false)
const error = ref('')
const eventStormResult = ref(null)
const selectedNode = ref(null)
const selectedEdge = ref(null)

// 편집용 상태
const editNodeName = ref('')
const editEdgeLabel = ref('')
const newCommandName = ref('')
const newEventName = ref('')

// 버전 관리 상태
const versions = ref([])
const currentVersion = ref(null)
const showVersionList = ref(false)
const showSaveDialog = ref(false)
const saveVersionName = ref('')
const saveVersionDescription = ref('')
const saveAsNewVersion = ref(false)
const showOntologyVersionList = ref(false)
const showSaveChangesDialog = ref(false)
const saveChangesMode = ref('update') // 'update' or 'new'
const saveChangesVersionName = ref('')
const saveChangesVersionDescription = ref('')
const ontologyVersions = ref([])

const { fitView, addNodes, removeNodes, addEdges, removeEdges, updateNode } = useVueFlow()
const nodes = ref([])
const edges = ref([])

// 노드 선택 시 편집 필드 업데이트
watch(selectedNode, (node) => {
  if (node) {
    editNodeName.value = node.data.label
    selectedEdge.value = null
  }
})

// 엣지 선택 시 편집 필드 업데이트
watch(selectedEdge, (edge) => {
  if (edge) {
    editEdgeLabel.value = edge.label || ''
    selectedNode.value = null
  }
})

async function analyze() {
  isAnalyzing.value = true
  error.value = ''

  try {
    const { data } = await axios.post('/api/event-storm/analyze', {
      description: businessDescription.value
    })

    console.log('API Response:', data)
    eventStormResult.value = data
    visualizeResult(data)

  } catch (err) {
    console.error('API Error:', err)
    error.value = err.response?.data?.detail || err.message
  } finally {
    isAnalyzing.value = false
  }
}

function visualizeResult(result) {
  console.log('Visualizing result:', result)
  // Dagre 레이아웃
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'LR', ranksep: 150, nodesep: 100 })
  g.setDefaultEdgeLabel(() => ({}))

  const nodeWidth = 250
  const nodeHeight = 200

  // Aggregates → 노드
  const newNodes = []
  result.aggregates.forEach((agg, i) => {
    const nodeId = agg.name
    g.setNode(nodeId, { width: nodeWidth, height: nodeHeight })

    newNodes.push({
      id: nodeId,
      type: 'aggregate',
      position: { x: 0, y: 0 },
      width: nodeWidth,
      height: nodeHeight,
      data: {
        label: agg.name,
        commands: agg.commands || [],
        events: agg.events || [],
        state: agg.state || {},
        invariants: agg.invariants || []
      }
    })
  })

  // Policies → 엣지
  const newEdges = []
  console.log('Processing policies:', result.policies)

  result.policies.forEach((policy, i) => {
    console.log(`Policy ${i}:`, policy)
    console.log('  - trigger_event:', policy.trigger_event)
    console.log('  - actions:', policy.actions)

    // 트리거 이벤트를 발행하는 Aggregate 찾기 (유연한 매칭)
    let sourceAgg = result.aggregates.find(agg =>
      agg.events.some(e => e.name === policy.trigger_event)
    )

    // 정확한 매칭이 안 되면 부분 매칭 시도
    if (!sourceAgg) {
      sourceAgg = result.aggregates.find(agg =>
        agg.events.some(e =>
          e.name.toLowerCase().includes(policy.trigger_event.toLowerCase()) ||
          policy.trigger_event.toLowerCase().includes(e.name.toLowerCase())
        )
      )
    }

    // 타겟 Command를 가진 Aggregate 찾기 (유연한 매칭)
    let targetAgg = null
    if (policy.actions && policy.actions.length > 0) {
      const firstAction = policy.actions[0]
      targetAgg = result.aggregates.find(agg =>
        agg.commands.some(c => c.name === firstAction)
      )

      // 정확한 매칭이 안 되면 부분 매칭 시도
      if (!targetAgg) {
        targetAgg = result.aggregates.find(agg =>
          agg.commands.some(c =>
            c.name.toLowerCase().includes(firstAction.toLowerCase()) ||
            firstAction.toLowerCase().includes(c.name.toLowerCase())
          )
        )
      }
    }

    console.log('  - sourceAgg:', sourceAgg?.name)
    console.log('  - targetAgg:', targetAgg?.name)

    if (sourceAgg && targetAgg && sourceAgg.name !== targetAgg.name) {
      g.setEdge(sourceAgg.name, targetAgg.name)

      newEdges.push({
        id: `policy-${i}`,
        source: sourceAgg.name,
        target: targetAgg.name,
        label: policy.name,
        type: 'smoothstep',
        animated: true
      })
      console.log(`  ✅ Edge created: ${sourceAgg.name} -> ${targetAgg.name}`)
    } else {
      console.warn(`  ❌ Edge NOT created - sourceAgg: ${sourceAgg?.name}, targetAgg: ${targetAgg?.name}`)

      // 폴백: 최소 2개의 aggregate가 있으면 순차적으로 연결
      if (!sourceAgg && !targetAgg && i < result.aggregates.length - 1) {
        const fallbackSource = result.aggregates[i % result.aggregates.length]
        const fallbackTarget = result.aggregates[(i + 1) % result.aggregates.length]

        if (fallbackSource && fallbackTarget && fallbackSource.name !== fallbackTarget.name) {
          g.setEdge(fallbackSource.name, fallbackTarget.name)
          newEdges.push({
            id: `policy-${i}`,
            source: fallbackSource.name,
            target: fallbackTarget.name,
            label: policy.name,
            type: 'smoothstep',
            animated: true
          })
          console.log(`  🔄 Fallback edge created: ${fallbackSource.name} -> ${fallbackTarget.name}`)
        }
      }
    }
  })

  // Dagre 레이아웃 계산
  dagre.layout(g)

  // 위치 적용
  newNodes.forEach(node => {
    const dagreNode = g.node(node.id)
    node.position = {
      x: dagreNode.x - nodeWidth / 2,
      y: dagreNode.y - nodeHeight / 2
    }
  })

  console.log('Generated nodes:', newNodes)
  console.log('Generated edges:', newEdges)

  nodes.value = newNodes
  edges.value = newEdges

  console.log('Vue Flow nodes:', nodes.value)
  console.log('Vue Flow edges:', edges.value)
}

function onNodeClick(nodeClickEvent) {
  // Vue Flow @node-click은 { event, node } 형태로 전달됨
  const node = nodeClickEvent.node || nodeClickEvent
  console.log('Node click event:', nodeClickEvent)
  console.log('Node:', node)

  if (!node || !node.id) {
    console.error('Invalid node object:', node)
    return
  }

  // 깊은 복사를 통해 반응성 문제 해결
  selectedNode.value = {
    id: node.id,
    type: node.type,
    position: { x: node.position?.x || 0, y: node.position?.y || 0 },
    data: {
      label: node.data?.label || node.id,
      commands: [...(node.data?.commands || [])],
      events: [...(node.data?.events || [])],
      state: { ...(node.data?.state || {}) },
      invariants: [...(node.data?.invariants || [])]
    }
  }
}

function onEdgeClick(edgeClickEvent) {
  const edge = edgeClickEvent.edge || edgeClickEvent
  console.log('Edge click event:', edgeClickEvent)

  if (!edge || !edge.id) {
    console.error('Invalid edge object:', edge)
    return
  }

  selectedEdge.value = {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label || '',
    type: edge.type,
    animated: edge.animated
  }
}

function onConnect(params) {
  const newEdge = {
    id: `edge-${Date.now()}`,
    source: params.source,
    target: params.target,
    label: 'NewPolicy',
    type: 'smoothstep',
    animated: true
  }
  edges.value = [...edges.value, newEdge]
}

function onNodesChange(changes) {
  // 노드 변경 사항 처리 (이동, 삭제 등)
  console.log('Nodes changed:', changes)
}

function onEdgesChange(changes) {
  // 엣지 변경 사항 처리
  console.log('Edges changed:', changes)
}

// 노드 편집 함수들
function updateNodeName() {
  if (selectedNode.value && editNodeName.value.trim()) {
    const nodeIndex = nodes.value.findIndex(n => n.id === selectedNode.value.id)
    if (nodeIndex !== -1) {
      const oldId = nodes.value[nodeIndex].id
      const newId = editNodeName.value.trim()

      // 노드 업데이트 (전체 배열 교체로 반응성 트리거)
      const updatedNode = {
        ...nodes.value[nodeIndex],
        id: newId,
        data: {
          ...nodes.value[nodeIndex].data,
          label: newId
        }
      }

      nodes.value = [
        ...nodes.value.slice(0, nodeIndex),
        updatedNode,
        ...nodes.value.slice(nodeIndex + 1)
      ]

      // 관련 엣지 업데이트
      edges.value = edges.value.map(edge => ({
        ...edge,
        source: edge.source === oldId ? newId : edge.source,
        target: edge.target === oldId ? newId : edge.target
      }))

      selectedNode.value = updatedNode
    }
  }
}

function addCommand() {
  console.log('addCommand called, selectedNode:', selectedNode.value?.id, 'newCommandName:', newCommandName.value)
  if (selectedNode.value && newCommandName.value.trim()) {
    const nodeId = selectedNode.value.id
    const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
    console.log('Node index:', nodeIndex)
    if (nodeIndex !== -1) {
      const newCmd = { name: newCommandName.value.trim(), parameters: [], triggered_by: 'user' }
      const currentNode = nodes.value[nodeIndex]
      const newCommands = [...currentNode.data.commands, newCmd]

      // 새 배열로 교체하여 반응성 트리거
      const newNodes = [...nodes.value]
      newNodes[nodeIndex] = {
        ...currentNode,
        data: {
          ...currentNode.data,
          commands: newCommands
        }
      }
      nodes.value = newNodes

      // selectedNode도 업데이트 (깊은 복사)
      selectedNode.value = {
        ...selectedNode.value,
        data: {
          ...selectedNode.value.data,
          commands: newCommands
        }
      }
      newCommandName.value = ''
      console.log('Command added successfully:', newCmd.name)
    }
  }
}

function removeCommand(idx) {
  console.log('removeCommand called, idx:', idx)
  if (selectedNode.value) {
    const nodeId = selectedNode.value.id
    const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
    if (nodeIndex !== -1) {
      const currentNode = nodes.value[nodeIndex]
      const newCommands = currentNode.data.commands.filter((_, i) => i !== idx)

      const newNodes = [...nodes.value]
      newNodes[nodeIndex] = {
        ...currentNode,
        data: {
          ...currentNode.data,
          commands: newCommands
        }
      }
      nodes.value = newNodes
      selectedNode.value = {
        ...selectedNode.value,
        data: {
          ...selectedNode.value.data,
          commands: newCommands
        }
      }
      console.log('Command removed successfully')
    }
  }
}

function addEvent() {
  console.log('addEvent called, selectedNode:', selectedNode.value?.id, 'newEventName:', newEventName.value)
  if (selectedNode.value && newEventName.value.trim()) {
    const nodeId = selectedNode.value.id
    const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
    console.log('Node index:', nodeIndex)
    if (nodeIndex !== -1) {
      const newEvt = { name: newEventName.value.trim(), data: {} }
      const currentNode = nodes.value[nodeIndex]
      const newEvents = [...currentNode.data.events, newEvt]

      const newNodes = [...nodes.value]
      newNodes[nodeIndex] = {
        ...currentNode,
        data: {
          ...currentNode.data,
          events: newEvents
        }
      }
      nodes.value = newNodes
      selectedNode.value = {
        ...selectedNode.value,
        data: {
          ...selectedNode.value.data,
          events: newEvents
        }
      }
      newEventName.value = ''
      console.log('Event added successfully:', newEvt.name)
    }
  }
}

function removeEvent(idx) {
  console.log('removeEvent called, idx:', idx)
  if (selectedNode.value) {
    const nodeId = selectedNode.value.id
    const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
    if (nodeIndex !== -1) {
      const currentNode = nodes.value[nodeIndex]
      const newEvents = currentNode.data.events.filter((_, i) => i !== idx)

      const newNodes = [...nodes.value]
      newNodes[nodeIndex] = {
        ...currentNode,
        data: {
          ...currentNode.data,
          events: newEvents
        }
      }
      nodes.value = newNodes
      selectedNode.value = {
        ...selectedNode.value,
        data: {
          ...selectedNode.value.data,
          events: newEvents
        }
      }
      console.log('Event removed successfully')
    }
  }
}

function updateCommandName(idx, newName) {
  if (!newName.trim() || !selectedNode.value) return

  const nodeId = selectedNode.value.id
  const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
  if (nodeIndex !== -1) {
    const currentNode = nodes.value[nodeIndex]
    const newCommands = currentNode.data.commands.map((cmd, i) =>
      i === idx ? { ...cmd, name: newName.trim() } : cmd
    )

    const newNodes = [...nodes.value]
    newNodes[nodeIndex] = {
      ...currentNode,
      data: {
        ...currentNode.data,
        commands: newCommands
      }
    }
    nodes.value = newNodes
    selectedNode.value = {
      ...selectedNode.value,
      data: {
        ...selectedNode.value.data,
        commands: newCommands
      }
    }
    console.log('Command name updated:', newName)
  }
}

function updateEventName(idx, newName) {
  if (!newName.trim() || !selectedNode.value) return

  const nodeId = selectedNode.value.id
  const nodeIndex = nodes.value.findIndex(n => n.id === nodeId)
  if (nodeIndex !== -1) {
    const currentNode = nodes.value[nodeIndex]
    const newEvents = currentNode.data.events.map((evt, i) =>
      i === idx ? { ...evt, name: newName.trim() } : evt
    )

    const newNodes = [...nodes.value]
    newNodes[nodeIndex] = {
      ...currentNode,
      data: {
        ...currentNode.data,
        events: newEvents
      }
    }
    nodes.value = newNodes
    selectedNode.value = {
      ...selectedNode.value,
      data: {
        ...selectedNode.value.data,
        events: newEvents
      }
    }
    console.log('Event name updated:', newName)
  }
}

function deleteSelectedNode() {
  if (selectedNode.value) {
    const nodeId = selectedNode.value.id
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    selectedNode.value = null
  }
}

// 엣지 편집 함수들
function updateEdgeLabel() {
  if (selectedEdge.value && editEdgeLabel.value.trim()) {
    const edgeIndex = edges.value.findIndex(e => e.id === selectedEdge.value.id)
    if (edgeIndex !== -1) {
      edges.value[edgeIndex] = {
        ...edges.value[edgeIndex],
        label: editEdgeLabel.value.trim()
      }
      selectedEdge.value = edges.value[edgeIndex]
    }
  }
}

function deleteSelectedEdge() {
  if (selectedEdge.value) {
    edges.value = edges.value.filter(e => e.id !== selectedEdge.value.id)
    selectedEdge.value = null
  }
}

// 새 Aggregate 추가
function addNewAggregate() {
  const newId = `NewAggregate${Date.now()}`
  const newNode = {
    id: newId,
    type: 'aggregate',
    position: { x: Math.random() * 400, y: Math.random() * 300 },
    width: 250,
    height: 200,
    data: {
      label: newId,
      commands: [],
      events: [],
      state: {},
      invariants: []
    }
  }
  nodes.value = [...nodes.value, newNode]
}

async function buildOntology() {
  try {
    // 현재 Vue Flow 상태를 eventStormResult에 동기화
    const updatedResult = {
      ...eventStormResult.value,
      aggregates: nodes.value.map(node => ({
        name: node.data.label,
        commands: node.data.commands,
        events: node.data.events,
        state: node.data.state,
        invariants: node.data.invariants
      })),
      policies: edges.value.map(edge => ({
        name: edge.label || 'Policy',
        trigger_event: '', // 실제로는 source aggregate의 event를 매핑해야 함
        actions: [], // 실제로는 target aggregate의 command를 매핑해야 함
        description: `${edge.source} -> ${edge.target}`
      }))
    }

    await axios.post('/api/ontology/build', updatedResult)

    // 현재 버전이 있으면 온톨로지와 연결
    if (currentVersion.value) {
      await axios.post(`/api/versions/${currentVersion.value.id}/link-ontology`)
    }

    alert('✅ 온톨로지가 Neo4j에 생성되었습니다!')
  } catch (err) {
    alert('❌ 온톨로지 생성 실패: ' + err.message)
  }
}

function exportJSON() {
  // 현재 Vue Flow 상태를 포함하여 내보내기
  const exportData = {
    ...eventStormResult.value,
    aggregates: nodes.value.map(node => ({
      name: node.data.label,
      commands: node.data.commands,
      events: node.data.events,
      state: node.data.state,
      invariants: node.data.invariants
    })),
    policies: edges.value.map(edge => ({
      name: edge.label || 'Policy',
      trigger_event: '',
      actions: [],
      description: `${edge.source} -> ${edge.target}`
    }))
  }

  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'event-storm-result.json'
  a.click()
}

async function loadCurrentOntology() {
  try {
    const { data } = await axios.get('/api/ontology/load')

    if (!data.aggregates || data.aggregates.length === 0) {
      alert('⚠️ Neo4j에 저장된 온톨로지가 없습니다.')
      return
    }

    // LLM 결과로 설정
    eventStormResult.value = data

    // Vue Flow에 시각화
    visualizeResult(data)

    showOntologyVersionList.value = false
    alert(`✅ Neo4j에서 ${data.aggregates.length}개의 Aggregate를 불러왔습니다.`)
  } catch (err) {
    console.error('Neo4j 로드 실패:', err)
    alert('❌ Neo4j에서 불러오기 실패: ' + (err.response?.data?.detail || err.message))
  }
}

async function loadVersionOntology(versionId) {
  try {
    // 버전 정보 로드
    const { data } = await axios.get(`/api/versions/${versionId}`)

    if (data.llm_result) {
      eventStormResult.value = data.llm_result

      if (data.flow_state) {
        // flow_state가 있으면 그대로 사용
        nodes.value = data.flow_state.nodes
        edges.value = data.flow_state.edges
      } else {
        // 없으면 시각화 생성
        visualizeResult(data.llm_result)
      }

      showOntologyVersionList.value = false
      alert(`✅ "${data.name}" 버전의 온톨로지를 불러왔습니다.`)
    } else {
      alert('⚠️ 이 버전에는 저장된 LLM 결과가 없습니다.')
    }
  } catch (err) {
    console.error('버전 온톨로지 로드 실패:', err)
    alert('❌ 온톨로지 불러오기 실패: ' + (err.response?.data?.detail || err.message))
  }
}

// 버전 관리 함수들
async function fetchVersions() {
  try {
    const { data } = await axios.get('/api/versions/list')
    versions.value = data
    // 온톨로지가 있는 버전만 필터링
    ontologyVersions.value = data.filter(v => v.has_ontology || v.has_llm_result)
  } catch (err) {
    console.error('버전 목록 조회 실패:', err)
  }
}

async function saveVersion() {
  try {
    const flowState = {
      nodes: nodes.value.map(n => ({
        id: n.id,
        type: n.type,
        position: n.position,
        width: n.width,
        height: n.height,
        data: n.data
      })),
      edges: edges.value.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: e.type,
        animated: e.animated
      }))
    }

    const request = {
      name: saveVersionName.value,
      description: saveVersionDescription.value,
      business_description: businessDescription.value,
      llm_result: eventStormResult.value,
      flow_state: flowState,
      parent_version_id: saveAsNewVersion.value && currentVersion.value ? currentVersion.value.id : null
    }

    const { data } = await axios.post('/api/versions/save', request)
    currentVersion.value = data

    // 저장 다이얼로그 닫기 및 초기화
    showSaveDialog.value = false
    saveVersionName.value = ''
    saveVersionDescription.value = ''
    saveAsNewVersion.value = false

    // 버전 목록 갱신
    await fetchVersions()

    alert('✅ 버전이 저장되었습니다!')
  } catch (err) {
    console.error('버전 저장 실패:', err)
    alert('❌ 버전 저장 실패: ' + (err.response?.data?.detail || err.message))
  }
}

function openSaveChangesDialog() {
  // 모달 열 때 초기화
  if (currentVersion.value) {
    saveChangesMode.value = 'update'
  } else {
    saveChangesMode.value = 'new'
  }
  saveChangesVersionName.value = ''
  saveChangesVersionDescription.value = ''
  showSaveChangesDialog.value = true
}

async function saveChanges() {
  try {
    // 현재 노드와 엣지 상태를 업데이트된 eventStormResult로 변환
    const updatedResult = {
      ...eventStormResult.value,
      aggregates: nodes.value.map(node => ({
        name: node.data.label,
        commands: node.data.commands,
        events: node.data.events,
        state: node.data.state,
        invariants: node.data.invariants
      })),
      policies: edges.value.map(edge => ({
        name: edge.label || 'Policy',
        trigger_event: '',
        actions: [],
        description: `${edge.source} -> ${edge.target}`
      }))
    }

    const flowState = {
      nodes: nodes.value.map(n => ({
        id: n.id,
        type: n.type,
        position: n.position,
        width: n.width,
        height: n.height,
        data: n.data
      })),
      edges: edges.value.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        type: e.type,
        animated: e.animated
      }))
    }

    if (currentVersion.value && saveChangesMode.value === 'update') {
      // 기존 버전 업데이트
      const request = {
        llm_result: updatedResult,
        flow_state: flowState
      }

      const { data } = await axios.put(`/api/versions/${currentVersion.value.id}`, request)
      currentVersion.value = data
      eventStormResult.value = updatedResult

      alert('✅ 버전이 업데이트되었습니다!')
    } else {
      // 새 버전으로 저장
      if (!saveChangesVersionName.value.trim()) {
        alert('❌ 버전 이름을 입력해주세요.')
        return
      }

      const request = {
        name: saveChangesVersionName.value,
        description: saveChangesVersionDescription.value || '',
        business_description: businessDescription.value,
        llm_result: updatedResult,
        flow_state: flowState,
        parent_version_id: currentVersion.value ? currentVersion.value.id : null
      }

      const { data } = await axios.post('/api/versions/save', request)
      currentVersion.value = data
      eventStormResult.value = updatedResult

      alert('✅ 새 버전이 저장되었습니다!')
    }

    // 저장 다이얼로그 닫기 및 초기화
    showSaveChangesDialog.value = false
    saveChangesMode.value = 'update'
    saveChangesVersionName.value = ''
    saveChangesVersionDescription.value = ''

    // 버전 목록 갱신
    await fetchVersions()
  } catch (err) {
    console.error('변경사항 저장 실패:', err)
    alert('❌ 변경사항 저장 실패: ' + (err.response?.data?.detail || err.message))
  }
}

async function loadVersion(versionId) {
  try {
    const { data } = await axios.get(`/api/versions/${versionId}`)

    currentVersion.value = data
    businessDescription.value = data.business_description

    if (data.llm_result) {
      eventStormResult.value = data.llm_result
    }

    if (data.flow_state) {
      nodes.value = data.flow_state.nodes
      edges.value = data.flow_state.edges
    } else if (data.llm_result) {
      // flow_state가 없으면 llm_result로 시각화
      visualizeResult(data.llm_result)
    }

    showVersionList.value = false
    alert(`✅ "${data.name}" 버전을 불러왔습니다.`)
  } catch (err) {
    console.error('버전 불러오기 실패:', err)
    alert('❌ 버전 불러오기 실패: ' + (err.response?.data?.detail || err.message))
  }
}

async function deleteVersion(versionId) {
  if (!confirm('정말로 이 버전을 삭제하시겠습니까?')) {
    return
  }

  try {
    await axios.delete(`/api/versions/${versionId}`)

    // 현재 버전이 삭제된 경우 초기화
    if (currentVersion.value && currentVersion.value.id === versionId) {
      currentVersion.value = null
    }

    await fetchVersions()
    alert('✅ 버전이 삭제되었습니다.')
  } catch (err) {
    console.error('버전 삭제 실패:', err)
    alert('❌ 버전 삭제 실패: ' + (err.response?.data?.detail || err.message))
  }
}

function clearCurrentVersion() {
  currentVersion.value = null
  businessDescription.value = ''
  eventStormResult.value = null
  nodes.value = []
  edges.value = []
  selectedNode.value = null
  selectedEdge.value = null
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 컴포넌트 마운트 시 버전 목록 로드
import { onMounted } from 'vue'
onMounted(() => {
  fetchVersions()
})
</script>

<style scoped>
.event-storm-container {
  display: flex;
  flex-direction: row;
  height: 100%;
  padding: 1.5rem;
  gap: 1.5rem;
  overflow: hidden;
  background: var(--bg-color);
}

/* Sidebar Panel */
.sidebar-panel {
  width: 380px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  gap: 1rem;
  z-index: 5;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.panel-header h2 {
  font-size: 1.25rem;
  margin: 0;
  background: var(--header-gradient);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.version-badge-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-hover);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
}

.badge-primary {
  background: var(--primary-color);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.input-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.premium-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--surface-color);
  transition: all 0.2s;
  font-family: inherit;
  resize: none;
}

.premium-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  outline: none;
}

.premium-input.sm {
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
}

textarea.premium-input {
  flex: 1;
  resize: none;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn-block {
  width: 100%;
  justify-content: center;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 0.75rem;
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
}

.divider {
  height: 1px;
  background: var(--border-color);
  margin: 0.5rem 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider span {
  background: var(--surface-color);
  padding: 0 0.5rem;
  color: var(--text-light);
  font-size: 0.75rem;
}

.sidebar-footer {
  margin-top: auto;
}

.result-actions {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.5rem;
}

/* Visualization Area */
.visualization-wrapper {
  flex: 1;
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  background: white;
  border: 1px solid var(--border-color);
}

.event-storm-flow {
  width: 100%;
  height: 100%;
}

/* Aggregate Node */
.aggregate-node {
  min-width: 280px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: all 0.2s;
}

.aggregate-node.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px var(--primary-color), var(--shadow-lg);
}

.node-header {
  background: var(--header-gradient);
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.node-header h3 {
  color: white;
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.node-body {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-section h4 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.25rem;
}

.node-section ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.node-section li {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  background: var(--surface-hover);
  border-radius: var(--radius-sm);
  margin-bottom: 0.25rem;
  color: var(--text-primary);
}

.commands li {
  border-left: 3px solid var(--secondary-color);
}

.events li {
  border-left: 3px solid var(--accent-color);
}

.node-handle {
  width: 10px !important;
  height: 10px !important;
  background: var(--text-secondary) !important;
  border: 2px solid white !important;
}

/* Inspector Panel */
.inspector-panel {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 300px;
  padding: 1.5rem;
  z-index: 10;
  max-height: calc(100% - 2rem);
  overflow-y: auto;
}

.btn-icon, .btn-icon-sm, .btn-icon-add, .btn-icon-danger {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}

.btn-icon { font-size: 1.25rem; padding: 0.25rem; }
.btn-icon:hover { background: var(--surface-hover); }

.btn-icon-sm { 
  color: var(--text-light); 
  padding: 0.25rem;
}
.btn-icon-sm:hover { color: #ef4444; background: #fee2e2; }

.btn-icon-add {
  background: var(--primary-color);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}
.btn-icon-add:hover { background: var(--primary-hover); }

.btn-icon-danger {
  color: #ef4444;
  padding: 0.5rem;
}
.btn-icon-danger:hover { background: #fee2e2; }

.list-editor {
  margin-top: 1rem;
}

.list-editor label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.list-item {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  align-items: center;
}

.add-item {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  align-items: center;
}

.btn-text-xs {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 0.75rem;
  cursor: pointer;
  text-decoration: underline;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
}

.modal-content {
  width: 100%;
  max-width: 500px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-light);
  cursor: pointer;
  line-height: 1;
}
.btn-close:hover { color: var(--text-primary); }

.version-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.version-item {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.version-info p {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.badge-sm {
  background: var(--surface-hover);
  border: 1px solid var(--border-color);
  padding: 0.1rem 0.4rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.radio-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.radio-card:hover {
  border-color: var(--primary-color);
  background: var(--surface-hover);
}

.radio-card.active {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

.radio-content strong {
  display: block;
  color: var(--text-primary);
}

.radio-content p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.new-version-inputs {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.875rem;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
  cursor: pointer;
}

.form-group.checkbox input {
  width: auto;
}
</style>
