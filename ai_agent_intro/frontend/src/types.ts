export interface Coordinates {
  lat: number;
  lon: number;
}

export interface WeatherData {
  temperature_min: number;
  temperature_max: number;
  wind_speed: number;
  precipitation_probability: number;
}

export interface Briefing {
  summary: string;
  outfit: string;
  activities: string[];
  note: string | null;
}

export interface BriefingResponse {
  city: string;
  country: string;
  coordinates: Coordinates;
  date: string;
  weather: WeatherData;
  briefing: Briefing;
  timestamp: string;
}

export interface HistoryEntry {
  city: string;
  date: string;
  timestamp: string;
}

export interface BriefingRequest {
  city: string;
  date?: string;
  language?: string;
}

export interface UserProfile {
  age: number | null;
  interests: string[];
  mobility: 'high' | 'medium' | 'low' | null;
  clothing_style: 'casual' | 'formal' | 'sporty' | null;
  dietary_preferences: string[];
}
