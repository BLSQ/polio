# Polio plugin extraction

Target: the same plugin model as SNT Malaria. No Module Federation remote, no published frontend SDK, no rewrite of Polio imports.

Polio stays a Django app plus a React tree. IASO loads it because the folder is on disk under `plugins/` when the image is built.

## How SNT works (the contract to copy)

SNT is its own git repo, gitignored in IASO, cloned into `plugins/snt_malaria`.

Local setup from the SNT README:

```bash
cd plugins
git clone git@github.com:BLSQ/snt-malaria.git snt_malaria
```

`.env` in the IASO repo:

```
PLUGINS=snt_malaria
```

What the host does with that folder:

- Backend: `hat/settings.py` imports `plugins.<name>.plugin_settings` and extends `INSTALLED_APPS`, `CONSTANTS`, template/static dirs, throttle rates. SNT ships `plugins/snt_malaria/plugin_settings.py`.
- API: `plugins/router.py` merges `plugins.<name>.api.router`.
- Extra pages: `hat/urls.py` includes `plugins.<name>.urls` at `/<name>/`. SNT uses this for the metrics import page and the public setup SPA.
- Frontend: `hat/assets/js/apps/Iaso/bundle/plugins.js` scans `plugins/*/js/config.tsx` at webpack build time and bundles those React files into the IASO app. Runtime only shows plugins listed in `PLUGINS`.
- SNT `js/config.tsx` exports the `Plugin` object: `routes`, `menu`, `translations`, `baseUrls`, `paramsConfig`, `homeUrl`, `theme`.
- SNT React imports host code with `Iaso/...` (about 200 files). That alias exists only because webpack compiles the plugin inside the IASO tree. That is expected. Do not try to remove it.
- Permissions live in `plugins/snt_malaria/permissions.py`. The host discovers them. The module constant `MODULE_SNT_MALARIA` still sits in `iaso/modules.py`.
- Cron for SNT lives in the plugin repo (`plugins/snt_malaria/cron.yaml`), not in IASO `cron.yaml`.
- One conditional backend import remains in core (`iaso/api/metrics/views.py` imports SNT only when the plugin is active). That does not prevent the split.

Polio after the split should match this. A Polio deploy clones the repo into `plugins/polio` before `manage.py` and `webpack-prod`. A vanilla IASO build does not need the folder.

## What Polio already matches

- `plugins/polio/js/config.tsx` already exports `routes`, `menu`, `translations`, `baseUrls`, `paramsConfig`, `redirections`, `homeUrl`, `customComponents`. Routes and menu are not hardcoded in the main app.
- API router is `plugins.polio.api` and is merged by `plugins/router.py`.
- Permissions are plugin-owned (`plugins/polio/permissions.py`) and discovered by `iaso/permissions/base.py`.
- Migrations live in `plugins/polio/migrations/` (app label `polio`). No Polio tables are created in `iaso` migrations.
- No foreign key from a core model to a Polio model.

Keep the Python import path `plugins.polio` and the app label `polio`. Content types (`polio.campaign`) and permission rows depend on them.

## Blockers

These are the differences that stop a SNT-style split. SNT does not have them.

### 1. Done — The host webpack build imported Polio source

`PlanningForm` renders `OrgUnitTreeviewModal` directly. It does not import `plugins/polio`. The integration test mocks the host modal. Polio screens keep their own `OrgUnitsSelect`.

### 2. Polio repo split

`.gitignore` ignores `plugins/polio`. The history lives in `github.com/BLSQ/polio`, cloned as `plugins/polio`. The plugin README has the clone steps. Still open: CI (phase 3 steps 4–5).

### 3. Done — `plugin_settings.py`

`plugins/polio/plugin_settings.py` sets `INSTALLED_APPS`, `TEMPLATES_DIRS`, and `AUTHENTICATION_CLASSES` (BasicAuth for PowerBI). `hat/settings.py` appends `AUTHENTICATION_CLASSES` after the plugin loop. The `"polio" in PLUGINS` check is gone.

### 4. Core tests import Polio at import time

- `iaso/tests/utils/test_clamav.py` imports `plugins.polio.models.NotificationImport`.
- `iaso/tests/api/test_tasks.py` builds the Polio notification task.

