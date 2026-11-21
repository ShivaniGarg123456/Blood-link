# BloodLink: Final API agreement

Base URL while testing: http://127.0.0.1:8000
Interactive test page: http://127.0.0.1:8000/docs

Status: **Built** = working now, **Planned** = needed for the final demo, **Stretch** = only if time is left.

## How to call the API

**Login.** Every endpoint except `/auth/*` and `/health` needs this header:

    Authorization: Bearer <token>

The token comes from `POST /auth/otp/verify`. The demo OTP is always `1234`.

**Service key.** Endpoints marked "service" are for the Automation bot only. They need:

    X-Service-Key: <value from the .env file>

**Errors** come back as `{"detail": "message"}` with these codes: 400 bad data, 401 not logged in,
404 not found, 409 not allowed right now (for example an expired alert).

**Privacy rule (everyone follows this).** A donor's name and phone reach the receiver, and the
receiver's name and phone reach the donor, **only after that donor is confirmed**. Never show them earlier.

---

## 1. Login
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| POST /auth/otp/send | Send OTP (demo) | Backend | Built |
| POST /auth/otp/verify | Check OTP. Returns `token`, `phone`, `is_registered_donor` | Backend | Built |
| GET /health | Server is running | Backend | Planned |

## 2. Donor
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| POST /donors/register | Save donor form and run eligibility rules. `consent` must be true | Backend | Built |
| GET /donors/me | Saved profile, so a returning donor skips the form | Backend | Built |
| PUT /donors/me/location | Update latitude and longitude | Backend | Built |
| PUT /donors/me | Edit profile (weight, last donation date, conditions). Rules run again | Backend | Planned |
| PUT /donors/me/availability | Donor pauses or resumes alerts (`{"available": false}`) | Backend | Planned |
| GET /donors/me/history | Past alerts and donations of this donor | Backend | Planned |
| DELETE /donors/me | Delete the account and all saved data (privacy) | Backend | Planned |

## 3. Donor alerts
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| GET /donors/me/alerts | Pending alerts with `distance_km` and `seconds_left` | Backend | Built |
| GET /alerts/{alert_id} | Result of one alert: pending, confirmed, standby, cancelled ... | Backend | Built |
| POST /alerts/{alert_id}/accept | Donor accepts. Nearest donor wins | Backend | Built |
| POST /alerts/{alert_id}/decline | Donor declines | Backend | Built |
| GET /alerts/{alert_id}/route | Road distance and travel time to the hospital (OSRM, cached) | Backend | Planned |

## 4. Receiver
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| POST /requests/parse | Voice or text in, structured request out (see below) | AI | Planned |
| POST /requests | Create request and start wave 1 (15 km) | Backend | Built |
| GET /requests/mine | All requests made by this receiver | Backend | Planned |
| GET /requests/{id}/status | Dashboard: units found, radius, confirmed donors | Backend | Built |
| POST /requests/{id}/close | Found blood elsewhere or no longer needed. Optional `reason` | Backend | Built |
| POST /requests/{id}/alerts/{alert_id}/arrived | Confirmed donor reached the hospital | Backend | Built |
| POST /requests/{id}/alerts/{alert_id}/no-show | Donor did not come. Unit is given back, search continues | Backend | Built |

## 5. Location helpers
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| GET /geo/search?q=AIIMS Delhi | Hospital or address to latitude and longitude (Nominatim, cached) | Backend | Planned |

## 6. AI
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| POST /ai/classify-conditions | Free-text disease to rule categories | AI | Planned |
| POST /ai/transcribe | Audio to text (Hindi and English) | AI | Planned |
| POST /ai/explain | Plain-language reason in the user's language | AI | Planned |

## 7. Automation (message delivery)
The backend never sends messages itself. It puts them in an **outbox**. The Automation bot reads the
outbox, sends the Telegram or WhatsApp message and voice clip, then reports back.

| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| GET /alerts/outbox?limit=50 | Messages waiting to be sent (service) | Backend | Planned |
| POST /alerts/outbox/{id}/delivered | Bot reports `sent` or `failed` (service) | Backend | Planned |
| POST /integrations/telegram/link | Save a donor's Telegram chat ID after `/start` (service) | Backend | Planned |

