<template>
  <div class="event-storm-container">
    <div class="input-panel">
      <div class="panel-top-bar">
        <h2>🚀 비즈니스 설명</h2>
        <div class="version-controls">
          <button @click="showVersionList = !showVersionList" class="btn-info btn-sm">
            📂 버전 목록 ({{ versions.length }})
          </button>
          <button @click="showSaveDialog = true" class="btn-success btn-sm" :disabled="!businessDescription.trim()">
            💾 저장
          </button>
        </div>
      </div>

      <div v-if="currentVersion" class="current-version-info">
        <span>현재 버전: <strong>{{ currentVersion.name }}</strong> (v{{ currentVersion.version }})</span>
        <button @click="clearCurrentVersion" class="btn-link">새로 시작</button>
      </div>

      <textarea
        v-model="businessDescription"
        placeholder="예: 고객이 주문하면 결제가 처리되고 배송이 시작됩니다..."
        rows="8"
      />
      <div class="action-buttons">
        <button
          @click="analyze"
          :disabled="isAnalyzing || !businessDescription.trim()"
          class="btn-primary"
        >
          {{ isAnalyzing ? '분석 중...' : '이벤트 스토밍 분석' }}
        </button>

        <button
          @click="showOntologyVersionList = true"
          class="btn-info"
        >
          🗄️ Neo4j에서 불러오기
        </button>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>

    <!-- 버전 목록 모달 -->
    <div v-if="showVersionList" class="modal-overlay" @click.self="showVersionList = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>📂 저장된 버전 목록</h3>
          <button @click="showVersionList = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="versions.length === 0" class="empty-state">
            저장된 버전이 없습니다.
          </div>
          <div v-else class="version-list">
            <div v-for="version in versions" :key="version.id" class="version-item">
              <div class="version-info">
                <h4>{{ version.name }} <span class="version-badge">v{{ version.version }}</span></h4>
                <p>{{ version.description }}</p>
                <div class="version-meta">
                  <span>📅 {{ formatDate(version.created_at) }}</span>
                  <span v-if="version.has_llm_result">✅ LLM 결과</span>
                  <span v-if="version.has_flow_state">🔄 Flow 상태</span>
                  <span v-if="version.has_ontology">🗄️ 온톨로지</span>
                </div>
              </div>
              <div class="version-actions">
                <button @click="loadVersion(version.id)" class="btn-primary btn-sm">불러오기</button>
                <button @click="deleteVersion(version.id)" class="btn-danger btn-sm">삭제</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 저장 다이얼로그 -->
    <div v-if="showSaveDialog" class="modal-overlay" @click.self="showSaveDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>💾 버전 저장</h3>
          <button @click="showSaveDialog = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>버전 이름 *</label>
            <input v-model="saveVersionName" placeholder="예: 온라인 쇼핑몰 v1" />
          </div>
          <div class="form-group">
            <label>설명</label>
            <textarea v-model="saveVersionDescription" rows="3" placeholder="이 버전에 대한 설명..." />
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="saveAsNewVersion" :disabled="!currentVersion" />
              새 버전으로 저장 (기존 버전에서 파생)
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showSaveDialog = false" class="btn-secondary">취소</button>
          <button @click="saveVersion" class="btn-success" :disabled="!saveVersionName.trim()">저장</button>
        </div>
      </div>
    </div>

    <!-- 변경사항 저장 모달 -->
    <div v-if="showSaveChangesDialog" class="modal-overlay" @click.self="showSaveChangesDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>💾 변경사항 저장</h3>
          <button @click="showSaveChangesDialog = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="currentVersion" class="form-group">
            <p><strong>현재 버전:</strong> {{ currentVersion.name }} (v{{ currentVersion.version }})</p>
            <div class="save-options">
              <label class="radio-option" @click="saveChangesMode = 'update'">
                <input type="radio" v-model="saveChangesMode" value="update" />
                <div>
                  <strong>기존 버전 업데이트</strong>
                  <p class="option-description">현재 버전을 수정된 내용으로 업데이트합니다.</p>
                </div>
              </label>
              <label class="radio-option" @click="saveChangesMode = 'new'">
                <input type="radio" v-model="saveChangesMode" value="new" />
                <div>
                  <strong>새 버전으로 저장</strong>
                  <p class="option-description">현재 버전에서 파생된 새 버전을 생성합니다.</p>
                </div>
              </label>
            </div>
          </div>
          <div v-else class="form-group">
            <p>새 버전으로 저장됩니다.</p>
          </div>
          <div v-if="saveChangesMode === 'new' || !currentVersion" class="form-group">
            <label>버전 이름 *</label>
            <input v-model="saveChangesVersionName" placeholder="예: 온라인 쇼핑몰 v1" />
          </div>
          <div v-if="saveChangesMode === 'new' || !currentVersion" class="form-group">
            <label>설명</label>
            <textarea v-model="saveChangesVersionDescription" rows="3" placeholder="이 버전에 대한 설명..." />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showSaveChangesDialog = false" class="btn-secondary">취소</button>
          <button @click="saveChanges" class="btn-success" :disabled="(saveChangesMode === 'new' || !currentVersion) && !saveChangesVersionName.trim()">
            저장
          </button>
        </div>
      </div>
    </div>

    <!-- Neo4j 온톨로지 선택 모달 -->
    <div v-if="showOntologyVersionList" class="modal-overlay" @click.self="showOntologyVersionList = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>🗄️ Neo4j에서 온톨로지 불러오기</h3>
          <button @click="showOntologyVersionList = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="load-options">
            <button @click="loadCurrentOntology" class="btn-primary load-option-btn">
              📦 현재 Neo4j 온톨로지 전체 불러오기
            </button>
            <p class="option-description">Neo4j에 저장된 모든 ObjectType을 불러옵니다.</p>
          </div>

          <hr class="divider" />

          <h4>또는 저장된 버전에서 불러오기:</h4>
          <div v-if="ontologyVersions.length === 0" class="empty-state">
            온톨로지가 연결된 버전이 없습니다.
          </div>
          <div v-else class="version-list">
            <div v-for="version in ontologyVersions" :key="version.id" class="version-item">
              <div class="version-info">
                <h4>{{ version.name }} <span class="version-badge">v{{ version.version }}</span></h4>
                <p>{{ version.description }}</p>
                <div class="version-meta">
                  <span>📅 {{ formatDate(version.created_at) }}</span>
                  <span v-if="version.has_ontology">🗄️ 온톨로지 있음</span>
                </div>
              </div>
              <div class="version-actions">
                <button @click="loadVersionOntology(version.id)" class="btn-info btn-sm">
                  온톨로지 불러오기
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="eventStormResult" class="visualization-wrapper">
      <div class="toolbar">
        <button @click="openSaveChangesDialog" class="btn-primary">
          💾 변경사항 저장
        </button>
        <button @click="buildOntology" class="btn-success">
          ✅ 온톨로지 생성 (Neo4j에 저장)
        </button>
        <button @click="exportJSON" class="btn-secondary">
          📥 JSON 내보내기
        </button>
      </div>

      <div class="visualization-panel">
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
        :snap-grid="[15, 15]"
        fit-view-on-init
        :nodes-draggable="true"
        :nodes-connectable="true"
        :edges-updatable="true"
        :delete-key-code="'Delete'"
      >
        <Background />
        <Controls />
        <MiniMap />

        <template #node-aggregate="{ data, selected }">
          <div class="aggregate-node" :class="{ selected }">
            <Handle type="target" :position="Position.Left" class="node-handle" />
            <h3>📦 {{ data.label }}</h3>

            <div class="section">
              <h4>Commands</h4>
              <ul>
                <li v-for="cmd in data.commands" :key="cmd.name">
                  ⚡ {{ cmd.name }}
                </li>
              </ul>
            </div>

            <div class="section">
              <h4>Events</h4>
              <ul>
                <li v-for="evt in data.events" :key="evt.name">
                  📢 {{ evt.name }}
                </li>
              </ul>
            </div>
            <Handle type="source" :position="Position.Right" class="node-handle" />
          </div>
        </template>
      </VueFlow>

      <div class="side-panel">
        <div v-if="selectedNode" class="inspector-panel">
          <div class="panel-header">
            <h3>📦 {{ selectedNode.data.label }}</h3>
            <button @click="deleteSelectedNode" class="btn-danger btn-sm">삭제</button>
          </div>

          <div class="edit-section">
            <label>Aggregate 이름</label>
            <input v-model="editNodeName" @blur="updateNodeName" />
          </div>

          <div class="edit-section">
            <label>Commands</label>
            <div v-for="(cmd, idx) in selectedNode.data.commands" :key="idx" class="list-item-editable">
              <span class="item-icon">⚡</span>
              <input
                :value="cmd.name"
                @blur="updateCommandName(idx, $event.target.value)"
                @keyup.enter="$event.target.blur()"
                class="item-name-input"
              />
              <button @click="removeCommand(idx)" class="btn-remove">×</button>
            </div>
            <div class="add-item">
              <input v-model="newCommandName" placeholder="새 Command 이름" @keyup.enter="addCommand" />
              <button @click="addCommand" class="btn-add">+</button>
            </div>
          </div>

          <div class="edit-section">
            <label>Events</label>
            <div v-for="(evt, idx) in selectedNode.data.events" :key="idx" class="list-item-editable">
              <span class="item-icon">📢</span>
              <input
                :value="evt.name"
                @blur="updateEventName(idx, $event.target.value)"
                @keyup.enter="$event.target.blur()"
                class="item-name-input"
              />
              <button @click="removeEvent(idx)" class="btn-remove">×</button>
            </div>
            <div class="add-item">
              <input v-model="newEventName" placeholder="새 Event 이름" @keyup.enter="addEvent" />
              <button @click="addEvent" class="btn-add">+</button>
            </div>
          </div>
        </div>

        <div v-if="selectedEdge" class="inspector-panel">
          <div class="panel-header">
            <h3>🔗 {{ selectedEdge.label || 'Policy' }}</h3>
            <button @click="deleteSelectedEdge" class="btn-danger btn-sm">삭제</button>
          </div>

          <div class="edit-section">
            <label>Policy 이름</label>
            <input v-model="editEdgeLabel" @blur="updateEdgeLabel" />
          </div>

          <div class="edge-info">
            <p><strong>Source:</strong> {{ selectedEdge.source }}</p>
            <p><strong>Target:</strong> {{ selectedEdge.target }}</p>
          </div>
        </div>

        <div v-if="!selectedNode && !selectedEdge" class="help-panel">
          <h3>도움말</h3>
          <ul>
            <li>노드 클릭: 선택 및 편집</li>
            <li>노드 드래그: 위치 이동</li>
            <li>엣지 클릭: 관계 편집</li>
            <li>노드 연결: 핸들을 드래그하여 연결</li>
            <li>Delete 키: 선택 항목 삭제</li>
          </ul>
          <button @click="addNewAggregate" class="btn-primary">+ 새 Aggregate 추가</button>
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
  flex-direction: column;
  height: 100%;
  padding: 1rem;
  gap: 1rem;
  overflow: hidden;
}

