"use client";

import React, { useState, useEffect, useCallback } from "react";
import { getNews, refreshNews } from "@/lib/api";
import NewsCard from "@/components/NewsCard";
import { NewsSkeletonGrid } from "@/components/LoadingState";
import FactCheckModal from "@/components/FactCheckModal";
import Button from "@/components/Button";
import ErrorState from "@/components/ErrorState";
import {
  Newspaper,
  Search,
  RefreshCw,
  Radio,
  Globe,
  Sparkles,
  X,
  ExternalLink,
} from "lucide-react";

export default function NewsPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [activeModalArticle, setActiveModalArticle] = useState(null);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const categories = [
    { id: "all", label: "ALL" },
    { id: "Technology", label: "TECH" },
    { id: "Science", label: "SCIENCE" },
    { id: "Politics", label: "POLITICS" },
    { id: "Health", label: "HEALTH" },
    { id: "Climate", label: "CLIMATE" },
  ];

  const fetchNews = useCallback(
    async (cat = selectedCategory, isRefresh = false, q = activeQuery) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        let res;
        if (isRefresh) {
          res = await refreshNews(cat, q);
        } else {
          res = await getNews(cat, { q });
        }

        if (res && res.data) {
          setArticles(res.data);
          setLastRefreshed(new Date());
        }
      } catch (err) {
        setError(err.message || "Failed to load news wire feed.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [selectedCategory, activeQuery]
  );

  // Initial load or category change
  useEffect(() => {
    fetchNews(selectedCategory, false, activeQuery);
  }, [selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = searchQuery.trim();
    setActiveQuery(trimmed);
    fetchNews(selectedCategory, false, trimmed);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setActiveQuery("");
    fetchNews(selectedCategory, false, "");
  };

  const handleRefresh = () => {
    fetchNews(selectedCategory, true, activeQuery);
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Page Header */}
      <div className="border-b-2 border-[#111111] pb-6 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 font-mono-tech text-xs uppercase font-bold text-[#111111]">
            <span className="w-2.5 h-2.5 rounded-full bg-[#B7FF3C] border border-[#111111] animate-ping" />
            <span>LIVE WEB INTELLIGENCE WIRE</span>
            {lastRefreshed && (
              <span className="hidden sm:inline-block text-[10px] bg-white border border-[#111111] px-2 py-0.5 ml-2 font-normal text-[#111111]/70">
                UPDATED: {lastRefreshed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              loading={refreshing}
              icon={RefreshCw}
              title="Force-refresh latest news from live web"
            >
              {refreshing ? "SYNCING..." : "REFRESH WIRE"}
            </Button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="font-display text-4xl sm:text-6xl uppercase tracking-tighter text-[#111111]">
              LATEST NEWS WIRE
            </h1>
            <p className="font-mono-tech text-xs sm:text-sm text-[#111111]/80 max-w-xl mt-1">
              Global intelligence feed continuously searched across the live web and parsed for factual integrity. Search any breaking event or verify any dispatch in real-time.
            </p>
          </div>
        </div>
      </div>

      {/* Control Bar: Categories & Live Web Search */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1">
          {categories.map((cat) => {
            const active = selectedCategory.toLowerCase() === cat.id.toLowerCase();
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 font-mono-tech text-xs uppercase font-bold border-2 border-[#111111] cursor-pointer whitespace-nowrap transition-all ${
                  active
                    ? "bg-[#111111] text-[#B7FF3C] shadow-hard-xs"
                    : "bg-white text-[#111111] hover:bg-[#E8E2D5]"
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>

        {/* Live Web Search Bar Form */}
        <form
          onSubmit={handleSearchSubmit}
          className="flex items-center gap-2 w-full lg:w-auto"
        >
          <div className="relative flex-1 lg:w-80">
            <input
              type="text"
              placeholder="Search any news from the web..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 font-mono-tech text-xs bg-white border-2 border-[#111111] shadow-hard-xs focus:outline-none focus:bg-[#F5F1E8]"
            />
            <Search className="w-4 h-4 text-[#111111] absolute left-3 top-3" />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-2.5 top-2.5 text-[#111111]/60 hover:text-[#111111] cursor-pointer"
                title="Clear search input"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <Button
            type="submit"
            variant="accent"
            size="sm"
            className="shrink-0 h-[38px] px-3.5"
            icon={Globe}
          >
            SEARCH WEB
          </Button>
        </form>
      </div>

      {/* Active Search / Filter State Pill */}
      {activeQuery && (
        <div className="flex items-center justify-between p-3 border-2 border-[#111111] bg-[#B7FF3C]/20 shadow-hard-xs">
          <div className="flex items-center gap-2 font-mono-tech text-xs text-[#111111]">
            <Globe className="w-4 h-4 text-[#111111]" />
            <span>
              LIVE WEB SEARCH RESULTS FOR:{" "}
              <strong className="underline decoration-2">&ldquo;{activeQuery}&rdquo;</strong>
            </span>
            <span className="bg-[#111111] text-[#B7FF3C] px-2 py-0.5 text-[10px] font-bold">
              {articles.length} DISPATCHES FOUND
            </span>
          </div>
          <button
            onClick={handleClearSearch}
            className="flex items-center gap-1 font-mono-tech text-xs uppercase font-bold text-[#111111] hover:text-[#FF4D4D] cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
            <span>CLEAR SEARCH</span>
          </button>
        </div>
      )}

      {/* Content Area */}
      {loading || refreshing ? (
        <div className="space-y-4">
          <div className="p-4 border-2 border-[#111111] bg-white shadow-hard-xs flex items-center justify-center gap-3 font-mono-tech text-xs uppercase font-bold">
            <RefreshCw className="w-4 h-4 text-[#111111] animate-spin" />
            <span>
              {activeQuery
                ? `SEARCHING LIVE WEB & GLOBAL WIRE FOR "${activeQuery}"...`
                : "FETCHING LATEST LIVE WIRE DISPATCHES FROM WEB..."}
            </span>
          </div>
          <NewsSkeletonGrid count={6} />
        </div>
      ) : error ? (
        <ErrorState
          title="FAILED TO RETRIEVE WIRE"
          message={error}
          onRetry={() => fetchNews(selectedCategory, true, activeQuery)}
        />
      ) : articles.length === 0 ? (
        <div className="border-2 border-[#111111] bg-white p-12 text-center shadow-hard space-y-4">
          <Globe className="w-10 h-10 text-[#111111] mx-auto" />
          <p className="font-display text-2xl uppercase text-[#111111]">
            NO WIRE ARTICLES FOUND
          </p>
          <p className="font-mono-tech text-xs text-[#111111]/70 max-w-md mx-auto">
            {activeQuery
              ? `No web news articles matched "${activeQuery}". Try searching for broader terms like "technology", "climate", or "science".`
              : "No current dispatches available for this category. Click Refresh Wire to fetch fresh news."}
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            {activeQuery && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearSearch}
              >
                CLEAR SEARCH
              </Button>
            )}
            <Button
              variant="accent"
              size="sm"
              onClick={handleRefresh}
              icon={RefreshCw}
            >
              REFRESH LIVE WIRE
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map((article, idx) => (
            <NewsCard
              key={article.id || `art-${idx}`}
              article={article}
              onFactCheck={(art) => setActiveModalArticle(art)}
            />
          ))}
        </div>
      )}

      {/* Fact Check Modal */}
      <FactCheckModal
        isOpen={!!activeModalArticle}
        article={activeModalArticle}
        onClose={() => setActiveModalArticle(null)}
      />
    </div>
  );
}
