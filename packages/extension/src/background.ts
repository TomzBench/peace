// Background service worker: Handle context menu and downloads

// Cross-browser compatibility: Use browser API if available, fallback to chrome
// @ts-ignore - browser global exists in Firefox/Safari
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const API_BASE_URL = 'http://localhost:8000';

console.log('🚀 Background script loaded!');
console.log('🔧 API Base URL:', API_BASE_URL);
console.log('🌍 Browser API:', typeof browserAPI);

// Extract video ID from YouTube URL
function extractVideoIdFromUrl(url: string): string | null {
  try {
    const urlObj = new URL(url);
    return urlObj.searchParams.get('v');
  } catch {
    return null;
  }
}

// Download PDF summary for video with progress updates
async function downloadPDF(videoId: string): Promise<void> {
  const url = `${API_BASE_URL}/audio/summary/${videoId}`;

  console.log(`📄 [1/8] Starting summary generation for video: ${videoId}`);
  console.log(`🔗 [2/8] Calling SSE endpoint: ${url}`);

  // Show initial notification
  await browserAPI.notifications.create(`summary-${videoId}`, {
    type: 'basic',
    iconUrl: 'icon.svg',
    title: 'YouTube Summarizer',
    message: 'Starting summary generation...',
  });
  console.log(`📢 [3/8] Initial notification shown`);

  try {
    console.log(`🌐 [4/8] Initiating fetch...`);
    const response = await fetch(url);
    console.log(`✅ [5/8] Fetch completed, status: ${response.status}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    console.log(`📖 [6/8] Reader initialized, starting to read stream...`);
    let buffer = '';
    let eventCount = 0;

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log(`🏁 [7/8] Stream finished after ${eventCount} events`);
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          eventCount++;
          const data = JSON.parse(line.slice(6));
          console.log(`📨 Event ${eventCount}: ${data.status} - ${data.message}`);

          // Update notification (Firefox doesn't support update, use create with same ID)
          await browserAPI.notifications.create(`summary-${videoId}`, {
            type: 'basic',
            iconUrl: 'icon.svg',
            title: 'YouTube Summarizer',
            message: data.message,
          });

          // Handle completion
          if (data.status === 'complete' && data.pdf) {
            console.log(`📦 Decoding PDF (${data.pdf.length} base64 chars)...`);
            const pdfBytes = Uint8Array.from(atob(data.pdf), c => c.charCodeAt(0));
            const blob = new Blob([pdfBytes], { type: 'application/pdf' });
            const blobUrl = URL.createObjectURL(blob);

            console.log(`💾 Triggering download...`);
            await browserAPI.downloads.download({
              url: blobUrl,
              filename: data.filename,
              saveAs: true,
            });

            // Show success notification
            await browserAPI.notifications.create(`summary-${videoId}`, {
              type: 'basic',
              iconUrl: 'icon.svg',
              title: 'YouTube Summarizer',
              message: '✅ Summary downloaded successfully!',
            });

            console.log(`✅ [8/8] Download initiated for: ${videoId}`);
          } else if (data.status === 'error') {
            const errorType = data.error_module ? `${data.error_module}.${data.error_type}` : data.error_type;
            console.error(`❌ Server error [${errorType}]: ${data.message}`);

            // Show user-friendly error message
            let userMessage = data.message;
            if (data.message.includes('rate_limit') || data.message.includes('quota')) {
              userMessage = '⚠️ API rate limit reached. Please try again later or upgrade your API tier.';
            } else if (data.message.includes('API key')) {
              userMessage = '⚠️ API key not configured. Check server .env file.';
            }

            throw new Error(userMessage);
          }
        }
      }
    }
  } catch (error) {
    // Log error concisely
    const errorMsg = error instanceof Error ? error.message : String(error);
    const errorName = error instanceof Error ? error.name : 'Error';
    console.error(`❌ Summary failed [${errorName}]: ${errorMsg}`);

    // Show error notification
    await browserAPI.notifications.create(`summary-${videoId}`, {
      type: 'basic',
      iconUrl: 'icon.svg',
      title: 'YouTube Summarizer - Error',
      message: errorMsg,
    });

    // Don't re-throw - error already handled
  }
}

// Create context menu items on install AND on startup
function createContextMenus() {
  console.log('🔧 Creating context menus...');

  // Remove existing menus first to avoid duplicates
  browserAPI.contextMenus.removeAll(() => {
    // Context menu for ALL contexts on YouTube
    browserAPI.contextMenus.create({
      id: 'summarize-video-all',
      title: '📄 Generate Summary',
      contexts: ['all'],
      documentUrlPatterns: ['*://www.youtube.com/*', '*://*.youtube.com/*']
    }, () => {
      if (browserAPI.runtime.lastError) {
        console.error('❌ Error creating context menu:', browserAPI.runtime.lastError);
      } else {
        console.log('✅ Context menu created successfully');
      }
    });
  });
}

// Create on install
browserAPI.runtime.onInstalled.addListener(() => {
  console.log('🎉 Extension installed/updated');
  createContextMenus();
});

// Recreate on startup (handles browser restart)
browserAPI.runtime.onStartup.addListener(() => {
  console.log('🚀 Browser started');
  createContextMenus();
});

// Create immediately on script load
createContextMenus();

// Handle context menu clicks
console.log('🎯 Registering context menu click handler...');
browserAPI.contextMenus.onClicked.addListener((info: any, tab: any) => {
  console.log('🖱️ ========== CONTEXT MENU CLICKED ==========');
  console.log('🖱️ Context menu clicked:', {
    menuItemId: info.menuItemId,
    linkUrl: info.linkUrl,
    srcUrl: info.srcUrl,
    pageUrl: info.pageUrl,
    tabUrl: tab?.url,
  });

  let videoId: string | null = null;

  // Try to extract video ID from various sources
  if (info.linkUrl) {
    // Right-clicked on a link
    videoId = extractVideoIdFromUrl(info.linkUrl);
    console.log(`📎 Video ID from linkUrl: ${videoId}`);
  }

  if (!videoId && info.pageUrl) {
    // Try page URL
    videoId = extractVideoIdFromUrl(info.pageUrl);
    console.log(`📄 Video ID from pageUrl: ${videoId}`);
  }

  if (!videoId && tab?.url) {
    // Try tab URL as fallback
    videoId = extractVideoIdFromUrl(tab.url);
    console.log(`🔖 Video ID from tab URL: ${videoId}`);
  }

  if (!videoId) {
    console.error('❌ Could not extract video ID from any source');
    browserAPI.notifications.create({
      type: 'basic',
      iconUrl: 'icon.svg',
      title: 'YouTube Summarizer',
      message: '❌ Could not find video ID. Try right-clicking directly on a video link.',
    });
    return;
  }

  console.log(`🎬 Summarizing video: ${videoId}`);

  downloadPDF(videoId).catch((error) => {
    console.error('❌ Download failed:', error);
  });
});
