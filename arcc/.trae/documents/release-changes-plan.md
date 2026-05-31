# Claude Code Implementation Plan

## Overview

This document outlines the implementation plan for a series of enhancements and bug fixes for Claude Code CLI. The changes span multiple areas: hook system improvements, UI/terminal rendering, auto mode enhancements, permissions handling, file tools, MCP integration, voice mode, and various bug fixes.

---

## 1. Hook System Enhancements

### 1.1 Add "defer" Permission Decision to PreToolUse Hooks

**Files to modify:**
- `src/types/hooks.ts` - Add `defer` option to `permissionBehaviorSchema` and `syncHookResponseSchema`
- `src/utils/hooks.ts` - Implement deferral logic in `runToolUseHooks`
- `src/services/tools/toolExecution.ts` - Handle deferred tool execution with resume support
- `src/cli/handlers/resume.ts` - Add `-p --resume` flag handling for headless sessions

**Implementation:**
- Add `{defer: true}` option to `PermissionDenied` hook response schema
- When hook returns `permissionDecision: { behavior: 'defer' }`, pause tool execution
- Store deferred tool in session state with unique marker
- On `claude -p --resume`, re-evaluate hook with same input
- If input exceeds 64KB or no marker exists, show error instead of hanging

### 1.2 Add PermissionDenied Hook

**Files to modify:**
- `src/types/hooks.ts` - Add `PermissionDenied` hook event type
- `src/utils/hooks.ts` - Implement `runPermissionDeniedHooks` function
- `src/utils/permissions/permissions.ts` - Call PermissionDenied hook after auto mode classifier denials
- `src/entrypoints/agentSdkTypes.ts` - Add `PermissionDenied` to `HookEvent` type

**Implementation:**
- Hook fires after auto mode classifier denies a command
- Return `{retry: true}` to indicate model can retry
- Hook receives command, cwd, and denial reason

### 1.3 Fix PreToolUse/PostToolUse Hooks file_path

**Files to modify:**
- `src/services/tools/toolHooks.ts` - Ensure `file_path` is absolute path for Write/Edit/Read tools
- `src/tools/FileEditTool/FileEditTool.ts` - Pass absolute path to hooks
- `src/tools/FileWriteTool/FileWriteTool.ts` - Pass absolute path to hooks
- `src/tools/FileReadTool/FileReadTool.ts` - Pass absolute path to hooks

**Implementation:**
- Convert relative paths to absolute before passing to hooks
- Use `path.resolve()` to get absolute paths
- Document this change in hook documentation

---

## 2. UI/Terminal Rendering

### 2.1 Add CLAUDE_CODE_NO_FLICKER=1 Environment Variable

**Files to modify:**
- `src/utils/env.ts` - Add `CLAUDE_CODE_NO_FLICKER` to known environment variables
- `src/ink/termio.ts` - Add flicker-free rendering mode
- `src/screens/REPL.tsx` - Apply no-flicker mode when env var is set
- `src/ink/virtualScroll.ts` (new file) - Virtualized scrollback for alt-screen

**Implementation:**
- When `CLAUDE_CODE_NO_FLICKER=1`, enable virtualized scrollback rendering
- Use alternate screen buffer with virtualized history
- Maintain compatibility with existing rendering behavior

### 2.2 Improved Collapsed Tool Summary

**Files to modify:**
- `src/components/messages/CollapsedReadSearchContent.tsx` - Improve "Listed N directories" display
- `src/utils/collapseReadSearch.ts` - Detect ls/tree/du commands vs file reads

**Implementation:**
- Check tool name and arguments to determine if it's directory listing
- Show "Listed N directories" instead of "Read N files" for ls/tree/du
- Maintain existing behavior for actual file reads

### 2.3 Fix Notification Invalidates

**Files to modify:**
- `src/context/notifications.tsx` - Clear displayed notification immediately on invalidate
- `src/components/Notification.tsx` - Handle immediate clear on invalidate

**Implementation:**
- Call `invalidate()` should clear `currentNotification` state immediately
- Add `forceClear` parameter for immediate UI update

### 2.4 Fix Prompt Disappearing After Submit

**Files to modify:**
- `src/components/PromptInput/PromptInput.tsx` - Prevent prompt from clearing during background message processing
- `src/hooks/useInputBuffer.ts` - Hold input state during background processing

**Implementation:**
- When `isProcessing` is true and background messages arrive, don't clear prompt
- Wait for all background messages to complete before clearing

### 2.5 Fix Devanagari/Combining Mark Truncation

