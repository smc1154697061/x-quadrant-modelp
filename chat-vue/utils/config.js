/**
 * uni-app 平台配置（仅按平台区分，不分测试/正式）
 * 目标：
 * - H5 打包部署在 Nginx：使用相对路径 '/api' 走反向代理
 * - 微信小程序：必须使用已备案的 HTTPS 域名
 * - App：可使用域名或直连 IP
 *
 * 同时提供可覆盖机制：
 * - 环境变量：import.meta.env.VITE_API_BASE_URL 或 process.env.VUE_APP_API_BASE_URL
 * - H5 运行时覆盖：window.__API_BASE_URL__
 * - App/小程序运行时覆盖：uni.getStorageSync('API_BASE_URL')
 */

// 平台探测
function getPlatform() {
  // #ifdef H5
  return 'h5';
  // #endif
  // #ifdef MP-WEIXIN
  return 'mp-weixin';
  // #endif
  // #ifdef APP-PLUS
  return 'app';
  // #endif
  return 'unknown';
}

const PLATFORM = getPlatform();

// 读取可选覆盖源
const ENV_API = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL)
  || (typeof process !== 'undefined' && process.env && process.env.VUE_APP_API_BASE_URL)
  || '';

let RUNTIME_API = '';
try {
  // H5: 允许通过全局变量覆盖
  if (typeof window !== 'undefined' && window.__API_BASE_URL__) {
    RUNTIME_API = window.__API_BASE_URL__;
  }
} catch (_) {}

try {
  // App/小程序: 允许通过本地存储覆盖
  if (typeof uni !== 'undefined' && typeof uni.getStorageSync === 'function') {
    const stored = uni.getStorageSync('API_BASE_URL');
    if (stored) RUNTIME_API = stored;
  }
} catch (_) {}

// 平台默认值
let DEFAULT_API = '';
let DEFAULT_WS = '';

if (PLATFORM === 'h5') {
  // H5：开发用直连后端，发行放 Nginx 走 /api 反代
  // 判断是否为开发环境
  let isDev = false;
  
  // Vite 环境
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    isDev = import.meta.env.DEV === true || import.meta.env.MODE === 'development';
  }
  // Webpack 环境
  else if (typeof process !== 'undefined' && process.env) {
    isDev = process.env.NODE_ENV === 'development';
  }
  // 运行时判断：如果在 localhost 或 127.0.0.1 上运行，认为是开发环境
  else if (typeof window !== 'undefined' && window.location) {
    const hostname = window.location.hostname;
    isDev = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
  }
  
  DEFAULT_API = isDev ? 'http://127.0.0.1:5000/api' : '/api';
  DEFAULT_WS = isDev ? 'ws://127.0.0.1:5000' : '';
  
} else if (PLATFORM === 'mp-weixin') {
  // 微信小程序必须是备案的 HTTPS 域名
  // 如需修改，编译前设置 VITE_API_BASE_URL 或在小程序端用 uni.setStorageSync('API_BASE_URL', 'https://your-domain.com/api')
  DEFAULT_API = 'https://wx-dudubot.vip.cpolar.cn/api';
  DEFAULT_WS = 'wss://wx-dudubot.vip.cpolar.cn';
  
} else if (PLATFORM === 'app') {
  // App 可用域名或直连 IP
  DEFAULT_API = 'http://115.190.130.68:5000/api';
  DEFAULT_WS = 'ws://115.190.130.68:5000';
}

// 最终 API 基础地址（优先级：ENV > RUNTIME > DEFAULT）
const API_BASE_URL = (ENV_API || RUNTIME_API || DEFAULT_API || '/api');
const WS_BASE_URL = (ENV_API && ENV_API.replace(/^http/, 'ws')) || DEFAULT_WS || '';

// 可选：导出一个设置函数，方便运行时切换（例如 App 内切换环境）
export function setApiBaseUrl(url) {
  if (!url) return;
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync('API_BASE_URL', url);
    }
    if (typeof window !== 'undefined') {
      window.__API_BASE_URL__ = url;
    }
  } catch (_) {}
}

export { API_BASE_URL, WS_BASE_URL, PLATFORM };
export default { API_BASE_URL, WS_BASE_URL, PLATFORM, setApiBaseUrl };
