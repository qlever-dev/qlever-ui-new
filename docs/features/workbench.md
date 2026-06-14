# Workbench

Everything around the editor: tabs, sharing, settings, shortcuts, and the
command prompt.

## Tabs

Work on several queries at once — each tab holds its own query and is tied
to a SPARQL endpoint. Tabs are restored when you come back.

## Sharing queries

Click the share button to turn the current query into a short link. The
query is stored server-side and addressed by a 6-character ID, so links stay
short no matter how large the query is. Opening a shared link loads the
query into a new tab.

Shared queries are deduplicated, capped at 100 KB, and persisted in a SQLite
database on the server (see
[Persisting shared queries](../setup/docker.md#persisting-shared-queries)).

## Endpoint selector

Switch between the configured
[SPARQL endpoints](../configuration/endpoints.md) at any time. The order of
the list is controlled by each endpoint's `sort_key`, and the endpoint
marked `default: true` is pre-selected on first visit.

## Settings

Open the settings panel with `Ctrl+,`. It groups everything tunable about
the [editor](editor.md) (formatting, completion, prefix handling) and the
[results view](results.md) (annotations, IRI shortening, images, page size).
Settings are stored in your browser's local storage and applied immediately.
See [Settings](../configuration/settings.md) for a reference of every option.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `?` | Open help |
| `Escape` | Close any dialog |
| `Ctrl+Enter` | Execute / cancel query |
| `Ctrl+F` | Format document |
| `Ctrl+,` | Open settings |
| `Ctrl+P` | Open the command palette |
| `Tab` | Jump to next position |
| `Shift+Tab` | Jump to previous position |

## Command palette

Open the command palette with `Ctrl+P` and type a command:

| Command | Action |
|---------|--------|
| `execute` | Run the current query |
| `format` | Format the editor content |
| `examples` | Browse query examples |
| `createExample "<name>"` | Save the current query as a new example for the active endpoint |
| `updateExample` | Update the currently loaded example |
| `parseTree` | Show the [SPARQL parse tree](analysis.md#parse-tree-view) |
| `analysis` | Show the [query execution tree](analysis.md#query-execution-tree-view) |
| `templates` | Open the [completion template editor](analysis.md#completion-template-editor) *(experimental)* |
| `clearCache` | Clear the language server cache |
| `toggleWideMode` | Toggle the wide editor layout |
| `version` | Show the build version |

The commands `createExample` and `updateExample` write to the server and
require an [API key](../setup/docker.md#enabling-writes-with-an-api-key).
