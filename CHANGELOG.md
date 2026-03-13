# Changelog

All notable changes to the MLB Game Bot project will be documented in this file. This project adheres to basic change control principles.

## [1.1.0] - 13/03/2026 - CURRENT

### Added
- Privacy Policy page (`privacy.html`).
- Link to Privacy Policy in `index.html` footer.
- Subresource Integrity (SRI) for external dependencies (Apache Arrow).
- This `CHANGELOG.md` to establish formal change control (PCI DSS 6.4 compliance).

### Changed
- Improved website security headers recommendations.
- Updated `Makefile` and `deploy-website.sh` to support minimization.

## [1.0.3] - 13/03/2026

### Added
- New build process for website content.
- Deployment script `scripts/deploy-website.sh`.
- GitHub Actions workflow for automated deployment.
- `Makefile` targets for website deployment.

## [1.0.0] - Initial Release
- Initial implementation of the MLB Game Bot.
- Static site served via GCS.
