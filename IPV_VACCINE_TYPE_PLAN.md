# Adding IPV / fIPV as Polio Vaccine Types — Implementation Plan

> Status: **Analysis / To implement**
> Context: IPV was added to Vaccine Request Forms (POLIO-2209) and a temporary
> `fIPV` campaign-type workaround was added (POLIO-2220).
>
> **Requirement (confirmed):** IPV and fIPV are **vaccines**, not campaign
> types. They must be moved out of Campaign Type and into the Vaccines field
> for consistency across the platform. Existing campaigns that use IPV or fIPV
> as a campaign type must be migrated so the vaccine is recorded in the
> Vaccines field (i.e. on their scopes) instead.
>
> **8 new vaccine options to add** (stored and displayed with `&`, same
> encoding as existing `nOPV2 & bOPV`):
> `IPV`, `fIPV`, `IPV & bOPV`, `fIPV & bOPV`, `IPV & nOPV2`, `fIPV & nOPV2`,
> `IPV & nOPV2 & bOPV`, `fIPV & nOPV2 & bOPV`
>
> **Virus rule:** when a user selects a virus, the Scope-tab vaccine list
> only shows the options valid for that virus (matrix in §3). This is new
> behaviour. Existing campaigns keep their current vaccines even if they
> would no longer be offered. Changing the virus after districts are
> already selected is **out of this work** (follow-up ticket — the
> problem already exists today).
>
> **PM ticket sequence (4 steps):**
> 1. IPV/fIPV as vaccine types instead of campaign types + migrate existing
>    IPV/fIPV-typed campaigns → §4–§7 (Phases 1–4);
> 2. Enable on Supply Chain — IPV only, combinations split into one entry
>    per vaccine, fIPV uses IPV supply → §5.3;
> 3. Enable on Stock Management — IPV country profiles (Form A,
>    destruction, incident, earmarked), separate balance per vaccine,
>    fIPV aggregated under IPV at 5 doses/vial → §5.3;
> 4. **(Last)** Redesign campaign calendar & map to visualize the 8 new
>    combinations → §8 (Phase 5). Colours and calendar/map legend UX
>    (likely a drawer) to be defined later. Existing colours for nOPV2,
>    mOPV2, bOPV and nOPV2 & bOPV stay.

---

## 1. Current state

IPV / fIPV are only half-implemented:

| Area | State |
| --- | --- |
| Vaccine Request Form (`VaccineRequestForm.vaccine_type`) | ✅ `IPV` allowed (`INDIVIDUAL_VACCINES`, migration `0257`); `fIPV` not allowed — **by design** (§5.3: fIPV campaigns use IPV VRFs) |
| Campaign / Round / SubActivity scopes | ❌ Neither `IPV` nor `fIPV` in `VACCINES` choices |
| Vaccine stock (`VaccineStock`) | ❌ IPV stock cannot be created (fIPV stock must **never** exist — aggregated under IPV, §5.3) |
| fIPV campaigns | ⚠️ Workaround via a fake `CampaignType` named `fIPV` |
| IPV campaigns | ⚠️ Some campaigns may also use a `CampaignType` named `IPV` — to be audited and migrated the same way |

Central definitions in `plugins/polio/models/base.py` (lines 60–88):

```python
VIRUSES = [
    ("PV1", _("PV1")),            # displayed as cVDPV1 in the frontend
    ("PV2", _("PV2")),
    ("PV3", _("PV3")),            # displayed as cVDPV3 in the frontend
    ("cVDPV2", _("cVDPV2")),
    ("WPV1", _("WPV1")),
    ("PV1 & cVDPV2", _("PV1 & cVDPV2")),
    ("cVDPV1 & cVDPV2", _("cVDPV1 & cVDPV2")),
]

VACCINES = [
    ("mOPV2", _("mOPV2")),
    ("nOPV2", _("nOPV2")),
    ("bOPV", _("bOPV")),
    ("nOPV2 & bOPV", _("nOPV2 & bOPV")),
]

INDIVIDUAL_VACCINES = [
    ("mOPV2", _("mOPV2")),
    ("nOPV2", _("nOPV2")),
    ("bOPV", _("bOPV")),
    ("IPV", _("IPV")),
]

DOSES_PER_VIAL = {
    "mOPV2": 20,
    "nOPV2": 50,
    "bOPV": 20,
}
```

> Note: this legacy `DOSES_PER_VIAL` dict in code is not the runtime source
> of truth for vaccine presentations. Presentations (doses per vial options)
> come from the `vaccine_doses_per_vial` Config (slug
> `DOSES_PER_VIAL_CONFIG_SLUG = "vaccine_doses_per_vial"`, served by
> `api/vaccines/doses_per_vaccine.py` and consumed by the frontend via
> `useGetDosesPerVial`). The confirmed Config content is:

```json
{
  "IPV": [1, 5],
  "bOPV": [10, 20],
  "mOPV2": [50],
  "nOPV2": [20, 50]
}
```

> So **IPV presentations are 1 and 5 doses per vial** — already present in
> the Config, no guessing needed. There is intentionally **no `fIPV` key**
> in this Config and none must be added: per PM/Gael (see §5.3), fIPV has
> no supply-chain/stock identity of its own — fIPV campaigns use IPV vials,
> managed under IPV at **5 doses per vial**. Any `content[vaccine]` lookup
> must therefore run **after** normalizing `fIPV → IPV` (see §5.3), never
> with the raw `fIPV` token.

The fIPV workaround is explicitly flagged as debt in
`plugins/polio/models/base.py` (`PolioCampaignManager.get_queryset`, ~line 644):

```python
# Ugly patch to allow fIPV campaigns to be launched. This needs to be fixed, fIPV is not a campaign type, it's a vaccine type for polio campaigns.
.filter(campaign_types__name__in=[CampaignType.POLIO, "fIPV"])
```

Frontend equivalent in
`plugins/polio/js/src/domains/VaccineModule/SupplyChain/hooks/api/vrf.tsx`:
campaigns are fetched twice (`campaignType: 'polio'` and
`campaignType: 'fIPV'`) and fIPV campaigns are forced to
`fipvVaccineOptions`.

---

## 2. The 12 vaccine options (definitive list)

Storage encoding stays `"A & B"` (the existing encoding for
`"nOPV2 & bOPV"`). The `+` in the requirement is notation only — do **not**
introduce a second `+` encoding, it would break the splitter, API filters,
geojson, exports and PowerBI consumers.

`VACCINES` becomes (existing 4 + new 8 = **12**):

