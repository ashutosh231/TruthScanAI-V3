"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Users, CheckCircle, Newspaper, FolderTree, BarChart3, Cpu, History,
  Settings, LogOut, Search, Bell, ChevronLeft, ChevronRight, TrendingUp,
  AlertTriangle, XCircle, Plus, RefreshCw, Download, Eye, Edit,
  Trash2, ExternalLink, X, Sliders, Shield, Ban, Check, Sparkles,
  CreditCard,
} from "lucide-react";
import {
  getAdminStats, getAdminCharts, getAdminUsers, getAdminUserDetail,
  createAdminUser, updateAdminUser, deleteAdminUser, getAdminFactChecks,
  getAdminFactCheckDetail, deleteAdminFactCheck, reviewAdminFactCheck,
  getAdminNews, createAdminNews, updateAdminNews, deleteAdminNews,
  getAdminCategories, createAdminCategory, updateAdminCategory, deleteAdminCategory,
  getAdminAiMonitoring, getAdminActivityLogs, getAdminSettings,
  updateAdminSettings, changeAdminPassword, adminLogout,
} from "@/lib/api";
import {
  FactChecksLineChart, VerdictDonutChart, UserGrowthAreaChart,
  CategoryBarChart, DailyAiVolumeChart,
} from "@/components/admin/Charts";

// ─── Neo-Brutalist helpers ────────────────────────────────────────────────────
const cls = (...args) => args.filter(Boolean).join(" ");

function NBCard({ children, className = "" }) {
  return (
    <div className={cls("border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111] p-4 sm:p-5 overflow-hidden", className)}>
      {children}
    </div>
  );
}

function NBBtn({ children, onClick, className = "", type = "button", disabled = false, variant = "default", size = "sm" }) {
  const base = "inline-flex items-center justify-center gap-1.5 font-mono-tech font-bold uppercase tracking-wide border-2 border-[#111111] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none";
  const sizes = { xs: "px-2 py-0.5 text-[10px]", sm: "px-3 py-1.5 text-xs", md: "px-4 py-2 text-xs", lg: "px-5 py-2.5 text-sm" };
  const variants = {
    default: "bg-white text-[#111111] shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
    accent: "bg-[#B7FF3C] text-[#111111] shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
    dark: "bg-[#111111] text-[#B7FF3C] shadow-[2px_2px_0px_0px_#B7FF3C] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
    danger: "bg-[#EF4444] text-white shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
    warning: "bg-[#F59E0B] text-[#111111] shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
    success: "bg-[#22C55E] text-white shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]",
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled}
      className={cls(base, sizes[size] || sizes.sm, variants[variant] || variants.default, className)}>
      {children}
    </button>
  );
}

function NBInput({ className = "", ...props }) {
  return (
    <input
      {...props}
      className={cls(
        "w-full border-2 border-[#111111] bg-[#F5F1E8] px-3 py-2 font-mono-tech text-xs text-[#111111] placeholder-[#111111]/40 focus:outline-none focus:bg-white",
        className
      )}
    />
  );
}

function NBSelect({ children, className = "", ...props }) {
  return (
    <select
      {...props}
      className={cls(
        "border-2 border-[#111111] bg-[#F5F1E8] px-3 py-2 font-mono-tech text-xs text-[#111111] focus:outline-none focus:bg-white",
        className
      )}
    >
      {children}
    </select>
  );
}

function VerdictBadge({ verdict }) {
  const map = {
    TRUE: "bg-[#22C55E] text-white",
    FALSE: "bg-[#EF4444] text-white",
    MISLEADING: "bg-[#F59E0B] text-[#111111]",
    UNCERTAIN: "bg-[#E8E2D5] text-[#111111]",
  };
  return (
    <span className={cls("border border-[#111111] px-2 py-0.5 font-mono-tech text-[10px] font-bold uppercase inline-block text-center", map[verdict] || "bg-[#E8E2D5] text-[#111111]")}>
      {verdict || "UNKNOWN"}
    </span>
  );
}

