# Security policy

Do not publish credentials, generated ticket transcripts, or runtime JSON data
in an issue or pull request.

If a Discord token, webhook URL, API key, or shared secret is exposed, revoke or
rotate it at the issuing service. Removing a value from a later commit is not
enough because Git preserves history.

This repository expects all credentials to be supplied through a local `.env`
file based on `.env.example`. The real `.env` file is ignored by Git.
