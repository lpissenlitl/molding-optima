<!--
  ModelPicker - 3D 模型选点组件（缺陷反馈辅助）

  职责：上传 STL 模型 → Three.js 渲染 → 单击模型表面 → 选点（输出 {x, y, z}）
  数据流：v-model 向父组件传递选点坐标（不取代父级 position 字段，仅作补充）

  设计：
  - 单点模式（每次点击替换上一个点）
  - 不做：体积/壁厚/投影面积等提取，参考 tkm-iprocess 的 STLPluginDrawer.vue 简化而来
-->
<template>
  <div class="model-picker">
    <!-- 未上传：拖拽上传 -->
    <el-upload
      v-if="!geometry"
      :auto-upload="false"
      :show-file-list="false"
      accept=".stl"
      :on-change="onFileChange"
      drag
      class="model-picker__upload"
    >
      <AppIcon icon="mdi:cube-outline" class="model-picker__upload-icon" />
      <div class="model-picker__upload-text">
        将 STL 模型拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="model-picker__upload-tip">
          支持 .stl 格式，文件大小不超过 50MB
        </div>
      </template>
    </el-upload>

    <!-- 已上传：3D 画布 + 工具栏 -->
    <template v-else>
      <div ref="canvasContainer" class="model-picker__canvas" />

      <div class="model-picker__tools">
        <el-button-group size="small">
          <el-button @click="resetCamera" :icon="Refresh">重置视角</el-button>
          <el-button @click="toggleAxes" :icon="Aim">
            {{ showAxes ? '隐藏坐标' : '显示坐标' }}
          </el-button>
          <el-button @click="reupload" :icon="Upload">重新上传</el-button>
          <el-button
            v-if="value"
            @click="clearPick"
            :icon="Delete"
            type="danger"
            plain
          >
            清除选点
          </el-button>
        </el-button-group>
      </div>

      <div v-if="value" class="model-picker__coord">
        <span>X: {{ value.x.toFixed(3) }}</span>
        <span>Y: {{ value.y.toFixed(3) }}</span>
        <span>Z: {{ value.z.toFixed(3) }}</span>
      </div>
      <div v-else class="model-picker__hint">
        点击模型表面标记缺陷位置（再次点击替换）
      </div>
    </template>

    <!-- 错误提示 -->
    <el-alert
      v-if="errorMessage"
      type="error"
      :closable="false"
      :title="errorMessage"
      show-icon
      class="model-picker__error"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Aim,
  Delete,
  Upload,
} from '@element-plus/icons-vue'

/** 3D 点坐标 */
export interface Point3D {
  x: number
  y: number
  z: number
}

const props = defineProps<{
  /** v-model 绑定的选点坐标（null = 未选）*/
  value?: Point3D | null
}>()

const emit = defineEmits<{
  (e: 'update:value', val: Point3D | null): void
}>()

// ============ 状态 ============
const geometry = ref<THREE.BufferGeometry | null>(null)
const errorMessage = ref('')
const showAxes = ref(true)

const canvasContainer = ref<HTMLDivElement | null>(null)

// Three.js 实例（不暴露到 ref，组件内部使用）
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let controls: OrbitControls | null = null
let stlMesh: THREE.Mesh | null = null
let pickMarker: THREE.Mesh | null = null
let axesHelper: THREE.AxesHelper | null = null
let gridHelper: THREE.GridHelper | null = null
let animationFrameId: number | null = null
let resizeObserver: ResizeObserver | null = null

// ============ 文件上传 ============
async function onFileChange(file: { raw?: File }) {
  const f = file?.raw
  if (!f) return
  if (!f.name.toLowerCase().endsWith('.stl')) {
    errorMessage.value = '仅支持 .stl 格式文件'
    return
  }
  if (f.size > 50 * 1024 * 1024) {
    errorMessage.value = '文件大小不能超过 50MB'
    return
  }

  errorMessage.value = ''
  try {
    const buffer = await f.arrayBuffer()
    const loader = new STLLoader()
    const geom = loader.parse(buffer)
    if (geometry.value) geometry.value.dispose()
    geometry.value = geom
    // 等待 DOM 更新（canvas 容器已挂载）
    await Promise.resolve()
    initThree(geom)
  } catch (e: any) {
    errorMessage.value = e?.message || 'STL 解析失败'
  }
}

