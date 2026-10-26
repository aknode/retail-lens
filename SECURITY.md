# Deployment boundary

This release is a local, single-user portfolio application. Bind to 127.0.0.1.
The Docker example exposes the service within the container; publish it with
`-p 127.0.0.1:8000:8000`. Before a public deployment add authentication, per-user
storage isolation, HTTPS, rate limits, backups and request-size limits at the
reverse proxy. Never commit secrets, uploaded documents, or customer records.
Only load model artifacts you trained yourself; joblib files can execute code.
Report issues privately through the repository owner's GitHub contact.
