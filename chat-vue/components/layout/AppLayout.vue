<template>
  <!-- PC端布局 -->
  <view v-if="isPc" class="pc-layout">
    <!-- 侧边栏导航 -->
    <pc-sidebar />
    
    <!-- 内容区域 -->
    <view class="pc-content">
      <!-- 顶部导航栏 -->
      <app-header v-if="hasTitle" :title="title" />
      <app-header v-else />
      
      <!-- 主要内容 -->
      <view class="pc-main-content">
        <slot></slot>
      </view>
    </view>
  </view>
  
  <!-- 移动端布局 -->
  <view v-else class="mobile-layout">
    <!-- 顶部导航栏 -->
    <app-header v-if="hasTitle" :title="title" />
    <app-header v-else />
    
    <!-- 主要内容 -->
    <view class="mobile-main-content" :class="{'no-tab-bar': hideTabBar}" 
          :style="{ paddingTop: (statusBarHeight + 44) + 'px', paddingBottom: (hideTabBar ? safeAreaBottom : safeAreaBottom) + 'px' }">
      <slot></slot>
    </view>
    
    <!-- 注释掉自定义底部导航栏，使用系统tabBar -->
    <!-- <view v-if="!hideTabBar" class="mobile-tab-bar" :style="{ paddingBottom: safeAreaBottom + 'px' }">
      <view 
        class="tab-item" 
        v-for="(item, index) in tabBarItems" 
        :key="index"
        :class="{ active: isActive(item.pagePath) }"
        @tap="switchTab(item.pagePath)"
      >
        <image 
          class="tab-icon" 
          :src="item.currentIconPath || (isActive(item.pagePath) ? item.selectedIconPath : item.iconPath)" 
          mode="aspectFit"
          :data-index="index"
          @error="handleImageError"
        ></image>
        <text class="tab-text" :class="{ 'active-text': isActive(item.pagePath) }">{{ item.text }}</text>
      </view>
    </view> -->
  </view>
</template>

<script>
import PcSidebar from './PcSidebar.vue'
import AppHeader from './AppHeader.vue'
import chatIcon from '@/static/images/chat.png'
import knowledgeIcon from '@/static/images/knowledge.png'
import extractionIcon from '@/static/images/extraction.png'
import settingsIcon from '@/static/images/settings.png'

