#!/usr/bin/env node
/**
 * nanobot WhatsApp Bridge - Buyer Omnichannel Version
 * 
 * This bridge connects WhatsApp to the MindPrint backend
 * via HTTP webhooks. It supports multiple sessions (one per rental).
 */

// Polyfill crypto for Baileys in ESM
import { webcrypto } from 'crypto';
if (!globalThis.crypto) {
  (globalThis as any).crypto = webcrypto;
}

import { BridgeServer } from './server.js';
import { homedir } from 'os';
import { join } from 'path';

const PORT = parseInt(process.env.BRIDGE_PORT || '3001', 10);
const AUTH_DIR = process.env.AUTH_DIR || join(homedir(), '.nanobot', 'buyer-whatsapp-auth');
const TOKEN = process.env.BRIDGE_TOKEN || undefined;
const WEBHOOK_URL = process.env.MINDPRINT_API_URL || 'http://localhost:5000/api/whatsapp/webhook';

console.log('🐈 nanobot Buyer WhatsApp Bridge');
console.log('=============================\n');
console.log(`Webhook URL: ${WEBHOOK_URL}`);

const server = new BridgeServer(PORT, AUTH_DIR, WEBHOOK_URL, TOKEN);

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\nShutting down...');
  await server.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await server.stop();
  process.exit(0);
});

// Start the server
server.start().catch((error) => {
  console.error('Failed to start bridge:', error);
  process.exit(1);
});
