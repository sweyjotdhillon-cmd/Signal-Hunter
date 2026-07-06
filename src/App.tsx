import { useState, useEffect, useRef } from "react";
import {
  Folder,
  FolderOpen,
  File,
  Download,
  Play,
  CheckCircle2,
  XCircle,
  Info,
  Terminal,
  ArrowRight,
  Settings,
  Search,
  Copy,
  Check,
  Cpu,
  Layers,
  FileText,
  BookOpen,
  Sparkles,
  Smartphone,
  ChevronRight,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import JSZip from "jszip";
import { PYTHON_PROJECT_FILES, ProjectFile } from "./code_data";

export default function App() {
  // Navigation & File Explorer state
  const [selectedFile, setSelectedFile] = useState<ProjectFile>(
    PYTHON_PROJECT_FILES.find((f) => f.path === "README.md") || PYTHON_PROJECT_FILES[0]
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedFile, setCopiedFile] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [activeSection, setActiveSection] = useState<"code" | "execution">("code");

  // Folder collapse states
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    config: true,
    collectors: true,
    analyzers: false,
    verifier: false,
    memory: true,
    delivery: false,
    models: true,
    utils: false,
    tests: false,
  });

  // Pipeline execution state
  const [isSimulating, setIsSimulating] = useState(false);
  const [simStep, setSimStep] = useState<"idle" | "config" | "collect" | "analyze" | "verify" | "store" | "deliver" | "done">("idle");
  const [simLogs, setSimLogs] = useState<string[]>([]);
  const [simulatedRunCount, setSimulatedRunCount] = useState(0);
  const [reportTab, setReportTab] = useState<"briefing" | "markdown" | "signals">("briefing");

  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll console to bottom
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [simLogs]);

  // Handle Copy file content
  const handleCopyCode = () => {
    navigator.clipboard.writeText(selectedFile.content);
    setCopiedFile(true);
    setTimeout(() => setCopiedFile(false), 2000);
  };

  // Toggle folder expansion
  const toggleFolder = (folder: string) => {
    setExpandedFolders((prev) => ({ ...prev, [folder]: !prev[folder] }));
  };

  // Run mock python simulation
  const handleSimulatePipeline = () => {
    if (isSimulating) return;

    setIsSimulating(true);
    setSimStep("config");
    setSimLogs([]);
    
    const logs = [
      "Starting pipeline: python main.py --dry-run",
      "Initializing environment variables... APP_URL, GEMINI_API_KEY detected.",
      "Searching configuration candidate locations...",
      "Loaded default pipeline configuration from: config/settings.yaml",
      "System initialized. Logging Level set to INFO. Logs will write to logs/signal_hunter.log",
      "=========================================",
      "   Starting Signal Hunter Intelligence   ",
      "=========================================",
      "Application: Signal Hunter v1.0.0-Beta",
      "Initializing core memory module: JSONMemoryStore with local target path 'data/items/'",
      "Bootstrapping AI Cognitive Analyzer: DummyAnalyzer with template 'gemini-2.5-flash'",
      "Bootstrapping Quality Gatekeeper: SignalVerifier (Min Score: 0.75, Strict: True)",
      "Bootstrapping Delivery Transport: MarkdownReporter configured for path 'reports/'"
    ];

    let currentLogIdx = 0;
    
    // Step 1: Config
    const interval = setInterval(() => {
      if (currentLogIdx < logs.length) {
        setSimLogs((prev) => [...prev, logs[currentLogIdx]]);
        currentLogIdx++;
      } else {
        clearInterval(interval);
        
        // Step 2: Collection
        setTimeout(() => {
          setSimStep("collect");
          setSimLogs((prev) => [
            ...prev,
            "[COLLECTION] Starting active crawlers...",
            "[COLLECTION] Running dry-run mode. Bypassing active internet calls.",
            "[COLLECTION] Ingesting mock signal feeds...",
            "[COLLECTION] candidate ingested: [LoRA paper] (https://arxiv.org/abs/2106.09685)",
            "[COLLECTION] candidate ingested: [vLLM repository] (https://github.com/vllm-project/vllm)",
            "[COLLECTION] candidate ingested: [Frontier safety blog] (https://openai.com/blog/frontier-risk-preparedness)",
            `[COLLECTION] Successfully ingested 3 candidate(s) into pipeline memory buffers.`
          ]);

          // Step 3: Analysis
          setTimeout(() => {
            setSimStep("analyze");
            setSimLogs((prev) => [
              ...prev,
              "[ANALYSIS] Invoking AI Cognitive Analyzers for content parsing...",
              "[ANALYSIS] [1/3] Enriched item 'LoRA: Low-Rank Adaptation of Large Language Models' using Gemini model...",
              "[ANALYSIS] [1/3] Extracted breakthrough signals: 'Adapter fine-tuning framework', 'Low-Rank neural adapter strategy'",
              "[ANALYSIS] [2/3] Enriched item 'vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention' using Gemini model...",
              "[ANALYSIS] [2/3] Extracted breakthrough signals: 'PagedAttention memory algorithm', 'Zero-waste inference optimization'",
              "[ANALYSIS] [3/3] Enriched item 'Frontier Risk Preparedness and Safety Frameworks' using Gemini model...",
              "[ANALYSIS] [3/3] Extracted breakthrough signals: 'Catastrophic hazard evaluations', 'Alignment validation suites'"
            ]);

            // Step 4: Verification
            setTimeout(() => {
              setSimStep("verify");
              setSimLogs((prev) => [
                ...prev,
                "[VERIFICATION] Quality gate matching active...",
                "[VERIFICATION] Verifying item: LoRA Low-Rank Adaptation (ID: e3b0c4...)",
                "[VERIFICATION] Score: 0.95 >= Threshold: 0.75. VERIFIED. Passed strict validation constraints.",
                "[VERIFICATION] Verifying item: vLLM PagedAttention (ID: 8fa73b...)",
                "[VERIFICATION] Score: 0.92 >= Threshold: 0.75. VERIFIED. Passed strict validation constraints.",
                "[VERIFICATION] Verifying item: Frontier Risk Preparedness (ID: c18d3e...)",
                "[VERIFICATION] Score: 0.65 < Threshold: 0.75. REJECTED. Failed confidence gates or strict outline counts."
              ]);

              // Step 5: Persistence
              setTimeout(() => {
                setSimStep("store");
                setSimLogs((prev) => [
                  ...prev,
                  "[PERSISTENCE] Committing verified opportunities to local memory cache...",
                  "[PERSISTENCE] Saved verified ResearchItem [e3b0c4...] to: data/items/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.json",
                  "[PERSISTENCE] Saved verified ResearchItem [8fa73b...] to: data/items/8fa73ba61e4fc3b8a36b2f15a97d2c3dfb8a19265f7c3db269c5957bcf9df7df.json",
                  "[PERSISTENCE] Local database JSON index updated cleanly."
                ]);

                // Step 6: Delivery
                setTimeout(() => {
                  setSimStep("deliver");
                  setSimLogs((prev) => [
                    ...prev,
                    "[DELIVERY] Compiling Daily Intelligence Briefing Markdown...",
                    "[DELIVERY] Report synthesized and structured cleanly under primary categories.",
                    "[DELIVERY] Published Daily Intelligence Briefing file to: reports/daily_intelligence_brief_2026_07_06.md",
                    "=========================================",
                    "   Pipeline Run Successfully Completed   ",
                    "========================================="
                  ]);
                  setSimStep("done");
                  setIsSimulating(false);
                  setSimulatedRunCount((c) => c + 1);
                }, 1200);

              }, 1200);

            }, 1200);

          }, 1200);

        }, 1200);
      }
    }, 100);
  };

  // Export full skeleton zip client-side using JSZip
  const handleExportZip = async () => {
    if (downloadingZip) return;
    setDownloadingZip(true);

    try {
      const zip = new JSZip();
      
      // Root level files
      zip.file("requirements.txt", PYTHON_PROJECT_FILES.find((f) => f.path === "requirements.txt")?.content || "");
      zip.file(".gitignore", PYTHON_PROJECT_FILES.find((f) => f.path === ".gitignore")?.content || "");
      zip.file("README.md", PYTHON_PROJECT_FILES.find((f) => f.path === "README.md")?.content || "");
      zip.file("main.py", PYTHON_PROJECT_FILES.find((f) => f.path === "main.py")?.content || "");

      // Folders
      const folders = ["models", "utils", "config", "collectors", "analyzers", "verifier", "memory", "delivery", "tests"];
      
      folders.forEach((folder) => {
        // Create folder structure in zip
        const zipFolder = zip.folder(folder);
        if (zipFolder) {
          // Write empty __init__.py files
          const initFile = PYTHON_PROJECT_FILES.find((f) => f.path === `${folder}/__init__.py`);
          if (initFile) {
            zipFolder.file("__init__.py", initFile.content);
          } else {
            zipFolder.file("__init__.py", `"""\nSignal Hunter ${folder} package.\n"""\n`);
          }

          // Write files belonging to this folder
          PYTHON_PROJECT_FILES.forEach((f) => {
            if (f.path.startsWith(`${folder}/`) && f.path !== `${folder}/__init__.py`) {
              const fileName = f.path.substring(folder.length + 1);
              zipFolder.file(fileName, f.content);
            }
          });
        }
      });

      // Generate the zip file async
      const content = await zip.generateAsync({ type: "blob" });
      const url = window.URL.createObjectURL(content);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "signal-hunter-skeleton.zip");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to generate zip:", err);
    } finally {
      setDownloadingZip(false);
    }
  };

  // Helper to categorize files
  const getFilesByFolder = (folder: string) => {
    return PYTHON_PROJECT_FILES.filter((f) => f.path.startsWith(`${folder}/`));
  };

  const getRootFiles = () => {
    return PYTHON_PROJECT_FILES.filter((f) => !f.path.includes("/"));
  };

  const filteredFiles = searchQuery
    ? PYTHON_PROJECT_FILES.filter(
        (f) =>
          f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          f.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const copyReportToClipboard = () => {
    navigator.clipboard.writeText(mockReportMarkdown);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

  return (
    <div id="signal_hunter_workbench" className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500/30 selection:text-teal-200">
      
      {/* HEADER BAR */}
      <header id="app_header" className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-teal-600 to-emerald-500 rounded-xl shadow-lg shadow-teal-900/30">
            <Cpu className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-300 to-teal-400 bg-clip-text text-transparent">
                SIGNAL HUNTER
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-teal-950 text-teal-400 border border-teal-900/50 rounded-full">
                v1.0.0-Beta
              </span>
            </div>
            <p className="text-xs text-slate-400">AI-Powered Research Intelligence Pipeline skeleton</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-300">
            <Smartphone className="w-3.5 h-3.5 text-teal-400" />
            <span>Termux Optimized</span>
          </div>
          <button
            id="download_zip_btn"
            onClick={handleExportZip}
            disabled={downloadingZip}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 disabled:from-slate-800 disabled:to-slate-800 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-teal-950/20 active:scale-95 disabled:pointer-events-none cursor-pointer"
          >
            {downloadingZip ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Bundling ZIP...</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Export Python Skeleton (ZIP)</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* SECTION TABS SUB-HEADER */}
      <div id="section_tabs_bar" className="border-b border-slate-900 bg-slate-950 px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex space-x-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800/80 w-full sm:w-auto">
          <button
            id="tab_code_workspace"
            onClick={() => setActiveSection("code")}
            className={`flex-1 sm:flex-initial flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer ${
              activeSection === "code"
                ? "bg-gradient-to-r from-teal-950/60 to-teal-900/40 text-teal-300 border border-teal-500/30 shadow-md shadow-teal-950/40"
                : "text-slate-400 hover:text-slate-200 border border-transparent"
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-teal-400" />
            <span>💻 CODE WORKSPACE</span>
          </button>
          <button
            id="tab_execution_sandbox"
            onClick={() => setActiveSection("execution")}
            className={`flex-1 sm:flex-initial flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer ${
              activeSection === "execution"
                ? "bg-gradient-to-r from-teal-950/60 to-teal-900/40 text-teal-300 border border-teal-500/30 shadow-md shadow-teal-950/40"
                : "text-slate-400 hover:text-slate-200 border border-transparent"
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${activeSection === "execution" ? "text-teal-400 fill-teal-400/20" : "text-slate-400"}`} />
            <span>⚡ EXECUTION SANDBOX</span>
          </button>
        </div>
        
        <div className="flex items-center space-x-2 text-[11px] text-slate-500 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span>Workspace Path:</span>
          <span className="text-slate-300 font-semibold bg-slate-900 px-2 py-0.5 rounded">/signal-hunter</span>
        </div>
      </div>

      {/* CORE WORKSPACE */}
      <main id="app_workspace" className="flex-1 flex flex-col overflow-hidden">
        
        {activeSection === "code" ? (
          <div className="flex-1 grid grid-cols-1 xl:grid-cols-12 overflow-hidden">
            {/* PANEL 1: FILE EXPLORER (3 cols) */}
            <section id="file_explorer_panel" className="xl:col-span-3 border-r border-slate-900 flex flex-col bg-slate-950/40 overflow-hidden">
              
              {/* Search bar */}
              <div className="p-4 border-b border-slate-900">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    id="search_files_input"
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search module code..."
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500 transition placeholder:text-slate-500"
                  />
                </div>
              </div>

              {/* Directory Tree */}
              <div className="flex-1 overflow-y-auto p-4 space-y-1 select-none">
                {searchQuery ? (
                  // Search Results view
                  <div className="space-y-2">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block mb-2">Search Results</span>
                    {filteredFiles.length === 0 ? (
                      <p className="text-xs text-slate-500 italic p-2">No matching file content found.</p>
                    ) : (
                      filteredFiles.map((file) => (
                        <button
                          key={file.path}
                          onClick={() => {
                            setSelectedFile(file);
                            setSearchQuery("");
                          }}
                          className="w-full flex items-center space-x-2 px-2 py-1.5 hover:bg-slate-900 rounded text-left text-xs text-teal-400 hover:text-teal-300"
                        >
                          <File className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate">{file.path}</span>
                        </button>
                      ))
                    )}
                  </div>
                ) : (
                  // Standard Directory Structure
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Project Skeleton Directory</span>
                      <span className="text-[10px] bg-slate-900 px-2 py-0.5 rounded text-slate-400 font-mono">/signal-hunter</span>
                    </div>

                    <div className="space-y-1.5">
                      {/* Folders List */}
                      {Object.keys(expandedFolders).map((folder) => {
                        const isExpanded = expandedFolders[folder];
                        const files = getFilesByFolder(folder);
                        return (
                          <div key={folder} className="space-y-0.5">
                            <button
                              onClick={() => toggleFolder(folder)}
                              className="w-full flex items-center justify-between px-2 py-1 hover:bg-slate-900/60 rounded text-left text-xs font-medium text-slate-300 hover:text-white transition group"
                            >
                              <div className="flex items-center space-x-2 truncate">
                                {isExpanded ? (
                                  <ChevronDown className="w-3 h-3 text-slate-500" />
                                ) : (
                                  <ChevronRight className="w-3 h-3 text-slate-500" />
                                )}
                                {isExpanded ? (
                                  <FolderOpen className="w-4 h-4 text-teal-500" />
                                ) : (
                                  <Folder className="w-4 h-4 text-teal-600 group-hover:text-teal-500" />
                                )}
                                <span className="truncate">{folder}/</span>
                              </div>
                              <span className="text-[9px] font-mono text-slate-600 px-1">{files.length} items</span>
                            </button>

                            {isExpanded && (
                              <div className="pl-6 border-l border-slate-900 space-y-0.5 ml-3.5 py-0.5">
                                {files.map((file) => (
                                  <button
                                    key={file.path}
                                    onClick={() => setSelectedFile(file)}
                                    className={`w-full flex items-center space-x-2 px-2 py-1 rounded text-left text-xs transition ${
                                      selectedFile.path === file.path
                                        ? "bg-teal-950/40 text-teal-300 font-medium"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
                                    }`}
                                  >
                                    <File className={`w-3.5 h-3.5 ${selectedFile.path === file.path ? "text-teal-400" : "text-slate-500"}`} />
                                    <span className="truncate">{file.name}</span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}

                      {/* Root files */}
                      <div className="pt-2 border-t border-slate-900/60 space-y-1">
                        <span className="text-[9px] uppercase font-semibold text-slate-600 px-2">Root Modules</span>
                        {getRootFiles().map((file) => (
                          <button
                            key={file.path}
                            onClick={() => setSelectedFile(file)}
                            className={`w-full flex items-center space-x-2 px-2 py-1 rounded text-left text-xs transition ${
                              selectedFile.path === file.path
                                ? "bg-teal-950/40 text-teal-300 font-medium"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
                            }`}
                          >
                            <File className={`w-3.5 h-3.5 ${selectedFile.path === file.path ? "text-teal-400" : "text-slate-500"}`} />
                            <span className="truncate">{file.name}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick info footer */}
              <div className="p-4 border-t border-slate-900 bg-slate-950 flex items-center space-x-3 text-xs text-slate-400 flex-shrink-0">
                <Info className="w-4 h-4 text-teal-500 flex-shrink-0" />
                <span>Files are physically populated on your workspace disk for immediate checkout.</span>
              </div>
            </section>

            {/* PANEL 2: CODE CONSOLE (9 cols) */}
            <section id="code_viewer_panel" className="xl:col-span-9 flex flex-col bg-slate-950 overflow-hidden">
              
              {/* File details bar */}
              <div className="px-5 py-3.5 border-b border-slate-900 flex items-center justify-between bg-slate-950/60">
                <div className="flex items-center space-x-2.5 truncate">
                  <FileText className="w-4 h-4 text-teal-400" />
                  <div>
                    <span className="text-xs font-mono font-medium text-slate-200">{selectedFile.path}</span>
                    <span className="mx-2 text-slate-600">•</span>
                    <span className="text-[10px] text-slate-400">{selectedFile.content.split("\n").length} lines</span>
                  </div>
                </div>

                <button
                  id="copy_code_btn"
                  onClick={handleCopyCode}
                  className="flex items-center space-x-1.5 px-2.5 py-1 bg-slate-900 border border-slate-800 text-[11px] text-slate-300 hover:text-white rounded transition hover:border-slate-700 active:scale-95 cursor-pointer"
                >
                  {copiedFile ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>

              {/* File Description Header */}
              <div className="px-5 py-3 bg-teal-950/10 border-b border-slate-900 text-xs text-slate-400 flex items-start space-x-2.5 flex-shrink-0">
                <BookOpen className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" />
                <p>{selectedFile.description}</p>
              </div>

              {/* Editor Sandbox with custom style syntax highlighting */}
              <div className="flex-1 overflow-auto bg-slate-950/80 p-5 font-mono text-xs leading-relaxed select-text">
                <pre className="relative h-full overflow-visible whitespace-pre">
                  {selectedFile.content.split("\n").map((line, idx) => {
                    // Extremely simple regex highlighting for preview purposes
                    let highlighted = line;
                    
                    // Color comments
                    if (line.trim().startsWith("#") || line.trim().startsWith('"""') || (line.includes('"""') && !line.includes('Pydantic'))) {
                      highlighted = `<span class="text-slate-500">${line}</span>`;
                    } else {
                      // Keywords
                      highlighted = line
                        .replace(/\b(def|class|import|from|return|if|elif|else|try|except|raise|as|pass|with|for|in|and|or|not)\b/g, '<span class="text-teal-400 font-semibold">$1</span>')
                        // Pydantic/Types
                        .replace(/\b(str|int|float|bool|datetime|List|Dict|Optional|Any|BaseModel|Field)\b/g, '<span class="text-blue-400 font-medium">$1</span>')
                        // Class name declarations
                        .replace(/\b(class\s+)([A-Za-z0-9_]+)/g, '$1<span class="text-emerald-300 font-bold">$2</span>')
                        // Function definitions
                        .replace(/\b(def\s+)([a-za-z0-9_]+)/g, '$1<span class="text-amber-200 font-medium">$2</span>');
                    }

                    return (
                      <div key={idx} className="flex hover:bg-slate-900/40 px-2 rounded -mx-2">
                        <span className="w-8 text-slate-700 select-none text-right pr-3 border-r border-slate-900 mr-4 text-[10px]">{idx + 1}</span>
                        <span dangerouslySetInnerHTML={{ __html: highlighted || " " }} />
                      </div>
                    );
                  })}
                </pre>
              </div>
            </section>
          </div>
        ) : (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
            {/* PANEL 3A: RUN CONTROL & TERMINAL LOGS (5 cols) */}
            <section id="execution_console_panel" className="lg:col-span-5 border-r border-slate-900 flex flex-col bg-slate-950 overflow-hidden">
              
              {/* Section Selector Tab */}
              <div className="px-5 py-3.5 border-b border-slate-900 bg-slate-950 flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <Terminal className="w-4 h-4 text-teal-400" />
                  <span className="text-xs uppercase font-bold tracking-wider text-slate-300">Execution Sandbox</span>
                </div>
                
                <button
                  id="simulate_pipeline_btn"
                  onClick={handleSimulatePipeline}
                  disabled={isSimulating}
                  className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 disabled:from-slate-800 disabled:to-slate-800 text-white rounded-lg text-xs font-semibold tracking-wide transition active:scale-95 disabled:pointer-events-none cursor-pointer"
                >
                  <Play className="w-3.5 h-3.5 fill-white animate-pulse" />
                  <span>{isSimulating ? "RUNNING PIPELINE..." : "RUN DRY-RUN SIMULATOR"}</span>
                </button>
              </div>

              {/* Active Schematics Node Chart */}
              <div className="p-4 border-b border-slate-900 bg-slate-950/30">
                <span className="text-[9px] uppercase font-bold tracking-wider text-slate-500 block mb-3">Live Scaffolding Schematics</span>
                
                <div className="grid grid-cols-5 gap-1 text-center select-none text-[10px] font-mono">
                  <div className={`p-1.5 border rounded flex flex-col items-center justify-center transition-all ${
                    simStep === "collect" 
                      ? "border-teal-500 bg-teal-950/30 text-teal-300 ring-1 ring-teal-500/50 animate-pulse" 
                      : simStep !== "idle" && simStep !== "config" ? "border-emerald-900/60 bg-slate-900/40 text-slate-500" : "border-slate-900 bg-slate-900/20 text-slate-400"
                  }`}>
                    <span className="font-semibold block truncate">COLLECT</span>
                    <span className="text-[8px] text-slate-500 block mt-0.5">arXiv/Feeds</span>
                  </div>
                  
                  <div className="flex items-center justify-center text-slate-700">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>

                  <div className={`p-1.5 border rounded flex flex-col items-center justify-center transition-all ${
                    simStep === "analyze" 
                      ? "border-teal-500 bg-teal-950/30 text-teal-300 ring-1 ring-teal-500/50 animate-pulse" 
                      : simStep !== "idle" && simStep !== "config" && simStep !== "collect" ? "border-emerald-900/60 bg-slate-900/40 text-slate-500" : "border-slate-900 bg-slate-900/20 text-slate-400"
                  }`}>
                    <span className="font-semibold block truncate">AI COG</span>
                    <span className="text-[8px] text-slate-500 block mt-0.5">Gemini</span>
                  </div>

                  <div className="flex items-center justify-center text-slate-700">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>

                  <div className={`p-1.5 border rounded flex flex-col items-center justify-center transition-all ${
                    simStep === "verify" 
                      ? "border-teal-500 bg-teal-950/30 text-teal-300 ring-1 ring-teal-500/50 animate-pulse" 
                      : simStep !== "idle" && simStep !== "config" && simStep !== "collect" && simStep !== "analyze" ? "border-emerald-900/60 bg-slate-900/40 text-slate-500" : "border-slate-900 bg-slate-900/20 text-slate-400"
                  }`}>
                    <span className="font-semibold block truncate">VERIFY</span>
                    <span className="text-[8px] text-slate-500 block mt-0.5">Scoring Gates</span>
                  </div>
                </div>
              </div>

              {/* Simulated Logging Output */}
              <div className="flex-1 bg-black p-5 font-mono text-[10px] text-slate-400 overflow-y-auto flex flex-col space-y-2">
                <div className="text-[10px] uppercase font-bold tracking-wider text-slate-600 mb-1 border-b border-slate-900 pb-1.5 flex items-center justify-between">
                  <span>Runtime Log stream</span>
                  {isSimulating && (
                    <span className="flex items-center space-x-1.5 text-teal-400 animate-pulse text-[9px]">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                      <span>STREAMING</span>
                    </span>
                  )}
                </div>
                {simLogs.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-slate-600 text-center select-none py-12">
                    <Terminal className="w-8 h-8 text-slate-800 mb-3" />
                    <span>Ready to execute main.py. Click run dry-run to stream log entries.</span>
                  </div>
                ) : (
                  simLogs.map((log, index) => {
                    let color = "text-slate-400";
                    if (log.includes("[COLLECTION]")) color = "text-blue-400";
                    if (log.includes("[ANALYSIS]")) color = "text-amber-400";
                    if (log.includes("[VERIFICATION]")) color = "text-indigo-400";
                    if (log.includes("[PERSISTENCE]")) color = "text-purple-400";
                    if (log.includes("[DELIVERY]")) color = "text-teal-400";
                    if (log.includes("VERIFIED")) color = "text-emerald-400 font-semibold";
                    if (log.includes("REJECTED")) color = "text-rose-400 font-semibold";
                    if (log.includes("===") || log.includes("Starting")) color = "text-white font-bold";

                    return (
                      <div key={index} className={`leading-relaxed whitespace-pre-wrap ${color}`}>
                        {log}
                      </div>
                    );
                  })
                )}
                <div ref={consoleEndRef} />
              </div>
            </section>

            {/* PANEL 3B: DAILY BRIEFING REPORT OUTPUT (7 cols) */}
            <section id="execution_report_panel" className="lg:col-span-7 flex flex-col bg-slate-950/20 overflow-hidden">
              {/* Daily Intelligence Briefing Output Visualizer */}
              <div className="flex-1 flex flex-col overflow-hidden">
                <div className="px-5 py-3.5 border-b border-slate-900 bg-slate-950/60 flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-300">
                    <Sparkles className="w-4 h-4 text-amber-400" />
                    <span className="font-medium">Output: daily_intelligence_brief.md</span>
                  </div>

                  {simulatedRunCount > 0 && (
                    <div className="flex space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 font-semibold">
                      <button
                        onClick={() => setReportTab("briefing")}
                        className={`px-3 py-1 rounded-md text-xs cursor-pointer transition ${reportTab === "briefing" ? "bg-teal-950 text-teal-400 border border-teal-900/50" : "text-slate-400 hover:text-slate-200"}`}
                      >
                        Styled Report
                      </button>
                      <button
                        onClick={() => setReportTab("markdown")}
                        className={`px-3 py-1 rounded-md text-xs cursor-pointer transition ${reportTab === "markdown" ? "bg-teal-950 text-teal-400 border border-teal-900/50" : "text-slate-400 hover:text-slate-200"}`}
                      >
                        Raw MD
                      </button>
                      <button
                        onClick={() => setReportTab("signals")}
                        className={`px-3 py-1 rounded-md text-xs cursor-pointer transition ${reportTab === "signals" ? "bg-teal-950 text-teal-400 border border-teal-900/50" : "text-slate-400 hover:text-slate-200"}`}
                      >
                        Signals Grid
                      </button>
                    </div>
                  )}
                </div>

                <div className="flex-1 overflow-y-auto p-6 select-text">
                  {simulatedRunCount === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center select-none py-12">
                      <FileText className="w-12 h-12 text-slate-800 mb-3" />
                      <p className="text-xs max-w-xs font-mono text-slate-500">
                        The daily briefing file compiles automatically after a pipeline run finishes. Run the simulator to examine the generated intelligence.
                      </p>
                    </div>
                  ) : (
                    <div className="h-full">
                      {reportTab === "briefing" && (
                        <div className="space-y-4 text-xs select-text">
                          <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between">
                            <div>
                              <h4 className="font-bold text-slate-200 text-sm">🎯 Signal Hunter Briefing</h4>
                              <span className="text-[10px] text-slate-500">Synthesized 2026-07-06 • Automated Build</span>
                            </div>
                            <span className="px-2 py-1 bg-emerald-950 text-emerald-400 font-mono border border-emerald-900/50 rounded-full font-bold">
                              Average confidence: 0.94
                            </span>
                          </div>

                          <div className="space-y-3">
                            {/* CATEGORY 1 */}
                            <div className="space-y-2">
                              <span className="text-[10px] font-bold text-teal-400 uppercase tracking-wider block bg-teal-950/20 px-2 py-1 border-l-2 border-teal-500 rounded">
                                Category: Research Paper
                              </span>

                              <div className="p-3 bg-slate-900/30 border border-slate-900 rounded-lg space-y-2">
                                <div className="flex items-center justify-between">
                                  <h5 className="font-semibold text-slate-200">1. LoRA: Low-Rank Adaptation of Large Language Models</h5>
                                  <span className="text-[10px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded font-mono font-bold">Score 0.95</span>
                                </div>
                                <p className="text-slate-400 italic leading-relaxed text-[11px] bg-slate-950 p-2 rounded-lg border border-slate-900">
                                  "Introduction of structural parameter adapters to preserve pretrained base layers while compressing learning dimensions dramatically."
                                </p>
                                <div className="space-y-1">
                                  <span className="text-[10px] font-semibold text-slate-500 block">Extracted Future Signals:</span>
                                  <div className="flex flex-wrap gap-1">
                                    <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded text-[10px] border border-slate-800">🚀 Adapter fine-tuning framework</span>
                                    <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded text-[10px] border border-slate-800">🚀 Low-Rank neural adapter strategy</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* CATEGORY 2 */}
                            <div className="space-y-2">
                              <span className="text-[10px] font-bold text-teal-400 uppercase tracking-wider block bg-teal-950/20 px-2 py-1 border-l-2 border-teal-500 rounded">
                                Category: GitHub Repository
                              </span>

                              <div className="p-3 bg-slate-900/30 border border-slate-900 rounded-lg space-y-2">
                                <div className="flex items-center justify-between">
                                  <h5 className="font-semibold text-slate-200">2. vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention</h5>
                                  <span className="text-[10px] bg-emerald-950 text-emerald-400 px-1.5 py-0.5 rounded font-mono font-bold">Score 0.92</span>
                                </div>
                                <p className="text-slate-400 italic leading-relaxed text-[11px] bg-slate-950 p-2 rounded-lg border border-slate-900">
                                  "vLLM achieves state-of-the-art throughput by using PagedAttention, managing sequence cache allocation cleanly."
                                </p>
                                <div className="space-y-1">
                                  <span className="text-[10px] font-semibold text-slate-500 block">Extracted Future Signals:</span>
                                  <div className="flex flex-wrap gap-1">
                                    <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded text-[10px] border border-slate-800">🚀 PagedAttention memory algorithm</span>
                                    <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded text-[10px] border border-slate-800">🚀 Zero-waste inference optimization</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {reportTab === "markdown" && (
                        <div className="h-full flex flex-col space-y-3 font-mono text-[10px]">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 text-[9px]">Markdown Briefing Text</span>
                            <button
                              onClick={copyReportToClipboard}
                              className="flex items-center space-x-1 px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-slate-400 hover:text-slate-200 text-[10px]"
                            >
                              {copiedReport ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-400" />
                                  <span className="text-emerald-400">Copied!</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" />
                                  <span>Copy Raw MD</span>
                                </>
                              )}
                            </button>
                          </div>
                          <textarea
                            readOnly
                            value={mockReportMarkdown}
                            className="flex-1 w-full bg-slate-950 border border-slate-900 p-4 rounded-xl text-slate-400 font-mono focus:outline-none min-h-[400px] select-text"
                          />
                        </div>
                      )}

                      {reportTab === "signals" && (
                        <div className="space-y-3">
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Verified Signal Index</span>
                          
                          <div className="border border-slate-900 rounded-lg overflow-hidden text-[11px] font-mono">
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="bg-slate-900 text-slate-400 border-b border-slate-900">
                                  <th className="p-3">Title</th>
                                  <th className="p-3">Source</th>
                                  <th className="p-3 text-right">Confidence</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-900">
                                <tr className="hover:bg-slate-900/20">
                                  <td className="p-3 font-medium text-slate-200 truncate max-w-[150px]">LoRA Parameter Adaptation</td>
                                  <td className="p-3 text-slate-400">Paper</td>
                                  <td className="p-3 text-right text-emerald-400 font-bold">0.95</td>
                                </tr>
                                <tr className="hover:bg-slate-900/20">
                                  <td className="p-3 font-medium text-slate-200 truncate max-w-[150px]">vLLM PagedAttention</td>
                                  <td className="p-3 text-slate-400">GitHub</td>
                                  <td className="p-3 text-right text-emerald-400 font-bold">0.92</td>
                                </tr>
                                <tr className="hover:bg-slate-900/20 bg-rose-950/10 text-slate-500">
                                  <td className="p-3 truncate max-w-[150px] line-through">Frontier Model Safe Preparedness</td>
                                  <td className="p-3">Blog</td>
                                  <td className="p-3 text-right text-rose-500">0.65</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}

      </main>
    </div>
  );
}

const mockReportMarkdown = `# 🎯 Signal Hunter Daily Intelligence Report - 2026-07-06
---
**Mission**: *Discover early opportunities, engineering breakthroughs, and scientific discoveries before they become mainstream.*

## 📊 Executive Summary Dashboard
- **Total Signals Analyzed & Verified**: 2
- **Average Confidence Score**: 0.94

## ⚡ Primary Breakthroughs
### 📂 Category: Research Paper

#### 1. LoRA: Low-Rank Adaptation of Large Language Models
- **Confidence Rating**: \`0.95\` 🔥 [High Signal]
- **Canonical URL**: <https://arxiv.org/abs/2106.09685>
- **Author/Creator**: Edward J. Hu et al.

**Core Technical Summary:**
> Introduction of structural parameter adapters to preserve pretrained base layers while compressing learning dimensions dramatically.

**Extracted Opportunities & Future Signals:**
- 🚀 Adapter fine-tuning framework
- 🚀 Low-Rank neural adapter strategy

*Verifier Critique:* Passed confidence threshold (0.95 >= 0.75). Passed strict validation constraints.

---

### 📂 Category: Github Repository

#### 2. vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention
- **Confidence Rating**: \`0.92\` 🔥 [High Signal]
- **Canonical URL**: <https://github.com/vllm-project/vllm>
- **Author/Creator**: UC Berkeley team

**Core Technical Summary:**
> vLLM achieves state-of-the-art throughput by using PagedAttention, managing sequence cache allocation cleanly.

**Extracted Opportunities & Future Signals:**
- 🚀 PagedAttention memory algorithm
- 🚀 Zero-waste inference optimization

*Verifier Critique:* Passed confidence threshold (0.92 >= 0.75). Passed strict validation constraints.

---

\`Signal Hunter Pipeline v1.0.0-Beta • Executed via local scheduler\`
`;
