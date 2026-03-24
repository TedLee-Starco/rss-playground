import channels from "../channels.json";

interface Channel {
  id: string;
  name: string;
  webhookKey: string;
  message?: string;
  showDescriptionUrls?: boolean;
  descriptionUrlFilter?: string;
}

interface Env {
  STATE: KVNamespace;
  YOUTUBE_API_KEY: string;
  [key: string]: unknown;
}

interface VideoEntry {
  videoId: string;
  title: string;
}

interface VideoDetails {
  durationSeconds: number;
  descriptionUrls: string[];
}

const YOUTUBE_RSS_BASE =
  "https://www.youtube.com/feeds/videos.xml?channel_id=";

function unescapeXml(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#39;/g, "'");
}

function parseLatestVideo(xml: string): VideoEntry | null {
  const entry = xml.match(/<entry>([\s\S]*?)<\/entry>/)?.[1];
  if (!entry) return null;

  const videoId = entry.match(/<yt:videoId>(.*?)<\/yt:videoId>/)?.[1];
  const title = entry.match(/<title>(.*?)<\/title>/)?.[1];

  if (!videoId || !title) return null;

  return { videoId, title: unescapeXml(title) };
}

function parseIsoDurationSeconds(iso: string): number {
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return 0;
  return (parseInt(match[1] ?? "0") * 3600)
    + (parseInt(match[2] ?? "0") * 60)
    + parseInt(match[3] ?? "0");
}

function extractUrls(text: string): string[] {
  return [...new Set(text.match(/https?:\/\/\S+/g) ?? [])];
}

async function fetchWithTimeout(url: string, timeoutMs = 10000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchVideoDetails(
  videoId: string,
  apiKey: string
): Promise<VideoDetails | null> {
  const params = new URLSearchParams({
    part: "contentDetails,snippet",
    id: videoId,
    key: apiKey,
  });
  const response = await fetchWithTimeout(
    `https://www.googleapis.com/youtube/v3/videos?${params}`
  );
  if (!response.ok) return null;

  const data = await response.json() as {
    items?: Array<{
      contentDetails: { duration: string };
      snippet: { description: string };
    }>;
  };
  const item = data.items?.[0];
  if (!item) return null;

  return {
    durationSeconds: parseIsoDurationSeconds(item.contentDetails.duration),
    descriptionUrls: extractUrls(item.snippet.description),
  };
}

async function sendDiscordNotification(
  webhookUrl: string,
  channelName: string,
  video: VideoEntry,
  message: string,
  descriptionUrls: string[]
): Promise<void> {
  const videoUrl = `https://www.youtube.com/watch?v=${video.videoId}`;
  const lines = [
    `⚔️ ${channelName} 發布了最新的COC影片!!!`,
    `📌 影片標題： ${video.title}`,
    `🔗 觀看連結： ${videoUrl}`,
    message,
  ];

  if (descriptionUrls.length > 0) {
    lines.push(` ---------------------------------------------------------------------------------------------------------`);
    lines.push(...descriptionUrls.slice(0, 10).map((url, i) => `✅ Base #${i + 1}： <${url}>`));
  }

  lines.push(` ---------------------------------------------------------------------------------------------------------`);

  const content = lines.join("\n");
  console.log(`Message length: ${content.length}`);

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error(`Discord webhook failed: ${response.status}`);
  }
}

async function checkChannel(channel: Channel, env: Env): Promise<void> {
  const response = await fetchWithTimeout(`${YOUTUBE_RSS_BASE}${channel.id}`);
  if (!response.ok) {
    console.error(`Failed to fetch RSS for ${channel.name}: ${response.status}`);
    return;
  }

  const latest = parseLatestVideo(await response.text());
  if (!latest) {
    console.log(`No videos found for ${channel.name}`);
    return;
  }

  const lastVideoId = await env.STATE.get(channel.id);

  if (latest.videoId === lastVideoId) return;

  if (lastVideoId !== null) {
    const details = await fetchVideoDetails(latest.videoId, env.YOUTUBE_API_KEY);

    if (details && details.durationSeconds <= 120) {
      console.log(`Skipping short: ${latest.title}`);
      await env.STATE.put(channel.id, latest.videoId);
      return;
    }

    const webhookUrl = env[channel.webhookKey] as string;
    if (!webhookUrl) {
      console.error(`Secret "${channel.webhookKey}" not set for ${channel.name}`);
      return;
    }
    const message = channel.message ?? "各位成員快去學習新打法新戰術";
    let descriptionUrls: string[] = [];
    if (channel.showDescriptionUrls && details) {
      descriptionUrls = channel.descriptionUrlFilter
        ? details.descriptionUrls.filter((u) => u.startsWith(channel.descriptionUrlFilter!))
        : details.descriptionUrls;
    }

    await sendDiscordNotification(webhookUrl, channel.name, latest, message, descriptionUrls);
    console.log(`New video on ${channel.name}: ${latest.title}`);
  } else {
    console.log(`First run for ${channel.name}, storing ${latest.videoId}`);
  }

  await env.STATE.put(channel.id, latest.videoId);
}

export default {
  async scheduled(
    _event: ScheduledEvent,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<void> {
    for (const channel of channels as Channel[]) {
      await checkChannel(channel, env).catch((err) =>
        console.error(`Error checking ${channel.id}:`, err)
      );
    }
  },

  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/seed-test") {
      const targetName = url.searchParams.get("name");
      const list = (channels as Channel[]).filter(
        (ch) => !targetName || ch.name === targetName
      );
      if (targetName && list.length === 0) {
        return new Response(`Channel "${targetName}" not found.`, { status: 404 });
      }
      for (const ch of list) {
        await env.STATE.put(ch.id, "fake-old-video-id");
      }
      const seeded = list.map((ch) => ch.name).join(", ");
      return new Response(`KV seeded for: ${seeded}. Now trigger /__scheduled to test Discord.`);
    }
    return new Response("Not found", { status: 404 });
  },
};
