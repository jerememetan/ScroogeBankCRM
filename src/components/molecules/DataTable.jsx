import { Message } from '../atoms/Message'

export function DataTable({ caption, labelledBy, columns, rows, empty }) {
  if (rows.length === 0) return <Message>{empty}</Message>

  return (
    <table className="table" aria-label={caption} aria-labelledby={labelledBy}>
      <thead>
        <tr>
          {columns.map((column) => <th key={column.key}>{column.header}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            {columns.map((column) => (
              <td key={column.key}>
                {column.render ? column.render(row) : row[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