**Files to modify:**
- `src/utils/stringUtils.ts` - Fix character width calculation for combining marks
- `src/ink/stringWidth.ts` - Use correct Unicode width algorithm

**Implementation:**
- Use Unicode 9+ width algorithm that handles combining marks correctly
- Test with Devanagari text containing virama and halant

### 2.6 Fix Rendering Artifacts After Layout Shifts

**Files to modify:**
- `src/ink/screen.ts` - Force full redraw after layout shifts
- `src/ink/renderer.ts` - Add `forceRedraw` flag

**Implementation:**
- Detect layout shift via ResizeObserver or terminal resize events
- Force complete terminal redraw instead of incremental

---

## 3. Auto Mode Improvements

### 3.1 Denied Commands Show Notification + Recent Tab

**Files to modify:**
- `src/utils/permissions/autoModeState.ts` - Track denied commands in session
- `src/components/permissions/PermissionsScreen.tsx` - Add "Recent" tab
- `src/cli/handlers/autoMode.ts` - Add `/permissions recent` command

**Implementation:**
- Store last N denied commands with timestamps
- Show notification on denial with "View in /permissions" action
- Add "Recent" tab to permissions UI showing last 10 denials
- Allow retry with 'r' key

### 3.2 Fix hooks if Condition Filtering

**Files to modify:**
- `src/utils/hooks/hookEvents.ts` - Fix compound command and env-var prefix matching
- `src/utils/bash/parser.ts` - Parse compound commands (ls && git push) correctly

**Implementation:**
- Split compound commands by `&&`, `||`, `;` before matching
- Handle `FOO=bar git push` style env-var prefixes
- Use proper shell parsing instead of simple string matching

### 3.3 Fix Autocompact Thrash Loop

**Files to modify:**
- `src/services/compact/prompt.ts` - Add thrash detection logic
- `src/utils/context.ts` - Detect when context refills immediately after compact

**Implementation:**
- Track consecutive compactions within short time window
- If 3+ compactions occur and context is still at limit, stop and show error
- Error message: "Context still full after multiple compactions. Consider increasing model context window or reducing conversation scope."

---

## 4. File Tools Fixes

### 4.1 Fix Edit/Write CRLF Doubling on Windows

**Files to modify:**
- `src/tools/FileEditTool/FileEditTool.ts` - Normalize line endings before processing
- `src/tools/FileWriteTool/FileWriteTool.ts` - Handle CRLF conversion properly
- `src/utils/fileRead.ts` - Ensure consistent line ending handling

**Implementation:**
- Detect file's existing line ending style on read
- Preserve original line endings during edit operations
- Strip hard line breaks (two trailing spaces + newline) for Markdown

### 4.2 Fix Edit/Write Work with Bash sed/cat

**Files to modify:**
- `src/tools/FileEditTool/FileEditTool.ts` - Support editing files viewed via Bash with sed/cat
- `src/services/tools/toolExecution.ts` - Track files read via Bash tool

**Implementation:**
- Files read via `Bash(sed -n ...)` or `Bash(cat ...)` should be editable
- Track "viewed files" separately from "explicit Read tool calls"
- Remove requirement for separate Read call before Edit

### 4.3 Fix Edit(//path/**) Symlink Resolution

**Files to modify:**
- `src/utils/permissions/permissions.ts` - Check resolved symlink target for glob patterns
- `src/utils/path.ts` - Add `resolveSymlink` utility

**Implementation:**
- For `Edit(//path/**)` patterns, resolve symlinks before checking allow rules
- Store both original path and resolved path in permission checks

### 4.4 Fix Large File OOM Crash

**Files to modify:**
- `src/tools/FileEditTool/FileEditTool.ts` - Add size check before editing
- `src/utils/fileRead.ts` - Reject reads/edits on files > 1GiB

**Implementation:**
- Check file size before attempting to read/edit
- Show error: "File is too large (>1GiB) to edit safely"
- Offer to use Bash with line number ranges instead

---

## 5. MCP Improvements

### 5.1 Add MCP_CONNECTION_NONBLOCKING=true

**Files to modify:**
- `src/services/mcp/client.ts` - Add non-blocking connection mode
- `src/services/mcp/config.ts` - Parse `MCP_CONNECTION_NONBLOCKING` env var
- `src/utils/cliArgs.ts` - Add `--mcp-nonblocking` CLI flag

**Implementation:**
- When enabled, skip MCP connection wait in `-p` mode
- Show "MCP servers connecting..." but don't block
- Tool calls to MCP wait for individual server if not connected

