import { vi } from 'vitest'

// Mock uni-app 全局对象
global.uni = {
  navigateTo: vi.fn(),
  redirectTo: vi.fn(),
  reLaunch: vi.fn(),
  switchTab: vi.fn(),
  navigateBack: vi.fn(),
  showToast: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn(),
  showModal: vi.fn(),
  showActionSheet: vi.fn(),
  getSystemInfoSync: vi.fn(() => ({
    platform: 'h5',
    windowWidth: 375,
    windowHeight: 667,
  })),
  getStorageSync: vi.fn(),
  setStorageSync: vi.fn(),
  removeStorageSync: vi.fn(),
  request: vi.fn(),
  uploadFile: vi.fn(),
  downloadFile: vi.fn(),
  chooseImage: vi.fn(),
  previewImage: vi.fn(),
  saveImageToPhotosAlbum: vi.fn(),
  getImageInfo: vi.fn(),
  compressImage: vi.fn(),
}

global.getCurrentPages = vi.fn(() => [])

// Mock console 避免测试中的日志干扰
// vi.spyOn(console, 'log').mockImplementation(() => {})
// vi.spyOn(console, 'warn').mockImplementation(() => {})
// vi.spyOn(console, 'error').mockImplementation(() => {})
