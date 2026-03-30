export default function HomeLoading() {
  return (
    <div className="space-y-6">
      {/* KPI cards skeleton - matches grid-cols-2 lg:grid-cols-5 layout */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>

      {/* Charts skeleton - matches the 2-column chart layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-72 bg-gray-100 rounded-xl animate-pulse" />
        <div className="h-72 bg-gray-100 rounded-xl animate-pulse" />
      </div>

      {/* Proximas consultas skeleton */}
      <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
    </div>
  )
}
