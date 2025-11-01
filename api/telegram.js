// Vercel Serverless function to handle Telegram webhooks.
// Deploy this project on Vercel and set the project's Environment Variables:
// - TELEGRAM_TOKEN = <your bot token>
// - API_URL = https://factcheckbot.onrender.com   (or your deployed backend)

const URL_REGEX = /https?:\/\/(?:[\w\-./?%&=+~#:,;@!$'()*\[\]]+)/i;

function extractUrl(text) {
  if (!text) return null;
  // If user used /check command: /check <url>
  const cmdMatch = text.match(/\/check\s+(\S+)/i);
  if (cmdMatch) return cmdMatch[1];
  const m = text.match(URL_REGEX);
  return m ? m[0] : null;
}

module.exports = async (req, res) => {
  try {
    if (req.method !== 'POST') return res.status(200).send('OK');

    const update = req.body || {};

    const message = update.message || update.edited_message || update.channel_post;
    if (!message) return res.status(200).send('no message');

    const chatId = message.chat && message.chat.id;
    const text = message.text || '';

    const url = extractUrl(text);
    if (!url) {
      // optional: ignore non-URL messages to save execution time
      await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId, text: 'Please send a URL or use /check <url>.' }),
      });
      return res.status(200).send('no url');
    }

    // Call the backend /check endpoint
    const apiUrl = (process.env.API_URL || 'https://factcheckbot.onrender.com').replace(/\/$/, '') + '/check';
    const resp = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });

    if (!resp.ok) {
      const textErr = await resp.text();
      await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId, text: `Error analyzing article: ${resp.status} ${textErr}` }),
      });
      return res.status(200).send('backend error');
    }

    const data = await resp.json();
    const reasons = (data.reasons || []).slice(0, 3).join(' | ') || 'No clear signals';
    const messageText = `📰 Title: ${data.title || 'N/A'}\n🎯 Trust Score: ${data.trust_score ?? 'N/A'}%\n✍️ Verdict: ${data.verdict || 'N/A'}\n\nWhy: ${reasons}`;

    // Send reply back to Telegram
    await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: messageText }),
    });

    return res.status(200).send('ok');
  } catch (err) {
    console.error('telegram webhook error', err);
    // best effort notify the user
    try {
      const chatId = (req.body && req.body.message && req.body.message.chat && req.body.message.chat.id) || null;
      if (chatId && process.env.TELEGRAM_TOKEN) {
        await fetch(`https://api.telegram.org/bot${process.env.TELEGRAM_TOKEN}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_id: chatId, text: 'Internal bot error. Try again later.' }),
        });
      }
    } catch (e) {}
    return res.status(500).send('error');
  }
};
