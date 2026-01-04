import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { briefingAPI } from "../api/client";

export const useBriefing = (params: {
  city: string;
  activity?: string;
}) => {
  return useQuery({
    queryKey: ["briefing", params],
    queryFn: () => briefingAPI.getBriefing(params).then((res) => res.data),
    enabled: !!params.city,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useHistory = (limit: number = 20) => {
  return useQuery({
    queryKey: ["history", limit],
    queryFn: () => briefingAPI.getHistory(limit).then((res) => res.data),
    staleTime: 1000 * 60 * 1, // 1 minute
  });
};

export const useGenerateBriefing = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (params: {
      city: string;
      activity?: string;
    }) => {
      console.log("🚀 Starting API call to:", params.city, "activity:", params.activity);
      try {
        const response = await briefingAPI.getBriefing(params);
        console.log("✅ API Response:", response);
        return response.data;
      } catch (error) {
        console.error("❌ API Error:", error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["history"] });
    },
    onError: (error) => {
      console.error("❌ Mutation error:", error);
    },
  });
};
