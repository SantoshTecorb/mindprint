import express, { Express } from 'express';
import { Server } from 'http';
import { WhatsAppClient, InboundMessage } from './whatsapp.js';
import path from 'path';
import fs from 'fs';

export class BridgeServer {
  private app: Express;
  private server: Server | null = null;
  private sessions: Map<string, WhatsAppClient> = new Map();

  constructor(
    private port: number, 
    private baseAuthDir: string, 
    private webhookUrl: string,
    private token?: string
  ) {
    this.app = express();
    this.app.use(express.json());
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // 1. Get QR Code for a rental session
    this.app.get('/session/qr', async (req, res) => {
      const rentalId = req.query.id as string;
      if (!rentalId) return res.status(400).json({ error: 'Missing id' });

      let client = this.sessions.get(rentalId);
      if (!client) {
        const authDir = path.join(this.baseAuthDir, `session_${rentalId}`);
        if (!fs.existsSync(authDir)) fs.mkdirSync(authDir, { recursive: true });

        let lastQR = '';
        client = new WhatsAppClient({
          authDir,
          webhookUrl: this.webhookUrl,
          onMessage: (msg) => console.log(`[${rentalId}] New message from ${msg.sender}`),
          onQR: (qr) => { lastQR = qr; },
          onStatus: (status) => console.log(`[${rentalId}] Status: ${status}`),
        });
        
        this.sessions.set(rentalId, client);
        await client.connect();

        // Wait a bit for QR to generate
        let attempts = 0;
        while (!lastQR && attempts < 20) {
          await new Promise(r => setTimeout(r, 1000));
          attempts++;
        }

        if (!lastQR) return res.status(504).json({ error: 'QR timeout. Try again.' });
        return res.json({ qr: lastQR });
      }

      // If session exists, we don't return a new QR usually unless status is disconnected
      return res.json({ status: 'already_exists' });
    });

    // 2. Send Message
    this.app.post('/send', async (req, res) => {
      const { to, message, session_id } = req.body;
      const client = this.sessions.get(String(session_id));
      if (!client) return res.status(404).json({ error: `Session ${session_id} not found` });

      try {
        await client.sendMessage(`${to}@s.whatsapp.net`, message);
        res.json({ success: true });
      } catch (error) {
        res.status(500).json({ error: String(error) });
      }
    });

    // 3. Status
    this.app.get('/status', (req, res) => {
        const result: any = {};
        for(const [id, client] of this.sessions.entries()){
            result[id] = 'active'; // In a real app, track real status
        }
        res.json(result);
    });
  }

  async start(): Promise<void> {
    this.server = this.app.listen(this.port, '127.0.0.1', () => {
      console.log(`🌉 Buyer Bridge HTTP server listening on http://127.0.0.1:${this.port}`);
    });
  }

  async stop(): Promise<void> {
    if (this.server) {
      this.server.close();
    }
    for (const client of this.sessions.values()) {
      await client.disconnect();
    }
    this.sessions.clear();
  }
}
