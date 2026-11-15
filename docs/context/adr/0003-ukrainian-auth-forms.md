# ADR 0003: Own sign-up and sign-in forms on top of Cognito

- Status: accepted · Date: 2026-11-15

**Context.** The product UI must be Ukrainian. Cognito's hosted/managed login pages do not offer Ukrainian.

**Decision.** The React app calls the Cognito API directly with `fetch` (SignUp, ConfirmSignUp with an email
code, InitiateAuth with USER_PASSWORD_AUTH, refresh token, forgot password). Tokens are kept in
`localStorage`. API Gateway verifies the ID token with a JWT authorizer.

**Alternatives.** Hosted UI (English only), Amplify UI (large dependency, partial translation).

**Consequences.** We own the error messages and screens. Tokens in `localStorage` are acceptable for a
prototype without third-party scripts; revisit before handling payments.
