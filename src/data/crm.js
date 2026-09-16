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

export const USER_ROLES = ['Agent', 'Admin']
export const USER_STATUSES = ['Active', 'Disabled']
export const ACCOUNT_STATUSES = ['Active', 'Inactive', 'Pending']

export const AGENT_FIELDS = [
  { label: 'First Name', name: 'first-name', type: 'text' },
  { label: 'Last Name', name: 'last-name', type: 'text' },
  { label: 'Email', name: 'email', type: 'email' },
  { label: 'Role', name: 'role', type: 'select', options: USER_ROLES, defaultValue: 'Agent' },
]

export const NAV = {
  agent: [
    ['agent', 'Dashboard'],
    ['clients', 'Clients'],
    ['accounts', 'Accounts'],
    ['transactions', 'Transactions'],
  ],
  admin: [
    ['admin', 'Dashboard'],
    ['agents', 'Agents'],
  ],
}

export const PAGE_TITLES = {
  agent: 'Agent Dashboard',
  admin: 'Admin Dashboard',
  clients: 'Clients',
  accounts: 'Accounts',
  transactions: 'Transactions',
  agents: 'Agents',
}

export const ACTIVITIES = {
  admin: ['Created agent Aisha Tan', 'Disabled agent Wei Lin'],
  agent: ['Opened a Savings account for Jane Smith', 'Updated profile for John Doe'],
}

export const INITIAL_CLIENTS = [
  {
    id: 'C1001',
    'first-name': 'John',
    'last-name': 'Doe',
    'date-of-birth': '1985-03-12',
    gender: 'Male',
    email: 'john.doe@email.com',
    phone: '+6591112222',
    address: '1 Raffles Place',
    city: 'Singapore',
    state: 'Singapore',
    country: 'Singapore',
    'postal-code': '048616',
  },
  {
    id: 'C1002',
    'first-name': 'Jane',
    'last-name': 'Smith',
    'date-of-birth': '1990-07-22',
    gender: 'Female',
    email: 'jane.smith@email.com',
    phone: '+6593334444',
    address: '8 Shenton Way',
    city: 'Singapore',
    state: 'Singapore',
    country: 'Singapore',
    'postal-code': '068811',
  },
  {
    id: 'C1003',
    'first-name': 'Alan',
    'last-name': 'Turing',
    'date-of-birth': '1978-06-23',
    gender: 'Male',
    email: 'alan.turing@email.com',
    phone: '+6595556666',
    address: '30 Raffles Avenue',
    city: 'Singapore',
    state: 'Singapore',
    country: 'Singapore',
    'postal-code': '039803',
  },
]

export const INITIAL_ACCOUNTS = [
  { id: 'A1234', client: 'John Doe', type: 'Savings', status: 'Active' },
  { id: 'A5678', client: 'Jane Smith', type: 'Checking', status: 'Active' },
  { id: 'A9101', client: 'Alan Turing', type: 'Business', status: 'Pending' },
]

export const INITIAL_AGENTS = [
  { id: 'U1000', 'first-name': 'Root', 'last-name': 'Admin', email: 'root.admin@scrooge.sg', role: 'Admin', status: 'Active', protected: true },
  { id: 'U1001', 'first-name': 'Aisha', 'last-name': 'Tan', email: 'aisha.tan@scrooge.sg', role: 'Agent', status: 'Active' },
  { id: 'U1002', 'first-name': 'Wei', 'last-name': 'Lin', email: 'wei.lin@scrooge.sg', role: 'Agent', status: 'Disabled' },
]

export const INITIAL_TRANSACTIONS = [
  { id: '1001', amount: '$500', type: 'Deposit', status: 'Completed', accountId: 'A1234', date: '2026-09-12' },
  { id: '1002', amount: '$750', type: 'Withdrawal', status: 'Pending', accountId: 'A5678', date: '2026-09-14' },
  { id: '1003', amount: '$200', type: 'Withdrawal', status: 'Failed', accountId: 'A9101', date: '2026-09-15' },
]
