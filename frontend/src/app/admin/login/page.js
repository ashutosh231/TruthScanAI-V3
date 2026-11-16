"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AdminLoginRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Admin login is unified on the main login screen with the ADMIN LOGIN clearance toggle
    router.replace("/login");
  }, [router]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center bg-[#F5F1E8]">
      <div className="border-2 border-[#111111] bg-white p-6 shadow-[4px_4px_0px_0px_#111111] font-mono-tech text-xs font-bold uppercase text-[#111111]">
        Redirecting to Unified Clearance Login...
      </div>
    </div>
  );
}
