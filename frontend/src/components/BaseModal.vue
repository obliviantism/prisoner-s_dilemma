<template>
  <Teleport to="body">
    <div v-if="show" class="modal-wrapper">
      <div class="modal-backdrop" @click="$emit('close')"></div>
      <div class="modal-container">
        <div class="modal-header">
          <h4 class="modal-title">{{ title }}</h4>
          <button class="close-btn" @click="$emit('close')">&times;</button>
        </div>
        <div class="modal-body">
          <slot></slot>
        </div>
        <div class="modal-footer">
          <slot name="footer">
            <button class="btn btn-secondary" @click="$emit('close')">关闭</button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
export default {
  name: 'BaseModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '提示'
    }
  },
  emits: ['close'],
  watch: {
    show(newVal) {
      if (newVal) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    }
  },
  unmounted() {
    // 确保组件卸载时恢复body滚动
    document.body.style.overflow = '';
  }
}
</script>

<style scoped>
.modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1051;
}

.modal-container {
  background-color: white;
  border-radius: 5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  z-index: 1052;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #eee;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #000;
}

.modal-body {
  padding: 15px;
  flex-grow: 1;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: 15px;
  border-top: 1px solid #eee;
}
</style> 