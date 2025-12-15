import { create } from 'zustand'
import { IProvider } from '@/types'
import {
  addProvider,
  deleteProviderById,
  getProviderById,
  getProviderList,
  updateProviderById,
} from '@/services/model.ts'

interface ProviderStore {
  provider: IProvider[]
  setProvider: (provider: IProvider) => void
  setAllProviders: (providers: IProvider[]) => void
  getProviderById: (id: number) => IProvider | undefined
  getProviderList: () => IProvider[]
  fetchProviderList: () => Promise<void>
  loadProviderById: (id: string) => Promise<IProvider | undefined>
  addNewProvider: (provider: IProvider) => Promise<string | undefined>
  updateProvider: (provider: IProvider) => Promise<string | undefined>
  deleteProvider: (id: string) => Promise<boolean>
}

export const useProviderStore = create<ProviderStore>((set, get) => ({
  provider: [],

  sanitizeProvider: (provider: IProvider) => ({
    ...provider,
    name: provider.name ? provider.name.trim() : provider.name,
    apiKey: provider.apiKey ? provider.apiKey.trim() : provider.apiKey,
    baseUrl: provider.baseUrl ? provider.baseUrl.trim() : provider.baseUrl,
    logo: provider.logo ? provider.logo.trim() : provider.logo,
    type: provider.type ? provider.type.trim() : provider.type,
  }),

  // 添加或更新一个 provider
  setProvider: newProvider =>
    set(state => {
      const exists = state.provider.find(p => p.id === newProvider.id)
      if (exists) {
        return {
          provider: state.provider.map(p => (p.id === newProvider.id ? newProvider : p)),
        }
      } else {
        return { provider: [...state.provider, newProvider] }
      }
    }),

  // 设置整个 provider 列表
  setAllProviders: providers => set({ provider: providers }),
  loadProviderById: async (id: string) => {
    const item = await getProviderById(id)
    if (!item) return

    return {
      id: item.id,
      name: item.name ? item.name.trim() : item.name,
      logo: item.logo,
      apiKey: item.api_key ? item.api_key.trim() : item.api_key,
      baseUrl: item.base_url ? item.base_url.trim() : item.base_url,
      type: item.type ? item.type.trim() : item.type,
      enabled: item.enabled,
    }
  },
  addNewProvider: async (provider: IProvider) => {
    const sanitized = get().sanitizeProvider(provider)
    const payload = {
      ...sanitized,
      api_key: sanitized.apiKey,
      base_url: sanitized.baseUrl,
    }
    try {
      const id = await addProvider(payload)
      if (id) {
        await get().fetchProviderList()
      }
      return id
    } catch (error) {
      console.error('Error fetching provider:', error)
    }
  },
  // 按 id 获取单个 provider
  getProviderById: id => get().provider.find(p => p.id === id),
  updateProvider: async (provider: IProvider) => {
    try {
      const sanitized = get().sanitizeProvider(provider)
      const data = {
        ...sanitized,
        api_key: sanitized.apiKey,
        base_url: sanitized.baseUrl,
      }
      const id = await updateProviderById(data)
      if (id) {
        await get().fetchProviderList()
      }
      return id
    } catch (error) {
      console.error('Error fetching provider:', error)
    }
  },
  deleteProvider: async (id: string) => {
    try {
      await deleteProviderById(id)
      await get().fetchProviderList()
      return true
    } catch (error) {
      console.error('删除模型供应商失败:', error)
      return false
    }
  },
  getProviderList: () => get().provider,
  fetchProviderList: async () => {
    try {
      const res  = await getProviderList()

        set({
          provider: res.map(
            (item: {
              id: string
              name: string
              logo: string
              api_key: string
              base_url: string
              type: string
              enabled: number
            }) => {
              return {
                id: item.id,
                name: item.name,
                logo: item.logo,
                apiKey: item.api_key,
                baseUrl: item.base_url,
                type: item.type,
                enabled: item.enabled,
              }
            }
          ),
        })
    } catch (error) {
      console.error('Error fetching provider list:', error)
    }
  },
}))
