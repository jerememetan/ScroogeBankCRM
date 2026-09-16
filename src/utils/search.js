export function matchesQuery(values, query) {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  return values.some((value) => String(value).toLowerCase().includes(needle))
}