function reupload() {
  clearPick()
  cleanupThree()
  if (geometry.value) {
    geometry.value.dispose()
    geometry.value = null
  }
  errorMessage.value = ''
}

// ============ Three.js 初始化 ============
function initThree(geom: THREE.BufferGeometry) {
  if (!canvasContainer.value) return
  cleanupThree()

  const container = canvasContainer.value
  const w = container.clientWidth || 600
  const h = container.clientHeight || 400

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xfafbfc)

  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 5000)
  camera.position.set(30, 20, 30)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setSize(w, h)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08

  // 光照
  scene.add(new THREE.AmbientLight(0xffffff, 0.6))
  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2)
  dirLight.position.set(5, 10, 5)
  scene.add(dirLight)
  const backLight = new THREE.DirectionalLight(0x9affff, 0.4)
  backLight.position.set(-5, 5, -5)
  scene.add(backLight)

  // 网格模型（双面 + 半透明 + 边缘线，避免背面看不到）
  const material = new THREE.MeshPhongMaterial({
    color: 0xcccccc,
    shininess: 30,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.92,
    emissive: 0x111111,
    specular: 0x333333,
  })
  stlMesh = new THREE.Mesh(geom, material)
  const edges = new THREE.EdgesGeometry(geom)
  const lineMaterial = new THREE.LineBasicMaterial({ color: 0x888888 })
  stlMesh.add(new THREE.LineSegments(edges, lineMaterial))
  scene.add(stlMesh)

  // 归一化缩放 + 居中 + 调整相机
  normalizeAndCenter(stlMesh)

  // 坐标轴 + 网格
  axesHelper = new THREE.AxesHelper(5)
  axesHelper.visible = showAxes.value
  scene.add(axesHelper)
  gridHelper = new THREE.GridHelper(20, 20, 0xcccccc, 0xe5e5e5)
  gridHelper.visible = showAxes.value
  scene.add(gridHelper)

  // 选点标记（红球）
  const markerGeo = new THREE.SphereGeometry(0.4, 16, 16)
  const markerMat = new THREE.MeshBasicMaterial({ color: 0xff3366 })
  pickMarker = new THREE.Mesh(markerGeo, markerMat)
  pickMarker.visible = !!props.value
  if (props.value) pickMarker.position.set(props.value.x, props.value.y, props.value.z)
  scene.add(pickMarker)

  // 点击拾取
  renderer.domElement.addEventListener('click', onCanvasClick)

  // 监听容器尺寸变化
  resizeObserver = new ResizeObserver(handleResize)
  resizeObserver.observe(container)

  animate()
}

function normalizeAndCenter(mesh: THREE.Mesh) {
  const box = new THREE.Box3().setFromObject(mesh)
  const size = new THREE.Vector3()
  box.getSize(size)
  const maxDim = Math.max(size.x, size.y, size.z) || 1
  // 归一化到 ~20 单位（与参考实现一致）
  const targetSize = 20
  const scale = targetSize / maxDim
  mesh.scale.set(scale, scale, scale)
  // 居中
  const box2 = new THREE.Box3().setFromObject(mesh)
  const center = box2.getCenter(new THREE.Vector3())
  mesh.position.set(-center.x, -center.y, -center.z)
  // 相机适配
  if (camera && controls) {
    const newBox = new THREE.Box3().setFromObject(mesh)
    const newSize = new THREE.Vector3()
    newBox.getSize(newSize)
    const newMax = Math.max(newSize.x, newSize.y, newSize.z) || 1
    camera.position.set(1.5 * newMax, 0.8 * newMax, 1.5 * newMax)
    camera.lookAt(0, 0, 0)
    controls.target.set(0, 0, 0)
    controls.update()
  }
}

