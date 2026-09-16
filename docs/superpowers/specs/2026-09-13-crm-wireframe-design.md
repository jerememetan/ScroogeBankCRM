# CRM Wireframe Design

## Goal

Create a minimal React-only visual wireframe that follows the six screens in Appendix 3 of the project brief. The interface is a front-end prototype only and does not connect to AWS services, authentication, APIs, or a database.

## Screens

1. CRM Login with username and password fields.
2. Admin Dashboard with actions for creating and managing accounts, viewing transactions, and settings, plus recent activity.
3. Manage Accounts with a search field, an add-account action, an account list, and edit/delete actions.
4. Agent Dashboard with actions for creating client profiles, managing profiles, and viewing transactions, plus the agent's recent activity.
5. Create Client Profile with the fields displayed in the supplied mockup and save/cancel actions.
6. View Transactions with a search field, transaction list, and view-details/retry actions.

## Interaction and Data

The prototype uses component state to move between screens. Buttons and navigation links switch the visible wireframe screen. Forms do not persist data; account, activity, and transaction rows are representative static sample data.

## Visual Direction

Keep the presentation intentionally plain: a readable layout, conventional controls, light borders, and no design system, animation, external UI library, or decorative styling. The content and hierarchy mirror Appendix 3 rather than reproducing its ASCII-art boxes.

## Verification

Build the React project, confirm the expected screens render, and visually inspect the running application once.
