# YouTube Video Summarizer Extension

Minimal browser extension that adds a "Summarize" button to YouTube videos, generating PDF summaries via local API.

## Features

- 📄 Right-click context menu on any YouTube video link
- 🌐 Cross-browser support (Chrome, Firefox, Edge, Safari)
- ⚡ Minimal footprint (~70 lines of TypeScript)
- 🔄 Automatic video ID extraction
- 💾 Browser-native download handling
- 🛡️ Stable - uses browser's native context menu (immune to YouTube UI changes)

## Prerequisites

1. **API Server Running**: Start the FastAPI backend on `http://localhost:8000`
   ```bash
   # From project root
   uvicorn python.infra.api.main:app --reload
   ```

2. **ANTHROPIC_API_KEY**: Set in `.env` file (required for Claude API)

## Installation

### Development Build

```bash
# From project root
pnpm install
pnpm --filter @peace/extension build
```

### Load Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `packages/extension` directory (not `dist/`)
5. Extension should appear with 📄 icon

### Load Extension in Firefox

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to `packages/extension` directory
4. Select `manifest.json`

### Load Extension in Edge

1. Open Edge and navigate to `edge://extensions/`
2. Enable "Developer mode" (toggle in left sidebar)
3. Click "Load unpacked"
4. Select the `packages/extension` directory

### Load Extension in Safari

1. **Enable Developer Menu**: Safari → Preferences → Advanced → Check "Show Develop menu"
2. **Convert to Safari Extension** (one-time setup):
   ```bash
   xcrun safari-web-extension-converter packages/extension --app-name "YouTube Summarizer"
   ```
3. Open the generated Xcode project and run
4. Enable extension in Safari → Preferences → Extensions

## Usage

### Right-Click Any YouTube Video Link

1. **Find any YouTube video link** on any page:
   - Video thumbnails (Home, Subscriptions, Search results)
   - Links in video descriptions
   - Links in comments
   - Links in playlists
   - Shared YouTube URLs anywhere

2. **Right-click the video link**

3. **Select "📄 Generate Summary"** from the context menu

4. **PDF downloads automatically**
   - File named: `VIDEO_ID_summary.pdf`
   - Browser's native download dialog appears

**Works on:**
- Desktop and laptop browsers
- Any page containing YouTube video links
- Both youtube.com and youtube.com subdomains

## Development

### Watch Mode

```bash
pnpm --filter @peace/extension build:watch
```

Changes to TypeScript files auto-compile. Reload extension in browser after changes.

### Clean Build

```bash
pnpm --filter @peace/extension clean
pnpm --filter @peace/extension build
```

## Architecture

```
background.ts (~70 lines)
├─ Register context menu on YouTube video links
├─ Extract video ID from right-clicked URL
├─ Fetch PDF from API
└─ Trigger browser download

content.ts (~3 lines)
└─ Minimal presence indicator (console log)

manifest.json
├─ Manifest V3 format
├─ contextMenus permission
└─ Background service worker
```

## Troubleshooting

### Context menu not appearing

- Verify extension is enabled in browser
- Check you're right-clicking a YouTube video link (must contain `/watch?v=`)
- Try reloading the extension
- Check browser console for errors (F12 → Console)

### Download fails

- Check API server is running: `curl http://localhost:8000/docs`
- Check browser console for error messages
- Verify video ID extraction: right-click URL should contain `?v=VIDEO_ID`
- Check API logs for errors in terminal running uvicorn

### API returns error

- Verify ANTHROPIC_API_KEY is set in `.env`
- Check video has audio/transcript available
- View API logs in terminal running uvicorn
- Test API directly: `curl http://localhost:8000/audio/summary/VIDEO_ID`

## API Endpoint

```
GET /audio/summary/{video_id}
```

**Response**: `application/pdf` binary

**Process**:
1. Download audio from YouTube (yt-dlp)
2. Transcribe audio (OpenAI Whisper)
3. Summarize with Claude API
4. Render HTML template (Jinja2)
5. Generate PDF (WeasyPrint)

## File Structure

```
packages/extension/
├── manifest.json          # Extension metadata
├── package.json          # NPM dependencies
├── tsconfig.json         # TypeScript config
├── src/
│   ├── content.ts        # YouTube page injection
│   └── background.ts     # API communication
└── dist/                 # Compiled JavaScript
    ├── content.js
    └── background.js
```

## Permissions

- `downloads`: Save PDF files
- `contextMenus`: Add right-click menu items
- `http://localhost:8000/*`: API access

## Advantages of Context Menu Approach

- **Stable**: Uses browser's native context menu API
- **Immune to YouTube UI changes**: No DOM manipulation needed
- **Works everywhere**: Any YouTube link on any page
- **Cross-browser compatible**: Standard browser API
- **Minimal code**: No mutation observers, event listeners, or DOM queries
- **Better UX**: Familiar right-click interaction

## Limitations (POC)

- Only works with localhost API
- No error notifications (console only)
- No retry logic
- No authentication
- No caching

## Future Enhancements

- [ ] Production API endpoint configuration
- [ ] Error notifications (browser notifications API)
- [ ] Progress indicator with badge
- [ ] Queue multiple videos
- [ ] Authentication support
- [ ] Cache summaries
- [ ] Settings page for API endpoint
