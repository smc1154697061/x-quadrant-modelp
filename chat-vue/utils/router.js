import { safeUniApiCall } from './api.js';
import { API_BASE_URL } from './config.js';

class Router {
  /**
   * 导航到页面
   */
  navigateTo(url, params = {}) {
    return this._navigate('navigateTo', url, params);
  }
  
  /**
   * 重定向到页面
   */
  redirectTo(url, params = {}) {
    return this._navigate('redirectTo', url, params);
  }
  
  /**
   * 重启到页面
   */
  reLaunch(url, params = {}) {
    return this._navigate('reLaunch', url, params);
  }
  
  /**
   * 切换到选项卡
   */
  switchTab(url) {
    return this._navigate('switchTab', url);
  }
  
  /**
   * 返回页面
   * @param {number} delta - 返回层级，默认为1
   * @param {Object} options - 可选配置
   * @param {string} options.fallbackUrl - navigateBack失败时的回退跳转地址
   * @param {boolean} options.useSmartFallback - 是否使用智能回退（根据当前页面路径自动判断），默认为true
   */
  navigateBack(delta = 1, options = {}) {
    const { fallbackUrl, useSmartFallback = true } = options;
    
    // 先检查页面栈长度，如果只有一页或没有上一页，直接走 fallback
    const pages = getCurrentPages();
    console.log('[Router] 当前页面栈长度:', pages?.length || 0);
    
    if (!pages || pages.length <= 1) {
      console.warn('[Router] 页面栈只有一页，无法返回，直接走 fallback');
      this._executeFallback(fallbackUrl, useSmartFallback);
      return;
    }
    
    uni.navigateBack({
      delta,
      success: () => {
        console.log('[Router] navigateBack 成功');
      },
      fail: (err) => {
        console.warn('[Router] navigateBack 失败:', err);
        this._executeFallback(fallbackUrl, useSmartFallback);
      }
    });
  }
  
  /**
   * 执行 fallback 跳转
   * @private
   */
  _executeFallback(fallbackUrl, useSmartFallback) {
    // 确定回退目标地址
    let targetUrl = fallbackUrl;
    
    // 如果没有指定fallbackUrl且启用智能回退，根据当前页面路径判断
    if (!targetUrl && useSmartFallback) {
      targetUrl = this._getFallbackUrlByCurrentPage();
    }
    
    if (targetUrl) {
      console.log('[Router] 使用 fallback 跳转:', targetUrl);
      
      // 先尝试使用 uni.switchTab（适用于 tabBar 页面）
      uni.switchTab({
        url: targetUrl,
        success: () => {
          console.log('[Router] switchTab 成功');
        },
        fail: (switchErr) => {
          console.warn('[Router] switchTab 失败，尝试 reLaunch:', switchErr);
          // 如果 switchTab 失败（可能目标页不是 tabBar），使用 reLaunch
          uni.reLaunch({
            url: targetUrl,
            success: () => {
              console.log('[Router] reLaunch 成功');
            },
            fail: (reLaunchErr) => {
              console.error('[Router] reLaunch 也失败了:', reLaunchErr);
            }
          });
        }
      });
    } else {
      console.warn('[Router] 没有可用的 fallback URL');
    }
  }
  
  /**
   * 根据当前页面路径获取回退目标地址
   * @private
   */
  _getFallbackUrlByCurrentPage() {
    const pages = getCurrentPages();
    if (!pages || pages.length === 0) {
      return null;
    }
    
    const currentPage = pages[pages.length - 1];
    const route = currentPage?.route || '';
    
    // 根据当前页面路径判断回退目标
    if (route.startsWith('pages/tools/')) {
      return '/pages/tools/index';
    }
    if (route.startsWith('pages/chat-modules/')) {
      return '/pages/bot-modules/bot-list/index';
    }
    if (route === 'pages/knowledge-base/detail') {
      return '/pages/knowledge-base/index';
    }
    if (route.startsWith('pages/bot-modules/bot-detail/') || route.startsWith('pages/bot-modules/edit-bot/')) {
      return '/pages/bot-modules/bot-list/index';
    }
    
    return null;
  }
  
  _navigate(method, url, params = {}) {
    const finalUrl = this._buildUrl(url, params);
    
    return new Promise((resolve, reject) => {
      uni[method]({
        url: finalUrl,
        success: resolve,
        fail: (err) => {
          console.error(`${method}失败:`, err);
          reject(err);
        }
      });
    });
  }
  
  _buildUrl(url, params) {
    if (!params || Object.keys(params).length === 0) {
      return url;
    }
    
    const queryString = Object.keys(params)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
      .join('&');
      
    return url.includes('?') ? `${url}&${queryString}` : `${url}?${queryString}`;
  }
  
  /**
   * 获取完整URL
   */
  getFullUrl(path) {
    // 如果是完整URL，直接返回
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    
    const baseUrl = API_BASE_URL;  // 使用统一配置的API基础URL
    
    // 如果路径以/开头，则不添加额外斜杠
    if (path.startsWith('/')) {
      return `${baseUrl}${path}`;
    }
    return `${baseUrl}/${path}`;
  }

  /**
   * @deprecated 请使用 api.upload() 方法进行文件上传
   * 文件上传（保留用于向后兼容）
   */
  async upload(url, filePath, formData = {}, requireAuth = true) {
    console.warn('[Router] upload 方法已废弃，请使用 api.upload() 替代');
    
    // 导入 api 服务
    const api = (await import('./api.js')).default;
    return api.upload(url, filePath, formData, requireAuth);
  }
}

export default new Router();
