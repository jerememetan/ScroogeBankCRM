# CRM Wireframe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a plain, front-end-only React CRM wireframe that matches all six Appendix 3 mockup screens.

**Architecture:** A single React application holds the active wireframe screen in component state. Static arrays provide account, transaction, and activity content; button clicks switch screens without calling any service.

**Tech Stack:** React, Vite, Vitest, React Testing Library, plain CSS.

---

## File Structure

- `package.json` declares the Vite, React, and test scripts/dependencies.
- `index.html` supplies the browser entry point.
- `src/main.jsx` mounts the application.
- `src/App.jsx` owns screen navigation and all six mockup screen components.
- `src/App.css` supplies minimal layout and control styling.
- `src/App.test.jsx` verifies all screen navigation labels and the client form.

### Task 1: Scaffold the React application

**Files:**
- Create: `package.json`
- Create: `index.html`
- Create: `src/main.jsx`

- [ ] **Step 1: Create the application manifest**

```json
{
  "scripts": { "dev": "vite", "build": "vite build", "test": "vitest run" },
  "dependencies": { "react": "latest", "react-dom": "latest" },
  "devDependencies": { "@vitejs/plugin-react": "latest", "vite": "latest", "vitest": "latest", "@testing-library/react": "latest", "@testing-library/jest-dom": "latest", "@testing-library/user-event": "latest", "jsdom": "latest" }
}
```

- [ ] **Step 2: Install dependencies**

Run: `pnpm install`
Expected: dependencies installed successfully.

### Task 2: Build and test the wireframe

**Files:**
- Create: `src/App.test.jsx`
- Create: `src/App.jsx`
- Create: `src/App.css`

- [ ] **Step 1: Write a failing screen-navigation test**

```jsx
it('opens the agent dashboard after login', async () => {
  render(<App />)
  await userEvent.click(screen.getByRole('button', { name: 'Login' }))
  expect(screen.getByRole('heading', { name: 'Agent Dashboard' })).toBeInTheDocument()
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pnpm test`
Expected: FAIL because `App` is not yet implemented.

- [ ] **Step 3: Implement the six supplied mockup screens**

Implement `App` with a `screen` state value for `login`, `admin`, `accounts`, `agent`, `client`, and `transactions`. Render semantic headings, forms, buttons, and static lists matching Appendix 3. The Login button opens the Agent Dashboard. The Admin Dashboard exposes the Manage Accounts and View Transactions screens; the Agent Dashboard exposes Create Client Profile and View Transactions. Add a Back button to each non-dashboard workflow screen.

- [ ] **Step 4: Run the test suite**

Run: `pnpm test`
Expected: PASS.

- [ ] **Step 5: Build the production bundle**

Run: `pnpm build`
Expected: output reports a successful Vite production build.

### Task 3: Browser verification

**Files:**
- Verify: `src/App.jsx`
- Verify: `src/App.css`

- [ ] **Step 1: Start the development server**

Run: `pnpm dev --host 127.0.0.1`
Expected: Vite reports a local URL.

- [ ] **Step 2: Inspect the login, agent, client, admin, accounts, and transactions screens**

Use browser navigation to select each screen. Confirm headings, labels, controls, and sample rows are visible without clipping.

- [ ] **Step 3: Stop the development server**

Expected: no development server remains running.