IASO CI without the clone fails. SNT tests that need the plugin are skipped with `@skipUnless(is_snt_malaria_plugin_active(), ...)`.

Fix: move Polio-only tests into `plugins/polio/tests`, or skip them the same way when the plugin is not installed.

## Polio behavior that still lives in core

These do not stop webpack or Django from starting. They mean a non-Polio IASO image still contains Polio product behavior. Move them with the split, the same way SNT keeps its cron and extra URLs in the plugin repo.

| Location | What to do |
|---|---|
| `iaso/api/logs.py` | Done. `plugin_log_access` asks each plugin's `has_log_access`. Polio answers for `Campaign`. |
| `iaso/api/org_units.py` | Done. `extra_org_unit_permissions` collects `org_unit_extra_permissions` from plugin settings. Polio contributes `POLIO_PERMISSION`. |
| `iaso/modules.py` | `MODULE_POLIO_PROJECT`. SNT’s module constant lives here too. Leave it. |
| `hat/assets/js/apps/Iaso/utils/permissions.ts` | Done. Polio codenames are gone. Plugin screens import `plugins/polio/js/src/constants/permissions.ts`. |
| `hat/.../users/permissionsMessages.ts` and `en.json` / `fr.json` | Done. Polio labels live in the plugin `permissionsMessages.ts`. The matching strings moved from the host `en.json`, `fr.json`, and `es.json` into `plugins/polio/js/src/constants/translations/`. Screens still import the host message constant, so they do not show plugin labels until they call `usePermissionsMessages`. |
| Tasks UI | Done. `ActionCell` renders every `tasks.rowAction` custom component. Polio registers `PolioNotificationTaskAction`. `GET /api/polio/notifications/for_task/<task_id>/` reads the import pk from `Task.params.kwargs`. `TaskSerializer` no longer has `polio_notification_import_id`. |
| `GroupsDialog.tsx` | Done. The dialog renders every `groups.dialogField` custom component. Polio registers `BlockOfCountriesField`, gated on `POLIO` / `POLIO_ADMIN`. `Group.block_of_countries` stays a core column and is still saved by the dialog. |
| `hat/dashboard/urls.py` | Done. The five embed routes are in `plugins/polio/urls.py` and call `embeddable_iaso`, so the pages stay public. The host includes that file. `hat/dashboard/urls.py` no longer lists them. |
| `hat/settings.py` WHO SSO | Done. Paths stay `polio/login/`, `polio/login/callback`, `polio/token/`. The WHO Entra app registration cannot be changed, so these redirect URIs stay as they are. |
| PowerBI refresh snippet | Done. Lives at `plugins/polio/templates/iaso/pages/refresh_data_set_snippet.html`. Core pages include it with `include_optional`, so a deploy without Polio still renders. |
| `cron.yaml` | Done. The three Polio jobs are in `plugins/polio/cron.yaml`. The root file keeps only core jobs. CI merges plugin `cron.yaml` files into the file the worker deploys. |
| `beanstalk_worker/views.py` | Done. The Polio skip is removed. Plugin cron jobs are only scheduled on a deploy that installs that plugin. |
| `iaso/plugins.py` | Done. `is_polio_plugin_active()` stays, same shape as `is_snt_malaria_plugin_active()`. |

## Out of scope

- Module Federation remotes, a separate webpack build for Polio, or an npm package for the React app.
- Rewriting the `Iaso/...` and relative `hat/...` imports inside `plugins/polio/js`. SNT does the same.
- Renaming the Django app, moving tables, or rewriting migrations.
- A plugin-owned module registry. SNT does not have one.
- Extracting LQAS sampling out of Planning.

## Phases

### Phase 1 — Done — IASO builds with the Polio folder absent

1. Done: `PlanningForm` renders `OrgUnitTreeviewModal` and no longer imports `plugins/polio`. The integration test mocks the host modal instead of the Polio select.
2. Done: accepted as-is for this phase. `iaso/tests/utils/test_clamav.py` still imports `NotificationImport`. That test runs when the plugin is cloned. Moving or skipping it stays optional (phase 4 / CI without the clone). The Polio field on `TaskSerializer` is removed in phase 2 step 5.
3. Done: no remaining host import of `plugins/polio` in the webpack graph. Django boots without Polio when `PLUGINS` does not list it.

