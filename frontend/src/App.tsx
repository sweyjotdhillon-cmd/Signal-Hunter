import React, { useState, useEffect, useRef } from "react";
import {
  Cpu,
  Layers,
  FileText,
  Terminal,
  Settings,
  Search,
  Check,
  Copy,
  Play,
  Activity,
  Database,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  Eye,
  LogOut,
  Sliders,
  SlidersHorizontal,
  Bookmark,
  BookmarkCheck,
  Trash2,
  Clock,
} from "lucide-react";

interface StatusData {
  kbSize: number;
  reportsCount: number;
  nvidiaConfigured: boolean;
  environment: string;
  lastRunTime: string | null;
}

interface KBItem {
  id: string;
  unique_id?: string;
  title: string;
  url: string;
  source_type: string;
  source_name?: string;
  publication_date?: string;
  discovered_date?: string;
  summary?: string;
  tags?: string[];
  categories?: string[];
  authors?: Array<{ name: string }>;
  opportunity_score: number;
  engineering_score: number;
  scientific_score: number;
  startup_score: number;
  novelty_score: number;
  confidence_score: number;
  extra_metadata?: {
    seller_pitch?: string;
    why_it_matters?: string;
  };
  raw_metadata?: {
    seller_pitch?: string;
    why_it_matters?: string;
  };
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "report" | "kb" | "logs" | "settings">("dashboard");
  
  // Pipeline state
  const [status, setStatus] = useState<StatusData | null>(null);
  const [latestReport, setLatestReport] = useState<string>("");
  const [kbItems, setKbItems] = useState<KBItem[]>([]);
  const [liveLogs, setLiveLogs] = useState<string>("Loading execution logs...");
  const [isRunning, setIsRunning] = useState(false);
  const [selectedKBItem, setSelectedKBItem] = useState<KBItem | null>(null);
  const [copied, setCopied] = useState(false);
  const [kbSearch, setKbSearch] = useState("");
  const [reportViewMode, setReportViewMode] = useState<"styled" | "raw">("styled");

  // Watch later state
  const [watchLater, setWatchLater] = useState<string[]>([]);
  const [kbFilter, setKbFilter] = useState<"all" | "watch_later">("all");

  // Credentials form state
  const [nvidiaApiKey, setNvidiaApiKey] = useState("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [resetStatus, setResetStatus] = useState<"idle" | "resetting" | "success" | "error">("idle");

  const logEndRef = useRef<HTMLDivElement>(null);

  // Fetch status, report, and KB items on startup
  const refreshAllData = async () => {
    try {
      const statusRes = await fetch("/api/status");
      if (statusRes.ok) {
        const data = await statusRes.json();
        setStatus(data);
      }

      const reportRes = await fetch("/api/report");
      if (reportRes.ok) {
        const data = await reportRes.json();
        setLatestReport(data.markdown || "");
      }

      const kbRes = await fetch("/api/items");
      if (kbRes.ok) {
        const data = await kbRes.json();
        setKbItems(data || []);
      }

      const logsRes = await fetch("/api/logs");
      if (logsRes.ok) {
        const data = await logsRes.json();
        setLiveLogs(data.logs || "");
      }
    } catch (e) {
      console.error("Failed to fetch pipeline data:", e);
    }
  };

  useEffect(() => {
    refreshAllData();

    // Load Local Storage values
    try {
      const savedKey = localStorage.getItem("nvidia_api_key") || "";
      setNvidiaApiKey(savedKey);

      const savedWatchLater = localStorage.getItem("signal_hunter_watch_later");
      if (savedWatchLater) {
        setWatchLater(JSON.parse(savedWatchLater));
      }
    } catch (e) {
      console.error("Error loading localStorage items:", e);
    }
  }, []);

  // Automatically clear save status badge
  useEffect(() => {
    if (saveStatus === "success") {
      const timer = setTimeout(() => setSaveStatus("idle"), 2000);
      return () => clearTimeout(timer);
    }
  }, [saveStatus]);

  // Poll logs and status during active pipeline execution
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRunning) {
      interval = setInterval(async () => {
        try {
          const logsRes = await fetch("/api/logs");
          if (logsRes.ok) {
            const data = await logsRes.json();
            setLiveLogs(data.logs || "");
            
            // Auto scroll logs during execution
            if (logEndRef.current) {
              logEndRef.current.scrollIntoView({ behavior: "smooth" });
            }

            // Stop polling if the python run reports termination
            if (data.logs.includes("PIPELINE RUN TERMINATED") || data.logs.includes("Pipeline execution successfully completed") || data.logs.includes("Pipeline failed")) {
              setIsRunning(false);
              refreshAllData();
            }
          }
        } catch (e) {
          console.error("Failed polling logs:", e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  // Handle run trigger
  const handleTriggerPipeline = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLiveLogs("Initializing Python Signal Hunter execution runtime...\n");
    setActiveTab("logs"); // Auto route to logs so operator sees stdout
    
    try {
      const localKey = localStorage.getItem("nvidia_api_key") || "";
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nvidiaApiKey: localKey }),
      });
      if (!res.ok) {
        setIsRunning(false);
        setLiveLogs((prev) => prev + "[-] Failed to contact backend server execution endpoint.");
      }
    } catch (err) {
      setIsRunning(false);
      setLiveLogs((prev) => prev + `[-] Error spawning process: ${err}`);
    }
  };

