# Settings

Open the settings panel with `Ctrl+,` (or the **Settings** button in the
top bar). Every option is applied immediately and stored in your browser's
local storage, so your configuration survives reloads and is scoped to the
machine you're using.

The panel is organized into three sections — **General**, **Editor**, and
**Results** — which this page documents option by option. Editor settings are
forwarded to the [Qlue-ls](https://github.com/IoannisNezis/Qlue-ls) language
server; results settings affect how the [results view](../features/results.md) renders.

!!! tip "Formatting examples"
    Formatting options take effect when you format the document with `Ctrl+F`.
    The before/after blocks below show the *same query formatted with the
    option off versus on* — everything else left at its default.

## General

### Access Token

A token sent with query execution and write operations. It authorizes
write actions such as saving examples
(`createExample` / `updateExample` in the [command palette](../features/workbench.md#command-palette))
against a backend that has an
[API key configured](../setup/docker.md#enabling-writes-with-an-api-key).
Leave it empty if you only run read queries.

## Editor — Formatting

These options control the formatter (`Ctrl+F`).

### Align prefixes

*Default: off.* Pads `PREFIX` names so the IRIs line up in a column.

=== "Off"
    ```sparql
    PREFIX namespace123: <iri>
    PREFIX namespace12: <iri>
    PREFIX namespace1: <iri>
    ```
=== "On"
    ```sparql
    PREFIX namespace123: <iri>
    PREFIX namespace12:  <iri>
    PREFIX namespace1:   <iri>
    ```

### Align predicates

*Default: on.* When a subject has several predicates (see
[Contract triples](#contract-triples)), vertically align them under each
other. With it off, continuation predicates get a fixed single indent.

=== "On"
    ```sparql
    ?person <http://name> "John" ;
            <http://age> 30 .
    ```
=== "Off"
    ```sparql
    ?person <http://name> "John" ;
      <http://age> 30 .
    ```

### Separate Prologue

*Default: off.* Inserts a blank line between the prologue (the `PREFIX` /
`BASE` declarations) and the query body.

=== "Off"
    ```sparql
    PREFIX namespace: <iri>
    SELECT * WHERE {}
    ```
=== "On"
    ```sparql
    PREFIX namespace: <iri>

    SELECT * WHERE {}
    ```

### Capitalize keywords

*Default: on.* Uppercases SPARQL keywords regardless of how you typed them.

=== "Off (as typed)"
    ```sparql
    prefix namespace: <iri>
    select * where {}
    ```
=== "On"
    ```sparql
    PREFIX namespace: <iri>
    SELECT * WHERE {}
    ```

### Line break after WHERE

*Default: off.* Puts `WHERE` (and the preceding clause) on its own line
instead of keeping it next to the projection.

=== "Off"
    ```sparql
    SELECT * WHERE {
      ?a ?b ?c
    }
    ```
=== "On"
    ```sparql
    SELECT *
    WHERE {
      ?a ?b ?c
    }
    ```

### Trailing Filter

*Default: on.* Keeps a `FILTER` on the same line as the triple it follows.
With it off, the `FILTER` is moved to its own line.

=== "On"
    ```sparql
    SELECT * WHERE {
      ?a ?b ?c FILTER (?a)
    }
    ```
=== "Off"
    ```sparql
    SELECT * WHERE {
      ?a ?b ?c
      FILTER (?a)
    }
    ```

### Insert spaces

*Default: on.* Indent with spaces. Turn it off to indent with tab
characters instead. The width is controlled by [Tab size](#tab-size).

### Contract triples

*Default: off.* Merges consecutive triples that share a subject into one
statement using `;` notation (predicates are aligned per
[Align predicates](#align-predicates)).

=== "Off"
    ```sparql
    SELECT * WHERE {
      ?person <http://name> "John" .
      ?person <http://age> 30 .
    }
    ```
=== "On"
    ```sparql
    SELECT * WHERE {
      ?person <http://name> "John" ;
              <http://age> 30 .
    }
    ```

### Keep empty lines

*Default: off.* Preserves intentional blank lines from your source
(consecutive blanks are collapsed to a single one). With it off, all blank
lines inside the query are removed.

=== "Off"
    ```sparql
    SELECT ?name WHERE {
      ?person foaf:name ?name .
      ?person foaf:age ?age .
    }
    ```
=== "On"
    ```sparql
    SELECT ?name WHERE {
      ?person foaf:name ?name .

      ?person foaf:age ?age .
    }
    ```

### Tab size

*Default: 2.* Number of spaces per indentation level (or the displayed
width of a tab when [Insert spaces](#insert-spaces) is off).

### Compact

*Default: off (empty).* When set to a column number, the formatter collapses
nested blocks onto a single line as long as they fit within that many
columns. Leave it empty to always expand blocks.

=== "Off (empty)"
    ```sparql
    SELECT * WHERE {
      {
        SELECT * WHERE { ?a ?b ?c }
      }
    }
    ```
=== "On (= 70)"
    ```sparql
    SELECT * WHERE {
      { SELECT * WHERE { ?a ?b ?c } }
    }
    ```

### Line length

*Default: 120.* Target maximum line width the formatter aims for when
deciding how to wrap and compact lines.

## Editor — Completion

These tune the [completion](../features/editor.md#completion) engine.

### Query timeout (ms)

*Default: 5000.* How long to wait for a completion query against the
endpoint before giving up. Raise it for slow endpoints, lower it to fail
fast.

### Result size

*Default: 101.* Maximum number of completion candidates fetched per query.

### Online char threshold

*Default: 3.* Minimum number of characters you must type before completions
that query the endpoint (e.g. subject suggestions) are triggered. A higher
value means fewer, more targeted requests.

### Object completion suffix

*Default: on.* After you accept an object completion, finish the triple with
` .`, start a new line at the right indentation, and trigger the next
completion — so you can keep adding triples without typing the separators.

=== "On — picking an object inserts"
    ```sparql
    ?s ?p wd:Q42 .
    ⎢   ← cursor, ready for the next triple
    ```
=== "Off"
    ```sparql
    ?s ?p wd:Q42⎢
    ```

### Same subject semicolon

*Default: on.* When you complete a subject that matches the previous
triple's subject, the completion switches to `;` notation instead of
repeating the subject and starting a new triple.

### Max variables

*Default: 10.* Caps how many variable names are offered as completions.
Leave it empty for unlimited.

## Editor — Miscellaneous

### Add missing prefixes

*Default: on.* Using a prefixed name like `wdt:P31` automatically inserts
the matching `PREFIX` declaration (from the endpoint's
[prefix map](endpoints.md#field-reference)).

### Remove unused prefixes

*Default: off.* On format, drop `PREFIX` declarations that are no longer
referenced in the query.

### Jump with tab

*Default: off.* Lets `Tab` / `Shift+Tab` jump between relevant positions in
the query (such as snippet tab stops) instead of inserting indentation.

### Auto line break

*Default: off.* Automatically starts a new line after you type `.` or `;`.

## Results

How the [results view](../features/results.md) renders. Annotation toggles take effect
immediately on the currently displayed results.

### Type annotations

*Default: on.* Show datatype tags (e.g. `xsd:integer`) on literal values.

### Language annotations

*Default: on.* Show language tags (e.g. `@en`) on literal values.

### Load images

*Default: on.* Render result values that are image IRIs as inline
thumbnails instead of plain links.

### Shorten IRIs

*Default: on.* Display IRIs as prefixed names (e.g. `wd:Q42`) using the
endpoint's prefix map. Turn it off to show full IRIs.

### Limit

*Default: 100.* Number of result rows fetched per page.
