interface PageHeaderProps {
  title: string
  description?: string
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
      {description && (
        <p className="mt-1 text-sm text-zinc-400">{description}</p>
      )}
    </div>
  )
}