  const handleSaveCredentials = async () => {
    setSaveStatus("saving");
    try {
      localStorage.setItem("nvidia_api_key", nvidiaApiKey);
      setSaveStatus("success");
      setTimeout(() => setSaveStatus("idle"), 3000);
      refreshAllData(); // reload status
    } catch (e) {
      setSaveStatus("error");
    }
  };

  const handleResetData = async () => {
    if (!window.confirm("Are you absolutely sure you want to clear all research papers, reports, and logs? This action cannot be undone.")) {
      return;
    }
    setResetStatus("resetting");
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      if (res.ok) {
        setResetStatus("success");
        setSelectedKBItem(null);
        setTimeout(() => setResetStatus("idle"), 3000);
        await refreshAllData();
      } else {
        setResetStatus("error");
      }
    } catch (e) {
      setResetStatus("error");
    }
  };

  const toggleWatchLater = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setWatchLater((prev) => {
      const updated = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      localStorage.setItem("signal_hunter_watch_later", JSON.stringify(updated));
      return updated;
    });
  };

  const handleCopyReport = () => {
    navigator.clipboard.writeText(latestReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter KB items
  const filteredKBItems = kbItems.filter(item => {
    const q = kbSearch.toLowerCase();
    const matchesSearch = (
      item.title.toLowerCase().includes(q) ||
      (item.summary && item.summary.toLowerCase().includes(q)) ||
      item.id.toLowerCase().includes(q)
    );
    if (kbFilter === "watch_later") {
      return matchesSearch && watchLater.includes(item.id);
    }
    return matchesSearch;
  });

  return (
    <div id="signal_hunter_app" className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500/30 selection:text-teal-200">
      
      {/* HEADER */}
      <header id="main_header" className="border-b border-slate-900 bg-slate-950 px-4 sm:px-6 py-3.5 flex items-center justify-between gap-4 sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-tr from-teal-600 to-emerald-500 rounded-lg shadow-lg shadow-teal-900/10">
            <Cpu className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm sm:text-md font-bold tracking-tight text-white uppercase">
                Signal Hunter
              </h1>
              <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-teal-950 text-teal-400 border border-teal-900/50 rounded-full">
                MVP v1.0.0
              </span>
            </div>
            <p className="text-[10px] sm:text-xs text-slate-400">Developer Operations & Ingest Control Panel</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            id="run_pipeline_header_btn"
            onClick={handleTriggerPipeline}
            disabled={isRunning}
            className="flex items-center space-x-2 px-2.5 sm:px-3 py-1.5 bg-teal-600 hover:bg-teal-500 disabled:bg-slate-900 disabled:text-slate-500 text-white rounded-md text-xs font-semibold transition active:scale-95 cursor-pointer"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span className="hidden xs:inline">Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Pipeline</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* NAVIGATION TABS */}
      <nav id="nav_tabs" className="border-b border-slate-900 bg-slate-950 px-4 sm:px-6 py-2 flex flex-wrap items-center gap-1.5">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer ${
            activeTab === "dashboard" ? "bg-slate-900 text-teal-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Dashboard</span>
        </button>

        <button
          onClick={() => setActiveTab("report")}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer ${
            activeTab === "report" ? "bg-slate-900 text-teal-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Today's Report</span>
        </button>

        <button
          onClick={() => setActiveTab("kb")}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer ${
            activeTab === "kb" ? "bg-slate-900 text-teal-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Knowledge Base</span>
        </button>

        <button
          onClick={() => setActiveTab("logs")}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer ${
            activeTab === "logs" ? "bg-slate-900 text-teal-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="w-4 h-4" />
          <span>Pipeline Logs</span>
        </button>

        <button
          onClick={() => setActiveTab("settings")}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer ${
            activeTab === "settings" ? "bg-slate-900 text-teal-400" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </button>
      </nav>

      {/* VIEWPORT AREA */}
      <main id="app_viewport" className="flex-1 p-4 sm:p-6 overflow-y-auto lg:overflow-hidden">
        
        {/* TAB 1: DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Real stats row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900/60 border border-slate-900 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Knowledge Base</span>
                  <span className="text-xl font-bold font-mono text-teal-400">{status ? status.kbSize : "0"}</span>
                  <span className="text-[9px] text-slate-400 block mt-1">Unique articles saved</span>
                </div>
                <Database className="w-8 h-8 text-slate-700" />
              </div>

              <div className="bg-slate-900/60 border border-slate-900 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Generated Reports</span>
                  <span className="text-xl font-bold font-mono text-emerald-400">{status ? status.reportsCount : "0"}</span>
                  <span className="text-[9px] text-slate-400 block mt-1">Briefings compiled to reports/</span>
                </div>
                <FileText className="w-8 h-8 text-slate-700" />
              </div>

              <div className="bg-slate-900/60 border border-slate-900 p-4 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">NVIDIA Opportunity LLM</span>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-block mt-2 font-mono ${(nvidiaApiKey || status?.nvidiaConfigured) ? "bg-emerald-950 text-emerald-400 border border-emerald-900" : "bg-rose-950/60 text-rose-400 border border-rose-900/60"}`}>
                    {(nvidiaApiKey || status?.nvidiaConfigured) ? "CONFIGURED (LOCAL KEY)" : "NOT ACTIVE"}
                  </span>
                </div>
                <Cpu className="w-6 h-6 text-slate-700" />
              </div>
            </div>

            {/* Run Pipeline CTA */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-4 bg-slate-900/20 border border-slate-900/60 p-6 rounded-lg flex flex-col justify-between space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide">Signal pipeline trigger</h3>
                  <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                    Instantly invoke the multi-stage discovery system. The engine queries arXiv, normalizes inputs, applies quality filters, scores opportunities, and writes reports.
                  </p>
                </div>
                <button
                  onClick={handleTriggerPipeline}
                  disabled={isRunning}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-semibold text-xs tracking-wider uppercase rounded-md shadow transition disabled:opacity-50 cursor-pointer"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>PROSPECTOR BUSY...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-white" />
                      <span>Execute pipeline run</span>
                    </>
                  )}
                </button>
              </div>

              {/* Status checklist */}
              <div className="lg:col-span-8 bg-slate-900/40 border border-slate-900 p-6 rounded-lg">
                <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400 mb-4 flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-teal-400" />
                  <span>System Telemetry Checklists</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-2 border-r border-slate-900 pr-4">
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Source Registry Ingestion (arXiv)</span>
                      <span className="text-[10px] text-emerald-400 font-bold">READY (ONLINE)</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Signal Normalizer & Verifier</span>
                      <span className="text-[10px] text-emerald-400 font-bold">STRICT CORES READY</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Strategic Scorer</span>
                      <span className="text-[10px] text-emerald-400 font-bold">MOCK VECTORS READY</span>
                    </div>
                  </div>

                  <div className="space-y-2 pl-2">
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Operating Platform</span>
                      <span className="text-[10px] text-slate-400 font-mono">{status ? status.environment : "Linux"}</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Last Operational Ingestion</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {status?.lastRunTime ? new Date(status.lastRunTime).toLocaleString() : "Never"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TODAY'S REPORT */}
        {activeTab === "report" && (
          <div className="h-[600px] lg:h-[calc(100vh-12rem)] flex flex-col space-y-4">
            <div className="flex items-center justify-between bg-slate-900/40 border border-slate-900 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-teal-400" />
                <span className="text-xs font-semibold text-slate-200">daily_intelligence_brief_latest.md</span>
              </div>

              <div className="flex items-center space-x-2">
                <div className="bg-slate-950 p-0.5 rounded border border-slate-800 flex text-xs">
                  <button
                    onClick={() => setReportViewMode("styled")}
                    className={`px-2 py-0.5 rounded font-medium cursor-pointer ${reportViewMode === "styled" ? "bg-slate-900 text-teal-400" : "text-slate-500"}`}
                  >
                    Styled View
                  </button>
                  <button
                    onClick={() => setReportViewMode("raw")}
                    className={`px-2 py-0.5 rounded font-medium cursor-pointer ${reportViewMode === "raw" ? "bg-slate-900 text-teal-400" : "text-slate-500"}`}
                  >
                    Raw Markdown
                  </button>
                </div>

                <button
                  onClick={handleCopyReport}
                  className="flex items-center space-x-1 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] text-slate-300 rounded cursor-pointer"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400 font-bold">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy MD</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="flex-1 bg-slate-900/10 border border-slate-900 p-6 rounded-lg overflow-y-auto">
              {reportViewMode === "raw" ? (
                <pre className="font-mono text-xs whitespace-pre-wrap leading-relaxed text-slate-400 bg-black/40 p-4 rounded-lg select-text">
                  {latestReport}
                </pre>
              ) : (
                <div className="prose prose-invert max-w-none text-slate-300 space-y-6 text-xs leading-relaxed select-text">
                  {/* Basic custom renderer to style markdown headers and lists cleanly */}
                  {latestReport.split("\n").map((line, idx) => {
                    if (line.startsWith("# ")) {
                      return <h1 key={idx} className="text-lg font-extrabold text-white tracking-tight border-b border-slate-900 pb-3 mt-4">{line.replace("# ", "")}</h1>;
                    }
                    if (line.startsWith("## ")) {
                      return <h2 key={idx} className="text-sm font-bold text-teal-400 uppercase tracking-wider mt-6 mb-2 border-l-2 border-teal-500 pl-2">{line.replace("## ", "")}</h2>;
                    }
                    if (line.startsWith("### ")) {
                      return <h3 key={idx} className="text-xs font-bold text-slate-200 mt-4">{line.replace("### ", "")}</h3>;
                    }
                    if (line.startsWith("- ")) {
                      return (
                        <div key={idx} className="flex items-start space-x-2 pl-4 py-0.5">
                          <span className="text-teal-500 select-none">•</span>
                          <span>{line.replace("- ", "")}</span>
                        </div>
                      );
                    }
                    if (line.startsWith("> ")) {
                      return (
                        <blockquote key={idx} className="border-l-2 border-slate-800 pl-4 py-1 italic text-slate-400 bg-slate-900/20 rounded-r-md">
                          {line.replace("> ", "")}
                        </blockquote>
                      );
                    }
                    if (line.trim() === "---") {
                      return <hr key={idx} className="border-slate-900 my-4" />;
                    }
                    return line.trim() ? <p key={idx} className="leading-relaxed">{line}</p> : null;
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: KNOWLEDGE BASE */}
        {activeTab === "kb" && (
          <div className="flex flex-col lg:grid lg:grid-cols-12 gap-6 h-[750px] lg:h-[calc(100vh-12rem)] overflow-hidden">
            {/* Left list (5 cols) */}
            <div className="lg:col-span-5 flex flex-col space-y-4 overflow-hidden h-[300px] lg:h-full">
              <div className="space-y-3">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={kbSearch}
                    onChange={(e) => setKbSearch(e.target.value)}
                    placeholder="Search articles & vectors..."
                    className="w-full bg-slate-900 border border-slate-900 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500 placeholder:text-slate-500"
                  />
                </div>

                <div className="flex bg-slate-900/60 p-0.5 rounded-lg border border-slate-900 text-xs">
                  <button
                    onClick={() => setKbFilter("all")}
                    className={`flex-1 py-1 rounded-md font-medium text-center cursor-pointer transition ${
                      kbFilter === "all" ? "bg-slate-950 text-teal-400 font-semibold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    All Papers ({kbItems.length})
                  </button>
                  <button
                    onClick={() => setKbFilter("watch_later")}
                    className={`flex-1 py-1 rounded-md font-medium text-center cursor-pointer transition flex items-center justify-center space-x-1.5 ${
                      kbFilter === "watch_later" ? "bg-slate-950 text-teal-400 font-semibold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                    <span>Watch Later ({watchLater.length})</span>
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto border border-slate-900 rounded-lg divide-y divide-slate-900 bg-slate-950">
                {filteredKBItems.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-600 font-mono">
                    {kbFilter === "watch_later"
                      ? "No watch later items bookmarked yet."
                      : "No stored breakthrough signals found. Run a pipeline ingestion loop."}
                  </div>
                ) : (
                  filteredKBItems.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedKBItem(item)}
                      className={`w-full text-left p-4 hover:bg-slate-900/40 transition flex flex-col space-y-1.5 cursor-pointer border-b border-slate-900/30 ${
                        selectedKBItem?.id === item.id ? "bg-teal-950/20 border-l-2 border-teal-500" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono text-slate-500">{item.id}</span>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={(e) => toggleWatchLater(item.id, e)}
                            className="text-slate-500 hover:text-teal-400 p-0.5 transition cursor-pointer"
                            title={watchLater.includes(item.id) ? "Remove from Watch Later" : "Add to Watch Later"}
                          >
                            {watchLater.includes(item.id) ? (
                              <BookmarkCheck className="w-4 h-4 text-teal-400 fill-teal-400/20" />
                            ) : (
                              <Bookmark className="w-4 h-4" />
                            )}
                          </button>
                          <span className="text-[10px] font-mono font-bold bg-emerald-950 text-emerald-400 px-1.5 py-0.2 rounded">
                            Opp: {item.opportunity_score.toFixed(2)}
                          </span>
                        </div>
                      </div>
                      <h4 className="text-xs font-semibold text-slate-200 line-clamp-1">{item.title}</h4>
                      <div className="flex items-center space-x-2 text-[10px] text-slate-400">
                        <span className="bg-slate-900 px-1.5 py-0.5 rounded text-[9px] uppercase border border-slate-800">
                          {item.source_type}
                        </span>
                        <span>•</span>
                        <span>{item.authors?.[0]?.name || "Unknown Author"}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right details visualizer (7 cols) */}
            <div className="lg:col-span-7 border border-slate-900 rounded-lg bg-slate-950 p-4 sm:p-6 overflow-y-auto flex flex-col h-[426px] lg:h-full">
              {selectedKBItem ? (
                <div className="space-y-6 text-xs leading-relaxed select-text">
                  <div className="border-b border-slate-900 pb-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-slate-500 uppercase">Knowledge Base Record ID: {selectedKBItem.id}</span>
                      
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={(e) => toggleWatchLater(selectedKBItem.id, e)}
                          className={`flex items-center space-x-1 px-2.5 py-1 rounded text-[11px] font-medium border transition cursor-pointer ${
                            watchLater.includes(selectedKBItem.id)
                              ? "bg-teal-950/40 border-teal-800/80 text-teal-400"
                              : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          {watchLater.includes(selectedKBItem.id) ? (
                            <>
                              <BookmarkCheck className="w-3.5 h-3.5 fill-teal-400/10" />
                              <span>Saved to Watch Later</span>
                            </>
                          ) : (
                            <>
                              <Bookmark className="w-3.5 h-3.5" />
                              <span>Add to Watch Later</span>
                            </>
                          )}
                        </button>

                        <a
                          href={selectedKBItem.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center space-x-1 text-teal-400 hover:text-teal-300 font-medium"
                        >
                          <span>Original link</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>
                    <h3 className="text-md font-bold text-white leading-tight">{selectedKBItem.title}</h3>
                    <p className="text-[10px] text-slate-400">
                      By {selectedKBItem.authors?.map(a => a.name).join(", ") || "No authors parsed"}
                    </p>
                  </div>

                  {/* Pitching details */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-teal-950/10 border border-teal-900/20 rounded-lg space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-teal-400 block tracking-wider">Seller Pitch</span>
                      <p className="text-slate-300 italic">
                        "{selectedKBItem.extra_metadata?.seller_pitch || selectedKBItem.raw_metadata?.seller_pitch || "Standard architectural acceleration benefit."}"
                      </p>
                    </div>

                    <div className="p-4 bg-emerald-950/10 border border-emerald-900/20 rounded-lg space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-emerald-400 block tracking-wider">Why It Matters</span>
                      <p className="text-slate-300">
                        {selectedKBItem.extra_metadata?.why_it_matters || selectedKBItem.raw_metadata?.why_it_matters || "Addresses core sequential scaling limits cleanly."}
                      </p>
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="space-y-2">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Canonical Summary</span>
                    <p className="text-slate-300 bg-slate-950/60 p-4 rounded-lg border border-slate-900">
                      {selectedKBItem.summary || "No technical summary generated."}
                    </p>
                  </div>

                  {/* Scores */}
                  <div className="space-y-3">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block tracking-wider">Pipeline score card vectors</span>
                    
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
                      <div className="bg-slate-900/60 p-3 rounded border border-slate-900">
                        <span className="text-[9px] text-slate-500 uppercase block">Viability</span>
                        <span className="text-sm font-bold font-mono text-teal-400">{selectedKBItem.opportunity_score.toFixed(2)}</span>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded border border-slate-900">
                        <span className="text-[9px] text-slate-500 uppercase block">Engineering</span>
                        <span className="text-sm font-bold font-mono text-teal-400">{selectedKBItem.engineering_score.toFixed(2)}</span>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded border border-slate-900">
                        <span className="text-[9px] text-slate-500 uppercase block">Scientific</span>
                        <span className="text-sm font-bold font-mono text-teal-400">{selectedKBItem.scientific_score.toFixed(2)}</span>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded border border-slate-900">
                        <span className="text-[9px] text-slate-500 uppercase block">Startup Fit</span>
                        <span className="text-sm font-bold font-mono text-teal-400">{selectedKBItem.startup_score.toFixed(2)}</span>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded border border-slate-900">
                        <span className="text-[9px] text-slate-500 uppercase block">Novelty</span>
                        <span className="text-sm font-bold font-mono text-teal-400">{selectedKBItem.novelty_score.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-600 text-center select-none">
                  <Database className="w-12 h-12 text-slate-800 mb-3" />
                  <p className="text-xs max-w-xs font-mono text-slate-500">
                    Select a knowledge base article from the list to view granular viability scores, technical pitches, and core summaries.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: PIPELINE LOGS */}
        {activeTab === "logs" && (
          <div className="h-[500px] lg:h-[calc(100vh-12rem)] flex flex-col space-y-4">
            <div className="px-5 py-3.5 border border-slate-900 bg-slate-950 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-teal-400 animate-pulse" />
                <span className="text-xs uppercase font-bold tracking-wider text-slate-300">Live Python Runtime logs</span>
              </div>

              {isRunning && (
                <div className="flex items-center space-x-2 text-teal-400 font-mono text-xs animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-teal-400"></span>
                  <span>EXECUTING AUTOMATED PIPELINE</span>
                </div>
              )}
            </div>

            <div className="flex-1 bg-black p-5 font-mono text-[10px] text-slate-400 overflow-y-auto flex flex-col space-y-1 rounded-lg border border-slate-950 select-text">
              {liveLogs.split("\n").map((line, idx) => {
                let color = "text-slate-400";
                if (line.includes("ERROR") || line.includes("failed")) color = "text-rose-400 font-bold";
                else if (line.includes("WARNING")) color = "text-amber-400";
                else if (line.includes("VERIFIED")) color = "text-emerald-400 font-semibold";
                else if (line.includes("SUCCESSFUL") || line.includes("completed")) color = "text-teal-400 font-bold";
                else if (line.includes("===")) color = "text-white font-extrabold";
                else if (line.includes("Stage")) color = "text-indigo-400 font-bold";

                return (
                  <div key={idx} className={`leading-relaxed whitespace-pre-wrap ${color}`}>
                    {line}
                  </div>
                );
              })}
              <div ref={logEndRef} />
            </div>
          </div>
        )}

        {/* TAB 5: SETTINGS */}
        {activeTab === "settings" && (
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="bg-slate-900/40 border border-slate-900 p-6 rounded-lg space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-teal-400" />
                <span>Operational Environment Settings</span>
              </h3>

              <div className="space-y-4 text-xs">
                <div className="p-4 bg-slate-950 rounded-lg border border-slate-900 space-y-2">
                  <span className="font-semibold text-slate-300">Configuration Source Directory</span>
                  <p className="text-slate-400 font-mono text-[10px]">/app/applet/signal-hunter/config/settings.yaml</p>
                </div>

                <div className="p-4 bg-slate-950 rounded-lg border border-slate-900 space-y-2">
                  <span className="font-semibold text-slate-300">Knowledge Base Files Directory</span>
                  <p className="text-slate-400 font-mono text-[10px]">/app/applet/data/items/*.json</p>
                </div>

                <div className="p-4 bg-slate-950 rounded-lg border border-slate-900 space-y-2">
                  <span className="font-semibold text-slate-300">Briefings Reports Target Path</span>
                  <p className="text-slate-400 font-mono text-[10px]">/app/applet/reports/*.md</p>
                </div>
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-900 p-6 rounded-lg space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center space-x-2">
                <Settings className="w-4 h-4 text-teal-400" />
                <span>Integration Credentials Configuration</span>
              </h3>

              <div className="space-y-4 text-xs">
                <div className="space-y-1">
                  <label className="block font-semibold text-slate-300">NVIDIA API Key</label>
                  <input
                    type="password"
                    value={nvidiaApiKey}
                    onChange={(e) => {
                      const val = e.target.value;
                      setNvidiaApiKey(val);
                      localStorage.setItem("nvidia_api_key", val);
                      setSaveStatus("success");
                    }}
                    placeholder="Enter nvapi-... key"
                    className="w-full bg-slate-950 border border-slate-900 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500 font-mono text-[11px]"
                  />
                  <p className="text-[10px] text-slate-500">Required to enable the NVIDIA Opportunity LLM analyzer stage.</p>
                </div>

                <div className="pt-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-emerald-400 text-xs font-medium">
                    {nvidiaApiKey ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Stored securely in browser Local Storage only</span>
                      </>
                    ) : (
                      <span className="text-amber-400">No key stored yet. Add your key above to enable NVIDIA Analysis.</span>
                    )}
                  </div>

                  {saveStatus === "success" && (
                    <span className="text-teal-400 font-mono text-[10px] bg-teal-950/40 px-2 py-0.5 rounded border border-teal-900/30">
                      Auto-saved!
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-900 p-6 rounded-lg space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide flex items-center space-x-2">
                <Trash2 className="w-4 h-4 text-rose-400" />
                <span>Reset Application Research Data</span>
              </h3>

              <div className="space-y-4 text-xs">
                <p className="text-slate-400 leading-relaxed">
                  Reset the local knowledge base, clear all research papers, wipe today's briefing report, and purge the pipeline logs. This option will permanently start the application over with fresh, clean states.
                </p>

                <div className="pt-2 flex items-center justify-between">
                  <button
                    onClick={handleResetData}
                    disabled={resetStatus === "resetting"}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:bg-slate-900 disabled:text-slate-500 text-white font-semibold text-xs tracking-wider uppercase rounded-md transition cursor-pointer"
                  >
                    {resetStatus === "resetting" ? "Resetting Data..." : "Reset Research Data"}
                  </button>

                  {resetStatus === "success" && (
                    <span className="text-emerald-400 font-semibold text-xs flex items-center space-x-1">
                      <Check className="w-4 h-4" />
                      <span>Data successfully cleared!</span>
                    </span>
                  )}

                  {resetStatus === "error" && (
                    <span className="text-rose-400 font-semibold text-xs flex items-center space-x-1">
                      <AlertCircle className="w-4 h-4" />
                      <span>Failed to reset data.</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 bg-teal-950/10 border border-teal-900/20 text-xs text-slate-400 rounded-lg flex items-start space-x-3">
              <AlertCircle className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
              <p>
                Credentials saved via this UI are stored strictly on your local browser's secure device storage, meaning your API key remains completely private and is never stored on the server filesystem or committed to any codebase.
              </p>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