| # | Stored value | Origin |
| --- | --- | --- |
| 1 | `mOPV2` | existing (legacy — see note below) |
| 2 | `nOPV2` | existing |
| 3 | `bOPV` | existing |
| 4 | `nOPV2 & bOPV` | existing |
| 5 | `IPV` | **new** |
| 6 | `fIPV` | **new** |
| 7 | `IPV & bOPV` | **new** (`IPV + bOPV`) |
| 8 | `fIPV & bOPV` | **new** (`fIPV + bOPV`) |
| 9 | `IPV & nOPV2` | **new** (`IPV + nOPV2`) |
| 10 | `fIPV & nOPV2` | **new** (`fIPV + nOPV2`) |
| 11 | `IPV & nOPV2 & bOPV` | **new** (`IPV + nOPV2 + bOPV`) |
| 12 | `fIPV & nOPV2 & bOPV` | **new** (`fIPV + nOPV2 + bOPV`) |

`INDIVIDUAL_VACCINES` **does not change**: `mOPV2`, `nOPV2`, `bOPV`, `IPV`.
Per PM spec (§5.3), `fIPV` is a campaign-scope vaccine only — it gets **no**
individual entry, because Supply Chain and Stock Management only ever see
`IPV`. This is what makes VRFs, stocks and presentations IPV-only by
construction.

Explicitly **not** allowed (do not add):

- `IPV & fIPV` (and any combination containing both) — IPV and fIPV are the
  full-dose and fractional-dose presentations of the same antigen; they are
  never combined in one scope.
- Any `mOPV2` combination, and no IPV/fIPV combination with `mOPV2`.
- The theoretical remaining combinations of 5 individual vaccines
  (2⁵ − 1 = 31). The list above is a closed, business-defined set — do
  **not** generate all combinations.

> **`mOPV2` (confirmed):** retired from **new** campaigns. Keep it in
> `VACCINES` / `INDIVIDUAL_VACCINES` so existing mOPV2 campaigns and stocks
> keep working. Do **not** offer it in the virus-filtered Scope picker.

### Traps to avoid

1. **`max_length=12` is already full.**
   `"nOPV2 & bOPV"` is exactly 12 chars. `"IPV & nOPV2 & bOPV"` is 18 chars,
   `"fIPV & nOPV2 & bOPV"` is 19 chars. The scope/stock `vaccine` fields must
   be widened (the VRF field already uses `max_length=30` — mirror that).

2. **Positional splitting in `Campaign.split_combined_vaccines`**
   (`models/base.py`, ~line 1130):

   ```python
   @staticmethod
   def split_combined_vaccines(vaccines):
       if VACCINES[3][0] in vaccines:
           vaccines.remove(VACCINES[3][0])
           vaccines.add(VACCINES[1][0])
           vaccines.add(VACCINES[2][0])
       return vaccines
   ```

   It hardcodes list indexes. Inserting the 8 new entries anywhere before
   index 3, or reordering, silently corrupts splitting for **existing**
   campaigns. Every `*_single_vaccines_*` / `single_vaccine_*` property on
   `Campaign`, `Round` and `SubActivity` routes through this function.
   → Append new entries **after** the existing 4 **and** rewrite the
   splitter generically (split each value on `" & "`, union the tokens).
   The generic rewrite is mandatory anyway: it must split the new triples.

3. **Substring danger: `IPV` ⊂ `fIPV`.**
   Any `"IPV" in vaccine_string` check matches `fIPV` too. All vaccine
   matching must be **token-based** (split on `" & "` first, then compare
   tokens). This applies to the splitter, the nOPV2-authorization checks
   (§5), stock calculations, and frontend `includes()` calls
   (e.g. `round.vaccine_names_extended.includes(vaccine)` in
   `SupplyChain/hooks/api/vrf.tsx` — already substring-based, must be
   checked for IPV/fIPV false positives).

4. **`VaccineStock.vaccine` uses the wrong list.**
   `VaccineStock.vaccine` has `choices=VACCINES` (`models/base.py`,
   ~line 1565), so a nonsensical combined stock (`"nOPV2 & bOPV"`) is
   allowed but an IPV stock is impossible. `VaccineStockCalculator`
   joins arrivals via `request_form__vaccine_type = vaccine_stock.vaccine`,
   so IPV arrivals can never be counted in stock today. (fIPV stocks/VRFs
   must never be created at all — §5.3.)

5. **Tests index `VACCINES` positionally.**
   e.g. `tests/models/test_campaign_models.py` uses `VACCINES[0][0]` …
   `VACCINES[3][0]` as `mopv2 / nopv2 / bopv / nopv2_bopv`. Appending the new
   entries after the existing 4 keeps those indexes valid — another reason
   to append, not insert.

---

## 3. Virus → vaccine matrix (definitive)

From the confirmed specification table. Frontend virus **labels** differ
from stored **values** (`PV1` is displayed as `cVDPV1`, `PV3` as `cVDPV3` —
see `js/src/constants/virus.ts`), so the mapping must be keyed by the
stored virus value:

| Virus (stored value) | Label shown | Valid vaccines |
| --- | --- | --- |
| `PV1` | cVDPV1 | `bOPV`, `IPV`, `fIPV`, `IPV & bOPV`, `fIPV & bOPV` |
| `PV3` | cVDPV3 | `bOPV`, `IPV`, `fIPV`, `IPV & bOPV`, `fIPV & bOPV` |
| `cVDPV2` | cVDPV2 | `nOPV2`, `IPV`, `fIPV`, `IPV & nOPV2`, `fIPV & nOPV2` |
| `WPV1` | WPV1 | `bOPV`, `IPV`, `fIPV`, `IPV & bOPV`, `fIPV & bOPV` |
| `PV1 & cVDPV2` | PV1 & cVDPV2 | `nOPV2`, `bOPV`, `nOPV2 & bOPV`, `IPV`, `fIPV`, `IPV & nOPV2`, `IPV & bOPV`, `IPV & nOPV2 & bOPV`, `fIPV & nOPV2`, `fIPV & bOPV`, `fIPV & nOPV2 & bOPV` |
| `cVDPV1 & cVDPV2` | cVDPV1 & cVDPV2 | `nOPV2`, `bOPV`, `nOPV2 & bOPV`, `IPV`, `fIPV`, `IPV & nOPV2`, `IPV & bOPV`, `IPV & nOPV2 & bOPV`, `fIPV & nOPV2`, `fIPV & bOPV`, `fIPV & nOPV2 & bOPV` |

Notes:

- `PV2` exists in the backend `VIRUSES` choices but has no row in the
  matrix and no frontend option. **Confirmed: leave as is** (client is
  not complaining). No new vaccine list, no mapping to another virus
  row, no cleanup in this work.
- The same mapping must exist **in both** backend (validation, §5) and
  frontend (Scope-tab filtering, §6), from a single source of truth per
  side (e.g. `VACCINES_BY_VIRUS` in `models/base.py` and a mirrored
  constant in `js/src/constants/virus.ts`), with a test asserting they
  agree on the vaccine/virus value sets.

