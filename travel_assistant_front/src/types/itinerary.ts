export interface Itinerary {
  id?: string;
  _id?: string; // MongoDB ObjectId mapeado como string
  title: string;
  content: string;
  users: string[];
  is_default: boolean;
  created_at?: string;
  updated_at?: string;
}