### Phase 2 — Match the SNT plugin files

1. Done: `plugin_settings.py` sets `INSTALLED_APPS`, `TEMPLATES_DIRS`, and `AUTHENTICATION_CLASSES` (BasicAuth).
2. Done: `hat/settings.py` appends `AUTHENTICATION_CLASSES` after the plugin loop. The `"polio" in PLUGINS` BasicAuth check is gone.
3. Done: the refresh snippet is `plugins/polio/templates/iaso/pages/refresh_data_set_snippet.html`. `powerbi.html`, `superset.html`, and `iframe.html` include it with `include_optional`.
4. Done: `plugins/polio/cron.yaml` holds the three Polio jobs. Root `cron.yaml` does not. CI merges plugin `cron.yaml` files into the deployed worker cron. No predeploy hook.
5. Done: the notification-import button lives in the plugin as `tasks.rowAction`. `TaskSerializer` no longer exposes `polio_notification_import_id`. The plugin loads the import from the task id.
6. Done: plugin screens import `plugins/polio/js/src/constants/permissions.ts`. Polio constants are removed from `hat/.../utils/permissions.ts`. The block-of-countries checkbox is the plugin component `groups.dialogField`.
7. Leave `MODULE_POLIO_PROJECT` in `iaso/modules.py`.

Embed routes live in `plugins/polio/urls.py` and stay public through `embeddable_iaso`. WHO SSO paths stay `polio/login/`, `polio/login/callback`, and `polio/token/`.

### Phase 3 — Split the git repo

1. Done: `github.com/BLSQ/polio` holds the plugin history. Cloned into `plugins/polio`, package path stays `plugins.polio`.
2. Done: `.gitignore` ignores `plugins/polio`.
3. Done: `plugins/polio/README.md` starts with the SNT-style setup: clone IASO, clone this repo into `plugins/polio`, set `PLUGINS=polio`, then `docker compose up`.
4. IASO CI: do not clone Polio for the default pipeline. Polio CI: clone IASO, clone this repo into `plugins/polio`, set `PLUGINS=polio`, run Polio pytest and the frontend checks.
5. Docker: `COPY plugins/` already picks up whatever was cloned before the image build. The Polio image build clones the repo first. Document the pin (tag or SHA) the way other external plugins are pinned.

### Phase 4 — Optional cleanup

Only after the repo split is in use:

- Done: `logs.py` and `org_units.py` call `plugin_log_access` and `extra_org_unit_permissions`. Polio implements both in `plugin_settings.py`.
- Done: the Polio skip in `task_launcher` is removed. A plugin cron file is only merged on a deploy that installs that plugin.
- Done: `is_polio_plugin_active()` stays as its own helper, like the SNT one.
- Done: WHO login paths stay `polio/login/`, `polio/login/callback`, and `polio/token/`. The Entra redirect URIs cannot be updated.

## Dev workflow after the split

```bash
cd plugins
git clone git@github.com:BLSQ/polio.git polio
```

IASO `.env`:

```
PLUGINS=polio
```

`docker compose up` mounts `./plugins` into the container, same as today. Webpack scans `plugins/polio/js/config.tsx` and bundles it. No second dev server.

## Risks

- Embed pages are public via `plugins/polio/urls.py` (`embeddable_iaso`). WHO SSO paths (`/polio/login/`) stay. The Entra app registration cannot be changed.
- Migration history assumes app label `polio` and dependency on the IASO squash. The plugin repo must keep that graph. Deployments run plugin migrations because the app is in `INSTALLED_APPS`.
- `Group.block_of_countries` and `iaso.models.json_config.Config` stay in IASO. Polio keeps using them.
- Core `iaso` migrations that mention `POLIO_PROJECT` in `Account.modules` choices stay in IASO. They are historical. The constant remains in `iaso/modules.py`.
- Polio frontend has no `package.json`. Dependencies (`formik`, `react-query`, `recharts`, maps) stay on the IASO root `package.json`, which is how SNT works too.
