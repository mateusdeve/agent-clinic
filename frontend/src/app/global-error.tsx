'use client'

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  return (
    <html lang="pt-BR">
      <body className="flex items-center justify-center min-h-screen bg-off-white">
        <div className="text-center space-y-4 p-8">
          <h2 className="font-serif text-2xl text-gray-800">Algo deu errado</h2>
          <p className="text-sm text-gray-500">
            Por favor, tente novamente ou entre em contato com o suporte.
          </p>
          <button
            onClick={() => unstable_retry()}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
          >
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  )
}
