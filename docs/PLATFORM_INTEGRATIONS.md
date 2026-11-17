# Platform Integrations

## Progressive Web App

The prototype includes a web app manifest and service worker. Offline caching requires HTTPS or localhost and at least one successful online load.

## Advertising

The repository defines a provider-neutral rewarded-ad contract. No production vendor SDK, application ID, placement ID, or credentials are included.

A production adapter should:

- Request an ad from the host platform.
- Report completion only after the provider confirms a completed view.
- Grant rewards exactly once.
- Reject failed, skipped, or unavailable ad attempts.
- Enforce server- or platform-authoritative daily limits where required.

## Cloud Saves

A provider-neutral cloud-save contract is included. A production implementation still requires an identity provider, backend, conflict-resolution policy, and credentials.

## Native Distribution

The current project is not packaged as a native mobile application. Store-specific wrappers, signing, privacy disclosures, SDK configuration, and release credentials remain outside this repository.
