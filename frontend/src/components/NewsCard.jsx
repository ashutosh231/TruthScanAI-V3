"use client";

import React, { useState } from "react";
import Badge from "./Badge";
import Button from "./Button";
import { Clock, ExternalLink, Sparkles } from "lucide-react";

export default function NewsCard({ article, onFactCheck }) {
  const [imgSrc, setImgSrc] = useState(
    article?.image ||
      "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop"
  );

  if (!article) return null;

  const headline = article.headline || article.title || "Breaking Intelligence Report";
  const source = typeof article.source === "string" ? article.source : article.source?.name || "Global News Wire";
  const {
    sourceIcon,
    category,
    publishedAt,
    description,
    url,
    verifiedVerdict,
  } = article;

  const formatPublishDate = (dateStr) => {
    if (!dateStr) return "Just now";
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return String(dateStr).slice(0, 16);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return String(dateStr).slice(0, 16);
    }
  };

  return (
    <article className="group flex flex-col justify-between border-2 border-[#111111] bg-white shadow-hard hover:shadow-hard-lg hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all duration-150 overflow-hidden">
      <div>
        {/* News Image with Category Badge Sticker */}
        <div className="relative w-full h-48 sm:h-52 bg-[#E8E2D5] border-b-2 border-[#111111] overflow-hidden">
          <img
            src={imgSrc}
            alt={headline}
            onError={() =>
              setImgSrc(
                "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop"
              )
            }
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 filter contrast-105"
            loading="lazy"
          />
          {/* Category sticker */}
          <div className="absolute top-3 left-3 flex gap-2">
            <Badge variant="lime" size="sm">
              {category || "General"}
            </Badge>
            {verifiedVerdict && (
              <Badge verdict={verifiedVerdict} size="sm" showIcon />
            )}
          </div>
        </div>

        {/* Content Details */}
        <div className="p-5 space-y-3">
          {/* Metadata Row */}
          <div className="flex items-center justify-between text-xs font-mono-tech text-[#111111]/70 pb-2 border-b border-[#111111]/15">
            <span className="font-bold text-[#111111] flex items-center gap-1 truncate max-w-[170px]" title={source}>
              <span>{sourceIcon || "📰"}</span>
              <span className="truncate">{source}</span>
            </span>
            <span className="flex items-center gap-1 shrink-0">
              <Clock className="w-3 h-3" />
              <span>{formatPublishDate(publishedAt)}</span>
            </span>
          </div>

          {/* Headline (Clickable to open original article) */}
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="block group/link"
              title="Open full web article in new tab"
            >
              <h3 className="font-display text-base sm:text-lg font-bold text-[#111111] leading-snug line-clamp-2 group-hover/link:text-[#0055FF] transition-colors flex items-start justify-between gap-1">
                <span>{headline}</span>
                <ExternalLink className="w-4 h-4 shrink-0 opacity-40 group-hover/link:opacity-100 mt-1" />
              </h3>
            </a>
          ) : (
            <h3 className="font-display text-base sm:text-lg font-bold text-[#111111] leading-snug line-clamp-2">
              {headline}
            </h3>
          )}

          {/* Description */}
          <p className="font-mono-tech text-xs text-[#111111]/75 leading-relaxed line-clamp-3">
            {description}
          </p>
        </div>
      </div>

      {/* Footer Action */}
      <div className="p-5 pt-0 mt-2">
        <div className="pt-4 border-t-2 border-[#111111] flex items-center justify-between gap-3">
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-mono-tech text-[11px] font-bold uppercase text-[#111111]/80 hover:text-[#0055FF] hover:underline"
            >
              <span>ORIGINAL SOURCE</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          ) : (
            <span className="font-mono-tech text-[10px] uppercase font-bold text-[#111111]/60">
              TRUTH CLASSIFIER
            </span>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={() => onFactCheck(article)}
            icon={Sparkles}
          >
            FACT CHECK
          </Button>
        </div>
      </div>
    </article>
  );
}
