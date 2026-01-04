export interface Coordinates {
  lat: number;
  lon: number;
}

export interface Activity {
  name: string;
  description: string;
  type: string;
}

export interface CityFact {
  title: string;
  content: string;
}

export interface Briefing {
  paragraph: string;
}

export interface POI {
  type: string;
  name: string;
  distance_m: number;
  walking_minutes: number;
  lat: number;
  lon: number;
}

export interface CityBriefingResponse {
  city: string;
  coordinates: Coordinates;
  recommended_activities: Activity[];
  city_facts: CityFact[];
  briefing: Briefing;
  nearby_places?: POI[];
  fallback_message?: string;
  metadata?: Record<string, any>;
}