### 5.2 Bounded MCP Config Connections at 5s

**Files to modify:**
- `src/services/mcp/client.ts` - Add connection timeout per server
- `src/services/mcp/config.ts` - Set 5s timeout on server connections

**Implementation:**
- Each MCP server has 5s connection timeout instead of blocking on slowest
- Show partial connection status if some servers timeout
- Log warning for timed-out servers

### 5.3 Fix MCP Tool Error Truncation

**Files to modify:**
- `src/services/mcp/client.ts` - Preserve all content blocks in error responses
- `src/utils/toolErrors.ts` - Don't truncate multi-block errors

**Implementation:**
- Check if error response has multiple content blocks
- Return all content blocks, not just first
- Update tool error formatting to handle arrays

---

## 6. Voice Mode Fixes

### 6.1 Fix Push-to-Talk Modifier Combos

**Files to modify:**
- `src/services/voice.ts` - Fix modifier combo detection
- `src/hooks/useVoice.ts` - Handle complex key bindings

**Implementation:**
- Test modifier combos (Ctrl+Shift+...) properly
- Use `keydown` event properly for modifier detection
- Prevent default browser behavior for bound keys

### 6.2 Fix macOS WebSocket "HTTP 101" Error

**Files to modify:**
- `src/services/voice.ts` - Fix WebSocket upgrade handling on macOS
- `src/utils/voiceModeEnabled.ts` - Platform-specific initialization

**Implementation:**
- Handle WebSocket upgrade rejected with HTTP 101 properly
- Add retry logic with exponential backoff
- Show actionable error if voice mode fails to initialize

### 6.3 Fix Microphone Permission on macOS Apple Silicon

**Files to modify:**
- `src/services/voice.ts` - Request microphone permission correctly
- `src/utils/platform.ts` - Detect Apple Silicon Mac

**Implementation:**
- Use MediaDevices.getUserMedia with correct permission prompt
- Handle the case where permission is denied silently
- Show clear instructions for enabling microphone in System Preferences

---

## 7. Session/Resume Fixes

### 7.1 Fix -p --resume Hangs

**Files to modify:**
- `src/cli/handlers/resume.ts` - Add 64KB input size check
- `src/services/tools/toolExecution.ts` - Handle missing deferred marker gracefully
- `src/utils/sessionRestore.ts` - Validate deferred tool data on restore

**Implementation:**
- Check if deferred tool input exceeds 64KB - show error if so
- If no deferred marker exists, show "Nothing to resume" error
- Add timeout for resume operations

### 7.2 Fix -p --continue Deferred Tools

**Files to modify:**
- `src/cli/handlers/resume.ts` - Handle `--continue` flag properly
- `src/services/tools/toolExecution.ts` - Resume deferred tools in continue mode

**Implementation:**
- `--continue` should resume deferred tools from previous session
- Same validation as `--resume` (64KB limit, marker exists)

### 7.3 Fix --resume Crash with Old Transcripts

**Files to modify:**
- `src/utils/sessionRestore.ts` - Handle tool results from older CLI versions
- `src/utils/messages.ts` - Gracefully parse malformed tool results

**Implementation:**
- Check for `tool_result` version/compatibility field
- If missing or from older version, skip validation
- Handle interrupted writes gracefully

---

## 8. Stats & History Fixes

### 8.1 Fix /stats Undercounting Tokens

**Files to modify:**
- `src/commands/stats/stats.tsx` - Include subagent usage in token counts
- `src/services/analytics/sink.ts` - Track subagent token usage
- `src/cost-tracker.ts` - Aggregate subagent costs

**Implementation:**
- Subagent usage should be added to main session stats
- Track `subagent_total_cost` and `subagent_total_tokens`
- Display in `/stats` output

### 8.2 Fix Stats Cache Historical Data Loss

**Files to modify:**
- `src/utils/statsCache.ts` - Add cache format versioning
- `src/commands/stats/stats.tsx` - Migrate old cache formats

**Implementation:**
- Store cache format version in stats cache file
- On cache format change, migrate old data instead of dropping
- Keep historical data beyond 30 days if present in cache

---

## 9. Settings/Configuration Changes

### 9.1 Reject cleanupPeriodDays: 0

**Files to modify:**
- `src/utils/settings/settings.ts` - Add validation for cleanupPeriodDays
- `src/utils/envValidation.ts` - Reject 0 value with clear error

