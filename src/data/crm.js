export function formatUserName(username) {
  const value = String(username || '').trim()
  if (!value) return 'there'
  return value
    .split(/[._\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export const BANK_NAME = 'Scrooge Global Bank'
export const PRODUCT_NAME = 'CRM System'

export const GENDERS = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
export const ACCOUNT_TYPES = ['Savings', 'Checking', 'Business']

export const CLIENT_FIELDS = [
  { label: 'First Name', name: 'first-name', type: 'text' },
  { label: 'Last Name', name: 'last-name', type: 'text' },
  { label: 'Date of Birth', name: 'date-of-birth', type: 'date' },
  { label: 'Gender', name: 'gender', type: 'select', options: GENDERS, placeholder: 'Select gender' },
  { label: 'Email', name: 'email', type: 'email' },
  { label: 'Phone', name: 'phone', type: 'tel' },
  { label: 'Address', name: 'address', type: 'text' },
  { label: 'City', name: 'city', type: 'text' },
  { label: 'State', name: 'state', type: 'text' },
  { label: 'Country', name: 'country', type: 'text', defaultValue: 'Singapore' },
  { label: 'Postal Code', name: 'postal-code', type: 'text' },
]

export const NAV = {
  agent: [
    ['agent', 'Dashboard'],
    ['client', 'Create Client'],
    ['transactions', 'Transactions'],
  ],
  admin: [
    ['admin', 'Dashboard'],
    ['accounts', 'Accounts'],
    ['transactions', 'Transactions'],
  ],
}

export const PAGE_TITLES = {
  agent: 'Agent Dashboard',
  admin: 'Admin Dashboard',
  client: 'Create Client Profile',
  accounts: 'Manage Accounts',
  transactions: 'View Transactions',
}

export const ACTIVITIES = {
  admin: ['User1 created an account', 'User2 updated profile details'],
  agent: ['Created profile for Client1', 'Updated profile for Client2'],
}

export const INITIAL_ACCOUNTS = [
  { id: '1234', client: 'John Doe', type: 'Savings', status: 'Active' },
  { id: '5678', client: 'Jane Smith', type: 'Checking', status: 'Active' },
  { id: '9101', client: 'Alan Turing', type: 'Business', status: 'Pending' },
]

export const INITIAL_TRANSACTIONS = [
  { id: '1001', amount: '$500', type: 'Deposit', status: 'Completed', clientId: '1234', date: '2026-09-12' },
  { id: '1002', amount: '$750', type: 'Withdrawal', status: 'Pending', clientId: '5678', date: '2026-09-14' },
  { id: '1003', amount: '$200', type: 'Withdrawal', status: 'Failed', clientId: '9101', date: '2026-09-15' },
]
