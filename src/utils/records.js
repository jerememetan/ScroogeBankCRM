export function withDefaults(fields, values) {
  if (!values) return fields
  return fields.map((field) => ({
    ...field,
    defaultValue: values[field.name] ?? field.defaultValue ?? '',
  }))
}

export function readFields(form, fields) {
  const data = new FormData(form)
  return Object.fromEntries(fields.map((field) => [field.name, String(data.get(field.name) || '').trim()]))
}

export function hasMissingFields(values, fields) {
  return fields.some((field) => !values[field.name])
}

export function personName(row) {
  return `${row['first-name'] || ''} ${row['last-name'] || ''}`.trim()
}

export function nextId(prefix, rows) {
  const max = rows.reduce((highest, row) => {
    const n = Number(String(row.id).replace(/\D/g, ''))
    return Number.isFinite(n) ? Math.max(highest, n) : highest
  }, 0)
  return `${prefix}${max + 1}`
}