function animate() {
  animationFrameId = requestAnimationFrame(animate)
  if (controls) controls.update()
  if (renderer && scene && camera) renderer.render(scene, camera)
}

function handleResize() {
  if (!canvasContainer.value || !renderer || !camera) return
  const w = canvasContainer.value.clientWidth
  const h = canvasContainer.value.clientHeight
  if (w === 0 || h === 0) return
  renderer.setSize(w, h)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function cleanupThree() {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (renderer) {
    renderer.domElement.removeEventListener('click', onCanvasClick)
    renderer.dispose()
    renderer.domElement.remove()
    renderer = null
  }
  if (controls) {
    controls.dispose()
    controls = null
  }
  if (stlMesh) {
    if (Array.isArray(stlMesh.material)) {
      stlMesh.material.forEach(m => m.dispose())
    } else {
      stlMesh.material.dispose()
    }
    stlMesh = null
  }
  if (pickMarker) {
    pickMarker.geometry.dispose()
    pickMarker.material.dispose()
    pickMarker = null
  }
  scene = null
  camera = null
  axesHelper = null
  gridHelper = null
}

// ============ 工具栏操作 ============
function resetCamera() {
  if (!stlMesh || !camera || !controls) return
  const box = new THREE.Box3().setFromObject(stlMesh)
  const size = new THREE.Vector3()
  box.getSize(size)
  const max = Math.max(size.x, size.y, size.z) || 1
  camera.position.set(1.5 * max, 0.8 * max, 1.5 * max)
  controls.target.set(0, 0, 0)
  controls.update()
}

function toggleAxes() {
  showAxes.value = !showAxes.value
  if (axesHelper) axesHelper.visible = showAxes.value
  if (gridHelper) gridHelper.visible = showAxes.value
}

function clearPick() {
  if (pickMarker) pickMarker.visible = false
  emit('update:value', null)
}

// ============ 3D 点选 ============
function onCanvasClick(event: MouseEvent) {
  if (!stlMesh || !camera || !renderer) return
  const rect = renderer.domElement.getBoundingClientRect()
  const ndc = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1,
  )
  const raycaster = new THREE.Raycaster()
  raycaster.setFromCamera(ndc, camera)
  const hits = raycaster.intersectObject(stlMesh, true)
  if (hits.length === 0) return
  const point = hits[0].point
  if (pickMarker) {
    pickMarker.position.copy(point)
    pickMarker.visible = true
  }
  emit('update:value', { x: point.x, y: point.y, z: point.z })
}

// ============ 生命周期 ============
onMounted(() => {
  // 初始时如已有选点（如父级传入 value），不重建场景，等用户上传后再用
})

onBeforeUnmount(() => {
  cleanupThree()
  if (geometry.value) {
    geometry.value.dispose()
    geometry.value = null
  }
})

// 监听外部 value 变化（理论上 picker 是 v-model 单向源，但保留同步能力）
watch(
  () => props.value,
  val => {
    if (val && pickMarker) {
      pickMarker.position.set(val.x, val.y, val.z)
      pickMarker.visible = true
    } else if (!val && pickMarker) {
      pickMarker.visible = false
    }
  },
)
</script>

<style lang="scss" scoped>
.model-picker {
  &__upload {
    :deep(.el-upload-dragger) {
      padding: 32px 16px;
    }
  }

  &__upload-icon {
    font-size: 48px;
    color: #909399;
    margin-bottom: 8px;
  }

  &__upload-text {
    font-size: 14px;
    color: #606266;
    em {
      color: var(--el-color-primary);
      font-style: normal;
    }
  }

  &__upload-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 8px;
  }

  &__canvas {
    width: 100%;
    height: 360px;
    background: #fafbfc;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;
  }

  &__tools {
    margin-top: 8px;
  }

  &__coord {
    margin-top: 8px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: monospace;
    color: #606266;
    background: #f5f7fa;
    border-radius: 4px;
    display: flex;
    gap: 16px;
  }

  &__hint {
    margin-top: 8px;
    font-size: 12px;
    color: #909399;
  }

  &__error {
    margin-top: 8px;
  }
}
</style>