**Implementation:**
- If `cleanupPeriodDays: 0` is set, reject with validation error
- Error message: "cleanupPeriodDays: 0 is not allowed. Set to a positive number or omit to use the default."
- Previously this silently disabled transcript persistence

### 9.2 Disable Thinking Summaries by Default

**Files to modify:**
- `src/utils/settings/settings.ts` - Default `showThinkingSummaries` to false
- `src/utils/systemPrompt.ts` - Only include thinking summary instructions if enabled
- `src/constants/prompts.ts` - Update default behavior

**Implementation:**
- `showThinkingSummaries: true` now opt-in (was opt-out)
- Interactive sessions don't generate thinking summaries by default
- Maintain backward compatibility for users who set it explicitly

### 9.3 Hook Output > 50K to Disk

**Files to modify:**
- `src/utils/hooks.ts` - Check hook output size before injection
- `src/utils/mcpOutputStorage.ts` - Reuse existing disk storage utility

**Implementation:**
- If hook output exceeds 50K characters, save to disk
- Show file path + preview instead of injecting full text
- Use existing `mcpOutputStorage` mechanism for consistency

---

## 10. PowerShell Tool Fixes

### 10.1 Fix Progress stderr on Windows PS 5.1

**Files to modify:**
- `src/utils/powershell/parser.ts` - Don't treat stderr progress as failure
- `src/tools/BashTool/utils.ts` - Handle mixed stdout/stderr correctly

**Implementation:**
- git push writes progress to stderr but exits 0
- Detect progress patterns in stderr and ignore them
- Only fail on actual error patterns

### 10.2 Fix Argument Splitting Hardening

**Files to modify:**
- `src/utils/powershell/parser.ts` - Handle double-quote + whitespace in arguments
- `src/utils/shellQuote.ts` - Improve PowerShell argument handling

**Implementation:**
- If command argument contains both `"` and whitespace, prompt instead of auto-allowing
- This is a security hardening for PowerShell 5.1 argument splitting quirks

### 10.3 Add Version-Appropriate Syntax Guidance

**Files to modify:**
- `src/tools/BashTool/prompt.ts` - Add PS version detection
- `src/utils/powershell/parser.ts` - Show version-appropriate examples

**Implementation:**
- Detect PowerShell version (5.1 vs 7+)
- Show `$PSVersionTable.PSVersion` examples for 7+
- Show `$host.version` examples for 5.1

---

## 11. Other Fixes

### 11.1 Fix StructuredOutput Schema Cache Bug

**Files to modify:**
- `src/utils/toolSchemaCache.ts` - Fix cache key to include full schema
- `src/services/tools/toolExecution.ts` - Clear cache on schema change

**Implementation:**
- Schema cache was using partial key causing ~50% failure rate
- Include full schema bytes in cache key
- Detect mid-session schema changes and invalidate

### 11.2 Fix LRU Cache Memory Leak

**Files to modify:**
- `src/utils/messages.ts` - Use weak keys or size-limited cache for large JSON inputs
- `src/services/api/client.ts` - Fix cache key for prompt cache

**Implementation:**
- Large JSON inputs were retained as LRU cache keys
- Use WeakMap for object keys or limit cache size
- Add memory pressure handling

### 11.3 Fix Large Session File Crash

**Files to modify:**
- `src/utils/sessionState.ts` - Add size check for session file operations
- `src/memdir/memdir.ts` - Stream large JSON files instead of loading

**Implementation:**
- Check session file size before loading
- If > 50MB, show error instead of crashing
- Offer to archive old sessions

### 11.4 Fix LSP Server Zombie State

**Files to modify:**
- `src/services/lsp/manager.ts` - Add restart on next request logic
- `src/tools/LSPTool/LSPTool.ts` - Handle LSP crash gracefully

**Implementation:**
- After crash, mark server as needing restart
- On next tool request, start new server instead of failing
- Don't require session restart

### 11.5 Fix CJK/Emoji History Boundary Drop

**Files to modify:**
- `src/utils/fileHistory.ts` - Handle 4KB boundary correctly for multi-byte text
- `src/utils/history.ts` - Use byte offset not char offset

**Implementation:**
- History entries containing CJK or emoji were dropped when on 4KB boundary
- Use byte-based offset instead of character offset
- Properly handle UTF-8 encoding in boundary detection

### 11.6 Fix Nested CLAUDE.md Re-injection

**Files to modify:**
- `src/utils/claudemd.ts` - Track which CLAUDE.md files have been injected
- `src/context.ts` - Deduplicate CLAUDE.md content

