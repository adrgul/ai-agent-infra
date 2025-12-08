import { useState, useEffect } from 'react';
import { UserProfile } from '../types';
import { getProfile, updateProfile } from '../api/client';

interface ProfileSettingsProps {
  onClose: () => void;
}

const INTEREST_OPTIONS = [
  'hiking', 'museums', 'photography', 'sports', 'cafes', 
  'shopping', 'nightlife', 'parks', 'food tours', 'art galleries',
  'live music', 'theater', 'architecture', 'beaches', 'cycling'
];

const DIETARY_OPTIONS = [
  'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 
  'halal', 'kosher', 'nut-free', 'low-carb'
];

export default function ProfileSettings({ onClose }: ProfileSettingsProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [profile, setProfile] = useState<UserProfile>({
    age: null,
    interests: [],
    mobility: null,
    clothing_style: null,
    dietary_preferences: [],
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await getProfile();
      if (data) {
        setProfile(data);
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await updateProfile(profile);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  const toggleInterest = (interest: string) => {
    setProfile(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const toggleDietary = (dietary: string) => {
    setProfile(prev => ({
      ...prev,
      dietary_preferences: prev.dietary_preferences.includes(dietary)
        ? prev.dietary_preferences.filter(d => d !== dietary)
        : [...prev.dietary_preferences, dietary]
    }));
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg max-w-2xl w-full my-8">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">👤 Your Profile</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Age */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Age (optional)
            </label>
            <input
              type="number"
              min="1"
              max="120"
              value={profile.age || ''}
              onChange={(e) => setProfile({ ...profile, age: e.target.value ? parseInt(e.target.value) : null })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your age"
            />
          </div>

          {/* Interests */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Interests (select all that apply)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {INTEREST_OPTIONS.map(interest => (
                <label
                  key={interest}
                  className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                >
                  <input
                    type="checkbox"
                    checked={profile.interests.includes(interest)}
                    onChange={() => toggleInterest(interest)}
                    className="rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{interest}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Mobility */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mobility Level
            </label>
            <div className="space-y-2">
              {(['high', 'medium', 'low'] as const).map(level => (
                <label
                  key={level}
                  className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                >
                  <input
                    type="radio"
                    name="mobility"
                    checked={profile.mobility === level}
                    onChange={() => setProfile({ ...profile, mobility: level })}
                    className="text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{level}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Clothing Style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Clothing Style
            </label>
            <div className="space-y-2">
              {(['casual', 'formal', 'sporty'] as const).map(style => (
                <label
                  key={style}
                  className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                >
                  <input
                    type="radio"
                    name="clothing_style"
                    checked={profile.clothing_style === style}
                    onChange={() => setProfile({ ...profile, clothing_style: style })}
                    className="text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{style}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Dietary Preferences */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dietary Preferences (optional)
            </label>
            <div className="grid grid-cols-2 gap-2">
              {DIETARY_OPTIONS.map(dietary => (
                <label
                  key={dietary}
                  className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                >
                  <input
                    type="checkbox"
                    checked={profile.dietary_preferences.includes(dietary)}
                    onChange={() => toggleDietary(dietary)}
                    className="rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 capitalize">{dietary}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </div>
    </div>
  );
}
