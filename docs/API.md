# Shared API agreement

| Endpoint | Purpose | Owner |
|---|---|---|
| POST /auth/otp/send, /auth/otp/verify | Mobile login | Backend |
| POST /donors/register | Save donor form, run screening | Backend |
| POST /requests/parse | Audio or text in, structured request out | AI |
| POST /requests | Create confirmed request, start first wave | Backend |
| POST /alerts/send | Deliver an alert to a donor | Automation |
| POST /requests/{id}/accept | Donor accepts, details exchanged | Backend |
| GET /requests/{id}/status | Current radius, timer, accepted donors | Backend |
| POST /requests/{id}/close | Cancel remaining alerts | Backend |