Outbox message types: `new_alert`, `confirmed`, `standby`, `cancelled`, `request_reopened`,
`request_fulfilled` (to the receiver).

## 8. Admin and demo
| Endpoint | Purpose | Owner | Status |
|---|---|---|---|
| GET /admin/stats | Requests, response times, donors per area (for the pitch dashboard) | Backend | Stretch |
| GET /admin/shortage-forecast | Blood groups likely to run low | Backend | Stretch |
| POST /dev/seed | Reload the 13 demo donors (demo mode only) | Backend | Planned |
| POST /dev/scheduler/tick | Run one scheduler check now (demo mode only) | Backend | Planned |

---

## Example bodies

**POST /donors/register**

    {
      "name": "Aman Verma", "state": "Delhi", "city": "New Delhi",
      "latitude": 28.5677, "longitude": 77.2433,
      "age": 28, "sex": "male", "weight_kg": 70, "blood_group": "B-",
      "conditions": [], "last_donation_date": null, "consent": true
    }

**POST /requests**

    {
      "receiver_name": "Test Receiver", "blood_group": "B-", "units_needed": 1,
      "hospital": "AIIMS Delhi", "latitude": 28.5672, "longitude": 77.2100,
      "urgency": "high"
    }

**POST /requests/parse** (AI returns this, the receiver confirms it, then the app calls POST /requests)

    {"blood_group": "B-", "units": 2, "hospital": "AIIMS Delhi", "urgency": "high", "language": "hi"}

**Outbox message**

    {
      "outbox_id": 12, "type": "new_alert", "to_phone": "9000000001",
      "telegram_chat_id": null, "language": "hi",
      "payload": {"alert_id": 5, "blood_group": "B-", "hospital": "AIIMS Delhi",
                  "distance_km": 3.3, "seconds_left": 180}
    }

---

## Allowed values

- **blood_group:** O-, O+, A-, A+, B-, B+, AB-, AB+
- **sex:** male, female
- **urgency:** critical, high, normal
- **conditions (the only names the AI may return):** hiv, hepatitis_b, hepatitis_c, heart_disease,
  cancer, epilepsy, fever, surgery, pregnancy, breastfeeding, tattoo
- **Donor status:** active, not_active, paused
- **Request status:** open, fulfilled, closed
- **Alert response:** pending, accepted, confirmed, arrived, standby, cancelled, declined, expired, no_show

## Rules everyone must know

- **Eligibility** is decided by fixed rules in the backend. The AI never decides eligibility or compatibility.
- **Waves:** 15, 30, 45, 60, 100, 200, 500, 1000, 5000 km. Each lasts 3 minutes, or ends early if
  everyone in it declines. Nobody is alerted twice for the same request.
- **The search does not stop** at a fixed distance. It stops only when the receiver closes the request
  or enough donors are confirmed.
- **1 donor = 1 unit** of whole blood. If more donors accept than needed, the nearest win. The rest
  become standby and get: "The need is fulfilled for now. Thank you, we will contact you if needed."
- If a nearer donor is still deciding, a farther donor who accepted waits up to 15 seconds.
- When a confirmed donor is marked **arrived**, the backend saves today as the last donation date and
  pauses that donor until the next eligible date.
- Each alert shows the distance. The donor decides whether to accept.

## Core data

- **Donor:** phone, name, state, city, latitude, longitude, age, sex, weight, blood group, language,
  last donation date, status, reason, eligible_after, consent_given_at, telegram_chat_id
- **Request:** receiver phone, name, blood group, units needed, units found, hospital, latitude,
  longitude, urgency, status, current radius
- **Alert:** request, donor, distance, wave radius, sent_at, expires_at, responded_at, response
- **Outbox:** alert, type, to_phone, telegram_chat_id, language, payload, status (waiting, sent, failed)

## Environment variables (.env, never push this file)

    JWT_SECRET, DEMO_OTP, WAVE_SECONDS, CONFIRM_WINDOW_SECONDS, SCHEDULER_TICK_SECONDS,
    SERVICE_KEY, TELEGRAM_BOT_TOKEN, LLM_API_KEY

## Out of scope for the prototype

Platelets and plasma, real SMS and voice calls (design only), payments, report and block,
languages beyond Hindi and English.