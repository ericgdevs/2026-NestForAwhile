# Local security and privacy audit

- Secrets are supplied through environment variables; `.env` is ignored and hygiene CI rejects tracked secrets.
- User passwords use Argon2; session tokens use HttpOnly cookies.
- Sensitive profile and identity fields use Fernet-backed encrypted columns.
- Seed and test identities are synthetic `@example.test` accounts.
- Role dependencies return 401 for missing authentication and 403 for disallowed roles.
- Analytics/reporting work must not expose client names, emails, or identifiers.
- Product and recipe text is treated as untrusted input; recipe output is schema-validated and rules-guarded.

This project uses the wording “designed with HIPAA safeguards”; it does not claim
HIPAA compliance.
