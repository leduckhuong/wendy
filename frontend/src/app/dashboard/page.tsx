"use client";

import { useState, useEffect } from "react";
import { Toaster } from "sonner";
import { notify } from "@/libs/utils";

interface DataItem {
  id: number;
  data: string;
  created_at: string;
}

export default function Dashboard() {
  const [data, setData] = useState<DataItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/reader/read', {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const result = await response.json();
        notify.success("Data synced successfully!");
        // Since the API doesn't return data in response, we'll just show success
        setData([]);
      } else {
        notify.error("Failed to sync data");
      }
    } catch (error) {
      console.error("Sync error:", error);
      notify.error("Error syncing data");
    } finally {
      setLoading(false);
      setSyncing(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    await fetchData();
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <Toaster />
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-2 bg-cyan-600 text-white rounded-md hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {syncing ? "Syncing..." : "Sync Data"}
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
          Data Overview
        </h2>

        {loading ? (
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600"></div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-cyan-50 dark:bg-cyan-900/20 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-cyan-900 dark:text-cyan-100">
                  Total Records
                </h3>
                <p className="text-2xl font-bold text-cyan-600 dark:text-cyan-400">
                  {data.length}
                </p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-green-900 dark:text-green-100">
                  Files Processed
                </h3>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  --
                </p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100">
                  Active Workers
                </h3>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  --
                </p>
              </div>
            </div>

            <div className="border-t pt-4">
              <h3 className="text-lg font-medium mb-4 text-gray-900 dark:text-white">
                Recent Data
              </h3>
              {data.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400">
                  No data available. Click "Sync Data" to load recent data.
                </p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {data.slice(0, 10).map((item) => (
                    <div
                      key={item.id}
                      className="p-3 bg-gray-50 dark:bg-gray-700 rounded border"
                    >
                      <p className="text-sm text-gray-900 dark:text-white font-mono">
                        {item.data}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
