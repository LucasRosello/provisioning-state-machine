# Demo Ownership Matrix

The demo ownership validator uses a local map so the workflow can show both
approved and rejected requests before Terraform runs. Keep `team` and
`service_name` in lowercase kebab-case.

| Team | Valid demo services |
| --- | --- |
| `platform` | `users-api`, `billing-api`, `catalog-service`, `identity-service`, `notifications-api`, `audit-service` |
| `growth` | `referrals-api`, `campaigns-api`, `experiments-api`, `landing-pages-api` |
| `payments` | `checkout-api`, `ledger-api`, `settlements-api`, `invoices-api`, `pricing-api` |
| `data` | `analytics-api`, `events-ingestion-api`, `feature-store-api`, `reports-api` |
| `risk` | `fraud-detection-api`, `kyc-api`, `limits-api`, `risk-scoring-api` |
| `mobile` | `mobile-bff`, `push-notifications-api`, `device-registry-api` |
| `support` | `helpdesk-api`, `customer-profile-api`, `case-management-api` |
| `security` | `secrets-broker-api`, `access-review-api`, `policy-audit-api` |

Useful demo examples:

| Scenario | Team | Service | Expected result |
| --- | --- | --- | --- |
| Happy path | `payments` | `checkout-api` | Ownership validation succeeds |
| Happy path | `data` | `analytics-api` | Ownership validation succeeds |
| Happy path | `risk` | `fraud-detection-api` | Ownership validation succeeds |
| Rejection | `growth` | `ledger-api` | Ownership validation fails because `ledger-api` belongs to `payments` |
| Rejection | `support` | `users-api` | Ownership validation fails because `users-api` belongs to `platform` |