function NBModal({ children, title, subtitle, onClose, wide = false }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#111111]/70 p-4">
      <div className={cls("relative border-2 border-[#111111] bg-white shadow-[8px_8px_0px_0px_#111111] overflow-y-auto max-h-[90vh]", wide ? "w-full max-w-2xl" : "w-full max-w-md")}>
        <div className="flex items-center justify-between bg-[#111111] px-5 py-3">
          <div>
            <span className="font-display text-sm uppercase text-[#B7FF3C]">{title}</span>
            {subtitle && <p className="font-mono-tech text-[10px] text-white/60 mt-0.5">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="text-[#B7FF3C] hover:text-white cursor-pointer">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function AdminDashboardPage() {
  const router = useRouter();

  const [activeTab, setActiveTab] = useState("overview");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [adminUser, setAdminUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [globalLoading, setGlobalLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  const [kpis, setKpis] = useState(null);
  const [overviewCharts, setOverviewCharts] = useState(null);

  // Users State
  const [usersList, setUsersList] = useState([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(1);
  const [usersSearch, setUsersSearch] = useState("");
  const [usersRoleFilter, setUsersRoleFilter] = useState("");
  const [usersStatusFilter, setUsersStatusFilter] = useState("");
  const [selectedUserDetail, setSelectedUserDetail] = useState(null);
  const [createUserModalOpen, setCreateUserModalOpen] = useState(false);
  const [editUserModalData, setEditUserModalData] = useState(null);
  const [deleteUserModalData, setDeleteUserModalData] = useState(null);
  const [userActionLoadingId, setUserActionLoadingId] = useState(null);

  // Fact Checks State
  const [factChecksList, setFactChecksList] = useState([]);
  const [factChecksTotal, setFactChecksTotal] = useState(0);
  const [factChecksPage, setFactChecksPage] = useState(1);
  const [fcSearch, setFcSearch] = useState("");
  const [fcVerdictFilter, setFcVerdictFilter] = useState("");
  const [selectedFactCheckDetail, setSelectedFactCheckDetail] = useState(null);
  const [reviewFactCheckModalData, setReviewFactCheckModalData] = useState(null);

  // News State
  const [newsList, setNewsList] = useState([]);
  const [newsTotal, setNewsTotal] = useState(0);
  const [newsPage, setNewsPage] = useState(1);
  const [newsSearch, setNewsSearch] = useState("");
  const [newsCategoryFilter, setNewsCategoryFilter] = useState("");
  const [createNewsModalOpen, setCreateNewsModalOpen] = useState(false);
  const [editNewsModalData, setEditNewsModalData] = useState(null);

  // Categories State
  const [categoriesList, setCategoriesList] = useState([]);
  const [createCategoryModalOpen, setCreateCategoryModalOpen] = useState(false);
  const [editCategoryModalData, setEditCategoryModalData] = useState(null);
  const [deleteCategoryModalData, setDeleteCategoryModalData] = useState(null);

  // Analytics & AI Monitoring
  const [analyticsPeriod, setAnalyticsPeriod] = useState("30d");
  const [analyticsCharts, setAnalyticsCharts] = useState(null);
  const [aiMonitoringData, setAiMonitoringData] = useState(null);

  // Activity Logs
  const [activityLogsList, setActivityLogsList] = useState([]);
  const [activityLogsTotal, setActivityLogsTotal] = useState(0);
  const [activityLogsPage, setActivityLogsPage] = useState(1);
  const [activityActionFilter, setActivityActionFilter] = useState("");

  // Settings
  const [settingsData, setSettingsData] = useState(null);
  const [changePasswordData, setChangePasswordData] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });

  const showToast = (message, type = "success") => {
    setToastMessage({ message, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const token = sessionStorage.getItem("truthscan_admin_token") || localStorage.getItem("truthscan_admin_token");
      const userStr = sessionStorage.getItem("truthscan_admin_user") || localStorage.getItem("truthscan_admin_user");
      if (!token || !userStr) { router.push("/login"); return; }
      try {
        const u = JSON.parse(userStr);
        const isAdmin = String(u.role || "").toLowerCase() === "admin" || u.isAdmin || u.email === "id-admin@gmail.com";
        if (!isAdmin) { router.push("/login"); return; }
        setAdminUser(u);
        setAuthChecking(false);
      } catch { router.push("/login"); }
    }
  }, [router]);

  const loadOverview = useCallback(async () => {
    setGlobalLoading(true);
    try {
      const [statsRes, chartsRes] = await Promise.all([getAdminStats(), getAdminCharts("30d")]);
      if (statsRes?.data?.kpis) setKpis(statsRes.data.kpis);
      if (chartsRes?.data) setOverviewCharts(chartsRes.data);
    } catch (err) { showToast(err.message || "Failed to load dashboard", "error"); }
    finally { setGlobalLoading(false); }
  }, []);

  const loadUsers = useCallback(async (page = 1) => {
    try {
      const res = await getAdminUsers({ page, limit: 15, search: usersSearch, role: usersRoleFilter, status: usersStatusFilter });
      if (res?.data) { setUsersList(res.data.users || []); setUsersTotal(res.data.total || 0); setUsersPage(page); }
    } catch (err) { showToast(err.message || "Failed to load users", "error"); }
  }, [usersSearch, usersRoleFilter, usersStatusFilter]);

  const loadFactChecks = useCallback(async (page = 1) => {
    try {
      const res = await getAdminFactChecks({ page, limit: 15, search: fcSearch, verdict: fcVerdictFilter });
      if (res?.data) { setFactChecksList(res.data.factChecks || []); setFactChecksTotal(res.data.total || 0); setFactChecksPage(page); }
    } catch (err) { showToast(err.message || "Failed to load fact checks", "error"); }
  }, [fcSearch, fcVerdictFilter]);

  const loadNews = useCallback(async (page = 1) => {
    try {
      const res = await getAdminNews({ page, limit: 15, search: newsSearch, category: newsCategoryFilter });
      if (res?.data) { setNewsList(res.data.news || []); setNewsTotal(res.data.total || 0); setNewsPage(page); }
    } catch (err) { showToast(err.message || "Failed to load news", "error"); }
  }, [newsSearch, newsCategoryFilter]);

  const loadCategories = useCallback(async () => {
    try {
      const res = await getAdminCategories();
      if (res?.data) setCategoriesList(res.data || []);
    } catch (err) { showToast(err.message || "Failed to load categories", "error"); }
  }, []);

  const loadAnalytics = useCallback(async (period = "30d") => {
    try {
      const res = await getAdminCharts(period);
      if (res?.data) setAnalyticsCharts(res.data);
    } catch (err) { showToast(err.message || "Failed to load analytics", "error"); }
  }, []);

  const loadAiMonitoring = useCallback(async () => {
    try {
      const res = await getAdminAiMonitoring();
      if (res?.data) setAiMonitoringData(res.data);
    } catch (err) { showToast(err.message || "Failed to load AI monitoring", "error"); }
  }, []);

  const loadActivityLogs = useCallback(async (page = 1) => {
    try {
      const res = await getAdminActivityLogs({ page, limit: 20, action: activityActionFilter });
      if (res?.data) { setActivityLogsList(res.data.logs || []); setActivityLogsTotal(res.data.total || 0); setActivityLogsPage(page); }
    } catch (err) { showToast(err.message || "Failed to load activity logs", "error"); }
  }, [activityActionFilter]);

  const loadSettings = useCallback(async () => {
    try {
      const res = await getAdminSettings();
      if (res?.data) setSettingsData(res.data);
    } catch (err) { showToast(err.message || "Failed to load settings", "error"); }
  }, []);

  useEffect(() => {
    if (authChecking) return;
    if (activeTab === "overview") loadOverview();
    else if (activeTab === "users") loadUsers(1);
    else if (activeTab === "factchecks") loadFactChecks(1);
    else if (activeTab === "news") loadNews(1);
    else if (activeTab === "categories") loadCategories();
    else if (activeTab === "analytics") loadAnalytics(analyticsPeriod);
    else if (activeTab === "monitoring") loadAiMonitoring();
    else if (activeTab === "activity") loadActivityLogs(1);
    else if (activeTab === "settings") loadSettings();
  }, [activeTab, authChecking, loadOverview, loadUsers, loadFactChecks, loadNews, loadCategories, loadAnalytics, analyticsPeriod, loadAiMonitoring, loadActivityLogs, loadSettings]);

  const handleLogout = async () => {
    await adminLogout();
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("truthscan_admin_token");
      sessionStorage.removeItem("truthscan_admin_user");
      localStorage.removeItem("truthscan_admin_token");
      localStorage.removeItem("truthscan_admin_user");
      sessionStorage.removeItem("truthscan_access_token");
      sessionStorage.removeItem("truthscan_user_session");
      localStorage.removeItem("truthscan_access_token");
      localStorage.removeItem("truthscan_user_session");
    }
    router.push("/login");
  };

  const refreshCurrentTab = () => {
    if (activeTab === "overview") loadOverview();
    else if (activeTab === "users") loadUsers(usersPage);
    else if (activeTab === "factchecks") loadFactChecks(factChecksPage);
    else if (activeTab === "news") loadNews(newsPage);
    else if (activeTab === "categories") loadCategories();
    else if (activeTab === "analytics") loadAnalytics(analyticsPeriod);
    else if (activeTab === "monitoring") loadAiMonitoring();
    else if (activeTab === "activity") loadActivityLogs(activityLogsPage);
    else if (activeTab === "settings") loadSettings();
    showToast("Data refreshed from MongoDB Atlas");
  };

  // ── User Manipulation Action Handlers ──
  const handleToggleSubscription = async (user) => {
    const nextPremium = !user.isPremium;
    const actionLabel = nextPremium ? "grant premium access to" : "revoke premium subscription from";
    if (!confirm(`Are you sure you want to ${actionLabel} ${user.email}?`)) return;

    setUserActionLoadingId(user.id);
    try {
      const res = await updateAdminUser(user.id, { isPremium: nextPremium });
      if (res?.success) {
        showToast(nextPremium ? `Premium subscription granted to ${user.name}` : `Subscription revoked for ${user.name}`);
        loadUsers(usersPage);
      } else {
        showToast(res?.message || "Failed to update subscription", "error");
      }
    } catch (err) {
      showToast(err.message || "Failed to update subscription", "error");
    } finally {
      setUserActionLoadingId(null);
    }
  };

  const handleToggleSuspension = async (user) => {
    const nextSuspended = !user.isSuspended;
    const actionLabel = nextSuspended ? "suspend account for" : "unsuspend account for";
    if (!confirm(`Are you sure you want to ${actionLabel} ${user.email}?`)) return;

    setUserActionLoadingId(user.id);
    try {
      const res = await updateAdminUser(user.id, { isSuspended: nextSuspended });
      if (res?.success) {
        showToast(nextSuspended ? `User ${user.email} suspended` : `User ${user.email} activated`);
        loadUsers(usersPage);
      } else {
        showToast(res?.message || "Failed to update suspension", "error");
      }
    } catch (err) {
      showToast(err.message || "Failed to update suspension", "error");
    } finally {
      setUserActionLoadingId(null);
    }
  };

  const handleDeleteUserConfirm = async (e) => {
    e.preventDefault();
    if (!deleteUserModalData) return;
    const isHard = e.target.isHard?.checked || false;

    setUserActionLoadingId(deleteUserModalData.id);
    try {
      const res = await deleteAdminUser(deleteUserModalData.id, isHard);
      if (res?.success) {
        showToast(`User ${deleteUserModalData.email} deleted successfully`);
        setDeleteUserModalData(null);
        loadUsers(usersPage);
      } else {
        showToast(res?.message || "Failed to delete user", "error");
      }
    } catch (err) {
      showToast(err.message || "Failed to delete user", "error");
    } finally {
      setUserActionLoadingId(null);
    }
  };

  if (authChecking) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center bg-[#F5F1E8]">
        <div className="border-2 border-[#111111] bg-white p-8 shadow-[4px_4px_0px_0px_#111111] text-center space-y-4">
          <Shield className="h-10 w-10 mx-auto text-[#111111]" />
          <div className="h-1 w-32 bg-[#111111] mx-auto overflow-hidden">
            <div className="h-full bg-[#B7FF3C] animate-[slide_1.5s_ease-in-out_infinite]" style={{ width: "60%" }} />
          </div>
          <p className="font-mono-tech text-xs font-bold uppercase tracking-widest text-[#111111]">Verifying Admin Clearance...</p>
        </div>
      </div>
    );
  }

  const navItems = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "users", label: "Users Management", icon: Users },
    { id: "factchecks", label: "Fact Checks", icon: CheckCircle },
    { id: "news", label: "News Management", icon: Newspaper },
    { id: "categories", label: "Categories", icon: FolderTree },
    { id: "analytics", label: "Analytics", icon: TrendingUp },
    { id: "monitoring", label: "AI Monitoring", icon: Cpu },
    { id: "activity", label: "Activity Logs", icon: History },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  return (
    /* Outer Neo-Brutalist Frame aligned with max-w-7xl */
    <div className="w-full border-2 border-[#111111] bg-[#F5F1E8] shadow-hard flex flex-col md:flex-row overflow-hidden min-h-[calc(100vh-140px)]">

      {/* ── Toast ─────────────────────────────────────────────────────────── */}
      {toastMessage && (
        <div className={cls(
          "fixed right-5 top-5 z-[999] flex items-center gap-2.5 border-2 border-[#111111] px-4 py-3 font-mono-tech text-xs font-bold uppercase shadow-[4px_4px_0px_0px_#111111]",
          toastMessage.type === "error" ? "bg-[#EF4444] text-white" : "bg-[#B7FF3C] text-[#111111]"
        )}>
          {toastMessage.type === "error" ? <AlertTriangle className="h-4 w-4" /> : <Check className="h-4 w-4" />}
          {toastMessage.message}
        </div>
      )}

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside className={cls(
        "flex flex-col border-b-2 md:border-b-0 md:border-r-2 border-[#111111] bg-white transition-all duration-300 shrink-0",
        sidebarCollapsed ? "md:w-16" : "md:w-60"
      )}>
        {/* Brand Header - exactly h-14 to match right topbar */}
        <div className="flex h-14 items-center justify-between border-b-2 border-[#111111] px-3">
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-[#111111]">
                <Shield className="h-4 w-4 text-[#B7FF3C]" />
              </div>
              <div className="overflow-hidden">
                <span className="font-display text-xs uppercase tracking-tight text-[#111111] block leading-tight">TruthScan</span>
                <span className="font-mono-tech text-[8px] font-bold uppercase tracking-widest text-[#B7FF3C] bg-[#111111] px-1 py-0.5 inline-block">Admin Core</span>
              </div>
            </div>
          )}
          {sidebarCollapsed && (
            <div className="flex h-8 w-8 items-center justify-center bg-[#111111] mx-auto">
              <Shield className="h-4 w-4 text-[#B7FF3C]" />
            </div>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden md:flex h-6 w-6 items-center justify-center border border-[#111111] hover:bg-[#B7FF3C] transition-colors cursor-pointer"
            title={sidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={sidebarCollapsed ? item.label : undefined}
                className={cls(
                  "flex w-full items-center gap-2.5 px-3 py-2.5 font-mono-tech text-[11px] font-bold uppercase tracking-wide transition-all border-l-4 cursor-pointer text-left",
                  isActive
                    ? "bg-[#B7FF3C] border-[#111111] text-[#111111]"
                    : "border-transparent text-[#111111]/70 hover:bg-[#F5F1E8] hover:text-[#111111] hover:border-[#111111]/30"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Admin User Footer / Logout */}
        <div className="border-t-2 border-[#111111] p-3 bg-[#F5F1E8]">
          <div className={cls("flex items-center gap-2", sidebarCollapsed ? "justify-center" : "justify-between")}>
            {!sidebarCollapsed && (
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center bg-[#111111] font-display text-xs text-[#B7FF3C]">
                  {adminUser?.name ? adminUser.name[0].toUpperCase() : "A"}
                </div>
                <div className="overflow-hidden">
                  <span className="block truncate font-mono-tech text-[11px] font-bold text-[#111111]">{adminUser?.name || "Admin"}</span>
                  <span className="block truncate font-mono-tech text-[9px] text-[#111111]/60">{adminUser?.email}</span>
                </div>
              </div>
            )}
            <button
              onClick={handleLogout}
              title="Terminate Admin Session"
              className="flex h-7 w-7 shrink-0 items-center justify-center border border-[#111111] bg-white hover:bg-[#EF4444] hover:text-white transition-colors cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area (min-w-0 to prevent flex layout blowout) ───────── */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#F5F1E8] overflow-hidden">

        {/* Top Header - exactly h-14 to align with sidebar header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b-2 border-[#111111] bg-white px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <h1 className="font-display text-base uppercase tracking-tight text-[#111111]">
              {navItems.find((n) => n.id === activeTab)?.label || "Overview"}
            </h1>
            <span className="border border-[#111111] bg-[#F5F1E8] px-2 py-0.5 font-mono-tech text-[9px] font-bold uppercase tracking-widest text-[#111111]/70">
              Live Mongo Atlas
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/"
              target="_blank"
              className="hidden items-center gap-1.5 border-2 border-[#111111] bg-[#F5F1E8] px-3 py-1 font-mono-tech text-[11px] font-bold uppercase hover:bg-[#B7FF3C] transition-colors sm:flex"
            >
              <ExternalLink className="h-3 w-3" /> Public Site
            </Link>

            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="relative border-2 border-[#111111] bg-[#F5F1E8] p-1.5 hover:bg-[#B7FF3C] transition-colors cursor-pointer"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute right-1 top-1 h-2 w-2 bg-[#B7FF3C] border border-[#111111]" />
              </button>
              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-72 border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111] z-50">
                  <div className="border-b-2 border-[#111111] bg-[#111111] px-3 py-2 flex items-center justify-between">
                    <span className="font-mono-tech text-xs font-bold uppercase text-[#B7FF3C]">System Status</span>
                    <span className="font-mono-tech text-[10px] text-[#B7FF3C]/70">Nominal</span>
                  </div>
                  <div className="p-3 space-y-2">
                    {[
                      { title: "AWS Bedrock DeepSeek V3.2", desc: "Operating at nominal latency (~1.34s)." },
                      { title: "MongoDB Atlas", desc: "PyMongo singleton client connected." },
                    ].map((n, i) => (
                      <div key={i} className="border border-[#111111]/20 bg-[#F5F1E8] p-2.5">
                        <p className="font-mono-tech text-[11px] font-bold text-[#111111]">{n.title}</p>
                        <p className="font-mono-tech text-[10px] text-[#111111]/60 mt-0.5">{n.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={refreshCurrentTab}
              className="flex items-center gap-1.5 border-2 border-[#111111] bg-[#F5F1E8] px-3 py-1 font-mono-tech text-[11px] font-bold uppercase hover:bg-[#B7FF3C] transition-colors cursor-pointer"
            >
              <RefreshCw className={cls("h-3.5 w-3.5", globalLoading && "animate-spin")} />
              <span className="hidden sm:inline">Sync DB</span>
            </button>
          </div>
        </header>

        {/* Content Container */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto">

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 1: OVERVIEW                                                   */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "overview" && (
            <div className="space-y-5">
              {/* Top KPI Cards Row */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: "Total Users", value: kpis?.totalUsers?.value ?? 0, sub: `+${kpis?.totalUsers?.growth ?? 0}%`, icon: Users, accent: "#B7FF3C" },
                  { label: "Fact Checks", value: kpis?.totalFactChecks?.value ?? 0, sub: `+${kpis?.totalFactChecks?.growth ?? 0}%`, icon: CheckCircle, accent: "#B7FF3C" },
                  { label: "False Claims", value: kpis?.falseClaims?.value ?? 0, sub: `${kpis?.falseClaims?.pct ?? 0}% share`, icon: XCircle, accent: "#EF4444" },
                  { label: "Active Users", value: kpis?.activeUsers?.value ?? 0, sub: `${kpis?.activeUsers?.pct ?? 0}% active`, icon: TrendingUp, accent: "#22C55E" },
                ].map(({ label, value, sub, icon: Icon, accent }) => (
                  <div key={label} className="border-2 border-[#111111] bg-white p-4 shadow-[4px_4px_0px_0px_#111111]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#111111]/70">{label}</span>
                      <span className="flex h-7 w-7 items-center justify-center border border-[#111111]" style={{ backgroundColor: accent }}>
                        <Icon className="h-3.5 w-3.5 text-[#111111]" />
                      </span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="font-display text-3xl text-[#111111]">{value}</span>
                      <span className="font-mono-tech text-xs font-bold" style={{ color: accent === "#EF4444" ? "#EF4444" : "#111111" }}>{sub}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
                <NBCard className="lg:col-span-2">
                  <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Fact Checks Over Time</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Daily verification volume across verdicts</p>
                  <FactChecksLineChart data={overviewCharts?.factChecksOverTime || []} />
                </NBCard>
                <NBCard>
                  <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Verdict Distribution</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Aggregate breakdown</p>
                  <VerdictDonutChart data={overviewCharts?.verdictDistribution || []} />
                </NBCard>
              </div>

              {/* Quick Actions */}
              <div className="border-2 border-[#111111] bg-white p-4 flex flex-wrap items-center gap-3">
                <span className="font-mono-tech text-[11px] font-bold uppercase tracking-wider text-[#111111]/70 mr-1">Quick Actions:</span>
                <NBBtn variant="accent" onClick={() => { setActiveTab("users"); setCreateUserModalOpen(true); }}>
                  <Plus className="h-3.5 w-3.5" /> Add User
                </NBBtn>
                <NBBtn onClick={() => { setActiveTab("news"); setCreateNewsModalOpen(true); }}>
                  <Newspaper className="h-3.5 w-3.5" /> Publish Article
                </NBBtn>
                <NBBtn onClick={() => { setActiveTab("categories"); setCreateCategoryModalOpen(true); }}>
                  <FolderTree className="h-3.5 w-3.5" /> Add Category
                </NBBtn>
                <NBBtn onClick={() => setActiveTab("monitoring")}>
                  <Cpu className="h-3.5 w-3.5" /> AI Telemetry
                </NBBtn>
              </div>

              {/* Category + Sources */}
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                <NBCard>
                  <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Fact Checks by Category</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Narrative density across domains</p>
                  <CategoryBarChart data={overviewCharts?.categories || []} />
                </NBCard>
                <NBCard>
                  <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Top Sources</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Institutional corroboration registries</p>
                  <div className="space-y-2">
                    {(overviewCharts?.topSources || []).map((s, idx) => (
                      <div key={idx} className="flex items-center justify-between border border-[#111111]/20 bg-[#F5F1E8] px-3 py-2">
                        <span className="font-mono-tech text-xs text-[#111111]">{s.source}</span>
                        <span className="border border-[#111111] bg-[#B7FF3C] px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#111111]">{s.count} cited</span>
                      </div>
                    ))}
                    {(!overviewCharts?.topSources || overviewCharts.topSources.length === 0) && (
                      <p className="font-mono-tech text-xs text-[#111111]/40 text-center py-4">No sources recorded yet.</p>
                    )}
                  </div>
                </NBCard>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 2: USERS MANAGEMENT (MANIPULATE, REVOKE SUB, DELETE)          */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "users" && (
            <div className="space-y-4">
              {/* Controls Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-2 border-[#111111] bg-white p-3">
                <div className="flex flex-wrap items-center gap-2 flex-1">
                  <div className="relative min-w-[200px] flex-1 sm:flex-initial">
                    <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#111111]/40" />
                    <NBInput
                      placeholder="Search name or email..."
                      value={usersSearch}
                      onChange={(e) => setUsersSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && loadUsers(1)}
                      className="pl-8"
                    />
                  </div>
                  <NBSelect value={usersRoleFilter} onChange={(e) => { setUsersRoleFilter(e.target.value); setUsersPage(1); }}>
                    <option value="">All Roles</option>
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </NBSelect>
                  <NBSelect value={usersStatusFilter} onChange={(e) => { setUsersStatusFilter(e.target.value); setUsersPage(1); }}>
                    <option value="">All Statuses</option>
                    <option value="verified">Verified</option>
                    <option value="unverified">Unverified</option>
                    <option value="suspended">Suspended</option>
                  </NBSelect>
                  <NBBtn onClick={() => loadUsers(1)}><Search className="h-3.5 w-3.5" /> Search</NBBtn>
                </div>
                <NBBtn variant="accent" onClick={() => setCreateUserModalOpen(true)}>
                  <Plus className="h-3.5 w-3.5" /> Add User
                </NBBtn>
              </div>

              {/* Users Table Container (responsive with overflow-x-auto & min-width) */}
              <div className="w-full overflow-x-auto border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111]">
                <table className="w-full min-w-[860px] text-left text-xs table-auto">
                  <thead className="border-b-2 border-[#111111] bg-[#111111]">
                    <tr>
                      <th className="w-[240px] px-4 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">User Profile</th>
                      <th className="w-[80px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Role</th>
                      <th className="w-[170px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Subscription Tier</th>
                      <th className="w-[70px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Checks</th>
                      <th className="w-[95px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Status</th>
                      <th className="w-[95px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Registered</th>
                      <th className="w-[140px] px-4 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C] text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersList.length === 0 ? (
                      <tr><td colSpan="7" className="p-8 text-center font-mono-tech text-xs text-[#111111]/40">No users match your filters.</td></tr>
                    ) : usersList.map((u, ri) => (
                      <tr key={u.id} className={cls("border-b border-[#111111]/10 hover:bg-[#F5F1E8] transition-colors", ri % 2 === 1 && "bg-[#F5F1E8]/50")}>
                        {/* User Profile (truncated to prevent blowout) */}
                        <td className="w-[240px] max-w-[240px] px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-[#111111] font-display text-xs text-[#B7FF3C]">
                              {u.name?.[0]?.toUpperCase() || "U"}
                            </div>
                            <div className="overflow-hidden min-w-0">
                              <div className="font-mono-tech text-[11px] font-bold text-[#111111] truncate" title={u.name}>{u.name}</div>
                              <div className="font-mono-tech text-[10px] text-[#111111]/60 truncate" title={u.email}>{u.email}</div>
                            </div>
                          </div>
                        </td>

                        {/* Role */}
                        <td className="w-[80px] px-3 py-3">
                          <span className={cls("border px-2 py-0.5 font-mono-tech text-[10px] font-bold uppercase inline-block",
                            u.role === "admin" ? "border-[#111111] bg-[#111111] text-[#B7FF3C]" : "border-[#111111]/30 bg-[#F5F1E8] text-[#111111]"
                          )}>{u.role}</span>
                        </td>

                        {/* Subscription Tier + Quick Revoke / Grant Action */}
                        <td className="w-[170px] px-3 py-3">
                          <div className="flex items-center gap-2">
                            <span className={cls("border px-2 py-0.5 font-mono-tech text-[10px] font-bold inline-block shrink-0",
                              u.isPremium ? "border-[#D97706] bg-[#F59E0B]/10 text-[#D97706]" : "border-[#111111]/20 bg-[#F5F1E8] text-[#111111]/60"
                            )}>
                              {u.isPremium ? "PRO ACTIVE" : "FREE TIER"}
                            </span>

                            {/* Direct Action: Revoke or Grant Subscription */}
                            {u.isPremium ? (
                              <button
                                onClick={() => handleToggleSubscription(u)}
                                disabled={userActionLoadingId === u.id}
                                title="Revoke Premium Subscription"
                                className="border border-[#EF4444] bg-[#EF4444]/10 hover:bg-[#EF4444] hover:text-white px-1.5 py-0.5 font-mono-tech text-[9px] font-bold uppercase text-[#EF4444] transition-colors cursor-pointer"
                              >
                                {userActionLoadingId === u.id ? "..." : "REVOKE"}
                              </button>
                            ) : (
                              <button
                                onClick={() => handleToggleSubscription(u)}
                                disabled={userActionLoadingId === u.id}
                                title="Grant Pro Subscription"
                                className="border border-[#111111] bg-[#B7FF3C] hover:bg-[#a3f021] px-1.5 py-0.5 font-mono-tech text-[9px] font-bold uppercase text-[#111111] transition-colors cursor-pointer"
                              >
                                {userActionLoadingId === u.id ? "..." : "GRANT PRO"}
                              </button>
                            )}
                          </div>
                        </td>

                        {/* Checks Count */}
                        <td className="w-[70px] px-3 py-3 font-display text-sm text-[#111111]">{u.factChecksCount || 0}</td>

                        {/* Status + Quick Suspend Toggle */}
                        <td className="w-[95px] px-3 py-3">
                          {u.isSuspended ? (
                            <span className="border border-[#EF4444] bg-[#EF4444]/10 px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#EF4444] block text-center">Suspended</span>
                          ) : u.isVerified ? (
                            <span className="border border-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#22C55E] block text-center">Verified</span>
                          ) : (
                            <span className="border border-[#F59E0B] bg-[#F59E0B]/10 px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#D97706] block text-center">Pending OTP</span>
                          )}
                        </td>

                        {/* Registered */}
                        <td className="w-[95px] px-3 py-3 font-mono-tech text-[10px] text-[#111111]/60">{u.createdAt?.slice(0, 10) || "N/A"}</td>

                        {/* Actions (View, Edit, Suspend, Delete) */}
                        <td className="w-[140px] px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {/* View Dossier */}
                            <button
                              onClick={async () => { const d = await getAdminUserDetail(u.id); if (d?.data) setSelectedUserDetail(d.data); }}
                              className="border border-[#111111]/30 bg-white p-1.5 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"
                              title="View Full User Dossier"
                            >
                              <Eye className="h-3.5 w-3.5 text-[#111111]" />
                            </button>

                            {/* Edit / Manipulate User */}
                            <button
                              onClick={() => setEditUserModalData(u)}
                              className="border border-[#111111]/30 bg-white p-1.5 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"
                              title="Edit / Manipulate User Profile"
                            >
                              <Edit className="h-3.5 w-3.5 text-[#111111]" />
                            </button>

                            {/* Suspend / Unsuspend Quick Toggle */}
                            <button
                              onClick={() => handleToggleSuspension(u)}
                              className={cls(
                                "border p-1.5 transition-colors cursor-pointer",
                                u.isSuspended
                                  ? "border-[#22C55E] bg-[#22C55E]/10 text-[#22C55E] hover:bg-[#22C55E] hover:text-white"
                                  : "border-[#F59E0B] bg-[#F59E0B]/10 text-[#D97706] hover:bg-[#F59E0B] hover:text-[#111111]"
                              )}
                              title={u.isSuspended ? "Unsuspend User Account" : "Suspend User Account"}
                            >
                              <Ban className="h-3.5 w-3.5" />
                            </button>

                            {/* Delete User */}
                            <button
                              onClick={() => setDeleteUserModalData(u)}
                              className="border border-[#EF4444] bg-white p-1.5 hover:bg-[#EF4444] hover:text-white transition-colors cursor-pointer"
                              title="Delete User"
                            >
                              <Trash2 className="h-3.5 w-3.5 text-[#EF4444] hover:text-white" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Table Footer / Pagination */}
                <div className="flex items-center justify-between border-t-2 border-[#111111] bg-[#F5F1E8] px-4 py-2.5">
                  <span className="font-mono-tech text-[10px] text-[#111111]/70 font-bold">
                    Showing {usersList.length} of {usersTotal} registered users
                  </span>
                  <div className="flex items-center gap-2">
                    <NBBtn size="xs" disabled={usersPage <= 1} onClick={() => loadUsers(usersPage - 1)}>← Prev</NBBtn>
                    <span className="font-mono-tech text-[10px] font-bold">Page {usersPage}</span>
                    <NBBtn size="xs" disabled={usersList.length < 15} onClick={() => loadUsers(usersPage + 1)}>Next →</NBBtn>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 3: FACT CHECKS                                                */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "factchecks" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-2 border-[#111111] bg-white p-3">
                <div className="flex flex-wrap items-center gap-2 flex-1">
                  <div className="relative min-w-[240px] flex-1 sm:flex-initial">
                    <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#111111]/40" />
                    <NBInput
                      placeholder="Search claims or explanations..."
                      value={fcSearch}
                      onChange={(e) => setFcSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && loadFactChecks(1)}
                      className="pl-8"
                    />
                  </div>
                  <NBSelect value={fcVerdictFilter} onChange={(e) => { setFcVerdictFilter(e.target.value); setFactChecksPage(1); }}>
                    <option value="">All Verdicts</option>
                    <option value="TRUE">TRUE</option>
                    <option value="FALSE">FALSE</option>
                    <option value="MISLEADING">MISLEADING</option>
                    <option value="UNCERTAIN">UNCERTAIN</option>
                  </NBSelect>
                  <NBBtn onClick={() => loadFactChecks(1)}><Search className="h-3.5 w-3.5" /> Search</NBBtn>
                </div>
                <a
                  href={`${(process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000/api").replace(/\/+$/, "")}/admin/fact-checks?export=csv`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 border-2 border-[#111111] bg-[#F5F1E8] px-3 py-1.5 font-mono-tech text-[11px] font-bold uppercase hover:bg-[#B7FF3C] transition-colors"
                >
                  <Download className="h-3.5 w-3.5" /> Export CSV
                </a>
              </div>

              <div className="w-full overflow-x-auto border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111]">
                <table className="w-full min-w-[860px] text-left text-xs table-auto">
                  <thead className="border-b-2 border-[#111111] bg-[#111111]">
                    <tr>
                      <th className="w-[280px] px-4 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Analyzed Claim</th>
                      <th className="w-[70px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Type</th>
                      <th className="w-[100px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Verdict</th>
                      <th className="w-[110px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Confidence</th>
                      <th className="w-[120px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Investigator</th>
                      <th className="w-[90px] px-3 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]">Date</th>
                      <th className="w-[90px] px-4 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C] text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {factChecksList.length === 0 ? (
                      <tr><td colSpan="7" className="p-8 text-center font-mono-tech text-xs text-[#111111]/40">No fact check records match your filters.</td></tr>
                    ) : factChecksList.map((fc, ri) => (
                      <tr key={fc.id} className={cls("border-b border-[#111111]/10 hover:bg-[#F5F1E8] transition-colors", ri % 2 === 1 && "bg-[#F5F1E8]/50")}>
                        <td className="w-[280px] max-w-[280px] px-4 py-3">
                          <span className="line-clamp-2 font-mono-tech text-[11px] text-[#111111]">{fc.input}</span>
                        </td>
                        <td className="w-[70px] px-3 py-3">
                          <span className="border border-[#111111]/20 bg-[#F5F1E8] px-2 py-0.5 font-mono-tech text-[10px] uppercase text-[#111111] inline-block">{fc.type || "text"}</span>
                        </td>
                        <td className="w-[100px] px-3 py-3"><VerdictBadge verdict={fc.verdict} /></td>
                        <td className="w-[110px] px-3 py-3">
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-14 border border-[#111111] bg-[#F5F1E8] overflow-hidden">
                              <div className="h-full bg-[#B7FF3C]" style={{ width: `${Math.min(100, fc.confidence || 0)}%` }} />
                            </div>
                            <span className="font-mono-tech text-[11px] font-bold">{fc.confidence}%</span>
                          </div>
                        </td>
                        <td className="w-[120px] max-w-[120px] px-3 py-3 font-mono-tech text-[11px] text-[#111111]/80 truncate">
                          {fc.userName || fc.userEmail || "Anonymous"}
                        </td>
                        <td className="w-[90px] px-3 py-3 font-mono-tech text-[10px] text-[#111111]/60">{fc.createdAt?.slice(0, 10)}</td>
                        <td className="w-[90px] px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              onClick={async () => { const d = await getAdminFactCheckDetail(fc.id); if (d?.data) setSelectedFactCheckDetail(d.data); }}
                              className="border border-[#111111]/30 bg-white p-1.5 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"
                              title="Inspect AI Dossier"
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={() => setReviewFactCheckModalData(fc)}
                              className="border border-[#111111]/30 bg-white p-1.5 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"
                              title="Record Admin Review"
                            >
                              <Sliders className="h-3.5 w-3.5" />
                            </button>
                            <button
                              onClick={async () => {
                                if (confirm("Delete this fact-check audit record? This action is permanent and audited.")) {
                                  const r = await deleteAdminFactCheck(fc.id);
                                  r?.success ? (showToast("Record deleted"), loadFactChecks(factChecksPage)) : showToast(r?.message || "Failed", "error");
                                }
                              }}
                              className="border border-[#EF4444] bg-white p-1.5 hover:bg-[#EF4444] hover:text-white transition-colors cursor-pointer"
                              title="Delete Record"
                            >
                              <Trash2 className="h-3.5 w-3.5 text-[#EF4444] hover:text-white" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex items-center justify-between border-t-2 border-[#111111] bg-[#F5F1E8] px-4 py-2.5">
                  <span className="font-mono-tech text-[10px] text-[#111111]/70 font-bold">{factChecksList.length} of {factChecksTotal} audits</span>
                  <div className="flex items-center gap-2">
                    <NBBtn size="xs" disabled={factChecksPage <= 1} onClick={() => loadFactChecks(factChecksPage - 1)}>← Prev</NBBtn>
                    <span className="font-mono-tech text-[10px] font-bold">Page {factChecksPage}</span>
                    <NBBtn size="xs" disabled={factChecksList.length < 15} onClick={() => loadFactChecks(factChecksPage + 1)}>Next →</NBBtn>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 4: NEWS MANAGEMENT                                            */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "news" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-2 border-[#111111] bg-white p-3">
                <div className="flex flex-wrap items-center gap-2 flex-1">
                  <div className="relative min-w-[220px] flex-1 sm:flex-initial">
                    <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#111111]/40" />
                    <NBInput
                      placeholder="Search headline or source..."
                      value={newsSearch}
                      onChange={(e) => setNewsSearch(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && loadNews(1)}
                      className="pl-8"
                    />
                  </div>
                  <NBSelect value={newsCategoryFilter} onChange={(e) => { setNewsCategoryFilter(e.target.value); setNewsPage(1); }}>
                    <option value="">All Categories</option>
                    {["General","Technology","Science","Politics","Health","Climate"].map(c => <option key={c} value={c}>{c}</option>)}
                  </NBSelect>
                </div>
                <NBBtn variant="accent" onClick={() => setCreateNewsModalOpen(true)}>
                  <Plus className="h-3.5 w-3.5" /> Publish Article
                </NBBtn>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {newsList.length === 0 ? (
                  <div className="col-span-3 border-2 border-dashed border-[#111111]/30 p-10 text-center font-mono-tech text-xs text-[#111111]/40">
                    No news articles match your filters.
                  </div>
                ) : newsList.map((item) => (
                  <div key={item.id} className="flex flex-col border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111]">
                    {item.image && (
                      <img src={item.image} alt={item.title} className="h-36 w-full object-cover border-b-2 border-[#111111]" />
                    )}
                    <div className="flex-1 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="border border-[#111111]/30 bg-[#F5F1E8] px-2 py-0.5 font-mono-tech text-[10px] text-[#111111]">{item.category || "General"}</span>
                        <span className={cls("border px-2 py-0.5 font-mono-tech text-[10px] font-bold",
                          item.isPublished ? "border-[#22C55E] bg-[#22C55E]/10 text-[#22C55E]" : "border-[#111111]/20 bg-[#F5F1E8] text-[#111111]/60"
                        )}>{item.isPublished ? "Published" : "Draft"}</span>
                      </div>
                      <h4 className="font-display text-sm uppercase text-[#111111] line-clamp-2 mb-1">{item.title}</h4>
                      <p className="font-mono-tech text-[11px] text-[#111111]/70 line-clamp-2">{item.description}</p>
                      <div className="mt-2 font-mono-tech text-[10px] text-[#111111]/50">Source: {item.source}</div>
                    </div>
                    <div className="flex items-center justify-between border-t-2 border-[#111111] px-4 py-2 bg-[#F5F1E8]">
                      <button
                        onClick={async () => {
                          const r = await updateAdminNews(item.id, { isPublished: !item.isPublished });
                          if (r?.success) { showToast(`Article ${!item.isPublished ? "published" : "set to draft"}`); loadNews(newsPage); }
                        }}
                        className="font-mono-tech text-[11px] font-bold uppercase text-[#111111] hover:text-[#B7FF3C] transition-colors cursor-pointer"
                      >
                        {item.isPublished ? "Unpublish" : "Publish"}
                      </button>
                      <div className="flex items-center gap-1">
                        <button onClick={() => setEditNewsModalData(item)} className="border border-[#111111]/30 p-1 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"><Edit className="h-3.5 w-3.5" /></button>
                        <button onClick={async () => { if (confirm("Delete this article?")) { const r = await deleteAdminNews(item.id); r?.success ? (showToast("Article deleted"), loadNews(newsPage)) : showToast(r?.message || "Failed", "error"); } }}
                          className="border border-[#EF4444] p-1 hover:bg-[#EF4444] hover:text-white transition-colors cursor-pointer"><Trash2 className="h-3.5 w-3.5 text-[#EF4444] hover:text-white" /></button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 5: CATEGORIES                                                 */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "categories" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-2 border-[#111111] bg-white p-3">
                <div>
                  <h3 className="font-display text-sm uppercase text-[#111111]">Domain Taxonomy</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60">Categories referenced across investigations</p>
                </div>
                <NBBtn variant="accent" onClick={() => setCreateCategoryModalOpen(true)}>
                  <Plus className="h-3.5 w-3.5" /> New Category
                </NBBtn>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {categoriesList.map((cat) => (
                  <div key={cat.id} className="border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111] p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="h-4 w-4 border border-[#111111]" style={{ backgroundColor: cat.color || "#B7FF3C" }} />
                      <span className="border border-[#111111]/20 bg-[#F5F1E8] px-2 py-0.5 font-mono-tech text-[10px] text-[#111111]">{cat.factChecksCount || 0} refs</span>
                    </div>
                    <h4 className="font-display text-sm uppercase text-[#111111] mb-1">{cat.name}</h4>
                    <p className="font-mono-tech text-[11px] text-[#111111]/60 line-clamp-2 mb-2">{cat.description}</p>
                    <div className="font-mono-tech text-[10px] text-[#111111]/50 mb-3">/{cat.slug}</div>
                    <div className="flex items-center justify-end gap-1 border-t border-[#111111]/10 pt-2">
                      <button onClick={() => setEditCategoryModalData(cat)} className="border border-[#111111]/30 p-1 hover:bg-[#B7FF3C] hover:border-[#111111] transition-colors cursor-pointer"><Edit className="h-3.5 w-3.5" /></button>
                      <button onClick={() => setDeleteCategoryModalData(cat)} className="border border-[#EF4444] p-1 hover:bg-[#EF4444] hover:text-white transition-colors cursor-pointer"><Trash2 className="h-3.5 w-3.5 text-[#EF4444] hover:text-white" /></button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 6: ANALYTICS                                                  */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "analytics" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between border-2 border-[#111111] bg-white p-3">
                <div>
                  <h3 className="font-display text-sm uppercase text-[#111111]">Aggregated Intelligence Analytics</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60">Direct MongoDB pipeline groupings</p>
                </div>
                <div className="flex items-center gap-1 border-2 border-[#111111] p-1 bg-[#F5F1E8]">
                  {["7d","30d","90d","365d"].map((p) => (
                    <button key={p} onClick={() => { setAnalyticsPeriod(p); loadAnalytics(p); }}
                      className={cls("px-3 py-1 font-mono-tech text-[11px] font-bold uppercase transition-colors cursor-pointer",
                        analyticsPeriod === p ? "bg-[#111111] text-[#B7FF3C]" : "text-[#111111]/60 hover:text-[#111111]"
                      )}>{p}</button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">Fact Checks Over Time</h4>
                  <FactChecksLineChart data={analyticsCharts?.factChecksOverTime || []} />
                </NBCard>
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">User Registration Growth</h4>
                  <UserGrowthAreaChart data={analyticsCharts?.userGrowth || []} />
                </NBCard>
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">Verdict Distribution</h4>
                  <VerdictDonutChart data={analyticsCharts?.verdictDistribution || []} />
                </NBCard>
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">By Domain Category</h4>
                  <CategoryBarChart data={analyticsCharts?.categories || []} />
                </NBCard>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 7: AI MONITORING                                              */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "monitoring" && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {[
                  { label: "Overall Success Rate", value: `${aiMonitoringData?.summary?.overallSuccessRate ?? 98.8}%`, color: "#22C55E" },
                  { label: "Avg Processing Latency", value: `${aiMonitoringData?.summary?.averageLatencyMs ?? 1180}ms`, color: "#2563EB" },
                  { label: "Total Neural Requests", value: aiMonitoringData?.summary?.totalRequests ?? 0, color: "#7C3AED" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="border-2 border-[#111111] bg-white p-5 shadow-[4px_4px_0px_0px_#111111]">
                    <span className="font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#111111]/60">{label}</span>
                    <div className="mt-2 font-display text-3xl" style={{ color }}>{value}</div>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">Daily Multi-Model Volume</h4>
                  <DailyAiVolumeChart data={aiMonitoringData?.dailyVolume || []} />
                </NBCard>
                <NBCard>
                  <h4 className="font-display text-sm uppercase text-[#111111] mb-3">Foundation Model Status</h4>
                  <div className="space-y-3">
                    {(aiMonitoringData?.models || []).map((m, i) => (
                      <div key={i} className="border-2 border-[#111111]/20 bg-[#F5F1E8] p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-mono-tech text-xs font-bold text-[#111111]">{m.name}</span>
                          <span className="border border-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#22C55E]">{m.status}</span>
                        </div>
                        <div className="flex items-center gap-4 font-mono-tech text-[10px] text-[#111111]/70">
                          <span>Calls: <strong className="text-[#111111]">{m.invocations}</strong></span>
                          <span>Success: <strong className="text-[#22C55E]">{m.successRate}%</strong></span>
                          <span>Latency: <strong className="text-[#2563EB]">{m.avgLatencyMs}ms</strong></span>
                        </div>
                      </div>
                    ))}
                    {(!aiMonitoringData?.models || aiMonitoringData.models.length === 0) && (
                      <p className="font-mono-tech text-xs text-[#111111]/40 text-center py-4">No model telemetry recorded.</p>
                    )}
                  </div>
                </NBCard>
              </div>

              {/* Recent AI Telemetry Table */}
              <div className="w-full overflow-x-auto border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111]">
                <div className="border-b-2 border-[#111111] bg-[#111111] px-4 py-2">
                  <span className="font-mono-tech text-xs font-bold uppercase text-[#B7FF3C]">Recent Neural Activity</span>
                </div>
                <table className="w-full min-w-[700px] text-left text-xs table-auto">
                  <thead className="border-b border-[#111111]/20 bg-[#F5F1E8]">
                    <tr>
                      {["Service","Operation","Claim Analyzed","Verdict","Latency","Status"].map(h => (
                        <th key={h} className="px-4 py-2 font-mono-tech text-[10px] font-bold uppercase text-[#111111]/70">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(aiMonitoringData?.recentActivity || []).map((log, i) => (
                      <tr key={i} className="border-b border-[#111111]/10 hover:bg-[#F5F1E8] transition-colors">
                        <td className="px-4 py-2 font-mono-tech text-[11px] font-bold text-[#111111]">{log.service}</td>
                        <td className="px-4 py-2 font-mono-tech text-[11px] text-[#111111]/70">{log.operation}</td>
                        <td className="max-w-[220px] truncate px-4 py-2 font-mono-tech text-[11px] text-[#111111]/60" title={log.claim}>{log.claim}</td>
                        <td className="px-4 py-2"><VerdictBadge verdict={log.verdict} /></td>
                        <td className="px-4 py-2 font-mono-tech text-[11px] text-[#111111]/60">{log.latencyMs}ms</td>
                        <td className="px-4 py-2">
                          <span className="border border-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#22C55E]">{log.status}</span>
                        </td>
                      </tr>
                    ))}
                    {(!aiMonitoringData?.recentActivity || aiMonitoringData.recentActivity.length === 0) && (
                      <tr><td colSpan="6" className="p-6 text-center font-mono-tech text-xs text-[#111111]/40">No recent AI activity logged.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 8: ACTIVITY LOGS                                              */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "activity" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-2 border-[#111111] bg-white p-3">
                <div>
                  <h3 className="font-display text-sm uppercase text-[#111111]">Admin Audit Trail</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60">Immutable ledger of administrative actions</p>
                </div>
                <NBSelect value={activityActionFilter} onChange={(e) => { setActivityActionFilter(e.target.value); setActivityLogsPage(1); }}>
                  <option value="">All Actions</option>
                  <option value="ADMIN_LOGIN">Admin Login</option>
                  <option value="USER_CREATED">User Created</option>
                  <option value="USER_UPDATED">User Updated</option>
                  <option value="USER_DELETED">User Deleted</option>
                  <option value="FACTCHECK_DELETED">Fact Check Deleted</option>
                  <option value="FACTCHECK_REVIEWED">Fact Check Reviewed</option>
                  <option value="NEWS_CREATED">News Created</option>
                  <option value="CATEGORY_CREATED">Category Created</option>
                </NBSelect>
              </div>

              <div className="w-full overflow-x-auto border-2 border-[#111111] bg-white shadow-[4px_4px_0px_0px_#111111]">
                <table className="w-full min-w-[760px] text-left text-xs table-auto">
                  <thead className="border-b-2 border-[#111111] bg-[#111111]">
                    <tr>
                      {["Action","Administrator","Target","IP Address","Details","Timestamp"].map((h, i) => (
                        <th key={h} className={cls("px-4 py-3 font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#B7FF3C]", i === 5 && "text-right")}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {activityLogsList.length === 0 ? (
                      <tr><td colSpan="6" className="p-8 text-center font-mono-tech text-xs text-[#111111]/40">No audit logs recorded yet.</td></tr>
                    ) : activityLogsList.map((log, ri) => (
                      <tr key={log.id} className={cls("border-b border-[#111111]/10 hover:bg-[#F5F1E8]", ri % 2 === 1 && "bg-[#F5F1E8]/50")}>
                        <td className="px-4 py-3">
                          <span className="border border-[#111111] bg-[#B7FF3C] px-2 py-0.5 font-mono-tech text-[10px] font-bold text-[#111111] inline-block">{log.action}</span>
                        </td>
                        <td className="px-4 py-3 font-mono-tech text-[11px] font-bold text-[#111111]">{log.adminEmail || "System"}</td>
                        <td className="px-4 py-3 font-mono-tech text-[11px] uppercase text-[#111111]/70">{log.targetType}</td>
                        <td className="px-4 py-3 font-mono-tech text-[10px] text-[#111111]/60">{log.ipAddress || "127.0.0.1"}</td>
                        <td className="max-w-[200px] truncate px-4 py-3 font-mono-tech text-[10px] text-[#111111]/50">{JSON.stringify(log.details || {})}</td>
                        <td className="px-4 py-3 text-right font-mono-tech text-[10px] text-[#111111]/60">{log.createdAt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex items-center justify-between border-t-2 border-[#111111] bg-[#F5F1E8] px-4 py-2.5">
                  <span className="font-mono-tech text-[10px] text-[#111111]/70 font-bold">{activityLogsList.length} of {activityLogsTotal} entries</span>
                  <div className="flex items-center gap-2">
                    <NBBtn size="xs" disabled={activityLogsPage <= 1} onClick={() => loadActivityLogs(activityLogsPage - 1)}>← Prev</NBBtn>
                    <span className="font-mono-tech text-[10px] font-bold">Page {activityLogsPage}</span>
                    <NBBtn size="xs" disabled={activityLogsList.length < 20} onClick={() => loadActivityLogs(activityLogsPage + 1)}>Next →</NBBtn>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ═════════════════════════════════════════════════════════════════ */}
          {/* TAB 9: SETTINGS                                                   */}
          {/* ═════════════════════════════════════════════════════════════════ */}
          {activeTab === "settings" && (
            <div className="max-w-2xl space-y-5">
              <NBCard>
                <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Administrator Profile</h3>
                <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Verified system administrator credentials</p>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {[
                    { label: "Display Name", value: adminUser?.name || "TruthScan Administrator" },
                    { label: "Email Address", value: adminUser?.email || "id-admin@gmail.com" },
                    { label: "Assigned Role", value: `SUPERUSER (${adminUser?.role})`, accent: true },
                    { label: "Security Clearance", value: "ACTIVE / UNRESTRICTED", green: true },
                  ].map(({ label, value, accent, green }) => (
                    <div key={label} className="border border-[#111111]/20 bg-[#F5F1E8] p-3">
                      <span className="font-mono-tech text-[9px] font-bold uppercase tracking-wider text-[#111111]/60">{label}</span>
                      <p className={cls("mt-1 font-mono-tech text-xs font-bold", accent ? "text-[#111111]" : green ? "text-[#22C55E]" : "text-[#111111]")}>{value}</p>
                    </div>
                  ))}
                </div>
              </NBCard>

              <NBCard>
                <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Change Admin Password</h3>
                <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Updates credentials in MongoDB Atlas</p>
                <form onSubmit={async (e) => {
                  e.preventDefault();
                  if (changePasswordData.newPassword !== changePasswordData.confirmPassword) { showToast("Passwords do not match", "error"); return; }
                  const res = await changeAdminPassword({ currentPassword: changePasswordData.currentPassword, newPassword: changePasswordData.newPassword });
                  if (res?.success) { showToast("Password updated"); setChangePasswordData({ currentPassword: "", newPassword: "", confirmPassword: "" }); }
                  else showToast(res?.message || "Failed", "error");
                }} className="space-y-3">
                  {[
                    { label: "Current Password", key: "currentPassword" },
                    { label: "New Password (min 8 chars)", key: "newPassword" },
                    { label: "Confirm New Password", key: "confirmPassword" },
                  ].map(({ label, key }) => (
                    <div key={key}>
                      <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">{label}</label>
                      <NBInput type="password" required minLength={8} value={changePasswordData[key]}
                        onChange={(e) => setChangePasswordData({ ...changePasswordData, [key]: e.target.value })} />
                    </div>
                  ))}
                  <NBBtn type="submit" variant="dark">Update Credentials</NBBtn>
                </form>
              </NBCard>

              {settingsData && (
                <NBCard>
                  <h3 className="font-display text-sm uppercase text-[#111111] mb-1">Portal Preferences</h3>
                  <p className="font-mono-tech text-[11px] text-[#111111]/60 mb-4">Interface defaults and alert parameters</p>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-[#111111]/10 pb-3">
                      <div>
                        <p className="font-mono-tech text-xs font-bold text-[#111111]">Default Date Window</p>
                        <p className="font-mono-tech text-[10px] text-[#111111]/60">Telemetry range on initial load</p>
                      </div>
                      <NBSelect value={settingsData.dashboardDateDefault || "30d"}
                        onChange={async (e) => { const u = { ...settingsData, dashboardDateDefault: e.target.value }; setSettingsData(u); await updateAdminSettings(u); showToast("Saved"); }}>
                        <option value="7d">7 Days</option>
                        <option value="30d">30 Days</option>
                        <option value="90d">90 Days</option>
                      </NBSelect>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-mono-tech text-xs font-bold text-[#111111]">Email Alerts on Security Events</p>
                        <p className="font-mono-tech text-[10px] text-[#111111]/60">Brevo transactional alerts on anomalies</p>
                      </div>
                      <input type="checkbox" checked={!!settingsData.emailAlerts}
                        onChange={async (e) => { const u = { ...settingsData, emailAlerts: e.target.checked }; setSettingsData(u); await updateAdminSettings(u); showToast("Saved"); }}
                        className="h-4 w-4 cursor-pointer" />
                    </div>
                  </div>
                </NBCard>
              )}
            </div>
          )}

        </div>
      </main>

      {/* ═════════════════════════════════════════════════════════════════ */}
      {/* MODALS & DRAWERS                                                  */}
      {/* ═════════════════════════════════════════════════════════════════ */}

      {/* 1. Fact Check Full Dossier Inspection Drawer */}
      {selectedFactCheckDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-[#111111]/70 p-4">
          <div className="h-full w-full max-w-2xl border-2 border-[#111111] bg-white shadow-[-8px_0px_0px_0px_#B7FF3C] overflow-y-auto">
            <div className="flex items-center justify-between border-b-2 border-[#111111] bg-[#111111] px-5 py-3">
              <span className="font-display text-sm uppercase text-[#B7FF3C]">Fact Check Dossier</span>
              <button onClick={() => setSelectedFactCheckDetail(null)} className="text-[#B7FF3C] hover:text-white cursor-pointer"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-5">
              <div>
                <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">Submitted Claim</span>
                <div className="mt-1 border-2 border-[#111111] bg-[#F5F1E8] p-3 font-mono-tech text-xs text-[#111111]">{selectedFactCheckDetail.input}</div>
              </div>
              <div className="flex items-center gap-6">
                <div>
                  <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">AI Verdict</span>
                  <div className="mt-1"><VerdictBadge verdict={selectedFactCheckDetail.verdict} /></div>
                </div>
                <div>
                  <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">Confidence</span>
                  <div className="mt-1 font-display text-xl text-[#111111]">{selectedFactCheckDetail.confidence}%</div>
                </div>
              </div>
              <div>
                <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">Forensic Explanation</span>
                <div className="mt-1 border border-[#111111]/20 bg-[#F5F1E8] p-3 font-mono-tech text-xs leading-relaxed text-[#111111]">{selectedFactCheckDetail.explanation}</div>
              </div>
              {selectedFactCheckDetail.metadata?.debunkingEvidence?.length > 0 && (
                <div>
                  <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">Debunking Evidence</span>
                  <ul className="mt-2 space-y-1 font-mono-tech text-xs text-[#111111]">
                    {selectedFactCheckDetail.metadata.debunkingEvidence.map((ev, i) => (
                      <li key={i} className="flex gap-2 items-start"><span className="text-[#B7FF3C] font-bold">›</span>{ev}</li>
                    ))}
                  </ul>
                </div>
              )}
              {selectedFactCheckDetail.metadata?.sourcesChecked?.length > 0 && (
                <div>
                  <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60">Sources Checked</span>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {selectedFactCheckDetail.metadata.sourcesChecked.map((s, i) => (
                      <span key={i} className="border border-[#111111]/30 bg-[#F5F1E8] px-2 py-0.5 font-mono-tech text-[10px] text-[#111111]">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 2. Fact Check Review Modal */}
      {reviewFactCheckModalData && (
        <NBModal title="Admin Review" subtitle="Attach official decision to this fact check" onClose={() => setReviewFactCheckModalData(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await reviewAdminFactCheck(reviewFactCheckModalData.id, { decision: form.decision.value, notes: form.notes.value });
            if (res?.success) { showToast("Review recorded"); setReviewFactCheckModalData(null); loadFactChecks(factChecksPage); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-4">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Official Decision</label>
              <NBSelect name="decision" className="w-full">
                <option value="CONFIRMED">CONFIRMED – Endorse AI Finding</option>
                <option value="CONTESTED">CONTESTED – Flag for Research</option>
                <option value="ARCHIVED">ARCHIVED – Closed / Historical</option>
              </NBSelect>
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Review Notes</label>
              <textarea name="notes" required rows="3" placeholder="Administrator assessment..."
                className="w-full border-2 border-[#111111] bg-[#F5F1E8] p-2.5 font-mono-tech text-xs focus:outline-none focus:bg-white" />
            </div>
            <div className="flex justify-end gap-2">
              <NBBtn onClick={() => setReviewFactCheckModalData(null)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="dark">Save Decision</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 3. Create User Modal */}
      {createUserModalOpen && (
        <NBModal title="Add User Account" subtitle="Creates a new user directly in MongoDB Atlas" onClose={() => setCreateUserModalOpen(false)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await createAdminUser({
              name: form.name.value,
              email: form.email.value,
              password: form.password.value,
              role: form.role.value,
              isVerified: form.isVerified.checked,
              isPremium: form.isPremium.checked,
            });
            if (res?.success) { showToast("User created successfully"); setCreateUserModalOpen(false); loadUsers(1); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-3">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Full Name</label>
              <NBInput type="text" name="name" required placeholder="Investigator Name" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Email Address</label>
              <NBInput type="email" name="email" required placeholder="analyst@domain.com" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Initial Password (min 8 chars)</label>
              <NBInput type="password" name="password" required minLength={8} placeholder="••••••••••••" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Role</label>
              <NBSelect name="role" className="w-full">
                <option value="user">User (Standard Investigator)</option>
                <option value="admin">Administrator</option>
              </NBSelect>
            </div>
            <div className="flex gap-4 pt-1">
              <label className="flex items-center gap-2 font-mono-tech text-[11px] text-[#111111] cursor-pointer">
                <input type="checkbox" name="isVerified" defaultChecked className="h-3.5 w-3.5" /> Verified Email
              </label>
              <label className="flex items-center gap-2 font-mono-tech text-[11px] text-[#111111] cursor-pointer">
                <input type="checkbox" name="isPremium" className="h-3.5 w-3.5" /> Premium Subscription
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setCreateUserModalOpen(false)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="accent">Create Account</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 4. Edit User Modal (Full User Manipulation) */}
      {editUserModalData && (
        <NBModal title="Manipulate User Account" subtitle={editUserModalData.email} onClose={() => setEditUserModalData(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const payload = {
              name: form.name.value,
              role: form.role.value,
              isVerified: form.isVerified.checked,
              isPremium: form.isPremium.checked,
              isSuspended: form.isSuspended.checked,
            };
            if (form.password.value) payload.password = form.password.value;
            const res = await updateAdminUser(editUserModalData.id, payload);
            if (res?.success) { showToast("User profile updated"); setEditUserModalData(null); loadUsers(usersPage); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-4">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Full Name</label>
              <NBInput type="text" name="name" required defaultValue={editUserModalData.name} />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Assigned Role</label>
                <NBSelect name="role" defaultValue={editUserModalData.role} className="w-full">
                  <option value="user">User</option>
                  <option value="admin">Administrator</option>
                </NBSelect>
              </div>
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Password Override</label>
                <NBInput type="password" name="password" minLength={8} placeholder="Leave blank to preserve" />
              </div>
            </div>

            {/* Direct Subscription & Status Manipulation Controls */}
            <div className="border-2 border-[#111111] bg-[#F5F1E8] p-3 space-y-2.5">
              <span className="font-mono-tech text-[10px] font-bold uppercase tracking-wider text-[#111111] block">
                Clearance & Entitlements Control
              </span>

              <label className="flex items-center justify-between p-2 border border-[#111111]/30 bg-white cursor-pointer">
                <div>
                  <span className="font-mono-tech text-xs font-bold text-[#111111] block">Premium Subscription</span>
                  <span className="font-mono-tech text-[10px] text-[#111111]/60">Unrestricted scans & priority neural synthesis</span>
                </div>
                <input type="checkbox" name="isPremium" defaultChecked={editUserModalData.isPremium} className="h-4 w-4 cursor-pointer" />
              </label>

              <label className="flex items-center justify-between p-2 border border-[#111111]/30 bg-white cursor-pointer">
                <div>
                  <span className="font-mono-tech text-xs font-bold text-[#111111] block">Verification Status</span>
                  <span className="font-mono-tech text-[10px] text-[#111111]/60">Email OTP verification confirmed</span>
                </div>
                <input type="checkbox" name="isVerified" defaultChecked={editUserModalData.isVerified} className="h-4 w-4 cursor-pointer" />
              </label>

              <label className="flex items-center justify-between p-2 border border-[#EF4444]/40 bg-white cursor-pointer">
                <div>
                  <span className="font-mono-tech text-xs font-bold text-[#EF4444] block">Account Suspended</span>
                  <span className="font-mono-tech text-[10px] text-[#111111]/60">Blocks login & revokes current access tokens</span>
                </div>
                <input type="checkbox" name="isSuspended" defaultChecked={editUserModalData.isSuspended} className="h-4 w-4 cursor-pointer" />
              </label>
            </div>

            <div className="flex justify-between items-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setDeleteUserModalData(editUserModalData);
                  setEditUserModalData(null);
                }}
                className="font-mono-tech text-xs text-[#EF4444] hover:underline font-bold uppercase cursor-pointer"
              >
                Delete User...
              </button>

              <div className="flex gap-2">
                <NBBtn onClick={() => setEditUserModalData(null)}>Cancel</NBBtn>
                <NBBtn type="submit" variant="accent">Save Changes</NBBtn>
              </div>
            </div>
          </form>
        </NBModal>
      )}

      {/* 5. Delete User Confirmation Modal */}
      {deleteUserModalData && (
        <NBModal
          title="Confirm User Deletion"
          subtitle={deleteUserModalData.email}
          onClose={() => setDeleteUserModalData(null)}
        >
          <form onSubmit={handleDeleteUserConfirm} className="space-y-4">
            <div className="border-2 border-[#EF4444] bg-[#EF4444]/10 p-4 font-mono-tech text-xs text-[#111111] space-y-2">
              <div className="flex items-center gap-2 font-bold text-[#EF4444]">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>CONFIRM CLEARANCE DELETION</span>
              </div>
              <p className="leading-relaxed">
                You are about to remove user <strong className="font-bold">{deleteUserModalData.email}</strong>.
                This action is recorded in the immutable administrator audit trail.
              </p>
              {deleteUserModalData.email === "id-admin@gmail.com" && (
                <p className="font-bold text-[#EF4444]">
                  PROTECTED: The primary administrator account cannot be deleted.
                </p>
              )}
            </div>

            <div className="border border-[#111111]/20 bg-[#F5F1E8] p-3">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input type="checkbox" name="isHard" className="mt-0.5 h-4 w-4 cursor-pointer" />
                <div>
                  <span className="font-mono-tech text-xs font-bold text-[#111111] block">Permanent Delete (Hard purge)</span>
                  <span className="font-mono-tech text-[10px] text-[#111111]/60 block">
                    Unchecked = soft delete (sets isDeleted: true, preserves audit logs). Checked = removes MongoDB document permanently.
                  </span>
                </div>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setDeleteUserModalData(null)}>Cancel</NBBtn>
              <NBBtn
                type="submit"
                variant="danger"
                disabled={deleteUserModalData.email === "id-admin@gmail.com" || userActionLoadingId === deleteUserModalData.id}
              >
                {userActionLoadingId === deleteUserModalData.id ? "Deleting..." : "Confirm Deletion"}
              </NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 6. User Dossier Drawer */}
      {selectedUserDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-[#111111]/70 p-4">
          <div className="h-full w-full max-w-md border-2 border-[#111111] bg-white shadow-[-8px_0px_0px_0px_#B7FF3C] overflow-y-auto">
            <div className="flex items-center justify-between border-b-2 border-[#111111] bg-[#111111] px-5 py-3">
              <span className="font-display text-sm uppercase text-[#B7FF3C]">Investigator Dossier</span>
              <button onClick={() => setSelectedUserDetail(null)} className="text-[#B7FF3C] hover:text-white cursor-pointer"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center bg-[#111111] font-display text-lg text-[#B7FF3C]">
                  {selectedUserDetail.name?.[0]?.toUpperCase() || "U"}
                </div>
                <div className="overflow-hidden">
                  <div className="font-display text-base uppercase text-[#111111] truncate">{selectedUserDetail.name}</div>
                  <div className="font-mono-tech text-xs text-[#111111]/60 truncate">{selectedUserDetail.email}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {[
                  ["Role", selectedUserDetail.role],
                  ["Fact Checks", selectedUserDetail.factChecksCount || 0],
                  ["Verified", selectedUserDetail.isVerified ? "Yes" : "No"],
                  ["Subscription", selectedUserDetail.isPremium ? "Premium (Active)" : "Free Tier"],
                  ["Suspended", selectedUserDetail.isSuspended ? "Yes (Blocked)" : "No (Active)"],
                  ["Joined", selectedUserDetail.createdAt?.slice(0, 10) || "N/A"],
                ].map(([label, value]) => (
                  <div key={label} className="border border-[#111111]/20 bg-[#F5F1E8] p-2.5">
                    <span className="font-mono-tech text-[9px] font-bold uppercase text-[#111111]/60">{label}</span>
                    <p className="font-mono-tech text-xs font-bold text-[#111111] mt-0.5 truncate">{String(value)}</p>
                  </div>
                ))}
              </div>

              {/* Dossier Quick Manipulation Actions */}
              <div className="pt-2 border-t border-[#111111]/10 space-y-2">
                <span className="font-mono-tech text-[10px] font-bold uppercase text-[#111111]/60 block">Direct Actions</span>
                <div className="flex flex-wrap gap-2">
                  <NBBtn
                    variant={selectedUserDetail.isPremium ? "warning" : "accent"}
                    size="xs"
                    onClick={() => {
                      handleToggleSubscription(selectedUserDetail);
                      setSelectedUserDetail(null);
                    }}
                  >
                    <CreditCard className="h-3 w-3" />
                    {selectedUserDetail.isPremium ? "Revoke Subscription" : "Grant Premium"}
                  </NBBtn>
                  <NBBtn
                    variant="default"
                    size="xs"
                    onClick={() => {
                      setEditUserModalData(selectedUserDetail);
                      setSelectedUserDetail(null);
                    }}
                  >
                    <Edit className="h-3 w-3" /> Edit Profile
                  </NBBtn>
                  <NBBtn
                    variant="danger"
                    size="xs"
                    onClick={() => {
                      setDeleteUserModalData(selectedUserDetail);
                      setSelectedUserDetail(null);
                    }}
                  >
                    <Trash2 className="h-3 w-3" /> Delete
                  </NBBtn>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. Create News Modal */}
      {createNewsModalOpen && (
        <NBModal title="Publish News Article" subtitle="Saves article to MongoDB news wire" onClose={() => setCreateNewsModalOpen(false)} wide>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await createAdminNews({ title: form.title.value, description: form.description.value, url: form.url.value, image: form.image.value, source: form.source.value, category: form.category.value, isPublished: form.isPublished.checked });
            if (res?.success) { showToast("Article published"); setCreateNewsModalOpen(false); loadNews(1); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-3">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Headline</label>
              <NBInput type="text" name="title" required />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Summary</label>
              <textarea name="description" required rows="3" className="w-full border-2 border-[#111111] bg-[#F5F1E8] p-2.5 font-mono-tech text-xs focus:outline-none focus:bg-white" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Source</label>
                <NBInput type="text" name="source" defaultValue="TruthScan Wire" />
              </div>
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Category</label>
                <NBSelect name="category" className="w-full">
                  {["General","Technology","Science","Politics","Health","Climate"].map(c => <option key={c} value={c}>{c}</option>)}
                </NBSelect>
              </div>
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Reference URL</label>
              <NBInput type="url" name="url" defaultValue="https://truthscan.ai" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Image URL</label>
              <NBInput type="url" name="image" defaultValue="https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop" />
            </div>
            <label className="flex items-center gap-2 font-mono-tech text-[11px] cursor-pointer">
              <input type="checkbox" name="isPublished" defaultChecked className="h-3.5 w-3.5" /> Publish immediately
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setCreateNewsModalOpen(false)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="accent">Publish Article</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 8. Edit News Modal */}
      {editNewsModalData && (
        <NBModal title="Edit Article" subtitle={editNewsModalData.title} onClose={() => setEditNewsModalData(null)} wide>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await updateAdminNews(editNewsModalData.id, { title: form.title.value, description: form.description.value, source: form.source.value, category: form.category.value, isPublished: form.isPublished.checked });
            if (res?.success) { showToast("Article updated"); setEditNewsModalData(null); loadNews(newsPage); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-3">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Headline</label>
              <NBInput type="text" name="title" required defaultValue={editNewsModalData.title} />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Summary</label>
              <textarea name="description" required rows="3" defaultValue={editNewsModalData.description}
                className="w-full border-2 border-[#111111] bg-[#F5F1E8] p-2.5 font-mono-tech text-xs focus:outline-none focus:bg-white" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Source</label>
                <NBInput type="text" name="source" defaultValue={editNewsModalData.source} />
              </div>
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Category</label>
                <NBSelect name="category" defaultValue={editNewsModalData.category} className="w-full">
                  {["General","Technology","Science","Politics","Health","Climate"].map(c => <option key={c} value={c}>{c}</option>)}
                </NBSelect>
              </div>
            </div>
            <label className="flex items-center gap-2 font-mono-tech text-[11px] cursor-pointer">
              <input type="checkbox" name="isPublished" defaultChecked={editNewsModalData.isPublished} className="h-3.5 w-3.5" /> Published
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setEditNewsModalData(null)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="accent">Save Changes</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 9. Create Category Modal */}
      {createCategoryModalOpen && (
        <NBModal title="Create Category" subtitle="Adds taxonomy category for investigations" onClose={() => setCreateCategoryModalOpen(false)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await createAdminCategory({ name: form.name.value, description: form.description.value, color: form.color.value, isActive: true });
            if (res?.success) { showToast("Category created"); setCreateCategoryModalOpen(false); loadCategories(); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-3">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Category Name</label>
              <NBInput type="text" name="name" required placeholder="e.g. Geopolitics" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Description</label>
              <textarea name="description" rows="2" placeholder="Brief scope..." className="w-full border-2 border-[#111111] bg-[#F5F1E8] p-2.5 font-mono-tech text-xs focus:outline-none focus:bg-white" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Accent Color Hex</label>
              <NBInput type="text" name="color" defaultValue="#B7FF3C" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setCreateCategoryModalOpen(false)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="accent">Create Category</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 10. Edit Category Modal */}
      {editCategoryModalData && (
        <NBModal title="Edit Category" subtitle={editCategoryModalData.name} onClose={() => setEditCategoryModalData(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const form = e.target;
            const res = await updateAdminCategory(editCategoryModalData.id, { name: form.name.value, description: form.description.value, color: form.color.value });
            if (res?.success) { showToast("Category updated"); setEditCategoryModalData(null); loadCategories(); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-3">
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Name</label>
              <NBInput type="text" name="name" required defaultValue={editCategoryModalData.name} />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Description</label>
              <textarea name="description" rows="2" defaultValue={editCategoryModalData.description}
                className="w-full border-2 border-[#111111] bg-[#F5F1E8] p-2.5 font-mono-tech text-xs focus:outline-none focus:bg-white" />
            </div>
            <div>
              <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Accent Color</label>
              <NBInput type="text" name="color" defaultValue={editCategoryModalData.color || "#B7FF3C"} />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <NBBtn onClick={() => setEditCategoryModalData(null)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="accent">Save Changes</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

      {/* 11. Delete Category Modal */}
      {deleteCategoryModalData && (
        <NBModal title={`Delete: ${deleteCategoryModalData.name}`}
          subtitle={deleteCategoryModalData.factChecksCount > 0 ? `Referenced by ${deleteCategoryModalData.factChecksCount} record(s)` : "No references. Safe to delete."}
          onClose={() => setDeleteCategoryModalData(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            const slug = e.target.reassignToSlug?.value || "";
            const res = await deleteAdminCategory(deleteCategoryModalData.id, slug);
            if (res?.success) { showToast(res.message); setDeleteCategoryModalData(null); loadCategories(); }
            else showToast(res?.message || "Failed", "error");
          }} className="space-y-4">
            {deleteCategoryModalData.factChecksCount > 0 && (
              <div>
                <label className="mb-1 block font-mono-tech text-[10px] font-bold uppercase text-[#111111]">Reassign records to</label>
                <NBSelect name="reassignToSlug" className="w-full">
                  {categoriesList.filter(c => c.id !== deleteCategoryModalData.id).map(c => (
                    <option key={c.id} value={c.slug}>{c.name}</option>
                  ))}
                </NBSelect>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <NBBtn onClick={() => setDeleteCategoryModalData(null)}>Cancel</NBBtn>
              <NBBtn type="submit" variant="danger">Confirm Delete</NBBtn>
            </div>
          </form>
        </NBModal>
      )}

    </div>
  );
}
