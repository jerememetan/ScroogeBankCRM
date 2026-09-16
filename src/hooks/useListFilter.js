import { useMemo, useState } from 'react'
import { matchesQuery } from '../utils/search'

export function useListFilter(items, getValues) {
  const [query, setQuery] = useState('')
  const [applied, setApplied] = useState('')

  const visible = useMemo(
    () => items.filter((item) => matchesQuery(getValues(item), applied)),
    [applied, getValues, items],
  )

  return {
    query,
    setQuery,
    visible,
    applySearch: () => setApplied(query),
  }
}