**Implementation:**
- Maintain set of injected CLAUDE.md paths
- Don't re-inject same file in long sessions
- Handle nested includes properly

### 11.7 Fix Prompt Cache Mid-Session Changes

**Files to modify:**
- `src/services/api/client.ts` - Track tool schema bytes
- `src/query/tokenBudget.ts` - Detect schema changes

**Implementation:**
- Tool schema bytes changing mid-session caused cache misses
- Track schema hash and include in cache key
- Invalidate prompt cache when schema changes

### 11.8 Fix claude-cli:// Deep Links on macOS

**Files to modify:**
- `src/utils/deepLink/banner.ts` - Register URL scheme properly
- `src/entrypoints/cli.tsx` - Handle deep link activation

**Implementation:**
- Use proper macOS URL scheme registration
- Handle `claude-cli://` URLs correctly
- Show instructions if deep links aren't working

### 11.9 Fix Skill Context Drop with Images

**Files to modify:**
- `src/utils/messages.ts` - Preserve skill reminders when sending images
- `src/services/api/client.ts` - Include system context with image messages

**Implementation:**
- When sending messages with images via SDK, include skill reminders
- Don't drop system context when images are present
- Ensure skill context is always included

### 11.10 Fix Collapsed Badge Duplication

**Files to modify:**
- `src/components/messages/CollapsedReadSearchContent.tsx` - Deduplicate badges
- `src/utils/collapseReadSearch.ts` - Track shown badges

**Implementation:**
- During heavy parallel tool use, badges were duplicating
- Track which badges have been shown in current render cycle
- Use Set for deduplication

### 11.11 Fix Shift+Enter on Windows Terminal Preview

**Files to modify:**
- `src/ink/parse-keypress.ts` - Handle vkey 0x0D (VK_RETURN) with shift
- `src/hooks/useInputBuffer.ts` - Distinguish Shift+Enter from Enter

**Implementation:**
- Windows Terminal Preview 1.25 sends different keycode for Shift+Enter
- Map VK_RETURN + shift to newline instead of submit
- Test on Windows Terminal Preview

### 11.12 Fix Periodic UI Jitter in iTerm2/tmux

**Files to modify:**
- `src/ink/renderer.ts` - Add tmux compatibility mode
- `src/ink/terminal.ts` - Detect tmux and adjust rendering

**Implementation:**
- Detect if running inside tmux
- Disable certain optimization that cause jitter in tmux
- Add `TMUX_JITTER_FIX` environment variable for explicit opt-in

---

## 12. New Features

### 12.1 Add TaskCreated Hook Event

**Files to modify:**
- `src/types/hooks.ts` - Add `TaskCreated` to `HookEvent`
- `src/entrypoints/agentSdkTypes.ts` - Document blocking behavior
- `src/tasks/types.ts` - Emit hook on task creation

**Implementation:**
- Document that TaskCreated is blocking
- Task waits for hook to complete before starting
- Hook receives task configuration

### 12.2 Preserve Task Notifications on Ctrl+B

**Files to modify:**
- `src/components/TaskListV2.tsx` - Don't clear notifications on background
- `src/hooks/useTasksV2.ts` - Preserve notification state

**Implementation:**
- Task notifications persist when backgrounding with Ctrl+B
- Notifications show until explicitly dismissed or task completes
- This was a regression - restore original behavior

### 12.3 Add /buddy April 1st Feature

**Files to modify:**
- `src/buddy/companion.ts` - Add companion sprite
- `src/buddy/sprites.ts` - Add sprite animations
- `src/commands/buddy/index.ts` - Add `/buddy` command

**Implementation:**
- Small creature that watches you code
- Hatch from egg interaction
- Various animations (typing, idle, happy)
- Only active around April 1st

### 12.4 Add @mention Typeahead Improvements

**Files to modify:**
- `src/hooks/useTypeahead.tsx` - Rank source files above MCP resources
- `src/components/PromptInput/PromptInput.tsx` - Update typeahead UI

**Implementation:**
- When `@` is typed, show typeahead with agents, files, MCP
- Rank source files higher than MCP resources with similar names
- Add keyboard navigation

### 12.5 Add /env PowerShell Support

**Files to modify:**
- `src/commands/env/index.js` - Apply env vars to PowerShell commands
- `src/utils/env.ts` - Parse env vars for PowerShell syntax

**Implementation:**
- `/env FOO=bar` now affects PowerShell tool commands
- Previously only affected Bash
- Use `$env:FOO = "bar"` syntax for PowerShell

