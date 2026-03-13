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
   */
  navigateBack(delta = 1) {
    return new Promise((resolve, reject) => {
      const pages = getCurrentPages();
      if (pages.length <= delta) {
        this._handleFallback();
        resolve();
        return;
      }
      
      uni.navigateBack({
        delta,
        success: resolve,
        fail: (err) => {
          this._handleFallback();
          resolve(err);
        }
      });
    });
  }
  
  _handleFallback() {
    const pages = getCurrentPages();
    if (pages.length === 0) return;
    
    const currentPage = pages[pages.length - 1];
    const route = currentPage.route || currentPage.$page?.fullPath || '';
    const path = `/${route.replace(/^\//, '')}`;
    
    let fallbackUrl = '/pages/tools/index';
    
    if (/^\/pages\/tools\//.test(path)) {
      fallbackUrl = '/pages/tools/index';
    } else if (/^\/pages\/chat-modules\//.test(path)) {
      fallbackUrl = '/pages/bot-modules/bot-list/index';
    } else if (/^\/pages\/knowledge-base\/detail/.test(path)) {
      fallbackUrl = '/pages/knowledge-base/index';
    } else if (/^\/pages\/bot-modules\/(bot-detail|edit-bot)\//.test(path)) {
      fallbackUrl = '/pages/bot-modules/bot-list/index';
    }
    
    uni.switchTab({ url: fallbackUrl });
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