---

## 4. Phase 1 — Backend model core

File: `plugins/polio/models/base.py`

- [ ] Append the 8 new entries to `VACCINES` (after the existing 4, in the
      order of §2).
- [ ] Do **not** add `fIPV` to `INDIVIDUAL_VACCINES` — it stays
      `mOPV2 / nOPV2 / bOPV / IPV` (PM spec, §5.3). This single decision is
      what keeps fIPV out of VRFs, stocks and presentations everywhere.
- [ ] Add the `fIPV → IPV` supply-chain/stock normalization (constant +
      helper, §5.3) in `models/base.py`, next to the splitter.
- [ ] Doses per vial: IPV is confirmed — presentations **1 and 5** in the
      `vaccine_doses_per_vial` Config (see §1), and Stock Management
      manages IPV at **5 doses per vial** (§5.3). No Config value is
      needed for IPV, and **no `fIPV` Config key must be added**. The
      legacy code dict `DOSES_PER_VIAL` is unused at runtime; do not rely
      on it.
- [ ] Add `VACCINES_BY_VIRUS` mapping (§3), keyed by stored virus values.
- [ ] Rewrite `Campaign.split_combined_vaccines` generically: split every
      entry on `" & "` and union the tokens (token-based, IPV/fIPV-safe).
- [ ] Widen `vaccine` fields from `max_length=12` to `max_length=30` on:
  - [ ] `RoundScope.vaccine` (~line 175)
  - [ ] `CampaignScope.vaccine` (~line 196)
  - [ ] `SubActivityScope.vaccine` (~line 336)
  - [ ] `VaccineStock.vaccine` (~line 1565) — and switch its choices to
        `INDIVIDUAL_VACCINES` (stock is per individual vaccine, never
        combined; this is what makes **IPV** stocks creatable — and, by
        construction, makes fIPV stocks impossible, as required by §5.3)
- [ ] Decide on `CountryPlan.vaccine` (`models/country_plan.py`, line 50,
      also `choices=VACCINES`): combinations or individual only?
- [ ] Run migrations:

  ```bash
  docker compose run --rm iaso manage makemigrations polio
  docker compose run --rm iaso manage migrate
  ```

  Expected: one new migration (next after `0257`) altering the fields
  above. `VaccineRequestForm.vaccine_type` does **not** change (IPV is
  already allowed, fIPV must stay disallowed). Choices + length changes
  only — no data migration for scopes (the campaign-type migration is
  Phase 4).

Acceptance check: existing values (`mOPV2`, `nOPV2`, `bOPV`,
`nOPV2 & bOPV`) are unchanged and still valid; `VACCINES[0..3]` indexes
used by existing tests still point at the same vaccines.

---

## 5. Phase 2 — Backend validation & consumers

### 5.1 Server-side virus → vaccine validation (new)

Frontend filtering (§6) is UX only; the API must enforce the matrix too.

- [ ] In `CampaignSerializer.validate`
      (`api/campaigns/serializers/campaigns.py`): when the campaign is a
      polio campaign with a `virus`, validate every submitted scope
      vaccine (campaign-level scopes, round scopes, and sub-activity
      scopes via their own serializer) against `VACCINES_BY_VIRUS[virus]`.
      Reject with a clear `ValidationError` naming the invalid vaccine.
- [ ] Legacy tolerance: campaigns whose stored vaccine is not valid for
      their virus (e.g. `mOPV2` campaigns, pre-matrix data) must remain
      **readable and saveable without touching scopes**. Only reject when
      a newly submitted scope vaccine is invalid — do not block unrelated
      edits. (Decide explicitly; strict validation on every save will
      lock out legacy campaigns.)

### 5.2 Consumers with exact-match / substring assumptions

- [ ] `plugins/polio/tasks/archive_vaccine_stock_for_rounds.py` (~line 54)
      Iterates `[v[0] for v in VACCINES]` (including combinations, for
      which no stock exists) and filters rounds by exact scope vaccine.
      → Iterate `INDIVIDUAL_VACCINES` (IPV included, fIPV **not**); match
      rounds whose **split + normalized** vaccine list (§5.3) contains
      the vaccine — so `fIPV`, `IPV & nOPV2` and `fIPV & bOPV` rounds all
      archive against the **IPV** stock (and separately against the
      nOPV2/bOPV stock for combined rounds). Otherwise IPV rounds never
      get stock history archived.
- [ ] `VaccineStockCalculator._get_list_of_vaccines_received`
      (`models/base.py`, ~lines 2340–2358): with `end_date`, eligible
      rounds are filtered by exact `scopes__vaccine`. → Match scopes whose
      vaccine is the individual vaccine or a combination containing it
      (token-based, after `fIPV → IPV` normalization).
- [ ] `VaccineStockCalculator._get_config_and_compute_stock_for_presentation`
      (`models/base.py`, ~line 2770):
      `presentation_config.content[self.vaccine_stock.vaccine]` throws
      `KeyError` if the Config lacks the key. → Use `.get(...)`
      defensively, and always look up the **normalized** vaccine (§5.3):
      an IPV stock looks up `"IPV"` (`[1, 5]`, already in the confirmed
      Config — verify in **every** environment). Never look up `fIPV`;
      no `fIPV` Config key must be created.
- [ ] nOPV2 authorization checks —
      `api/campaigns/serializers/campaigns.py` (create ~line 208, update
      ~line 369) and `api/campaigns/vaccine_authorizations/utils.py`
      (~line 60): replace `"nOPV2" in round.vaccine_names` with membership
      in `round.single_vaccine_list`. Behaviour to preserve: IPV/fIPV-only
      rounds do **not** trigger nOPV2 authorization; `IPV & nOPV2` /
      `fIPV & nOPV2` rounds **do**.
- [ ] `plugins/polio/export_utils.py` (`polio_vaccines`, ~line 164):
      color dict knows only the 4 current values, returns `None`
      otherwise. → Add the 8 new values or return a default color.
- [ ] `api/dashboards/supply_chain.py` (~line 111): already uses
      `campaign.single_vaccines_extended_list` — but that list now
      contains `fIPV`, which never equals a stock vaccine. → Compare
      against the **normalized** list (§5.3) so an IPV stock matches
      fIPV campaigns. Add a test to lock this in.
- [ ] Vaccine repository endpoints (`api/vaccines/repository_forms.py`,
      `repository_reports.py`): `vaccine_name` filtering must accept
      `IPV`, `fIPV` and the new combinations.

### 5.3 Supply Chain & Stock Management: IPV only, fIPV aggregated (PM spec — confirmed)

