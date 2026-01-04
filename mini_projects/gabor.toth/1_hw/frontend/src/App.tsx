import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BriefingForm } from "./components/BriefingForm";
import { BriefingView } from "./components/BriefingView";
import { useGenerateBriefing, useHistory } from "./hooks/useBriefing";
import { CityBriefingResponse } from "./api/types";

const queryClient = new QueryClient();

function AppContent() {
  const [activeTab, setActiveTab] = useState<"generate" | "history">("generate");
  const [status, setStatus] = useState<string>("");
  const { mutate: generateBriefing, isPending, data: briefingData, error } = useGenerateBriefing();
  const { data: historyData } = useHistory();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Navigation */}
      <nav className="bg-slate-950 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">🌍 Város Tájékoztató Ügynök</h1>
            <p className="text-slate-400">Olvasd végig a README.md-t először</p>
          </div>
        </div>
      </nav>

      {/* Tabs */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("generate")}
              className={`px-4 py-3 font-semibold transition-colors ${
                activeTab === "generate"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Tájékoztató Készítése
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-4 py-3 font-semibold transition-colors ${
                activeTab === "history"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Előzmények ({historyData?.length || 0})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === "generate" ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <BriefingForm
                onSubmit={(params) => {
                  setStatus("🔄 Starting briefing generation...");
                  generateBriefing(params);
                }}
                isLoading={isPending}
              />
              
              {/* Status Message */}
              {(isPending || status || error) && (
                <div className={`mt-6 p-4 rounded-lg ${
                  error 
                    ? "bg-red-900/30 border border-red-500 text-red-300" 
                    : "bg-blue-900/30 border border-blue-500 text-blue-200"
                }`}>
                  {error && (
                    <div>
                      <p className="font-semibold">❌ Error</p>
                      <p className="text-sm mt-1">{(error as any).message || "Failed to generate briefing"}</p>
                    </div>
                  )}
                  {isPending && (
                    <div>
                      <p className="font-semibold">⏳ Processing...</p>
                      <p className="text-sm mt-1">{status || "Initializing..."}</p>
                      <div className="mt-3 w-full bg-gray-700 rounded h-1">
                        <div className="bg-blue-500 h-1 rounded animate-pulse" style={{width: "100%"}}></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="lg:col-span-2">
              {briefingData ? (
                <BriefingView data={briefingData} />
              ) : (
                <div className="bg-slate-800/50 p-12 rounded-lg text-center text-slate-300">
                  <p className="text-lg">Add meg a város nevét, és hogy mit szeretnél csinálni, én pedig elkészítem a személyre szabott tájékoztatást.</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Briefing History</h2>
            {historyData && historyData.length > 0 ? (
              <div className="space-y-4">
                {historyData.map((briefing: CityBriefingResponse, idx: number) => (
                  <div key={idx} className="bg-slate-800 p-6 rounded-lg hover:bg-slate-700 transition cursor-pointer">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-xl font-bold text-white">{briefing.city}</h3>
                        <p className="text-slate-400">
                          {briefing.metadata?.generated_at ? new Date(briefing.metadata.generated_at).toLocaleDateString() : ""}
                        </p>
                      </div>
                      <span className="text-xs bg-slate-700 text-slate-300 px-3 py-1 rounded">
                        {briefing.metadata?.generated_at ? new Date(briefing.metadata.generated_at).toLocaleTimeString() : ""}
                      </span>
                    </div>
                    <p className="text-slate-300 mt-3 line-clamp-2">{briefing.briefing.paragraph}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-slate-800/50 p-12 rounded-lg text-center text-slate-300">
                <p>No briefings generated yet. Start by generating one!</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
