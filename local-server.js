const https = require('https');
const { execSync } = require('child_process');

const API_BASE = 'https://navigare.onrender.com/api';
const TARGET_URL = 'https://navigare-one.vercel.app/api/proxy';

const BUISINESS_WEEKLY = 20;     // business users per week
const REGULAR_WEEKLY = 450;      // regular users per week  
const ONBOARD_RATE = 0.50;       // 50% onboarded
const INTERVAL = 60000;          // 1 minute intervals

const msPerWeek = 7 * 24 * 60 * 60 * 1000;
const perIntervalBusiness = BUISINESS_WEEKLY * INTERVAL / msPerWeek;
const perIntervalRegular = REGULAR_WEEKLY * INTERVAL / msPerWeek;

async function increment(endpoint) {
  return new Promise((resolve) => {
    const url = `${TARGET_URL}/${endpoint}`;
    https.get(url, (res) => {
      res.on('data', () => {});
      res.on('end', resolve);
    }).on('error', resolve);
  });
}

function randFloat() {
  return Math.random();
}

async function tick() {
  if (randFloat() < perIntervalBusiness / 100) {
    await increment('counters/business-client');
  }
  if (randFloat() < perIntervalRegular / 100) {
    await increment('counters/client');
  }
  if (randFloat() < ONBOARD_RATE * perIntervalRegular / 100) {
    await increment('counters/onboarded');
  }
  
  try {
    const res = await https.get(`${TARGET_URL}/counters`, (r) => {
      let d = '';
      r.on('data', c => d += c);
      r.on('end', () => console.log(`[${new Date().toISOString()}] ${d}`));
    });
  } catch {}
}

setInterval(tick, INTERVAL);
console.log('Background daemon started. Logging every minute...');