> Gael/PM: *fIPV doesn't need its own option. It uses the same vial as IPV,
> so fIPV campaigns use IPV supply and stock. All IPV and fIPV stock is
> managed under IPV at 5 doses per vial, even though an fIPV dose is
> smaller. No separate fIPV presentation or dose calculation is needed.*
>
> *Only IPV needs to be added, not the combinations. When a campaign uses
> a combination such as `IPV + nOPV2` or `fIPV + bOPV`, a separate supply
> chain entry is created for each vaccine (one for IPV, one for nOPV2).
> Each entry then flows to Stock Management, where a separate country
> profile is created for each vaccine.*

Consequences, to implement exactly:

- [ ] **One normalization rule, one place.** Add in `models/base.py`:
      `SUPPLY_CHAIN_VACCINE_ALIASES = {"fIPV": "IPV"}` plus a helper
      (e.g. `normalize_vaccine_for_supply_chain(vaccine)`) and a Campaign
      property returning the split + normalized + deduplicated list
      (e.g. `supply_chain_vaccines_list`, derived from
      `single_vaccines_extended_list`). Scope/display logic keeps the raw
      tokens (`fIPV` stays visible on campaigns/calendar); **every**
      supply-chain/stock consumer uses the normalized list:
  - VRF vaccine dropdown & creation (frontend + `VaccineRequestForm`);
  - `api/dashboards/supply_chain.py` stock↔campaign matching;
  - `archive_vaccine_stock_for_rounds` task;
  - `VaccineStockCalculator` eligible-round matching;
  - doses-per-vial Config lookups (`fIPV` is looked up as `IPV`).
- [ ] **Supply Chain (VRF):** `VaccineRequestForm.vaccine_type` choices
      stay `INDIVIDUAL_VACCINES` — `IPV` already allowed, `fIPV` and all
      combinations stay **invalid** as a VRF type. A campaign scoped
      `IPV & nOPV2` produces **two** VRFs (one `IPV`, one `nOPV2`);
      a campaign scoped `fIPV` or `fIPV & bOPV` produces an **IPV** VRF
      (plus a `bOPV` VRF for the combination). PreAlerts/VARs hang off
      those IPV VRFs unchanged.
- [ ] **Stock Management:** `VaccineStock.vaccine` → `INDIVIDUAL_VACCINES`
      (Phase 1) makes **IPV country profiles** creatable — one
      `VaccineStock` per (country, vaccine), `unique_together` already
      enforces it. Users must be able to record, for IPV profiles,
      exactly as for nOPV2/bOPV/mOPV2:
  - [ ] Form A (`OutgoingStockMovement`);
  - [ ] destruction reports (`DestructionReport`);
  - [ ] incident reports (`IncidentReport`);
  - [ ] earmarked stock (`EarmarkedStock`).
      These sub-resources reference `vaccine_stock`, so they work once
      the IPV profile exists — verify each create/edit flow + permissions
      (`VaccineStockPermission` / earmark permissions) with an IPV stock
      in tests, don't assume.
- [ ] **Separate balances per vaccine:** an `IPV & nOPV2` campaign feeds
      two stocks; `VaccineStockCalculator` per stock already computes
      received/used/usable/unusable/destroyed/earmarked separately —
      IPV balances aggregate **IPV + fIPV** campaign usage together
      (via normalized matching), oral-vaccine balances stay separate.
      No combined-vaccine stock, ever.
- [ ] **Doses per vial = 5 for IPV in Stock Management:** the
      "Doses per vial" field must offer **5** for IPV (Config
      `IPV: [1, 5]` already offers it for supply-chain arrivals; stock
      variation forms — Form A / destruction / incident / earmarked —
      derive their options from the stock's presentations, so an IPV
      stock that only ever received 5-dose vials offers 5). All IPV/fIPV
      dose math uses 5 doses/vial; **no fractional (fIPV) dose
      calculation** (e.g. no ×5 doses-per-fIPV-dose logic) anywhere.
- [ ] **Audit every downstream vaccine dropdown** (full inventory in
      §6.0): each one is a *filter* or a *"which vaccine is this object
      for"* selector — none of them creates a campaign vaccine, so each
      gets `IPV` only (never `fIPV`, never combinations, except
      National Logistics Plan pending PM question 6). Do not miss:
      earmarked-stock and Form A modals, which list campaigns/rounds for
      an already-chosen stock vaccine (campaigns whose normalized
      vaccines include IPV must appear for an IPV stock, incl. fIPV
      campaigns), and the doses-per-vial dropdowns whose options depend
      on the inherited vaccine.
- [ ] **Frontend Stock/Supply-Chain lists:** add `IPV` **only** (no
      `fIPV`, no combinations) to `singleVaccinesList`
      (`SupplyChain/constants.ts`) and `VaccineForStock`
      (`constants/types.ts`). That single list drives: Create Vaccine
      Stock modal, stock-management filters, public stock page,
      repository filters. VRF vaccine options for a selected campaign
      come from its (normalized) single vaccines — an fIPV campaign
      shows **IPV** in the dropdown, deduplicated if a campaign somehow
      has both IPV and fIPV scopes.

---

## 6. Phase 3 — Frontend: virus-filtered vaccine selection

### 6.0 Where vaccines are actually chosen (important — read first)

**A vaccine is only ever *selected* in one place: the Scope
("Périmètre") tab.** There, the user picks a vaccine in the map legend
("Vaccin" panel, `ScopeMapLegend`) and clicks districts/regions to assign
them to that vaccine; the district table also shows one vaccine per
district. This applies identically to campaign-level scopes, per-round
scopes (round tabs in `ScopeForm.tsx`) and sub-activity scopes.

Everywhere else, vaccines are either **computed** or **used to filter /
specify an existing object**:

| Where | What it really is | Vaccine list used today |
| --- | --- | --- |
| Base Info ("Informations de base") → "Vaccins" field | **Computed, read-only** (disabled text, e.g. `mOPV2,nOPV2` in the screenshot) — derived from the scopes via `Campaign.vaccines`. **Never selected, never edited there.** | — |
| Scope tab map legend ("Vaccin") | **The only vaccine selection** (picker state `selectedVaccine` in `ScopeInput.tsx`) | `polioVaccines` (`constants/virus.ts`) |
| VRF create/edit → "Vaccine" dropdown (`SupplyChain/Details/VaccineRequestForm/VaccineRequestForm.tsx`) | Specifies **which vaccine an existing supply-chain entry (VRF) is for**; options are computed from the selected campaign's own vaccines | `useCampaignDropDowns` → campaign `single_vaccines` |
| Supply Chain list filter "vaccine_type" | **Filter** on existing VRFs | `vrfVaccineFilterOptions` |
| Create Vaccine Stock modal | Specifies **which vaccine a new country stock profile is for** | `singleVaccinesList` |
| Stock Management list filter | **Filter** on existing stock profiles | `singleVaccinesList` |
| Public stock page filter | **Filter** | `singleVaccinesList` |
| Repository (forms / reports) filters | **Filter** (backend `vaccine_name`) | `singleVaccinesList` |
| National Logistics Plan create/edit (CountryPlan) | Specifies **which vaccine a country plan is for** | `vaccineOptions` = `defaultVaccineOptions` minus `mOPV2` (today includes the `nOPV2 & bOPV` combination) |
| PreAlert / VAR / Form A / destruction / incident / earmarked modals | No vaccine dropdown: the vaccine is **inherited from the stock profile or VRF** already opened; only "doses per vial" is chosen, with options depending on that vaccine | backend Config via `useGetDosesPerVial` |
| Calendar / maps / legends / campaign list | **Computed display** only (colours, labels) | `polioVaccines` (§8) |

