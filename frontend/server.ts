import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';
import { initialSignals, mockEntities, mockBehaviorInsights, promptResponses, Signal } from './src/lib/data.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // In-memory data store for live persistence during container lifetime
  let liveSignals: Signal[] = [...initialSignals];

  // Initialize Gemini AI lazily
  function getGeminiClient() {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) return null;
    return new GoogleGenAI({ apiKey });
  }

  // --- PROXY API REQUESTS TO FASTAPI BACKEND ---
  app.use('/api', async (req, res) => {
    const targetUrl = `http://localhost:8000/api${req.url}`;
    try {
      const headers: Record<string, string> = {};
      if (req.headers['content-type']) {
        headers['content-type'] = req.headers['content-type'] as string;
      }
      if (req.headers.authorization) {
        headers['authorization'] = req.headers.authorization as string;
      }

      const fetchOptions: RequestInit = {
        method: req.method,
        headers,
      };

      if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(req.method) && req.body && Object.keys(req.body).length > 0) {
        fetchOptions.body = JSON.stringify(req.body);
      }

      const backendResponse = await fetch(targetUrl, fetchOptions);
      const contentType = backendResponse.headers.get('content-type') || '';
      
      res.status(backendResponse.status);
      if (contentType.includes('application/json')) {
        const data = await backendResponse.json();
        res.json(data);
      } else {
        const text = await backendResponse.text();
        res.send(text);
      }
    } catch (err: any) {
      res.status(502).json({
        error: 'FastAPI Backend Connection Error',
        details: err.message,
        tip: 'Ensure FastAPI backend is running on port 8000 (python -m uvicorn app.main:app --port 8000)',
      });
    }
  });

  // Vite Middleware integration for SPA rendering
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Signal server running on http://localhost:${PORT}`);
  });
}

startServer();
