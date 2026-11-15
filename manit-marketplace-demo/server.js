require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 8080;

// Read config from env or defaults
const SOC_API_URL = process.env.SOC_API_URL || 'http://localhost:8000/api/v1/events';
const SOC_API_KEY = process.env.SOC_API_KEY;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Simple API proxy to send events to SentinelSOC
app.post('/api/telemetry', async (req, res) => {
  if (!SOC_API_KEY) {
    console.warn('WARNING: SOC_API_KEY is not set. Events are not being sent to the SOC.');
    return res.status(200).json({ status: 'ignored', reason: 'No API Key' });
  }

  try {
    // Support X-Forwarded-For for safe test harness IP spoofing
    const forwardedFor = req.headers['x-forwarded-for'];
    const clientIp = forwardedFor ? forwardedFor.split(',')[0].trim() : req.ip;
    
    const payload = {
      ...req.body,
      timestamp: new Date().toISOString(),
      source_ip: req.body.source_ip || (clientIp === '::1' ? '127.0.0.1' : clientIp)
    };

    console.log(`Sending ${payload.event_type} to SOC...`);
    
    await axios.post(SOC_API_URL, payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': SOC_API_KEY
      }
    });

    res.status(200).json({ status: 'sent' });
  } catch (error) {
    console.error('Failed to send event to SOC:', error.response?.data || error.message);
    res.status(500).json({ error: 'SOC integration failed' });
  }
});

app.listen(PORT, () => {
  console.log(`MANIT Marketplace Demo running at http://localhost:${PORT}`);
  console.log(`SOC API URL: ${SOC_API_URL}`);
  console.log(`SOC API Key Configured: ${SOC_API_KEY ? 'Yes' : 'No'}`);
});