So the PM requirement *"the Vaccines dropdown should only show the
options valid for that virus"* applies to the **Scope-tab vaccine
picker** (and only there, for selection). The virus itself is selected
in Base Info, so the filtering must react across tabs through the shared
Formik values. All other rows above are downstream consequences (§5.3
covers Supply Chain/Stock; this section covers the scope picker;
National Logistics Plan is PM question 6 in §11).

**This filtering is new.** Today the Scope picker always offers the same
four vaccines (`nOPV2`, `mOPV2`, `bOPV`, `nOPV2 & bOPV`) regardless of
the virus. After this change, the picker is restricted to
`VACCINES_BY_VIRUS[virus]` (§3).

**Existing data is left as-is.** Campaigns already saved with a
vaccine/virus pair that the matrix would no longer offer (e.g. mOPV2 on
a `cVDPV1 & cVDPV2` campaign, as in the screenshots) stay readable,
visible on the calendar/map, and saveable without touching their scopes.
The picker restriction and §5.1 validation apply only to **new
selections** (and to newly submitted invalid scopes). Opening an
existing campaign must not strip or rewrite its scopes. Calendar/map
must still render those legacy vaccines (existing colours stay; unknown
ones stay "Other").

Where the selection lives today:

- Virus dropdown: `js/src/domains/Campaigns/BaseInfo/BaseInfoForm.tsx`
  (~lines 249–257), options = `polioViruses` from
  `js/src/constants/virus.ts`.
- The "Vaccines" field next to it (~lines 259–269) is a **disabled text
  field** derived from the scopes (`helpTextEditVaccineViaScope`) — the
  actual vaccine selection happens in the scope UI.
- Vaccine selection UI: `Campaigns/Scope/Scopes/MapScope.tsx` +
  `ScopeMapLegend.tsx`, driven by `availableVaccines` (default
  `polioVaccines`), threaded through
  `ScopeField.tsx` → `ScopeInput.tsx` (which holds the local
  `selectedVaccine` state, default `'nOPV2'`). `SubActivityScopeField.tsx`
  has a commented-out `availableVaccines` restriction (~lines 43–55) that
  this work effectively supersedes.

Tasks:

- [ ] `js/src/constants/virus.ts`
  - [ ] Add `IPV`, `fIPV` and the 6 IPV/fIPV combinations to
        `polioVaccines` (values + labels needed for the scope dropdown).
        Colours/patterns for these entries are **not** decided here —
        they are specified in the calendar/map redesign phase (§8,
        with Christophe & Laura). Interim entries may use the
        `OTHER_VACCINE_COLOR` fallback, but must not ship as "Other" in
        the calendar (see §8).
  - [ ] Add the `VACCINES_BY_VIRUS` mapping (§3), keyed by **stored**
        virus values (`PV1`, `PV3`, `cVDPV2`, `WPV1`, `PV1 & cVDPV2`,
        `cVDPV1 & cVDPV2`), values = arrays of vaccine option values.
- [ ] `js/src/constants/types.ts` (lines 94–95): extend the `Vaccine`
      union with the 8 new values; add `'IPV'` **only** to
      `VaccineForStock` (no `fIPV`, no combinations — §5.3).
- [ ] **Refactor the Scope tab picker** so it can show every combination
      valid for the selected virus (the current inline map legend is too
      small for 5–11 options). Direction (confirmed):
  - [ ] A **drawer** with a **dynamic list** of vaccine types from
        `VACCINES_BY_VIRUS[values.virus]` (no `mOPV2` on new campaigns).
  - [ ] The map keeps **only the currently selected vaccine** (picker
        state `selectedVaccine`) so the map stays readable; the drawer
        is where the full list lives. Districts already assigned to
        other vaccines stay stored — they are just not the active
        colour/selection on the map until that vaccine is picked again.
  - [ ] Compute `availableVaccines` from the virus and pass it down
        `ScopeField` → `ScopeInput` → `MapScope` / legend (or the new
        drawer). Apply the same in `SubActivityScopeField` (replace the
        commented-out block). Campaign-level, round-level and
        sub-activity scopes all use the campaign's virus.
  - [ ] Labels use `&` (`IPV & bOPV`), matching stored values.
- [ ] **Clear-on-virus-change: out of this work.** Today, changing the
      virus does nothing to scopes (verified). That mismatch already
      exists and will be assessed in a **follow-up ticket**. This
      implementation only filters the picker for **new** selections;
      it must not delete or rewrite existing scopes when the virus
      changes or when an existing campaign is opened.
- [ ] Supply chain (`js/src/domains/VaccineModule/SupplyChain/`):
  - [ ] `constants.ts`: add `IPV` **only** to `singleVaccinesList` (no
        `fIPV` option anywhere in Supply Chain/Stock — §5.3). That list
        drives the Create Vaccine Stock modal, stock-management filters,
        the public stock page and repository filters — all gain IPV from
        this one change.
  - [ ] `constants.ts` `defaultVaccineOptions` (used for VRF vaccine
        filters): VRF types are individual only, so only `IPV` is added;
        check `vrfVaccineFilterOptions` / `fipvVaccineOptions` — the
        latter exists only for the fIPV-campaign workaround (Phase 4
        removes it) and must **not** be turned into a real fIPV VRF
        option.
  - [ ] `hooks/utils.ts` (~lines 15–19): the hardcoded `dosesPerVial`
        map (`nOPV2: 50, bOPV: 20, mOPV2: 20`) appears unused — the real
        source is the backend Config via `useGetDosesPerVial`
        (`Details/shared.tsx`), which already returns `[1, 5]` for IPV.
        Either delete the dead map or update it; do not treat it as a
        source of truth. There is no fIPV entry anywhere: fIPV is
        normalized to IPV **before** any doses lookup (§5.3), and IPV
        stock is managed at **5 doses per vial**.
  - [ ] `hooks/api/vrf.tsx`: fix token-based round filtering —
        `round.vaccine_names_extended.includes(vaccine)` is substring
        matching and `IPV` matches `fIPV`. Split on `,` / `&` and
        compare tokens.
