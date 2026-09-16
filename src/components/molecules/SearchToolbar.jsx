import { Button } from '../atoms/Button'
import { TextInput } from '../atoms/TextInput'
import { FormField } from './FormField'
import { Surface } from './Surface'

export function SearchToolbar({ label, query, onQueryChange, placeholder, onSearch, children }) {
  return (
    <Surface className="cluster" aria-label={label}>
      <FormField label="Search">
        <TextInput value={query} onChange={onQueryChange} placeholder={placeholder} />
      </FormField>
      <Button onClick={onSearch}>Search</Button>
      {children}
    </Surface>
  )
}
