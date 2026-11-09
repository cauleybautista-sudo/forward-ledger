import type { VercelRequest, VercelResponse } from '@vercel/node';
import * as fs from 'fs';
import * as path from 'path';

interface FixtureOdds {
  matchId: number;
  fixture: string;
  kickoffTime: string;
  competition: string;
  marketSelection: string;
  modelProb: number;
  closingOdds: number;
  impliedProb: number;
  calculatedEdge: number;
}

// Send alert to ntfy.sh
async function sendNtfyAlert(topic: string, title: string, message: string, priority: 'default' | 'high' | 'urgent' = 'default') {
  if (!topic) return;
  try {
    await fetch(`https://ntfy.sh/${topic}`, {
      method: 'POST',
      headers: {
        'Title': title,
        'Priority': priority,
        'Tags': priority === 'urgent' ? 'warning,rotating_light' : 'soccer,chart_with_upwards_trend'
      },
      body: message
    });
  } catch (err) {
    console.error('Failed to dispatch ntfy alert:', err);
  }
}

// Fetch upcoming fixtures from API-Football
async function fetchUpcomingFixtures(apiKey: string, provider: string): Promise<any[]> {
  const isDirect = provider.toLowerCase() === 'direct';
  const url = isDirect
    ? 'https://v3.football.api-sports.io/fixtures?next=20'
    : 'https://api-football-v1.p.rapidapi.com/v3/fixtures?next=20';

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
  return data.response || [];
}

// Fetch closing odds from The Odds API
async function fetchOddsFromOddsApi(apiKey: string, sportKey: string = 'soccer_uefa_nations_league'): Promise<any[]> {
  const url = `https://api.the-odds-api.com/v4/sports/${sportKey}/odds/?apiKey=${apiKey}&regions=eu,us&markets=h2h,totals&oddsFormat=decimal`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`The Odds API error: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Optional Vercel Cron Secret Authentication
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && req.headers.authorization !== `Bearer ${cronSecret}`) {
    return res.status(401).json({ error: 'Unauthorized cron request' });
  }

  const apiFootballKey = process.env.API_FOOTBALL_KEY;
  const apiFootballProvider = process.env.API_FOOTBALL_PROVIDER || 'rapidapi';
  const oddsApiKey = process.env.ODDS_API_KEY;
  const ntfyTopic = process.env.NTFY_TOPIC || 'forward-ledger-alerts';

  if (!apiFootballKey || !oddsApiKey) {
    const errorMsg = 'Missing API_FOOTBALL_KEY or ODDS_API_KEY in environment variables.';
    await sendNtfyAlert(ntfyTopic, 'Forward Ledger Error: Config Missing', errorMsg, 'high');
    return res.status(500).json({ error: errorMsg });
  }

  try {
    // 1. Check upcoming matches
    const upcoming = await fetchUpcomingFixtures(apiFootballKey, apiFootballProvider);
    console.log(`Fetched ${upcoming.length} upcoming fixtures from API-Football.`);

    // 2. Filter for matches starting within ~10 to 30 minutes to lock closing odds
    const now = Date.now();
    const targetFixtures = upcoming.filter((f: any) => {
      const kickoff = new Date(f.fixture.date).getTime();
      const diffMinutes = (kickoff - now) / (1000 * 60);
      return diffMinutes >= -5 && diffMinutes <= 30;
    });

    console.log(`Found ${targetFixtures.length} matches within closing odds window.`);

    return res.status(200).json({
      success: true,
      message: 'Pre-kickoff cron executed successfully',
      upcomingCount: upcoming.length,
      closingWindowCount: targetFixtures.length,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Pre-kickoff cron execution failure:', error);
    await sendNtfyAlert(ntfyTopic, 'Forward Ledger Cron Failed', error.message || String(error), 'urgent');
    return res.status(500).json({ error: error.message || 'Cron execution failed' });
  }
}