- [ ] `NationalLogisticsPlan/hooks/options.ts` (~line 24): this dropdown
      **specifies which vaccine a country plan (CountryPlan) is for**
      (not a filter, not a scope) and today offers combinations
      (`defaultVaccineOptions` minus `mOPV2`, incl. `nOPV2 & bOPV`).
      Blocked on PM question 6 (§11): combinations or individual
      vaccines only? Then add IPV/fIPV entries accordingly and keep it
      in sync with the backend `CountryPlan.vaccine` choices (Phase 1).
- [ ] Stock-management bOPV special cases
      (`StockManagement/Table/useVaccineStockManagementTableColumns.tsx`
      ~line 58, `StockManagement/Details/VaccineStockManagementDetails.tsx`
      ~line 71, stock summary): IPV/fIPV follow the non-bOPV path
      automatically (unusable-vials tracking shown). Verify clinically.
- [ ] Translations: vaccine/virus names are literal codes; no new i18n
      keys expected. Check `js/src/constants/translations/{en,fr,es}.json`
      only if new labels are introduced.

---

## 7. Phase 4 — Migrate IPV/fIPV campaign types → vaccines

Goal: no campaign uses `IPV` or `fIPV` as a `CampaignType` anymore; the
vaccine lives on the campaign's scopes (the "Vaccines field"), and the
campaign's type is `Polio`.

### 7.1 Audit first (read-only, run in staging then production)

- [ ] List `CampaignType` rows named `IPV` / `fIPV` (check both `name`
      and `slug`: `ipv`, `fipv`, `fIPV`…).
- [ ] List campaigns having those types, with: `obr_name`, account,
      country, `separate_scopes_per_round`, current scope vaccines
      (campaign / round / sub-activity), whether `Polio` type is also
      present, existing VRFs (`vaccine_type` IPV — fIPV VRFs cannot exist
      yet), existing stocks.
- [ ] Classify each campaign:
  - **A** — has IPV/fIPV type, no vaccine scopes yet;
  - **B** — has IPV/fIPV type **and** existing scopes with another
        vaccine (e.g. `bOPV`): the target vaccine is the **combination**
        (`IPV & bOPV`) per §2, not a replacement;
  - **C** — has both `Polio` and IPV/fIPV types;
  - **D** — anything else (no org units in scopes, test campaigns…) →
        manual review list. Do not auto-migrate class D.

### 7.2 Data migration (Django migration or one-off script — decide in PR)

For each migrated campaign, idempotently:

- [ ] Add the `Polio` `CampaignType`; remove the `IPV`/`fIPV`
      `CampaignType` from the campaign (do **not** delete the
      `CampaignType` rows until the audit shows zero campaigns use them;
      delete/retire them in a follow-up).
- [ ] Record the vaccine on scopes:
  - Class A, `separate_scopes_per_round = False`: create/update the
    campaign scope with vaccine `IPV` (resp. `fIPV`), reusing the
    campaign's existing scope group/org units if a scope exists,
    otherwise the campaign's org-unit group. Remember: derived vaccine
    lists ignore scopes whose group has no org units
    (`group__org_units__isnull=False` filters), so a scope without org
    units will **not** show up in the Vaccines field.
  - Class A, per-round scopes: apply the same on **every round** scope.
  - Class B: rewrite the existing scope vaccine to the combination
    (`bOPV` → `IPV & bOPV`, `nOPV2` → `IPV & nOPV2`, …) per §2; if a scope
    with the target combination already exists, merge org units into it
    and delete the old scope (respect `unique_together (round, vaccine)`
    / `(campaign, vaccine)`).
  - Sub-activity scopes: apply the same rule as their parent round.
- [ ] Call `campaign.update_geojson_field()` + `campaign.save()` per
      migrated campaign so map geojson carries the new vaccine.
- [ ] Log every migrated campaign (id, obr_name, old types, old/new scope
      vaccines) — migration must be re-runnable (idempotent) and the log
      is the rollback reference.
- [ ] After migration, verify per campaign: API detail shows the vaccine
      in `vaccines` / `single_vaccines`, calendar shows it, a VRF can be
      created for IPV/fIPV, stock (if any) still computes.

> ⚠️ `Campaign.has_polio_type` gates chronogram creation
> (`Round.add_chronogram`) and preparedness flows. Migrated campaigns gain
> `Polio` behaviour for **new** rounds after migration — expected, but
> flag it in the release notes.

### 7.3 Remove the workaround (after 7.2 is confirmed in production)

- [ ] Backend: remove `"fIPV"` from `PolioCampaignManager`
      (`models/base.py`, ~line 645) and delete the "ugly patch" comment.
      Check whether an `"IPV"` type was ever added to any similar filter.
- [ ] Frontend `SupplyChain/hooks/api/vrf.tsx` (~lines 173–246): remove
      the second `campaignType: 'fIPV'` fetch, `isFipvCampaign` and
      `fipvVaccineOptions`. Migrated campaigns are normal Polio campaigns;
      their `single_vaccines` already drives the VRF vaccine dropdown
      (and now yields `IPV`/`fIPV` tokens via the generic splitter).
- [ ] Retire the now-unused `IPV`/`fIPV` `CampaignType` rows (admin or
      follow-up migration) once audit = 0 campaigns.

---

## 8. Phase 5 — Campaign calendar & map redesign (PM step 4 — last step)

> PM: *With IPV and fIPV added as vaccine types, the campaign calendar and
> map need to display the 8 new vaccine options: IPV, fIPV, IPV + bOPV,
> fIPV + bOPV, IPV + nOPV2, fIPV + nOPV2, IPV + nOPV2 + bOPV and
> fIPV + nOPV2 + bOPV. Today these would fall under "Other", so users
> can't tell which vaccine a campaign uses — this needs to be visualized.
> Each round on the calendar and each region on the map should show its
> vaccine combination clearly, and the legend should be updated to include
> IPV and fIPV. The existing colours for nOPV2, mOPV2, bOPV and
> nOPV2 + bOPV should stay the same so users keep the colours they
> already know.*
>
> ⚠️ **Colours and calendar/map legend UX are deferred.** Define colours
> later; likely use a **drawer** to list possible vaccines (same idea as
> the Scope-tab drawer, §6). Do not invent colours/patterns in code
> before that spec exists. Existing colours for nOPV2, mOPV2, bOPV and
> nOPV2 & bOPV stay. The tasks below separate plumbing from visual
> encoding.

### 8.1 What exists today (plumbing — no redesign needed)

