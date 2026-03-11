class EventBus {
  constructor() {
    this.events = {};
  }
  
  on(eventName, callback) {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    
    // 确保不重复添加同一回调
    if (!this.events[eventName].includes(callback)) {
      this.events[eventName].push(callback);
    }
  }
  
  off(eventName, callback) {
    if (this.events[eventName]) {
      if (callback) {
        // 移除特定回调
        this.events[eventName] = this.events[eventName].filter(cb => cb !== callback);
      } else {
        // 移除该事件的所有回调
        delete this.events[eventName];
      }
    }
  }
  
  emit(eventName, ...args) {
    if (this.events[eventName]) {
      // 使用展开复制数组，避免回调中修改数组导致问题
      [...this.events[eventName]].forEach(callback => {
        try {
          callback(...args);
        } catch (e) {
          console.error(`事件${eventName}处理出错:`, e);
        }
      });
    }
  }
  
  // 兼容uni事件系统的方法，但不依赖uni.$on/$emit
  bindToUni() {
    // 在组件初始化时调用此方法，将uni事件系统绑定到eventBus
    try {
      const self = this;
      
      // 覆盖uni.$on方法，同时注册到eventBus
      const originalOn = uni.$on;
      uni.$on = function(eventName, callback) {
        self.on(eventName, callback);
        // 仍然调用原始方法，但捕获可能的错误
        try {
          return originalOn.call(this, eventName, callback);
        } catch (e) {
          console.error('uni.$on调用失败:', e);
          return false;
        }
      };
      
      // 覆盖uni.$off方法，同时从eventBus解除注册
      const originalOff = uni.$off;
      uni.$off = function(eventName, callback) {
        self.off(eventName, callback);
        // 仍然调用原始方法，但捕获可能的错误
        try {
          return originalOff.call(this, eventName, callback);
        } catch (e) {
          console.error('uni.$off调用失败:', e);
          return false;
        }
      };
      
      // 覆盖uni.$emit方法，同时从eventBus发送事件
      const originalEmit = uni.$emit;
      uni.$emit = function(eventName, ...args) {
        self.emit(eventName, ...args);
        // 仍然调用原始方法，但捕获可能的错误
        try {
          return originalEmit.call(this, eventName, ...args);
        } catch (e) {
          console.error('uni.$emit调用失败:', e);
          return false;
        }
      };
    } catch (e) {
      console.error('绑定到uni事件系统失败:', e);
    }
  }
}

const eventBus = new EventBus();

// 初始化时绑定到uni事件系统
setTimeout(() => {
  eventBus.bindToUni();
}, 0);

export default eventBus;