.input-panel {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.input-panel h2 {
  margin-top: 0;
}

.input-panel textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  resize: vertical;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  flex: 1;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #ffebee;
  color: #c62828;
  border-radius: 4px;
}

.visualization-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 0;
  overflow: hidden;
}

.visualization-panel {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 1rem;
  min-height: 0;
  overflow: hidden;
  position: relative;
}

.toolbar {
  display: flex;
  gap: 0.5rem;
}

.btn-success, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-success {
  background: #4CAF50;
  color: white;
}

.btn-secondary {
  background: #2196F3;
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

.event-storm-flow {
  flex: 1;
  min-height: 500px;
  background: #f5f5f5;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

/* Vue Flow Controls와 MiniMap이 보이도록 */
.event-storm-flow :deep(.vue-flow__controls) {
  z-index: 10 !important;
  position: absolute !important;
  top: 10px !important;
  left: 10px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 4px !important;
  background: white !important;
  border: 1px solid #ddd !important;
  border-radius: 4px !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
  padding: 4px !important;
}

.event-storm-flow :deep(.vue-flow__controls-button) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  border: 1px solid #ddd !important;
  background: white !important;
  cursor: pointer !important;
  border-radius: 4px !important;
  color: #333 !important;
  font-size: 16px !important;
}

.event-storm-flow :deep(.vue-flow__controls-button:hover) {
  background: #f5f5f5 !important;
  border-color: #2196F3 !important;
}

.event-storm-flow :deep(.vue-flow__controls-button svg) {
  width: 16px !important;
  height: 16px !important;
  display: block !important;
}

.event-storm-flow :deep(.vue-flow__minimap) {
  z-index: 10 !important;
  position: absolute !important;
  top: 10px !important;
  right: 370px !important; /* 사이드바 너비(350px) + gap(20px) */
}

.side-panel {
  width: 350px;
  flex-shrink: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.aggregate-node {
  padding: 1rem;
  background: white;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  min-width: 200px;
  position: relative;
}

.aggregate-node.selected {
  border-color: #2196F3;
  box-shadow: 0 0 10px rgba(33, 150, 243, 0.5);
}

.aggregate-node h3 {
  margin: 0 0 0.5rem 0;
  color: #4CAF50;
}

.aggregate-node .section {
  margin-bottom: 0.5rem;
}

.aggregate-node h4 {
  margin: 0.5rem 0 0.25rem 0;
  font-size: 0.9rem;
  color: #666;
}

.aggregate-node ul {
  margin: 0;
  padding-left: 1.5rem;
  font-size: 0.85rem;
}

.node-handle {
  width: 12px !important;
  height: 12px !important;
  background: #2196F3 !important;
  border: 2px solid white !important;
  border-radius: 50% !important;
}

.inspector-panel {
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
}

.edit-section {
  margin-bottom: 1rem;
}

.edit-section label {
  display: block;
  font-weight: bold;
  margin-bottom: 0.25rem;
  color: #666;
}

.edit-section input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.list-item-editable {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 0.25rem;
  gap: 0.5rem;
}

.item-icon {
  flex-shrink: 0;
}

.item-name-input {
  flex: 1;
  padding: 0.25rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
}

.item-name-input:focus {
  border-color: #2196F3;
  outline: none;
}

.btn-remove {
  background: #f44336;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  cursor: pointer;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.add-item {
  display: flex;
  gap: 0.5rem;
}

.add-item input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-add {
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.edge-info {
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 4px;
}

.edge-info p {
  margin: 0.25rem 0;
}

.help-panel {
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.help-panel h3 {
  margin-top: 0;
}

.help-panel ul {
  padding-left: 1.5rem;
}

.help-panel li {
  margin-bottom: 0.5rem;
}

/* 버전 관리 스타일 */
.panel-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-top-bar h2 {
  margin: 0;
}

.version-controls {
  display: flex;
  gap: 0.5rem;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-link {
  background: none;
  border: none;
  color: #2196F3;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
}

.current-version-info {
  background: #e3f2fd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #ddd;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.version-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.version-info h4 {
  margin: 0 0 0.5rem 0;
}

.version-badge {
  background: #4CAF50;
  color: white;
  padding: 0.1rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.version-info p {
  margin: 0 0 0.5rem 0;
  color: #666;
}

.version-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: #888;
}

.version-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: bold;
  color: #666;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

/* 온톨로지 선택 모달 스타일 */
.load-options {
  text-align: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.load-option-btn {
  width: 100%;
  padding: 1rem;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.option-description {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.divider {
  border: none;
  border-top: 1px solid #ddd;
  margin: 1.5rem 0;
}

.modal-body h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.save-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-option:hover {
  border-color: #2196F3;
  background: #f5f5f5;
}

.radio-option input[type="radio"] {
  margin-top: 0.25rem;
  cursor: pointer;
}

.radio-option input[type="radio"]:checked + div {
  color: #2196F3;
}

.radio-option input[type="radio"]:checked ~ div,
.radio-option:has(input[type="radio"]:checked) {
  border-color: #2196F3;
  background: #e3f2fd;
}

.radio-option > div {
  flex: 1;
}

.radio-option strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 1rem;
}

.option-description {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}
</style>
