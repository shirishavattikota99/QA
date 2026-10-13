# Providers Collection Documentation

## Collection: `providers`

**Description**  
The `providers` collection stores configuration, branding, and commercial details for game providers integrated into the platform. It is used for provider management, revenue attribution, branding display, and operational control of provider-supplied games.

---

## Collection Fields

### Provider Identity & Configuration

* **`_id`**  
  MongoDB ObjectId uniquely identifying the provider record.  
  **Usage:** Primary key reference across collections

* **`name`**  
  Official name of the provider.  
  **Usage:** Identification across the platform and display in dashboards or game listings

* **`uniqueId`**  
  Unique alphanumeric identifier assigned to the provider.  
  **Usage:** Internal referencing and third-party integrations

---

### Commercial & Operational Settings

* **`royaltyPercentage`**  
  Default revenue share percentage allocated to the provider.  
  **Usage:** Revenue calculation for transactions, bets, or game earnings

* **`status`**  
  Current operational status of the provider.  
  **Values:** `Pending`, `Active`, `Inactive`  
  **Usage:** Controls availability of games and services from this provider

---

### Branding & Visual Configuration

* **`iconTheme`**  
  Preferred icon theme for the provider.  
  **Values:** `Light`, `Dark`, `Custom`  
  **Usage:** Determines which icon variant is shown in the UI

* **`iconLightUrl`**  
  URL for the light-themed provider icon.  
  **Usage:** Displayed when the UI theme is light

* **`iconDarkUrl`**  
  URL for the dark-themed provider icon.  
  **Usage:** Displayed when the UI theme is dark

* **`iconCustomUrl`**  
  URL for the custom-themed provider icon.  
  **Usage:** Used when a custom branding theme is applied

* **`backgroundColor`**  
  Hex code or CSS color value used for provider branding backgrounds.  
  **Usage:** Styling in dashboards and game interfaces

---

### Timestamps

* **`createdAt`**  
  Timestamp when the provider record was created.

* **`updatedAt`**  
  Timestamp of the last update to the provider record.

---

### System Fields

* **`__v`**  
  Mongoose internal version key.  
  **Usage:** Document versioning and concurrency control

---

## Relationships

* `providers._id` → `games.providerId`

---

## Notes

* Provider availability is controlled via the `status` field  
* Branding fields directly impact frontend presentation  
* Revenue calculations rely on `royaltyPercentage`  
* Deactivating a provider implicitly disables its associated games
