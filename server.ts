import express from "express";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import { createServer as createViteServer } from "vite";

const app = express();
const PORT = 3000;

app.use(express.json());

// API Endpoints: Always declared first!

// 1. Live status
app.get("/api/status", (req, res) => {
  const kbDir = path.join(process.cwd(), "data", "items");
  const reportsDir = path.join(process.cwd(), "reports");

  let kbSize = 0;
  if (fs.existsSync(kbDir)) {
    try {
      kbSize = fs.readdirSync(kbDir).filter(f => f.endsWith(".json")).length;
    } catch (e) {
      kbSize = 0;
    }
  }

  let reportsCount = 0;
  if (fs.existsSync(reportsDir)) {
    try {
      reportsCount = fs.readdirSync(reportsDir).filter(f => f.endsWith(".md") && f !== "latest.md").length;
    } catch (e) {
      reportsCount = 0;
    }
  }

  const tgConfigured = !!(process.env.BOT_TOKEN && process.env.CHAT_ID) || !!(process.env.TELEGRAM_BOT_TOKEN && process.env.TELEGRAM_CHAT_ID);
  const nvidiaConfigured = !!process.env.NVIDIA_API_KEY;

  res.json({
    kbSize,
    reportsCount,
    tgConfigured,
    nvidiaConfigured,
    environment: "Cloud Run Container",
    lastRunTime: fs.existsSync(path.join(process.cwd(), "data", "pipeline_run.log"))
      ? fs.statSync(path.join(process.cwd(), "data", "pipeline_run.log")).mtime
      : null,
  });
});

// 2. Fetch Knowledge Base Items
app.get("/api/items", (req, res) => {
  const kbDir = path.join(process.cwd(), "data", "items");
  const items: any[] = [];

  if (fs.existsSync(kbDir)) {
    try {
      const files = fs.readdirSync(kbDir).filter(f => f.endsWith(".json"));
      for (const file of files) {
        const filePath = path.join(kbDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
        items.push(data);
      }
    } catch (e) {
      console.error("Error reading knowledge base items:", e);
    }
  }

  // Sort items by collected_at or publication_date descending
  items.sort((a, b) => {
    const da = new Date(a.discovered_date || a.collected_at || 0).getTime();
    const db = new Date(b.discovered_date || b.collected_at || 0).getTime();
    return db - da;
  });

  res.json(items);
});

// 3. Fetch Latest Report
app.get("/api/report", (req, res) => {
  const latestPath = path.join(process.cwd(), "reports", "latest.md");
  if (fs.existsSync(latestPath)) {
    try {
      const markdown = fs.readFileSync(latestPath, "utf-8");
      res.json({ found: true, markdown });
    } catch (e) {
      res.status(500).json({ found: false, error: "Failed to read report." });
    }
  } else {
    res.json({ found: false, markdown: "# No Daily Intelligence Report Available\n\nPlease run the pipeline to generate your first briefing." });
  }
});

// 4. Trigger Pipeline Run
app.post("/api/run", (req, res) => {
  const logDir = path.join(process.cwd(), "data");
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  const logFilePath = path.join(logDir, "pipeline_run.log");
  const logStream = fs.createWriteStream(logFilePath, { flags: "w" });

  const pyProcess = spawn("python3", ["main.py", "--run"]);

  pyProcess.stdout.on("data", (data) => {
    logStream.write(data);
    console.log(`[Python Stdout]: ${data}`);
  });

  pyProcess.stderr.on("data", (data) => {
    logStream.write(data);
    console.error(`[Python Stderr]: ${data}`);
  });

  pyProcess.on("close", (code) => {
    logStream.write(`\n--- PIPELINE RUN TERMINATED WITH CODE ${code} ---\n`);
    logStream.end();
    console.log(`Pipeline process exited with code ${code}`);
  });

  // Return immediately indicating the run has started
  res.json({ status: "started", logFile: "pipeline_run.log" });
});

// 5. Fetch Live Run Logs
app.get("/api/logs", (req, res) => {
  const logFilePath = path.join(process.cwd(), "data", "pipeline_run.log");
  if (fs.existsSync(logFilePath)) {
    try {
      const logs = fs.readFileSync(logFilePath, "utf-8");
      res.json({ logs });
    } catch (e) {
      res.status(500).json({ logs: "Failed to read pipeline execution log." });
    }
  } else {
    res.json({ logs: "No active or prior execution logs found. Trigger a pipeline run to start." });
  }
});

// Vite Middleware Integration for App Serving
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT} in ${process.env.NODE_ENV || "development"} mode`);
  });
}

startServer();