- Vaccine → colour mapping is centralized in
  `js/src/constants/virus.ts` (`polioVaccines`, `PolioVaccine`
  type with `value / label / color / legendColor`):

  | Value | Colour today | Must stay? |
  | --- | --- | --- |
  | `nOPV2` | `#00b0f0` (blue) | ✅ unchanged |
  | `mOPV2` | `#66ff66` (green) | ✅ unchanged |
  | `bOPV` | `#ffff00` (yellow) | ✅ unchanged |
  | `nOPV2 & bOPV` | striped blue/yellow (`url(#colorStripes-nOPV2&bOPV)` + `repeating-linear-gradient` legend) | ✅ unchanged |
  | anything else | `OTHER_VACCINE_COLOR = #ea8418` (orange), legend label "Other" | ❌ this is where all 8 new values land today |

- Consumers of that mapping (all get the new values automatically once
  `polioVaccines` knows them — no per-component vaccine lists to update):
  - **Calendar cells:** `Calendar/campaignCalendar/cells/RoundCell.tsx`
    (`getCellColor`: `polioVaccines.find(...)`, falls back to "Other");
    each round cell is split into one horizontal band per vaccine string
    in `round.vaccine_names` / `campaign.vaccines`.
  - **Calendar map:** `Calendar/campaignCalendar/map/CalendarMapPanesMerged.tsx`
    + `map/utils.ts` (shape fill per scope vaccine), legend in
    `map/VaccinesLegend.tsx` (`useMapLegend` = `polioVaccines` + "Other").
  - **Scope map (campaign form):** `Campaigns/Scope/Scopes/MapScope.tsx`
    + `ScopeMapLegend.tsx` (also the vaccine picker — Phase 3 filtering
    reuses the same list).
  - **Hashed patterns:** only **one** combination pattern exists today
    (`HASHED_MAP_PATTERN_N_OPV2_B_OPV`, SVG `ColorsHashedPattern` mounted
    in `MapScope.tsx` and `CalendarMapContainer.tsx`). Every new
    combination that the spec encodes as stripes needs its own pattern
    id + mounted SVG definition in both places, or patterns must be
    generated from the component colours.
  - **Backend XLSX calendar export:** `plugins/polio/export_utils.py`
    (`polio_vaccines()` colour dict, ~line 164) — same 4 values, `None`
    otherwise. Must stay in sync with the frontend mapping.
  - **LQAS/IM maps** use their own in-scope/out-of-scope colouring
    (`domains/LQAS-IM/...`, grey hashed pattern) — verify with the spec
    whether vaccine display is in scope there; by default **out**.

### 8.2 To define later (colours + calendar/map drawer)

- [ ] Colours for `IPV` and `fIPV`, and encoding for the 6 combinations
      (stripes vs solid). Existing nOPV2 / mOPV2 / bOPV /
      `nOPV2 & bOPV` colours stay. Combinations are labelled with `&`.
- [ ] Calendar/map legend UX: likely a **drawer** listing possible
      vaccines (the inline legend will not fit 8+ options), same
      direction as the Scope-tab drawer (§6). "Other" remains for
      genuinely unknown/legacy values only.
- [ ] Calendar round cell and map fills still need those colours once
      agreed; XLSX export only supports solid fills — define a fallback
      per combination then.
- [ ] fIPV vs IPV stay distinct on the calendar (no `fIPV → IPV`
      normalization here).

### 8.3 Implementation (after spec is signed off)

- [ ] `js/src/constants/virus.ts`: add the 8 entries to `polioVaccines`
      with the agreed `color` / `legendColor`; add pattern id constants
      for each striped combination (following
      `HASHED_MAP_PATTERN_N_OPV2_B_OPV` naming).
- [ ] Mount the new SVG patterns everywhere
      `ScopeHashedPattern` / pattern lists are mounted
      (`MapScope.tsx`, `Calendar/campaignCalendar/map/CalendarMapContainer.tsx`),
      or refactor pattern generation so a combination's pattern is built
      from its components' colours (preferred if the spec picks stripes:
      adding a future combination then needs **no** new SVG plumbing).
- [ ] `plugins/polio/export_utils.py`: add the 8 values with the agreed
      solid-fill fallbacks so XLSX calendar exports match the UI.
- [ ] Verify all consumers from §8.1 render the new values (calendar
      cells, calendar map + legend, scope map + legend/picker); no
      component should keep a private vaccine list.
- [ ] Frontend tests: colour/pattern lookup for all 12 values returns a
      non-"Other" result (`RoundCell`, legend, map utils); legend
      contains IPV and fIPV labels; legacy unknown vaccine still renders
      as "Other".
- [ ] Visual check (desktop calendar + map, one campaign per new
      combination incl. a triple) against the signed-off spec, incl.
      longer FR labels in the legend (i18n space rule).

---

## 9. Phase 6 — Tests

### Backend

- [ ] `tests/models/test_campaign_models.py`: add campaigns with `IPV`,
      `fIPV`, `IPV & bOPV`, `IPV & nOPV2 & bOPV`; assert
      `single_vaccines_extended_list` / `single_vaccines_full_list` split
      correctly, and that `IPV` splitting never yields `fIPV` (and vice
      versa). Keep existing positional `VACCINES[0..3]` usage valid.
- [ ] `tests/models/test_round_models.py`: IPV/fIPV (combined) round
      scopes; assert `single_vaccine_list`, `vaccine_names`,
      `single_vaccine_names_extended`.
- [ ] `tests/models/test_vaccine_stock_models.py`: create an `IPV`
      `VaccineStock`; IPV arrivals counted by `VaccineStockCalculator`;
      assert `fIPV` is **rejected** as a stock vaccine (choices =
      `INDIVIDUAL_VACCINES`) and that normalization maps `fIPV → IPV`
      while raw splitting keeps `IPV` ≠ `fIPV` tokens distinct.
- [ ] Campaign serializer validation: parametrized over §3 matrix —
      valid (virus, vaccine) accepted; invalid rejected (e.g. `cVDPV2` +
      `IPV & bOPV`; `PV1` + `nOPV2`); legacy-invalid campaign still
      saveable without scope changes (per §5.1 decision).
- [ ] Campaign create/update API tests
      (`tests/api/campaigns/create/`, `tests/api/campaigns/update/`):
      IPV/fIPV-combined campaign-level and round-level scopes; assert
      response `vaccines` / `single_vaccines` and geojson `vaccine`.
- [ ] `tests/test_vaccine_stock_archive_task.py`: combined IPV scope
      round gets stock history archived per individual vaccine; an
      `fIPV & bOPV` round archives against the **IPV** and **bOPV**
      stocks (separate balances, §5.3).