### 12.6 Add /usage Pro/Enterprise Week Bar Hide

**Files to modify:**
- `src/commands/usage/usage.tsx` - Check plan type before showing bar
- `src/services/api/usage.ts` - Get plan type from API

**Implementation:**
- Hide redundant "Current week (Sonnet only)" bar for Pro and Enterprise
- Only show for free tier users
- Check ` entitlement

### 12.7 Image Paste No Trailing Space

**Files to modify:**
- `src/utils/imagePaste.ts` - Don't append space after image paste
- `src/hooks/usePasteHandler.ts` - Handle image paste specially

**Implementation:**
- When pasting image, don't add trailing space
- Pasting `!command` into empty prompt enters bash mode

### 12.8 Bash Tool Formatter/Linter Warning

**Files to modify:**
- `src/tools/BashTool/utils.ts` - Track previously read files
- `src/tools/BashTool/prompt.ts` - Add warning for stale edits

**Implementation:**
- If user runs formatter/linter that modifies previously read files, warn
- Prevents stale-edit errors where file was reformatted after read
- Track file reads from Bash tool

---

## 13. Document Hook Events

### 13.1 Document TaskCreated Hook Event

**Files to modify:**
- `src/schemas/hooks.ts` - Document TaskCreated with blocking behavior
- `src/types/hooks.ts` - Add JSDoc comments

**Implementation:**
- TaskCreated hook blocks task execution until hook completes
- Document use cases: logging, task naming, pre-flight checks
- Provide example hook configuration

---

## Implementation Order

1. **Critical Bug Fixes First**
   - Fix `-p --resume` hangs (7.1, 7.2)
   - Fix Edit/Write CRLF doubling (4.1)
   - Fix StructuredOutput schema cache (11.1)
   - Fix LRU cache memory leak (11.2)
   - Fix notification clearing (2.3)

2. **Hook System Enhancements**
   - Add PermissionDenied hook (1.2)
   - Add defer permission decision (1.1)
   - Fix PreToolUse file_path (1.3)
   - Fix hooks if condition filtering (3.2)

3. **Auto Mode & Permissions**
   - Add denied commands notification + Recent tab (3.1)
   - Fix autocompact thrash loop (3.3)
   - Reject cleanupPeriodDays: 0 (9.1)

4. **UI/Terminal**
   - Add CLAUDE_CODE_NO_FLICKER (2.1)
   - Fix Devanagari truncation (2.5)
   - Fix Shift+Enter on Windows Terminal Preview (11.11)

5. **MCP & Voice**
   - Add MCP_CONNECTION_NONBLOCKING (5.1)
   - Fix voice push-to-talk (6.1)
   - Fix macOS WebSocket error (6.2)

6. **File Tools**
   - Fix Edit/Write work with Bash sed/cat (4.2)
   - Fix Edit glob symlink resolution (4.3)
   - Fix large file OOM (4.4)

7. **Stats & History**
   - Fix /stats subagent counting (8.1)
   - Fix stats cache data loss (8.2)
   - Fix CJK/Emoji history boundary (11.5)

8. **Settings & Configuration**
   - Disable thinking summaries by default (9.2)
   - Hook output > 50K to disk (9.3)

9. **PowerShell Tool**
   - Fix progress stderr (10.1)
   - Fix argument splitting (10.2)
   - Add version syntax guidance (10.3)

10. **New Features**
    - TaskCreated hook documentation (12.1, 13.1)
    - /buddy April 1st (12.3)
    - @mention improvements (12.4)
    - /env PowerShell support (12.5)

---

## Testing Strategy

1. **Unit Tests**: Each module should have corresponding test file
2. **Integration Tests**: Test hook flow end-to-end
3. **Platform-Specific Tests**: Windows, macOS, Linux分别测试
4. **Regression Tests**: Run existing test suite before/after changes
5. **Manual Testing**: Critical fixes require manual verification

---

## Risk Assessment

### High Risk Changes
- Hook system modifications (could break existing hooks)
- Auto mode permission flow (could affect security)
- CRLF handling (could corrupt files)

### Medium Risk Changes
- Terminal rendering changes (could cause display issues)
- MCP connection handling (could affect tool availability)

### Low Risk Changes
- UI text improvements
- New optional features
- Documentation additions

---

## Rollback Plan

For high-risk changes, prepare rollback procedures:
- Hook changes: Feature flag to disable deferral
- CRLF changes: Detect file encoding and use original
- Permission changes: Maintain old behavior with flag
