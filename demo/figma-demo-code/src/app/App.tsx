import { useState, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bell,
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Cloud,
  Cpu,
  Database,
  DollarSign,
  FileText,
  GitBranch,
  Globe,
  HeartPulse,
  Home,
  Layers,
  LayoutGrid,
  MessageSquare,
  MoreVertical,
  Package,
  RefreshCw,
  Search,
  Send,
  Server,
  Settings,
  Shield,
  Sparkles,
  Terminal,
  TrendingDown,
  Wrench,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";

// ── 공통 스타일 ──────────────────────────────────────────────────────────────
const SANS = { fontFamily: "'Inter', sans-serif" };
const MONO = { fontFamily: "'JetBrains Mono', monospace" };

// ── 타입 ────────────────────────────────────────────────────────────────────
type Screen = "clusters" | "overview" | "service" | "service-detail" | "change-risk" | "self-healing"
           | "cost-overview" | "cost-right-sizing" | "cost-pod-placement"
           | "resources-nodes" | "resources-deployments" | "topology";
type AIMode = "diagnostic" | "new" | null;

// ── 더미 데이터 ──────────────────────────────────────────────────────────────
const SERVICES = [
  { id: 1,  name: "checkout-api-v2",    status: "UNHEALTHY", issue: "FAILED DEPLOY",  replicas: "1/3", ns: "checkout",    updated: "23분 전", healthy: false, errorRate: "8.2%",  latency: "2,400ms", restarts: 6 },
  { id: 2,  name: "order-api",          status: "HEALTHY",   issue: null,              replicas: "3/3", ns: "production",  updated: "2시간 전",healthy: true,  errorRate: "0.1%",  latency: "142ms",   restarts: 0 },
  { id: 3,  name: "inventory-api",      status: "HEALTHY",   issue: null,              replicas: "2/2", ns: "production",  updated: "1일 전",  healthy: true,  errorRate: "0.0%",  latency: "89ms",    restarts: 0 },
  { id: 4,  name: "web-frontend",       status: "UNHEALTHY", issue: "HIGH LATENCY",   replicas: "2/3", ns: "production",  updated: "45분 전", healthy: false, errorRate: "2.7%",  latency: "621ms",   restarts: 1 },
  { id: 5,  name: "recommend-worker",   status: "HEALTHY",   issue: null,              replicas: "1/1", ns: "production",  updated: "3시간 전",healthy: true,  errorRate: "0.0%",  latency: "204ms",   restarts: 0 },
  { id: 6,  name: "auth-service",       status: "HEALTHY",   issue: null,              replicas: "2/2", ns: "production",  updated: "5시간 전",healthy: true,  errorRate: "0.0%",  latency: "56ms",    restarts: 0 },
  { id: 7,  name: "notification-svc",   status: "HEALTHY",   issue: null,              replicas: "1/1", ns: "production",  updated: "1일 전",  healthy: true,  errorRate: "0.1%",  latency: "312ms",   restarts: 0 },
  { id: 8,  name: "payment-gateway",    status: "HEALTHY",   issue: null,              replicas: "2/2", ns: "checkout",    updated: "1시간 전",healthy: true,  errorRate: "0.2%",  latency: "98ms",    restarts: 0 },
];

const CLUSTERS = [
  { provider: "aws",   name: "Production",       nodes: 310, pods: { warning: 28, ok: 4, total: 632 }, cpu: "28.2%", mem: "17%", disk: "17%", issues: 7,  risks: 14, savings: "$63,672", health: 89, opt: 72 },
  { provider: "gcp",   name: "demo",             nodes: 142, pods: { warning: 20, ok: 9, total: 563 }, cpu: "26%",  mem: "17%", disk: "23%", issues: 1,  risks: 3,  savings: "$16,501", health: 83, opt: 85 },
  { provider: "aws",   name: "cluster-dev-use-2", nodes: 39,  pods: { warning: 14, ok: 0, total: 162 }, cpu: "28%",  mem: "–",   disk: "57%", issues: 0,  risks: 0,  savings: "$5,433",  health: 85, opt: 79 },
  { provider: "azure", name: "cluster-nip-use-1", nodes: 31,  pods: { warning: 3,  ok: 1, total: 13  }, cpu: "26%",  mem: "–",   disk: "–",   issues: 0,  risks: 0,  savings: "$3,599",  health: 88, opt: 79 },
  { provider: "aws",   name: "testing",           nodes: 4,   pods: { warning: 0,  ok: 1, total: 0   }, cpu: "–",    mem: "–",   disk: "–",   issues: 0,  risks: 0,  savings: "$99",     health: 100, opt: 0  },
];

const ISSUE_TREND = Array.from({ length: 30 }, (_, i) => ({
  d: `${i + 1}일`,
  Workload: Math.floor(Math.random() * 12),
  Services: Math.floor(Math.random() * 8),
  Jobs: Math.floor(Math.random() * 4),
  "Add-ons": Math.floor(Math.random() * 3),
  Nodes: Math.floor(Math.random() * 5),
}));

const SERVICE_EVENTS = [
  { time: "5월 14일 03:34 PM", type: "Pod pending",       icon: "warn",  summary: "ledger-writer-6f65db4-digru는 Pending 상태", detail: "컨테이너 이미지 pull 실패" },
  { time: "5월 14일 03:34 PM", type: "Availability Issue", icon: "error", summary: "production/bank-of-hill-valley 가용성 문제 발생", detail: "NonZeroExitCode · Exit code 1" },
  { time: "5월 14일 03:33 PM", type: "Deploy",            icon: "info",  summary: "새 서비스 버전 배포됨", detail: "이미지 업데이트" },
  { time: "5월 14일 03:32 PM", type: "Service Discovered", icon: "ok",    summary: "Discovery: ledger-writer 서비스 확인", detail: "Namespace: production" },
];

const REMEDIATION_STEPS = [
  { label: "Run Kubectl Command",  desc: "Fix SPRING_DATASOURCE_URL key typo", status: "running",   done: false },
  { label: "Restart Service",      desc: "Restart ledger-writer deployment",   status: "running",   done: false },
  { label: "Run Kubectl Cmd",      desc: "Fix SPRING_DATASOURCE_URL key typo", status: "completed", done: true  },
  { label: "Restart Service",      desc: "Restart ledger-writer deployment",   status: "completed", done: true  },
];

const HEAL_EVENTS = [
  { time: "3월 17일 5:37 PM", type: "Pod running (ready)",   icon: "ok",   summary: "cash-cache-5c69b8d4e-d8t5s가 Running 상태", started: "Mar 17, 2025, 5:07:51 PM", status: "Running (ready)" },
  { time: "3월 17일 5:37 PM", type: "Pod pending",           icon: "warn", summary: "cash-cache-5c69b8d4e-d8t5bs Pending 상태",  started: "Mar 17, 2025, 5:07:51 PM", status: "Pending" },
  { time: "3월 17일 1:20 PM", type: "Node terminated",       icon: "error",summary: "ip-172-26-4-212.ec2.internal - deleted",     started: "Mar 17, 2025, 1:20:34 PM", status: "Terminated" },
  { time: "3월 17일 1:20 PM", type: "Node terminated",       icon: "error",summary: "ip-172-26-4-212.ec2.internal - deleted",     started: "Mar 17, 2025, 11:55:53 AM", status: "Terminated" },
];

// ── Sidebar ───────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: "clusters",     label: "클러스터",       icon: Layers,      group: null },
  { id: "overview",     label: "Overview",      icon: BarChart3,   group: null },
  { id: null,           label: "워크로드 Health", icon: HeartPulse,  group: null },
  { id: null,           label: "사용자",          icon: Globe,       group: null },
  { id: null,           label: "AI 워크로드",     icon: Sparkles,    group: null },
  { id: "service",      label: "Services",      icon: LayoutGrid,  group: null },
  { id: null,           label: "Drift 분석",     icon: GitBranch,   group: null },
  { id: null,           label: "Jobs",           icon: Clock,       group: null },
];

const COST_NAV = [
  { id: "cost-overview",       label: "Cost Overview"  },
  { id: null,                  label: "Allocation"     },
  { id: "cost-right-sizing",   label: "Right Sizing"   },
  { id: "cost-pod-placement",  label: "Pod Placement"  },
];
const NAV_K8S = [
  { id: null, label: "Kubernetes Addons", icon: Package },
];
const NAV_NATIVE = [
  { id: "self-healing",          label: "Configuration", icon: Settings },
  { id: "topology",              label: "Topology View", icon: Globe    },
];
const RESOURCES_NAV = [
  { id: "resources-nodes",       label: "Nodes"       },
  { id: null,                    label: "Workloads"   },
  { id: "resources-deployments", label: "Deployments", indent: true },
  { id: null,                    label: "Pods",        indent: true },
  { id: null,                    label: "ReplicaSets", indent: true },
  { id: null,                    label: "StatefulSets",indent: true },
  { id: null,                    label: "DaemonSets",  indent: true },
  { id: null,                    label: "Storage"     },
];

