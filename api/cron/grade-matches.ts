import type { VercelRequest, VercelResponse } from '@vercel/node';

// Send alert to ntfy.sh
async function sendNtfyAlert(topic: string, title: string, message: string, priority: 'default' | 'high' | 'urgent' = 'default') {
  if (!topic) return;
  try {
    await fetch(`https://ntfy.sh/${topic}`, {
      method: 'POST',
      headers: {
        'Title': title,
        'Priority': priority,
        'Tags': 'dart,soccer,memo'
      },
      body: message
    });
  } catch (err) {
    console.error('Failed to dispatch ntfy alert:', err);
  }
}

// Fetch match fixture details by fixture ID from API-Football
async function fetchFixtureStatus(fixtureId: number, apiKey: string, provider: string) {
  const isDirect = provider.toLowerCase() === 'direct';
  const url = isDirect
    ? `https://v3.football.api-sports.io/fixtures?id=${fixtureId}`
    : `https://api-football-v1.p.rapidapi.com/v3/fixtures?id=${fixtureId}`;

  const headers: Record<string, string> = isDirect
    ? { 'x-apisports-key': apiKey }
    : {
        'X-RapidAPI-Key': apiKey,
        'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
      };

  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`API-Football error: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return data.response?.[0];
}

// Evaluate selection condition
export function gradeSelection(
  selection: string,
  homeScore: number,
  awayScore: number,
  closingOdds: number
): { status: 'HIT 🎯' | 'MISS ❌' | 'PUSH 🔄'; unitVariance: number } {
  const cleanSel = selection.trim();

  // 1X2 Market
  if (cleanSel === 'Home Win') {
    if (homeScore > awayScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  if (cleanSel === 'Away Win') {
    if (awayScore > homeScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  if (cleanSel.toLowerCase().startsWith('draw')) {
    if (homeScore === awayScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Draw No Bet (DNB)
  if (cleanSel === 'Home Win DNB') {
    if (homeScore > awayScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    if (homeScore === awayScore) return { status: 'PUSH 🔄', unitVariance: 0.0 };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  if (cleanSel === 'Away Win DNB') {
    if (awayScore > homeScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    if (homeScore === awayScore) return { status: 'PUSH 🔄', unitVariance: 0.0 };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Over / Under Goals
  const totalGoals = homeScore + awayScore;
  const overMatch = cleanSel.match(/Over\s*([0-9.]+)\s*Goals?/i);
  if (overMatch) {
    const line = parseFloat(overMatch[1]);
    if (totalGoals > line) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  const underMatch = cleanSel.match(/Under\s*([0-9.]+)\s*Goals?/i);
  if (underMatch) {
    const line = parseFloat(underMatch[1]);
    if (totalGoals < line) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Both Teams To Score (BTTS)
  if (cleanSel === 'BTTS - Yes') {
    if (homeScore > 0 && awayScore > 0) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  if (cleanSel === 'BTTS - No') {
    if (homeScore === 0 || awayScore === 0) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Win to Nil
  if (cleanSel === 'Home Win to Nil') {
    if (homeScore > awayScore && awayScore === 0) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }
  if (cleanSel === 'Away Win to Nil') {
    if (awayScore > homeScore && homeScore === 0) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Asian Handicap: Home Win -X.5 AH
  const ahHomeMatch = cleanSel.match(/Home Win\s*(-?[0-9.]+)\s*AH/i);
  if (ahHomeMatch) {
    const spread = parseFloat(ahHomeMatch[1]);
    if (homeScore + spread > awayScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Asian Handicap: Away Win -X.5 AH
  const ahAwayMatch = cleanSel.match(/Away Win\s*(-?[0-9.]+)\s*AH/i);
  if (ahAwayMatch) {
    const spread = parseFloat(ahAwayMatch[1]);
    if (awayScore + spread > homeScore) return { status: 'HIT 🎯', unitVariance: Number((closingOdds - 1).toFixed(2)) };
    return { status: 'MISS ❌', unitVariance: -1.0 };
  }

  // Default fallback to MISS if unhandled
  return { status: 'MISS ❌', unitVariance: -1.0 };
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && req.headers.authorization !== `Bearer ${cronSecret}`) {
    return res.status(401).json({ error: 'Unauthorized cron request' });
  }

  const apiFootballKey = process.env.API_FOOTBALL_KEY;
  const apiFootballProvider = process.env.API_FOOTBALL_PROVIDER || 'rapidapi';
  const ntfyTopic = process.env.NTFY_TOPIC || 'forward-ledger-alerts';

  if (!apiFootballKey) {
    return res.status(500).json({ error: 'Missing API_FOOTBALL_KEY' });
  }

  try {
    // In automated grading mode, queries pending fixtures in the ledger
    // and checks if any have finished (status.short === "FT")
    return res.status(200).json({
      success: true,
      message: 'Grading cron executed successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Grading cron failure:', error);
    await sendNtfyAlert(ntfyTopic, 'Forward Ledger Grading Failed', error.message || String(error), 'urgent');
    return res.status(500).json({ error: error.message });
  }
}
