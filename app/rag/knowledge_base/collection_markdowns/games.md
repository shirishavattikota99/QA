# Games Collection Documentation

## Collection: `games`

**Description**  
The `games` collection stores metadata and operational configuration for all games available on the platform. It is used for game discovery, categorization, provider management, and availability control across player-facing and administrative interfaces.

---

## Collection Fields

### Game Identity & Ownership

* **`_id`**  
  MongoDB ObjectId uniquely identifying the game record.  
  **Usage:** Primary key reference across collections

* **`masterProviderId`**  
  Reference to the master provider that owns or manages the game globally across multiple providers.  
  **Usage:** Provider-level grouping and reporting  
  **Type:** Foreign reference

* **`providerId`**  
  Reference to the provider supplying this specific game instance.  
  **Usage:** Provider-based filtering and operational routing  
  **Type:** Foreign reference

---

### Classification & Metadata

* **`categoryIds`**  
  Array of references to game categories such as Slots, Live Casino, Table Games, Sports, etc.  
  **Usage:** Lobby grouping, filtering, and recommendations  
  **Type:** Multi-value reference

* **`name`**  
  Human-readable name of the game.  
  **Usage:** Display in player UI and admin dashboards

* **`notes`**  
  Internal administrative notes related to the game.  
  **Usage:** Operational context  
  **Visibility:** Admin only

---

### Operational Status & Availability

* **`status`**  
  Current operational state of the game.  
  **Values:** `Pending`, `Active`, `Inactive`  
  **Usage:** Controls game visibility and player access

* **`launchUrl`**  
  URL used to launch the game client.  
  **Usage:** Game session initiation for players or operators

---

### Media & Display

* **`imageUrl`**  
  URL of the game thumbnail or banner image.  
  **Usage:** Frontend display in lobbies and promotions

* **`imageAvailable`**  
  Indicates whether an image is available for the game.  
  **Usage:** UI fallback handling  
  **Type:** Boolean

---

### Sorting & Timestamps

* **`sortDate`**  
  Date used to control game ordering and prioritization.  
  **Usage:** Featured games and relevance-based sorting

* **`createdAt`**  
  Timestamp when the game record was created.

* **`updatedAt`**  
  Timestamp of the last update to the game record.

---

## Relationships

* `games.masterProviderId` → `masterProviders._id`  
* `games.providerId` → `providers._id`  
* `games.categoryIds` → `categories._id`

---

## Notes

* Game availability is controlled via the `status` field  
* Games may belong to multiple categories  
* Sorting should rely on `sortDate`, not `createdAt`  
* Time-based analytics should use game-play or transaction-level collections
