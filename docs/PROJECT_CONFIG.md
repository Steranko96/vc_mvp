# Project configuration format

`devforge new` saves UTF-8 JSON to `.devforge/projects/<project-id>.json` under
the current working directory. The structural format is described by
[project-config-v1.schema.json](project-config-v1.schema.json), generated from
`ProjectConfig.model_json_schema()`. `schema_version` is always `1`; incompatible
future formats must use a new version. Unknown fields and versions are rejected
by the model. The JSON Schema is not a complete domain validator: consumers must
validate with `ProjectConfig.model_validate_json()` before using a configuration.
The schema does not trim text or implement the Unicode normalization required
for project IDs. It can accept whitespace-only strings and names that the model
rejects, and can reject padded strings whose trimmed length the model accepts.
No timestamps, absolute paths, credentials, or environment settings are included.

```json
{
  "schema_version": 1,
  "name": "Task Tracker",
  "description": "A personal task tracker to learn web development",
  "difficulty": "beginner",
  "language": "TypeScript",
  "scaffold_level": "minimal"
}
```

Names and descriptions are trimmed and must be nonempty. Names allow at most 200
characters and descriptions at most 5000. Difficulty is `beginner` or `intermediate`;
language is `TypeScript` (on Node.js); scaffold level is `minimal`. All selections
describe future generation preferences only.

Project IDs use Unicode NFKD normalization, discard non-ASCII characters, lowercase
letters, replace runs of characters other than `a-z` and `0-9` with a hyphen, trim
hyphens, and truncate to 80 characters (trimming any trailing hyphen again).
Names without ASCII letters or digits after normalization are rejected. Reserved
Windows device names (`con`, `prn`, `aux`, `nul`, `com0`–`com9`, `lpt0`–`lpt9`)
receive a `project-` prefix. For example, `Task Tracker!` becomes `task-tracker`.
The ID is derived from the name and used as the filename, rather than duplicated
in the configuration.

A complete temporary file is written in the destination directory and published
with a hard link, which atomically fails if the destination already exists.
Metadata directory symlinks are rejected. Directory-relative operations keep writes
anchored to the opened project directories, including during symlink replacement.
Platforms without directory-relative operations or filesystems without hard-link
support report a save error rather than using an unsafe fallback.
Temporary files are removed on handled failures when possible. Cleanup failure
logs a warning with the temporary path and manual removal instructions. A cleanup
failure after publication still returns success; before publication it preserves
the original exception. Different names can normalize to the same ID; choose
another name if an ID already exists. No existing configuration is overwritten.
Cancellation during prompts never writes configuration data. A forcibly terminated
process during persistence may leave a temporary file for manual cleanup.
