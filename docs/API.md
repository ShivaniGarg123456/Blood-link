# BloodLink API

Status: **Built** = working now, **Planned** = coming, **Stretch** = only if time is left.

## How to use

- Every endpoint except login needs the header `Authorization: Bearer <token>`.
- Get the token from `POST /auth/otp/verify`. The demo OTP is always `1234`.
- The token never expires. The app saves it on the phone, and the user stays logged in until they log out (the app deletes the token) or delete their account.
- One login is used for both roles. The same phone number can be a donor and a receiver. The Home screen should always show both choices: "I need blood" and "I want to donate".
- Errors look like `{"detail": "message"}`. Codes: 400 bad data, 401 not logged in, 404 not found, 409 not allowed right now.
- **Privacy rule:** donor and receiver phone numbers are shared only after the donor is confirmed.
- To test on your own laptop: run the backend, then open `/docs` on the address shown in the terminal.

## 1. Login

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| POST /auth/otp/send | Send an OTP (demo) | Backend | Built |
| POST /auth/otp/verify | Check the OTP, return a token and `is_registered_donor` | Backend | Built |

## 2. Donor

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| POST /donors/register | Save the donor form and run eligibility rules | Backend | Built |
| GET /donors/me | Show the saved profile | Backend | Built |
| PUT /donors/me/location | Update location | Backend | Built |
| PUT /donors/me | Edit profile, rules run again (blood group and phone cannot be changed) | Backend | Planned |
| PUT /donors/me/availability | Pause or resume alerts | Backend | Planned |
| DELETE /donors/me | Delete account and data | Backend | Planned |

## 3. Donor alerts

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| GET /donors/me/alerts | Pending alerts, with blood group, component, distance and seconds left | Backend | Built |
| GET /alerts/{alert_id} | Result of one alert | Backend | Built |
| POST /alerts/{alert_id}/accept | Donor accepts | Backend | Built |
| POST /alerts/{alert_id}/decline | Donor declines | Backend | Built |
| GET /alerts/{alert_id}/route | Road distance and travel time | Backend | Planned |

## 4. Receiver

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| POST /requests/parse | Voice or text in, structured request out | AI | Planned |
| POST /requests | Create a request and start the first wave | Backend | Built |
| GET /requests/mine | History: all requests by this receiver, with the donors who helped | Backend | Built |
| GET /requests/{id}/status | Dashboard: units found, radius, confirmed donors | Backend | Built |
| POST /requests/{id}/close | Found blood elsewhere, stop the search | Backend | Built |
| POST /requests/{id}/alerts/{alert_id}/arrived | Donor reached the hospital | Backend | Built |
| POST /requests/{id}/alerts/{alert_id}/no-show | Donor did not come, search continues | Backend | Built |

## 5. Location

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| GET /geo/search | Hospital name to latitude and longitude | Backend | Planned |

## 6. AI

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| POST /ai/transcribe | Audio to text (Hindi and English) | AI | Planned |
| POST /ai/classify-conditions | Free-text disease to rule categories | AI | Planned |
| POST /ai/explain | Reason in simple language | AI | Planned |

## 7. Automation (sending messages)

The backend does not send messages. It puts them in an outbox. The Automation bot reads the outbox, sends the Telegram message and voice clip, then reports back.

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| GET /alerts/outbox | Messages waiting to be sent | Backend | Planned |
| POST /alerts/outbox/{id}/delivered | Bot reports sent or failed | Backend | Planned |
| POST /integrations/telegram/link | Save a donor's Telegram chat ID | Backend | Planned |

These three need the header `X-Service-Key`.

## 8. Demo and admin

| Endpoint | What it does | Owner | Status |
|---|---|---|---|
| POST /dev/seed | Reload the 13 demo donors | Backend | Planned |
| POST /dev/scheduler/tick | Run one scheduler check now | Backend | Planned |
| GET /admin/stats | Numbers for the pitch dashboard | Backend | Stretch |

## Example: register a donor

```json
{
  "name": "Aman Verma",
  "state": "Delhi",
  "city": "New Delhi",
  "latitude": 28.5677,
  "longitude": 77.2433,
  "age": 28,
  "sex": "male",
  "weight_kg": 70,
  "blood_group": "B-",
  "conditions": [],
  "last_donation_date": null,
  "consent": true
}
```

## Example: create a request

```json
{
  "receiver_name": "Test Receiver",
  "blood_group": "B-",
  "units_needed": 1,
  "hospital": "AIIMS Delhi",
  "latitude": 28.5672,
  "longitude": 77.2100,
  "urgency": "high",
  "component": "whole_blood"
}
```

## Example: what the AI returns from /requests/parse

`component` is `whole_blood`, `rbc` or `null` (if the receiver did not say). The app uses `whole_blood` when it is `null`, and the receiver can change it on the confirm screen. The AI gives only the hospital name. The backend finds the latitude and longitude.

```json
{
  "blood_group": "B-",
  "units": 2,
  "hospital": "AIIMS Delhi",
  "urgency": "high",
  "component": "rbc",
  "language": "hi"
}
```

## Allowed values

| Field | Values |
|---|---|
| blood_group | O-, O+, A-, A+, B-, B+, AB-, AB+ |
| sex | male, female |
| urgency | critical, high, normal |
| component | whole_blood (default), rbc |
| conditions | hiv, hepatitis_b, hepatitis_c, heart_disease, cancer, epilepsy, fever, surgery, pregnancy, breastfeeding, tattoo |
| Donor status | active, not_active, paused |
| Request status | open, fulfilled, closed |
| Alert response | pending, accepted, confirmed, arrived, standby, cancelled, declined, expired, no_show |

## Rules everyone should know

- Eligibility and blood compatibility are decided by fixed rules in the backend. The AI never decides them.
- The receiver chooses the component: whole blood (default) or RBC (red cells). The donor does not choose. Every donor gives the same donation.
- Matching depends on the component. Whole blood is stricter (same ABO group, and Rh-negative receivers get Rh-negative blood only). RBC is more flexible (O- can give to everyone). Platelets and plasma are out of scope.
- The compatibility tables still need a review by a doctor or blood bank officer before real use. The hospital cross-match is always the final check.
- The search starts at 15 km and grows: 15, 30, 45, 60, 100, 200, 500, 1000, 5000 km.
- Each wave lasts 3 minutes, or ends early if everyone in it declines.
- Nobody is alerted twice for the same request.
- The search stops when the receiver closes the request, enough donors are confirmed, or 24 hours pass (the request then closes automatically).
- 1 donor gives 1 unit.
- If more donors accept than needed, the nearest ones win. The rest become standby and get a thank-you message.
- If a nearer donor is still deciding, a farther donor who accepted waits up to 15 seconds.
- A receiver sees the name and phone of the donors who helped (confirmed or arrived) in the request history, so they can contact them in future.

## Out of scope for the prototype

Platelets and plasma, real SMS and voice calls, payments, report and block, languages other than Hindi and English.