function Sidebar({ screen, onNav }: { screen: Screen; onNav: (s: Screen) => void }) {
  const [costOpen, setCostOpen] = useState(screen.startsWith("cost"));
  const [resOpen, setResOpen]   = useState(screen.startsWith("resources"));
  const isCost = screen.startsWith("cost");
  const isService = screen === "service" || screen === "service-detail";

  return (
    <aside className="w-48 shrink-0 flex flex-col bg-[#0f1628] text-slate-300 border-r border-white/6 overflow-y-auto">
      {/* Logo */}
      <div className="px-4 py-4 flex items-center gap-2.5 border-b border-white/8">
        <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center">
          <Zap size={14} className="text-white" />
        </div>
        <span className="text-[13px] font-bold text-white" style={SANS}>Easy-ku</span>
      </div>

      {/* Go-To search */}
      <div className="px-3 py-2.5 border-b border-white/6">
        <div className="flex items-center gap-2 bg-white/6 rounded-lg px-2.5 py-1.5 text-[10px] text-slate-500 cursor-pointer hover:bg-white/10 transition-colors">
          <Search size={10} />
          <span style={MONO}>Go-To</span>
          <span className="ml-auto text-[8px] bg-white/10 px-1.5 py-0.5 rounded text-slate-400">⌘K</span>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 p-2 space-y-0.5">
        {NAV_ITEMS.map((item, i) => {
          const Icon = item.icon;
          const active = item.id === "service" ? isService : item.id === screen;
          return (
            <button key={i} onClick={() => item.id && onNav(item.id as Screen)}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all cursor-pointer text-[11px] ${
                active ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-white/6"
              }`} style={SANS}>
              <Icon size={13} />
              {item.label}
            </button>
          );
        })}

        {/* Cost 섹션 (접이식) */}
        <div className="mt-1">
          <button onClick={() => setCostOpen(v => !v)}
            className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all cursor-pointer text-[11px] ${
              isCost ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-white/6"}`}
            style={SANS}>
            <DollarSign size={13} />
            <span className="flex-1">Cost</span>
            <ChevronDown size={11} className={`transition-transform ${costOpen ? "rotate-180" : ""}`} />
          </button>
          {costOpen && (
            <div className="ml-4 mt-0.5 space-y-0.5 border-l border-white/10 pl-2">
              {COST_NAV.map((item, i) => (
                <button key={i}
                  onClick={() => item.id && onNav(item.id as Screen)}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-[10px] transition-colors cursor-pointer ${
                    item.id === screen ? "text-indigo-300 bg-indigo-600/30 font-semibold"
                      : item.id ? "text-slate-400 hover:text-slate-200 hover:bg-white/6"
                      : "text-slate-600 cursor-default"}`}
                  style={SANS}>
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* AI Actions */}
        <button className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all cursor-pointer text-[11px] text-slate-400 hover:text-slate-200 hover:bg-white/6" style={SANS}>
          <Sparkles size={13} className="text-indigo-400" />
          <span className="flex-1">AI Actions</span>
          <span className="text-[8px] bg-indigo-600/40 text-indigo-300 px-1.5 py-0.5 rounded font-bold">NEW</span>
        </button>

        {/* Settings */}
        <button className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all cursor-pointer text-[11px] text-slate-400 hover:text-slate-200 hover:bg-white/6" style={SANS}>
          <Settings size={13} />
          Settings
        </button>

        <div className="pt-2 pb-1">
          <div className="text-[8px] uppercase tracking-widest text-slate-600 px-2 mb-1" style={MONO}>Kubernetes 탐색기</div>
          {NAV_K8S.map((item, i) => {
            const Icon = item.icon;
            return (
              <button key={i} className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-left text-[11px] text-slate-500 hover:text-slate-300 hover:bg-white/6 transition-colors cursor-pointer" style={SANS}>
                <Icon size={12} />{item.label}
              </button>
            );
          })}

          {/* Resources 접이식 */}
          <button onClick={() => setResOpen(v => !v)}
            className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-left text-[11px] transition-colors cursor-pointer ${
              screen.startsWith("resources") ? "bg-indigo-600 text-white" : "text-slate-500 hover:text-slate-300 hover:bg-white/6"}`}
            style={SANS}>
            <Server size={12} />
            <span className="flex-1">Resources</span>
            <ChevronDown size={10} className={`transition-transform ${resOpen ? "rotate-180" : ""}`} />
          </button>
          {resOpen && (
            <div className="ml-4 mt-0.5 border-l border-white/10 pl-2 space-y-0.5">
              {RESOURCES_NAV.map((item, i) => (
                <button key={i}
                  onClick={() => item.id && onNav(item.id as Screen)}
                  className={`w-full text-left rounded-lg text-[10px] transition-colors cursor-pointer py-1 ${
                    (item as {indent?: boolean}).indent ? "px-4" : "px-2.5"
                  } ${item.id === screen ? "text-indigo-300 bg-indigo-600/30 font-semibold"
                    : item.id ? "text-slate-400 hover:text-slate-200 hover:bg-white/6"
                    : "text-slate-600 font-semibold mt-1 cursor-default"}`}
                  style={SANS}>
                  {item.label}
                </button>
              ))}
            </div>
          )}

          {NAV_NATIVE.map((item, i) => {
            const Icon = item.icon;
            const active = item.id === screen;
            return (
              <button key={i} onClick={() => item.id && onNav(item.id as Screen)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-left text-[11px] transition-colors cursor-pointer ${
                  active ? "bg-indigo-600 text-white" : "text-slate-500 hover:text-slate-300 hover:bg-white/6"
                }`} style={SANS}>
                <Icon size={12} />{item.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* User */}
      <div className="p-3 border-t border-white/8 flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-indigo-500 flex items-center justify-center text-[10px] font-bold text-white">A</div>
        <div>
          <div className="text-[10px] text-slate-300" style={SANS}>admin</div>
          <div className="text-[8px] text-slate-600" style={MONO}>prod-cluster</div>
        </div>
      </div>
    </aside>
  );
}

// ── 공통 헤더 ─────────────────────────────────────────────────────────────────
function TopBar({
  breadcrumb,
  onAIClick,
  showAIBtn = false,
}: {
  breadcrumb: string[];
  onAIClick?: () => void;
  showAIBtn?: boolean;
}) {
  return (
    <div className="h-11 shrink-0 border-b border-slate-200 bg-white flex items-center justify-between px-5">
      <div className="flex items-center gap-1 text-[11px]" style={SANS}>
        {breadcrumb.map((b, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={10} className="text-slate-400" />}
            <span className={i === breadcrumb.length - 1 ? "text-slate-700 font-semibold" : "text-slate-400"}>{b}</span>
          </span>
        ))}
      </div>
      <div className="flex items-center gap-2">
        {showAIBtn && (
          <button onClick={onAIClick}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-[11px] font-semibold transition-colors cursor-pointer shadow-sm"
            style={SANS}>
            <Sparkles size={12} />
            Klaudia AI
          </button>
        )}
        <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><Search size={14} /></button>
        <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer relative">
          <Bell size={14} />
          <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-red-500" />
        </button>
        <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><Settings size={14} /></button>
      </div>
    </div>
  );
}

// ── 상태 뱃지 ─────────────────────────────────────────────────────────────────
function Badge({ label, variant }: { label: string; variant: "healthy" | "unhealthy" | "warning" | "blue" | "gray" }) {
  const cls = {
    healthy:   "bg-emerald-100 text-emerald-700 border border-emerald-200",
    unhealthy: "bg-red-100 text-red-700 border border-red-200",
    warning:   "bg-amber-100 text-amber-700 border border-amber-200",
    blue:      "bg-sky-100 text-sky-700 border border-sky-200",
    gray:      "bg-slate-100 text-slate-600 border border-slate-200",
  }[variant];
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[9px] font-semibold ${cls}`} style={MONO}>{label}</span>;
}

// ── Cost 더미 데이터 ─────────────────────────────────────────────────────────
const COST_TREND_DATA = Array.from({ length: 28 }, (_, i) => ({
  d: `${11}/${i + 1}`,
  Cost: Math.floor(8500 + Math.sin(i * 0.4) * 2000 + Math.random() * 1500),
}));

const RESOURCE_OPT_DATA = Array.from({ length: 14 }, (_, i) => ({
  d: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun","Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i],
  현재할당: 4200 - i * 30,
  최적할당: 1800 + Math.sin(i * 0.5) * 200,
  실제사용: 1200 + Math.sin(i * 0.8) * 300,
  절감량:   2400 - i * 25,
}));

const POD_CAPACITY_DATA = Array.from({ length: 14 }, (_, i) => ({
  d: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun","Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i],
  현재용량: 85 - Math.random() * 5,
  최적용량: 62 + Math.random() * 4,
}));

const RIGHT_SIZING_ROWS = [
  { service: "events-collector",   ns: "default",     cluster: "production",     rec: { cpu: "4.5 core", mem: "5 GiB" },  rightSized: "0/4", actual: "4.5c / 5GiB",   savings: "$420", policy: "Production", auto: false },
  { service: "payment-processor",  ns: "data",        cluster: "pre-production", rec: { cpu: "2.6 core", mem: "2.5 GiB" }, rightSized: "1/2", actual: "2.6c / 3GiB",   savings: "$310", policy: "Production", auto: true  },
  { service: "correlation-engine", ns: "frontend",    cluster: "demo",           rec: { cpu: "1 core",   mem: "960 MiB"}, rightSized: "2/3", actual: "1c / 1GiB",     savings: "$185", policy: "Aggressive", auto: false },
  { service: "nginx-controller",   ns: "monitoring",  cluster: "labs-e2e",       rec: { cpu: "2 core",   mem: "240 MiB"}, rightSized: "0/1", actual: "2c / 512MiB",   savings: "$95",  policy: "Production", auto: false },
  { service: "pyramid-al",         ns: "default",     cluster: "xsign-non-prod", rec: { cpu: "8 core",   mem: "3 GiB" },  rightSized: "3/3", actual: "8c / 4GiB",     savings: "$680", policy: "Moderate",   auto: true  },
  { service: "planner-service",    ns: "static-insp", cluster: "poc-ci",         rec: { cpu: "1.2 core", mem: "1.2 GiB"}, rightSized: "1/5", actual: "1.2c / 2GiB",   savings: "$220", policy: "Production", auto: false },
  { service: "inventory",          ns: "brain",       cluster: "data-engine",    rec: { cpu: "1.5 core", mem: "800 MiB"}, rightSized: "2/2", actual: "1.5c / 1GiB",   savings: "$140", policy: "Production", auto: false },
  { service: "atlas-api",          ns: "db-cache",    cluster: "qa-playground",  rec: { cpu: "3 core",   mem: "800 MiB"}, rightSized: "0/3", actual: "3c / 1GiB",     savings: "$340", policy: "Aggressive", auto: true  },
];

const POD_PLACEMENT_ROWS = [
  { cluster: "production",        nodes: 310, cpuBin: "710 → 601 CPUs", memBin: "2.1k → 1.7k GiB", unmovable: "2,146 (27%)", savings: "Up to $63k", placement: true  },
  { cluster: "cluster-dev-use-2", nodes: 39,  cpuBin: "1,108 → 923 CPUs",memBin: "3.1k → 2.6k GiB",unmovable: "1312 (29%)", savings: "Up to $41k", placement: false },
  { cluster: "demo",              nodes: 142, cpuBin: "520 → 480 CPUs", memBin: "1.4k → 1.2k GiB", unmovable: "943 (18%)",  savings: "Up to $28k", placement: false },
  { cluster: "testing",           nodes: 4,   cpuBin: "12 → 10 CPUs",   memBin: "24 → 20 GiB",     unmovable: "8 (40%)",    savings: "Up to $2k",  placement: false },
];

const CPU_CHART = Array.from({ length: 30 }, (_, i) => ({
  d: i, usage: 800 + Math.sin(i * 0.4) * 500 + Math.random() * 200,
  req: 4500, limit: 4700, rec: 1300,
}));

const MEM_CHART = Array.from({ length: 30 }, (_, i) => ({
  d: i, usage: 2500 + Math.sin(i * 0.3) * 800 + Math.random() * 300,
  req: 4000, limit: 5200, rec: 2150,
}));

// ─────────────────────────────────────────────────────────────────────────────
// PANEL: Minimal Cost (slide-in)
// ─────────────────────────────────────────────────────────────────────────────
function MinimalCostPanel({ onClose }: { onClose: () => void }) {
  const [expanded, setExpanded] = useState({ worker: false, algo: false });

  return (
    <div className="fixed inset-y-0 right-0 w-[640px] bg-white border-l border-slate-200 flex flex-col shadow-2xl z-50 overflow-hidden"
      style={{ animation: "slideIn 0.2s ease" }}>
      <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between shrink-0 bg-slate-50">
        <div>
          <div className="text-[12px] font-bold text-slate-800" style={SANS}>최소 비용으로 최대 안정성 확보</div>
          <div className="text-[9px] text-slate-500 mt-0.5" style={MONO}>Right-sizing 권장 사항 — Container 최적화</div>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><X size={16} /></button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* 좌측: 서비스 목록 */}
        <div className="w-56 border-r border-slate-200 overflow-y-auto shrink-0">
          <div className="px-3 py-2 border-b border-slate-100">
            <div className="text-[10px] font-semibold text-slate-600 mb-2" style={SANS}>Right-sizing by Service</div>
            <div className="flex items-center gap-2 text-[9px] text-slate-500">
              <button className="flex items-center gap-1 hover:text-slate-700 cursor-pointer"><span>⊞</span> Columns</button>
              <button className="flex items-center gap-1 hover:text-slate-700 cursor-pointer"><span>↓</span> Export</button>
            </div>
          </div>
          <div className="text-[8px] grid grid-cols-3 gap-1 px-3 py-1.5 bg-slate-50 border-b border-slate-100 text-slate-400 font-semibold uppercase" style={MONO}>
            <span>Service</span><span>Namespace</span><span>Cluster</span>
          </div>
          {RIGHT_SIZING_ROWS.map((row, i) => (
            <div key={i} className={`grid grid-cols-3 gap-1 px-3 py-2 border-b border-slate-50 text-[9px] cursor-pointer hover:bg-indigo-50 transition-colors ${i === 0 ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`} style={MONO}>
              <span className="text-indigo-600 truncate font-medium">{row.service}</span>
              <span className="text-slate-500 truncate">{row.ns}</span>
              <span className="text-slate-500 truncate">{row.cluster}</span>
            </div>
          ))}
        </div>

        {/* 우측: Container 최적화 상세 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Container: main */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <div className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 border-b border-slate-100">
              <span className="text-[11px] font-bold text-slate-700" style={SANS}>Container: main</span>
              <span className="text-[9px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded" style={MONO}>CPU 4500 → 1300 millicores</span>
              <span className="text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded" style={MONO}>Memory 5,000 → 2,150 MB</span>
            </div>
            <div className="p-4 grid grid-cols-2 gap-4">
              {/* CPU */}
              <div>
                <div className="text-[10px] font-semibold text-slate-600 mb-2" style={SANS}>CPU</div>
                <div className="space-y-1 text-[9px] mb-3" style={MONO}>
                  <div className="flex justify-between"><span className="text-slate-400">Requests</span><span className="text-slate-700 font-semibold">4500 millicores</span></div>
                  <div className="flex justify-between text-emerald-600"><span>Recommended</span><span className="font-bold">1300 Millicores</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Limits</span><span className="text-slate-700">4700 millicores</span></div>
                </div>
                <ResponsiveContainer width="100%" height={80}>
                  <LineChart data={CPU_CHART.slice(0, 15)}>
                    <Line type="monotone" dataKey="usage" stroke="#6366f1" strokeWidth={1.5} dot={false} name="사용량" />
                    <Line type="monotone" dataKey="rec"   stroke="#10b981" strokeWidth={1.5} dot={false} strokeDasharray="4 3" name="권장" />
                    <Line type="monotone" dataKey="req"   stroke="#94a3b8" strokeWidth={1}   dot={false} strokeDasharray="2 2" name="Requests" />
                    <Tooltip contentStyle={{ fontSize: 9 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              {/* Memory */}
              <div>
                <div className="text-[10px] font-semibold text-slate-600 mb-2" style={SANS}>Memory</div>
                <div className="space-y-1 text-[9px] mb-3" style={MONO}>
                  <div className="flex justify-between"><span className="text-slate-400">Requests</span><span className="text-slate-700 font-semibold">4000 MB</span></div>
                  <div className="flex justify-between text-emerald-600"><span>Recommended</span><span className="font-bold">2150 MiB</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Limits</span><span className="text-slate-700">5200 MB</span></div>
                </div>
                <ResponsiveContainer width="100%" height={80}>
                  <LineChart data={MEM_CHART.slice(0, 15)}>
                    <Line type="monotone" dataKey="usage" stroke="#8b5cf6" strokeWidth={1.5} dot={false} name="사용량" />
                    <Line type="monotone" dataKey="rec"   stroke="#10b981" strokeWidth={1.5} dot={false} strokeDasharray="4 3" name="권장" />
                    <Line type="monotone" dataKey="req"   stroke="#94a3b8" strokeWidth={1}   dot={false} strokeDasharray="2 2" name="Requests" />
                    <Tooltip contentStyle={{ fontSize: 9 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Container: worker (접이식) */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button onClick={() => setExpanded(e => ({ ...e, worker: !e.worker }))}
              className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 cursor-pointer hover:bg-slate-100 transition-colors">
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-bold text-slate-700" style={SANS}>Container: worker</span>
                <span className="text-[9px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded" style={MONO}>CPU 2,100 → 1,010 millicores</span>
              </div>
              <ChevronDown size={13} className={`text-slate-400 transition-transform ${expanded.worker ? "rotate-180" : ""}`} />
            </button>
            {expanded.worker && (
              <div className="p-4">
                <div className="text-[10px] text-slate-500" style={MONO}>CPU 2100m → 1010m · Memory 1000MB → 1500MB</div>
              </div>
            )}
          </div>

          {/* Container: algo-research (접이식) */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button onClick={() => setExpanded(e => ({ ...e, algo: !e.algo }))}
              className="w-full flex items-center justify-between px-4 py-2.5 bg-slate-50 cursor-pointer hover:bg-slate-100 transition-colors">
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-bold text-slate-700" style={SANS}>Container: algo-research</span>
                <span className="text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded" style={MONO}>Memory 2,000 → 1,500 MB</span>
              </div>
              <ChevronDown size={13} className={`text-slate-400 transition-transform ${expanded.algo ? "rotate-180" : ""}`} />
            </button>
            {expanded.algo && (
              <div className="p-4">
                <div className="text-[10px] text-slate-500" style={MONO}>Memory 2000MB → 1500MB</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div className="px-5 py-3 border-t border-slate-200 flex items-center justify-end gap-2 bg-slate-50 shrink-0">
        <button onClick={onClose} className="px-4 py-2 text-[11px] text-slate-600 hover:text-slate-800 cursor-pointer" style={SANS}>취소</button>
        <button className="px-4 py-2 text-[11px] border border-slate-300 rounded-lg hover:bg-slate-100 text-slate-600 cursor-pointer" style={SANS}>값 초기화</button>
        <button className="px-4 py-2 text-[11px] bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 cursor-pointer font-semibold" style={SANS}>3개 Container 업데이트</button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PANEL: Automated Policy Settings (slide-in)
// ─────────────────────────────────────────────────────────────────────────────
function AutomatedPolicyPanel({ serviceName, onClose }: { serviceName: string; onClose: () => void }) {
  return (
    <div className="fixed inset-y-0 right-0 w-[400px] bg-white border-l border-slate-200 flex flex-col shadow-2xl z-50"
      style={{ animation: "slideIn 0.2s ease" }}>
      <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between shrink-0 bg-slate-50">
        <div>
          <div className="text-[12px] font-bold text-slate-800" style={SANS}>서비스 & 정책 생성</div>
          <div className="text-[9px] text-slate-500 mt-0.5" style={MONO}>{serviceName}</div>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><X size={16} /></button>
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        <div className="text-[10px] text-slate-500 bg-amber-50 border border-amber-200 rounded-xl p-3" style={MONO}>
          Production 환경에 적용할 Right Sizing 정책을 설정합니다.
        </div>
        {[
          { label: "클러스터", value: "production" },
          { label: "Namespace", value: "default" },
          { label: "서비스", value: serviceName },
        ].map(({ label, value }) => (
          <div key={label}>
            <div className="text-[9px] text-slate-400 uppercase tracking-wider mb-1" style={MONO}>{label}</div>
            <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-700" style={MONO}>
              <span>{value}</span>
              <ChevronDown size={11} className="text-slate-400" />
            </div>
          </div>
        ))}
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider mb-1" style={MONO}>정책 공격성</div>
          <div className="flex gap-2">
            {["Conservative", "Moderate", "Aggressive"].map((p) => (
              <button key={p} className={`flex-1 py-1.5 rounded-lg text-[10px] border cursor-pointer transition-colors ${p === "Moderate" ? "bg-indigo-600 text-white border-indigo-600" : "border-slate-200 text-slate-500 hover:border-slate-300"}`} style={SANS}>{p}</button>
            ))}
          </div>
        </div>
        <div className="space-y-3 pt-2">
          <div className="text-[10px] font-semibold text-slate-600" style={SANS}>CPU 설정</div>
          {[
            { label: "최소 CPU Request", value: "100m" },
            { label: "최대 CPU Request", value: "4000m" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-[10px] text-slate-500" style={MONO}>{label}</span>
              <input defaultValue={value} className="w-24 px-2 py-1 border border-slate-200 rounded-lg text-[10px] text-slate-700 text-right outline-none focus:border-indigo-400" style={MONO} />
            </div>
          ))}
          <div className="text-[10px] font-semibold text-slate-600 pt-1" style={SANS}>Memory 설정</div>
          {[
            { label: "최소 Memory Request", value: "128MiB" },
            { label: "최대 Memory Request", value: "4096MiB" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between">
              <span className="text-[10px] text-slate-500" style={MONO}>{label}</span>
              <input defaultValue={value} className="w-24 px-2 py-1 border border-slate-200 rounded-lg text-[10px] text-slate-700 text-right outline-none focus:border-indigo-400" style={MONO} />
            </div>
          ))}
        </div>
      </div>
      <div className="px-5 py-3 border-t border-slate-200 flex justify-end gap-2 bg-slate-50 shrink-0">
        <button onClick={onClose} className="px-4 py-2 text-[11px] text-slate-600 cursor-pointer" style={SANS}>취소</button>
        <button className="px-4 py-2 text-[11px] bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 cursor-pointer font-semibold" style={SANS}>정책 저장</button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN: Cost Overview
// ═══════════════════════════════════════════════════════════════════════════════
function CostOverview({ onNav }: { onNav: (s: Screen) => void }) {
  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "Cost", "Cost Overview"]} />
      <div className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[11px]" style={MONO}>
            <span className="text-slate-500">클러스터</span>
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 cursor-pointer hover:border-slate-300">
              <span className="text-slate-700">전체 클러스터</span><ChevronDown size={11} className="text-slate-400" />
            </div>
          </div>
          <div className="flex items-center gap-2 text-[10px]">
            <button className="px-3 py-1.5 border border-slate-200 bg-white rounded-lg text-slate-600 hover:border-slate-300 cursor-pointer" style={SANS}>가격 & 할인 설정</button>
            <button className="px-3 py-1.5 border border-slate-200 bg-white rounded-lg text-slate-600 hover:border-slate-300 cursor-pointer" style={SANS}>Nodepool 구성</button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* 좌측: 비용 요약 */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="text-[22px] font-bold text-slate-800 mb-1" style={SANS}>$356,191</div>
            <div className="text-[10px] text-slate-400 mb-4" style={MONO}>총 월 예상 비용</div>
            <div className="flex gap-4 mb-4">
              <div>
                <div className="text-[14px] font-bold text-slate-700" style={SANS}>$216,762</div>
                <div className="text-[9px] text-slate-400" style={MONO}>할당됨</div>
              </div>
              <div>
                <div className="text-[14px] font-bold text-slate-700" style={SANS}>$139,429</div>
                <div className="text-[9px] text-slate-400" style={MONO}>미할당</div>
              </div>
            </div>
            <div className="border-t border-slate-100 pt-4 space-y-3">
              <div>
                <div className="text-[18px] font-bold text-emerald-600" style={SANS}>18%</div>
                <div className="text-[9px] text-slate-400" style={MONO}>잠재 절감액</div>
              </div>
              <div>
                <div className="text-[16px] font-bold text-blue-600" style={SANS}>10%</div>
                <div className="text-[9px] text-slate-400 mb-1" style={MONO}>Right Sizing 절감 가능</div>
                <button onClick={() => onNav("cost-right-sizing")}
                  className="text-[9px] bg-blue-600 text-white px-2.5 py-1 rounded-lg cursor-pointer hover:bg-blue-500 font-semibold" style={SANS}>
                  Save now →
                </button>
              </div>
              <div>
                <div className="text-[16px] font-bold text-indigo-600" style={SANS}>8%</div>
                <div className="text-[9px] text-slate-400 mb-1" style={MONO}>Pod Placement 절감</div>
                <button onClick={() => onNav("cost-pod-placement")}
                  className="text-[9px] bg-indigo-600 text-white px-2.5 py-1 rounded-lg cursor-pointer hover:bg-indigo-500 font-semibold" style={SANS}>
                  Save now →
                </button>
              </div>
            </div>
          </div>

          {/* 우측: Cost Trend 차트 */}
          <div className="col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="text-[12px] font-semibold text-slate-700" style={SANS}>Cost Trend</div>
              <div className="text-[9px] text-slate-400" style={MONO}>최근 30일</div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={COST_TREND_DATA} barSize={14}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="d" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} interval={3} />
                <YAxis tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={35}
                  tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => [`$${v.toLocaleString()}`, "비용"]} contentStyle={{ fontSize: 10, borderRadius: 6 }} />
                <Bar dataKey="Cost" fill="#3b82f6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Optimization Impact */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="text-[12px] font-semibold text-slate-700 mb-4" style={SANS}>Optimization Impact</div>
          <div className="grid grid-cols-5 gap-6">
            {[
              { val: "14%", label: "Right-sized 절감", sub: "68% (5,449/7,978)", color: "text-emerald-600" },
              { val: "11%", label: "Pod placement 절감", sub: "59% (57/98)", color: "text-emerald-600" },
              { val: "14,710", label: "Under-Provisioned Containers", sub: "(42%)", color: "text-amber-600" },
              { val: "11,778", label: "미최적화 Containers", sub: "", color: "text-slate-700" },
              { val: "68%", label: "자동화율", sub: "워크로드 기준", color: "text-indigo-600" },
            ].map((s) => (
              <div key={s.label}>
                <div className={`text-[22px] font-bold mb-1 ${s.color}`} style={SANS}>{s.val}</div>
                <div className="text-[9px] text-slate-500 leading-snug" style={MONO}>{s.label}</div>
                {s.sub && <div className="text-[8px] text-slate-400 mt-0.5" style={MONO}>{s.sub}</div>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN: Cost Right Sizing
// ═══════════════════════════════════════════════════════════════════════════════
function CostRightSizing() {
  const [autoRows, setAutoRows] = useState<boolean[]>(RIGHT_SIZING_ROWS.map(r => r.auto));
  const [minimalPanel, setMinimalPanel] = useState(false);

  function toggleAuto(i: number) {
    const next = [...autoRows];
    next[i] = !next[i];
    setAutoRows(next);
    if (next[i]) setMinimalPanel(true);
  }

  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "Cost", "Right Sizing"]} />
      <div className="p-5 space-y-4">
        <div className="text-[10px] text-slate-500" style={MONO}>
          AI 기반 Right Sizing — <span className="text-indigo-600 cursor-pointer hover:underline">자세히 알아보기</span>
        </div>

        {/* 상단 메트릭 카드 */}
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="text-[9px] text-slate-400 mb-1" style={MONO}>절감 가능 (30일 기준)</div>
            <div className="text-[22px] font-bold text-emerald-600 mb-0.5" style={SANS}>14%</div>
            <div className="text-[9px] text-slate-400" style={MONO}>활성 절감 (30일): 8%</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="text-[9px] text-slate-400 mb-1" style={MONO}>Resources Active → Projected</div>
            <div className="text-[13px] font-bold text-slate-800" style={SANS}>5,570 → 24,140</div>
            <div className="text-[9px] text-slate-400 mt-1" style={MONO}>CPU Core hours 절감</div>
            <div className="text-[13px] font-bold text-slate-800" style={SANS}>8,318 → 41,342</div>
            <div className="text-[9px] text-slate-400" style={MONO}>Memory GiB hours 절감</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="text-[9px] text-slate-400 mb-1" style={MONO}>잔여 절감 가능</div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] text-slate-500" style={MONO}>자동화</span>
              <span className="text-[14px] font-bold text-blue-600" style={SANS}>10%</span>
            </div>
            <div className="text-[9px] text-slate-400" style={MONO}>잔여 가능: 2,529</div>
            <div className="text-[9px] text-slate-400" style={MONO}>비자동화 워크로드 32%</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="text-[9px] text-slate-400 mb-1" style={MONO}>Right-sized 워크로드</div>
            <div className="text-[22px] font-bold text-slate-800 mb-1" style={SANS}>5,449</div>
            <div className="flex items-center gap-1.5 text-[9px]" style={MONO}>
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-slate-500">자동화 워크로드 68%</span>
            </div>
            <div className="flex items-center gap-1.5 text-[9px] mt-0.5" style={MONO}>
              <span className="w-2 h-2 rounded-full bg-slate-300" />
              <span className="text-slate-500">비자동화 32%</span>
            </div>
          </div>
        </div>

        {/* Resource Requests Optimization 차트 */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Resource Requests Optimization</span>
            <div className="flex gap-1.5 ml-auto">
              {["1w","1M","3M"].map(t => (
                <button key={t} className={`px-2 py-0.5 rounded text-[9px] cursor-pointer border ${t === "1w" ? "bg-indigo-600 text-white border-indigo-600" : "border-slate-200 text-slate-500"}`} style={MONO}>{t}</button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4 text-[9px] mb-3" style={MONO}>
            {[
              { color: "#94a3b8", label: "최적화 없는 대안" },
              { color: "#3b82f6", label: "현재 할당량" },
              { color: "#10b981", label: "최적 할당량 (예측)" },
              { color: "#6366f1", label: "절감량" },
            ].map(({ color, label }) => (
              <span key={label} className="flex items-center gap-1">
                <span className="w-6 h-0.5 rounded inline-block" style={{ backgroundColor: color }} />
                {label}
              </span>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={RESOURCE_OPT_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={35} />
              <Tooltip contentStyle={{ fontSize: 10, borderRadius: 6 }} />
              <Line type="monotone" dataKey="현재할당"  stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="최적할당"  stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="5 3" />
              <Line type="monotone" dataKey="실제사용"  stroke="#6366f1" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="절감량"    stroke="#94a3b8" strokeWidth={1} dot={false} strokeDasharray="3 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Right-sizing by Service 테이블 */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Right-sizing by Service</span>
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-700 cursor-pointer border border-slate-200 rounded-lg px-2.5 py-1.5" style={SANS}>
                <span>⊞</span> Columns
              </button>
              <button className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-700 cursor-pointer border border-slate-200 rounded-lg px-2.5 py-1.5" style={SANS}>
                정책 보기
              </button>
              <button className="flex items-center gap-1 text-[10px] bg-indigo-600 text-white rounded-lg px-2.5 py-1.5 cursor-pointer hover:bg-indigo-500 font-semibold" style={SANS}>
                + 새 정책
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[10px]">
              <thead>
                <tr className="border-b border-slate-100 text-[8px] uppercase text-slate-400" style={MONO}>
                  <th className="text-left px-4 py-2.5 font-semibold">서비스</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Namespace</th>
                  <th className="text-left px-3 py-2.5 font-semibold">클러스터</th>
                  <th className="text-left px-3 py-2.5 font-semibold text-blue-600">권장사항</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Right-Sized</th>
                  <th className="text-left px-3 py-2.5 font-semibold">현재 설정</th>
                  <th className="text-left px-3 py-2.5 font-semibold">절감 가능</th>
                  <th className="text-left px-3 py-2.5 font-semibold">정책</th>
                  <th className="text-center px-3 py-2.5 font-semibold">자동화</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {RIGHT_SIZING_ROWS.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 text-indigo-600 font-medium cursor-pointer hover:underline" style={MONO}>{row.service}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{row.ns}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{row.cluster}</td>
                    <td className="px-3 py-3">
                      <button onClick={() => setMinimalPanel(true)}
                        className="flex flex-col gap-0.5 cursor-pointer hover:opacity-80 transition-opacity">
                        <span className="text-blue-600 font-semibold hover:underline" style={MONO}>{row.rec.cpu}</span>
                        <span className="text-purple-600 font-semibold hover:underline" style={MONO}>{row.rec.mem}</span>
                      </button>
                    </td>
                    <td className="px-3 py-3 text-slate-600" style={MONO}>{row.rightSized}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{row.actual}</td>
                    <td className="px-3 py-3 text-emerald-600 font-semibold" style={MONO}>{row.savings}</td>
                    <td className="px-3 py-3">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px]" style={MONO}>{row.policy}</span>
                    </td>
                    <td className="px-3 py-3 text-center">
                      <button onClick={() => toggleAuto(i)}
                        className={`w-9 h-5 rounded-full transition-colors cursor-pointer relative inline-flex ${autoRows[i] ? "bg-blue-500" : "bg-slate-300"}`}>
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${autoRows[i] ? "left-4" : "left-0.5"}`} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Minimal Cost 사이드 패널 */}
      {minimalPanel && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20" onClick={() => setMinimalPanel(false)} />
          <MinimalCostPanel onClose={() => setMinimalPanel(false)} />
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN: Cost Pod Placement
// ═══════════════════════════════════════════════════════════════════════════════
function CostPodPlacement() {
  const [minimalPanel, setMinimalPanel] = useState(true); // 진입 시 즉시 열림

  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "Cost", "Pod Placement"]} />
      <div className="p-5 space-y-4">
        {/* 상단 메트릭 */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { val: "3,288", sub1: "3,069 CPUs", sub2: "잠재 절감액", color: "text-blue-600" },
            { val: "4,317", sub1: "4,008 CPUs", sub2: "활성 절감액", color: "text-emerald-600" },
            { val: "10,665", sub1: "9,613", sub2: "총 최적화 가능", color: "text-indigo-600" },
            { val: "57%", sub1: "49/86 클러스터", sub2: "자동화됨", color: "text-amber-600" },
          ].map((s, i) => (
            <div key={i} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
              <div className={`text-[22px] font-bold mb-1 ${s.color}`} style={SANS}>{s.val}</div>
              <div className="text-[9px] text-slate-400" style={MONO}>{s.sub1}</div>
              <div className="text-[9px] text-slate-500 mt-0.5" style={MONO}>{s.sub2}</div>
            </div>
          ))}
        </div>

        {/* Optimization Blockers */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="text-[12px] font-semibold text-slate-700 mb-3" style={SANS}>Optimization Blockers</div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { time: "7일 전", msg: "과도한 Pod anti-affinity 설정으로 스케일 다운 방지" },
              { time: "7일 전", msg: "Namespace 내 최소 노드 수 요건으로 스케일 다운 불가" },
              { time: "7일 전", msg: "Pod Disruption Budget 제한으로 스케일 다운 방지됨" },
              { time: "7일 전", msg: "비최적 메모리 유형이 최적 bin packing에 영향을 줌" },
            ].map((b, i) => (
              <div key={i} className="flex items-start gap-2.5 px-3 py-2.5 bg-red-50 border border-red-200 rounded-xl">
                <AlertTriangle size={12} className="text-red-500 shrink-0 mt-0.5" />
                <div>
                  <div className="text-[9px] text-red-600 leading-snug" style={MONO}>{b.msg}</div>
                  <div className="text-[8px] text-red-400 mt-0.5" style={MONO}>{b.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Resource Capacity Optimization 차트 */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Resource Capacity Optimization</span>
            <div className="flex gap-1.5">
              {["CPU","메모리"].map(t => (
                <button key={t} className={`px-2.5 py-1 rounded-lg text-[9px] cursor-pointer border ${t === "CPU" ? "bg-indigo-600 text-white border-indigo-600" : "border-slate-200 text-slate-500"}`} style={MONO}>{t}</button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-4 text-[9px] mb-3" style={MONO}>
            {[
              { color: "#3b82f6", label: "현재 용량" },
              { color: "#10b981", label: "최적 용량 (예측)" },
            ].map(({ color, label }) => (
              <span key={label} className="flex items-center gap-1">
                <span className="w-5 h-0.5 rounded inline-block" style={{ backgroundColor: color }} />{label}
              </span>
            ))}
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={POD_CAPACITY_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="d" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={30} domain={[40, 100]} />
              <Tooltip contentStyle={{ fontSize: 10, borderRadius: 6 }} />
              <Line type="monotone" dataKey="현재용량" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="최적용량" stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="5 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Potential Savings 테이블 */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Potential Savings</span>
            <div className="flex items-center gap-2">
              <button className="text-[10px] text-indigo-600 hover:underline cursor-pointer" style={SANS}>전체 보고서 보기 →</button>
              <label className="flex items-center gap-1.5 text-[10px] text-slate-500 cursor-pointer" style={MONO}>
                <input type="checkbox" className="w-3 h-3 accent-indigo-600" />Filters
              </label>
            </div>
          </div>
          <table className="w-full text-[10px]">
            <thead>
              <tr className="border-b border-slate-100 text-[8px] uppercase text-slate-400" style={MONO}>
                <th className="text-left px-4 py-2.5 font-semibold">클러스터</th>
                <th className="text-left px-3 py-2.5 font-semibold">노드 수</th>
                <th className="text-left px-3 py-2.5 font-semibold">최적 CPU Bin Packing</th>
                <th className="text-left px-3 py-2.5 font-semibold">최적 Memory Bin Packing</th>
                <th className="text-left px-3 py-2.5 font-semibold">이동 불가 Pods</th>
                <th className="text-left px-3 py-2.5 font-semibold">잠재 절감액</th>
                <th className="text-center px-3 py-2.5 font-semibold">Intelligent Placement</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {POD_PLACEMENT_ROWS.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-700" style={MONO}>{row.cluster}</td>
                  <td className="px-3 py-3 text-slate-500" style={MONO}>{row.nodes}</td>
                  <td className="px-3 py-3 text-slate-600" style={MONO}>{row.cpuBin}</td>
                  <td className="px-3 py-3 text-slate-600" style={MONO}>{row.memBin}</td>
                  <td className="px-3 py-3 text-amber-600 font-medium" style={MONO}>{row.unmovable}</td>
                  <td className="px-3 py-3 text-emerald-600 font-bold" style={MONO}>{row.savings}</td>
                  <td className="px-3 py-3 text-center">
                    <span className={`text-[9px] px-2 py-0.5 rounded font-semibold ${row.placement ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`} style={MONO}>
                      {row.placement ? "활성화됨" : "비활성화됨"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Minimal Cost 사이드 패널 (진입 즉시) */}
      {minimalPanel && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20" onClick={() => setMinimalPanel(false)} />
          <MinimalCostPanel onClose={() => setMinimalPanel(false)} />
        </>
      )}
    </div>
  );
}

// ── Resources / Topology 데이터 ───────────────────────────────────────────────
const NODES_DATA = [
  { name: "node-1", status: "Ready",    role: "control-plane", age: "12d", version: "v1.26.3", ip: "10.0.0.1", cpu: 42, mem: 61, pods: 18 },
  { name: "node-2", status: "Ready",    role: "worker",        age: "12d", version: "v1.26.3", ip: "10.0.0.2", cpu: 67, mem: 74, pods: 24 },
  { name: "node-3", status: "Ready",    role: "worker",        age: "11d", version: "v1.26.3", ip: "10.0.0.3", cpu: 89, mem: 88, pods: 31 },
  { name: "node-4", status: "NotReady", role: "worker",        age: "5d",  version: "v1.26.3", ip: "10.0.0.4", cpu: 0,  mem: 0,  pods: 0  },
  { name: "node-5", status: "Ready",    role: "worker",        age: "8d",  version: "v1.26.3", ip: "10.0.0.5", cpu: 38, mem: 52, pods: 15 },
];

const DEPLOYMENTS_DATA = [
  { name: "auth-proxy",              ns: "kube-system",  cluster: "production", status: "Healthy",   replicas: "1/1", updated: "1달 전" },
  { name: "auth-sponsor",            ns: "default",      cluster: "production", status: "Healthy",   replicas: "1/1", updated: "1달 전" },
  { name: "buildkite-operator",      ns: "kube-system",  cluster: "production", status: "Healthy",   replicas: "1/1", updated: "1달 전" },
  { name: "canary-example",          ns: "canary",       cluster: "production", status: "Healthy",   replicas: "3/3", updated: "2일 전" },
  { name: "canary-example-canary",   ns: "canary",       cluster: "production", status: "Healthy",   replicas: "1/3", updated: "2일 전" },
  { name: "car-watcher",             ns: "infra-sllogs", cluster: "demo",       status: "Healthy",   replicas: "1/1", updated: "3일 전" },
  { name: "cashier",                 ns: "infra-sllogs", cluster: "demo",       status: "Unhealthy", replicas: "0/1", updated: "41분 전" },
  { name: "demo-kube-authenticate",  ns: "infra-sllogs", cluster: "demo",       status: "Healthy",   replicas: "1/1", updated: "5일 전" },
  { name: "roll-manager",            ns: "default",      cluster: "production", status: "Healthy",   replicas: "2/2", updated: "1주 전" },
];

const DEPLOY_EVENTS = [
  { type: "Deploy",           summary: "image updated to auth-proxy:v2", start: "Mar 3, 2025, 11:47 PM", end: "Mar 13, 2025, 8:32:55 PM", changes: "No changes", status: "Failed"    },
  { type: "Service Discovered", summary: "Discovered auth-proxy",         start: "Mar 15, 2025, 8:32:59 PM", end: "Mar 15, 2025, 8:32:55 PM", changes: "–", status: "Discovered" },
];

const TOPO_NODES = [
  {
    id: "node-1", label: "Node-1", ip: "10.0.0.1", cpu: 42, mem: 61,
    pods: [
      { id: "pod-a", name: "auth-proxy-7d9f-abc",  ns: "kube-system", status: "Running",   cpu: 12, mem: 34 },
      { id: "pod-b", name: "coredns-5d98-xyz",     ns: "kube-system", status: "Running",   cpu: 8,  mem: 28 },
    ],
  },
  {
    id: "node-2", label: "Node-2", ip: "10.0.0.2", cpu: 67, mem: 74,
    pods: [
      { id: "pod-c", name: "ledger-writer-6f65-bbb", ns: "production",  status: "CrashLoop", cpu: 0,  mem: 0  },
      { id: "pod-d", name: "api-server-4d88-qqq",    ns: "production",  status: "Running",   cpu: 45, mem: 62 },
    ],
  },
  {
    id: "node-3", label: "Node-3", ip: "10.0.0.3", cpu: 89, mem: 88,
    pods: [
      { id: "pod-e", name: "frontend-5b77-mmm",    ns: "production",  status: "Running",   cpu: 23, mem: 41 },
      { id: "pod-f", name: "payment-8c44-nnn",     ns: "production",  status: "Running",   cpu: 38, mem: 55 },
      { id: "pod-g", name: "log-aggregator-1x",    ns: "monitoring",  status: "Running",   cpu: 19, mem: 31 },
    ],
  },
  {
    id: "node-5", label: "Node-5", ip: "10.0.0.5", cpu: 38, mem: 52,
    pods: [
      { id: "pod-h", name: "webapp-3e99-hhh",      ns: "default",     status: "Running",   cpu: 15, mem: 28 },
    ],
  },
];

// ── Resources: Nodes ─────────────────────────────────────────────────────────
function ResourcesNodes() {
  const [selected, setSelected] = useState<string | null>(null);
  const sel = NODES_DATA.find(n => n.name === selected);

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-50">
      <div className="flex-1 overflow-auto">
        <TopBar breadcrumb={["Resources", "Nodes"]} />
        <div className="p-5 space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-2 text-[11px] text-slate-400 w-60">
              <Search size={12} /><input className="bg-transparent outline-none" placeholder="Node 검색..." style={SANS} />
            </div>
            <div className="ml-auto text-[10px] text-slate-500" style={MONO}>총 {NODES_DATA.length}개 노드</div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-slate-100 text-[8px] uppercase text-slate-400" style={MONO}>
                  <th className="text-left px-4 py-2.5 font-semibold">이름</th>
                  <th className="text-left px-3 py-2.5 font-semibold">상태</th>
                  <th className="text-left px-3 py-2.5 font-semibold">역할</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Age</th>
                  <th className="text-left px-3 py-2.5 font-semibold">버전</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Internal IP</th>
                  <th className="text-left px-3 py-2.5 font-semibold">CPU</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Memory</th>
                  <th className="text-left px-3 py-2.5 font-semibold">Pods</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {NODES_DATA.map((node) => (
                  <tr key={node.name}
                    onClick={() => setSelected(selected === node.name ? null : node.name)}
                    className={`cursor-pointer transition-colors hover:bg-slate-50 ${selected === node.name ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`}>
                    <td className="px-4 py-3 font-semibold text-indigo-600" style={MONO}>{node.name}</td>
                    <td className="px-3 py-3">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-semibold ${node.status === "Ready" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`} style={MONO}>
                        {node.status}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{node.role}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{node.age}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{node.version}</td>
                    <td className="px-3 py-3 text-slate-500" style={MONO}>{node.ip}</td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden w-16">
                          <div className={`h-full rounded-full ${node.cpu >= 80 ? "bg-red-500" : node.cpu >= 60 ? "bg-amber-400" : "bg-emerald-500"}`}
                            style={{ width: `${node.cpu}%` }} />
                        </div>
                        <span className={`text-[10px] font-semibold ${node.cpu >= 80 ? "text-red-500" : node.cpu >= 60 ? "text-amber-500" : "text-emerald-600"}`} style={MONO}>
                          {node.cpu || "–"}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden w-16">
                          <div className={`h-full rounded-full ${node.mem >= 80 ? "bg-red-500" : node.mem >= 60 ? "bg-amber-400" : "bg-emerald-500"}`}
                            style={{ width: `${node.mem}%` }} />
                        </div>
                        <span className={`text-[10px] font-semibold ${node.mem >= 80 ? "text-red-500" : node.mem >= 60 ? "text-amber-500" : "text-emerald-600"}`} style={MONO}>
                          {node.mem || "–"}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-slate-600 font-medium" style={MONO}>{node.pods}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 우측 상세 패널 */}
      {sel && (
        <div className="w-72 border-l border-slate-200 bg-white flex flex-col shrink-0 overflow-y-auto">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[12px] font-bold text-slate-700" style={SANS}>{sel.name}</span>
            <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 cursor-pointer"><X size={14} /></button>
          </div>
          <div className="p-4 space-y-3 text-[10px]" style={MONO}>
            {[
              { k: "상태",    v: sel.status,  c: sel.status === "Ready" ? "text-emerald-600 font-bold" : "text-red-500 font-bold" },
              { k: "역할",    v: sel.role,    c: "text-slate-700" },
              { k: "버전",    v: sel.version, c: "text-slate-700" },
              { k: "IP",      v: sel.ip,      c: "text-slate-700" },
              { k: "CPU",     v: `${sel.cpu}%`, c: sel.cpu >= 80 ? "text-red-500 font-bold" : "text-slate-700" },
              { k: "Memory",  v: `${sel.mem}%`, c: sel.mem >= 80 ? "text-red-500 font-bold" : "text-slate-700" },
              { k: "Pods",    v: String(sel.pods), c: "text-slate-700" },
            ].map(({ k, v, c }) => (
              <div key={k} className="flex justify-between border-b border-slate-50 pb-2">
                <span className="text-slate-400">{k}</span>
                <span className={c}>{v}</span>
              </div>
            ))}
            {sel.cpu >= 80 && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-[9px] leading-relaxed">
                ⚠ CPU 사용률이 높습니다. Pod 재배치를 권장합니다.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Resources: Deployments ────────────────────────────────────────────────────
function ResourcesDeployments() {
  const [selected, setSelected] = useState<string>("auth-proxy");
  const [tab, setTab] = useState("Events");
  const sel = DEPLOYMENTS_DATA.find(d => d.name === selected)!;

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-50">
      {/* 좌측: 목록 */}
      <div className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 overflow-hidden">
        <div className="px-3 py-2.5 border-b border-slate-100">
          <div className="text-[11px] font-semibold text-slate-700 mb-2" style={SANS}>Deployments</div>
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-[10px] text-slate-400">
            <Search size={10} /><input className="bg-transparent outline-none w-full" placeholder="검색..." style={MONO} />
          </div>
        </div>
        <div className="text-[9px] text-slate-400 px-3 py-1.5 border-b border-slate-100" style={MONO}>
          {DEPLOYMENTS_DATA.length}개 Deployment 표시 중
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-50">
          {DEPLOYMENTS_DATA.map((d) => (
            <button key={d.name} onClick={() => setSelected(d.name)}
              className={`w-full text-left px-3 py-2.5 transition-colors cursor-pointer hover:bg-slate-50 ${selected === d.name ? "bg-indigo-50 border-l-2 border-l-indigo-500" : ""}`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[10px] font-semibold text-slate-700 truncate" style={MONO}>{d.name}</span>
                <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold ${d.status === "Healthy" ? "text-emerald-600" : "text-red-500"}`} style={MONO}>
                  {d.status === "Healthy" ? "●" : "●"}
                </span>
              </div>
              <div className="text-[9px] text-slate-400" style={MONO}>{d.ns}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 우측: 상세 */}
      <div className="flex-1 overflow-auto">
        <TopBar breadcrumb={["Resources", "Workloads", "Deployments", sel.name]} />
        <div className="p-5 space-y-4">
          {/* 헤더 */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <h1 className="text-[16px] font-bold text-slate-800" style={SANS}>{sel.name}</h1>
                <Badge label={sel.status === "Healthy" ? "HEALTHY" : "UNHEALTHY"} variant={sel.status === "Healthy" ? "healthy" : "unhealthy"} />
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 text-[10px] border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 cursor-pointer" style={SANS}>YAML 편집</button>
                <button className="px-3 py-1.5 text-[10px] border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 cursor-pointer" style={SANS}>Scale</button>
                <button className="px-3 py-1.5 text-[10px] bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 cursor-pointer font-semibold" style={SANS}>Restart</button>
              </div>
            </div>
            <div className="grid grid-cols-5 gap-4 text-[10px]" style={MONO}>
              {[
                { label: "유형",      value: "Deployment"   },
                { label: "클러스터",   value: sel.cluster    },
                { label: "Namespace", value: sel.ns         },
                { label: "Replicas",  value: sel.replicas   },
                { label: "수정됨",    value: sel.updated    },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div className="text-[8px] text-slate-400 uppercase tracking-wider mb-1">{label}</div>
                  <div className="text-slate-700 font-medium">{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 탭 */}
          <div className="flex items-center gap-0.5 border-b border-slate-200">
            {["Events", "Pods", "Nodes", "Info"].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-[11px] font-medium cursor-pointer border-b-2 -mb-px transition-colors ${
                  tab === t ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-700"}`} style={SANS}>{t}</button>
            ))}
          </div>

          {tab === "Events" && (
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-100">
                <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Events ({DEPLOY_EVENTS.length})</span>
              </div>
              {/* 핑크 타임라인 바 */}
              <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
                <div className="text-[9px] text-slate-400 mb-2" style={MONO}>Deployment 설치 진행 중...</div>
                <div className="relative h-5 bg-slate-100 rounded overflow-hidden">
                  <div className="absolute left-0 top-0 h-full bg-pink-500 rounded" style={{ width: "70%" }} />
                  <div className="absolute inset-0 flex items-center justify-between px-2 text-[8px] text-white font-semibold" style={MONO}>
                    {["0.0s","0.2s","0.4s","0.6s","0.8s","1.0s","1.2s"].map(t => <span key={t}>{t}</span>)}
                  </div>
                </div>
              </div>
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="border-b border-slate-100 text-[8px] uppercase text-slate-400" style={MONO}>
                    <th className="text-left px-4 py-2.5">이벤트 유형</th>
                    <th className="text-left px-3 py-2.5">요약</th>
                    <th className="text-left px-3 py-2.5">시작 시각</th>
                    <th className="text-left px-3 py-2.5">마지막 업데이트</th>
                    <th className="text-left px-3 py-2.5">변경사항</th>
                    <th className="text-left px-3 py-2.5">상태</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {DEPLOY_EVENTS.map((ev, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center ${ev.type === "Deploy" ? "bg-pink-100" : "bg-blue-100"}`}>
                            {ev.type === "Deploy" ? <RefreshCw size={10} className="text-pink-500" /> : <CheckCircle2 size={10} className="text-blue-500" />}
                          </div>
                          <span className="font-medium text-slate-700" style={MONO}>{ev.type}</span>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-slate-500" style={MONO}>{ev.summary}</td>
                      <td className="px-3 py-3 text-slate-500" style={MONO}>{ev.start}</td>
                      <td className="px-3 py-3 text-slate-500" style={MONO}>{ev.end}</td>
                      <td className="px-3 py-3 text-slate-500" style={MONO}>{ev.changes}</td>
                      <td className="px-3 py-3">
                        <Badge label={ev.status} variant={ev.status === "Failed" ? "unhealthy" : "blue"} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="px-5 py-4 text-center text-[10px] text-slate-400 border-t border-slate-100" style={MONO}>
                이 시간대에 다른 변경사항 없음
              </div>
              <div className="px-5 pb-4 flex justify-center">
                <button className="px-4 py-2 bg-indigo-600 text-white text-[10px] font-semibold rounded-lg cursor-pointer hover:bg-indigo-500" style={SANS}>이전 변경사항 보기</button>
              </div>
            </div>
          )}
          {tab !== "Events" && (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400 text-[11px]" style={MONO}>{tab} 로딩 중...</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Topology View ─────────────────────────────────────────────────────────────
function TopologyView() {
  const [viewMode, setViewMode] = useState<"list" | "topology">("topology");
  const [selectedPod, setSelectedPod] = useState<{ nodeId: string; podId: string } | null>(null);
  const [autoPlay, setAutoPlay] = useState(false);

  const selPodData = selectedPod
    ? TOPO_NODES.find(n => n.id === selectedPod.nodeId)?.pods.find(p => p.id === selectedPod.podId)
    : null;
  const selNodeData = selectedPod
    ? TOPO_NODES.find(n => n.id === selectedPod.nodeId)
    : null;

  // AI 분석 결과 (노드 CPU/Mem 기준)
  const aiRisk = selNodeData && selNodeData.cpu >= 80 ? "High" : selNodeData && selNodeData.cpu >= 60 ? "Medium" : "Low";
  const aiCause = selNodeData && selNodeData.cpu >= 80 ? "리소스 과부하 — CPU 포화 상태" : "정상 범위";
  const aiRec = selNodeData && selNodeData.cpu >= 80 ? "Node-1 또는 Node-5로 이동 권장" : "현재 위치 유지";

  return (
    <div className="flex-1 overflow-auto bg-white">
      <TopBar breadcrumb={["Resources", "Topology View"]} />
      <div className="p-5 space-y-4">
        {/* 헤더 */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-[16px] font-bold text-slate-800 mb-1" style={SANS}>Topology View</h1>
            <p className="text-[11px] text-slate-400" style={MONO}>
              클러스터 내 Cluster → Namespace → Deployment → Pod → Node 관계를 시각화합니다.
              <span className="text-indigo-600 cursor-pointer hover:underline ml-1">자세히 알아보기</span>
            </p>
          </div>
          {/* List / Topology 토글 */}
          <div className="flex items-center gap-1 bg-slate-100 rounded-xl p-1">
            <button onClick={() => setViewMode("list")}
              className={`px-4 py-1.5 rounded-lg text-[11px] font-medium cursor-pointer transition-all ${viewMode === "list" ? "bg-white shadow text-slate-800" : "text-slate-500"}`} style={SANS}>
              List
            </button>
            <button onClick={() => setViewMode("topology")}
              className={`px-4 py-1.5 rounded-lg text-[11px] font-medium cursor-pointer transition-all ${viewMode === "topology" ? "bg-slate-800 text-white shadow" : "text-slate-500"}`} style={SANS}>
              Topology
            </button>
          </div>
        </div>

        {viewMode === "list" ? (
          /* List 뷰 */
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-slate-100 text-[8px] uppercase text-slate-400" style={MONO}>
                  <th className="text-left px-4 py-2.5">Node</th>
                  <th className="text-left px-3 py-2.5">Pod</th>
                  <th className="text-left px-3 py-2.5">Namespace</th>
                  <th className="text-left px-3 py-2.5">상태</th>
                  <th className="text-left px-3 py-2.5">CPU</th>
                  <th className="text-left px-3 py-2.5">Memory</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {TOPO_NODES.flatMap(n => n.pods.map(p => (
                  <tr key={p.id} className="hover:bg-slate-50 transition-colors cursor-pointer"
                    onClick={() => { setSelectedPod({ nodeId: n.id, podId: p.id }); setViewMode("topology"); }}>
                    <td className="px-4 py-2.5 font-medium text-slate-600" style={MONO}>{n.label}</td>
                    <td className="px-3 py-2.5 text-indigo-600" style={MONO}>{p.name}</td>
                    <td className="px-3 py-2.5 text-slate-500" style={MONO}>{p.ns}</td>
                    <td className="px-3 py-2.5">
                      <Badge label={p.status} variant={p.status === "Running" ? "healthy" : "unhealthy"} />
                    </td>
                    <td className="px-3 py-2.5 text-slate-600" style={MONO}>{p.cpu ? `${p.cpu}%` : "–"}</td>
                    <td className="px-3 py-2.5 text-slate-600" style={MONO}>{p.mem ? `${p.mem}%` : "–"}</td>
                  </tr>
                )))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Topology 뷰 */
          <div className="flex gap-4 items-start">
            {/* 캔버스 영역 */}
            <div className="flex-1 min-w-0">
              {/* 컨트롤 바 */}
              <div className="flex items-center gap-2 mb-3">
                <button onClick={() => setAutoPlay(v => !v)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium cursor-pointer border transition-colors ${autoPlay ? "bg-slate-800 text-white border-slate-800" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`} style={SANS}>
                  {autoPlay ? "▶ Auto" : "▶ Auto"}
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-[10px] text-slate-600 hover:bg-slate-50 cursor-pointer" style={SANS}>
                  ‖ Pause
                </button>
                <div className="ml-auto text-[9px] text-slate-400" style={MONO}>클릭하여 Pod 선택 → AI 분석</div>
              </div>

              {/* 토폴로지 그래프 (SVG + div 혼합) */}
              <div className="relative bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden"
                style={{ height: 420, backgroundImage: "radial-gradient(circle, #e2e8f0 1px, transparent 1px)", backgroundSize: "20px 20px" }}>

                {/* SVG 연결선 */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                  {/* 클러스터 → 네임스페이스 */}
                  <line x1="50%" y1="60" x2="25%" y2="140" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="5 3" />
                  <line x1="50%" y1="60" x2="75%" y2="140" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="5 3" />
                  {/* 네임스페이스 → 노드들 */}
                  {[22, 40, 58, 76].map((x, i) => (
                    <line key={i} x1={`${i < 2 ? 25 : 75}%`} y1="185" x2={`${x}%`} y2="270" stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="4 3" />
                  ))}
                  {/* 노드 → Pod들 */}
                  <line x1="22%" y1="330" x2="18%" y2="390" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 2" />
                  <line x1="22%" y1="330" x2="26%" y2="390" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 2" />
                  <line x1="40%" y1="330" x2="36%" y2="390" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="3 2" />
                  <line x1="40%" y1="330" x2="44%" y2="390" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="3 2" />
                  <line x1="58%" y1="330" x2="56%" y2="390" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 2" />
                  <line x1="76%" y1="330" x2="76%" y2="390" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3 2" />
                </svg>

                {/* 클러스터 노드 (상단 중앙) */}
                <div className="absolute" style={{ left: "50%", top: 20, transform: "translateX(-50%)" }}>
                  <div className="flex flex-col items-center gap-1">
                    <div className="bg-slate-800 text-white px-3 py-1.5 rounded-xl text-[10px] font-semibold shadow-md whitespace-nowrap" style={MONO}>
                      🌐 production-cluster
                    </div>
                    <div className="text-[8px] text-slate-400" style={MONO}>Cluster</div>
                  </div>
                </div>

                {/* Namespace 노드들 */}
                {[
                  { label: "ns: production", x: "25%" },
                  { label: "ns: monitoring", x: "75%" },
                ].map((ns) => (
                  <div key={ns.label} className="absolute" style={{ left: ns.x, top: 120, transform: "translateX(-50%)" }}>
                    <div className="flex flex-col items-center gap-1">
                      <div className="bg-indigo-700 text-white px-3 py-1.5 rounded-xl text-[9px] font-semibold shadow-md whitespace-nowrap" style={MONO}>
                        {ns.label}
                      </div>
                      <div className="text-[8px] text-slate-400" style={MONO}>Namespace</div>
                    </div>
                  </div>
                ))}

                {/* Node 노드들 */}
                {TOPO_NODES.map((node, i) => {
                  const xs = ["22%", "40%", "58%", "76%"];
                  const colors: Record<string, string> = {
                    "node-1": "bg-emerald-700",
                    "node-2": "bg-amber-600",
                    "node-3": "bg-red-600",
                    "node-5": "bg-emerald-700",
                  };
                  return (
                    <div key={node.id} className="absolute" style={{ left: xs[i], top: 250, transform: "translateX(-50%)" }}>
                      <div className="flex flex-col items-center gap-1">
                        <div className={`${colors[node.id] || "bg-slate-700"} text-white px-2.5 py-1.5 rounded-xl text-[9px] font-semibold shadow-md whitespace-nowrap`} style={MONO}>
                          {node.label}
                        </div>
                        <div className="text-[7px] text-slate-400" style={MONO}>CPU {node.cpu}%</div>
                      </div>
                    </div>
                  );
                })}

                {/* Pod 노드들 */}
                {TOPO_NODES.map((node, ni) => {
                  const nodeXs = ["22%", "40%", "58%", "76%"];
                  return node.pods.map((pod, pi) => {
                    const podX = ni < 2
                      ? `${ni === 0 ? [18, 26][pi] : [36, 44][pi]}%`
                      : ni === 2
                      ? `${[54, 58, 62][pi] || 58}%`
                      : "76%";
                    const isSelected = selectedPod?.nodeId === node.id && selectedPod?.podId === pod.id;
                    const isCrash = pod.status === "CrashLoop";
                    return (
                      <button key={pod.id}
                        onClick={() => setSelectedPod(isSelected ? null : { nodeId: node.id, podId: pod.id })}
                        className="absolute cursor-pointer" style={{ left: podX, top: 370, transform: "translateX(-50%)" }}>
                        <div className="flex flex-col items-center gap-0.5">
                          <div className={`px-2 py-1 rounded-lg text-[8px] font-semibold shadow-sm border-2 transition-all whitespace-nowrap ${
                            isSelected ? "border-indigo-500 bg-indigo-600 text-white scale-110"
                              : isCrash ? "border-red-400 bg-red-50 text-red-700"
                              : "border-slate-300 bg-white text-slate-700 hover:border-indigo-300"}`} style={MONO}>
                            {pod.name.split("-")[0]}
                          </div>
                          <div className={`text-[7px] ${isCrash ? "text-red-500" : "text-slate-400"}`} style={MONO}>
                            {isCrash ? "⚠ Crash" : "● Running"}
                          </div>
                        </div>
                      </button>
                    );
                  });
                })}
              </div>

              {/* AI Placement Analysis (Pod 선택 시) */}
              {selectedPod && selPodData && selNodeData && (
                <div className="mt-4 border-2 border-indigo-200 rounded-2xl overflow-hidden bg-white shadow-md">
                  <div className="px-4 py-3 bg-indigo-600 flex items-center gap-2">
                    <Sparkles size={14} className="text-white" />
                    <span className="text-[12px] font-bold text-white" style={SANS}>AI Placement Analysis</span>
                    <span className="ml-auto text-[9px] text-indigo-200" style={MONO}>{selPodData.name}</span>
                  </div>
                  <div className="px-5 py-4 grid grid-cols-3 gap-4">
                    {[
                      { label: "CPU",    value: `${selNodeData.cpu}%`, c: selNodeData.cpu >= 80 ? "text-red-500" : "text-amber-500" },
                      { label: "Memory", value: `${selNodeData.mem}%`, c: selNodeData.mem >= 80 ? "text-red-500" : "text-amber-500" },
                      { label: "Risk",   value: aiRisk, c: aiRisk === "High" ? "text-red-500 font-bold" : aiRisk === "Medium" ? "text-amber-500" : "text-emerald-600" },
                    ].map(({ label, value, c }) => (
                      <div key={label} className="text-center">
                        <div className="text-[9px] text-slate-400 mb-1 uppercase tracking-wider" style={MONO}>{label}</div>
                        <div className={`text-[18px] font-bold ${c}`} style={SANS}>{value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="border-t border-slate-100 px-5 py-3 space-y-2 text-[10px]" style={MONO}>
                    <div className="flex gap-2">
                      <span className="text-slate-400 w-20 shrink-0">원인:</span>
                      <span className="text-slate-700">{aiCause}</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-slate-400 w-20 shrink-0">권장:</span>
                      <span className={`font-semibold ${aiRisk === "High" ? "text-indigo-600" : "text-emerald-600"}`}>→ {aiRec}</span>
                    </div>
                    {aiRisk === "High" && (
                      <button className="mt-2 w-full py-2 bg-indigo-600 text-white rounded-xl text-[10px] font-semibold cursor-pointer hover:bg-indigo-500 transition-colors" style={SANS}>
                        AI 권장 배치 적용
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 우측 트리 패널 */}
            <div className="w-60 shrink-0 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <div className="text-[11px] font-semibold text-slate-700" style={SANS}>클러스터 트리</div>
              </div>
              <div className="p-3 text-[10px] space-y-1 overflow-y-auto" style={MONO}>
                <div className="text-slate-500 font-semibold mb-2">🌐 production-cluster</div>
                {TOPO_NODES.map(node => (
                  <div key={node.id} className="ml-2">
                    <div className={`flex items-center gap-1.5 py-1 px-2 rounded-lg font-medium cursor-pointer hover:bg-slate-50 ${
                      node.cpu >= 80 ? "text-red-500" : node.cpu >= 60 ? "text-amber-500" : "text-slate-600"}`}>
                      <span>{node.cpu >= 80 ? "🔴" : node.cpu >= 60 ? "🟡" : "🟢"}</span>
                      <span>{node.label}</span>
                      <span className="ml-auto text-[8px] text-slate-400">CPU {node.cpu}%</span>
                    </div>
                    {node.pods.map(pod => {
                      const isSelected = selectedPod?.nodeId === node.id && selectedPod?.podId === pod.id;
                      return (
                        <button key={pod.id}
                          onClick={() => setSelectedPod(isSelected ? null : { nodeId: node.id, podId: pod.id })}
                          className={`w-full text-left ml-4 flex items-center gap-1.5 py-0.5 px-2 rounded-lg cursor-pointer transition-colors ${
                            isSelected ? "bg-indigo-100 text-indigo-700 font-semibold"
                              : pod.status === "CrashLoop" ? "text-red-500 hover:bg-red-50"
                              : "text-slate-500 hover:bg-slate-50"}`}>
                          <span className="text-[8px]">
                            {pod.status === "CrashLoop" ? "⚠" : isSelected ? "◀" : "└"}
                          </span>
                          <span className="truncate">{pod.name.split("-")[0]}</span>
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 1: 클러스터 뷰
// ═══════════════════════════════════════════════════════════════════════════════
function ClusterView() {
  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "클러스터"]} />
      <div className="p-5 space-y-4">
        {/* 필터 바 */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-2 text-[11px] text-slate-400 w-52">
            <Search size={12} /><span>검색</span>
          </div>
          {["클라우드 제공자", "Kube 버전", "그룹", "Health Score"].map((f) => (
            <div key={f} className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-3 py-2 text-[11px] text-slate-500 cursor-pointer hover:border-slate-300">
              <span>{f}</span><ChevronDown size={10} />
            </div>
          ))}
        </div>

        <div className="text-[11px] text-slate-500" style={MONO}>전체 {CLUSTERS.length}개 클러스터 표시 중</div>

        {/* 테이블 */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
          <div className="grid grid-cols-12 px-5 py-2.5 border-b border-slate-100 text-[9px] uppercase tracking-wider text-slate-400" style={MONO}>
            <span className="col-span-1">제공자</span>
            <span className="col-span-2">이름</span>
            <span className="col-span-1"># 노드</span>
            <span className="col-span-2">Pods</span>
            <span className="col-span-2">할당량</span>
            <span className="col-span-1">이슈</span>
            <span className="col-span-1">리스크</span>
            <span className="col-span-1">절감 가능</span>
            <span className="col-span-1">Health</span>
          </div>
          {CLUSTERS.map((c, i) => (
            <div key={i} className="grid grid-cols-12 px-5 py-4 border-b border-slate-50 hover:bg-slate-50 transition-colors items-center">
              <div className="col-span-1">
                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded uppercase ${
                  c.provider === "aws" ? "bg-amber-100 text-amber-700" : c.provider === "gcp" ? "bg-blue-100 text-blue-700" : "bg-sky-100 text-sky-700"
                }`} style={MONO}>{c.provider}</span>
              </div>
              <div className="col-span-2 font-semibold text-[12px] text-slate-800" style={SANS}>{c.name}</div>
              <div className="col-span-1 text-[11px] text-slate-600" style={MONO}>{c.nodes}</div>
              <div className="col-span-2 flex items-center gap-1.5 text-[10px]" style={MONO}>
                <span className="text-amber-600 font-semibold">{c.pods.warning}</span>
                <span className="text-emerald-600 font-semibold">{c.pods.ok}</span>
                <span className="text-slate-400">| {c.pods.total}</span>
              </div>
              <div className="col-span-2">
                <div className="text-[9px] text-slate-500 space-y-0.5" style={MONO}>
                  <div>CPU <span className="text-slate-700">{c.cpu}</span></div>
                  <div>MEM <span className="text-slate-700">{c.mem}</span></div>
                </div>
              </div>
              <div className="col-span-1 text-[12px] font-semibold text-red-500" style={MONO}>{c.issues || "–"}</div>
              <div className="col-span-1 text-[12px] font-semibold text-amber-500" style={MONO}>{c.risks || "–"}</div>
              <div className="col-span-1 text-[10px] text-emerald-600 font-semibold" style={MONO}>{c.savings}</div>
              <div className="col-span-1">
                <div className="relative w-10 h-10">
                  <svg width="40" height="40" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="16" fill="none" stroke="#f1f5f9" strokeWidth="4"/>
                    <circle cx="20" cy="20" r="16" fill="none"
                      stroke={c.health >= 90 ? "#10b981" : c.health >= 75 ? "#f59e0b" : "#ef4444"}
                      strokeWidth="4" strokeDasharray={`${(c.health / 100) * 100.5} 100.5`}
                      strokeLinecap="round" transform="rotate(-90 20 20)" />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-[8px] font-bold text-slate-700" style={MONO}>{c.health}%</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 2: Overview  (발표용 메인 화면)
// ═══════════════════════════════════════════════════════════════════════════════

const OVERVIEW_SERVICES = [
  {
    id: "checkout-api-v2",
    status: "critical" as const,
    replicas: "0/3",
    ns: "production",
    lastDeploy: "23분 전",
    errorRate: "34.2%",
    latency: "2,841ms",
    deployTrigger: true,
    gitCommit: "feat: payment gateway v2 migration",
    events: 5,
  },
  {
    id: "order-api",
    status: "healthy" as const,
    replicas: "3/3",
    ns: "production",
    lastDeploy: "2시간 전",
    errorRate: "0.1%",
    latency: "142ms",
    deployTrigger: false,
    gitCommit: null,
    events: 0,
  },
  {
    id: "inventory-api",
    status: "healthy" as const,
    replicas: "2/2",
    ns: "production",
    lastDeploy: "1일 전",
    errorRate: "0.0%",
    latency: "89ms",
    deployTrigger: false,
    gitCommit: null,
    events: 0,
  },
  {
    id: "web-frontend",
    status: "warning" as const,
    replicas: "2/3",
    ns: "production",
    lastDeploy: "45분 전",
    errorRate: "2.7%",
    latency: "621ms",
    deployTrigger: false,
    gitCommit: "chore: bump node version",
    events: 2,
  },
  {
    id: "recommend-worker",
    status: "healthy" as const,
    replicas: "1/1",
    ns: "production",
    lastDeploy: "3시간 전",
    errorRate: "0.0%",
    latency: "204ms",
    deployTrigger: false,
    gitCommit: null,
    events: 0,
  },
];

const ERROR_SPARK = Array.from({ length: 20 }, (_, i) => ({
  v: i < 14 ? Math.random() * 3 : 20 + Math.random() * 18,
}));
const LATENCY_SPARK = Array.from({ length: 20 }, (_, i) => ({
  v: i < 14 ? 100 + Math.random() * 60 : 800 + Math.random() * 600,
}));

function StatusDot({ status }: { status: "critical" | "warning" | "healthy" }) {
  const cls = {
    critical: "bg-red-500 shadow-[0_0_6px_2px_rgba(239,68,68,0.5)]",
    warning:  "bg-amber-400 shadow-[0_0_6px_2px_rgba(251,191,36,0.4)]",
    healthy:  "bg-emerald-500",
  }[status];
  return <span className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${cls}`} />;
}

function Overview({ onSelectService }: { onSelectService?: (id: number) => void }) {
  const [selected, setSelected] = useState<string>("checkout-api-v2");
  const [aiExpanded, setAiExpanded] = useState(true);
  const sel = OVERVIEW_SERVICES.find(s => s.id === selected)!;

  const summaryCards = [
    { label: "전체 클러스터",  value: "5",  sub: "AWS · GCP · Azure",      icon: Layers,     color: "text-indigo-600", bg: "bg-indigo-50" },
    { label: "전체 서비스",    value: "24", sub: "3개 클러스터",             icon: LayoutGrid,  color: "text-slate-600",  bg: "bg-slate-100" },
    { label: "정상 서비스",    value: "21", sub: "87.5%",                   icon: CheckCircle2,color: "text-emerald-600",bg: "bg-emerald-50" },
    { label: "위험 서비스",    value: "1",  sub: "즉시 확인 필요",           icon: XCircle,    color: "text-red-600",    bg: "bg-red-50" },
    { label: "최근 배포",      value: "3",  sub: "지난 1시간",               icon: RefreshCw,  color: "text-amber-600",  bg: "bg-amber-50" },
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[#f6f8fb]">
      {/* 상단 바 */}
      <div className="h-11 shrink-0 border-b border-slate-200 bg-white flex items-center justify-between px-5">
        <div className="flex items-center gap-1 text-[11px]" style={SANS}>
          <span className="text-slate-400">Production</span>
          <ChevronRight size={10} className="text-slate-300" />
          <span className="text-slate-700 font-semibold">Overview</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-red-50 border border-red-200 rounded-lg text-[10px] text-red-600 font-semibold animate-pulse" style={MONO}>
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
            1개 서비스 장애 중
          </div>
          <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><Search size={14} /></button>
          <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer relative">
            <Bell size={14} />
            <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-red-500" />
          </button>
          <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer"><Settings size={14} /></button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="p-5 space-y-4">

          {/* ── 요약 카드 5개 ── */}
          <div className="grid grid-cols-5 gap-3">
            {summaryCards.map((c) => {
              const Icon = c.icon;
              return (
                <div key={c.label} className={`bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-start gap-3 ${
                  c.label === "위험 서비스" ? "border-red-200 bg-red-50/40 ring-1 ring-red-100" : ""
                }`}>
                  <div className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center shrink-0`}>
                    <Icon size={15} className={c.color} />
                  </div>
                  <div>
                    <div className={`text-[22px] font-bold leading-tight ${
                      c.label === "위험 서비스" ? "text-red-600" : "text-slate-800"
                    }`} style={SANS}>{c.value}</div>
                    <div className="text-[10px] text-slate-500 leading-snug" style={MONO}>{c.label}</div>
                    <div className="text-[9px] text-slate-400 mt-0.5" style={MONO}>{c.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── 메인 2컬럼: 서비스 목록 + AI 패널 ── */}
          <div className="flex gap-4 items-start">

            {/* 왼쪽: 서비스 앨범형 카드 그리드 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[12px] font-semibold text-slate-700" style={SANS}>서비스 상태</span>
                <div className="flex items-center gap-1.5 text-[9px]" style={MONO}>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Critical</span>
                  <span className="flex items-center gap-1 ml-2"><span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />Warning</span>
                  <span className="flex items-center gap-1 ml-2"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />Healthy</span>
                </div>
              </div>

              {/* 앨범형 카드 그리드 */}
              <div className="grid grid-cols-3 gap-3">
                {OVERVIEW_SERVICES.map((svc) => {
                  const isCritical = svc.status === "critical";
                  const isWarning  = svc.status === "warning";
                  const isSelected = svc.id === selected;

                  return (
                    <button key={svc.id}
                      onClick={() => {
                        setSelected(svc.id);
                        if (isCritical) setAiExpanded(false);
                      }}
                      className={`text-left rounded-xl border-2 shadow-sm transition-all cursor-pointer hover:shadow-md overflow-hidden
                        ${isCritical ? "border-red-400 bg-gradient-to-br from-red-50 to-red-100/40"
                          : isWarning ? "border-amber-300 bg-gradient-to-br from-amber-50 to-amber-100/30"
                          : "border-slate-200 bg-white hover:border-slate-300"}
                        ${isSelected && isCritical ? "ring-2 ring-red-400 ring-offset-1" : ""}
                      `}>
                      {/* 상단 컬러 바 */}
                      <div className={`h-1.5 w-full ${isCritical ? "bg-red-500" : isWarning ? "bg-amber-400" : "bg-emerald-500"}`} />

                      <div className="p-3.5">
                        {/* 서비스명 + 상태 */}
                        <div className="flex items-start justify-between mb-2.5">
                          <div className="flex items-center gap-1.5 min-w-0 flex-1">
                            <StatusDot status={svc.status} />
                            <span className={`text-[11px] font-bold truncate ${isCritical ? "text-red-700" : isWarning ? "text-amber-700" : "text-slate-800"}`} style={SANS}>
                              {svc.id}
                            </span>
                          </div>
                          {svc.events > 0 && (
                            <span className={`shrink-0 w-5 h-5 rounded-full text-[9px] font-bold flex items-center justify-center ${isCritical ? "bg-red-500 text-white" : "bg-amber-400 text-white"}`} style={MONO}>
                              {svc.events}
                            </span>
                          )}
                        </div>

                        {/* 상태 배지 */}
                        <div className="mb-3">
                          {isCritical && <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500 text-white text-[8px] font-bold rounded" style={MONO}><AlertTriangle size={8} />CRITICAL</span>}
                          {isWarning  && <span className="inline-block px-2 py-0.5 bg-amber-100 text-amber-700 border border-amber-300 text-[8px] font-bold rounded" style={MONO}>WARNING</span>}
                          {!isCritical && !isWarning && <span className="inline-block px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[8px] font-semibold rounded" style={MONO}>HEALTHY</span>}
                        </div>

                        {/* 미니 스파크라인 (Critical) */}
                        {isCritical && (
                          <div className="h-12 mb-2 -mx-1">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={ERROR_SPARK}>
                                <defs>
                                  <linearGradient id={`errG-${svc.id}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0.4} />
                                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                                  </linearGradient>
                                </defs>
                                <Area type="monotone" dataKey="v" stroke="#ef4444" strokeWidth={1.5} fill={`url(#errG-${svc.id})`} dot={false} />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                        )}

                        {/* 핵심 메트릭 */}
                        <div className="space-y-1 text-[9px]" style={MONO}>
                          <div className="flex justify-between">
                            <span className="text-slate-400">에러율</span>
                            <span className={`font-bold ${isCritical ? "text-red-600" : isWarning ? "text-amber-600" : "text-slate-600"}`}>{svc.errorRate}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">응답시간</span>
                            <span className={`font-bold ${isCritical ? "text-red-600" : isWarning ? "text-amber-600" : "text-slate-600"}`}>{svc.latency}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">Replicas</span>
                            <span className={`font-bold ${isCritical ? "text-red-600" : "text-slate-600"}`}>{svc.replicas}</span>
                          </div>
                        </div>

                        {/* 배포 정보 */}
                        <div className="mt-2.5 pt-2 border-t border-current/10 flex items-center gap-1 text-[9px] text-slate-400" style={MONO}>
                          <Clock size={8} className="shrink-0" />
                          <span className="truncate">배포 {svc.lastDeploy}</span>
                          {svc.deployTrigger && <span className="ml-auto shrink-0 text-red-500 font-bold">배포 후 장애</span>}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* 슬라이드 상세 패널: Critical 카드 클릭 시 */}
              {selected === "checkout-api-v2" && (
                <div className="mt-3 border-2 border-red-300 rounded-xl bg-white overflow-hidden shadow-md"
                  style={{ animation: "slideDown 0.2s ease" }}>
                  <style>{`@keyframes slideDown { from { opacity:0; transform:translateY(-8px) } to { opacity:1; transform:translateY(0) } }`}</style>
                  <div className="px-4 py-3 bg-red-600 flex items-center gap-2">
                    <AlertTriangle size={13} className="text-white" />
                    <span className="text-[12px] font-bold text-white" style={SANS}>checkout-api-v2 — 장애 상세</span>
                    <span className="ml-auto text-[9px] text-red-200" style={MONO}>배포 후 10분 뒤 장애 감지</span>
                    <button onClick={() => setSelected("")} className="ml-2 text-red-200 hover:text-white cursor-pointer"><X size={14} /></button>
                  </div>
                  <div className="p-4 grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[10px] font-semibold text-slate-600 mb-2" style={SANS}>에러율 급증</div>
                      <div className="h-20">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={ERROR_SPARK}>
                            <defs>
                              <linearGradient id="errGrad2ov" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#fef2f2" />
                            <YAxis tick={{ fontSize: 7, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={24} />
                            <Tooltip contentStyle={{ fontSize: 9, borderRadius: 6 }} />
                            <Area type="monotone" dataKey="v" stroke="#ef4444" strokeWidth={2} fill="url(#errGrad2ov)" dot={false} name="에러율 %" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex justify-between text-[9px] mt-1" style={MONO}>
                        <span className="text-slate-400">배포 전 <span className="text-slate-600">0.8%</span></span>
                        <span className="text-red-600 font-bold">배포 후 34.2% ↑</span>
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] font-semibold text-slate-600 mb-2" style={SANS}>응답 시간 증가</div>
                      <div className="h-20">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={LATENCY_SPARK}>
                            <defs>
                              <linearGradient id="latGradov" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#f97316" stopOpacity={0.3} />
                                <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#fff7ed" />
                            <YAxis tick={{ fontSize: 7, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={24} />
                            <Tooltip contentStyle={{ fontSize: 9, borderRadius: 6 }} />
                            <Area type="monotone" dataKey="v" stroke="#f97316" strokeWidth={2} fill="url(#latGradov)" dot={false} name="응답시간 ms" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex justify-between text-[9px] mt-1" style={MONO}>
                        <span className="text-slate-400">배포 전 <span className="text-slate-600">142ms</span></span>
                        <span className="text-orange-600 font-bold">배포 후 2,841ms ↑</span>
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-red-100 px-4 py-3 flex items-center gap-3">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <GitBranch size={11} className="text-slate-400 shrink-0" />
                      <span className="text-[9px] text-slate-500 truncate" style={MONO}>feat: payment gateway v2 migration</span>
                    </div>
                    <button onClick={() => onSelectService && onSelectService(1)}
                      className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-[10px] font-semibold cursor-pointer transition-colors" style={SANS}>
                      <Sparkles size={11} />AI로 원인 분석
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* 오른쪽: AI 요약 패널 */}
            <div className="w-72 shrink-0">
              <div className="bg-[#0f1628] rounded-xl overflow-hidden shadow-lg border border-white/10">
                {/* 헤더 */}
                <div className="px-4 py-3 flex items-center gap-2 border-b border-white/10">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center">
                    <Sparkles size={13} className="text-white" />
                  </div>
                  <div>
                    <div className="text-[12px] font-bold text-white" style={SANS}>Klaudia AI</div>
                    <div className="text-[9px] text-indigo-300" style={MONO}>실시간 장애 분석 중</div>
                  </div>
                  <button onClick={() => setAiExpanded(v => !v)}
                    className="ml-auto text-slate-400 hover:text-white cursor-pointer transition-colors">
                    <ChevronDown size={14} className={`transition-transform ${aiExpanded ? "rotate-180" : ""}`} />
                  </button>
                </div>

                {/* AI 인사이트 */}
                {aiExpanded && (
                  <div className="p-4 space-y-3">
                    {/* 인사이트 1 */}
                    <div className="rounded-xl bg-red-950/60 border border-red-500/30 p-3">
                      <div className="flex items-start gap-2 mb-2">
                        <AlertTriangle size={12} className="text-red-400 shrink-0 mt-0.5" />
                        <span className="text-[10px] font-semibold text-red-300" style={SANS}>배포 직후 이상 감지</span>
                      </div>
                      <p className="text-[10px] text-slate-300 leading-relaxed" style={MONO}>
                        결제 서비스에서 <span className="text-red-300 font-semibold">배포 직후</span> 에러율과 응답 시간이 동시에 증가했습니다.
                      </p>
                    </div>

                    {/* 인사이트 2 */}
                    <div className="rounded-xl bg-amber-950/50 border border-amber-500/30 p-3">
                      <div className="flex items-start gap-2 mb-2">
                        <GitBranch size={12} className="text-amber-400 shrink-0 mt-0.5" />
                        <span className="text-[10px] font-semibold text-amber-300" style={SANS}>Git 변경 연관</span>
                      </div>
                      <p className="text-[10px] text-slate-300 leading-relaxed" style={MONO}>
                        최근 Git 변경 <span className="text-amber-300">"payment gateway v2 migration"</span>과 연결된 장애 가능성이 있습니다.
                      </p>
                    </div>

                    {/* 인사이트 3 */}
                    <div className="rounded-xl bg-indigo-950/60 border border-indigo-500/30 p-3">
                      <div className="flex items-start gap-2 mb-2">
                        <TrendingDown size={12} className="text-indigo-400 shrink-0 mt-0.5" />
                        <span className="text-[10px] font-semibold text-indigo-300" style={SANS}>영향 범위</span>
                      </div>
                      <p className="text-[10px] text-slate-300 leading-relaxed" style={MONO}>
                        checkout-api-v2 장애로 인해 <span className="text-indigo-300 font-semibold">order-api</span> 연쇄 영향 가능성 감지. 즉시 확인 필요.
                      </p>
                    </div>

                    {/* 권고 조치 */}
                    <div className="border-t border-white/10 pt-3">
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider mb-2" style={MONO}>AI 권고 조치</div>
                      <div className="space-y-1.5">
                        {[
                          { icon: "1", action: "이전 버전으로 즉시 롤백", color: "text-red-400" },
                          { icon: "2", action: "payment gateway 설정 확인", color: "text-amber-400" },
                          { icon: "3", action: "에러 로그 상세 분석", color: "text-indigo-400" },
                        ].map((step) => (
                          <div key={step.icon} className="flex items-center gap-2 text-[9px]" style={MONO}>
                            <span className={`w-4 h-4 rounded-full border flex items-center justify-center text-[8px] font-bold shrink-0 ${step.color} border-current`}>{step.icon}</span>
                            <span className="text-slate-300">{step.action}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 자세히 보기 버튼 */}
                    <button
                      onClick={() => onSelectService && onSelectService(1)}
                      className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-[11px] font-semibold cursor-pointer transition-colors" style={SANS}>
                      <ArrowRight size={13} />
                      자세히 보기
                    </button>
                  </div>
                )}
              </div>

              {/* 최근 이벤트 요약 */}
              <div className="mt-3 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-4 py-2.5 border-b border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-700" style={SANS}>최근 이벤트</span>
                </div>
                <div className="divide-y divide-slate-50">
                  {[
                    { icon: "error", time: "23분 전", msg: "checkout-api-v2 Pod CrashLoopBackOff" },
                    { icon: "warn",  time: "24분 전", msg: "checkout-api-v2 배포 완료" },
                    { icon: "warn",  time: "46분 전", msg: "web-frontend Pod 1개 Pending" },
                    { icon: "ok",    time: "2시간 전", msg: "order-api 배포 성공" },
                  ].map((ev, i) => (
                    <div key={i} className="flex items-center gap-2.5 px-4 py-2.5 hover:bg-slate-50 transition-colors cursor-pointer">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                        ev.icon === "error" ? "bg-red-100" : ev.icon === "warn" ? "bg-amber-100" : "bg-emerald-100"
                      }`}>
                        {ev.icon === "error" && <XCircle size={10} className="text-red-500" />}
                        {ev.icon === "warn"  && <AlertTriangle size={10} className="text-amber-500" />}
                        {ev.icon === "ok"    && <CheckCircle2 size={10} className="text-emerald-500" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[9px] text-slate-600 truncate" style={MONO}>{ev.msg}</div>
                        <div className="text-[8px] text-slate-400" style={MONO}>{ev.time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 3: Service 목록 — 화면 2 (장애 서비스 선택)
// ═══════════════════════════════════════════════════════════════════════════════

// 서비스 연결 토폴로지 노드 정의 (key 기반으로 엣지 연결)
const TOPO_FLOW = [
  { key: "frontend",  svcId: 4, name: "web-frontend",    x: 120,  y: 90,  status: "warning",  isDb: false },
  { key: "checkout",  svcId: 1, name: "checkout-api-v2", x: 380,  y: 90,  status: "critical", isDb: false },
  { key: "order",     svcId: 2, name: "order-api",        x: 650,  y: 90,  status: "healthy",  isDb: false },
  { key: "payment",   svcId: 8, name: "payment-gateway",  x: 240,  y: 270, status: "healthy",  isDb: false },
  { key: "inventory", svcId: 3, name: "inventory-api",    x: 520,  y: 270, status: "healthy",  isDb: false },
  { key: "recommend", svcId: 5, name: "recommend-worker", x: 780,  y: 270, status: "healthy",  isDb: false },
  { key: "db",        svcId: null, name: "PostgreSQL DB", x: 160,  y: 430, status: "healthy",  isDb: true  },
  { key: "redis",     svcId: null, name: "Redis Cache",   x: 460,  y: 430, status: "healthy",  isDb: true  },
];

const TOPO_EDGES = [
  { from: "frontend",  to: "checkout"  },
  { from: "checkout",  to: "order"     },
  { from: "checkout",  to: "payment"   },
  { from: "checkout",  to: "db"        },
  { from: "order",     to: "inventory" },
  { from: "order",     to: "recommend" },
  { from: "order",     to: "redis"     },
  { from: "payment",   to: "db"        },
];

function getTopoPos(key: string) {
  const n = TOPO_FLOW.find(n => n.key === key);
  return n ? { x: n.x, y: n.y } : { x: 0, y: 0 };
}

function ServiceGrid({
  onSelect,
  onNewAI,
  recovered = false,
}: {
  onSelect: (id: number) => void;
  onNewAI: () => void;
  recovered?: boolean;
}) {
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan]   = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [panStart, setPanStart]   = useState({ x: 0, y: 0 });

  const colorMap: Record<string, { node: string; border: string; ring: string; shadow: string }> = {
    critical: { node: "bg-red-600",     border: "border-red-500",    ring: "ring-red-400",    shadow: "shadow-red-300" },
    warning:  { node: "bg-amber-400",   border: "border-amber-400",  ring: "ring-amber-300",  shadow: "" },
    healthy:  { node: "bg-emerald-500", border: "border-emerald-400",ring: "ring-emerald-300",shadow: "" },
  };

  const CANVAS_W = 960;
  const CANVAS_H = 540;

  function handleWheel(e: React.WheelEvent) {
    e.preventDefault();
    setZoom(z => Math.min(2, Math.max(0.4, z - e.deltaY * 0.001)));
  }
  function handleMouseDown(e: React.MouseEvent) {
    setDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    setPanStart({ ...pan });
  }
  function handleMouseMove(e: React.MouseEvent) {
    if (!dragging) return;
    setPan({ x: panStart.x + e.clientX - dragStart.x, y: panStart.y + e.clientY - dragStart.y });
  }
  function handleMouseUp() { setDragging(false); }

  return (
    <div className="flex-1 overflow-auto bg-[#f6f8fb]">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "Services"]} onAIClick={onNewAI} showAIBtn />
      <div className="p-5 space-y-5">

        {/* ── 헤더 ── */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[14px] font-bold text-slate-800" style={SANS}>서비스 연결 구조</h2>
            <p className="text-[11px] text-slate-500 mt-0.5" style={MONO}>서비스 간 연결을 확인하고 장애 위치를 추적합니다 · 드래그로 이동 · 휠로 확대/축소</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-[10px] bg-white border border-slate-200 rounded-lg px-2 py-1" style={MONO}>
              <button onClick={() => setZoom(z => Math.min(2, z + 0.1))} className="px-1.5 py-0.5 hover:bg-slate-100 rounded cursor-pointer">+</button>
              <span className="w-10 text-center text-slate-500">{Math.round(zoom * 100)}%</span>
              <button onClick={() => setZoom(z => Math.max(0.4, z - 0.1))} className="px-1.5 py-0.5 hover:bg-slate-100 rounded cursor-pointer">−</button>
              <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} className="ml-1 px-1.5 py-0.5 hover:bg-slate-100 rounded cursor-pointer text-indigo-500">⟳</button>
            </div>
            <div className="flex items-center gap-1.5 text-[10px]" style={MONO}>
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> Critical
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block ml-2" /> Warning
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block ml-2" /> Healthy
            </div>
          </div>
        </div>

        {/* ── 서비스 토폴로지 그래프 ── */}
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-2">
            <Globe size={14} className="text-slate-400" />
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>서비스 흐름 — production 클러스터</span>
            <span className="ml-auto text-[10px] bg-red-50 text-red-600 border border-red-200 px-2 py-0.5 rounded font-semibold" style={MONO}>
              ⚠ 1개 서비스 장애 중
            </span>
          </div>

          {/* pan/zoom 캔버스 */}
          <div
            className={`relative overflow-hidden select-none ${dragging ? "cursor-grabbing" : "cursor-grab"}`}
            style={{ height: 480, background: "radial-gradient(circle, #e2e8f0 1px, transparent 1px) #f8fafc", backgroundSize: "24px 24px" }}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}>

            {/* 레이어 배경 힌트 */}
            <div className="absolute top-3 left-4 flex flex-col gap-1 pointer-events-none z-10">
              {[
                { label: "Client / Frontend", color: "bg-amber-50 border-amber-200 text-amber-600" },
                { label: "API Layer",          color: "bg-indigo-50 border-indigo-200 text-indigo-600" },
                { label: "Service Layer",      color: "bg-slate-50 border-slate-200 text-slate-500" },
                { label: "Data Layer",         color: "bg-emerald-50 border-emerald-200 text-emerald-600" },
              ].map(l => (
                <span key={l.label} className={`inline-flex items-center gap-1 text-[8px] font-semibold px-1.5 py-0.5 rounded border ${l.color}`} style={MONO}>{l.label}</span>
              ))}
            </div>

            {/* 변환 컨테이너 */}
            <div style={{ transform: `translate(${pan.x}px,${pan.y}px) scale(${zoom})`, transformOrigin: "top left", width: CANVAS_W, height: CANVAS_H, position: "absolute", top: 0, left: 0 }}>

              {/* SVG 엣지 */}
              <svg width={CANVAS_W} height={CANVAS_H} className="absolute inset-0 pointer-events-none">
                <defs>
                  <marker id="arr-normal" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#94a3b8" />
                  </marker>
                  <marker id="arr-critical" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L0,6 L6,3 z" fill="#ef4444" />
                  </marker>
                </defs>
                {TOPO_EDGES.map((e, i) => {
                  const f = getTopoPos(e.from);
                  const t = getTopoPos(e.to);
                  const isCritEdge = e.from === "checkout" || e.to === "checkout";
                  // mid control point for slight curve
                  const mx = (f.x + t.x) / 2;
                  const my = (f.y + t.y) / 2;
                  const dx = t.x - f.x; const dy = t.y - f.y;
                  const len = Math.sqrt(dx * dx + dy * dy);
                  // shorten line by 75px from each end
                  const ux = dx / len; const uy = dy / len;
                  const x1 = f.x + ux * 75; const y1 = f.y + uy * 75;
                  const x2 = t.x - ux * 75; const y2 = t.y - uy * 75;
                  return (
                    <g key={i}>
                      <line x1={x1} y1={y1} x2={x2} y2={y2}
                        stroke={isCritEdge ? "#fca5a5" : "#cbd5e1"}
                        strokeWidth={isCritEdge ? 2.5 : 1.5}
                        strokeDasharray={isCritEdge ? "7 4" : "0"}
                        markerEnd={isCritEdge ? "url(#arr-critical)" : "url(#arr-normal)"}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* 서비스 노드 */}
              {TOPO_FLOW.map((node) => {
                const colors = colorMap[node.status];
                const isCritical = node.status === "critical";
                const isHovered  = hoveredKey === node.key;
                const svc = node.svcId ? SERVICES.find(s => s.id === node.svcId) : null;

                return (
                  <div key={node.key}
                    className="absolute"
                    style={{ left: node.x, top: node.y, transform: "translate(-50%, -50%)", zIndex: isCritical ? 10 : 1 }}
                    onMouseEnter={() => setHoveredKey(node.key)}
                    onMouseLeave={() => setHoveredKey(null)}
                    onMouseDown={e => e.stopPropagation()}
                    onClick={() => svc && onSelect(svc.id)}>

                    {/* 크리티컬 펄스 링 */}
                    {isCritical && (
                      <div className="absolute inset-0 rounded-2xl animate-ping bg-red-400 opacity-20" style={{ transform: "scale(1.5)" }} />
                    )}

                    <div className={`relative flex flex-col items-center gap-1.5 px-5 py-3 rounded-2xl border-2 shadow-lg transition-all
                      ${colors.node} ${colors.border}
                      ${isHovered ? `ring-3 ${colors.ring} ring-offset-2 scale-110 shadow-xl ${colors.shadow}` : ""}
                      ${isCritical ? "shadow-red-400/40 shadow-xl cursor-pointer" : svc ? "cursor-pointer" : "cursor-default"}
                    `} style={{ minWidth: 150 }}>
                      {node.isDb
                        ? <Database size={15} className="text-white/80" />
                        : isCritical
                        ? <AlertTriangle size={15} className="text-white animate-pulse" />
                        : node.status === "warning"
                        ? <AlertTriangle size={14} className="text-white/90" />
                        : <Server size={13} className="text-white/80" />}
                      <span className="text-[11px] font-bold text-white whitespace-nowrap" style={SANS}>{node.name}</span>
                      {svc && (
                        <div className="flex items-center gap-1 text-[9px] text-white/75" style={MONO}>
                          <span>{svc.replicas}</span><span>·</span><span>{svc.errorRate}</span>
                        </div>
                      )}
                      {isCritical && (
                        <span className="text-[8px] bg-white/25 text-white rounded-lg px-2 py-0.5 font-bold animate-pulse" style={MONO}>CRITICAL</span>
                      )}
                    </div>

                    {/* 툴팁 */}
                    {isHovered && svc && (
                      <div className="absolute z-30 bottom-full mb-3 left-1/2 -translate-x-1/2 bg-slate-900 text-white rounded-xl p-3 text-[9px] shadow-2xl whitespace-nowrap pointer-events-none" style={MONO}>
                        <div className="font-bold text-[10px] mb-1.5 border-b border-white/20 pb-1.5">{svc.name}</div>
                        <div className="space-y-0.5">
                          <div>에러율 <span className={isCritical ? "text-red-300 font-bold" : "text-emerald-300 font-semibold"}>{svc.errorRate}</span></div>
                          <div>응답시간 <span className={isCritical ? "text-red-300 font-bold" : "text-slate-300"}>{svc.latency}</span></div>
                          <div>Replicas <span className="text-slate-300">{svc.replicas}</span></div>
                          <div>배포 <span className="text-slate-300">{svc.updated}</span></div>
                        </div>
                        {isCritical && <div className="text-red-300 font-bold mt-1.5 pt-1.5 border-t border-white/20">⚠ 클릭하여 장애 상세 확인</div>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── 서비스 카드 목록 ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[12px] font-semibold text-slate-700" style={SANS}>서비스 목록 ({SERVICES.length}개)</span>
            <div className="flex items-center gap-1.5 text-[10px]" style={MONO}>
              <span className="bg-red-100 text-red-600 px-2 py-0.5 rounded font-semibold">Critical 1</span>
              <span className="bg-amber-100 text-amber-600 px-2 py-0.5 rounded font-semibold">Warning 1</span>
              <span className="bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded font-semibold">Healthy {SERVICES.filter(s => s.healthy).length}</span>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            {SERVICES.map((svc) => {
              const isCritical = svc.id === 1 && !recovered;
              const isWarning  = svc.id === 4;
              const isRecovered = svc.id === 1 && recovered;
              const borderCls  = isCritical
                ? "border-red-400 bg-red-50 hover:border-red-500 shadow-red-100"
                : isWarning
                ? "border-amber-300 bg-amber-50/50 hover:border-amber-400"
                : isRecovered
                ? "border-emerald-400 bg-emerald-50/40 hover:border-emerald-500"
                : "border-slate-200 bg-white hover:border-emerald-300";

              return (
                <button key={svc.id} onClick={() => onSelect(svc.id)}
                  className={`text-left p-4 rounded-xl border-2 shadow-sm transition-all cursor-pointer hover:shadow-md relative overflow-hidden ${borderCls}`}>

                  {/* 크리티컬 강조 스트라이프 */}
                  {isCritical && (
                    <div className="absolute top-0 left-0 right-0 h-1 bg-red-500" />
                  )}

                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${isCritical ? "bg-red-500 shadow-[0_0_4px_1px_rgba(239,68,68,0.6)]" : isWarning ? "bg-amber-400" : "bg-emerald-500"}`} />
                      <span className={`text-[12px] font-bold leading-tight ${isCritical ? "text-red-700" : isWarning ? "text-amber-700" : "text-slate-800"}`} style={SANS}>
                        {svc.name}
                      </span>
                    </div>
                    <ChevronRight size={12} className="text-slate-300 shrink-0 mt-0.5" />
                  </div>

                  <div className="flex items-center gap-1.5 mb-2.5">
                    {isCritical   && <span className="px-1.5 py-0.5 bg-red-500 text-white text-[8px] font-bold rounded" style={MONO}>CRITICAL</span>}
                    {isWarning    && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 border border-amber-300 text-[8px] font-bold rounded" style={MONO}>WARNING</span>}
                    {isRecovered  && <span className="flex items-center gap-0.5 px-1.5 py-0.5 bg-emerald-500 text-white text-[8px] font-bold rounded" style={MONO}><CheckCircle2 size={8} />복구됨</span>}
                    {!isCritical && !isWarning && !isRecovered && <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[8px] font-semibold rounded" style={MONO}>HEALTHY</span>}
                    {svc.issue && !isRecovered && <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 text-[8px] rounded" style={MONO}>{svc.issue}</span>}
                  </div>

                  <div className="grid grid-cols-2 gap-1 text-[9px] text-slate-500 mb-2" style={MONO}>
                    <span>Pod <strong className={isCritical ? "text-red-600" : "text-slate-700"}>{svc.replicas}</strong></span>
                    <span>에러 <strong className={isCritical ? "text-red-600" : isWarning ? "text-amber-600" : "text-slate-600"}>{svc.errorRate}</strong></span>
                    <span>응답 <strong className={isCritical ? "text-red-600" : "text-slate-600"}>{svc.latency}</strong></span>
                    <span>배포 {svc.updated}</span>
                  </div>

                  {/* 크리티컬 전용 경고 문구 */}
                  {isCritical && (
                    <div className="flex items-center gap-1.5 pt-2 border-t border-red-200">
                      <AlertTriangle size={10} className="text-red-500 shrink-0" />
                      <span className="text-[9px] text-red-600 font-semibold" style={MONO}>최근 배포 10분 후 장애 감지</span>
                    </div>
                  )}
                  {isRecovered && (
                    <div className="flex items-center gap-1.5 pt-2 border-t border-emerald-200">
                      <CheckCircle2 size={10} className="text-emerald-500 shrink-0" />
                      <span className="text-[9px] text-emerald-600 font-semibold" style={MONO}>PR #1235 적용 — 정상 복구</span>
                    </div>
                  )}
                  {isWarning && (
                    <div className="flex items-center gap-1.5 pt-2 border-t border-amber-200">
                      <AlertTriangle size={10} className="text-amber-500 shrink-0" />
                      <span className="text-[9px] text-amber-600" style={MONO}>Pod 1개 Pending</span>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 4: Service 상세 — 화면 3
// ═══════════════════════════════════════════════════════════════════════════════

const ERR_BEFORE = Array.from({ length: 12 }, (_, i) => ({ t: `${i}m`, v: 0.8 + Math.random() * 0.5 }));
const ERR_AFTER  = Array.from({ length: 8  }, (_, i) => ({ t: `${i+12}m`, v: 4 + i * 0.55 + Math.random() * 0.4 }));
const ERR_DATA   = [...ERR_BEFORE, ...ERR_AFTER];

const LAT_BEFORE = Array.from({ length: 12 }, (_, i) => ({ t: `${i}m`, v: 160 + Math.random() * 40 }));
const LAT_AFTER  = Array.from({ length: 8  }, (_, i) => ({ t: `${i+12}m`, v: 500 + i * 250 + Math.random() * 100 }));
const LAT_DATA   = [...LAT_BEFORE, ...LAT_AFTER];

const DETAIL_EVENTS = [
  { time: "오전 11:23", icon: "error", type: "CrashLoopBackOff",    msg: "checkout-v2-2 재시작 6회 반복 — exit code 1" },
  { time: "오전 11:22", icon: "error", type: "OOMKilled",           msg: "checkout-v2-3 메모리 한도 초과 종료 (256Mi)" },
  { time: "오전 11:21", icon: "warn",  type: "Readiness Probe Fail",msg: "checkout-v2-2 /health 응답 없음 — timeout 5s" },
  { time: "오전 11:20", icon: "warn",  type: "DB Connection Error",  msg: "connection pool exhausted — max 5 connections" },
  { time: "오전 11:13", icon: "info",  type: "Deploy",              msg: "image: v1.4.1 → v1.4.2  배포 시작" },
  { time: "오전 11:12", icon: "ok",    type: "Service Discovered",   msg: "checkout-api-v2 v1.4.1 정상 운영 확인" },
];

const PODS_DATA = [
  { name: "checkout-v2-1", status: "Running",   ready: true,  restarts: 0, memory: "211Mi / 256Mi", cpu: "34m / 500m", node: "node-2" },
  { name: "checkout-v2-2", status: "CrashLoop", ready: false, restarts: 6, memory: "0Mi / 256Mi",   cpu: "0m / 500m",  node: "node-3" },
  { name: "checkout-v2-3", status: "OOMKilled",  ready: false, restarts: 3, memory: "256Mi / 256Mi", cpu: "420m / 500m",node: "node-3" },
];

const LOG_LINES = [
  { t: "11:23:04", level: "ERROR", msg: "DB timeout after 30s: connection pool exhausted (pool size: 5)" },
  { t: "11:23:03", level: "ERROR", msg: "Failed to acquire connection from pool after 30000ms" },
  { t: "11:23:01", level: "WARN",  msg: "Readiness probe failed: GET /health HTTP/1.1 504 Gateway Timeout" },
  { t: "11:22:58", level: "ERROR", msg: "java.sql.SQLTransientConnectionException: pool exhausted" },
  { t: "11:22:55", level: "INFO",  msg: "Attempting DB reconnect... retry 6/6" },
  { t: "11:22:50", level: "ERROR", msg: "Out of memory: Kill process 1 (java) score 1000 or sacrifice child" },
  { t: "11:22:44", level: "WARN",  msg: "High heap usage: 248Mi / 256Mi (96.8%)" },
  { t: "11:22:40", level: "INFO",  msg: "Application started in 3.241s — connecting to DB..." },
];

const CHANGES_DATA = [
  { label: "PR / 커밋", key: "#1234",           prev: "v1.4.1",    next: "v1.4.2",  type: "deploy",  danger: false },
  { label: "이미지",    key: "image",            prev: "v1.4.1",    next: "v1.4.2",  type: "version", danger: false },
  { label: "DB_POOL_SIZE", key: "env",          prev: "20",        next: "5",       type: "env",     danger: true  },
  { label: "MEMORY_LIMIT", key: "resource",     prev: "512Mi",     next: "256Mi",   type: "resource",danger: true  },
  { label: "CPU_LIMIT",    key: "resource",     prev: "1000m",     next: "500m",    type: "resource",danger: false },
];

function ServiceDetail({
  serviceId,
  onBack,
  onDiagnosticAI,
  onNewAI,
  recovered = false,
}: {
  serviceId: number;
  onBack: () => void;
  onDiagnosticAI: () => void;
  onNewAI: () => void;
  recovered?: boolean;
}) {
  const svc = SERVICES.find(s => s.id === serviceId) || SERVICES[0];
  const [tab, setTab] = useState("Events");
  const isCritical = svc.id === 1 && !recovered;

  const metricCards = [
    {
      label: "에러율",
      before: "1.1%",
      after: "8.2%",
      icon: TrendingDown,
      danger: true,
      sub: "배포 후 7.1%p 증가",
    },
    {
      label: "응답 시간",
      before: "180ms",
      after: "2,400ms",
      icon: Clock,
      danger: true,
      sub: "배포 후 13배 증가",
    },
    {
      label: "가용 Pod",
      before: "3/3",
      after: "1/3",
      icon: Cpu,
      danger: true,
      sub: "2개 Pod 비정상",
    },
    {
      label: "재시작 횟수",
      before: "0",
      after: "6",
      icon: RefreshCw,
      danger: true,
      sub: "최근 10분",
    },
  ];

  return (
    <div className="flex-1 overflow-auto bg-[#f6f8fb]">
      <TopBar breadcrumb={["클러스터: 전체 클러스터", "Services", svc.name]} onAIClick={onNewAI} showAIBtn />
      <div className="p-5 space-y-4">

        {/* ── 서비스 헤더 ── */}
        <div className={`rounded-xl border-2 p-5 shadow-sm ${isCritical ? "bg-red-50 border-red-300" : "bg-white border-slate-200"}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <button onClick={onBack} className="text-slate-400 hover:text-slate-700 cursor-pointer transition-colors p-1 rounded-lg hover:bg-white/60">
                <ChevronRight size={16} className="rotate-180" />
              </button>
              <div>
                <div className="flex items-center gap-2.5 mb-1">
                  <h1 className={`text-[18px] font-bold ${isCritical ? "text-red-800" : "text-slate-800"}`} style={SANS}>{svc.name}</h1>
                  {isCritical
                    ? <span className="flex items-center gap-1 px-2 py-0.5 bg-red-500 text-white text-[10px] font-bold rounded-lg" style={MONO}><AlertTriangle size={10} /> CRITICAL</span>
                    : svc.healthy
                    ? <Badge label="HEALTHY" variant="healthy" />
                    : <Badge label="WARNING" variant="warning" />}
                </div>
                <div className="flex items-center gap-4 text-[10px] text-slate-500" style={MONO}>
                  <span>클러스터: <strong className="text-slate-700">production</strong></span>
                  <span>Namespace: <strong className="text-slate-700">{svc.ns}</strong></span>
                  <span>유형: <strong className="text-slate-700">Deployment</strong></span>
                  <span>마지막 배포: <strong className={isCritical ? "text-red-600" : "text-slate-700"}>{svc.updated}</strong></span>
                </div>
              </div>
            </div>
            {isCritical && (
              <button onClick={onDiagnosticAI}
                className="flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-[12px] font-semibold cursor-pointer transition-colors shadow-sm" style={SANS}>
                <Sparkles size={13} />
                AI로 원인 분석
              </button>
            )}
          </div>
        </div>

        {/* ── 장애 알림 배너 ── */}
        {isCritical && (
          <div className="bg-red-600 rounded-xl p-4 flex items-center gap-3 shadow">
            <AlertTriangle size={18} className="text-white shrink-0" />
            <div className="flex-1">
              <div className="text-[13px] font-bold text-white" style={SANS}>배포 직후 가용성 이슈 감지</div>
              <div className="text-[10px] text-red-100 mt-0.5" style={MONO}>
                CrashLoopBackOff · OOMKilled · DB connection pool exhausted — 오전 11:13 배포 후 7분 뒤 장애 시작
              </div>
            </div>
          </div>
        )}

        {/* ── 주요 지표 카드 4개 ── */}
        {isCritical && (
          <div className="grid grid-cols-4 gap-3">
            {metricCards.map((m) => {
              const Icon = m.icon;
              return (
                <div key={m.label} className="bg-white border-2 border-red-200 rounded-xl p-4 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-red-100 flex items-center justify-center">
                      <Icon size={13} className="text-red-500" />
                    </div>
                    <span className="text-[10px] text-slate-500" style={MONO}>{m.label}</span>
                  </div>
                  <div className="flex items-end gap-2 mb-1">
                    <span className="text-[20px] font-bold text-red-600" style={SANS}>{m.after}</span>
                    <span className="text-[10px] text-slate-400 pb-0.5 line-through" style={MONO}>{m.before}</span>
                  </div>
                  <div className="text-[9px] text-red-500 font-semibold" style={MONO}>{m.sub}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── 탭 ── */}
        <div className="flex items-center gap-0.5 border-b border-slate-200 bg-white rounded-t-xl px-2">
          {["Events", "Logs", "Pods", "최근 변경", "Metrics", "YAML"].map((t) => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-[11px] font-medium transition-colors cursor-pointer border-b-2 -mb-px ${
                tab === t ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-700"
              }`} style={SANS}>
              {t}
              {t === "Events" && isCritical && (
                <span className="ml-1.5 bg-red-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-full">{DETAIL_EVENTS.length}</span>
              )}
            </button>
          ))}
        </div>

        {/* ── Events 탭 ── */}
        {tab === "Events" && (
          <div className="bg-white border border-slate-200 rounded-b-xl rounded-tr-xl shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Events ({DETAIL_EVENTS.length})</span>
              <span className="text-[10px] text-slate-400 flex items-center gap-1" style={MONO}><Clock size={10} />최근 1시간</span>
            </div>
            {/* 타임라인 도트 */}
            <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-1.5 overflow-x-auto">
              {DETAIL_EVENTS.map((e, i) => (
                <div key={i} className={`w-4 h-4 rounded-full shrink-0 cursor-pointer transition-transform hover:scale-125 ${
                  e.icon === "error" ? "bg-red-500" : e.icon === "warn" ? "bg-amber-400" : e.icon === "ok" ? "bg-emerald-500" : "bg-blue-400"
                }`} title={e.type} />
              ))}
            </div>
            <div className="divide-y divide-slate-50">
              {DETAIL_EVENTS.map((ev, i) => (
                <div key={i} className={`flex items-start gap-4 px-5 py-3.5 hover:bg-slate-50 transition-colors ${i === 0 ? "bg-red-50/50" : ""}`}>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                    ev.icon === "error" ? "bg-red-100" : ev.icon === "warn" ? "bg-amber-100" : ev.icon === "ok" ? "bg-emerald-100" : "bg-blue-100"
                  }`}>
                    {ev.icon === "error" && <XCircle size={13} className="text-red-500" />}
                    {ev.icon === "warn"  && <AlertTriangle size={13} className="text-amber-500" />}
                    {ev.icon === "ok"    && <CheckCircle2 size={13} className="text-emerald-500" />}
                    {ev.icon === "info"  && <RefreshCw size={13} className="text-blue-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={`text-[11px] font-semibold ${ev.icon === "error" ? "text-red-700" : "text-slate-700"}`} style={SANS}>{ev.type}</span>
                      <span className="text-[9px] text-slate-400" style={MONO}>{ev.time}</span>
                    </div>
                    <div className="text-[10px] text-slate-500" style={MONO}>{ev.msg}</div>
                  </div>
                  <ChevronRight size={13} className="text-slate-300 shrink-0 mt-1" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Logs 탭 ── */}
        {tab === "Logs" && (
          <div className="bg-[#0d1117] rounded-xl border border-slate-700 shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal size={13} className="text-slate-400" />
                <span className="text-[12px] font-semibold text-slate-200" style={SANS}>실시간 로그 — checkout-v2-2</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse inline-block" />
                <span className="text-[10px] text-red-400" style={MONO}>에러 패턴 감지됨</span>
              </div>
            </div>
            <div className="p-4 font-mono text-[10px] space-y-1 max-h-72 overflow-y-auto">
              {LOG_LINES.map((l, i) => (
                <div key={i} className={`flex items-start gap-3 ${l.level === "ERROR" ? "text-red-400" : l.level === "WARN" ? "text-amber-400" : "text-slate-400"}`}>
                  <span className="text-slate-600 shrink-0 tabular-nums">{l.t}</span>
                  <span className={`shrink-0 font-bold w-10 ${l.level === "ERROR" ? "text-red-400" : l.level === "WARN" ? "text-amber-400" : "text-blue-400"}`}>{l.level}</span>
                  <span className="leading-relaxed">{l.msg}</span>
                </div>
              ))}
            </div>
            {/* 로그 패턴 요약 */}
            <div className="border-t border-slate-700 px-5 py-3">
              <div className="text-[9px] text-slate-500 uppercase tracking-wider mb-2" style={MONO}>반복 패턴</div>
              <div className="flex items-center gap-3 flex-wrap">
                {[
                  { label: "DB timeout", count: 8, color: "bg-red-900/50 text-red-300 border-red-700" },
                  { label: "connection pool exhausted", count: 6, color: "bg-red-900/50 text-red-300 border-red-700" },
                  { label: "readiness probe failed", count: 4, color: "bg-amber-900/50 text-amber-300 border-amber-700" },
                  { label: "OOMKilled", count: 3, color: "bg-orange-900/50 text-orange-300 border-orange-700" },
                ].map(p => (
                  <span key={p.label} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[9px] font-semibold ${p.color}`} style={MONO}>
                    {p.label}
                    <span className="bg-white/10 px-1 rounded text-[8px]">×{p.count}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Pods 탭 ── */}
        {tab === "Pods" && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100">
              <span className="text-[12px] font-semibold text-slate-700" style={SANS}>Pod 상태 (3개)</span>
            </div>
            <div className="divide-y divide-slate-50">
              {PODS_DATA.map((pod, i) => {
                const statusColor = pod.status === "Running" ? "text-emerald-600 bg-emerald-100" : "text-red-600 bg-red-100";
                const statusIcon  = pod.status === "Running" ? CheckCircle2 : XCircle;
                const Icon = statusIcon;
                return (
                  <div key={i} className={`flex items-center gap-4 px-5 py-4 ${pod.status !== "Running" ? "bg-red-50/40" : ""}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center ${statusColor}`}>
                      <Icon size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[12px] font-semibold text-slate-700" style={MONO}>{pod.name}</span>
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${statusColor}`} style={MONO}>{pod.status}</span>
                        {pod.restarts > 0 && (
                          <span className="flex items-center gap-1 text-[9px] text-red-600 font-semibold" style={MONO}>
                            <RefreshCw size={9} />재시작 {pod.restarts}회
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-[9px] text-slate-500" style={MONO}>
                        <span>Memory: <strong className={pod.status !== "Running" ? "text-red-600" : "text-slate-700"}>{pod.memory}</strong></span>
                        <span>CPU: <strong className="text-slate-700">{pod.cpu}</strong></span>
                        <span>Node: <strong className="text-slate-700">{pod.node}</strong></span>
                      </div>
                    </div>
                    {pod.status === "CrashLoop" && (
                      <div className="text-[9px] text-red-600 bg-red-100 px-2 py-1 rounded-lg font-semibold" style={MONO}>계속 재시작 중</div>
                    )}
                    {pod.status === "OOMKilled" && (
                      <div className="text-[9px] text-orange-600 bg-orange-100 px-2 py-1 rounded-lg font-semibold" style={MONO}>메모리 부족 종료</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── 최근 변경 탭 ── */}
        {tab === "최근 변경" && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-2">
              <GitBranch size={13} className="text-slate-400" />
              <span className="text-[12px] font-semibold text-slate-700" style={SANS}>PR #1234 — image v1.4.1 → v1.4.2</span>
              <span className="ml-auto text-[9px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-semibold" style={MONO}>위험 변경 2개 감지</span>
            </div>
            <div className="divide-y divide-slate-50">
              {CHANGES_DATA.map((c, i) => (
                <div key={i} className={`flex items-center gap-4 px-5 py-3.5 ${c.danger ? "bg-red-50/60" : ""}`}>
                  <div className={`w-5 h-5 rounded flex items-center justify-center shrink-0 ${c.danger ? "bg-red-100" : "bg-slate-100"}`}>
                    {c.type === "deploy"   && <RefreshCw size={10} className={c.danger ? "text-red-500" : "text-slate-400"} />}
                    {c.type === "version"  && <Package   size={10} className={c.danger ? "text-red-500" : "text-slate-400"} />}
                    {c.type === "env"      && <Terminal  size={10} className="text-red-500" />}
                    {c.type === "resource" && <Cpu       size={10} className={c.danger ? "text-red-500" : "text-slate-400"} />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={`text-[11px] font-semibold ${c.danger ? "text-red-700" : "text-slate-700"}`} style={SANS}>{c.label}</span>
                      {c.danger && (
                        <span className="text-[8px] bg-red-100 text-red-600 border border-red-200 px-1.5 py-0.5 rounded font-bold" style={MONO}>위험</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[10px]" style={MONO}>
                      <span className="text-slate-400 line-through">{c.prev}</span>
                      <ArrowRight size={10} className="text-slate-400" />
                      <span className={`font-bold ${c.danger ? "text-red-600" : "text-slate-700"}`}>{c.next}</span>
                    </div>
                  </div>
                  {c.danger && (
                    <AlertTriangle size={14} className="text-red-400 shrink-0" />
                  )}
                </div>
              ))}
            </div>
            <div className="px-5 py-3 bg-red-50 border-t border-red-200">
              <div className="flex items-center gap-2 text-[10px] text-red-600" style={MONO}>
                <AlertTriangle size={11} />
                <strong>AI 분석:</strong> DB_POOL_SIZE 20→5 축소와 메모리 제한 512Mi→256Mi 감소가 현재 장애의 직접적인 원인으로 추정됩니다.
              </div>
            </div>
          </div>
        )}

        {/* ── Metrics 탭 ── */}
        {tab === "Metrics" && (
          <div className="space-y-4">
            {/* 4개 메트릭 미니 차트 */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { title: "에러율 (%)",    data: ERR_DATA,  color: "#ef4444", grad: "errMetric", unit: "%" },
                { title: "응답 시간 (ms)",data: LAT_DATA,  color: "#f97316", grad: "latMetric", unit: "ms" },
              ].map(m => (
                <div key={m.title} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[12px] font-semibold text-slate-700" style={SANS}>{m.title}</span>
                    <div className="flex gap-1">
                      {["1h","3h","24h"].map(t => (
                        <button key={t} className={`px-2 py-0.5 rounded text-[8px] cursor-pointer border ${t === "1h" ? "bg-indigo-600 text-white border-indigo-600" : "border-slate-200 text-slate-500"}`} style={MONO}>{t}</button>
                      ))}
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={140}>
                    <AreaChart data={m.data}>
                      <defs>
                        <linearGradient id={m.grad} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={m.color} stopOpacity={0.3} />
                          <stop offset="100%" stopColor={m.color} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="t" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={30} />
                      <Tooltip contentStyle={{ fontSize: 9, borderRadius: 6 }} formatter={(v: number) => [`${v.toFixed(1)}${m.unit}`, m.title]} />
                      <Area type="monotone" dataKey="v" stroke={m.color} strokeWidth={2} fill={`url(#${m.grad})`} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                  {/* 배포 시점 마커 라벨 */}
                  <div className="flex items-center gap-1.5 mt-2 text-[9px] text-red-500 font-semibold" style={MONO}>
                    <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />배포 시점 (t=12m) 이후 급등
                  </div>
                </div>
              ))}
            </div>

            {/* CPU / Memory 리소스 */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { title: "CPU 사용률",   vals: [34, 41, 38, 290, 480, 420, 0, 0], limit: 500, unit: "m" },
                { title: "Memory 사용량",vals: [180, 195, 210, 240, 255, 256, 256, 256], limit: 256, unit: "Mi" },
              ].map(r => {
                const chartData = r.vals.map((v, i) => ({ t: `${i * 3}m`, v, limit: r.limit }));
                return (
                  <div key={r.title} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[12px] font-semibold text-slate-700" style={SANS}>{r.title}</span>
                      <span className="text-[9px] text-red-500 font-bold" style={MONO}>한도: {r.limit}{r.unit}</span>
                    </div>
                    <ResponsiveContainer width="100%" height={100}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="t" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                        <YAxis tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={28} />
                        <Tooltip contentStyle={{ fontSize: 9, borderRadius: 6 }} />
                        <Line type="monotone" dataKey="v" stroke="#6366f1" strokeWidth={2} dot={false} name="사용량" />
                        <Line type="monotone" dataKey="limit" stroke="#ef4444" strokeWidth={1.5} dot={false} strokeDasharray="5 3" name="한도" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── YAML 탭 ── */}
        {tab === "YAML" && (
          <div className="bg-[#0d1117] rounded-xl border border-slate-700 shadow-sm overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText size={13} className="text-slate-400" />
                <span className="text-[12px] font-semibold text-slate-200" style={SANS}>checkout-api-v2 Deployment YAML</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] bg-red-900/60 text-red-300 border border-red-700/50 px-2 py-0.5 rounded font-semibold" style={MONO}>위험 설정 2개</span>
                <button className="text-[9px] text-slate-400 border border-slate-600 px-2 py-0.5 rounded hover:bg-slate-700 cursor-pointer" style={MONO}>복사</button>
              </div>
            </div>
            <div className="p-5 font-mono text-[10px] leading-relaxed overflow-y-auto max-h-[500px] text-slate-300">
              <pre className="whitespace-pre-wrap">{`apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api-v2
  namespace: checkout
  labels:
    app: checkout-api
    version: v1.4.2
spec:
  replicas: 3
  selector:
    matchLabels:
      app: checkout-api
  template:
    metadata:
      labels:
        app: checkout-api
        version: v1.4.2
    spec:
      containers:
      - name: checkout-api
        image: myregistry/checkout-api:v1.4.2
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          value: "postgres.checkout.svc.cluster.local"
        - name: DB_PORT
          value: "5432"`}</pre>
              {/* 위험 환경변수 강조 */}
              <div className="bg-red-900/30 border border-red-600/40 rounded-lg px-3 py-2 my-1">
                <pre className="text-red-300 whitespace-pre-wrap">{`        - name: DB_POOL_SIZE   # ⚠ 위험: 20 → 5 로 감소됨
          value: "5"           # 이전 값: "20"`}</pre>
              </div>
              <pre className="whitespace-pre-wrap">{`        - name: DB_NAME
          value: "checkout_db"
        resources:
          requests:
            cpu: "200m"
            memory: "128Mi"`}</pre>
              <div className="bg-red-900/30 border border-red-600/40 rounded-lg px-3 py-2 my-1">
                <pre className="text-red-300 whitespace-pre-wrap">{`          limits:
            cpu: "500m"
            memory: "256Mi"    # ⚠ 위험: 512Mi → 256Mi 로 감소됨`}</pre>
              </div>
              <pre className="whitespace-pre-wrap">{`        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: checkout-api-v2
  namespace: checkout
spec:
  selector:
    app: checkout-api
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP`}</pre>
            </div>
            <div className="border-t border-slate-700 px-5 py-3 flex items-center gap-3">
              <AlertTriangle size={12} className="text-red-400 shrink-0" />
              <span className="text-[9px] text-red-300" style={MONO}>
                DB_POOL_SIZE(5)와 memory limit(256Mi) 설정이 장애 원인으로 추정됩니다. 이전 값으로 롤백을 권장합니다.
              </span>
              <button className="ml-auto shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-[10px] font-semibold cursor-pointer transition-colors" style={SANS}>
                <RefreshCw size={11} />롤백 실행
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 5: Self-Healing
// ═══════════════════════════════════════════════════════════════════════════════
function SelfHealing({ onNewAI }: { onNewAI: () => void }) {
  const [healed, setHealed] = useState(true);

  return (
    <div className="flex-1 overflow-auto bg-slate-50">
      <TopBar breadcrumb={["Services", "development-self-healing", "Configuration"]} onAIClick={onNewAI} showAIBtn />
      <div className="p-5 space-y-4">
        {/* 서비스 헤더 */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <h1 className="text-[18px] font-bold text-slate-800" style={SANS}>development-self-healing</h1>
              <Badge label="HEALTHY" variant="healthy" />
            </div>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-[11px] font-medium cursor-pointer" style={SANS}>
              <RefreshCw size={12} />재시작
            </button>
          </div>
          <div className="grid grid-cols-6 gap-4 text-[11px]" style={MONO}>
            {[
              { label: "유형",       value: "Deployment" },
              { label: "클러스터",   value: "development-self-healing" },
              { label: "Namespace",  value: "bank-of-metropolis" },
              { label: "이미지",     value: "redis 7.2 alpine" },
              { label: "관리",       value: "cash-cache" },
              { label: "마지막 교체", value: "약 20시간 전" },
            ].map(({ label, value }) => (
              <div key={label}>
                <div className="text-[9px] text-slate-400 uppercase tracking-wider mb-1">{label}</div>
                <div className="text-slate-700 font-medium truncate">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Status 바 */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-6">
          {[
            { label: "HEALTH",     value: "HEALTHY", color: "text-emerald-600" },
            { label: "REPLICAS",   value: "1/1",     color: "text-slate-700" },
            { label: "마지막 교체", value: "COMPLETED", color: "text-blue-600" },
            { label: "변경됨",     value: "이미지",  color: "text-slate-600" },
            { label: "시작됨",     value: "약 20시간 전", color: "text-slate-600" },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div className="text-[8px] uppercase tracking-wider text-slate-400 mb-0.5" style={MONO}>{label}</div>
              <div className={`text-[11px] font-semibold ${color}`} style={MONO}>{value}</div>
            </div>
          ))}
          {/* Self-Healing 토글 */}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[10px] text-slate-500 font-medium" style={SANS}>자가 치유 활성화</span>
            <button onClick={() => setHealed(!healed)}
              className={`w-10 h-5 rounded-full transition-colors cursor-pointer relative ${healed ? "bg-emerald-500" : "bg-slate-300"}`}>
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-all ${healed ? "left-5" : "left-0.5"}`} />
            </button>
          </div>
        </div>

        {/* 탭 */}
        <div className="flex items-center gap-0.5 border-b border-slate-200">
          {["Events", "Logs", "Cost & Optimization", "Nodes", "Details", "Metrics", "YAML"].map(t => (
            <button key={t} className={`px-4 py-2.5 text-[11px] font-medium cursor-pointer border-b-2 -mb-px transition-colors ${
              t === "Events" ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500 hover:text-slate-700"}`} style={SANS}>{t}</button>
          ))}
          <button className="ml-auto px-3 py-2 text-[10px] text-indigo-600 font-medium cursor-pointer hover:text-indigo-800" style={SANS}>
            + 타임라인에 리소스 추가
          </button>
        </div>

        {/* 이벤트 테이블 */}
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="grid grid-cols-12 px-5 py-2.5 border-b border-slate-100 text-[9px] uppercase tracking-wider text-slate-400" style={MONO}>
            <span className="col-span-1"></span>
            <span className="col-span-2">이벤트 유형</span>
            <span className="col-span-3">요약</span>
            <span className="col-span-2">시작 시각 (UTC+2)</span>
            <span className="col-span-2">마지막 업데이트</span>
            <span className="col-span-1">세부</span>
            <span className="col-span-1">상태</span>
          </div>
          {HEAL_EVENTS.map((ev, i) => (
            <div key={i} className="grid grid-cols-12 px-5 py-3.5 border-b border-slate-50 items-center hover:bg-slate-50 transition-colors">
              <div className="col-span-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  ev.icon === "error" ? "bg-red-100" : ev.icon === "warn" ? "bg-amber-100" : "bg-emerald-100"}`}>
                  {ev.icon === "error" && <XCircle size={11} className="text-red-500" />}
                  {ev.icon === "warn"  && <AlertTriangle size={11} className="text-amber-500" />}
                  {ev.icon === "ok"    && <CheckCircle2 size={11} className="text-emerald-500" />}
                </div>
              </div>
              <div className="col-span-2 text-[10px] font-medium text-slate-700" style={SANS}>{ev.type}</div>
              <div className="col-span-3 text-[10px] text-slate-500 truncate" style={MONO}>{ev.summary}</div>
              <div className="col-span-2 text-[9px] text-slate-500" style={MONO}>{ev.started}</div>
              <div className="col-span-2 text-[9px] text-slate-500" style={MONO}>{ev.started}</div>
              <div className="col-span-1"><ChevronRight size={12} className="text-slate-300 cursor-pointer hover:text-slate-600" /></div>
              <div className="col-span-1">
                <Badge label={ev.status} variant={ev.icon === "ok" ? "healthy" : ev.icon === "error" ? "unhealthy" : "warning"} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// AI CHAT PANEL (slide-in)
// ═══════════════════════════════════════════════════════════════════════════════
// ─────────────────────────────────────────────────────────────────────────────
// AI Chat — 화면 5·6·7 통합 대화 패널
// ─────────────────────────────────────────────────────────────────────────────

type ChatStage = "init" | "q1" | "q2" | "q3" | "pr-proposed" | "recovered";

interface ChatMsg {
  role: "user" | "ai";
  text: string;
  stage?: ChatStage;
}

const INIT_MSGS: ChatMsg[] = [
  {
    role: "ai",
    text: "checkout-api-v2 서비스에서 장애가 감지되었습니다. Pod 상태, 로그, 최근 배포, 지표를 바탕으로 분석을 시작합니다.",
    stage: "init",
  },
];

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN: 변경 위험 분석 — 화면 4 (web-frontend 경고 카드 클릭 시)
// ═══════════════════════════════════════════════════════════════════════════════

const PR_CHANGES = [
  { key: "image",        label: "이미지",         prev: "v2.1.3",   next: "v2.2.0",  type: "version", risk: null    },
  { key: "db_pool",      label: "DB_POOL_SIZE",   prev: "20",       next: "5",       type: "env",     risk: "high"  },
  { key: "memory",       label: "memory limit",   prev: "512Mi",    next: "256Mi",   type: "resource",risk: "high"  },
  { key: "replicas",     label: "replicas",       prev: "3",        next: "4",       type: "replica", risk: "low"   },
];

const RISK_ANALYSIS = [
  {
    change: "DB_POOL_SIZE 20 → 5",
    level: "high" as const,
    title: "DB timeout 위험",
    desc: "동시 DB 연결 수가 75% 감소합니다. 트래픽 집중 시 connection pool이 소진되어 DB timeout이 발생할 수 있습니다.",
    evidence: ["과거 pool size < 8 에서 timeout 발생 이력 3건", "현재 평균 동시 요청: 12 req/s"],
    badge: "즉시 위험",
  },
  {
    change: "memory limit 512Mi → 256Mi",
    level: "high" as const,
    title: "OOMKilled 위험",
    desc: "메모리 제한이 50% 감소합니다. 현재 평균 메모리 사용량이 320Mi로, 제한 256Mi를 초과 시 Pod가 강제 종료됩니다.",
    evidence: ["현재 평균 메모리 사용: 320Mi", "피크 메모리: 410Mi (지난 7일)"],
    badge: "즉시 위험",
  },
  {
    change: "replicas 3 → 4",
    level: "low" as const,
    title: "노드 배치 여유 확인 필요",
    desc: "Pod가 1개 늘어납니다. 현재 노드 리소스 여유가 충분한지 확인이 필요합니다.",
    evidence: ["현재 노드 CPU 사용률: 68%", "현재 노드 Memory 사용률: 71%"],
    badge: "확인 필요",
  },
  {
    change: "image v2.1.3 → v2.2.0",
    level: "neutral" as const,
    title: "이미지 업데이트",
    desc: "마이너 버전 업데이트입니다. 변경 로그를 확인하세요.",
    evidence: ["CHANGELOG: dependency 업데이트", "보안 패치 포함"],
    badge: "정보",
  },
];

const AFFECTED_RESOURCES = [
  { type: "Deployment", name: "web-frontend",     ns: "production", impact: "high"    },
  { type: "Pod",        name: "web-frontend-*",   ns: "production", impact: "high"    },
  { type: "Service",    name: "frontend-service",  ns: "production", impact: "medium"  },
  { type: "HPA",        name: "web-frontend-hpa",  ns: "production", impact: "medium"  },
  { type: "ConfigMap",  name: "frontend-config",   ns: "production", impact: "low"     },
];

function ChangeRiskView({ onBack, onAIClick }: { onBack: () => void; onAIClick: () => void }) {
  const [selectedChange, setSelectedChange] = useState<string | null>("db_pool");

  const riskCount = { high: RISK_ANALYSIS.filter(r => r.level === "high").length, low: RISK_ANALYSIS.filter(r => r.level === "low").length };

  return (
    <div className="flex-1 overflow-auto bg-[#f6f8fb]">
      {/* 상단 바 */}
      <div className="h-11 shrink-0 border-b border-slate-200 bg-white flex items-center justify-between px-5">
        <div className="flex items-center gap-2 text-[11px]" style={SANS}>
          <button onClick={onBack} className="text-slate-400 hover:text-slate-700 cursor-pointer transition-colors p-0.5">
            <ChevronRight size={14} className="rotate-180" />
          </button>
          <span className="text-slate-400">Services</span>
          <ChevronRight size={10} className="text-slate-300" />
          <span className="text-slate-400">web-frontend</span>
          <ChevronRight size={10} className="text-slate-300" />
          <span className="text-slate-700 font-semibold">변경 위험 분석</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-[9px] bg-red-50 border border-red-200 text-red-600 px-2 py-0.5 rounded font-semibold" style={MONO}>
            <AlertTriangle size={9} />위험 변경 {riskCount.high}개
          </span>
          <button onClick={onAIClick}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-[11px] font-semibold transition-colors cursor-pointer shadow-sm" style={SANS}>
            <Sparkles size={12} />Klaudia AI
          </button>
        </div>
      </div>

      <div className="p-5">
        {/* 헤더 */}
        <div className="mb-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="flex items-center gap-2">
              <GitBranch size={16} className="text-amber-500" />
              <h2 className="text-[16px] font-bold text-slate-800" style={SANS}>PR #1072 — web-frontend v2.2.0</h2>
            </div>
            <span className="px-2 py-0.5 bg-amber-100 text-amber-700 border border-amber-300 text-[9px] font-bold rounded" style={MONO}>MERGE 위험</span>
          </div>
          <p className="text-[11px] text-slate-500" style={MONO}>
            이 화면이 저희 서비스의 핵심입니다. 바뀐 줄이 아니라, <strong className="text-slate-700">실제 서비스 영향</strong>까지 분석합니다.
          </p>
        </div>

        {/* 3컬럼 레이아웃 */}
        <div className="grid grid-cols-12 gap-4">

          {/* ── 왼쪽: Git PR 변경 목록 ── */}
          <div className="col-span-3">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
                <GitBranch size={13} className="text-slate-400" />
                <span className="text-[12px] font-semibold text-slate-700" style={SANS}>PR 변경 목록</span>
                <span className="ml-auto text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded" style={MONO}>{PR_CHANGES.length}개</span>
              </div>
              <div className="divide-y divide-slate-50">
                {PR_CHANGES.map((c) => {
                  const isSelected = selectedChange === c.key;
                  const riskCls = c.risk === "high"
                    ? "border-l-4 border-l-red-500 bg-red-50/60"
                    : c.risk === "low"
                    ? "border-l-4 border-l-amber-400 bg-amber-50/30"
                    : "border-l-4 border-l-slate-200";

                  return (
                    <button key={c.key} onClick={() => setSelectedChange(c.key)}
                      className={`w-full text-left px-4 py-3.5 transition-all cursor-pointer ${riskCls} ${isSelected ? "ring-1 ring-inset ring-indigo-300 bg-indigo-50/60" : "hover:bg-slate-50"}`}>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-bold text-slate-700" style={SANS}>{c.label}</span>
                        {c.risk === "high" && <AlertTriangle size={11} className="text-red-500 shrink-0" />}
                        {c.risk === "low"  && <AlertTriangle size={11} className="text-amber-400 shrink-0" />}
                      </div>
                      <div className="flex items-center gap-1.5 text-[9px]" style={MONO}>
                        <span className="text-slate-400 line-through">{c.prev}</span>
                        <ArrowRight size={9} className="text-slate-400 shrink-0" />
                        <span className={`font-bold ${c.risk === "high" ? "text-red-600" : c.risk === "low" ? "text-amber-600" : "text-indigo-600"}`}>{c.next}</span>
                      </div>
                      <div className="mt-1.5">
                        <span className={`text-[8px] px-1.5 py-0.5 rounded font-semibold ${
                          c.type === "env"      ? "bg-purple-100 text-purple-600" :
                          c.type === "resource" ? "bg-red-100 text-red-600" :
                          c.type === "replica"  ? "bg-amber-100 text-amber-600" :
                          "bg-blue-100 text-blue-600"}`} style={MONO}>
                          {c.type === "env" ? "환경변수" : c.type === "resource" ? "리소스" : c.type === "replica" ? "스케일" : "이미지"}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* diff 미리보기 */}
            <div className="mt-3 bg-[#0d1117] border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-3 py-2 border-b border-slate-700 flex items-center gap-1.5">
                <FileText size={11} className="text-slate-400" />
                <span className="text-[9px] text-slate-400" style={MONO}>deployment.yaml diff</span>
              </div>
              <div className="p-3 font-mono text-[9px] leading-relaxed">
                <div className="text-slate-500">  containers:</div>
                <div className="text-slate-500">  - name: web-frontend</div>
                <div className="bg-red-500/15 text-red-400 px-1">-   memory: "512Mi"</div>
                <div className="bg-emerald-500/15 text-emerald-400 px-1">+   memory: "256Mi"</div>
                <div className="bg-red-500/15 text-red-400 px-1">-   DB_POOL_SIZE: "20"</div>
                <div className="bg-emerald-500/15 text-emerald-400 px-1">+   DB_POOL_SIZE: "5"</div>
                <div className="bg-red-500/15 text-red-400 px-1">-   replicas: 3</div>
                <div className="bg-emerald-500/15 text-emerald-400 px-1">+   replicas: 4</div>
              </div>
            </div>
          </div>

          {/* ── 중앙: 변경 위험 분석 ── */}
          <div className="col-span-6 space-y-3">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
                <Shield size={13} className="text-red-500" />
                <span className="text-[12px] font-semibold text-slate-700" style={SANS}>변경 위험 분석</span>
                <div className="ml-auto flex items-center gap-1.5 text-[9px]" style={MONO}>
                  <span className="bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-bold">즉시 위험 {riskCount.high}</span>
                  <span className="bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded font-bold">확인 필요 {riskCount.low}</span>
                </div>
              </div>
              <div className="divide-y divide-slate-50">
                {RISK_ANALYSIS.map((r, i) => (
                  <div key={i} className={`p-4 ${r.level === "high" ? "bg-red-50/40" : r.level === "low" ? "bg-amber-50/30" : ""}`}>
                    <div className="flex items-start gap-3">
                      {/* 아이콘 */}
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                        r.level === "high" ? "bg-red-100" : r.level === "low" ? "bg-amber-100" : "bg-slate-100"}`}>
                        {r.level === "high"    ? <AlertTriangle size={15} className="text-red-500" /> :
                         r.level === "low"     ? <AlertTriangle size={15} className="text-amber-500" /> :
                         <CheckCircle2 size={15} className="text-slate-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        {/* 헤더 */}
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-[12px] font-bold ${r.level === "high" ? "text-red-700" : r.level === "low" ? "text-amber-700" : "text-slate-600"}`} style={SANS}>
                            {r.title}
                          </span>
                          <span className={`text-[8px] px-2 py-0.5 rounded font-bold ${
                            r.level === "high" ? "bg-red-500 text-white" :
                            r.level === "low"  ? "bg-amber-400 text-white" :
                            "bg-slate-200 text-slate-600"}`} style={MONO}>{r.badge}</span>
                        </div>
                        {/* 변경 원본 */}
                        <div className="text-[9px] text-slate-400 mb-2 font-semibold" style={MONO}>{r.change}</div>
                        {/* 설명 */}
                        <p className="text-[10px] text-slate-600 leading-relaxed mb-2" style={SANS}>{r.desc}</p>
                        {/* 근거 */}
                        <div className="space-y-1">
                          {r.evidence.map((e, j) => (
                            <div key={j} className="flex items-center gap-1.5 text-[9px] text-slate-500" style={MONO}>
                              <span className="w-1.5 h-1.5 rounded-full bg-slate-300 shrink-0" />
                              {e}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI 권고 요약 */}
            <div className="bg-[#0f1628] border border-indigo-500/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={13} className="text-indigo-400" />
                <span className="text-[11px] font-bold text-white" style={SANS}>AI 권고</span>
              </div>
              <p className="text-[10px] text-slate-300 leading-relaxed mb-3" style={MONO}>
                DB_POOL_SIZE와 memory limit 변경은 현재 트래픽 수준에서 <span className="text-red-300 font-bold">즉시 장애로 이어질 가능성</span>이 있습니다. 이 PR을 그대로 Merge하면 안 됩니다.
              </p>
              <div className="flex gap-2">
                <button onClick={onAIClick}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-[10px] font-semibold cursor-pointer transition-colors" style={SANS}>
                  <MessageSquare size={11} />AI와 수정 방법 논의
                </button>
                <button className="px-3 py-2 border border-white/20 text-slate-300 hover:bg-white/10 rounded-xl text-[10px] cursor-pointer transition-colors" style={SANS}>
                  PR 차단
                </button>
              </div>
            </div>
          </div>

          {/* ── 오른쪽: 영향 받는 리소스 ── */}
          <div className="col-span-3 space-y-3">
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
                <Layers size={13} className="text-slate-400" />
                <span className="text-[12px] font-semibold text-slate-700" style={SANS}>영향 리소스</span>
              </div>
              <div className="divide-y divide-slate-50">
                {AFFECTED_RESOURCES.map((r, i) => (
                  <div key={i} className={`flex items-center gap-3 px-4 py-3 ${r.impact === "high" ? "bg-red-50/30" : ""}`}>
                    <div className={`w-1.5 h-8 rounded-full shrink-0 ${
                      r.impact === "high" ? "bg-red-500" : r.impact === "medium" ? "bg-amber-400" : "bg-slate-200"}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-[10px] font-bold text-slate-700 truncate" style={SANS}>{r.name}</div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="text-[8px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded" style={MONO}>{r.type}</span>
                        <span className="text-[8px] text-slate-400" style={MONO}>{r.ns}</span>
                      </div>
                    </div>
                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                      r.impact === "high" ? "bg-red-100 text-red-600" :
                      r.impact === "medium" ? "bg-amber-100 text-amber-600" :
                      "bg-slate-100 text-slate-500"}`} style={MONO}>
                      {r.impact === "high" ? "HIGH" : r.impact === "medium" ? "MED" : "LOW"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 배포 전 체크리스트 */}
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <span className="text-[11px] font-semibold text-slate-700" style={SANS}>배포 전 체크리스트</span>
              </div>
              <div className="p-3 space-y-2">
                {[
                  { label: "DB_POOL_SIZE 원복 확인",    done: false },
                  { label: "memory limit 검토",         done: false },
                  { label: "스테이징 환경 검증",         done: true  },
                  { label: "On-call 엔지니어 알림",      done: true  },
                  { label: "롤백 계획 수립",             done: false },
                ].map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-[9px]" style={MONO}>
                    {c.done
                      ? <CheckCircle2 size={11} className="text-emerald-500 shrink-0" />
                      : <div className="w-2.5 h-2.5 rounded border-2 border-slate-300 shrink-0" />}
                    <span className={c.done ? "text-slate-400 line-through" : "text-slate-600"}>{c.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AIChat({
  mode,
  serviceName,
  onClose,
  onRecovered,
}: {
  mode: AIMode;
  serviceName?: string;
  onClose: () => void;
  onRecovered?: () => void;
}) {
  const [msgs, setMsgs] = useState<ChatMsg[]>(INIT_MSGS);
  const [stage, setStage] = useState<ChatStage>("init");
  const [input, setInput] = useState("");
  const [prGenerated, setPrGenerated] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const chatEndRef = { current: null as HTMLDivElement | null };
  const isDiagnostic = mode === "diagnostic";

  function addMsg(role: "user" | "ai", text: string, newStage?: ChatStage) {
    setMsgs(prev => [...prev, { role, text, stage: newStage }]);
    if (newStage) setStage(newStage);
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }

  function handleQuestion(q: string, nextStage: ChatStage) {
    addMsg("user", q);
    setTimeout(() => {
      const answers: Record<string, string> = {
        q1: "결제 API 배포 이후 DB timeout 로그가 급증했습니다. 동시에 사용 가능한 Pod가 3개 중 1개로 줄었습니다.\n\n최근 변경에서 DB_POOL_SIZE가 20→5로, 메모리 제한이 512Mi→256Mi로 줄어든 것이 가장 높은 원인 후보입니다. 메모리 부족으로 Pod가 강제 종료되면서 가용 Pod 수가 감소한 것으로 보입니다.",
        q2: "즉시 롤백도 가능하지만, 설정 값 복원 PR이 더 안전한 방법입니다. AI가 수정 후보를 검증하고 Safe PR을 제안합니다. 아래에서 조치를 선택하세요.",
        q3: "가장 먼저 확인할 설정:\n\n① DB_POOL_SIZE: 현재 5 → 원래 값 20으로 복원\n② memory limit: 현재 256Mi → 원래 값 512Mi로 복원\n\n이 두 값을 먼저 복원하면 Pod 재시작 없이도 연결 문제가 해소될 가능성이 높습니다.",
      };
      addMsg("ai", answers[nextStage.startsWith("q") ? nextStage : "q1"] || "", nextStage);
    }, 600);
  }

  function handleSend() {
    if (!input.trim()) return;
    const q = input.trim();
    setInput("");
    addMsg("user", q);
    setTimeout(() => {
      addMsg("ai", "현재 분석 결과를 기반으로 답변드립니다. DB 연결 수 부족과 메모리 제한이 주요 원인으로 판단됩니다. 아래 제안된 Safe PR을 통해 안전하게 복구할 수 있습니다.", stage);
    }, 700);
  }

  function handleCreatePR() {
    setPrGenerated(true);
    addMsg("user", "Safe PR 생성");
    setTimeout(() => addMsg("ai", "PR #1235가 생성되었습니다. GitOps 파이프라인을 통해 변경이 반영됩니다.", "pr-proposed"), 400);
    setTimeout(() => {
      setMsgs(prev => [...prev, { role: "ai", text: "__recovery__", stage: "recovered" }]);
      setStage("recovered");
      onRecovered?.();
    }, 1800);
  }

  const isDone = stage === "recovered";

  return (
    <div className="fixed inset-y-0 right-0 w-[540px] bg-[#0f1628] flex flex-col shadow-2xl z-50 border-l border-white/10"
      style={{ animation: "slideIn 0.25s ease" }}>
      <style>{`@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

      {/* ── 헤더 ── */}
      <div className="px-5 py-3.5 border-b border-white/10 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-indigo-500 flex items-center justify-center shadow">
            <Sparkles size={15} className="text-white" />
          </div>
          <div>
            <div className="text-[13px] font-bold text-white" style={SANS}>Klaudia AI Copilot</div>
            <div className="text-[9px] text-indigo-300" style={MONO}>분석 기준: 최근 배포 · Pod 상태 · 로그 · 지표</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isDone && (
            <span className="flex items-center gap-1 text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-lg font-semibold" style={MONO}>
              <CheckCircle2 size={10} />복구 완료
            </span>
          )}
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 cursor-pointer transition-colors"><X size={16} /></button>
        </div>
      </div>

      {/* ── 컨텍스트 배너 ── */}
      {isDiagnostic && (
        <div className="px-4 py-2.5 bg-red-950/60 border-b border-red-500/20 flex items-center gap-2.5">
          <AlertTriangle size={13} className="text-red-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <span className="text-[10px] font-semibold text-red-300" style={SANS}>checkout-api-v2 장애 분석 중</span>
            <span className="text-[9px] text-red-400 ml-2" style={MONO}>CrashLoopBackOff · OOMKilled · DB timeout</span>
          </div>
        </div>
      )}

      {/* ── 채팅 영역 ── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">

        {msgs.map((msg, idx) => {
          const isUser = msg.role === "user";

          /* ── 복구 결과 카드 ── */
          if (msg.text === "__recovery__") return (
            <div key={idx} className="space-y-3" style={{ animation: "slideDown 0.3s ease" }}>
              {/* 복구 성공 배너 */}
              <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 size={16} className="text-emerald-400" />
                  <span className="text-[13px] font-bold text-emerald-300" style={SANS}>복구 완료 — 서비스 정상화</span>
                </div>
                {/* 타임라인 */}
                <div className="space-y-2">
                  {[
                    { label: "PR #1235 생성",   sub: "DB_POOL_SIZE·memory limit 복원",  done: true,  time: "11:28" },
                    { label: "리뷰 승인 완료",   sub: "kim.admin 승인",                  done: true,  time: "11:29" },
                    { label: "GitOps 동기화",    sub: "ArgoCD sync — production",        done: true,  time: "11:30" },
                    { label: "Pod 3/3 정상화",   sub: "checkout-v2 모두 Running",        done: true,  time: "11:31" },
                  ].map((s, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <span className="text-[10px] font-semibold text-emerald-200" style={SANS}>{s.label}</span>
                        <span className="text-[9px] text-emerald-400/70 ml-2" style={MONO}>{s.sub}</span>
                      </div>
                      <span className="text-[8px] text-emerald-500 shrink-0" style={MONO}>{s.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 지표 변화 */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <div className="text-[10px] font-semibold text-slate-300 mb-3" style={SANS}>지표 변화</div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "에러율",    before: "8.2%",    after: "0.4%",   good: true },
                    { label: "응답시간",  before: "2,400ms", after: "190ms",  good: true },
                    { label: "재시작",    before: "6회",     after: "0회",    good: true },
                  ].map(m => (
                    <div key={m.label} className="text-center">
                      <div className="text-[8px] text-slate-500 mb-1" style={MONO}>{m.label}</div>
                      <div className="text-[10px] text-slate-400 line-through" style={MONO}>{m.before}</div>
                      <div className="text-[14px] font-bold text-emerald-400" style={SANS}>{m.after}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 감사 기록 */}
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <FileText size={12} className="text-slate-400" />
                  <span className="text-[10px] font-semibold text-slate-300" style={SANS}>감사 기록</span>
                </div>
                <div className="space-y-1.5 text-[9px]" style={MONO}>
                  {[
                    { label: "승인자",    val: "kim.admin (SRE Lead)" },
                    { label: "PR",        val: "#1235 — checkout-api-v2 config restore" },
                    { label: "변경 내용", val: "DB_POOL_SIZE 5→20 · memory 256Mi→512Mi" },
                    { label: "반영 시각", val: "2025-05-17 11:31:04 UTC+9" },
                    { label: "방식",      val: "GitOps (ArgoCD) — production 클러스터" },
                  ].map(r => (
                    <div key={r.label} className="flex gap-2">
                      <span className="text-slate-500 w-16 shrink-0">{r.label}</span>
                      <span className="text-slate-300">{r.val}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );

          return (
            <div key={idx} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
              {!isUser && (
                <div className="w-6 h-6 rounded-lg bg-indigo-500 flex items-center justify-center shrink-0 mr-2 mt-0.5">
                  <Sparkles size={11} className="text-white" />
                </div>
              )}
              <div className={`max-w-[82%] ${isUser ? "bg-indigo-600 text-white rounded-2xl rounded-tr-sm" : "bg-white/8 text-slate-200 rounded-2xl rounded-tl-sm"} px-4 py-3`}>
                <p className="text-[11px] leading-relaxed whitespace-pre-line" style={MONO}>{msg.text}</p>

                {/* 초기 분석 메시지 아래 근거 카드 */}
                {msg.stage === "init" && (
                  <div className="mt-3 space-y-2">
                    <button onClick={() => setShowEvidence(v => !v)}
                      className="flex items-center gap-1.5 text-[9px] text-indigo-300 hover:text-indigo-200 cursor-pointer transition-colors" style={MONO}>
                      <ChevronDown size={11} className={`transition-transform ${showEvidence ? "rotate-180" : ""}`} />
                      분석 근거 {showEvidence ? "접기" : "펼치기"}
                    </button>
                    {showEvidence && (
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        {[
                          { icon: GitBranch, label: "Git 변경", val: "DB_POOL_SIZE 20→5\nmemory 512Mi→256Mi", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
                          { icon: Cpu, label: "Pod 상태", val: "1/3 Running\n2개 비정상", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
                          { icon: Terminal, label: "로그 패턴", val: "DB timeout ×8\nOOMKilled ×3", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
                          { icon: TrendingDown, label: "지표 변화", val: "에러율 ↑ 8.2%\n응답시간 ↑ 2,400ms", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
                        ].map(c => {
                          const Icon = c.icon;
                          return (
                            <div key={c.label} className={`border rounded-xl p-3 ${c.bg}`}>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <Icon size={11} className={c.color} />
                                <span className={`text-[9px] font-bold ${c.color}`} style={SANS}>{c.label}</span>
                              </div>
                              <p className="text-[9px] text-slate-300 whitespace-pre-line leading-relaxed" style={MONO}>{c.val}</p>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}

                {/* Safe PR 제안 카드 (q2 단계) */}
                {msg.stage === "q2" && !prGenerated && (
                  <div className="mt-4 space-y-3">
                    {/* 조치 카드 */}
                    <div className="space-y-2">
                      {[
                        { label: "DB_POOL_SIZE 복원",     val: "5 → 20",           risk: "낮음", effect: "DB 연결 고갈 해소",  color: "border-emerald-500/30 bg-emerald-500/10" },
                        { label: "memory limit 복원",     val: "256Mi → 512Mi",    risk: "낮음", effect: "OOMKilled 방지",     color: "border-emerald-500/30 bg-emerald-500/10" },
                        { label: "배포 일시 중단",         val: "replicas pause",   risk: "중간", effect: "추가 피해 차단",     color: "border-amber-500/30 bg-amber-500/10" },
                        { label: "v1.4.1 롤백 (선택)",    val: "v1.4.2 → v1.4.1", risk: "중간", effect: "이전 상태 복원",     color: "border-slate-500/30 bg-white/5" },
                      ].map((a, i) => (
                        <div key={i} className={`border rounded-xl p-3 ${a.color}`}>
                          <div className="flex items-start justify-between mb-1.5">
                            <span className="text-[10px] font-bold text-slate-200" style={SANS}>{a.label}</span>
                            <span className={`text-[8px] px-1.5 py-0.5 rounded font-bold ${a.risk === "낮음" ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"}`} style={MONO}>위험도 {a.risk}</span>
                          </div>
                          <div className="flex items-center justify-between text-[9px]" style={MONO}>
                            <span className="text-slate-400">{a.val}</span>
                            <span className="text-slate-300">{a.effect}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* 검증 상태 */}
                    <div className="border border-white/10 rounded-xl p-3 bg-white/5">
                      <div className="text-[9px] text-slate-400 uppercase tracking-wider mb-2" style={MONO}>검증 결과</div>
                      <div className="space-y-1.5">
                        {[
                          { label: "dry-run 통과",    done: true  },
                          { label: "정책 검사 통과",   done: true  },
                          { label: "권한 검사 통과",   done: true  },
                          { label: "사용자 승인 대기", done: false },
                        ].map(v => (
                          <div key={v.label} className="flex items-center gap-2 text-[9px]" style={MONO}>
                            {v.done
                              ? <CheckCircle2 size={11} className="text-emerald-400 shrink-0" />
                              : <div className="w-2.5 h-2.5 rounded-full border-2 border-amber-400 shrink-0 animate-pulse" />}
                            <span className={v.done ? "text-slate-300" : "text-amber-300 font-semibold"}>{v.label}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* PR 생성 버튼 */}
                    <div className="flex gap-2">
                      <button onClick={handleCreatePR}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-[11px] font-bold cursor-pointer transition-colors" style={SANS}>
                        <GitBranch size={12} />Safe PR 생성
                      </button>
                      <button onClick={handleCreatePR}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-white/10 hover:bg-white/15 text-slate-200 rounded-xl text-[11px] font-semibold cursor-pointer transition-colors" style={SANS}>
                        <RefreshCw size={12} />롤백 PR 생성
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* 제안 질문 버튼 */}
        {stage === "init" && (
          <div className="space-y-2 pl-8">
            {[
              { q: "어디서 문제가 난 건가요?",        next: "q1" as ChatStage },
              { q: "바로 롤백해야 하나요?",            next: "q2" as ChatStage },
              { q: "수정하면 어떤 값부터 봐야 하나요?",next: "q3" as ChatStage },
            ].map(s => (
              <button key={s.q} onClick={() => handleQuestion(s.q, s.next)}
                className="w-full text-left px-4 py-2.5 bg-white/6 hover:bg-indigo-600/30 border border-white/10 hover:border-indigo-400/40 rounded-xl text-[11px] text-slate-300 cursor-pointer transition-all" style={MONO}>
                💬 {s.q}
              </button>
            ))}
          </div>
        )}

        {stage === "q1" && (
          <div className="space-y-2 pl-8">
            {[
              { q: "바로 롤백해야 하나요?",            next: "q2" as ChatStage },
              { q: "수정하면 어떤 값부터 봐야 하나요?",next: "q3" as ChatStage },
            ].map(s => (
              <button key={s.q} onClick={() => handleQuestion(s.q, s.next)}
                className="w-full text-left px-4 py-2.5 bg-white/6 hover:bg-indigo-600/30 border border-white/10 hover:border-indigo-400/40 rounded-xl text-[11px] text-slate-300 cursor-pointer transition-all" style={MONO}>
                💬 {s.q}
              </button>
            ))}
          </div>
        )}

        {stage === "q3" && (
          <div className="pl-8">
            <button onClick={() => handleQuestion("바로 롤백해야 하나요?", "q2")}
              className="w-full text-left px-4 py-2.5 bg-white/6 hover:bg-indigo-600/30 border border-white/10 hover:border-indigo-400/40 rounded-xl text-[11px] text-slate-300 cursor-pointer transition-all" style={MONO}>
              💬 바로 롤백해야 하나요?
            </button>
          </div>
        )}

        <div ref={r => { chatEndRef.current = r; }} />
      </div>

      {/* ── 입력창 ── */}
      <div className="px-4 py-3 border-t border-white/10 shrink-0 bg-white/3">
        <div className="flex items-center gap-2 bg-white/8 border border-white/10 rounded-xl px-3 py-2.5 focus-within:border-indigo-400/50 transition-colors">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder="Klaudia AI에게 질문하세요..."
            className="flex-1 bg-transparent text-[11px] text-slate-300 outline-none placeholder:text-slate-600"
            style={MONO}
          />
          <button onClick={handleSend}
            className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer transition-colors">
            <Send size={12} />
          </button>
        </div>
        <div className="text-[8px] text-slate-600 mt-1.5 text-center" style={MONO}>AI 답변은 시스템이 수집한 분석 자료 기반입니다</div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ROOT APP
// ═══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [screen, setScreen]           = useState<Screen>("overview");
  const [selectedSvc, setSelectedSvc] = useState<number | null>(null);
  const [aiMode, setAIMode]           = useState<AIMode>(null);
  const [recovered, setRecovered]     = useState(false);

  function openDiagnosticAI() { setAIMode("diagnostic"); }
  function openNewAI()        { setAIMode("new"); }
  function closeAI()          { setAIMode(null); }

  function selectService(id: number) {
    const svc = SERVICES.find(s => s.id === id);
    setSelectedSvc(id);
    // web-frontend (id=4) → 변경 위험 분석
    if (id === 4) {
      setScreen("change-risk");
      closeAI();
    } else {
      setScreen("service-detail");
      if (svc && !svc.healthy && !recovered) openDiagnosticAI();
    }
  }

  const currentSvc = SERVICES.find(s => s.id === selectedSvc);

  return (
    <div className="h-screen flex overflow-hidden bg-white" style={SANS}>
      <style>{`
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }
      `}</style>

      <Sidebar screen={screen} onNav={(s) => {
        setScreen(s);
        if (s !== "service-detail") setSelectedSvc(null);
        if (s !== "service" && s !== "service-detail") closeAI();
      }} />

      {/* 메인 컨텐츠 */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {screen === "clusters"        && <ClusterView />}
        {screen === "overview"        && <Overview onSelectService={selectService} />}
        {screen === "service"         && (
          <ServiceGrid onSelect={selectService} onNewAI={openNewAI} recovered={recovered} />
        )}
        {screen === "change-risk"     && (
          <ChangeRiskView onBack={() => setScreen("service")} onAIClick={openNewAI} />
        )}
        {screen === "service-detail"  && selectedSvc !== null && (
          <ServiceDetail
            serviceId={selectedSvc}
            onBack={() => { setScreen("service"); closeAI(); }}
            onDiagnosticAI={openDiagnosticAI}
            onNewAI={openNewAI}
            recovered={recovered}
          />
        )}
        {screen === "self-healing"       && <SelfHealing onNewAI={openNewAI} />}
        {screen === "cost-overview"          && <CostOverview onNav={(s) => setScreen(s)} />}
        {screen === "cost-right-sizing"      && <CostRightSizing />}
        {screen === "cost-pod-placement"     && <CostPodPlacement />}
        {screen === "resources-nodes"        && <ResourcesNodes />}
        {screen === "resources-deployments"  && <ResourcesDeployments />}
        {screen === "topology"               && <TopologyView />}
      </div>

      {/* AI 채팅 슬라이드인 */}
      {aiMode && (
        <>
          <div className="fixed inset-0 z-40 bg-black/20" onClick={closeAI} />
          <AIChat
            mode={aiMode}
            serviceName={currentSvc?.name}
            onClose={closeAI}
            onRecovered={() => setRecovered(true)}
          />
        </>
      )}
    </div>
  );
}
