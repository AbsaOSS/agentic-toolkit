# field-notes

A single-page notes app in plain TypeScript (no framework). Sign-in is handled by `src/auth.ts`,
a thin wrapper over the company's identity SDK. Log records go to our log service: `POST
/api/logs` (one JSON record per request) and `GET /api/logs?correlationId=…` to read them back.
