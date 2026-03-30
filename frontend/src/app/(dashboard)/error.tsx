'use client'

import { useEffect } from 'react'
import { AlertCircle } from 'lucide-react'

export default function DashboardError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    console.error('[dashboard-error]', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 text-gray-600">
      <AlertCircle className="size-10 text-red-400" />
      <p className="text-sm">Ocorreu um erro ao carregar esta pagina.</p>
      <button
        onClick={() => unstable_retry()}
        className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
      >
        Tentar novamente
      </button>
    </div>
  )
}