export default {
  name: 'AppLayout',
  components: {
    PcSidebar,
    AppHeader
  },
  props: {
    title: {
      type: String,
      default: '渡渡鸟知识库'
    },
    hideTabBar: {
      type: Boolean,
      default: false
    },
    showBack: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isPc: false,
      currentPath: '',
      tabBarItems: [
        {
          pagePath: '/pages/knowledge-base/index',
          text: '知识库',
          iconPath: knowledgeIcon,
          selectedIconPath: knowledgeIcon
        },
        {
          pagePath: '/pages/bot-modules/bot-list/index',
          text: '智能对话',
          iconPath: chatIcon,
          selectedIconPath: chatIcon
        },
        {
          pagePath: '/pages/tools/index',
          text: '工具',
          iconPath: extractionIcon,
          selectedIconPath: extractionIcon
        },
        {
          pagePath: '/pages/settings/index',
          text: '设置',
          iconPath: settingsIcon,
          selectedIconPath: settingsIcon
        }
      ],
      iconLoadError: false,
      statusBarHeight: 0,
      safeAreaBottom: 0,
      tabBarHeight: 50,
      navBarHeight: 44,
      contentStyle: {}
    }
  },
  computed: {
    hasTitle() {
      // 检查title是否为自定义值（非默认值）
      return this.title !== '渡渡鸟知识库' && !!this.title.trim();
    }
  },
  created() {
    // 获取全局设置的设备类型
    const app = getApp();
    if (app && app.globalData) {
      this.isPc = app.globalData.isPc || false;
    } else {
      // 如果没有全局设置，根据屏幕宽度判断
      this.checkDeviceType();
    }
    
    // 获取当前页面路径
    this.getCurrentPagePath();
    
    // 监听设备类型变化事件
    uni.$on('deviceTypeChange', this.handleDeviceTypeChange);
    
    // 监听页面切换事件
    uni.$on('pageChange', this.handlePageChange);
    
    // 获取系统信息
    this.getSystemInfo();
  },
  mounted() {
    // 页面加载时预加载所有图标
    this.preloadIcons();
    
    // #ifdef H5
    // 添加触摸结束事件监听，修复图片显示问题
    if (!this.isPc) {
      document.addEventListener('touchend', this.refreshImages);
    }
    // #endif
  },
  beforeDestroy() {
    // 移除事件监听
    uni.$off('deviceTypeChange', this.handleDeviceTypeChange);
    uni.$off('pageChange', this.handlePageChange);
    
    // #ifdef H5
    // 移除触摸事件监听
    if (!this.isPc) {
      document.removeEventListener('touchend', this.refreshImages);
    }
    // #endif
  },
  methods: {
    // 预加载所有图标
    preloadIcons() {
      if (this.isPc) return; // 仅移动端需要
      
      // #ifdef H5
      // 创建图片缓存对象
      this.iconCache = {};
      
      this.tabBarItems.forEach(item => {
        // 创建新的图片对象
        const normalImg = new Image();
        const activeImg = new Image();
        
        // 设置源
        normalImg.src = item.iconPath;
        activeImg.src = item.selectedIconPath;
        
        // 设置图片属性以确保正确渲染
        normalImg.style.opacity = '1';
        activeImg.style.opacity = '1';
        normalImg.setAttribute('crossOrigin', 'anonymous');
        activeImg.setAttribute('crossOrigin', 'anonymous');
        
        // 存入缓存
        this.iconCache[item.pagePath] = {
          normal: normalImg,
          active: activeImg
        };
        
        // 加载事件
        normalImg.onload = () => {
          this.$forceUpdate(); // 强制更新视图
        };
        activeImg.onload = () => {
          this.$forceUpdate(); // 强制更新视图
        };
        
        // 错误处理
        normalImg.onerror = () => {
          // 重试加载
          setTimeout(() => {
            normalImg.src = item.iconPath + '?t=' + new Date().getTime();
          }, 500);
        };
        activeImg.onerror = () => {
          // 重试加载
          setTimeout(() => {
            activeImg.src = item.selectedIconPath + '?t=' + new Date().getTime();
          }, 500);
        };
      });
      // #endif
      
      // #ifndef H5
      // 为微信小程序环境初始化图标状态
      this.tabBarItems.forEach((item, index) => {
        const isActive = this.isActive(item.pagePath);
        this.$set(this.tabBarItems, index, {
          ...item,
          isActive: isActive,
          currentIconPath: isActive ? item.selectedIconPath : item.iconPath
        });
      });
      // #endif
    },
    
    // 刷新所有图像显示
    refreshImages() {
      if (this.isPc) return; // 仅移动端需要
      
      // 强制更新视图
      this.$forceUpdate();
      
      // 延迟处理，确保在DOM更新后执行
      setTimeout(() => {
        // #ifdef H5
        // 查找所有底部导航栏图标
        const icons = document.querySelectorAll('.mobile-tab-bar .tab-icon');
        
        // 对每个图标强制刷新
        icons.forEach((icon, index) => {
          if (icon) {
            // 获取对应的tabBarItem
            const item = this.tabBarItems[index];
            if (item) {
              // 重新设置src属性触发重新加载
              const isActive = this.isActive(item.pagePath);
              const newSrc = isActive ? item.selectedIconPath : item.iconPath;
              
              // 只有当src不同时才更新，避免不必要的重新加载
              if (icon.src !== newSrc) {
                icon.src = newSrc;
              }
              
              // 确保图标可见
              icon.style.opacity = '1';
              icon.style.visibility = 'visible';
              icon.style.display = 'block';
              icon.style.filter = 'grayscale(0)';
              
              // 添加动画效果
              if (isActive) {
                icon.style.transform = 'scale(1.05)';
              } else {
                icon.style.transform = 'scale(1)';
              }
            }
          }
        });
        // #endif
        
        // #ifndef H5
        // 在微信小程序中使用uni API更新图标
        const query = uni.createSelectorQuery().in(this);
        this.tabBarItems.forEach((item, index) => {
          // 使用数据绑定方式更新图标
          const isActive = this.isActive(item.pagePath);
          this.$set(this.tabBarItems, index, {
            ...item,
            isActive: isActive,
            currentIconPath: isActive ? item.selectedIconPath : item.iconPath
          });
        });
        // #endif
      }, 50);
    },

    // 处理设备类型变化
    handleDeviceTypeChange(data) {
      if (data) {
        this.isPc = data.isPc;
      }
    },
    
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 获取当前页面路径
    getCurrentPagePath() {
      const pages = getCurrentPages();
      if (pages.length > 0) {
        const currentPage = pages[pages.length - 1];
        this.currentPath = `/${currentPage.route}`;
      }
    },
    
    // 处理页面切换事件
    handlePageChange(data) {
      if (data && data.path) {
        this.currentPath = data.path;
      }
    },
    
    // 检查当前页面是否激活
    isActive(path) {
      // 处理知识库详情页面的特殊情况
      if (path === '/pages/knowledge-base/index' && this.currentPath.startsWith('/pages/knowledge-base/')) {
        return true;
      }
      
      // 处理智能对话的特殊情况
      if (path === '/pages/bot-modules/bot-list/index' && 
          (this.currentPath.startsWith('/pages/bot-modules/') || 
           this.currentPath.startsWith('/pages/chat-modules/'))) {
        return true;
      }
      
      // 处理内容提取的特殊情况
      if (path === '/pages/tools/index' && 
          this.currentPath.startsWith('/pages/tools/')) {
        return true;
      }
      
      // 处理设置的特殊情况
      if (path === '/pages/settings/index' && 
          this.currentPath.startsWith('/pages/settings/')) {
        return true;
      }
      
      // 普通路径匹配
      return this.currentPath.startsWith(path);
    },
    
    // 切换Tab - 重写此方法，移除document.querySelectorAll使用
    switchTab(path) {
      if (this.currentPath === path) return;
      
      // 预先更新当前路径，提前反馈给用户
      const oldPath = this.currentPath;
      this.currentPath = path;
      
      // 使用uni.switchTab进行导航
      uni.switchTab({
        url: path,
        success: () => {
          // Tab切换成功
        },
        fail: (err) => {
          // 恢复原路径
          this.currentPath = oldPath;
          
          // 尝试使用navigateTo导航
          uni.navigateTo({
            url: path,
            success: () => {
              this.currentPath = path;
            },
            fail: () => {
              // 导航失败，恢复原路径
              this.currentPath = oldPath;
            }
          });
        }
      });
    },
    
    // 处理图片加载错误
    handleImageError(e) {
      // 尝试重新加载图片
      const index = parseInt(e.currentTarget.dataset.index);
      if (!isNaN(index) && index >= 0 && index < this.tabBarItems.length) {
        const item = this.tabBarItems[index];
        if (item) {
          // 从缓存中获取预加载的图片
          const cachedImg = this.iconCache && this.iconCache[item.pagePath];
          if (cachedImg) {
            // 使用缓存中的图片URL重新设置
            e.currentTarget.src = this.isActive(item.pagePath) 
              ? cachedImg.active.src 
              : cachedImg.normal.src;
          } else {
            // 如果没有缓存，直接重新设置原始URL
            e.currentTarget.src = this.isActive(item.pagePath) 
              ? item.selectedIconPath 
              : item.iconPath;
          }
          
          // 强制更新视图
          this.$forceUpdate();
        }
      }
    },
    
    // 获取系统信息
    getSystemInfo() {
      uni.getSystemInfo({
        success: (res) => {
          this.statusBarHeight = res.statusBarHeight || 0;
          this.safeAreaBottom = res.safeAreaInsets ? (res.safeAreaInsets.bottom || 0) : 0;
          this.navBarHeight = 44;
          
          // 计算内容区域样式
          this.contentStyle = {
            height: `calc(100vh - ${this.statusBarHeight + this.navBarHeight}px)`,
            paddingTop: `${this.statusBarHeight + this.navBarHeight}px`
          };
        }
      });
    },
    goBack() {
      uni.navigateBack({
        delta: 1,
        fail: () => {
          uni.switchTab({
            url: '/pages/chat-modules/chat-list/index'
          });
        }
      });
    }
  }
}
</script>

<style>
/* PC端布局样式 */
.pc-layout {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
}

.pc-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  box-sizing: border-box;
  min-height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.pc-main-content {
  flex: 1;
  padding: 60px 20px 20px; /* 增加顶部padding，避免内容被导航栏遮挡 */
  box-sizing: border-box;
  position: relative;
}

/* 移动端布局样式 */
.mobile-layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
  position: relative;
}

.mobile-main-content {
  flex: 1;
  box-sizing: border-box;
  width: 100%;
}

.mobile-main-content.no-tab-bar {
  padding-bottom: 0;
}

.mobile-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 50px;
  background-color: #fff;
  box-shadow: 0 -1px 5px rgba(0,0,0,0.1);
  display: flex;
  z-index: 100;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5px 0;
}

.tab-icon {
  width: 24px;
  height: 24px;
  margin-bottom: 2px;
}

.tab-text {
  font-size: 12px;
  color: #7A7E83;
}

.active-text {
  color: #007AFF;
}

.tab-item.active {
  opacity: 1;
}

/* 响应式处理 */
@media (max-width: 767px) {
  .pc-layout {
    display: none;
  }
}

@media (min-width: 768px) {
  .mobile-layout {
    display: none;
  }
}
</style> 