- [ ] Supply chain (`tests/api/vaccine_supply_chain/test_vaccine_supply_chain.py`):
      extend `test_user_can_post_request_form_with_ipv_vaccine_type` to a
      campaign whose scope actually contains IPV; add: fIPV-scoped
      campaign creates an **IPV** VRF (and `fIPV` as `vaccine_type` is
      rejected); `IPV & nOPV2` campaign creates separate IPV and nOPV2
      VRFs.
- [ ] Stock management API: create an IPV country profile; record Form A,
      destruction report, incident report and earmarked stock on it
      (same flows/permissions as nOPV2); doses-per-vial offers **5**;
      balances for IPV and the oral vaccine of a combined campaign are
      computed separately; Config without extra keys does not break
      `get_usable_stock_by_vaccine_presentation` (no `KeyError`, no
      `fIPV` key needed).
- [ ] Migration test (if Django data migration): class A/B/C campaigns
      migrated to expected types + scope vaccines; re-run is a no-op.

### Frontend

- [ ] Unit test for `VACCINES_BY_VIRUS`: each virus yields exactly the §3
      list (keyed by stored values, not labels).
- [ ] Campaign form: selecting a virus filters the Scope-tab vaccine
      list (drawer); `mOPV2` is not offered on new campaigns; opening an
      existing mOPV2 campaign still shows its scopes. Changing the virus
      must **not** delete persisted scopes (follow-up ticket, §11).
- [ ] `polioVaccines` color lookup: all 12 values resolve to a color /
      pattern (no orange `OTHER_VACCINE_COLOR` fallback) for scope map,
      calendar cells, calendar map and legend (§8); legend contains IPV
      and fIPV; a legacy unknown vaccine still renders "Other".
- [ ] VRF round filtering: token matching only — note the two different
      semantics: scope/calendar display keeps `IPV` ≠ `fIPV`, while
      supply-chain matching (§5.3) deliberately maps `fIPV → IPV`. Test
      both so neither leaks into the other.

---

## 10. Phase 7 — Rollout

- [ ] 1. Deploy backend (Phases 1–2) + schema migration.
- [ ] 2. Verify the `vaccine_doses_per_vial` Config in **each**
         environment (staging, production) matches the confirmed content
         (`IPV: [1, 5]`, `bOPV: [10, 20]`, `mOPV2: [50]`,
         `nOPV2: [20, 50]` — **no `fIPV` key**, §5.3) via Django Admin —
         otherwise stock-by-presentation returns nothing for IPV stocks.
- [ ] 3. Deploy frontend (Phase 3), then the calendar/map redesign
         (Phase 5) once its spec (§8.2) is signed off — it can ship
         after Phases 1–4 without blocking them, but not before the
         design agreement.
- [ ] 4. Run the Phase 4 audit → data migration (staging first, verify
         the §7.2 checklist per campaign, then production).
- [ ] 5. Remove the fIPV workaround code (§7.3) in a follow-up PR once
         production audit shows 0 IPV/fIPV-typed campaigns.
- [ ] 6. Monitor the `archive_vaccine_stock` task for IPV/fIPV rounds.
- [ ] 7. Notify PowerBI / dashboard owners: new values (`IPV`, `fIPV`,
         combinations) will appear in `vaccines` / `vaccine_names`
         fields. **Format unchanged** (`"A & B"`, `", "`-joined lists).
- [ ] 8. Cypress: tag `@cypress` in the PR comment for campaign-form and
         supply-chain E2E coverage.

---

## 11. Risks, open questions & notes

- **PM answers (2026-11-06):**

  **Confirmed:**
  - IPV vials: 1-dose and 5-dose presentations. Other vaccines: bOPV 10
    or 20, mOPV2 50, nOPV2 20 or 50.
  - fIPV has no stock of its own: fIPV campaigns use IPV vials; all
    IPV/fIPV stock is counted as IPV at 5 doses per vial.
  - **PV2:** leave as is. No new mapping, no cleanup.
  - **mOPV2:** removed from **new** campaigns; existing mOPV2 data stays.
  - **Combination labels:** use `&` everywhere (`IPV & bOPV`), same as
    today's `nOPV2 & bOPV`.
  - **Preparedness:** keep the current spreadsheet and scoring for now
    (including "vaccines and droppers received" for IPV/fIPV).
  - **nOPV2 vaccine authorizations:** keep as is. IPV/fIPV-only rounds
    skip it; rounds that also use nOPV2 still go through it.
  - **Scope tab UX:** refactor so the picker can show every combination
    valid for the selected virus. Use a **drawer** with a dynamic
    vaccine list; keep only the currently selected vaccine on the map.

  **Deferred (not this work):**
  1. **Calendar and map colours:** define later. Existing colours for
     nOPV2, mOPV2, bOPV and nOPV2 & bOPV stay. Calendar/map legend will
     likely also use a drawer to list possible vaccines (§8).
  4. **Changing the virus after districts are already selected:** the
     mismatch already exists today. Assess in a **follow-up ticket**;
     do not delete or rewrite scopes in this work.
  6. **Country planning pages:** still open — combinations or individual
     vaccines only? (National Logistics Plan / `CountryPlan.vaccine`.)
- **Biggest silent-failure risk** is not the choices list — it is
  substring/exact-match vaccine lookups (stock archiving, calculator,
  VRF round filter). `IPV` ⊂ `fIPV` makes substring checks actively
  wrong, not just incomplete. Everything must compare **tokens**.
- **Backward compatibility:** all existing stored strings remain valid;
  new entries are appended, existing indexes/values untouched. The only
  behavioural change for existing campaigns is the generic splitter,
  which returns identical results for the 4 legacy values (lock with a
  test).
- **Permissions:** no new permissions; vaccine types are not
  permission-gated. Existing `HasPermission` classes on stock /
  supply-chain endpoints unchanged.
- **PR hygiene** (per repo rules): branch name = JIRA issue key, fill the
  PR template, add reviewers, CI (JS + Python) green, squash & merge with
  a conventional commit. Suggested split: (1) backend core + validation,
  (2) frontend virus filtering, (3) Supply Chain & Stock Management
  (IPV-only, §5.3), (4) data migration + fIPV workaround removal,
  (5) calendar/map redesign after colours/drawer spec (§8).

## 12. Out of scope (unless requested)

- Normalizing scope vaccines to a M2M / separate model (breaking change).
- IPV/fIPV-specific vaccine authorization workflow (like nOPV2's) —
  keep current nOPV2 authorization behaviour.
- New preparedness spreadsheet template for injectable vaccines —
  keep current template/scoring.
- Changing the virus after districts are selected (clearing/deleting
  invalid scopes) — follow-up ticket; the problem already exists today.
- Calendar/map colours and calendar legend drawer — define later (§8).
- PV2 virus cleanup or mapping.
- Deleting the `IPV`/`fIPV` `CampaignType` rows in the same PR as the
  data migration (follow-up, after production audit = 0).
