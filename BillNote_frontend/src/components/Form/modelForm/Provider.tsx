import ProviderCard from '@/components/Form/modelForm/components/providerCard.tsx'
import { Button } from '@/components/ui/button.tsx'
import { useProviderStore } from '@/store/providerStore'
import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'

const Provider = () => {
  const providers = useProviderStore(state => state.provider)
  const fetchProviderList = useProviderStore(state => state.fetchProviderList)
  const navigate = useNavigate()
  
  // 监听 providers 变化，确保列表及时更新
  useEffect(() => {
    fetchProviderList()
  }, [])
  
  const handleClick = () => {
    navigate(`/settings/model/new`)
  }

  return (
    <div className="flex flex-col gap-2">
      <div className={'search flex gap-1 py-1.5'}>
        <Button
          type={'button'}
          onClick={() => {
            handleClick()
          }}
          className="w-full"
        >
          添加模型供应商
        </Button>
      </div>
      <div className="text-sm font-light">模型供应商列表</div>
      <div>
        {providers &&
          providers.map((provider, index) => {
            return (
              <ProviderCard
                key={provider.id}
                providerName={provider.name}
                Icon={provider.logo}
                baseUrl={provider.baseUrl}
                id={provider.id}
                enable={provider.enabled}
              />
            )
          })}
      </div>
    </div>
  )
}
export default Provider
